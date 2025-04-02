"""
Dependencies for FastAPI dependency injection.
"""
from fastapi import Depends
from .database.sqlite.sqlite_storage import WordStorage
from .database.mongodb_connection import get_mongodb_client

# Create a singleton instance of the WordStorage
# This is more efficient than creating a new one for each request
_word_storage = None

async def get_sqlite_storage():
    """Get the SQLite word storage instance."""
    global _word_storage
    if _word_storage is None:
        _word_storage = WordStorage()
        # Initialize the database asynchronously
        await _word_storage.initialize_db()
    return _word_storage

async def get_mongo_client():
    """Get the MongoDB client instance."""
    return await get_mongodb_client()