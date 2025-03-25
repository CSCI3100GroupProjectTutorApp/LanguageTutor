from datetime import datetime, timezone, timedelta

# Define Hong Kong timezone (UTC+8)
HK_TIMEZONE = timezone(timedelta(hours=8), name='Asia/Hong_Kong')

def get_hk_time():
    """Get current time in Hong Kong timezone (UTC+8)"""
    return datetime.now(HK_TIMEZONE)

def convert_to_hk_time(dt):
    """Convert a datetime object to Hong Kong timezone"""
    if dt.tzinfo is None:
        # If the datetime has no timezone, assume it's UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(HK_TIMEZONE) 