from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import List
from io import BytesIO
import os
import logging
from google.cloud import vision
from google.oauth2 import service_account

from ..auth.auth_handler import get_current_user
from ..database.mongodb_connection import get_mongodb_client

router = APIRouter(prefix="/extract-text", tags=["Text Extraction (OCR)"])

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Google Cloud Vision client
try:
    # Check if we have credentials as environment variable
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
        # Parse credentials from environment variable
        import json
        credentials_info = json.loads(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"))
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        vision_client = vision.ImageAnnotatorClient(credentials=credentials)
        logger.info("Initialized Vision API client with credentials from environment variable JSON")
    elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        # Use standard credentials file
        vision_client = vision.ImageAnnotatorClient()
        logger.info("Initialized Vision API client with standard credentials")
    else:
        logger.warning("No Google Cloud credentials found. OCR will not work.")
        vision_client = None
except Exception as e:
    logger.error(f"Failed to initialize Google Cloud Vision client: {e}")
    vision_client = None

async def detect_text(image_content):
    """
    Detect text in an image using Google Cloud Vision API
    
    Args:
        image_content: Binary content of the image
        
    Returns:
        Extracted text
    """
    if vision_client is None:
        raise Exception("Google Cloud Vision client not initialized")
    
    try:    
        image = vision.Image(content=image_content)
        
        # Perform text detection
        response = vision_client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"Google Cloud Vision API error: {response.error.message}")
            
        texts = response.text_annotations
        
        if texts:
            return texts[0].description
        
        return ""
    except Exception as e:
        error_message = str(e)
        if "billing" in error_message.lower():
            # Special handling for billing-related errors
            logger.error(f"Billing error with Google Cloud Vision API: {e}")
            raise Exception("Google Cloud Vision API requires billing to be enabled. This is a development environment with limited functionality.")
        else:
            # Re-raise the original exception
            raise

@router.post("", status_code=status.HTTP_200_OK)
async def extract_text_from_image(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    Extract text from an uploaded image using OCR
    
    - Requires authentication
    - Accepts image files (JPEG, PNG)
    - Returns detected text
    """
    # Check if OCR is available
    if vision_client is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OCR service is not configured properly. Check Google Cloud Vision credentials."
        )
    
    # Check file size (5MB limit)
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    file_size = 0
    
    # Read the file in chunks to check size
    contents = BytesIO()
    chunk = await file.read(1024)
    while chunk:
        file_size += len(chunk)
        if file_size > MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large (max 5MB)"
            )
        contents.write(chunk)
        chunk = await file.read(1024)
    
    # Check file format
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["jpg", "jpeg", "png"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG and PNG images are supported"
        )
    
    try:
        # Reset file pointer to beginning
        contents.seek(0)
        image_content = contents.read()
        
        # Extract text using Google Cloud Vision
        extracted_text = await detect_text(image_content)
        
        return {
            "text": extracted_text,
            "detected_language": "auto-detect"  # Simple language detection could be added later
        }
        
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        
        # Check if it's a billing error
        if "billing" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Google Cloud Vision API requires billing to be enabled. Please check your Google Cloud console to enable billing."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error extracting text: {str(e)}"
            ) 