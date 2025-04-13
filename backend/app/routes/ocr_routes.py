from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import List
from io import BytesIO
import os
import logging
from google.cloud import vision
from google.oauth2 import service_account
import tempfile
import PyPDF2
import pdfplumber

from ..auth.auth_handler import get_current_user
from ..database.mongodb_connection import get_mongodb_client

router = APIRouter(prefix="/extract-text", tags=["Text Extraction (OCR)"])

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Google Cloud Vision client
try:
    # Check if we have credentials as environment variable
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        # Parse credentials from environment variable
        import json
        credentials_info = json.loads(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
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

async def process_pdf(pdf_content):
    """
    Process a PDF file and extract text
    
    Args:
        pdf_content: Binary content of the PDF file
        
    Returns:
        Extracted text
    """
    try:
        pdf_file = BytesIO(pdf_content)
        
        # First try with pdfplumber, which has better text extraction capabilities
        extracted_text = ""
        
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text(x_tolerance=3)
                if page_text and page_text.strip():
                    extracted_text += f"--- Page {page_num+1} ---\n{page_text}\n\n"
        
        # If we got meaningful text, return it
        if extracted_text and len(extracted_text.strip()) > 50:  # Arbitrary threshold
            return extracted_text
            
        # If pdfplumber didn't extract enough text, try PyPDF2 as a fallback
        pdf_file.seek(0)  # Reset file pointer
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            if page_text and page_text.strip():
                extracted_text += f"--- Page {page_num+1} ---\n{page_text}\n\n"
        
        # If we still don't have meaningful text, we can't extract text from this PDF
        if not extracted_text or len(extracted_text.strip()) < 50:
            return "This PDF does not contain extractable text. It may be scanned documents or images. Please try OCR on individual pages as images."
                
        return extracted_text
                
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise Exception(f"Error processing PDF: {str(e)}")

@router.post("", status_code=status.HTTP_200_OK)
async def extract_text_from_image(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    Extract text from an uploaded image or PDF using OCR
    
    - Requires authentication
    - Accepts image files (JPEG, PNG) and PDF files
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
    if file_extension not in ["jpg", "jpeg", "png", "pdf"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, and PDF files are supported"
        )
    
    try:
        # Reset file pointer to beginning
        contents.seek(0)
        file_content = contents.read()
        
        # Extract text based on file type
        if file_extension == "pdf":
            extracted_text = await process_pdf(file_content)
        else:
            # Image files (jpg, png)
            extracted_text = await detect_text(file_content)
        
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