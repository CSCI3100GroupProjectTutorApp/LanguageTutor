from typing import List, Optional, Dict
from pydantic import BaseModel

class SyncOperation(BaseModel):
    operation: str  # "add", "update", "delete", "mark", etc.
    wordid: Optional[str] = None
    word: str
    translation: Optional[str] = None
    context: Optional[str] = None
    data: Optional[dict] = None
    timestamp: str

class SyncRequest(BaseModel):
    user_id: str
    operations: List[SyncOperation]
    device_id: str
    last_sync_timestamp: Optional[str] = None

class SyncResponse(BaseModel):
    sync_timestamp: str
    new_server_operations: List[SyncOperation] = []
    success: bool = True 
    message: str = "Sync completed successfully"  
    processed_operations: int = 0 
    failed_operations: int = 0  