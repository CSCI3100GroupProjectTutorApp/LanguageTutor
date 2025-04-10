from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from datetime import timezone
from bson import ObjectId
from jose import jwt

from ..models.user_model import UserCreate, UserResponse, Token, RefreshToken
from ..auth.auth_handler import get_password_hash, authenticate_user, get_current_user
from ..auth.jwt_handler import create_access_token, create_refresh_token, verify_token
from ..auth.token_blacklist import add_to_blacklist
from ..database.mongodb_connection import get_db, get_mongodb_client
from ..database import mongodb_utils as mdb
from ..config import settings
from ..utils.timezone_utils import get_hk_time, convert_to_hk_time, HK_TIMEZONE

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    try:
        client = await get_mongodb_client()
        
        # Check if username exists
        existing_user = await client.async_db.users.find_one({"username": user_data.username})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )
            
        # Check if email exists
        existing_email = await client.async_db.users.find_one({"email": user_data.email})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        time_now = get_hk_time()

        # Set default license values
        has_valid_license = False
        license_key = None
        
        # If license key was provided, validate it first
        if hasattr(user_data, 'license_key') and user_data.license_key:
            # Check if license exists and is valid (not used or revoked)
            license_doc = await client.async_db.licenses.find_one({
                "license_key": user_data.license_key
            })
            
            if not license_doc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid license key"
                )
                
            if license_doc.get("status") == "revoked":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="License key has been revoked"
                )
                
            if license_doc.get("user_id") and license_doc.get("status") == "used":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="License key already in use"
                )
                
            # Valid license found, will be activated after user creation
            license_key = user_data.license_key

        user_obj = {
            "username": user_data.username,
            "email": user_data.email,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_admin": False,
            "created_at": time_now,
            "last_login": None,
            "refresh_token": False,
            "has_valid_license": has_valid_license,
            "license_key": license_key
        }
        
        # Add user to database
        userid = await mdb.add_user(client, user_obj)
        
        # Add the user_id to the response object
        user_obj["user_id"] = str(userid)
        
        # If license key was provided, activate it for this user
        if license_key:
            print(f"Activating license key: {license_key} for user: {userid}")
            # Update license record to mark as used by this user
            await client.async_db.licenses.update_one(
                {"license_key": license_key},
                {
                    "$set": {
                        "user_id": str(userid),
                        "status": "used",
                        "activated_at": time_now
                    }
                }
            )
            
            from bson import ObjectId
            result = await client.async_db.users.update_one(
                {"_id": ObjectId(userid)},
                {
                    "$set": {
                        "has_valid_license": True,
                        "license_key": license_key
                    }
                }
            )
            print(f"User update result: {result.modified_count} document(s) updated")
                        
            # Update the response object
            user_obj["has_valid_license"] = True
            
            # Log license activation event
            await mdb.add_event(client, userid, "license_activation", time_now)

        # Add registration event to usage logs
        await mdb.add_event(client, userid, "register", time_now)
        
        return UserResponse(**user_obj)
    except HTTPException as he:
        raise he
    except Exception as e:
        if "duplicate key error" in str(e):
            if "username" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already exists"
                )
            elif "email" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists"
                )
        print(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during registration: {str(e)}"
        )
    
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user and return JWT tokens.
    
    - **username**: Username of the registered user
    - **password**: Password for the user account
    
    Returns access and refresh tokens if authentication is successful.
    
    Raises:
      - 401: Invalid credentials
    """
    client = await get_mongodb_client()
    db = await get_db()
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    time_now = get_hk_time()
    # Update last login time
    await db.users.update_one(
        {"username": user.username},
        {"$set": {"last_login": time_now}}
    )

    user_doc = await mdb.get_user(client, username=user.username)
    userid = user_doc["userid"]

    # Add login event to usage logs
    await mdb.add_event(client, userid, "login", time_now)

    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(
        data={"sub": user.username}
    )
    
    # Store refresh token hash in database (optional, for additional security)
    refresh_token_hash = get_password_hash(refresh_token)
    await db.users.update_one(
        {"username": user.username},
        {"$set": {"refresh_token": refresh_token_hash}}
    )
    
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

@router.post("/logout")
async def logout(request: Request, current_user = Depends(get_current_user)):
    """
    Logout a user by invalidating their current token.
    
    Requires authentication.
    """
    # Get the token from the Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Decode the token to get its expiry
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        jti = payload.get("sub", "")  # Use the subject as the token ID
        exp = datetime.fromtimestamp(payload.get("exp", 0))
        
        # Add token to blacklist
        add_to_blacklist(jti, exp)
        
        # Clear the refresh token from the database
        db = await get_db()
        await db.users.update_one(
            {"username": current_user.username},
            {"$unset": {"refresh_token": ""}}
        )

        time_now = get_hk_time()
        client = await get_mongodb_client()
        user_doc = await mdb.get_user(client, username=current_user.username)
        print(f"User document: {user_doc}")
        userid = user_doc["userid"]

        # Add login event to usage logs
        await mdb.add_event(client, userid, "logout", time_now)
        
        return {"detail": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.post("/refresh-token", response_model=Token)
async def refresh_token(refresh_token_data: RefreshToken):
    """
    Refresh an access token using a valid refresh token.
    
    - **refresh_token**: The refresh token obtained during login
    
    Returns a new access token and refresh token pair.
    
    Raises:
      - 401: Invalid or expired refresh token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify the refresh token
        token_data = verify_token(
            refresh_token_data.refresh_token, 
            credentials_exception,
            token_type="refresh"
        )
        username = token_data["user_id"]
        
        # Get the user
        db = await get_db()
        user_doc = await db.users.find_one({"username": username})
        
        if not user_doc:
            raise credentials_exception
        
        # Optional: Verify the refresh token against stored hash
        # if "refresh_token" in user_doc:
        #     if not verify_password(refresh_token_data.refresh_token, user_doc["refresh_token"]):
        #         raise credentials_exception
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires
        )
        
        # Create new refresh token
        new_refresh_token = create_refresh_token(data={"sub": username})
        
        # Update refresh token in database
        refresh_token_hash = get_password_hash(new_refresh_token)
        await db.users.update_one(
            {"username": username},
            {"$set": {"refresh_token": refresh_token_hash}}
        )
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "refresh_token": new_refresh_token
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )