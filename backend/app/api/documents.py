from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import asyncio
from datetime import datetime

from ..core.database import get_db
from ..models.models import Document, DocumentChunk
from ..services.document_service import DocumentProcessor
from ..services.vector_service import VectorService

router = APIRouter()

# Initialize services
document_processor = DocumentProcessor()
vector_service = VectorService()

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a document"""
    
    # Validate file type
    file_extension = file.filename.split('.')[-1].lower()
    allowed_extensions = ['pdf', 'txt', 'csv']
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_extension} not supported. Allowed: {allowed_extensions}"
        )
    
    # Validate file size (10MB limit)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 10MB")
    
    try:
        # Save file
        file_path, generated_filename = document_processor.save_uploaded_file(
            file_content, file.filename
        )
        
        # Create database record
        db_document = Document(
            filename=generated_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_type=file_extension,
            file_size=len(file_content),
            processed=False
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        # Process document in background
        background_tasks.add_task(
            process_document_background,
            db_document.id,
            file_path,
            file_extension
        )
        
        return {
            "id": db_document.id,
            "filename": db_document.original_filename,
            "file_type": db_document.file_type,
            "file_size": db_document.file_size,
            "processed": db_document.processed,
            "upload_date": db_document.upload_date
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

async def process_document_background(document_id: int, file_path: str, file_type: str):
    """Background task to process document"""
    from ..core.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return
        
        # Extract text
        text_content = document_processor.extract_text_from_file(file_path, file_type)
        
        # Create chunks
        chunks = document_processor.chunk_text(text_content, file_type)
        
        # Store chunks in vector database
        chunk_ids = vector_service.add_document_chunks(
            document_id=document_id,
            chunks=chunks,
            metadata={
                "filename": document.original_filename,
                "file_type": document.file_type
            }
        )
        
        # Save chunks to database
        for i, (chunk_text, chunk_id) in enumerate(zip(chunks, chunk_ids)):
            db_chunk = DocumentChunk(
                document_id=document_id,
                chunk_text=chunk_text,
                chunk_index=i,
                embedding_id=chunk_id
            )
            db.add(db_chunk)
        
        # Mark document as processed
        document.processed = True
        db.commit()
        
    except Exception as e:
        print(f"Error processing document {document_id}: {e}")
        # Mark document as failed (you might want to add a status field)
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.processed = False
            db.commit()
    finally:
        db.close()

@router.get("/")
async def get_documents(db: Session = Depends(get_db)):
    """Get all documents"""
    documents = db.query(Document).all()
    return [
        {
            "id": doc.id,
            "filename": doc.original_filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "processed": doc.processed,
            "upload_date": doc.upload_date
        }
        for doc in documents
    ]

@router.get("/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get a specific document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "filename": document.original_filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "processed": document.processed,
        "upload_date": document.upload_date
    }

@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete from vector database
        vector_service.delete_document_chunks(document_id)
        
        # Delete chunks from database
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        
        # Delete document record
        db.delete(document)
        db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}") 