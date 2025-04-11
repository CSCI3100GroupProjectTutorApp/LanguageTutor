# app/routers/license_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import JSONResponse
import base64
from typing import List, Optional, Dict
from ..models.license_model import License, LicenseActivate, LicenseFileUpload, LicenseStatus
from ..auth.auth_handler import get_current_user, is_admin
from ..database.mongodb_connection import get_db
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
    # Get the user_id from the current_user object
    user_id = current_user.user_id  # Assuming current_user has a user_id attribute
    
    result = await activate_license(db, license_data.license_key, user_id)
    
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
        # Get the user_id from the current_user object
        user_id = current_user.user_id
        
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
            result = await activate_license(db, key, user_id)
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
async def check_license_status(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Check the license status for the current user"""
    user_id = current_user.user_id
    result = await check_user_license(db, user_id)
    return result

# Admin endpoints
@router.post("/generate", response_model=Dict)
async def generate_license_key(
    admin_user = Depends(is_admin),
    db = Depends(get_db)
):
    """Generate a new license key (admin only)"""
    # Print debug info about the admin user
    print(f"Admin user data: {admin_user}")
    
    # Get the user_id consistently from admin_user
    admin_id = admin_user.user_id  # Assuming user_id is the correct attribute
    print(f"Using admin ID: {admin_id}")
    
    try:
        license_key, license_id = await create_license(db, admin_id)
        
        return {
            "license_key": license_key,
            "license_id": license_id,
            "message": "License key generated successfully"
        }
    except Exception as e:
        # Log the error for debugging
        print(f"Error generating license: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating license: {str(e)}"
        )

@router.post("/generate-bulk")
async def generate_bulk_license_keys(
    count: int = Body(..., gt=0, le=100),
    admin_user = Depends(is_admin),
    db = Depends(get_db)
):
    """Generate multiple license keys at once (admin only)"""
    # Get the user_id consistently
    admin_id = admin_user.user_id
    
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