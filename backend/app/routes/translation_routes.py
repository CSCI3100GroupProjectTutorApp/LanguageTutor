from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Optional
import requests
import hashlib
import uuid
import time
import os

from ..auth.auth_handler import get_current_user

router = APIRouter(prefix="/translate", tags=["Translation"])

# Get Youdao API credentials from environment
YOUDAO_APP_KEY = os.environ.get("YOUDAO_APP_KEY", "")
YOUDAO_APP_SECRET = os.environ.get("YOUDAO_APP_SECRET", "")

# Youdao API endpoint
YOUDAO_API_URL = "https://openapi.youdao.com/api"

class TranslationRequest:
    def __init__(self, text: str, target_language: str):
        self.text = text
        self.target_language = target_language
        self.source_language = "auto"  # Auto-detect source language
        
    def get_youdao_params(self):
        """
        Generate parameters for Youdao API request
        """
        if not YOUDAO_APP_KEY or not YOUDAO_APP_SECRET:
            raise Exception("Youdao API credentials not configured")
            
        salt = str(uuid.uuid1())
        timestamp = str(int(time.time()))
        input_text = self.text
        
        # If query text is too long, truncate and use hash instead
        if len(input_text) > 20:
            input_len = len(input_text)
            input_text = input_text[:10] + str(input_len) + input_text[-10:]
            
        # Generate sign according to Youdao API requirements
        sign_str = YOUDAO_APP_KEY + input_text + salt + timestamp + YOUDAO_APP_SECRET
        sign = hashlib.sha256(sign_str.encode()).hexdigest()
        
        # Map language codes to Youdao codes
        target_lang = self.target_language
        if target_lang.lower() == "zh" or target_lang.lower() == "zh-cn":
            target_lang = "zh-CHS"
        elif target_lang.lower() == "zh-tw":
            target_lang = "zh-CHT"
            
        params = {
            "q": self.text,
            "from": self.source_language,
            "to": target_lang,
            "appKey": YOUDAO_APP_KEY,
            "salt": salt,
            "sign": sign,
            "signType": "v3",
            "curtime": timestamp
        }
        
        return params

@router.post("", status_code=status.HTTP_200_OK)
async def translate_text(
    data: Dict[str, str] = Body(...),
    current_user = Depends(get_current_user)
):
    """
    Translate text to target language
    
    - Requires authentication
    - Request body:
      {
        "text": "Text to translate",
        "target_language": "zh" (language code, e.g., en, zh, ja, etc.)
      }
    - Returns translated text
    - Rate-limited to 100 requests per hour (Youdao API free tier)
    """
    if not data.get("text"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text to translate is required"
        )
        
    if not data.get("target_language"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target language is required"
        )
        
    try:
        translation_request = TranslationRequest(
            text=data["text"],
            target_language=data["target_language"]
        )
        
        # If Youdao credentials are not set, return dummy translation for development
        if not YOUDAO_APP_KEY or not YOUDAO_APP_SECRET:
            return {
                "text": data["text"],
                "translated_text": f"[Translation of '{data['text']}' to {data['target_language']}]",
                "source_language": "auto",
                "target_language": data["target_language"]
            }
            
        # Get Youdao API parameters
        params = translation_request.get_youdao_params()
        
        # Send request to Youdao API
        response = requests.get(YOUDAO_API_URL, params=params)
        response_json = response.json()
        
        if response_json.get("errorCode") != "0":
            raise Exception(f"Youdao API error: {response_json.get('errorCode')}")
            
        # Extract translation from response
        translations = response_json.get("translation", [])
        if not translations:
            raise Exception("No translation found in response")
            
        return {
            "text": data["text"],
            "translated_text": translations[0],
            "source_language": response_json.get("l", "").split("2")[0],
            "target_language": data["target_language"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error translating text: {str(e)}"
        ) 