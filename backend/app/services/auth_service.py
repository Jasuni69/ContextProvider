from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session
from ..core.config import settings
from ..core.database import get_db
from ..models.models import User

# JWT token handling
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key or settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key or settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def verify_google_token(token: str):
    """Verify Google ID token and return user info"""
    try:
        # Verify the token
        id_info = id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.google_client_id
        )
        
        # Verify the issuer
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        return {
            'google_id': id_info['sub'],
            'email': id_info['email'],
            'name': id_info.get('name', ''),
            'picture': id_info.get('picture', ''),
            'email_verified': id_info.get('email_verified', False)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )


def get_or_create_user(google_user_info: dict, db: Session) -> User:
    """Get existing user or create new one from Google info"""
    user = db.query(User).filter(User.google_id == google_user_info['google_id']).first()
    
    if not user:
        # Check if user exists with same email
        existing_user = db.query(User).filter(User.email == google_user_info['email']).first()
        if existing_user:
            # Update existing user with Google ID
            existing_user.google_id = google_user_info['google_id']
            existing_user.name = google_user_info['name']
            existing_user.picture = google_user_info['picture']
            existing_user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_user)
            return existing_user
        
        # Create new user
        user = User(
            google_id=google_user_info['google_id'],
            email=google_user_info['email'],
            name=google_user_info['name'],
            picture=google_user_info['picture'],
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update existing user info
        user.name = google_user_info['name']
        user.picture = google_user_info['picture']
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
    
    return user 