import requests
import json
from datetime import datetime
import traceback

# Server configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin"

def test_sync_endpoint():
    try:
        # Step 1: Login to get an access token
        print("Logging in...")
        response = requests.post(
            f"{BASE_URL}/login",
            data={"username": USERNAME, "password": PASSWORD}
        )
        
        if response.status_code != 200:
            print(f"Login failed with status {response.status_code}")
            print(response.text)
            return
        
        token_data = response.json()
        access_token = token_data["access_token"]
        print(f"Successfully logged in, got token")
        
        # Step 2: Get user information to verify user_id
        print("\nGetting user information...")
        response = requests.get(
            f"{BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code != 200:
            print(f"Failed to get user info with status {response.status_code}")
            print(response.text)
            return
        
        user_data = response.json()
        print(f"User data: {json.dumps(user_data, indent=2)}")
        
        # Get the user_id from the API response
        if "user_id" in user_data:
            user_id = user_data["user_id"]
            print(f"Using user_id: {user_id}")
        else:
            print("Could not find user_id in response")
            return
         
        # Step 3: Try the basic sync at correct endpoint
        print("\nTrying sync at endpoint: /sync/")
        
        simple_sync_data = {
            "user_id": user_id,
            "device_id": "test_device_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "last_sync_timestamp": None,
            "operations": []  # Empty operations list for initial test
        }
        
        response = requests.post(
            f"{BASE_URL}/sync/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=simple_sync_data
        )
        
        print(f"Sync response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Sync response: {json.dumps(result, indent=2)}")
            print("Empty sync successful!")
            
            # Step 4: Try adding a word with sync
            print("\nTrying to add a word with sync...")
            
            # Create a timestamp for the operation
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            word_sync_data = {
                "user_id": user_id,
                "device_id": "test_device_" + datetime.now().strftime("%Y%m%d%H%M%S"),
                "last_sync_timestamp": None,
                "operations": [
                    {
                        "operation": "add",
                        "word": "simple",
                        "translation": "簡單",
                        "timestamp": current_timestamp,
                        "data": {
                            "en_meaning": "Easy to understand or do",
                            "part_of_speech": ["adjective"]
                        }
                    }
                ]
            }
            
            response = requests.post(
                f"{BASE_URL}/sync/",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=word_sync_data
            )
            
            print(f"Word sync response status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Word sync response: {json.dumps(result, indent=2)}")
                print("Word sync successful!")
                
                # Step 5: Check if word was added
                print("\nChecking if word was added using /words/ endpoint...")
                
                response = requests.get(
                    f"{BASE_URL}/words/",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                print(f"Get words response status: {response.status_code}")
                if response.status_code == 200:
                    words = response.json()
                    print(f"Total words: {len(words)}")
                    
                    # Look for our added word
                    found = False
                    for word in words:
                        if word.get("word") == "simple":
                            found = True
                            print(f"Found added word: {json.dumps(word, indent=2)}")
                            break
                    
                    if not found:
                        print("Added word 'simple' was not found in the words list!")
                else:
                    print(f"Failed to get words: {response.text}")
            else:
                print(f"Word sync failed: {response.text}")
                print("\nPossible issues:")
                print("1. Data model validation error")
                print("2. Database connection issue")
                print("3. Sqlite error in add_word function")
                print("4. Error in syncing with MongoDB")
                
                # Try with a different model format
                print("\nTrying with simplified data model...")
                simplified_op = {
                    "user_id": user_id,
                    "device_id": "test_device_" + datetime.now().strftime("%Y%m%d%H%M%S"),
                    "last_sync_timestamp": None,
                    "operations": [
                        {
                            "operation": "add",
                            "word": "test",
                            "translation": "测试",
                            "timestamp": current_timestamp,
                            "context": None,
                            "wordid": None,
                            "data": {
                                "en_meaning": "A procedure for critical evaluation",
                                "part_of_speech": ["noun"]
                            }
                        }
                    ]
                }
                
                response = requests.post(
                    f"{BASE_URL}/sync/",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json=simplified_op
                )
                
                print(f"Simplified sync response status: {response.status_code}")
                if response.status_code == 200:
                    print("Simplified sync worked! Issue is with data model.")
                    print(response.text)
                else:
                    print(f"Simplified sync also failed: {response.text}")
        else:
            print(f"Empty sync failed: {response.text}")
            
            # Try with a common error
            if "token" in response.text.lower():
                print("\nPossible token issue. Check your token handling.")
            
            if "not found" in response.text.lower():
                print("\nEndpoint not found. Check your router setup.")
                
            if "internal server error" in response.text.lower():
                print("\nServer error. Check your server logs.")
                
    except Exception as e:
        print(f"Test exception: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_sync_endpoint()