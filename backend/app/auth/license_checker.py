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
    result = await check_user_license(db, current_user.id)
    
    if not result["has_license"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A valid license is required to use this application"
        )
    
    return True