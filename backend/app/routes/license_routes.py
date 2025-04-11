# app/routers/license_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import JSONResponse
import base64
from pydantic import BaseModel
from typing import List, Optional, Dict
from ..models.license_model import (
    License, LicenseActivate, LicenseFileUpload, LicenseStatus,
    EmailLicenseRequest, GenerateAndEmailLicenseRequest
)
from ..auth.auth_handler import get_current_user, is_admin
from ..database.mongodb_connection import get_db, get_mongodb_client
from ..utils.license_utils import parse_license_file
from ..utils.email_utils import send_license_key_email
from ..database.license_db import (
    create_license, get_license_by_key, get_all_licenses,
    activate_license, revoke_license, check_user_license,
    create_bulk_licenses
)
from ..database import mongodb_utils as mdb

router = APIRouter(prefix="/licenses", tags=["License Management"])

# User endpoints
@router.post("/activate")
async def activate_license_key(
    license_data: LicenseActivate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Activate a license key for the current user"""
    # Get the user_id from the current user
    user_id = current_user.user_id if hasattr(current_user, 'user_id') else current_user.id
    
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
        # Get the user_id from the current user
        user_id = current_user.user_id if hasattr(current_user, 'user_id') else current_user.id
        
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
    """Check the current user's license status"""
    # Get the user_id from the current user
    user_id = current_user.user_id if hasattr(current_user, 'user_id') else current_user.id
    
    result = await check_user_license(db, user_id)
    
    return {
        "has_valid_license": result["has_license"],
        "license_key": result.get("license_key"),
        "activated_at": result.get("activated_at"),
        "message": result.get("message", "")
    }

# Admin endpoints
@router.post("/generate", response_model=Dict)
async def generate_license_key(
    admin_user = Depends(is_admin),
    db = Depends(get_db)
):
    """Generate a new license key (admin only)"""
    # Get admin ID
    admin_id = admin_user.user_id if hasattr(admin_user, 'user_id') else admin_user.id
    
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
    admin_id = admin_user.user_id if hasattr(admin_user, 'user_id') else admin_user.id
    
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

@router.post("/email", response_model=Dict)
async def email_license_key(
    request: EmailLicenseRequest,
    admin_user = Depends(is_admin),
    db = Depends(get_db)
):
    """Email an existing license key to a user (admin only)"""
    # Generate a new license key
    admin_id = admin_user.user_id if hasattr(admin_user, 'user_id') else admin_user.id
    license_key, license_id = await create_license(db, admin_id)
    
    # Send email with the license key
    email_result = await send_license_key_email(
        request.email, 
        license_key, 
        request.username
    )
    
    if not email_result["success"]:
        # If email fails, don't lose the license key
        return {
            "success": False,
            "license_key": license_key,
            "message": f"License key generated but email could not be sent: {email_result['message']}"
        }
    
    return {
        "success": True,
        "license_key": license_key,
        "license_id": license_id,
        "message": f"License key has been emailed to {request.email}"
    }

@router.post("/generate-and-email", response_model=Dict)
async def generate_and_email_license(
    request: GenerateAndEmailLicenseRequest,
    admin_user = Depends(is_admin),
    db = Depends(get_db)
):
    """Generate a new license key and email it to a user (admin only)"""
    # Generate license keys
    admin_id = admin_user.user_id if hasattr(admin_user, 'user_id') else admin_user.id
    result = await create_bulk_licenses(db, request.count, admin_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    # For each license key, send an email
    licenses = result["licenses"]
    sent_results = []
    
    for license_key in licenses:
        email_result = await send_license_key_email(
            request.email, 
            license_key, 
            request.username
        )
        sent_results.append({
            "license_key": license_key,
            "email_sent": email_result["success"],
            "message": email_result["message"]
        })
    
    # Check if any emails failed
    all_sent = all(result["email_sent"] for result in sent_results)
    
    return {
        "success": all_sent,
        "licenses": sent_results,
        "count": len(licenses),
        "message": "All license keys have been emailed successfully" if all_sent else 
                   "Some license keys could not be emailed, check the details"
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

@router.post("/check-email-config")
async def check_email_configuration(
    admin_user = Depends(is_admin)
):
    """Check if email configuration is set up (admin only)"""
    from ..utils.email_utils import get_email_config
    
    config = get_email_config()
    
    has_sender = bool(config["email_sender"])
    has_password = bool(config["email_password"])
    
    return {
        "email_configured": has_sender and has_password,
        "smtp_server": config["smtp_server"],
        "smtp_port": config["smtp_port"],
        "email_sender": config["email_sender"] if has_sender else None,
        "has_password": has_password,
        "use_tls": config["use_tls"]
    }