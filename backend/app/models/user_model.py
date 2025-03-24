from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from datetime import timezone
from bson import ObjectId

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    # I havn't add any validation here 
    username: str = Field(..., description="Unique username, 3-20 characters")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., description="Password, minimum 8 characters")

class UserLogin(BaseModel):
    username: str
    password: str

class UserInDB(UserBase):
    user_id: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    
    class Config:
        # Allow population by field name or alias
        populate_by_name = True
        # Set up aliases for MongoDB field names
        json_encoders = {
            ObjectId: str
        }
        
    @field_validator('user_id', mode='before')
    @classmethod  
    def set_id(cls, v):
        # If we get the MongoDB ObjectId directly, convert it to string
        if hasattr(v, '__str__'):
            return str(v)
        return v

class UserResponse(UserBase):
    user_id: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None

class RefreshToken(BaseModel):
    refresh_token: str