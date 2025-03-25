from fastapi import APIRouter, Depends, HTTPException, status
from ..models.user_model import UserResponse
from ..auth.auth_handler import get_current_user
from ..database.mongodb_connection import get_db
router = APIRouter(prefix="/users", tags=["User Management"])

@router.get("/me", response_model=UserResponse)
async def get_user_profile(current_user = Depends(get_current_user)):
    """Get current user profile"""
    try:
        # Correctly extract the ID regardless of field name
        user_id = None
        
        # Try different field names that might contain the ID
        if hasattr(current_user, 'user_id') and current_user.user_id:
            user_id = str(current_user.user_id)
        elif hasattr(current_user, '_id') and current_user._id:
            user_id = str(current_user._id)
        elif hasattr(current_user, 'id') and current_user.id:
            user_id = str(current_user.id)
        
        # If ID still not found, get it from the dict representation
        if not user_id and hasattr(current_user, 'dict'):
            user_dict = current_user.dict()
            user_id = str(user_dict.get('_id') or user_dict.get('id') or user_dict.get('user_id'))
        
        # If still no ID, try to get the MongoDB document directly
        if not user_id:
            db = await get_db()
            user_doc = await db.users.find_one({"username": current_user.username})
            if user_doc and '_id' in user_doc:
                user_id = str(user_doc['_id'])
        
        # If still no ID found, raise a clear error
        if not user_id:
            raise ValueError("Could not extract user ID from user object")
        
        # Return a properly formatted user response
        return UserResponse(
            user_id=user_id,
            username=current_user.username,
            email=current_user.email,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            last_login=current_user.last_login
        )
    except Exception as e:
        print(f"Error in get_user_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user profile: {str(e)}"
        )