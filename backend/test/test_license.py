# test/test_license.py
import sys
import os
import uuid
import requests
import time
import random
import string

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
BASE_URL = "http://localhost:8000"  # Update if your server runs on a different port


def admin_login():
    """Login as admin and return the access token"""
    # Get admin credentials
    username, password = "admin", "admin"
    
    # Login using form data
    response = requests.post(
        f"{BASE_URL}/login",
        data={
            "username": username,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"Admin login response: {response.status_code} - {response.text}")
    
    # Check if login was successful
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    
    # Extract and return the token
    token_data = response.json()
    assert "access_token" in token_data
    
    return token_data["access_token"]

def test_generate_license():
    """Test generating a single license key as admin"""
    # Login as admin
    admin_token = admin_login()
    
    # Generate a license key
    response = requests.post(
        f"{BASE_URL}/licenses/generate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"License generation response: {response.status_code} - {response.text}")
    
    # Verify successful response
    assert response.status_code == 200, f"License generation failed: {response.text}"
    
    # Verify response structure
    license_data = response.json()
    assert "license_key" in license_data
    assert "message" in license_data
    
    # Verify license key format (AAAA-BBBB-CCCC-DDDD)
    license_key = license_data["license_key"]
    assert len(license_key) == 19
    assert license_key[4] == '-' and license_key[9] == '-' and license_key[14] == '-'
    
    return license_key

def test_generate_bulk_licenses():
    """Test generating multiple license keys at once"""
    # Login as admin
    admin_token = admin_login()
    
    # Use path parameter endpoint instead of body parameter
    response = requests.post(
        f"{BASE_URL}/licenses/generate-bulk/5",  # Use path parameter
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"Bulk license generation response: {response.status_code} - {response.text}")
    
    # Verify successful response
    assert response.status_code == 200, f"Bulk license generation failed: {response.text}"
    
    # Verify response structure
    license_data = response.json()
    assert "licenses" in license_data
    assert "count" in license_data
    assert license_data["count"] == 5
    
    # Verify we got 5 licenses
    licenses = license_data["licenses"]
    assert len(licenses) == 5
    
    return licenses

def test_get_all_licenses():
    """Test retrieving all licenses as admin"""
    # Login as admin
    admin_token = admin_login()
    
    # Get all licenses
    response = requests.get(
        f"{BASE_URL}/licenses/all",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"Get all licenses response: {response.status_code} - {response.text[:200]}...")
    
    # Verify successful response
    assert response.status_code == 200, f"Failed to get all licenses: {response.text}"
    
    # Verify we got a list of licenses
    licenses = response.json()
    assert isinstance(licenses, list)
    
    # If there are licenses, check the structure of the first one
    if licenses:
        first_license = licenses[0]
        assert "license_key" in first_license
        assert "status" in first_license
    
    return licenses

def create_regular_user():
    """Create a regular user for testing"""
    unique_id = str(uuid.uuid4())
    username = f"user_{unique_id}"
    email = f"{username}@example.com"
    password = "userpass123"
    
    # Register user
    response = requests.post(
        f"{BASE_URL}/register", 
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )
    
    print(f"User registration response: {response.status_code} - {response.text}")
    
    # Check if successful
    assert response.status_code == 201, f"Failed to register user: {response.text}"
    
    return username, password

def user_login(username, password):
    """Login as a regular user and return the access token"""
    # Login using form data
    response = requests.post(
        f"{BASE_URL}/login",
        data={
            "username": username,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    print(f"User login response: {response.status_code} - {response.text}")
    
    # Check if login was successful
    assert response.status_code == 200, f"User login failed: {response.text}"
    
    # Extract and return the token
    token_data = response.json()
    assert "access_token" in token_data
    
    return token_data["access_token"]

def test_activate_license():
    """Test activating a license for a user"""
    # Create a user
    username, password = create_regular_user()
    
    # Login as user
    user_token = user_login(username, password)
    
    # Generate a license as admin
    license_key = test_generate_license()
    
    # Activate the license
    response = requests.post(
        f"{BASE_URL}/licenses/activate",
        json={"license_key": license_key},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    print(f"License activation response: {response.status_code} - {response.text}")
    
    # Verify successful response
    assert response.status_code == 200, f"License activation failed: {response.text}"
    
    # Verify message
    result = response.json()
    assert "message" in result
    assert "activated" in result["message"].lower()
    
    return license_key, user_token

def test_license_status():
    """Test checking license status for a user"""
    # Activate a license first
    license_key, user_token = test_activate_license()
    
    # Check license status
    response = requests.get(
        f"{BASE_URL}/licenses/status",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    print(f"License status response: {response.status_code} - {response.text}")
    
    # Verify successful response
    assert response.status_code == 200, f"Failed to get license status: {response.text}"
    
    # Verify status shows the user has a license
    status = response.json()
    assert "has_license" in status
    assert status["has_license"] == True
    assert "license_key" in status
    assert status["license_key"] == license_key

def test_revoke_license():
    """Test revoking a license as admin"""
    # Activate a license first
    license_key, user_token = test_activate_license()
    
    # Login as admin
    admin_token = admin_login()
    
    # Revoke the license
    response = requests.post(
        f"{BASE_URL}/licenses/revoke/{license_key}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    print(f"License revocation response: {response.status_code} - {response.text}")
    
    # Verify successful response
    assert response.status_code == 200, f"License revocation failed: {response.text}"
    
    # Verify revocation message
    result = response.json()
    assert "message" in result
    assert "revoked" in result["message"].lower()
    
    # Check user's license status is now inactive
    response = requests.get(
        f"{BASE_URL}/licenses/status",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    status = response.json()
    assert "has_license" in status
    assert status["has_license"] == False, "User still has an active license after revocation"

def test_upload_license_file():
    """Test uploading a license file"""
    # Create a user
    username, password = create_regular_user()
    
    # Login as user
    user_token = user_login(username, password)
    
    # Generate a license as admin
    license_key = test_generate_license()
    
    # Create a fake license file content with the valid license key
    file_content = f"Test License File\n{license_key}\nInvalid-License-Key"
    
    # Convert to base64
    import base64
    base64_content = base64.b64encode(file_content.encode()).decode()
    
    # Upload the license file
    response = requests.post(
        f"{BASE_URL}/licenses/upload-file",
        json={"file_content": base64_content},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    print(f"License file upload response: {response.status_code} - {response.text}")
    
    # Verify successful response
    assert response.status_code == 200, f"License file upload failed: {response.text}"
    
    # Verify activation message
    result = response.json()
    assert "message" in result
    assert license_key in result["message"] or "activated" in result["message"].lower()

def test_register_with_license():
    """Test registering a new user with a license key"""
    # Generate a license as admin first
    license_key = test_generate_license()
    print(f"Generated license key: {license_key}")

    # Generate unique user details
    unique_id = str(uuid.uuid4())
    username = f"licensed_user_{unique_id}"
    email = f"{username}@example.com"
    password = "password123"

    # Register with license key
    registration_data = {
        "username": username,
        "email": email,
        "password": password,
        "license_key": license_key
    }
    print(f"Registration data: {registration_data}")
    
    response = requests.post(
        f"{BASE_URL}/register",
        json=registration_data
    )

    print(f"Register with license response: {response.status_code} - {response.text}")

    # Check if successful
    assert response.status_code == 201, f"Failed to register with license: {response.text}"
    
    # Check if the registration response already contains license info
    reg_data = response.json()
    print(f"Registration response data: {reg_data}")
    if "has_valid_license" in reg_data and reg_data["has_valid_license"]:
        print("Registration response shows user has valid license")
    
    # Login to get token
    user_token = user_login(username, password)
    print(f"User login successful, got token: {user_token[:20]}...")
    print(f"username: {username}, password: {password}")
    # Check license status
    response = requests.get(
        f"{BASE_URL}/licenses/status",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    print(f"License status response: {response.status_code} - {response.text}")

    # Verify the user has an active license
    status = response.json()
    print(f"Status response fields: {list(status.keys())}")
    
    # Check different possible field names
    has_license = (
        status.get("has_license", False) or 
        status.get("has_valid_license", False) or
        status.get("active", False) or
        status.get("valid", False)
    )
    
    assert has_license, f"User should have an active license. Status response: {status}"
    
    # If we get here, the test passed, so let's return the license key
    # for other tests to use
    return license_key
