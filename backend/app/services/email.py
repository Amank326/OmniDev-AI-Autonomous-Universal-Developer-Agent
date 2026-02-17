"""Email service for sending notifications."""

import logging
from typing import Optional
from emails.message import Message

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending emails."""

    def __init__(self):
        """Initialize email service."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email."""
        try:
            message = Message(
                subject=subject,
                html=html_content,
                text=text_content,
                mail_from=(self.from_name, self.from_email),
            )

            if self.smtp_host:
                response = message.send(
                    to=to_email,
                    smtp={
                        "host": self.smtp_host,
                        "port": self.smtp_port,
                        "user": self.smtp_user,
                        "password": self.smtp_password,
                        "tls": True,
                    },
                )
                return response.status_code == 250
            else:
                logger.warning("SMTP not configured, email not sent")
                return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def send_verification_email(self, to_email: str, token: str) -> bool:
        """Send email verification."""
        verification_link = f"http://localhost:3000/verify?token={token}"
        html_content = f"""
        <html>
            <body>
                <h1>Welcome to OmniDev AI!</h1>
                <p>Please verify your email by clicking the link below:</p>
                <a href="{verification_link}">Verify Email</a>
            </body>
        </html>
        """
        return await self.send_email(
            to_email=to_email,
            subject="Verify your email",
            html_content=html_content,
        )

    async def send_password_reset(self, to_email: str, token: str) -> bool:
        """Send password reset email."""
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        html_content = f"""
        <html>
            <body>
                <h1>Password Reset Request</h1>
                <p>Click the link below to reset your password:</p>
                <a href="{reset_link}">Reset Password</a>
                <p>This link will expire in 1 hour.</p>
            </body>
        </html>
        """
        return await self.send_email(
            to_email=to_email,
            subject="Password Reset",
            html_content=html_content,
        )


email_service = EmailService()
