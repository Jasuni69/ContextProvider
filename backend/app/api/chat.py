from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..core.database import get_db
from ..models.models import ChatSession, ChatMessage, User, Document
from ..services.chat_service import ChatService
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessageRequest(BaseModel):
    message: str
    document_id: Optional[int] = None


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime
    relevance_score: Optional[float] = None

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    document_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ChatSessionCreateRequest(BaseModel):
    title: str
    document_id: Optional[int] = None


class ChatResponse(BaseModel):
    session_id: int
    message: ChatMessageResponse
    response: ChatMessageResponse


class SimpleChatResponse(BaseModel):
    response: str
    sources: List[str] = []


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_request: ChatSessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    
    # Validate document ownership if document_id is provided
    if session_request.document_id:
        document = db.query(Document).filter(
            Document.id == session_request.document_id,
            Document.user_id == current_user.id
        ).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
    
    # Create chat session
    chat_session = ChatSession(
        user_id=current_user.id,
        document_id=session_request.document_id,
        title=session_request.title
    )
    
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    
    return ChatSessionResponse.from_orm(chat_session)


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for the current user"""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()
    
    # Add message count to each session
    session_responses = []
    for session in sessions:
        session_dict = session.__dict__.copy()
        session_dict['message_count'] = len(session.messages)
        session_responses.append(ChatSessionResponse(**session_dict))
    
    return session_responses


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat session"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    session_dict = session.__dict__.copy()
    session_dict['message_count'] = len(session.messages)
    return ChatSessionResponse(**session_dict)


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages in a chat session"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    return [ChatMessageResponse.from_orm(msg) for msg in messages]


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: int,
    message_request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """Send a message in a chat session (temporarily without authentication for testing)"""
    
    # Get session (without user validation for testing)
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Create user message
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_request.message
    )
    
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    try:
        # Get AI response
        chat_service = ChatService()
        
        # Use document from message request or session
        document_id = message_request.document_id or session.document_id
        
        if document_id:
            # Get document (without user validation for testing)
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            # Get document-specific response
            ai_response, relevance_score = chat_service.get_document_response(
                message_request.message,
                document_id,
                document.user_id  # Use document's user_id instead of current_user.id
            )
        else:
            # Get general response
            ai_response = chat_service.get_general_response(message_request.message)
            relevance_score = None
        
        # Create AI message
        ai_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=ai_response,
            relevance_score=relevance_score
        )
        
        db.add(ai_message)
        
        # Update session timestamp
        session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(ai_message)
        
        return ChatResponse(
            session_id=session_id,
            message=ChatMessageResponse.from_orm(user_message),
            response=ChatMessageResponse.from_orm(ai_message)
        )
        
    except Exception as e:
        # Create error response
        error_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=f"I apologize, but I encountered an error processing your request: {str(e)}"
        )
        
        db.add(error_message)
        db.commit()
        db.refresh(error_message)
        
        return ChatResponse(
            session_id=session_id,
            message=ChatMessageResponse.from_orm(user_message),
            response=ChatMessageResponse.from_orm(error_message)
        )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Delete all messages in the session (cascade should handle this)
    db.delete(session)
    db.commit()
    
    return {"message": "Chat session deleted successfully"}


@router.post("/message", response_model=SimpleChatResponse)
async def send_quick_message(
    message_request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """Send a quick message (temporarily without authentication for testing)"""
    
    # For testing: get or create a default user
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
    
    # If no specific document_id provided, search across all user documents
    if not message_request.document_id:
        # Get all processed documents for the user
        processed_docs = db.query(Document).filter(
            Document.user_id == current_user.id,
            Document.processed == True
        ).all()
        
        if not processed_docs:
            return SimpleChatResponse(
                response="I don't have any processed documents to search through. Please upload and process a document first.",
                sources=[]
            )
        
        # Use the first processed document or search across all
        message_request.document_id = processed_docs[0].id
    
    # Get AI response directly without creating session
    try:
        chat_service = ChatService()
        document_id = message_request.document_id
        
        if document_id:
            # Get document
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return SimpleChatResponse(
                    response="Document not found.",
                    sources=[]
                )
            
            # Get document-specific response
            ai_response, relevance_score = chat_service.get_document_response(
                message_request.message,
                document_id,
                document.user_id
            )
            
            return SimpleChatResponse(
                response=ai_response,
                sources=[f"Document: {document.original_filename}"]
            )
        else:
            # Get general response
            ai_response = chat_service.get_general_response(message_request.message)
            return SimpleChatResponse(
                response=ai_response,
                sources=[]
            )
            
    except Exception as e:
        return SimpleChatResponse(
            response=f"I apologize, but I encountered an error processing your request: {str(e)}",
            sources=[]
        ) 