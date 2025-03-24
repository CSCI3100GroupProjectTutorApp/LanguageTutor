# mongodb_utils/client.py
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

class MongoDBClient:
    """Main client class for MongoDB connections"""
    
    def __init__(self, username:str, password:str):
        self.uri = f"mongodb+srv://{username}:{password}@csci3100-project.tloff.mongodb.net/?retryWrites=true&w=majority&appName=CSCI3100-Project"
        self.db_name = "languageTutor"
        self.client = None
        self.db = None
        
    def connect(self):
        """Connect to MongoDB database"""
        try:
            self.client = MongoClient(self.uri, server_api=ServerApi('1'))
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
            self.db = self.client[self.db_name]
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
    
    def close(self):
        """Close the MongoDB connection"""
        if self.client is not None:  
            self.client.close()
            print("MongoDB connection closed")
            self.client = None
            self.db = None
    
    def get_collection(self, collection_name):
        """Get a collection from the database"""
        if self.db is None:  
            self.connect()
        return self.db[collection_name]
    
    def print_collection(self, collection_name):
        """Print all documents in a collection"""
        if self.db is None:  
            self.connect()
        collection = self.db[collection_name]
        for doc in collection.find():
            print(doc)
        return
    
    def __enter__(self):
        """Support for with statement context management"""
        self.connect()
        return self
    
    def __exit__(self):
        """Ensure connection is closed when exiting context"""
        self.close()
        return