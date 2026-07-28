"""
Central application settings.
Loaded once from environment variables / .env file, validated by Pydantic.
Never read os.environ directly anywhere else in the codebase — import `settings` from here.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # General
    APP_NAME: str = "ClipMind AI"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # Will be used starting Module 3 (Database)
    DATABASE_URL: str = "postgresql://clipmind:clipmind@db:5432/clipmind"

    # Will be used starting Module for Celery/Redis
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "changeme-dev-only-secret"
    OPENROUTER_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""

    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024 * 1024  # 5GB, per your spec
    ALLOWED_VIDEO_EXTENSIONS: tuple = (".mp4", ".mov", ".avi", ".mkv")
    UPLOAD_DIR: str = "uploads"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unrelated env vars instead of crashing
    )


# Singleton instance imported everywhere else in the app
settings = Settings()
