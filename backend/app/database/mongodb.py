from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from ..config import settings

# These variables need to be properly exposed
client = None
db = None

async def connect_to_mongodb():
    """Connect to MongoDB Atlas"""
    global client, db
    
    print(f"Attempting to connect to MongoDB using URL: {settings.MONGODB_URL.split('@')[1] if settings.MONGODB_URL else 'No URL found'}")
    
    try:
        # Create client
        client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000
        )
        
        # Set the database
        db = client.language_tutoring_app
        
        # Test connection
        await db.command("ping")
        
        print("Successfully connected to MongoDB Atlas!")
        return db
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        raise e

async def close_mongodb_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        print("MongoDB connection closed")

# Add this function to get db from other modules
def get_db():
    """Return database instance"""
    if db is None:
        raise Exception("Database not initialized. Call connect_to_mongodb first.")
    return db