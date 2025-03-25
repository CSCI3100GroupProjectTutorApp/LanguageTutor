"""
Database initialization script
Creates required collections and indices
"""
from .mongodb_connection import get_db
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    """Initialize database by creating collections and indices"""
    try:
        logger.info("Initializing database...")
        db = await get_db()
        
        # List of collections that should exist
        required_collections = ['users', 'words']
        
        # Get existing collections
        existing_collections = await db.list_collection_names()
        logger.info(f"Existing collections: {existing_collections}")
        
        # Create missing collections
        for collection in required_collections:
            if collection not in existing_collections:
                logger.info(f"Creating collection: {collection}")
                await db.create_collection(collection)
        
        # Create indices for users collection
        logger.info("Creating indices for users collection...")
        await db.users.create_index("username", unique=True)
        await db.users.create_index("email", unique=True)
        
        # Create indices for words collection if needed
        logger.info("Creating indices for words collection...")
        await db.words.create_index("user_id")
        
        logger.info("Database initialization complete!")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e 