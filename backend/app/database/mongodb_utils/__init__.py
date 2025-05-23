# mongodb_utils/__init__.py

# Import the client class
from .client import MongoDBClient

# Import functions from user module
from .user import add_user, get_user, update_user, delete_user, update_last_login

# Import functions from word module
from .word import add_word, find_word, update_word, delete_word

# Import functions from usage_log module
from .usage_log import add_event

# Import functions from word_operation module
from .word_operations import log_word_operation

# Export publicly available components
__all__ = [
    'MongoDBClient',
    'add_user', 'get_user', 'update_user', 'delete_user', 'update_last_login',
    'add_word', 'find_word', 'update_word', 'delete_word',
    'add_event',
    'log_word_operation'
]