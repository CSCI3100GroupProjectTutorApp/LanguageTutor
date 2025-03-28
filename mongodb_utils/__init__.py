# mongodb_utils/__init__.py

# Import the client class
from .client import MongoDBClient

# Import functions from user module
from .user import add_user, get_user, delete_user

# Import functions from word module
from .word import add_word, find_word, delete_word

# Export publicly available components
__all__ = [
    'MongoDBClient',
    'add_user', 'get_user', 'delete_user',
    'add_word', 'find_word', 'delete_word',
]