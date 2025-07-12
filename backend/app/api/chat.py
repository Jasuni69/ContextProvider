from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from ..core.database import get_db
from ..models.models import ChatSession, ChatMessage, Document
from ..services.vector_service import VectorService
from ..services.chat_service import ChatService

router = APIRouter()

# Initialize services
vector_service = VectorService()
chat_service = ChatService()

class MessageRequest(BaseModel):
    message: str
    session_id: Optional[int] = None

class MessageResponse(BaseModel):
    response: str
    sources: List[str] = []
    session_id: int

@router.post("/message", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    db: Session = Depends(get_db)
):
    """Send a message and get AI response"""
    
    try:
        # Get or create session
        if request.session_id:
            session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            # Create new session
            session = ChatSession(title="New Chat")
            db.add(session)
            db.commit()
            db.refresh(session)
        
        # Search for relevant document chunks
        search_results = vector_service.search_similar_chunks(
            query=request.message,
            n_results=5
        )
        
        # Generate response using chat service
        response_text, sources = chat_service.generate_response(
            query=request.message,
            search_results=search_results
        )
        
        # Save message and response to database
        chat_message = ChatMessage(
            session_id=session.id,
            message=request.message,
            response=response_text
        )
        db.add(chat_message)
        db.commit()
        
        return MessageResponse(
            response=response_text,
            sources=sources,
            session_id=session.id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.get("/sessions")
async def get_sessions(db: Session = Depends(get_db)):
    """Get all chat sessions"""
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
    return [
        {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }
        for session in sessions
    ]

@router.post("/sessions")
async def create_session(db: Session = Depends(get_db)):
    """Create a new chat session"""
    session = ChatSession(title="New Chat")
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at
    }

@router.get("/sessions/{session_id}")
async def get_session(session_id: int, db: Session = Depends(get_db)):
    """Get a specific chat session with messages"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp).all()
    
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "messages": [
            {
                "id": msg.id,
                "message": msg.message,
                "response": msg.response,
                "timestamp": msg.timestamp
            }
            for msg in messages
        ]
    }

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int, db: Session = Depends(get_db)):
    """Delete a chat session"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete all messages in the session
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    
    # Delete the session
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"} 