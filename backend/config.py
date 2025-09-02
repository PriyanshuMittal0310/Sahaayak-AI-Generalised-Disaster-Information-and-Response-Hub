from pydantic import BaseSettings, AnyHttpUrl
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sahaayak AI"
    VERSION: str = "0.3.0"
    API_PREFIX: str = "/api"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # React frontend
        "http://localhost:8000",  # Local development
    ]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/sahaayak")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # USGS API
    USGS_API_URL: str = os.getenv("USGS_API_URL", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson")
    
    class Config:
        case_sensitive = True

settings = Settings()
