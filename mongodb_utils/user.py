# mongodb_utils/user.py
import datetime
import time

"""
Attributes in collection 'user':
    userid: ID of user
    username: Username of the user
    email: Email of the user
    hashed_password: Hashed password
    is_active: Boolean indicating if user is active
    created_at: Timestamp of when the user was created
    last_login: Timestamp of last login
"""

async def add_user(client, document: dict) -> int:
    """
    Add a new user to the user collection
    
    Args:
        client: MongoDBClient instance
        document: User information including username, email, and password
        
    Returns:
        userid: The ID of the newly created user
    """
    # Ensure client is connected asynchronously
    if client.async_db is None:
        await client.connect_async()
        
    collection = client.async_db['users']
    
    try:
        # Check if username or email already exists
        existing_user = await collection.find_one({
            "$or": [
                {"username": document.get("username")},
                {"email": document.get("email")}
            ]
        })
        
        if existing_user:
            print(f"User '{document.get('username')}' already exists")
            return existing_user.get("userid")
        
        # Find the maximum user ID
        max_user = await collection.find_one({}, sort=[("userid", -1)])
        if max_user and "userid" in max_user:
            userid = max_user["userid"] + 1
        else:
            userid = 1  # Start with ID 1 if collection is empty
        
        # Add userid to the document
        document["userid"] = userid
        
        # If timestamps aren't provided, add them
        if "created_at" not in document:
            document["created_at"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert the document
        result = await collection.insert_one(document)
        print(f"User added. Inserted document ID: {result.inserted_id}")
        return userid
    except Exception as e:
        print(f"Error adding user:", e)
        raise e

async def get_user(client, username=None, userid=None, email=None):
    """
    Get user(s) by username, email, or userid
    
    Args:
        client: MongoDBClient instance
        username: (Optional) Username to search for
        userid: (Optional) User ID to search for
        email: (Optional) Email to search for
        
    Returns:
        A user document or None if not found
    """
    # Ensure client is connected asynchronously
    if client.async_db is None:
        await client.connect_async()
        
    collection = client.async_db['users']
    
    try:
        # Search by userid if provided
        if userid is not None:
            return await collection.find_one({"userid": userid})
        
        # Search by username if provided
        if username is not None:
            return await collection.find_one({"username": username})
            
        # Search by email if provided
        if email is not None:
            return await collection.find_one({"email": email})
            
        # If no search criteria provided, return all users
        cursor = collection.find()
        return [doc async for doc in cursor]
    except Exception as e:
        print(f"Error getting user:", e)
        raise e

async def update_user(client, userid, update_data):
    """
    Update user information
    
    Args:
        client: MongoDBClient instance
        userid: User ID to update
        update_data: Dictionary of fields to update
        
    Returns:
        Boolean indicating success
    """
    # Ensure client is connected asynchronously
    if client.async_db is None:
        await client.connect_async()
        
    collection = client.async_db['users']
    
    try:
        result = await collection.update_one(
            {"userid": userid},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print(f"User {userid} successfully updated")
            return True
        else:
            print(f"No changes made to user {userid}")
            return False
    except Exception as e:
        print(f"Error updating user:", e)
        raise e

async def delete_user(client, username=None, userid=None, email=None):
    """
    Delete a user by username, email, or userid
    
    Args:
        client: MongoDBClient instance
        username: (Optional) Username to delete
        userid: (Optional) User ID to delete
        email: (Optional) Email to delete
        
    Returns:
        Boolean indicating if the user was deleted
    """
    # Ensure client is connected asynchronously
    if client.async_db is None:
        await client.connect_async()
        
    collection = client.async_db['users']
    
    try:
        query = {}
        
        # Delete by userid if provided
        if userid is not None:
            query["userid"] = userid
        # Delete by username if provided
        elif username is not None:
            query["username"] = username
        # Delete by email if provided
        elif email is not None:
            query["email"] = email
        else:
            print("Either username, email, or userid must be provided")
            return False
            
        result = await collection.delete_one(query)
        
        if result.deleted_count > 0:
            print(f"User successfully deleted")
            return True
        else:
            print(f"No user found to delete")
            return False
    except Exception as e:
        print(f"Error deleting user:", e)
        raise e

async def update_last_login(client, userid):
    """
    Update user's last login timestamp
    
    Args:
        client: MongoDBClient instance
        userid: User ID to update
        
    Returns:
        Boolean indicating success
    """
    try:
        return await update_user(client, userid, {
            "last_login": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        print(f"Error updating last login:", e)
        raise e