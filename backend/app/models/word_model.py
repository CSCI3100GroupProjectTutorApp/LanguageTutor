from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from datetime import timezone
from enum import Enum
from ..utils.timezone_utils import get_hk_time, HK_TIMEZONE

class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCED = "synced"

class Word(BaseModel):
    word_id: Optional[str] = None
    text: str
    translation: Optional[str] = None
    language_pair: str = "en-zh"
    notes: Optional[str] = None
    date_added: datetime = Field(default_factory=get_hk_time)
    user_id: str
    sync_status: SyncStatus = SyncStatus.SYNCED
    proficiency_level: Optional[int] = None

class WordCreate(BaseModel):
    text: str
    translation: Optional[str] = None
    language_pair: str = "en-zh"
    notes: Optional[str] = None
    proficiency_level: Optional[int] = None