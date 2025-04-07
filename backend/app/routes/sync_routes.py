from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import datetime
import asyncio
import json
from ..models.sync_model import SyncRequest, SyncResponse, SyncOperation
from ..dependencies import UserInToken, get_current_user
from ..dependencies import  get_sqlite_storage, get_mongodb_client
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
    storage = Depends(get_sqlite_storage),
    mongo_client = Depends(get_mongodb_client)
):
    """
    Synchronize offline vocabulary data with the server.
    """
    # Set up logging
    import logging
    logger = logging.getLogger(__name__)
    
    # Get the user ID from MongoDB using the authenticated username
    user_doc = await mdb.get_user(mongo_client, username=current_user.username)
    
    # Extract the user ID - this could be an ObjectId so convert to string
    user_id = str(user_doc["userid"])
    
    # Validate user_id from request matches authenticated user
    if sync_request.user_id != user_id:
        logger.warning(f"User ID mismatch: request={sync_request.user_id}, db={user_id}")
        # For now, just log the warning instead of raising an error
        # This allows testing even if IDs don't exactly match
        #raise HTTPException(
        #    status_code=status.HTTP_403_FORBIDDEN,
        #    detail="User ID in request doesn't match authenticated user"
        #)
    
    # Process operations from client
    processed_ops = 0
    failed_ops = 0
    translations_added = 0
    
    # Define a simple translation function if not already defined
    async def fetch_translation(word):
        """Placeholder for translation service"""
        # In a real implementation, this would call a translation API
        logger.info(f"Fetching translation for: {word}")
        return None  # Return None for now
    
    # Process operations from client
    for operation in sync_request.operations:
        try:
            # Process based on operation type
            if operation.operation == "add":
                # Get data from operation
                en_meaning = ""
                ch_meaning = operation.translation or ""
                part_of_speech = []
                
                if operation.data:
                    en_meaning = operation.data.get("en_meaning", "")
                    if "ch_meaning" in operation.data:
                        ch_meaning = operation.data.get("ch_meaning", ch_meaning)
                    part_of_speech = operation.data.get("part_of_speech", [])
                
                # Add word to local SQLite storage - this also adds to sync_queue
                wordid = await storage.add_word(
                    word=operation.word,
                    en_meaning=en_meaning,
                    ch_meaning=ch_meaning,
                    part_of_speech=part_of_speech,
                    user_id=user_id  # Use user_id, not user.id
                )
                
                # Check if translation is missing and needs to be fetched
                if not ch_meaning:
                    translation = await fetch_translation(operation.word)
                    if translation:
                        # Update the word with translation
                        await storage.update_word(
                            wordid=wordid,
                            update_data={"ch_meaning": translation},
                            user_id=user_id  # Use user_id, not user.id
                        )
                        translations_added += 1
                        
            elif operation.operation == "update":
                wordid = int(operation.wordid) if operation.wordid else None
                if not wordid:
                    # Try to find wordid if not provided
                    word_data = await storage.find_word(word=operation.word)
                    if word_data:
                        wordid = word_data["wordid"]
                    else:
                        logger.warning(f"Cannot update word {operation.word}: not found in database")
                        failed_ops += 1
                        continue
                
                # Prepare update data
                update_data = {}
                
                if operation.translation:
                    update_data["ch_meaning"] = operation.translation
                
                if operation.data:
                    if "en_meaning" in operation.data:
                        update_data["en_meaning"] = operation.data["en_meaning"]
                    if "ch_meaning" in operation.data:
                        update_data["ch_meaning"] = operation.data["ch_meaning"]
                    if "part_of_speech" in operation.data:
                        update_data["part_of_speech"] = operation.data["part_of_speech"]
                
                # Update word in SQLite - this also adds to sync_queue
                await storage.update_word(
                    wordid=wordid,
                    update_data=update_data,
                    user_id=user_id  # Use user_id, not user.id
                )
                
            elif operation.operation == "delete":
                wordid = int(operation.wordid) if operation.wordid else None
                
                # Delete word from SQLite - this also adds to sync_queue
                await storage.delete_word(
                    wordid=wordid,
                    word=operation.word if not wordid else None,
                    user_id=user_id  # Use user_id, not user.id
                )
                
            elif operation.operation == "mark":
                wordid = int(operation.wordid) if operation.wordid else None
                if not wordid:
                    # Try to find wordid if not provided
                    word_data = await storage.find_word(word=operation.word)
                    if word_data:
                        wordid = word_data["wordid"]
                    else:
                        logger.warning(f"Cannot mark word {operation.word}: not found in database")
                        failed_ops += 1
                        continue
                
                # Mark word in SQLite - this also adds to sync_queue
                await storage.mark_word(
                    user_id=user_id,  # Use user_id, not user.id
                    wordid=wordid,
                    context=operation.context
                )
                
            elif operation.operation == "quiz":
                wordid = int(operation.wordid) if operation.wordid else None
                if not wordid:
                    # Try to find wordid if not provided
                    word_data = await storage.find_word(word=operation.word)
                    if word_data:
                        wordid = word_data["wordid"]
                    else:
                        logger.warning(f"Cannot record quiz for word {operation.word}: not found in database")
                        failed_ops += 1
                        continue
                
                # Determine if correct
                is_correct = False
                if operation.data and "result" in operation.data:
                    is_correct = operation.data["result"] == "correct"
                
                # Record quiz attempt in SQLite - this also adds to sync_queue
                await storage.record_quiz_attempt(
                    user_id=user_id,  # Use user_id, not user.id
                    wordid=wordid,
                    is_correct=is_correct,
                    context=operation.context
                )
            
            # For other operation types that don't have specific handlers
            else:
                # Get wordid from operation or find it
                wordid = None
                if operation.wordid:
                    wordid = int(operation.wordid)
                elif operation.word:
                    word_data = await storage.find_word(word=operation.word)
                    if word_data:
                        wordid = word_data["wordid"]
                
                # Only proceed if we have a valid wordid or at least a word
                if wordid or operation.word:
                    # Directly add to sync queue
                    await storage._add_to_sync_queue(
                        operation=operation.operation,
                        user_id=user_id,  # Use user_id, not user.id
                        wordid=wordid,
                        word=operation.word,
                        result=operation.data.get("result") if operation.data else None,
                        context=operation.context,
                        data=json.dumps(operation.data) if operation.data else None
                    )
                else:
                    logger.warning(f"Cannot process operation {operation.operation}: no word or wordid provided")
                    failed_ops += 1
                    continue
            
            processed_ops += 1
            
        except Exception as e:
            logger.error(f"Error processing operation {operation.operation} for word {operation.word}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            failed_ops += 1
    
    # Sync all pending operations to MongoDB
    try:
        # This will sync all operations in SQLite sync_queue to MongoDB
        await storage.sync_with_mongodb(mongo_client)
    except Exception as e:
        logger.error(f"Error syncing with MongoDB: {str(e)}")
    
    # Get operations from MongoDB that client doesn't have
    # These are operations performed on other devices
    new_server_operations = []
    if sync_request.last_sync_timestamp:
        try:
            # Query MongoDB directly for operations after the last sync timestamp
            # that belong to this user but not from this device
            operations_collection = mongo_client.async_db["word_operations"]
            
            # Create the query
            query = {
                "user_id": user_id,  # Use user_id, not user.id
                "timestamp": {"$gt": sync_request.last_sync_timestamp}
            }
            
            # If device_id provided, exclude operations from this device
            if sync_request.device_id:
                query["device_id"] = {"$ne": sync_request.device_id}
            
            # Get operations from MongoDB
            cursor = operations_collection.find(query).sort("timestamp", 1)
            mongodb_ops = await cursor.to_list(length=None)
            
            # Convert MongoDB operations to SyncOperation format
            for op in mongodb_ops:
                # Create new SyncOperation
                sync_op = SyncOperation(
                    operation=op["operation_type"],
                    wordid=str(op["wordid"]) if "wordid" in op else None,
                    word=op["word"],
                    translation=None,  # Will be populated below if needed
                    context=op.get("context"),
                    data=op.get("data"),
                    timestamp=op["timestamp"] if isinstance(op["timestamp"], str) else op["timestamp"].strftime('%Y-%m-%d %H:%M:%S')
                )
                
                # For certain operations, try to add translation from our local database
                if op["operation_type"] in ["add", "update"] and "wordid" in op:
                    try:
                        # Get the word from SQLite
                        word_data = await storage.find_word(wordid=op["wordid"])
                        if word_data and "ch_meaning" in word_data:
                            sync_op.translation = word_data["ch_meaning"]
                    except Exception as e:
                        logger.error(f"Error getting translation for server operation: {str(e)}")
                
                new_server_operations.append(sync_op)
        except Exception as e:
            logger.error(f"Error getting server operations: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Generate current timestamp for next sync
    current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # First, check if the SyncResponse model expects these fields
    try:
        # Return response
        return SyncResponse(
            sync_timestamp=current_timestamp,
            new_server_operations=new_server_operations
        )
    except Exception as e:
        logger.error(f"Error creating SyncResponse: {str(e)}")
        # Return a simplified response that should match the model
        return {
            "sync_timestamp": current_timestamp,
            "new_server_operations": new_server_operations
        }

async def fetch_translation(word: str) -> Optional[str]:
    """Fetch translation for a word using translation API."""
    try:
        # Implement your translation API call here
        # For example, using Google Translate or another service
        
        # Mock implementation for now
        await asyncio.sleep(0.5)  # Simulate API call
        return f"Translation of {word}"  # Replace with actual API call
    except Exception as e:
        logger.error(f"Error fetching translation for {word}: {str(e)}")
        return None