from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from authlib.integrations.starlette_client import OAuth
from ..core.database import get_db
from ..core.config import settings
from ..services.auth_service import (
    create_access_token, 
    verify_google_token, 
    get_or_create_user,
    get_current_user
)
from ..models.models import User

router = APIRouter(prefix="/auth", tags=["authentication"])

# OAuth setup
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://accounts.google.com/o/oauth2/token",
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
    client_kwargs={
        "scope": "openid email profile"
    }
)


class GoogleTokenRequest(BaseModel):
    token: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    picture: str = None
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


@router.get("/google/login")
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        # Get the authorization code and exchange for token
        token = await oauth.google.authorize_access_token(request)
        
        # Verify the ID token
        google_user_info = verify_google_token(token.get('id_token'))
        
        # Get or create user
        user = get_or_create_user(google_user_info, db)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        # Redirect to frontend with token (you might want to adjust this)
        frontend_url = f"http://localhost:3000/auth/callback?token={access_token}"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/google/token", response_model=TokenResponse)
async def google_token_auth(
    token_request: GoogleTokenRequest,
    db: Session = Depends(get_db)
):
    """Authenticate with Google ID token (for frontend integration)"""
    try:
        # Verify the Google ID token
        google_user_info = verify_google_token(token_request.token)
        
        # Get or create user
        user = get_or_create_user(google_user_info, db)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserResponse.from_orm(current_user)


@router.post("/logout")
async def logout():
    """Logout user (client should delete token)"""
    return {"message": "Successfully logged out"} 