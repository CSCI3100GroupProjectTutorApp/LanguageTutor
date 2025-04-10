from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from datetime import timezone
from bson import ObjectId
from ..utils.timezone_utils import get_hk_time, HK_TIMEZONE
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    # I havn't add any validation here 
    username: str = Field(..., description="Unique username, 3-20 characters")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., description="Password, minimum 8 characters")
    license_key: Optional[str] = None # Optional for now, can be activated later

class UserLogin(BaseModel):
    username: str
    password: str

class UserInDB(UserBase):
    user_id: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=get_hk_time)
    last_login: Optional[datetime] = None
    has_valid_license: bool = False
    license_key: Optional[str] = None
    
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

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    is_active: bool
    has_valid_license: bool = False
    license_key: Optional[str] = None
    is_admin: bool

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None

class RefreshToken(BaseModel):
    refresh_token: str
