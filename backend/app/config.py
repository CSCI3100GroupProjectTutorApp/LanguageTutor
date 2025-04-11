from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "language_tutoring_app")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # SQLite settings
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "data/word_storage.db")
    ENABLE_AUTO_SYNC: bool = os.getenv("ENABLE_AUTO_SYNC", "true").lower() == "true"
    AUTO_SYNC_INTERVAL: int = int(os.getenv("AUTO_SYNC_INTERVAL", "60"))

    # Youdao API
    YOUDAO_APP_KEY: str = os.getenv("YOUDAO_APP_KEY")
    YOUDAO_APP_SECRET: str = os.getenv("YOUDAO_APP_SECRET")

    # Google Cloud Vision API credentials
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Email settings
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_SENDER: Optional[str] = os.getenv("EMAIL_SENDER")
    EMAIL_USERNAME: Optional[str] = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD: Optional[str] = os.getenv("EMAIL_PASSWORD")
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()



