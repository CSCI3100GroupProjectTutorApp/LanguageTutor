"""
Dependencies for FastAPI dependency injection.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import Optional
from .database.mongodb_connection import get_mongodb_client
from .database import mongodb_utils as mdb
from .database.sqlite.sqlite_storage import WordStorage  # Import the class directly
from .auth.token_blacklist import is_blacklisted
from .config import settings

# Create a singleton instance of the WordStorage
# This is more efficient than creating a new one for each request
_word_storage = None

async def get_sqlite_storage():
    """Get the SQLite word storage instance."""
    global _word_storage
    if _word_storage is None:
        _word_storage = WordStorage()
        # Initialize the database asynchronously
        await _word_storage.initialize_db()
    return _word_storage

async def get_mongo_client():
    """Get the MongoDB client instance."""
    return await get_mongodb_client()

# User model for current_user
class UserInToken(BaseModel):
    username: str
    email: Optional[str] = None
    is_active: Optional[bool] = True

# Setup OAuth2 password bearer with token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current authenticated user based on JWT token.
    
    Args:
        token: JWT token from OAuth2PasswordBearer
        
    Returns:
        UserInToken: User object with username and other fields
        
    Raises:
        HTTPException: If token is invalid or user doesn't exist
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Check if token is blacklisted (logged out)
        if is_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Decode the JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract username from the 'sub' field
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Get user from database
        client = await get_mongodb_client()
        user_doc = await mdb.get_user(client, username=username)
        
        if user_doc is None:
            raise credentials_exception
            
        # Check if user is active
        if not user_doc.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user account"
            )
        
        # Create and return a UserInToken object
        user = UserInToken(
            username=username,
            email=user_doc.get("email"),
            is_active=user_doc.get("is_active", True)
        )
        
        return user
        
    except JWTError:
        raise credentials_exception