import pytest
from httpx import AsyncClient
from backend.app.main import app

@pytest.mark.asyncio
async def test_register_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/register", json={"username": "testuser", "password": "testpass"})
        assert response.status_code == 200
        assert response.json()["message"] == "User registered successfully"