from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional
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
    processing_error: Optional[str] = None
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
    db: Session = Depends(get_db)
):
    """Upload a document for processing (temporarily without authentication for testing)"""
    
    # For testing: get or create a default user
    from ..models.models import User
    default_user = db.query(User).filter(User.email == "test@example.com").first()
    if not default_user:
        default_user = User(
            email="test@example.com",
            google_id="test_user",
            name="Test User"
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
    
    current_user = default_user
    
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
    db: Session = Depends(get_db)
):
    """Get a specific document (temporarily without authentication for testing)"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse.from_orm(document)


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document (temporarily without authentication for testing)"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
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
    """Background task to process uploaded document with batch processing for large datasets"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return
        
        print(f"Starting processing for document {document.id}: {document.original_filename}")
        
        # Initialize document processor
        processor = DocumentProcessor()
        
        # Process the document
        chunks = processor.process_document(document.file_path, document.file_type)
        
        print(f"Generated {len(chunks)} chunks for document {document.id}")
        
        # Store chunks in vector database with batch processing
        from ..services.vector_service import VectorService
        vector_service = VectorService()
        
        # Create document collection ID
        collection_id = f"doc_{document.id}"
        
        # Process chunks in batches to avoid overwhelming ChromaDB and OpenAI
        batch_size = 10  # Process 10 chunks at a time
        successful_chunks = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            print(f"Processing batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size} ({len(batch)} chunks)")
            
            for j, chunk in enumerate(batch):
                try:
                    chunk_index = i + j
                    metadata = {
                        "document_id": document.id,
                        "user_id": document.user_id,
                        "chunk_index": chunk_index,
                        "filename": document.original_filename,
                        "file_type": document.file_type
                    }
                    
                    vector_service.add_document(collection_id, chunk, metadata)
                    successful_chunks += 1
                    
                    # Small delay to avoid overwhelming the API
                    import time
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error processing chunk {chunk_index}: {e}")
                    # Continue with next chunk rather than failing entirely
                    continue
            
            # Longer delay between batches
            if i + batch_size < len(chunks):
                import time
                time.sleep(1)
                print(f"Completed batch, {successful_chunks}/{len(chunks)} chunks processed so far")
        
        print(f"Completed processing: {successful_chunks}/{len(chunks)} chunks successfully stored")
        
        # Update document status
        document.processed = True
        document.chunk_count = successful_chunks
        document.processing_error = None
        
        if successful_chunks == 0:
            document.processing_error = "No chunks were successfully processed"
            document.processed = False
        elif successful_chunks < len(chunks):
            document.processing_error = f"Partial processing: {successful_chunks}/{len(chunks)} chunks stored"
        
        db.commit()
        
    except Exception as e:
        # Update document with error
        print(f"Error processing document {document_id}: {e}")
        import traceback
        traceback.print_exc()
        
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.processed = False
            document.processing_error = str(e)
            db.commit()
        
        print(f"Error processing document {document_id}: {e}") 