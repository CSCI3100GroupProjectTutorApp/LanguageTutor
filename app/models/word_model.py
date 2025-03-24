from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from datetime import timezone
from enum import Enum

class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCED = "synced"

class Word(BaseModel):
    word_id: Optional[str] = None
    text: str
    translation: Optional[str] = None
    language_pair: str = "en-zh"
    notes: Optional[str] = None
    date_added: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str
    sync_status: SyncStatus = SyncStatus.SYNCED
    proficiency_level: Optional[int] = None

class WordCreate(BaseModel):
    text: str
    translation: Optional[str] = None
    language_pair: str = "en-zh"
    notes: Optional[str] = None
    proficiency_level: Optional[int] = None