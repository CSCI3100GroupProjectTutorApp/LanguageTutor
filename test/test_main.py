# test/test_main.py
import pytest
from httpx import AsyncClient
from backend.app.main import app

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to the Language Tutoring API"}
        
@pytest.mark.asyncio
async def test_db_connectivity(monkeypatch):
    async def mock_command(*args, **kwargs):
        return {"ok": 1}
    async def mock_list_collection_names(*args, **kwargs):
        return ["users", "words"]

    monkeypatch.setattr("backend.app.database.mongodb.get_db", lambda: type('MockDB', (), {
        'command': mock_command,
        'list_collection_names': mock_list_collection_names
    })())

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/test-db")
        assert response.status_code == 200
        assert response.json() == {
            "status": "Connected to MongoDB Atlas",
            "database": "language_tutoring_app",
            "collections": ["users", "words"]
        }