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

    # Database
    DATABASE_URL: str = "postgresql://clipmind:clipmind@db:5432/clipmind"

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"

    # Auth
    JWT_SECRET: str = "changeme-dev-only-secret"

    # Uploads
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024 * 1024  # 5GB
    ALLOWED_VIDEO_EXTENSIONS: tuple = (".mp4", ".mov", ".avi", ".mkv")
    UPLOAD_DIR: str = "uploads"

    # OpenRouter (AI)
    OPENROUTER_API_KEY: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""

    # Resend (email)
    RESEND_API_KEY: str = ""

    # Cloudflare R2 (persistent file storage)
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""

    PROXY_HOST: str = ""
    PROXY_PORT: str = ""
    PROXY_USERNAME: str = ""
    PROXY_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()