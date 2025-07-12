from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx
import os
from datetime import datetime

from app.core.database import get_db

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint that verifies:
    - API is running
    - Database connectivity
    - ChromaDB connectivity
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = {
            "status": "healthy",
            "type": "postgresql"
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "type": "postgresql"
        }
        health_status["status"] = "degraded"
    
    # Check ChromaDB connectivity
    try:
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = os.getenv("CHROMA_PORT", "8000")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{chroma_host}:{chroma_port}/api/v1/heartbeat",
                timeout=5.0
            )
            
        if response.status_code == 200:
            health_status["services"]["chromadb"] = {
                "status": "healthy",
                "type": "vector_database"
            }
        else:
            health_status["services"]["chromadb"] = {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}",
                "type": "vector_database"
            }
            health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["services"]["chromadb"] = {
            "status": "unhealthy",
            "error": str(e),
            "type": "vector_database"
        }
        health_status["status"] = "degraded"
    
    # Return appropriate HTTP status
    if health_status["status"] == "healthy":
        return health_status
    else:
        raise HTTPException(status_code=503, detail=health_status) 