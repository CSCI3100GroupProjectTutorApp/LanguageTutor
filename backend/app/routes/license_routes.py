# app/routers/license_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import JSONResponse
import base64
from pydantic import BaseModel
from typing import List, Optional, Dict
from ..models.license_model import License, LicenseActivate, LicenseFileUpload, LicenseStatus
from ..auth.auth_handler import get_current_user, is_admin
from ..database.mongodb_connection import get_db, get_mongodb_client
from ..utils.license_utils import parse_license_file
from ..database.license_db import (
    create_license, get_license_by_key, get_all_licenses,
    activate_license, revoke_license, check_user_license,
    create_bulk_licenses
)

router = APIRouter(prefix="/licenses", tags=["License Management"])

# User endpoints
@router.post("/activate")
async def activate_license_key(
    license_data: LicenseActivate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Activate a license key for the current user"""
    result = await activate_license(db, license_data.license_key, current_user.id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return {"message": "License activated successfully"}

@router.post("/upload-file")
async def upload_license_file(
    file_data: LicenseFileUpload,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Upload and process a license file"""
    try:
        # Decode base64 file content
        file_content = base64.b64decode(file_data.file_content).decode('utf-8')
        
        # Parse the file to extract license keys
        license_keys = parse_license_file(file_content)
        
        if not license_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid license keys found in the file"
            )
        
        # Try to activate each license key
        for key in license_keys:
            result = await activate_license(db, key, current_user.id)
            if result["success"]:
                return {"message": f"License key {key} activated successfully"}
        
        # If we get here, none of the keys worked
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="None of the license keys in the file could be activated"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing license file: {str(e)}"
        )

@router.get("/status")
async def check_license_status(current_user = Depends(get_current_user)):
    """Check the license status for the current user"""
    try:
        client = await get_mongodb_client()
        
        # Get the complete user document from the database
        user_doc = await client.async_db.users.find_one({"username": current_user.username})
        print(f"User document: {user_doc}")
        
        if not user_doc:
            return {
                "has_license": False,
                "message": "User not found"
            }
        
        # Check if user has a valid license
        has_valid_license = user_doc.get("has_valid_license", False)
        license_key = user_doc.get("license_key")
        
        # If no license key or not marked as valid, return false
        if not license_key or not has_valid_license:
            return {
                "has_license": False,
                "message": "No license associated with user"
            }
        
        # Double-check the license in the licenses collection
        license_doc = await client.async_db.licenses.find_one({"license_key": license_key})
        
        # If license doesn't exist in licenses collection
        if not license_doc:
            # Update user record to correct the inconsistency
            await client.async_db.users.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"has_valid_license": False, "license_key": None}}
            )
            return {
                "has_license": False,
                "message": "License record not found"
            }
        
        # Check if license is assigned to this user
        if license_doc.get("user_id") != str(user_doc["_id"]):
            # Update user record to correct the inconsistency
            await client.async_db.users.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"has_valid_license": False, "license_key": None}}
            )
            return {
                "has_license": False,
                "message": "License assigned to another user"
            }
        
        # Check if license is revoked
        if license_doc.get("status") == "revoked":
            # Update user record to correct the inconsistency
            await client.async_db.users.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"has_valid_license": False, "license_key": None}}
            )
            return {
                "has_license": False,
                "message": "License has been revoked"
            }
        
        # At this point, the license is valid
        return {
            "has_license": True,
            "license_key": license_key,
            "activated_at": license_doc.get("activated_at"),
            "message": "Valid license found"
        }
            
    except Exception as e:
        print(f"Error checking license status: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return {
            "has_license": False,
            "error": str(e),
            "message": "Error checking license status"
        }

# Admin endpoints
@router.post("/generate", response_model=Dict)
async def generate_license_key(
    admin_user = Depends(is_admin),
    db = Depends(get_db)
):
    """Generate a new license key (admin only)"""
    # Print some debug info
    print(f"Admin user data: {admin_user}")
    print(f"Admin user ID field: {admin_user.user_id if hasattr(admin_user, 'user_id') else 'No user_id attribute'}")
    print(f"Admin user ID field: {admin_user.id if hasattr(admin_user, 'id') else 'No id attribute'}")
    
    # Use the correct ID field based on your user model
    admin_id = getattr(admin_user, "user_id", None) or getattr(admin_user, "id", None)
    
    license_key, license_id = await create_license(db, admin_id)
    
    return {
        "license_key": license_key,
        "license_id": license_id,
        "message": "License key generated successfully"
    }

@router.post("/generate-bulk/{count}", response_model=Dict)
async def generate_bulk_licenses_path(
    count: int,  # Path parameter
    admin_user = Depends(is_admin),
    db = Depends(get_db)
):
    """Generate multiple license keys at once using path parameter (admin only)"""
    # Validate count
    if count <= 0 or count > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Count must be between 1 and 100"
        )
    
    # Get admin ID
    admin_id = admin_user.user_id
    
    # Generate licenses
    result = await create_bulk_licenses(db, count, admin_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return {
        "licenses": result["licenses"],
        "count": result["count"],
        "message": f"Generated {result['count']} license keys successfully"
    }

@router.get("/all", response_model=List[Dict])
async def get_all_license_keys(
    admin_user = Depends(is_admin),
    db = Depends(get_db)
):
    """Get all license keys (admin only)"""
    licenses = await get_all_licenses(db)
    
    # Convert ObjectId to string for JSON serialization
    for license in licenses:
        if "_id" in license:
            license["_id"] = str(license["_id"])
        if "user_id" in license and license["user_id"]:
            license["user_id"] = str(license["user_id"])
        if "created_by" in license and license["created_by"]:
            license["created_by"] = str(license["created_by"])
    
    return licenses

@router.post("/revoke/{license_key}")
async def revoke_license_key(
    license_key: str,
    admin_user = Depends(is_admin),
    db = Depends(get_db)
):
    """Revoke a license (admin only)"""
    result = await revoke_license(db, license_key)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return {"message": "License revoked successfully"}