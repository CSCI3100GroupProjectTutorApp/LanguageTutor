# test/test_auth.py
import sys
import os
import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

client = TestClient(app)

def test_register_user():
    unique_id = str(uuid.uuid4())  # Generate a unique ID
    response = client.post("/register", json={
        "username": f"testuser_{unique_id}",
        "email": f"testuser_{unique_id}@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    assert response.json()["message"] == "User registered successfully"