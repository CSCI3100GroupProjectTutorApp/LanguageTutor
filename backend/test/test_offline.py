import pytest
from httpx import AsyncClient
from backend.app.main import app
from backend.app.database.sqlite import get_sqlite_db

@pytest.fixture
def sqlite_db():
    conn = get_sqlite_db(test_mode=True)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS words (word_id TEXT PRIMARY KEY, text TEXT, user_id TEXT, sync_status TEXT)")
    conn.commit()
    yield conn
    conn.close()

@pytest.mark.asyncio
async def test_offline_storage(sqlite_db):
    cursor = sqlite_db.cursor()
    cursor.execute("INSERT INTO words (word_id, text, user_id, sync_status) VALUES (?, ?, ?, ?)", 
                   ("1", "hello", "testuser", "pending"))
    sqlite_db.commit()
    cursor.execute("SELECT * FROM words WHERE word_id = ?", ("1",))
    result = cursor.fetchone()
    assert result[1] == "hello"
    assert result[3] == "pending"

@pytest.mark.asyncio
async def test_sync_data(sqlite_db):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and login to get a token
        await client.post("/register", json={"username": "testuser", "password": "testpass"})
        login_response = await client.post("/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["token"]

        # Add a word to SQLite (offline)
        cursor = sqlite_db.cursor()
        cursor.execute("INSERT INTO words (word_id, text, user_id, sync_status) VALUES (?, ?, ?, ?)", 
                       ("1", "hello", "testuser", "pending"))
        sqlite_db.commit()

        # Simulate sync
        response = await client.post(
            "/sync",
            json=[{"word_id": "1", "text": "hello", "user_id": "testuser"}],
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["synced_count"] == 1

        # Verify the word is in MongoDB
        get_response = await client.get("/words", headers={"Authorization": f"Bearer {token}"})
        assert any(word["text"] == "hello" for word in get_response.json())