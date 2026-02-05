"""
Configuration management for AIPipeline.

Loads settings from environment variables with sensible defaults.
"""

import os
from typing import Optional
from functools import lru_cache

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars


class Settings:
    """Application settings loaded from environment variables."""
    
    # Server
    MASTER_HOST: str = os.getenv("MASTER_HOST", "0.0.0.0")
    MASTER_PORT: int = int(os.getenv("MASTER_PORT", "8002"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # ComfyUI
    COMFYUI_URL: str = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
    
    # Worker
    MASTER_WS_URL: str = os.getenv("MASTER_WS_URL", "ws://localhost:8002/ws/worker")
    
    # Frontend
    API_BASE_URL: str = os.getenv("VITE_API_BASE_URL", "http://127.0.0.1:8002")
    
    # Security (Phase 4)
    JWT_SECRET_KEY: Optional[str] = os.getenv("JWT_SECRET_KEY")
    ALLOWED_ORIGINS: list = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    ).split(",")
    
    # Database (Phase 3)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode."""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()
