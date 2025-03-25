"""
MongoDB connection utilities for the language tutoring API.
This module integrates the MongoDBClient from mongodb_utils.
"""
import os
import sys
from pathlib import Path

# Add the root directory to the Python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(ROOT_DIR))

from mongodb_utils.client import MongoDBClient
from ..config import settings

# Global client instance
mongodb_client = None
db = None

async def get_mongodb_client():
    """Get or create the MongoDB client"""
    global mongodb_client
    if mongodb_client is None:
        mongodb_client = MongoDBClient()
        await mongodb_client.connect_async()
    return mongodb_client

async def get_db():
    """Get the database instance"""
    client = await get_mongodb_client()
    return client.async_db

async def connect_to_mongodb():
    """Connect to MongoDB Atlas"""
    global mongodb_client, db
    try:
        mongodb_client = MongoDBClient()
        await mongodb_client.connect_async()
        db = mongodb_client.async_db
        print("Successfully connected to MongoDB using integrated client!")
        return db
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        raise e

async def close_mongodb_connection():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        await mongodb_client.close_async()
        print("MongoDB connection closed") 