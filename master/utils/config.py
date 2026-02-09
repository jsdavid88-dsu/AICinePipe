"""
Configuration management for AIPipeline.

Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars

# Project root: two levels up from this file (master/utils/config.py -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings:
    """Application settings loaded from environment variables."""

    # Server
    MASTER_HOST: str = os.getenv("MASTER_HOST", "0.0.0.0")
    MASTER_PORT: int = int(os.getenv("MASTER_PORT", "8002"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Paths
    PROJECTS_DIR: str = os.getenv("PROJECTS_DIR", str(_PROJECT_ROOT / "projects"))
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", str(_PROJECT_ROOT / "data" / "aipipeline.db"))
    LOG_DIR: str = os.getenv("LOG_DIR", str(_PROJECT_ROOT / "logs"))
    WORKFLOWS_DIR: str = os.getenv("WORKFLOWS_DIR", str(_PROJECT_ROOT / "workflows"))

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

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode."""
        return cls.ENVIRONMENT.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()
