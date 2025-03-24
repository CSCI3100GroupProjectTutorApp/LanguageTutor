# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import jwt

from .database.mongodb import connect_to_mongodb, close_mongodb_connection, get_db
from .routes import auth_routes, user_routes
from .config import settings
from .auth.token_blacklist import is_blacklisted

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
    await connect_to_mongodb()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongodb_connection()

# Include routers
app.include_router(auth_routes.router)
app.include_router(user_routes.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Language Tutoring API"}

@app.get("/test-db")
async def test_db():
    """Test database connectivity"""
    try:
        # Use the get_db function to retrieve the database
        db = get_db()
        
        # Test connection
        await db.command("ping")
        
        # Get collections
        collections = await db.list_collection_names()
        
        return {
            "status": "Connected to MongoDB Atlas",
            "database": "language_tutoring_app",
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