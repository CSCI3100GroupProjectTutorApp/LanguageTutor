# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import jwt
import logging
import os

# MongoDB connections
from .database.mongodb_connection import connect_to_mongodb, close_mongodb_connection, get_db
from .database.init_db import init_db

# SQLite storage
from .database.sqlite.sqlite_storage import WordStorage
from .dependencies import get_sqlite_storage, get_mongo_client

# Routes
from .routes import auth_routes, user_routes, utility_routes, sync_routes, word_routes, ocr_routes, translation_routes
from .config import settings
from .auth.token_blacklist import is_blacklisted

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Language Tutoring API",
    description="API for the Language Tutoring Application with Offline Support",
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

# Initialize SQLite storage
sqlite_db_path = os.getenv("SQLITE_DB_PATH", "data/word_storage.db")
word_storage = None

# Database events
@app.on_event("startup")
async def startup_db_client():
    try:
        global word_storage
        
        # Connect to MongoDB
        logger.info("Starting MongoDB connection...")
        await connect_to_mongodb()
        
        # Initialize MongoDB database (create collections and indices)
        logger.info("Initializing MongoDB database...")
        await init_db()
        
        # Initialize SQLite storage
        logger.info("Initializing SQLite storage...")
        word_storage = WordStorage(db_path=sqlite_db_path)
        await word_storage.initialize_db()
        
        # Start auto-sync in background if enabled
        if os.getenv("ENABLE_AUTO_SYNC", "true").lower() == "true":
            logger.info("Starting auto-sync with MongoDB...")
            mongo_client = await get_mongo_client()
            auto_sync_interval = int(os.getenv("AUTO_SYNC_INTERVAL", "60"))
            word_storage.start_auto_sync(mongo_client)
            logger.info(f"Auto-sync started with interval: {auto_sync_interval} seconds")
        
        logger.info("Database setup complete!")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Don't crash the application, but log the error

@app.on_event("shutdown")
async def shutdown_db_client():
    global word_storage
    
    # Stop auto-sync if active
    logger.info("Stopping auto-sync...")
    if word_storage:
        word_storage.stop_auto_sync()
    
    # Close MongoDB connection
    logger.info("Closing database connections...")
    await close_mongodb_connection()

# Include routers
app.include_router(auth_routes.router)
app.include_router(user_routes.router)
app.include_router(utility_routes.router, prefix="/utils")
app.include_router(word_routes.router, prefix="/words")
app.include_router(sync_routes.router, prefix="/sync")
app.include_router(ocr_routes.router)
app.include_router(translation_routes.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Language Tutoring API with Offline Support"}

@app.get("/test-db")
async def test_db():
    """Test database connectivity"""
    try:
        # Test MongoDB connection
        db = await get_db()
        await db.command("ping")
        collections = await db.list_collection_names()
        
        # Test SQLite connection
        storage = await get_sqlite_storage()
        sqlite_status = "Connected" if storage else "Not connected"
        
        return {
            "mongodb": {
                "status": "Connected to MongoDB Atlas",
                "database": "languageTutor",
                "collections": collections
            },
            "sqlite": {
                "status": sqlite_status,
                "path": sqlite_db_path,
                "sync_status": storage.get_sync_status() if storage else None
            }
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