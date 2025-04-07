from datetime import datetime, timedelta
from datetime import timezone
from typing import Optional
from jose import jwt, JWTError
from fastapi import HTTPException, status
import secrets

from ..config import settings
from ..utils.timezone_utils import get_hk_time, HK_TIMEZONE

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a new JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = get_hk_time() + expires_delta
    else:
        expire = get_hk_time() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create a new JWT refresh token with longer expiry"""
    to_encode = data.copy()
    
    # Refresh tokens typically last longer than access tokens
    expire = get_hk_time() + timedelta(days=7)  # 7 days
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt

def verify_token(token: str, credentials_exception, token_type: str = "access"):
    """Verify the JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Check token type if provided in the token
        if "type" in payload and payload.get("type") != token_type:
            raise credentials_exception
            
        return {"user_id": username}
    except JWTError as e:
        print(f"JWT verification error: {str(e)}")
        raise credentials_exception
