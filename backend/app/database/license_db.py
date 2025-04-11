# app/database/license_db.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from ..models.license_model import LicenseStatus

async def create_license(db, admin_id=None):
    """Create a new license key"""
    from ..utils.license_utils import generate_license_key
    
    try:
        license_key = generate_license_key()
        
        # Use the string value directly to avoid potential enum issues
        license_data = {
            "license_key": license_key,
            "status": "active",  # Use string directly instead of enum
            "issued_date": datetime.now(),
            "user_id": None,
            "activated_at": None,
            "created_by": admin_id
        }
        
        result = await db.licenses.insert_one(license_data)
        print(f"License created: {license_key}, ID: {result.inserted_id}")
        return license_key, str(result.inserted_id)
    except Exception as e:
        print(f"Error in create_license: {e}")
        # Include more detailed error information
        import traceback
        print(traceback.format_exc())
        raise

async def get_license_by_key(db, license_key):
    """Find a license by its key"""
    return await db.licenses.find_one({"license_key": license_key})

async def get_all_licenses(db):
    """Get all licenses"""
    cursor = db.licenses.find()
    return await cursor.to_list(length=100)

async def activate_license(db, license_key, user_id):
    """Activate a license for a user"""
    # Check if license exists
    license_data = await get_license_by_key(db, license_key)
    
    if not license_data:
        return {"success": False, "message": "Invalid license key"}
    
    # Check if already used
    if license_data.get("user_id") and license_data["user_id"] != user_id:
        return {"success": False, "message": "License key already used by another user"}
    
    if license_data.get("status") == LicenseStatus.REVOKED:
        return {"success": False, "message": "License key has been revoked"}
    
    # Update license record
    await db.licenses.update_one(
        {"license_key": license_key},
        {
            "$set": {
                "user_id": user_id,
                "status": LicenseStatus.USED,
                "activated_at": datetime.now()
            }
        }
    )
    
    # Update user record to mark as licensed
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "has_valid_license": True,
                "license_key": license_key
            }
        }
    )
    
    return {"success": True, "message": "License activated successfully"}

async def revoke_license(db, license_key):
    """Revoke a license"""
    license_data = await get_license_by_key(db, license_key)
    
    if not license_data:
        return {"success": False, "message": "License not found"}
    
    # Update license status
    result = await db.licenses.update_one(
        {"license_key": license_key},
        {"$set": {"status": LicenseStatus.REVOKED}}
    )
    
    if result.modified_count == 0:
        return {"success": False, "message": "Failed to revoke license"}
    
    # If license is associated with a user, update user record
    if license_data.get("user_id"):
        await db.users.update_one(
            {"_id": ObjectId(license_data["user_id"])},
            {"$set": {"has_valid_license": False}}
        )
    
    return {"success": True, "message": "License revoked successfully"}

async def check_user_license(db, user_id):
    """Check if a user has a valid license"""
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return {"has_license": False, "message": "User not found"}
    
    if not user.get("has_valid_license"):
        return {"has_license": False, "message": "No license associated with user"}
    
    license_key = user.get("license_key")
    if not license_key:
        return {"has_license": False, "message": "License key not found"}
    
    license_data = await get_license_by_key(db, license_key)
    if not license_data or license_data.get("status") != LicenseStatus.USED:
        # Update user record to fix inconsistency
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"has_valid_license": False, "license_key": None}}
        )
        return {"has_license": False, "message": "License key is invalid or revoked"}
    
    return {
        "has_license": True,
        "license_key": license_key,
        "activated_at": license_data.get("activated_at")
    }

async def create_bulk_licenses(db, count, admin_id=None):
    """Create multiple license keys at once"""
    if count <= 0 or count > 100:
        return {"success": False, "message": "Count must be between 1 and 100"}
    
    licenses = []
    for _ in range(count):
        try:
            license_key, _ = await create_license(db, admin_id)
            licenses.append(license_key)
        except Exception as e:
            print(f"Error generating license in bulk: {str(e)}")
            # Continue with the next one
    
    return {"success": True, "licenses": licenses, "count": len(licenses)}