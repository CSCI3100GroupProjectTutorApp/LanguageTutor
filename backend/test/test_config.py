# backend/test_config.py
from backend.app.config import settings

print(settings.MONGODB_URL)
print(settings.SECRET_KEY)