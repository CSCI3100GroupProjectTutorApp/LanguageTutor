from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Dict, Any
from bson import ObjectId


from ..models.word_model import Word, WordCreate, WordUpdate, SyncStatus
from ..auth.auth_handler import get_current_user
from ..database.mongodb_connection import get_mongodb_client, get_db
from ..utils.timezone_utils import get_hk_time
import mongodb_utils.word as mdb

router = APIRouter(prefix="/sync", tags=["Data Synchronization"])

@router.post("", status_code=status.HTTP_200_OK)
async def sync_data(
    sync_data: List[Dict[str, Any]] = Body(...),
    current_user = Depends(get_current_user)
):
    """
    Synchronize offline data with server
    
    - Requires authentication
    - Accepts a list of pending words from local storage
    - Returns a list of processed words with their server IDs
    """
    client = await get_mongodb_client()
    
    # Process each word in the sync request
    results = []
    
    for word_data in sync_data:
        try:
            # Check if we need to create, update, or delete
            word_id = word_data.get("word_id")
            action = word_data.get("action", "create")
            
            # If word has a temporary local ID (string starting with "local_"), 
            # it's a new word that was created offline
            if action == "create" or (word_id and str(word_id).startswith("local_")):
                # Create WordCreate model from the data
                word_create = WordCreate(
                    text=word_data.get("text", ""),
                    translation=word_data.get("translation", ""),
                    notes=word_data.get("notes", ""),
                    part_of_speech=word_data.get("part_of_speech", []),
                    language_pair=word_data.get("language_pair", "en-zh"),
                    proficiency_level=word_data.get("proficiency_level")
                )
                
                # Get parameters for add_word
                word_params = word_create.to_add_word_params()
                
                # Add the word using MongoDB utils
                new_word_id = await mdb.add_word(
                    client,
                    word_params["word"],
                    word_params["en_meaning"],
                    word_params["ch_meaning"],
                    word_params["part_of_speech"]
                )
                
                # Update the word document with user ID
                await client.async_db.words.update_one(
                    {"wordid": new_word_id},
                    {"$set": {"user_id": str(current_user.user_id)}}
                )
                
                # Return the result with the local_id and new server ID
                results.append({
                    "local_id": word_id,
                    "server_id": str(new_word_id),
                    "action": "created",
                    "success": True
                })
                
            elif action == "update" and word_id and not str(word_id).startswith("local_"):
                # Convert to int since our MongoDB uses integer IDs
                try:
                    word_id_int = int(word_id)
                except ValueError:
                    results.append({
                        "word_id": word_id,
                        "action": "update",
                        "success": False,
                        "error": "Invalid word ID format"
                    })
                    continue
                
                # Check if word exists and belongs to user
                existing_word = await mdb.find_word(client, wordid=word_id_int)
                
                if not existing_word:
                    results.append({
                        "word_id": word_id,
                        "action": "update",
                        "success": False,
                        "error": "Word not found"
                    })
                    continue
                    
                if str(existing_word.get("user_id", "")) != str(current_user.user_id):
                    results.append({
                        "word_id": word_id,
                        "action": "update",
                        "success": False,
                        "error": "Not authorized to update this word"
                    })
                    continue
                
                # Create WordUpdate model from the data
                word_update = WordUpdate(
                    text=word_data.get("text"),
                    translation=word_data.get("translation"),
                    notes=word_data.get("notes"),
                    part_of_speech=word_data.get("part_of_speech"),
                    proficiency_level=word_data.get("proficiency_level")
                )
                
                # Get update data
                update_data = word_update.to_update_data()
                
                # Update the word
                success = await mdb.update_word(client, word_id_int, update_data)
                
                results.append({
                    "word_id": word_id,
                    "action": "updated",
                    "success": success
                })
                
            elif action == "delete" and word_id and not str(word_id).startswith("local_"):
                # Convert to int since our MongoDB uses integer IDs
                try:
                    word_id_int = int(word_id)
                except ValueError:
                    results.append({
                        "word_id": word_id,
                        "action": "delete",
                        "success": False,
                        "error": "Invalid word ID format"
                    })
                    continue
                
                # Check if word exists and belongs to user
                existing_word = await mdb.find_word(client, wordid=word_id_int)
                
                if not existing_word:
                    # Word doesn't exist - consider it "successfully" deleted
                    results.append({
                        "word_id": word_id,
                        "action": "deleted",
                        "success": True
                    })
                    continue
                    
                if str(existing_word.get("user_id", "")) != str(current_user.user_id):
                    results.append({
                        "word_id": word_id,
                        "action": "delete",
                        "success": False,
                        "error": "Not authorized to delete this word"
                    })
                    continue
                
                # Delete the word
                success = await mdb.delete_word(client, wordid=word_id_int)
                
                results.append({
                    "word_id": word_id,
                    "action": "deleted",
                    "success": success
                })
                
        except Exception as e:
            # Log the error and continue processing other words
            print(f"Error processing sync item: {str(e)}")
            results.append({
                "word_id": word_data.get("word_id", "unknown"),
                "action": word_data.get("action", "unknown"),
                "success": False,
                "error": str(e)
            })
    
    return {
        "timestamp": get_hk_time().isoformat(),
        "results": results
    } 