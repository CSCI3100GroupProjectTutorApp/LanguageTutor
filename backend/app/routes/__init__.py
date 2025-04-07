# Routes package initialization

# Import all routers to be included in the API
from fastapi import APIRouter

from .auth_routes import router as auth_router
from .user_routes import router as user_router
from .utility_routes import router as utility_router
from .word_routes import router as word_router
from .ocr_routes import router as ocr_router
from .translation_routes import router as translation_router
from .sync_routes import router as sync_router

# Create a router that includes all the other routers
router = APIRouter()

# Include the routers
router.include_router(auth_router)
router.include_router(user_router)
router.include_router(utility_router)
router.include_router(word_router)
router.include_router(ocr_router)
router.include_router(translation_router)
router.include_router(sync_router)
