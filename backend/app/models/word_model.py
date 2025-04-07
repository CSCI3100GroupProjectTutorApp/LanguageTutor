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
    """
    Word model 
    """
    word_id: Optional[str] = Field(None, alias="wordid")  # Maps to wordid in MongoDB
    text: str = Field(..., alias="word")  # Maps to word in MongoDB
    translation: Optional[str] = Field(None, alias="ch_meaning")  # Maps to ch_meaning in MongoDB
    notes: Optional[str] = Field(None, alias="en_meaning")  # Maps to en_meaning in MongoDB
    part_of_speech: Optional[List[str]] = Field(default_factory=list)  # Maps to part_of_speech in MongoDB
    date_added: Optional[datetime] = Field(None, alias="wordtime")  # Maps to wordtime in MongoDB
    user_id: Optional[str] = None  # Added for user association
    language_pair: str = "en-zh"  # Default language pair (not in MongoDB structure)
    sync_status: SyncStatus = SyncStatus.SYNCED  # For sync functionality
    proficiency_level: Optional[int] = None  # For future learning analytics

    class Config:
        """
        Pydantic configuration for field aliases and data validation
        """
        populate_by_name = True  # Allow populating by field name or alias
        schema_extra = {
            "example": {
                "word_id": "1",
                "text": "hello",
                "translation": "你好",
                "notes": "Common greeting",
                "part_of_speech": ["noun", "interjection"],
                "date_added": "2023-04-01T12:00:00",
                "user_id": "123456",
                "language_pair": "en-zh",
                "sync_status": "synced",
                "proficiency_level": 3
            }
        }
        
    # Method to convert to MongoDB document format
    def to_mongodb_dict(self) -> dict:
        """
        Convert to MongoDB document format
        """
        return {
            "wordid": int(self.word_id) if self.word_id and self.word_id.isdigit() else None,
            "word": self.text,
            "ch_meaning": self.translation or "",
            "en_meaning": self.notes or "",
            "part_of_speech": self.part_of_speech or [],
            "wordtime": self.date_added.strftime('%Y-%m-%d %H:%M:%S') if self.date_added else None,
            "user_id": self.user_id,
            # We don't store these in MongoDB directly
            # "language_pair": self.language_pair,
            # "sync_status": self.sync_status,
            # "proficiency_level": self.proficiency_level
        }
    
    # Method to create model from MongoDB document
    @classmethod
    def from_mongodb_dict(cls, doc: dict):
        """
        Create model from MongoDB document
        """
        if not doc:
            return None
            
        return cls(
            wordid=str(doc.get("wordid")),
            word=doc.get("word", ""),
            ch_meaning=doc.get("ch_meaning", ""),
            en_meaning=doc.get("en_meaning", ""),
            part_of_speech=doc.get("part_of_speech", []),
            wordtime=doc.get("wordtime"),
            user_id=doc.get("user_id"),
            language_pair="en-zh",  # Default
            sync_status=SyncStatus.SYNCED,
            proficiency_level=None
        )

class WordCreate(BaseModel):
    """
    Model for creating a new word
    """
    text: str
    translation: Optional[str] = None
    notes: Optional[str] = None
    part_of_speech: Optional[List[str]] = Field(default_factory=list)
    language_pair: str = "en-zh"
    proficiency_level: Optional[int] = None
    
    # Convert to format needed by MongoDB utils
    def to_add_word_params(self):
        """
        Convert to parameters for add_word MongoDB util
        """
        return {
            "word": self.text,
            "en_meaning": self.notes or "",
            "ch_meaning": self.translation or "",
            "part_of_speech": self.part_of_speech or []
        }

class WordUpdate(BaseModel):
    """
    Model for updating an existing word
    """
    text: Optional[str] = None
    translation: Optional[str] = None
    notes: Optional[str] = None
    part_of_speech: Optional[List[str]] = None
    proficiency_level: Optional[int] = None
    
    # Convert to format needed by MongoDB utils
    def to_update_data(self):
        """
        Convert to update_data for update_word MongoDB util
        """
        update_data = {}
        if self.text is not None:
            update_data["word"] = self.text
        if self.translation is not None:
            update_data["ch_meaning"] = self.translation
        if self.notes is not None:
            update_data["en_meaning"] = self.notes
        if self.part_of_speech is not None:
            update_data["part_of_speech"] = self.part_of_speech
        return update_data