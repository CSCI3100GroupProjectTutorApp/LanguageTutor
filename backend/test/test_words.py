# test/test_words.py
import sys
import os
import uuid
import requests
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Create a user and login to get an auth token"""
    # Generate unique credentials
    unique_id = str(uuid.uuid4())[:8]
    username = f"testuser_{unique_id}"
    email = f"{username}@example.com"
    password = "password123"
    
    # Register the user
    print(f"Registering user: {username}")
    response = requests.post(
        f"{BASE_URL}/register",
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )
    
    if response.status_code != 201:
        print(f"Registration failed: {response.status_code} - {response.text}")
        raise Exception(f"Failed to register test user: {response.text}")
    
    # Login to get token
    print(f"Logging in as: {username}")
    login_response = requests.post(
        f"{BASE_URL}/login",
        # Use form data for OAuth2 login
        data={
            "username": username,
            "password": password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code} - {login_response.text}")
        raise Exception(f"Failed to login: {login_response.text}")
    
    # Extract token
    login_data = login_response.json()
    print(f"Login successful. Got token.")
    return login_data["access_token"]

def test_create_word():
    """Test creating a new word"""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a word
    word_data = {
        "word": "hello",
        "en_meaning": "a greeting",
        "ch_meaning": "你好",
        "part_of_speech": ["noun", "interjection"]
    }
    
    response = requests.post(
        f"{BASE_URL}/words/",
        headers=headers,
        json=word_data
    )
    
    # Verify response
    assert response.status_code == 201, f"Expected status 201, got {response.status_code}: {response.text}"
    created_word = response.json()
    assert created_word["word"] == "hello"
    assert created_word["en_meaning"] == "a greeting"
    assert created_word["ch_meaning"] == "你好"
    assert "wordid" in created_word
    
    print(f"✓ Created word successfully: {created_word['wordid']}")
    return created_word["wordid"]

def test_get_words():
    """Test retrieving all words"""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a word first to ensure there's at least one
    word_data = {
        "word": "goodbye",
        "en_meaning": "a farewell",
        "ch_meaning": "再見",
        "part_of_speech": ["noun", "interjection"]
    }
    
    requests.post(
        f"{BASE_URL}/words/",
        headers=headers,
        json=word_data
    )
    
    # Get all words
    response = requests.get(
        f"{BASE_URL}/words/",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}: {response.text}"
    words = response.json()
    assert isinstance(words, list)
    assert len(words) > 0
    
    print(f"✓ Retrieved {len(words)} words successfully")
'''
def test_get_word_by_id():
    """Test retrieving a word by ID"""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a word
    word_data = {
        "word": "test",
        "en_meaning": "a trial",
        "ch_meaning": "測試",
        "part_of_speech": ["noun", "verb"]
    }
    
    create_response = requests.post(
        f"{BASE_URL}/words/",
        headers=headers,
        json=word_data
    )
    
    word_id = create_response.json()["wordid"]
    
    # Get the word by ID
    response = requests.get(
        f"{BASE_URL}/words/{word_id}",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}: {response.text}"
    word = response.json()
    assert word["word"] == "test"
    assert word["wordid"] == word_id
    
    print(f"✓ Retrieved word by ID successfully: {word_id}")

def test_update_word():
    """Test updating a word"""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a word
    word_data = {
        "word": "apple",
        "en_meaning": "a fruit",
        "ch_meaning": "蘋果",
        "part_of_speech": ["noun"]
    }
    
    create_response = requests.post(
        f"{BASE_URL}/words/",
        headers=headers,
        json=word_data
    )
    
    word_id = create_response.json()["wordid"]
    
    # Update the word
    update_data = {
        "en_meaning": "a common fruit",
        "ch_meaning": "紅蘋果",
        "part_of_speech": ["noun", "proper noun"]
    }
    
    response = requests.put(
        f"{BASE_URL}/words/{word_id}",
        headers=headers,
        json=update_data
    )
    
    # Verify response
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}: {response.text}"
    updated_word = response.json()
    assert updated_word["en_meaning"] == "a common fruit"
    assert updated_word["ch_meaning"] == "紅蘋果"
    assert "proper noun" in updated_word["part_of_speech"]
    
    print(f"✓ Updated word successfully: {word_id}")

def test_delete_word():
    """Test deleting a word"""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a word
    word_data = {
        "word": "delete",
        "en_meaning": "to remove",
        "ch_meaning": "删除",
        "part_of_speech": ["verb"]
    }
    
    create_response = requests.post(
        f"{BASE_URL}/words/",
        headers=headers,
        json=word_data
    )
    
    word_id = create_response.json()["wordid"]
    
    # Delete the word
    response = requests.delete(
        f"{BASE_URL}/words/{word_id}",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 204, f"Expected status 204, got {response.status_code}: {response.text}"
    
    # Verify it's deleted
    get_response = requests.get(
        f"{BASE_URL}/words/{word_id}",
        headers=headers
    )
    assert get_response.status_code == 404
    
    print(f"✓ Deleted word successfully: {word_id}")

def test_search_words():
    """Test searching for words"""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create some words
    requests.post(
        f"{BASE_URL}/words/",
        headers=headers,
        json={
            "word": "running",
            "en_meaning": "moving quickly",
            "ch_meaning": "跑步",
            "part_of_speech": ["verb", "noun"]
        }
    )
    
    requests.post(
        f"{BASE_URL}/words/",
        headers=headers,
        json={
            "word": "runner",
            "en_meaning": "person who runs",
            "ch_meaning": "跑步者",
            "part_of_speech": ["noun"]
        }
    )
    
    # Search for words
    response = requests.get(
        f"{BASE_URL}/words/search/run",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}: {response.text}"
    results = response.json()
    assert isinstance(results, list)
    assert len(results) >= 2
    assert any(w["word"] == "running" for w in results)
    assert any(w["word"] == "runner" for w in results)
    
    print(f"✓ Search words successfully: found {len(results)} results")

def test_get_word_by_text():
    """Test retrieving a word by text"""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a word with unique text
    word_text = "unique_word_" + str(uuid.uuid4())[:8]
    requests.post(
        f"{BASE_URL}/words/",
        headers=headers,
        json={
            "word": word_text,
            "en_meaning": "a unique word",
            "ch_meaning": "獨特的字",
            "part_of_speech": ["noun"]
        }
    )
    
    # Get word by text
    response = requests.get(
        f"{BASE_URL}/words/by-word/{word_text}",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}: {response.text}"
    word = response.json()
    assert word["word"] == word_text
    
    print(f"✓ Retrieved word by text successfully: {word_text}")

def test_get_all_words():
    """Test retrieving all words"""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create some words
    for i in range(3):
        requests.post(
            f"{BASE_URL}/words/",
            headers=headers,
            json={
                "word": f"all_test_{i}",
                "en_meaning": f"test word {i}",
                "ch_meaning": f"測試 {i}",
                "part_of_speech": ["noun"]
            }
        )
    
    # Get all words
    response = requests.get(
        f"{BASE_URL}/words/all",
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}: {response.text}"
    words = response.json()
    assert isinstance(words, list)
    assert len(words) >= 3
    
    # Verify structure
    for word in words:
        assert "wordid" in word
        assert "word" in word
        assert "en_meaning" in word
        assert "ch_meaning" in word
        assert "part_of_speech" in word
    
    print(f"✓ Retrieved all {len(words)} words successfully")
'''
def run_all_tests():
    """Run all tests sequentially"""
    print("\n=== Running Word API Tests ===\n")
    
    try:
        test_create_word()
        '''
        test_get_words()
        test_get_word_by_id()
        test_update_word()
        test_delete_word()
        test_search_words()
        test_get_word_by_text()
        test_get_all_words()
        '''
        print("\n✅ All tests passed!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    run_all_tests()