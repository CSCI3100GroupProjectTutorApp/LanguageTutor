# Simple in-memory token blacklist - in production, use Redis or a database
from datetime import datetime, timedelta
from datetime import timezone
from ..utils.timezone_utils import get_hk_time, HK_TIMEZONE

# Store revoked tokens with their expiry times
blacklisted_tokens = {}

def add_to_blacklist(jti: str, expires_at: datetime):
    """Add a token to the blacklist"""
    blacklisted_tokens[jti] = expires_at

def is_blacklisted(jti: str) -> bool:
    """Check if a token is blacklisted"""
    # First, clean up expired tokens
    current_time = get_hk_time()
    expired_tokens = [token for token, expires in blacklisted_tokens.items() if expires < current_time]
    for token in expired_tokens:
        blacklisted_tokens.pop(token, None)
    
    # Check if token is in blacklist
    return jti in blacklisted_tokens

def clear_expired_tokens():
    """Remove expired tokens from blacklist"""
    current_time = get_hk_time()
    expired_tokens = [token for token, expires in blacklisted_tokens.items() if expires < current_time]
    for token in expired_tokens:
        blacklisted_tokens.pop(token, None)