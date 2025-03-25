from fastapi import APIRouter, Depends, status, HTTPException
from ..utils.timezone_utils import get_hk_time, HK_TIMEZONE
from datetime import datetime, timezone

router = APIRouter(tags=["Utilities"])

@router.get("/time")
async def get_time():
    """Get current server time in different timezones"""
    utc_time = datetime.now(timezone.utc)
    hk_time = get_hk_time()
    
    return {
        "utc_time": utc_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "hong_kong_time": hk_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "timezone_offset": "+08:00",
        "timezone_name": "Asia/Hong_Kong"
    } 