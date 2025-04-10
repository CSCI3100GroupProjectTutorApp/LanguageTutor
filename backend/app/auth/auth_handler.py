# app/auth/auth_handler.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

from ..models.user_model import UserInDB
from .jwt_handler import verify_token
from ..database.mongodb_connection import get_db

# For password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

async def get_user(username: str):
    """Get a user by username"""
    try:
        db = await get_db()
        user_doc = await db.users.find_one({"username": username})
        if user_doc:
            # Explicitly convert MongoDB's _id to user_id string
            if '_id' in user_doc:
                user_doc['user_id'] = str(user_doc['_id'])
            return UserInDB(**user_doc)
        return None
    except Exception as e:
        print(f"Error retrieving user: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail=f"Database error: {str(e)}"
        )

async def authenticate_user(username: str, password: str):
    """Authenticate a user"""
    db = await get_db()
    user_doc = await db.users.find_one({"username": username})
    
    if not user_doc:
        return False
    
    user = UserInDB(**user_doc)
    
    if not verify_password(password, user.hashed_password):
        return False
        
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token and get user_id
        token_data = verify_token(token, credentials_exception)
        username = token_data["user_id"]
        
        # Get user from database
        user = await get_user(username)
        if user is None:
            raise credentials_exception
            
        return user
    except HTTPException:
        # Re-raise HTTP exceptions as is
        raise
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        # Instead of a general error, always return the unauthorized error
        # for security reasons
        raise credentials_exception

async def is_admin(current_user: UserInDB = Depends(get_current_user)):
    """Check if the current user is an admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user