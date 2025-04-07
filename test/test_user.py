import pytest
from httpx import AsyncClient
from backend.app.main import app

@pytest.mark.asyncio
async def test_add_word():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and login to get a token
        await client.post("/register", json={"username": "testuser", "password": "testpass"})
        login_response = await client.post("/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["token"]

        # Add a word
        response = await client.post("/words", json={"text": "hello", "notes": "greeting"}, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert "word_id" in response.json()
        assert response.json()["text"] == "hello"

@pytest.mark.asyncio
async def test_get_words():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register, login, and add a word
        await client.post("/register", json={"username": "testuser", "password": "testpass"})
        login_response = await client.post("/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["token"]
        await client.post("/words", json={"text": "hello", "notes": "greeting"}, headers={"Authorization": f"Bearer {token}"})

        # Retrieve words
        response = await client.get("/words", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0
        assert response.json()[0]["text"] == "hello"

@pytest.mark.asyncio
async def test_get_word_by_id():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register, login, and add a word
        await client.post("/register", json={"username": "testuser", "password": "testpass"})
        login_response = await client.post("/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["token"]
        add_response = await client.post("/words", json={"text": "hello", "notes": "greeting"}, headers={"Authorization": f"Bearer {token}"})
        word_id = add_response.json()["word_id"]

        # Retrieve the specific word
        response = await client.get(f"/words/{word_id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["word_id"] == word_id
        assert response.json()["text"] == "hello"

@pytest.mark.asyncio
async def test_update_word():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register, login, and add a word
        await client.post("/register", json={"username": "testuser", "password": "testpass"})
        login_response = await client.post("/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["token"]
        add_response = await client.post("/words", json={"text": "hello", "notes": "greeting"}, headers={"Authorization": f"Bearer {token}"})
        word_id = add_response.json()["word_id"]

        # Update the word
        response = await client.put(f"/words/{word_id}", json={"text": "hi", "notes": "updated greeting"}, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["message"] == "Word updated successfully"

        # Verify the update
        get_response = await client.get(f"/words/{word_id}", headers={"Authorization": f"Bearer {token}"})
        assert get_response.json()["text"] == "hi"

@pytest.mark.asyncio
async def test_delete_word():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register, login, and add a word
        await client.post("/register", json={"username": "testuser", "password": "testpass"})
        login_response = await client.post("/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["token"]
        add_response = await client.post("/words", json={"text": "hello", "notes": "greeting"}, headers={"Authorization": f"Bearer {token}"})
        word_id = add_response.json()["word_id"]

        # Delete the word
        response = await client.delete(f"/words/{word_id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["message"] == "Word deleted successfully"

        # Verify deletion
        get_response = await client.get(f"/words/{word_id}", headers={"Authorization": f"Bearer {token}"})
        assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_word_database():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register, login, and add a word
        await client.post("/register", json={"username": "testuser", "password": "testpass"})
        login_response = await client.post("/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["token"]
        await client.post("/words", json={"text": "hello", "notes": "greeting"}, headers={"Authorization": f"Bearer {token}"})

        # Retrieve words from the database
        response = await client.get("/words", headers={"Authorization": f"Bearer {token}"})
        assert len(response.json()) > 0
        assert response.json()[0]["text"] == "hello"
        
@pytest.mark.asyncio
async def test_add_word_invalid_data():
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/register", json={"username": "testuser", "password": "testpass"})
        login_response = await client.post("/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["token"]

        # Test with empty text
        response = await client.post("/words", json={"text": "", "notes": "greeting"}, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 400
        assert "text cannot be empty" in response.json()["detail"]
        
@pytest.mark.asyncio
async def test_words_unauthorized():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/words")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]