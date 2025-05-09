from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
import datetime
import asyncio
import json
import os
from ..models.sync_model import SyncRequest, SyncResponse, SyncOperation
from ..dependencies import UserInToken, get_current_user
from ..dependencies import get_sqlite_storage, get_mongodb_client
from ..database import mongodb_utils as mdb
from ..utils.logger import logger
from ..database.mongodb_utils.word_operations import log_word_operation, get_user_word_stats


router = APIRouter(
    prefix="/sync",
    tags=["sync"],
)

@router.post("/", response_model=SyncResponse)
async def sync_data(
    sync_request: SyncRequest, 
    current_user: UserInToken = Depends(get_current_user),
    mongo_client = Depends(get_mongodb_client)
):
    """
    Upload all operations from the JSON request to MongoDB.
    """
    # Set up logging
    import logging
    logger = logging.getLogger(__name__)
    
    # Get the user ID from MongoDB using the authenticated username
    user_doc = await mdb.get_user(mongo_client, username=current_user.username)
    user_id = str(user_doc["_id"])  # Convert ObjectId to string
    
    # Statistics for tracking
    stats = {
        "processed_ops": 0,
        "failed_ops": 0
    }
    
    try:
        # Iterate over the operations in the sync_request
        for operation in sync_request.operations:
            try:
                # Log the operation to MongoDB
                await log_word_operation(
                    client=mongo_client,
                    user_id=user_id,
                    wordid=int(operation.wordid) if operation.wordid else None,
                    word=operation.word,
                    operation_type=operation.operation,
                    data=operation.data,
                    timestamp=operation.timestamp
                )
                stats["processed_ops"] += 1
            except Exception as e:
                logger.error(f"Error uploading operation {operation.operation} for word {operation.word}: {str(e)}")
                stats["failed_ops"] += 1
        
        logger.info(f"Upload completed. Processed: {stats['processed_ops']}, Failed: {stats['failed_ops']}")
    
    except Exception as e:
        logger.error(f"Error during upload: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Generate current timestamp for the response
    current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Return response
    return SyncResponse(
        sync_timestamp=current_timestamp,
        new_server_operations=[],  # No new server operations in this simplified version
        stats=stats
    )

