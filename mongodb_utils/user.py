# mongodb_utils/user.py

"""
Attributes in collection 'user':
    userid: ID of the user
    username: Username of the user
    password: Password of the user
"""

def add_user(client, username, password) -> int:
    """
    Add a new user to the user collection
    
    Args:
        client: MongoDBClient instance
        username: Username for the new user
        password: Password for the new user
        
    Returns:
        userid: The ID of the newly created user
    """
    if client.db is None:
        client.connect()
        
    collection = client.db['user']
    try:
        # Check if username already exists
        existing_user = collection.find_one({"username": username})
        if existing_user:
            print(f"Username '{username}' already exists")
            return existing_user["userid"]
            
        # Find the maximum user ID
        max_user = collection.find_one({}, sort=[("userid", -1)])
        if max_user:
            userid = max_user["userid"] + 1
        else:
            userid = 1  # Start with ID 1 if collection is empty

        # Add a new user to the collection
        document = {
            "userid": userid, 
            "username": username, 
            "password": password
        }
        
        result = collection.insert_one(document)
        print(f"User added. Inserted document ID: {result.inserted_id}")
        return userid
    except Exception as e:
        print(f"Error adding user:", e)

def get_user(client, username=None, userid=None):
    """
    Get user(s) by username or userid
    
    Args:
        client: MongoDBClient instance
        username: (Optional) Username to search for
        userid: (Optional) User ID to search for
        
    Returns:
        A user document or None if not found
    """
    if client.db is None:
        client.connect()
        
    collection = client.db['user']
    try:
        # Search by userid if provided
        if userid is not None:
            return collection.find_one({"userid": userid})
        
        # Search by username if provided
        if username is not None:
            return collection.find_one({"username": username})
            
        # If neither is provided, return all users
        return list(collection.find())
    except Exception as e:
        print(f"Error getting user:", e)

def delete_user(client, username=None, userid=None) -> bool:
    """
    Delete a user by username or userid
    
    Args:
        client: MongoDBClient instance
        username: (Optional) Username to delete
        userid: (Optional) User ID to delete
        
    Returns:
        Boolean indicating if the user was deleted
    """
    if client.db is None:
        client.connect()
        
    collection = client.db['user']
    try:
        # Delete by userid if provided
        if userid is not None:
            result = collection.delete_one({"userid": userid})
            
        # Delete by username if provided
        elif username is not None:
            result = collection.delete_one({"username": username})
        else:
            print("Either username or userid must be provided")
            return False
            
        if result.deleted_count > 0:
            print(f"User successfully deleted")
            return True
        else:
            print(f"No user found to delete")
            return False
    except Exception as e:
        print(f"Error deleting user:", e)