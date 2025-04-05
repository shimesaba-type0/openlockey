import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "OpenLockey"
    SECRET_KEY: str
    DEBUG: bool = False
    LISTEN_IP: str = "0.0.0.0"
    LISTEN_PORT: int = 9080
    
    # データベース設定
    DATABASE_URL: str
    
    # セキュリティ設定
    SESSION_COOKIE_NAME: str = "openlockey_session"
    SESSION_EXPIRE_HOURS: int = 72
    FAIL_LOCK_ATTEMPTS: int = 5
    FAIL_LOCK_WINDOW_MINUTES: int = 30
    FAIL_LOCK_DURATION_HOURS: int = 2
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

