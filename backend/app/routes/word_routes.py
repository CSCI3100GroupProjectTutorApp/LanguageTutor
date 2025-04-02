# app/routes/word_routes.py
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from pydantic import BaseModel
from ..dependencies import get_sqlite_storage, get_mongo_client
from ..database.mongodb_utils.word_operation import find_word as mongo_find_word

router = APIRouter(
    prefix="/words",
    tags=["words"],
    responses={404: {"description": "Not found"}},
)

class PartOfSpeech(BaseModel):
    parts: List[str]

class WordBase(BaseModel):
    word: str
    en_meaning: str
    ch_meaning: str
    part_of_speech: List[str]

class WordCreate(WordBase):
    pass

class WordUpdate(BaseModel):
    en_meaning: Optional[str] = None
    ch_meaning: Optional[str] = None
    part_of_speech: Optional[List[str]] = None

class Word(WordBase):
    wordid: int
    wordtime: str
    synced: int

    class Config:
        orm_mode = True

@router.post("/", response_model=Word, status_code=201)
async def create_word(
    word_data: WordCreate,
    storage=Depends(get_sqlite_storage)
):
    """Add a new word to the database (stored locally and synced when online)."""
    try:
        wordid = await storage.add_word(
            word=word_data.word,
            en_meaning=word_data.en_meaning,
            ch_meaning=word_data.ch_meaning,
            part_of_speech=word_data.part_of_speech
        )
        
        # Retrieve the created word
        created_word = await storage.find_word(wordid=wordid)
        if not created_word:
            raise HTTPException(status_code=404, detail="Word not found after creation")
            
        return created_word
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create word: {str(e)}")

@router.get("/", response_model=List[Word])
async def get_words(
    storage=Depends(get_sqlite_storage)
):
    """Get all words from local database."""
    try:
        words = await storage.find_word()
        return words
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve words: {str(e)}")

@router.get("/{word_id}", response_model=Word)
async def get_word(
    word_id: int,
    storage=Depends(get_sqlite_storage)
):
    """Get a specific word by ID."""
    try:
        word = await storage.find_word(wordid=word_id)
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")
        return word
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve word: {str(e)}")

@router.put("/{word_id}", response_model=Word)
async def update_word(
    word_id: int,
    word_data: WordUpdate,
    storage=Depends(get_sqlite_storage)
):
    """Update a word (stored locally and synced when online)."""
    try:
        # Convert model to dict and remove None values
        update_data = {k: v for k, v in word_data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Update the word
        success = await storage.update_word(word_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Word not found or update failed")
        
        # Get the updated word
        updated_word = await storage.find_word(wordid=word_id)
        return updated_word
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update word: {str(e)}")

@router.delete("/{word_id}", status_code=204)
async def delete_word(
    word_id: int,
    storage=Depends(get_sqlite_storage)
):
    """Delete a word (stored locally and synced when online)."""
    try:
        success = await storage.delete_word(wordid=word_id)
        if not success:
            raise HTTPException(status_code=404, detail="Word not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete word: {str(e)}")

@router.get("/search/{query}", response_model=List[Word])
async def search_words(
    query: str,
    storage=Depends(get_sqlite_storage)
):
    """Search for words by partial match."""
    try:
        words = await storage.find_word(word=query, partial_match=True)
        return words
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search words: {str(e)}")

@router.get("/by-word/{exact_word}", response_model=Word)
async def get_word_by_text(
    exact_word: str,
    storage=Depends(get_sqlite_storage)
):
    """Get a word by exact text match."""
    try:
        word = await storage.find_word(word=exact_word)
        if not word:
            raise HTTPException(status_code=404, detail="Word not found")
        return word
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve word: {str(e)}")