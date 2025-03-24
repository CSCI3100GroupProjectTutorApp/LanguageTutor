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
from ..database.mongodb import get_db
from ..config import settings

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user in the system.
    
    - **user_data**: User information including username, email, and password
    
    Returns a newly created user without the password hash.
    
    Raises:
      - 400: Username or email already exists
      - 422: Invalid input data
    """
    try:
        # Get database instance
        db = get_db()
        
        # Check if username or email already exists
        existing_user = await db.users.find_one({
            "$or": [
                {"username": user_data.username},
                {"email": user_data.email}
            ]
        })
        
        if existing_user:
            # Return specific error message based on which field is duplicated
            if existing_user["username"] == user_data.username:
                detail = "Username already registered"
            else:
                detail = "Email already registered"
                
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail
            )
        
        # Hash password and create user
        hashed_password = get_password_hash(user_data.password)
        
        user_obj = {
            "username": user_data.username,
            "email": user_data.email,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "last_login": None
        }
        
        result = await db.users.insert_one(user_obj)
        user_obj["user_id"] = str(result.inserted_id)
        
        return UserResponse(**user_obj)
    except HTTPException as he:
        # Re-raise HTTP exceptions (like our 400 Bad Request)
        raise he
    except Exception as e:
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
    db = get_db()
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    await db.users.update_one(
        {"username": user.username},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )
    
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
        db = get_db()
        await db.users.update_one(
            {"username": current_user.username},
            {"$unset": {"refresh_token": ""}}
        )
        
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
        db = get_db()
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