# test/test_auth.py
import sys
import os
import uuid
import requests

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
BASE_URL = "http://localhost:8000"  # Update if your server runs on a different port

def test_register_user():
    """Test user registration and return the credentials for other tests"""
    unique_id = str(uuid.uuid4())
    username = f"testuser_{unique_id}"
    email = f"{username}@example.com"
    password = "password123"
    
    # Register a new user directly using requests
    response = requests.post(
        f"{BASE_URL}/register", 
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )
    
    print(f"Register response: {response.status_code} - {response.text}")
    
    # Check if successful
    assert response.status_code == 201, f"Failed to register: {response.text}"
    
    # Return the credentials for other tests to use
    return username, password

def test_login_user():
    """Test user login with valid credentials"""
    # Get a fresh username/password - don't rely on previous test
    username, password = test_register_user()
    
    # Login using form data (required for OAuth2)
    response = requests.post(
        f"{BASE_URL}/login",
        data={
            "username": username,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"Login response: {response.status_code} - {response.text}")
    
    # Verify login was successful
    assert response.status_code == 200, f"Login failed: {response.text}"
    
    # Verify we got a token
    token_data = response.json()
    assert "access_token" in token_data
    assert "token_type" in token_data
    assert token_data["token_type"] == "bearer"
    
    return token_data["access_token"]

def test_login_invalid_credentials():
    """Test login with invalid credentials should fail"""
    # Use form data with invalid credentials
    response = requests.post(
        f"{BASE_URL}/login",
        data={
            "username": "nonexistent_user",
            "password": "wrongpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"Invalid login response: {response.status_code} - {response.text}")
    
    # Should return 401 Unauthorized
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"

def test_user_profile():
    """Test fetching the user profile with a valid token"""
    # First login to get a token
    token = test_login_user()
    
    # Get the user profile
    response = requests.get(
        f"{BASE_URL}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Profile response: {response.status_code} - {response.text}")
    
    # Verify successful response
    assert response.status_code == 200
    
    # Verify the user data structure
    user_data = response.json()
    assert "username" in user_data
    assert "email" in user_data
    assert "user_id" in user_data
    
    print(f"User profile: {user_data}")

if __name__ == "__main__":
    # Can be run directly with python test_auth.py
    try:
        print("Testing user registration...")
        username, password = test_register_user()
        
        print("\nTesting user login...")
        token = test_login_user()
        
        print("\nTesting invalid login...")
        test_login_invalid_credentials()
        
        print("\nTesting user profile...")
        test_user_profile()
        
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        print(traceback.format_exc())