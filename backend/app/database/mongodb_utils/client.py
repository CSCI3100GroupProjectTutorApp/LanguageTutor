# mongodb_utils/client.py
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MongoDBClient:
    """Main client class for MongoDB connections"""
    
    def __init__(self):
        # Get MongoDB connection string from environment variables
        self.uri = os.environ.get("MONGODB_URL", "")
        if not self.uri:
            raise ValueError("MongoDB connection URL not found in environment variables")
            
        self.db_name = os.environ.get("MONGODB_DB_NAME", "languageTutor")
        self.client = None
        self.db = None
        self.async_client = None
        self.async_db = None
        
    def connect(self):
        """Connect to MongoDB database (synchronous)"""
        try:
            self.client = MongoClient(self.uri, server_api=ServerApi('1'))
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
            self.db = self.client[self.db_name]
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
    
    async def connect_async(self):
        """Connect to MongoDB database (asynchronous)"""
        try:
            self.async_client = AsyncIOMotorClient(self.uri, server_api=ServerApi('1'))
            self.async_db = self.async_client[self.db_name]
            # Test connection
            await self.async_db.command("ping")
            print("Successfully connected to MongoDB asynchronously!")
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB asynchronously: {e}")
    
    def close(self):
        """Close the MongoDB connection (synchronous)"""
        if self.client is not None:  
            self.client.close()
            print("MongoDB connection closed")
            self.client = None
            self.db = None
    
    async def close_async(self):
        """Close the MongoDB connection (asynchronous)"""
        if self.async_client is not None:
            self.async_client.close()
            print("Async MongoDB connection closed")
            self.async_client = None
            self.async_db = None
    
    def get_collection(self, collection_name):
        """Get a collection from the database (synchronous)"""
        if self.db is None:  
            self.connect()
        return self.db[collection_name]
    
    async def get_async_collection(self, collection_name):
        """Get a collection from the database (asynchronous)"""
        if self.async_db is None:
            await self.connect_async()
        return self.async_db[collection_name]
    
    def print_collection(self, collection_name):
        """Print all documents in a collection"""
        if self.db is None:  
            self.connect()
        collection = self.db[collection_name]
        for doc in collection.find():
            print(doc)
        return
    
    async def print_async_collection(self, collection_name):
        """Print all documents in a collection asynchronously"""
        if self.async_db is None:
            await self.connect_async()
        collection = self.async_db[collection_name]
        documents = []
        async for doc in collection.find():
            print(doc)
            documents.append(doc)
        return documents
    
    def __enter__(self):
        """Support for with statement context management (synchronous)"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connection is closed when exiting context"""
        self.close()
        return
        
    async def __aenter__(self):
        """Support for async with statement context management"""
        await self.connect_async()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ensure async connection is closed when exiting context"""
        await self.close_async()
        return