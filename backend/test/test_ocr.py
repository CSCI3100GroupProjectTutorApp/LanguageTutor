import pytest
from httpx import AsyncClient
from backend.app.main import app
from unittest.mock import patch

@pytest.mark.asyncio
async def test_extract_text():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and login to get a token
        await client.post("/register", json={"username": "testuser", "password": "testpass"})
        login_response = await client.post("/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["token"]

        # Mock the Google Cloud Vision API response
        with patch("path.to.your.ocr.function", return_value={"text": "hello"}):
            response = await client.post(
                "/extract-text",
                files={"image": ("test.jpg", b"fake-image-data", "image/jpeg")},
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            assert response.json() == {"extracted_text": "hello"}

@pytest.mark.asyncio
async def test_extract_text_invalid_file():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and login to get a token
        await client.post("/register", json={"username": "testuser", "password": "testpass"})
        login_response = await client.post("/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["token"]

        # Test with an invalid file (e.g., non-image)
        response = await client.post(
            "/extract-text",
            files={"image": ("test.txt", b"not-an-image", "text/plain")},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
        
@pytest.mark.asyncio
async def test_ocr_to_word_creation():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register and login to get a token
        await client.post("/register", json={"username": "testuser", "password": "testpass"})
        login_response = await client.post("/login", json={"username": "testuser", "password": "testpass"})
        token = login_response.json()["token"]

        # Mock OCR response
        with patch("path.to.your.ocr.function", return_value={"text": "hello"}):
            ocr_response = await client.post(
                "/extract-text",
                files={"image": ("test.jpg", b"fake-image-data", "image/jpeg")},
                headers={"Authorization": f"Bearer {token}"}
            )
            extracted_text = ocr_response.json()["extracted_text"]

        # Add the extracted text as a word
        add_response = await client.post(
            "/words",
            json={"text": extracted_text, "notes": "from OCR"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert add_response.status_code == 200
        assert add_response.json()["text"] == "hello"