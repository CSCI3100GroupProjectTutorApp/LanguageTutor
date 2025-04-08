# test/test_words.py
import sys
import os
import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def auth_token(client):
    # Register a user
    unique_id = str(uuid.uuid4())
    client.post("/register", json={
        "username": f"testuser_{unique_id}",
        "email": f"testuser_{unique_id}@example.com",
        "password": "password123"
    })
    # Login to get a token
    login_response = client.post("/login", json={
        "username": f"testuser_{unique_id}",
        "password": "password123"
    })
    print(f"Login response: {login_response.json()}")
    return login_response.json()["access_token"]

def test_create_word(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.post("/words", json={
        "text": "hello",
        "translation": "hola",
        "notes": "Spanish greeting"
    }, headers=headers)
    assert response.status_code == 201
    assert "word_id" in response.json()
    return response.json()["word_id"]

def test_read_words(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Create a word first
    client.post("/words", json={
        "text": "hello",
        "translation": "hola",
        "notes": "Spanish greeting"
    }, headers=headers)
    # Read words
    response = client.get("/words", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_update_word(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Create a word
    create_response = client.post("/words", json={
        "text": "hello",
        "translation": "hola",
        "notes": "Spanish greeting"
    }, headers=headers)
    word_id = create_response.json()["word_id"]
    # Update the word
    response = client.put(f"/words/{word_id}", json={
        "text": "hello",
        "translation": "saludos",
        "notes": "Updated Spanish greeting"
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["translation"] == "saludos"

def test_delete_word(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Create a word
    create_response = client.post("/words", json={
        "text": "hello",
        "translation": "hola",
        "notes": "Spanish greeting"
    }, headers=headers)
    word_id = create_response.json()["word_id"]
    # Delete the word
    response = client.delete(f"/words/{word_id}", headers=headers)
    assert response.status_code == 200
    assert "message" in response.json()