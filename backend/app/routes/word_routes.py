from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from bson import ObjectId

from ..models.word_model import Word, WordCreate, WordUpdate
from ..auth.auth_handler import get_current_user
from ..database.mongodb_connection import get_mongodb_client, get_db
from ..utils.timezone_utils import get_hk_time
import mongodb_utils.word as mdb

router = APIRouter(prefix="/words", tags=["Vocabulary Management"])

@router.post("", response_model=Word, status_code=status.HTTP_201_CREATED)
async def add_word(word_data: WordCreate, current_user = Depends(get_current_user)):
    """
    Add a new vocabulary word
    
    - Requires authentication
    - Returns the created word
    """
    try:
        client = await get_mongodb_client()
        
        # Get parameters for add_word
        word_params = word_data.to_add_word_params()
        
        # Add the word with MongoDB utils
        wordid = await mdb.add_word(
            client, 
            word_params["word"],
            word_params["en_meaning"],
            word_params["ch_meaning"],
            word_params["part_of_speech"]
        )
        
        # Update the word with user ID
        await client.async_db.words.update_one(
            {"wordid": wordid},
            {"$set": {"user_id": str(current_user.user_id)}}
        )
        
        # Get the newly created word
        word_doc = await mdb.find_word(client, wordid=wordid)
        
        # Use the from_mongodb_dict method to convert to Word model
        word = Word.from_mongodb_dict(word_doc)
        
        # Set additional fields not in MongoDB
        word.language_pair = word_data.language_pair
        word.proficiency_level = word_data.proficiency_level
        
        return word
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding word: {str(e)}"
        )

@router.get("", response_model=List[Word])
async def get_words(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """
    Get all words for the current user
    
    - Supports pagination with skip/limit
    - Requires authentication
    """
    try:
        client = await get_mongodb_client()
        
        # Get words from the database
        all_words = await mdb.find_word(client)
        
        # Filter by current user and paginate
        user_words = [
            word for word in all_words 
            if str(word.get("user_id", "")) == str(current_user.user_id)
        ]
        
        paginated_words = user_words[skip:skip+limit]
        
        # Use the from_mongodb_dict method to convert to Word models
        return [Word.from_mongodb_dict(word) for word in paginated_words]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving words: {str(e)}"
        )

@router.get("/{word_id}", response_model=Word)
async def get_word(word_id: int, current_user = Depends(get_current_user)):
    """
    Get a specific word by ID
    
    - Requires authentication
    - Returns 404 if word not found
    """
    try:
        client = await get_mongodb_client()
        
        # Get the word
        word_doc = await mdb.find_word(client, wordid=word_id)
        
        if not word_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Word with ID {word_id} not found"
            )
            
        # Check if the word belongs to the current user
        if str(word_doc.get("user_id", "")) != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this word"
            )
            
        # Use the from_mongodb_dict method to convert to Word model
        return Word.from_mongodb_dict(word_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving word: {str(e)}"
        )

@router.put("/{word_id}", response_model=Word)
async def update_word(
    word_id: int,
    word_update: WordUpdate,
    current_user = Depends(get_current_user)
):
    """
    Update a word
    
    - Requires authentication
    - Returns the updated word
    """
    try:
        client = await get_mongodb_client()
        
        # Get the word to check if it exists and belongs to the user
        word_doc = await mdb.find_word(client, wordid=word_id)
        
        if not word_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Word with ID {word_id} not found"
            )
            
        # Check if the word belongs to the current user
        if str(word_doc.get("user_id", "")) != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this word"
            )
            
        # Get update data using the to_update_data method
        update_data = word_update.to_update_data()
        
        # Update the word
        success = await mdb.update_word(client, word_id, update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update word"
            )
            
        # Get the updated word
        updated_word_doc = await mdb.find_word(client, wordid=word_id)
        
        # Use the from_mongodb_dict method to convert to Word model
        word = Word.from_mongodb_dict(updated_word_doc)
        
        # Update fields not stored in MongoDB
        if word_update.proficiency_level is not None:
            word.proficiency_level = word_update.proficiency_level
            
        return word
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating word: {str(e)}"
        )

@router.delete("/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_word(word_id: int, current_user = Depends(get_current_user)):
    """
    Delete a word
    
    - Requires authentication
    - Returns 204 No Content on success
    """
    try:
        client = await get_mongodb_client()
        
        # Get the word to check if it exists and belongs to the user
        word_doc = await mdb.find_word(client, wordid=word_id)
        
        if not word_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Word with ID {word_id} not found"
            )
            
        # Check if the word belongs to the current user
        if str(word_doc.get("user_id", "")) != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this word"
            )
            
        # Delete the word
        success = await mdb.delete_word(client, wordid=word_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete word"
            )
            
        # Return 204 No Content (happens automatically with status_code)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting word: {str(e)}"
        ) 