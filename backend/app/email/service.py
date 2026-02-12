"""
Email Service Implementation

Handles sending emails via SMTP with template support.

Features:
    - SMTP email sending with TLS/SSL
    - Template-based emails
    - Retry logic for failed sends
    - HTML and plain text support
    - Async email sending
    - Email logging and tracking

Classes:
    EmailService: Main email service class
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.email.config import email_config

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending emails via SMTP.
    
    Handles SMTP connection, template rendering, and email delivery.
    """
    
    def __init__(self, config=None):
        """
        Initialize email service.
        
        Args:
            config: EmailConfig instance (uses global if not provided)
        """
        self.config = config or email_config
        self.max_retries = 3
    
    def is_enabled(self) -> bool:
        """Check if email service is enabled and configured."""
        return self.config.is_configured()
    
    def send_email(
        self,
        recipient_email: str,
        subject: str,
        html_content: str,
        plain_text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        retry_count: int = 0
    ) -> bool:
        """
        Send an email.
        
        Args:
            recipient_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_text_content: Plain text fallback
            cc: CC recipients
            bcc: BCC recipients
            reply_to: Reply-to address
            retry_count: Internal retry counter
        
        Returns:
            True if successful, False otherwise
        
        Example:
            success = email_service.send_email(
                recipient_email="user@example.com",
                subject="Welcome to OmniDev",
                html_content="<h1>Welcome!</h1>",
                plain_text_content="Welcome!"
            )
        """
        if not self.is_enabled():
            logger.warning("Email service is not enabled or configured")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.config.get_from_address()
            message["To"] = recipient_email
            
            if cc:
                message["Cc"] = ", ".join(cc)
            if reply_to:
                message["Reply-To"] = reply_to
            
            # Add plain text part
            if plain_text_content:
                message.attach(MIMEText(plain_text_content, "plain"))
            else:
                # Strip HTML tags for plain text
                import re
                plain_text = re.sub("<[^<]+?>", "", html_content)
                message.attach(MIMEText(plain_text, "plain"))
            
            # Add HTML part
            message.attach(MIMEText(html_content, "html"))
            
            # Prepare recipient list
            recipients = [recipient_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # Send email
            self._send_via_smtp(message, recipients)
            
            logger.info(
                "Email sent successfully",
                extra={
                    "recipient": recipient_email,
                    "subject": subject,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return True
        
        except smtplib.SMTPException as e:
            logger.error(
                f"SMTP error sending email: {str(e)}",
                extra={
                    "recipient": recipient_email,
                    "error": str(e),
                    "retry_count": retry_count
                }
            )
            
            # Retry logic
            if retry_count < self.max_retries:
                logger.info(f"Retrying email send (attempt {retry_count + 1}/{self.max_retries})")
                return self.send_email(
                    recipient_email,
                    subject,
                    html_content,
                    plain_text_content,
                    cc,
                    bcc,
                    reply_to,
                    retry_count + 1
                )
            
            return False
        
        except Exception as e:
            logger.error(
                f"Unexpected error sending email: {str(e)}",
                extra={
                    "recipient": recipient_email,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return False
    
    def _send_via_smtp(self, message: MIMEMultipart, recipients: List[str]) -> None:
        """
        Send message via SMTP.
        
        Args:
            message: MIME message object
            recipients: List of recipient email addresses
        
        Raises:
            SMTPException: If SMTP operation fails
        """
        # Choose connection method
        if self.config.smtp_use_ssl:
            smtp = smtplib.SMTP_SSL(
                self.config.smtp_host,
                self.config.smtp_port,
                timeout=self.config.smtp_timeout
            )
        else:
            smtp = smtplib.SMTP(
                self.config.smtp_host,
                self.config.smtp_port,
                timeout=self.config.smtp_timeout
            )
        
        try:
            # Start TLS if configured
            if self.config.smtp_use_tls:
                smtp.starttls()
            
            # Login if credentials provided
            if self.config.smtp_user and self.config.smtp_password:
                smtp.login(self.config.smtp_user, self.config.smtp_password)
            
            # Send email
            smtp.sendmail(self.config.smtp_from_email, recipients, message.as_string())
        
        finally:
            smtp.quit()
    
    def send_verification_email(
        self,
        recipient_email: str,
        verification_token: str,
        app_url: str = "http://localhost:3000"
    ) -> bool:
        """
        Send email verification email.
        
        Args:
            recipient_email: Recipient email address
            verification_token: Email verification token
            app_url: Application URL for verification link
        
        Returns:
            True if successful
        
        Example:
            success = email_service.send_verification_email(
                "user@example.com",
                "token-123",
                "https://app.omnidev.ai"
            )
        """
        verification_url = f"{app_url}/verify-email?token={verification_token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Verify Your Email</h2>
                    <p>Welcome to OmniDev AI! Please verify your email address to complete registration.</p>
                    <p>
                        <a href="{verification_url}" style="
                            display: inline-block;
                            padding: 12px 24px;
                            background-color: #007bff;
                            color: white;
                            text-decoration: none;
                            border-radius: 5px;
                            margin: 20px 0;
                        ">
                            Verify Email
                        </a>
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        Or copy this link: <br>
                        <code>{verification_url}</code>
                    </p>
                    <p style="color: #999; font-size: 12px; margin-top: 30px;">
                        This link expires in 24 hours.
                    </p>
                </div>
            </body>
        </html>
        """
        
        plain_text = f"""
        Verify Your Email
        
        Welcome to OmniDev AI! Please verify your email address to complete registration.
        
        Verify Email: {verification_url}
        
        This link expires in 24 hours.
        """
        
        return self.send_email(
            recipient_email,
            subject="Verify Your Email - OmniDev AI",
            html_content=html_content,
            plain_text_content=plain_text
        )
    
    def send_password_reset_email(
        self,
        recipient_email: str,
        reset_token: str,
        app_url: str = "http://localhost:3000"
    ) -> bool:
        """
        Send password reset email.
        
        Args:
            recipient_email: Recipient email address
            reset_token: Password reset token
            app_url: Application URL
        
        Returns:
            True if successful
        """
        reset_url = f"{app_url}/reset-password?token={reset_token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Reset Your Password</h2>
                    <p>We received a request to reset your password. Click the button below to reset it.</p>
                    <p>
                        <a href="{reset_url}" style="
                            display: inline-block;
                            padding: 12px 24px;
                            background-color: #28a745;
                            color: white;
                            text-decoration: none;
                            border-radius: 5px;
                            margin: 20px 0;
                        ">
                            Reset Password
                        </a>
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        Or copy this link: <br>
                        <code>{reset_url}</code>
                    </p>
                    <p style="color: #999; font-size: 12px; margin-top: 30px;">
                        This link expires in 1 hour. If you didn't request this, you can ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        plain_text = f"""
        Reset Your Password
        
        We received a request to reset your password. Click the link below to reset it.
        
        Reset Password: {reset_url}
        
        This link expires in 1 hour. If you didn't request this, you can ignore this email.
        """
        
        return self.send_email(
            recipient_email,
            subject="Reset Your Password - OmniDev AI",
            html_content=html_content,
            plain_text_content=plain_text
        )
    
    def send_welcome_email(
        self,
        recipient_email: str,
        username: str,
        app_url: str = "http://localhost:3000"
    ) -> bool:
        """
        Send welcome email to new user.
        
        Args:
            recipient_email: Recipient email address
            username: User's username
            app_url: Application URL
        
        Returns:
            True if successful
        """
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Welcome to OmniDev AI, {username}!</h2>
                    <p>Your account has been created successfully. You can now log in and start collaborating.</p>
                    <p>
                        <a href="{app_url}/login" style="
                            display: inline-block;
                            padding: 12px 24px;
                            background-color: #007bff;
                            color: white;
                            text-decoration: none;
                            border-radius: 5px;
                            margin: 20px 0;
                        ">
                            Go to Dashboard
                        </a>
                    </p>
                    <h3>Getting Started</h3>
                    <ul>
                        <li>Create your first project</li>
                        <li>Invite team members</li>
                        <li>Start collaborating in real-time</li>
                    </ul>
                    <p style="color: #666; font-size: 14px;">
                        Need help? Check out our documentation at <a href="{app_url}/docs">docs.omnidev.ai</a>
                    </p>
                </div>
            </body>
        </html>
        """
        
        plain_text = f"""
        Welcome to OmniDev AI, {username}!
        
        Your account has been created successfully. You can now log in and start collaborating.
        
        Go to Dashboard: {app_url}/login
        
        Getting Started:
        - Create your first project
        - Invite team members
        - Start collaborating in real-time
        
        Need help? Check out our documentation at {app_url}/docs
        """
        
        return self.send_email(
            recipient_email,
            subject=f"Welcome to OmniDev AI, {username}!",
            html_content=html_content,
            plain_text_content=plain_text
        )
    
    def send_notification_email(
        self,
        recipient_email: str,
        subject: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None
    ) -> bool:
        """
        Send general notification email.
        
        Args:
            recipient_email: Recipient email address
            subject: Email subject
            title: Email title/heading
            message: Email message body
            action_url: Optional action URL
            action_text: Optional action button text
        
        Returns:
            True if successful
        """
        action_button = ""
        if action_url and action_text:
            action_button = f"""
            <p>
                <a href="{action_url}" style="
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                ">
                    {action_text}
                </a>
            </p>
            """
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>{title}</h2>
                    <p>{message}</p>
                    {action_button}
                </div>
            </body>
        </html>
        """
        
        plain_text = f"""
        {title}
        
        {message}
        
        {f'{action_text}: {action_url}' if action_url and action_text else ''}
        """
        
        return self.send_email(
            recipient_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_text
        )


# Global email service instance
email_service = EmailService()
