# test/test_user_license_flow.py
import sys
import os
import uuid
import requests
import pytest
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
BASE_URL = "http://localhost:8000"  # Update if your server runs on a different port

def create_test_user():
    """Create a test user with a unique username and email"""
    unique_id = str(uuid.uuid4())
    username = f"licenseuser_{unique_id}"
    email = f"{username}@example.com"
    password = "password123"
    
    # Register the user
    response = requests.post(
        f"{BASE_URL}/register", 
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )
    
    if response.status_code != 201:
        pytest.fail(f"Failed to register test user: {response.text}")
    
    return username, email, password

def login_user(username, password):
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/login",
        data={
            "username": username,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        pytest.fail(f"Failed to login: {response.text}")
    
    return response.json()["access_token"]

def get_admin_token():
    """Login as admin and return token"""
    response = requests.post(
        f"{BASE_URL}/login",
        data={
            "username": "admin",
            "password": "admin"  # Replace with your actual admin password if different
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        pytest.fail(f"Failed to login as admin: {response.text}")
    
    return response.json()["access_token"]

def test_user_registration():
    """Test user registration with email"""
    username, email, password = create_test_user()
    
    # Verify by getting the user profile
    token = login_user(username, password)
    profile_response = requests.get(
        f"{BASE_URL}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Print the detailed error response if it's not 200
    if profile_response.status_code != 200:
        print(f"Error getting profile: {profile_response.status_code} - {profile_response.text}")
    
    assert profile_response.status_code == 200, f"Failed to get user profile: {profile_response.text}"
    
    user_data = profile_response.json()
    assert "username" in user_data, "Username field missing in profile response"
    assert "email" in user_data, "Email field missing in profile response" 
    assert "user_id" in user_data, "user_id field missing in profile response"
    assert "is_admin" in user_data, "is_admin field missing in profile response"
    
    assert user_data["username"] == username
    assert user_data["email"] == email
    
    return token, username, email

def test_request_license():
    """Test requesting a license key"""
    # Get an authenticated user
    token, username, email = test_user_registration()
    
    # Request a license key
    license_request_response = requests.post(
        f"{BASE_URL}/users/request-license",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Print response for debugging
    print(f"License request response: {license_request_response.status_code} - {license_request_response.text}")
    
    assert license_request_response.status_code == 200, f"License request failed: {license_request_response.text}"
    
    license_request_data = license_request_response.json()
    assert "success" in license_request_data, "success field missing in response"
    assert license_request_data["success"] == True, "License request was not successful"
    
    # In our modified endpoint, we now always get a license_key in the response
    assert "license_key" in license_request_data, "License key not found in response"
    license_key = license_request_data["license_key"]
    
    # Return the token, username, email, and license key for use in other tests
    return token, username, email, license_key

def test_license_activation():
    """Test license key activation"""
    # Create a user, request a license, and get the license key directly
    token, username, email, license_key = test_request_license()
    
    # Activate the license
    activate_response = requests.post(
        f"{BASE_URL}/users/activate-license",
        json={"license_key": license_key},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert activate_response.status_code == 200
    
    # Verify license status
    status_response = requests.get(
        f"{BASE_URL}/users/license-status",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["has_valid_license"] == True
    
    return token, license_key

def test_protected_data_access():
    """Test access to protected data with valid license"""
    # Get a user with an activated license
    token, _ = test_license_activation()
    
    # Try accessing protected data
    protected_response = requests.get(
        f"{BASE_URL}/users/protected-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert protected_response.status_code == 200
    protected_data = protected_response.json()
    assert "message" in protected_data
    assert "data" in protected_data

def test_complete_user_license_flow():
    """
    Test the complete user flow from registration to protected data access
    """
    # 1. Register a new user
    username, email, password = create_test_user()
    
    # 2. Login to get token
    token = login_user(username, password)
    
    # 3. Request a license key and get it directly from the response
    license_request_response = requests.post(
        f"{BASE_URL}/users/request-license",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert license_request_response.status_code == 200
    license_request_data = license_request_response.json()
    assert "license_key" in license_request_data, "License key not found in response"
    license_key = license_request_data["license_key"]
    
    # 5. Activate the license
    activate_response = requests.post(
        f"{BASE_URL}/users/activate-license",
        json={"license_key": license_key},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert activate_response.status_code == 200
    
    # 6. Verify license is active
    status_response = requests.get(
        f"{BASE_URL}/users/license-status",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["has_valid_license"] == True
    
    # 7. Access protected data
    protected_response = requests.get(
        f"{BASE_URL}/users/protected-data",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert protected_response.status_code == 200
    
    # Success!
    return username, email, license_key

if __name__ == "__main__":
    # Can be run directly with python test_user_license_flow.py
    try:
        username, email, license_key = test_complete_user_license_flow()
        print(f"\nSuccessfully tested complete flow for user {username} with email {email}")
        print(f"License key: {license_key}")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        print(traceback.format_exc()) 