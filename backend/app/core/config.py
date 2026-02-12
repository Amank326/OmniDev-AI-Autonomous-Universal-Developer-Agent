"""Application configuration."""

import secrets
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


def generate_secret_key() -> str:
    """Generate a secure random secret key."""
    return secrets.token_urlsafe(32)


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project Info
    PROJECT_NAME: str = "OmniDev AI Platform"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "Production-ready AI platform with autonomous agents, "
        "real-time collaboration, and cloud-native architecture"
    )
    API_V1_STR: str = "/api/v1"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://omnidev:omnidev@localhost:5432/omnidev"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    # WARNING: SECRET_KEY must be set in production via environment variable
    # Generate a secure key: python -c "import secrets; print(secrets.token_urlsafe(32))"
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    def __init__(self, **kwargs):
        """Initialize settings and validate SECRET_KEY."""
        super().__init__(**kwargs)
        if not self.SECRET_KEY or self.SECRET_KEY == "your-secret-key-change-in-production":
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "SECRET_KEY must be set in production environment. "
                    "Generate one using: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            # Auto-generate for development only
            self.SECRET_KEY = generate_secret_key()

    # Email Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: str = "noreply@omnidev.ai"
    EMAILS_FROM_NAME: str = "OmniDev AI"

    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # AI Agents Configuration
    AGENT_MAX_WORKERS: int = 5
    AGENT_TIMEOUT: int = 300

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    ENVIRONMENT: str = "development"

    # WebSocket
    WEBSOCKET_URL: str = "ws://localhost:8000"


settings = Settings()
