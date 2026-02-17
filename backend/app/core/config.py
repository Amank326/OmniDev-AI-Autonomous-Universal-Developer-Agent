"""Application configuration."""

import secrets
from typing import List, Optional, Union
from pydantic import field_validator
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

    # Environment (must be declared before __init__ uses it)
    ENVIRONMENT: str = "development"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins — uses CORS_ORIGINS env if set, else BACKEND_CORS_ORIGINS."""
        if self.CORS_ORIGINS:
            return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return self.BACKEND_CORS_ORIGINS

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        raise ValueError(v)

    # CORS override (comma-separated) — set in production
    CORS_ORIGINS: Optional[str] = None

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://omnidev:omnidev_password@localhost:5432/omnidev"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        """Convert postgres:// to postgresql+asyncpg:// for Render/Railway."""
        if v and v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v and v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

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
        insecure_defaults = {
            "",
            "your-secret-key-change-in-production",
            "your-super-secret-key-change-in-production-min-32-chars",
        }
        if self.SECRET_KEY in insecure_defaults:
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

    # Rate Limiting
    RATE_LIMIT_AUTHENTICATED: int = 100  # requests per minute
    RATE_LIMIT_UNAUTHENTICATED: int = 20  # requests per minute

    # WebSocket
    WEBSOCKET_URL: str = "ws://localhost:8000"


settings = Settings()
