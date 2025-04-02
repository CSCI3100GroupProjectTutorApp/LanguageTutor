# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import jwt
import logging

# Use the new mongodb connection module
from .database.mongodb_connection import connect_to_mongodb, close_mongodb_connection, get_db
from .database.init_db import init_db
from .routes import router
from .config import settings
from .auth.token_blacklist import is_blacklisted

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Language Tutoring API",
    description="API for the Language Tutoring Application",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database events
@app.on_event("startup")
async def startup_db_client():
    try:
        logger.info("Starting database connection...")
        await connect_to_mongodb()
        
        # Initialize database (create collections and indices)
        logger.info("Initializing database...")
        await init_db()
        
        logger.info("Database setup complete!")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Don't crash the application, but log the error
        # The error will be handled when endpoints try to access the database

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("Closing database connection...")
    await close_mongodb_connection()

# Include all routes
app.include_router(router)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Language Tutoring API"}

@app.get("/test-db")
async def test_db():
    """Test database connectivity"""
    try:
        # Use the get_db function to retrieve the database
        db = await get_db()
        
        # Test connection
        await db.command("ping")
        
        # Get collections
        collections = await db.list_collection_names()
        
        return {
            "status": "Connected to MongoDB Atlas",
            "database": "languageTutor",
            "collections": collections
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
@app.middleware("http")
async def check_blacklisted_tokens(request: Request, call_next):
    # Skip token check for non-protected routes
    if request.url.path in ["/docs", "/redoc", "/openapi.json", "/", "/login", "/register", "/refresh-token"]:
        return await call_next(request)
    
    # Check if token is blacklisted
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            jti = payload.get("sub", "")
            if is_blacklisted(jti):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token has been revoked"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except:
            # Let the endpoint handler deal with invalid tokens
            pass
    
    # Continue with the request
    return await call_next(request)