"""
Email Configuration

Configures SMTP settings for email sending.

Environment Variables:
    SMTP_HOST: SMTP server hostname (default: localhost)
    SMTP_PORT: SMTP server port (default: 587)
    SMTP_USER: SMTP username/email
    SMTP_PASSWORD: SMTP password
    SMTP_FROM_EMAIL: From email address
    SMTP_FROM_NAME: From display name
    SMTP_USE_TLS: Use TLS encryption (default: true)
    SMTP_USE_SSL: Use SSL encryption (default: false)
    SMTP_TIMEOUT: Connection timeout in seconds (default: 10)

Example .env:
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=your-email@gmail.com
    SMTP_PASSWORD=your-app-password
    SMTP_FROM_EMAIL=noreply@omnidev.ai
    SMTP_FROM_NAME=OmniDev AI
    SMTP_USE_TLS=true
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class EmailConfig(BaseSettings):
    """Email/SMTP configuration."""
    
    smtp_host: str = os.getenv("SMTP_HOST", "localhost")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: Optional[str] = os.getenv("SMTP_USER")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "noreply@omnidev.ai")
    smtp_from_name: str = os.getenv("SMTP_FROM_NAME", "OmniDev AI")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    smtp_use_ssl: bool = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    smtp_timeout: int = int(os.getenv("SMTP_TIMEOUT", "10"))
    
    # Email feature flags
    enable_email: bool = os.getenv("ENABLE_EMAIL", "false").lower() == "true"
    enable_verification_emails: bool = os.getenv("ENABLE_VERIFICATION_EMAILS", "false").lower() == "true"
    require_email_verification: bool = os.getenv("REQUIRE_EMAIL_VERIFICATION", "false").lower() == "true"
    
    # Email token expiration (in seconds)
    verification_token_expire: int = 86400  # 24 hours
    password_reset_token_expire: int = 3600  # 1 hour
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables
    
    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        return (
            self.enable_email and
            self.smtp_user is not None and
            self.smtp_password is not None and
            self.smtp_host is not None
        )
    
    def get_from_address(self) -> str:
        """Get formatted from address."""
        return f"{self.smtp_from_name} <{self.smtp_from_email}>"


# Global configuration instance
email_config = EmailConfig()
