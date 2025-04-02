# app/routes/sync_routes.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from ..dependencies import get_sqlite_storage, get_mongo_client

router = APIRouter(
    prefix="/sync",
    tags=["sync"],
    responses={404: {"description": "Not found"}},
)

class SyncResult(BaseModel):
    success: bool
    message: str
    operations_processed: int = 0

class SyncStatus(BaseModel):
    last_sync_attempt: str = None
    last_successful_sync: str = None
    pending_operations: int = 0
    is_online: bool = False
    sync_in_progress: bool = False

@router.get("/status", response_model=SyncStatus)
async def get_sync_status(
    storage=Depends(get_sqlite_storage)
):
    """Get the current synchronization status."""
    return storage.get_sync_status()

@router.post("/force", response_model=SyncResult)
async def force_sync(
    storage=Depends(get_sqlite_storage),
    mongo_client=Depends(get_mongo_client)
):
    """Force an immediate synchronization with MongoDB."""
    result = await storage.force_sync(mongo_client)
    return result

@router.post("/start-auto")
async def start_auto_sync(
    storage=Depends(get_sqlite_storage),
    mongo_client=Depends(get_mongo_client)
):
    """Start automatic background synchronization."""
    storage.start_auto_sync(mongo_client)
    return {"message": "Auto-sync started"}

@router.post("/stop-auto")
async def stop_auto_sync(
    storage=Depends(get_sqlite_storage)
):
    """Stop automatic background synchronization."""
    storage.stop_auto_sync()
    return {"message": "Auto-sync stopped"}

@router.get("/pending", response_model=List[Dict[str, Any]])
async def get_pending_operations(
    storage=Depends(get_sqlite_storage)
):
    """Get all pending synchronization operations."""
    return await storage.get_pending_syncs()