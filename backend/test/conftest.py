# app/tests/conftest.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
from datetime import datetime
import logging
from bson import ObjectId

from app.main import app
from app.database.mongodb_connection import get_db
from app.auth.auth_handler import get_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test database settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DATABASE", "test_db")

# Create a single event loop for all tests
@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for all tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

# Create a single client for the session
@pytest.fixture(scope="session")
async def mongodb_client(event_loop):
    """MongoDB client fixture."""
    logger.info(f"Connecting to MongoDB at {MONGODB_URL}")
    client = AsyncIOMotorClient(MONGODB_URL, io_loop=event_loop)
    
    # Verify connection works
    try:
        await client.admin.command('ping')
        logger.info("MongoDB connection successful!")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise
    
    yield client
    client.close()

@pytest.fixture
async def test_db(mongodb_client):
    """Test database fixture."""
    db = mongodb_client[DB_NAME]
    # Clear existing data
    collections = await db.list_collection_names()
    for collection in collections:
        await db.drop_collection(collection)
    yield db

@pytest.fixture(scope="function")
def override_get_db(test_db):
    """Return a callable that will return the test database."""
    async def _override_get_db():
        yield test_db
    return _override_get_db

@pytest.fixture
def client(override_get_db):
    """Get FastAPI test client with override for get_db."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides = {}

@pytest.fixture
async def test_admin(test_db):
    """Create a test admin user."""
    admin_data = {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": get_password_hash("adminpass"),
        "is_active": True,
        "is_admin": True,
        "created_at": datetime.now(),
        "has_valid_license": True
    }
    
    # Make sure to delete the existing admin if it exists
    await test_db.users.delete_one({"username": "admin"})
    
    result = await test_db.users.insert_one(admin_data)
    admin_id = result.inserted_id
    
    # Update the document to include the user_id field
    await test_db.users.update_one(
        {"_id": admin_id},
        {"$set": {"user_id": str(admin_id)}}
    )
    
    logger.info(f"Created test admin with ID: {admin_id}")
    return {"username": "admin", "password": "adminpass"}

@pytest.fixture
def admin_token(client, test_admin):
    """Get admin token for tests."""
    response = client.post(
        "/login",
        data={"username": test_admin["username"], "password": test_admin["password"]}
    )
    token = response.json()["access_token"]
    logger.info(f"Got admin token: {token[:20]}...")
    return token