from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str
    
    # Redis (for tokens and sessions)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: str = "0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_USERNAME: Optional[str] = None
    REDIS_SSL: bool = False
    
    # Security
    SECRET_KEY: str
    JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_HOURS: int = 12
    
    # Email
    EMAIL_HOST: str
    EMAIL_PORT: int = 587
    EMAIL_FROM: str
    EMAIL_USER: str
    EMAIL_PASSWORD: str
    #RESEND_API_KEY: str
    SENDGRID_API_KEY: str
    EMAIL_FROM_NAME: str = "Diabetic Risk Prediction"
    # Admin
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    
    # Application
    APP_NAME: str = "Diabetes Risk Prediction API"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
