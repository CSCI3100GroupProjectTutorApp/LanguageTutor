# app/models/license_model.py
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator, EmailStr
import re
import uuid

class LicenseStatus(str, Enum):
    ACTIVE = "active"
    USED = "used"
    REVOKED = "revoked"

class License(BaseModel):
    license_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    license_key: str
    user_id: Optional[str] = None  # Will be set when license is used
    status: LicenseStatus = LicenseStatus.ACTIVE
    issued_date: datetime = Field(default_factory=datetime.now)
    activated_at: Optional[datetime] = None
    created_by: Optional[str] = None  # Admin who created the license
    
    @validator('license_key')
    def validate_license_format(cls, v):
        if not re.match(r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$', v):
            raise ValueError('License key must be in format AAAA-BBBB-CCCC-DDDD')
        return v

class LicenseActivate(BaseModel):
    license_key: str
    
    @validator('license_key')
    def validate_license_key(cls, v):
        # Convert to uppercase and validate format
        v = v.upper()
        if not re.match(r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$', v):
            raise ValueError('License key must be in format AAAA-BBBB-CCCC-DDDD')
        return v

class LicenseFileUpload(BaseModel):
    file_content: str  # Base64 encoded file content

class EmailLicenseRequest(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    
class GenerateAndEmailLicenseRequest(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    count: int = Field(1, ge=1, le=10)  # Number of license keys to generate, default 1, max 10