"""Configuration for ASCII Lab."""
import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    APP_ENV: str = "development"
    MAX_UPLOAD_SIZE_MB: int = 25
    MAX_IMAGE_WIDTH: int = 1920
    MAX_VIDEO_DURATION_SECONDS: int = 60
    CORS_ORIGINS: str = "*"
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    
    @property
    def max_upload_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


settings = Settings()