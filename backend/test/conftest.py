# test/conftest.py
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import motor.motor_asyncio
from app.config import settings

@pytest.fixture
async def mongodb():
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    # Clear the users collection before each test
    await db.users.delete_many({})
    yield db
    # Clean up after each test
    await db.users.delete_many({})

@pytest.fixture
def client():
    from app.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)