from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
import os
import shutil

from ..core.database import get_db
from ..core.config import settings
from ..models.models import Document, User
from ..services.document_service import DocumentProcessor
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    upload_date: datetime
    processed: bool
    processing_error: str = None
    chunk_count: int = 0

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document for processing"""
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
        )
    
    # Check file size
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
        )
    
    # Create unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create document record
    document = Document(
        user_id=current_user.id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        file_type=file_extension,
        processed=False
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Process document in background
    background_tasks.add_task(process_document_background, document.id, db)
    
    return DocumentUploadResponse(
        message="Document uploaded successfully and is being processed",
        document=DocumentResponse.from_orm(document)
    )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    db: Session = Depends(get_db)
):
    """List all documents (temporarily without authentication for testing)"""
    documents = db.query(Document).all()
    return [DocumentResponse.from_orm(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific document"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse.from_orm(document)


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete physical file
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}


def process_document_background(document_id: int, db: Session):
    """Background task to process uploaded document"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return
        
        # Initialize document processor
        processor = DocumentProcessor()
        
        # Process the document
        chunks = processor.process_document(document.file_path, document.file_type)
        
        # Store chunks in vector database
        from ..services.vector_service import VectorService
        vector_service = VectorService()
        
        # Create document collection ID
        collection_id = f"doc_{document.id}"
        
        # Store chunks with metadata
        for i, chunk in enumerate(chunks):
            metadata = {
                "document_id": document.id,
                "user_id": document.user_id,
                "chunk_index": i,
                "filename": document.original_filename,
                "file_type": document.file_type
            }
            vector_service.add_document(collection_id, chunk, metadata)
        
        # Update document status
        document.processed = True
        document.chunk_count = len(chunks)
        document.processing_error = None
        
        db.commit()
        
    except Exception as e:
        # Update document with error
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.processed = False
            document.processing_error = str(e)
            db.commit()
        
        print(f"Error processing document {document_id}: {e}") 