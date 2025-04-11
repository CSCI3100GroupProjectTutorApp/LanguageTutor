import asyncio
import argparse
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_user(username, email, password, mongodb_url):
    """Create an admin user directly in the database"""
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongodb_url)
    db = client.languageTutor  # Replace with your actual database name
    
    # Check if user already exists
    existing_user = await db.users.find_one({"username": username})
    if existing_user:
        print(f"User '{username}' already exists.")
        
        # Update to admin if needed
        if not existing_user.get("is_admin", False):
            result = await db.users.update_one(
                {"username": username},
                {"$set": {"is_admin": True}}
            )
            print(f"User '{username}' has been updated to admin status.")
        else:
            print(f"User '{username}' is already an admin.")
            
        client.close()
        return
    
    # Create new admin user
    hashed_password = pwd_context.hash(password)
    user_data = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "is_active": True,
        "is_admin": True,
        "created_at": datetime.now(),
        "has_valid_license": True  # Auto-license the admin
    }
    
    await db.users.insert_one(user_data)
    print(f"Admin user '{username}' created successfully!")
    client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    
    # Get MongoDB URL from .env file
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    
    args = parser.parse_args()
    
    asyncio.run(create_admin_user(
        args.username, 
        args.email, 
        args.password,
        mongodb_url
    ))