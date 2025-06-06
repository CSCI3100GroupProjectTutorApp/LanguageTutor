# test/test_auth.py
import sys
import os
import pytest
import uuid
from fastapi.testclient import TestClient
from backend.app.main import app

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

client = TestClient(app)

def test_register_user():
    unique_id = str(uuid.uuid4())
    username = f"testuser_{unique_id}"
    email = f"{username}@example.com"
    
    response = client.post("/register", json={
        "username": username,
        "email": email,
        "password": "password123"
    })
    
    # Print response for debugging
    print(f"Register response: {response.status_code} - {response.text}")
    
    # Check status code
    assert response.status_code == 201
    
    # Validate response structure based on UserResponse model
    response_data = response.json()
    assert response_data["username"] == username
    assert response_data["email"] == email
    assert "user_id" in response_data
    assert response_data["is_active"] == True
    assert "created_at" in response_data