# app/auth/license_checker.py
from fastapi import Depends, HTTPException, status
from ..database.mongodb_connection import get_db
from ..auth.auth_handler import get_current_user
from ..database.license_db import check_user_license

async def verify_license(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Verify the user has a valid license"""
    # Get the user_id from the current user object, trying different attribute names
    user_id = None
    if hasattr(current_user, 'user_id'):
        user_id = current_user.user_id
    elif hasattr(current_user, 'id'):
        user_id = current_user.id
    elif hasattr(current_user, '_id'):
        user_id = current_user._id
    
    if not user_id:
        # If we can't find the user ID in any of the expected attributes, try to get it from dict()
        if hasattr(current_user, 'dict'):
            user_dict = current_user.dict()
            user_id = user_dict.get('user_id') or user_dict.get('id') or user_dict.get('_id')
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not determine user ID from authentication token"
        )
    
    result = await check_user_license(db, user_id)
    
    if not result["has_license"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A valid license is required to use this application"
        )
    
    return True