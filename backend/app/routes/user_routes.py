from fastapi import APIRouter, Depends, HTTPException, status
from ..models.user_model import UserResponse
from ..models.license_model import LicenseActivate, EmailLicenseRequest
from ..auth.auth_handler import get_current_user
from ..database.mongodb_connection import get_db, get_mongodb_client
from ..database import mongodb_utils as mdb
from ..database.license_db import activate_license, check_user_license, create_license
from ..utils.email_utils import send_license_key_email
from ..auth.license_checker import verify_license

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
        
        # Check license status
        client = await get_mongodb_client()
        user_doc = await mdb.get_user(client, userid=user_id)
        
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found in database"
            )
            
        has_valid_license = user_doc.get("has_valid_license", False)
        license_key = user_doc.get("license_key")
        is_admin = user_doc.get("is_admin", False)
        created_at = user_doc.get("created_at")
        last_login = user_doc.get("last_login")
        
        # Return a properly formatted user response
        return UserResponse(
            user_id=user_id,
            username=user_doc.get("username"),
            email=user_doc.get("email"),
            is_active=user_doc.get("is_active", True),
            has_valid_license=has_valid_license,
            license_key=license_key,
            is_admin=is_admin,
            created_at=created_at,
            last_login=last_login
        )
    except Exception as e:
        print(f"Error in get_user_profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user profile: {str(e)}"
        )

@router.post("/activate-license")
async def activate_user_license(
    license_data: LicenseActivate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Activate a license key for the current user"""
    # Get the user ID
    user_id = current_user.user_id if hasattr(current_user, 'user_id') else current_user.id
    
    # Activate the license
    result = await activate_license(db, license_data.license_key, user_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return {"message": "License key activated successfully"}

@router.get("/license-status")
async def get_user_license_status(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get the license status for the current user"""
    # Get the user ID
    user_id = current_user.user_id if hasattr(current_user, 'user_id') else current_user.id
    
    # Check license status
    result = await check_user_license(db, user_id)
    
    return {
        "has_valid_license": result["has_license"],
        "license_key": result.get("license_key"),
        "activated_at": result.get("activated_at"),
        "message": result.get("message", "")
    }

@router.post("/request-license")
async def request_license_key(
    current_user = Depends(get_current_user)
):
    """Request a license key to be sent to user's email"""
    client = await get_mongodb_client()
    db = await get_db()
    user_id = current_user.user_id if hasattr(current_user, 'user_id') else current_user.id
    
    # Get user document to access email
    user_doc = await mdb.get_user(client, userid=user_id)
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user already has a valid license
    if user_doc.get("has_valid_license", False):
        return {
            "success": False,
            "message": "You already have an active license"
        }
    
    # Get user email
    email = user_doc.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no registered email"
        )
    
    # Find admin for the license creation
    admin_user = await db.users.find_one({"is_admin": True})
    if not admin_user:
        # Create a fallback admin ID if none exists
        admin_id = "system"
    else:
        admin_id = str(admin_user.get("_id"))
    
    try:
        # Generate a license key
        license_key, license_id = await create_license(db, admin_id)
        
        # Send the license key via email
        username = user_doc.get("username")
        email_result = await send_license_key_email(email, license_key, username)
        
        # Handle either boolean or dictionary return type
        email_success = False
        email_message = ""
        
        if isinstance(email_result, bool):
            # Handle boolean return
            email_success = email_result
            email_message = "Email sending failed" if not email_success else "Email sent successfully"
        elif isinstance(email_result, dict):
            # Handle dictionary return
            email_success = email_result.get("success", False)
            email_message = email_result.get("message", "")
        
        if not email_success:
            print(f"Email sending failed: {email_message}")
            # For testing, always return success with the license key
            return {
                "success": True,
                "license_key": license_key,
                "message": f"License key generated, but email could not be sent: {email_message}"
            }
        
        return {
            "success": True,
            "license_key": license_key,  
            "message": f"A license key has been sent to your email address: {email}"
        }
    except Exception as e:
        print(f"Error generating/sending license: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing license request: {str(e)}"
        )

@router.get("/protected-data")
async def get_protected_data(
    current_user = Depends(get_current_user),
    _: bool = Depends(verify_license),  # This ensures user has a valid license
    db = Depends(get_db)
):
    """Access protected data (requires a valid license)"""
    return {
        "message": "You have access to protected data",
        "data": {
            "sample": "This is protected data that requires a valid license"
        }
    }