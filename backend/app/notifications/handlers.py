"""Notification handlers for different channels."""

import logging
import json
from typing import Dict, Any, Optional

from app.utils.websocket import manager

logger = logging.getLogger(__name__)


class EmailNotificationHandler:
    """Handle email notifications."""

    async def send(self, user_email: str, title: str, message: str) -> bool:
        """Send an email notification."""
        from app.services.email import email_service

        html_content = f"""
        <html>
            <body>
                <h2>{title}</h2>
                <p>{message}</p>
                <hr>
                <p style="color: #666; font-size: 12px;">OmniDev AI Platform</p>
            </body>
        </html>
        """
        return await email_service.send_email(
            to_email=user_email,
            subject=title,
            html_content=html_content,
        )


class WebSocketNotificationHandler:
    """Handle WebSocket notifications."""

    async def send(
        self,
        user_id: int,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a WebSocket notification."""
        try:
            payload = json.dumps({
                "type": "notification",
                "title": title,
                "message": message,
                "data": data,
            })
            await manager.send_personal_message(payload, user_id)
            return True
        except Exception as e:
            logger.error(f"WebSocket notification failed: {e}")
            return False


class SMSNotificationHandler:
    """Handle SMS notifications (placeholder for Twilio integration)."""

    async def send(self, phone_number: str, message: str) -> bool:
        """Send an SMS notification."""
        logger.info(f"SMS notification to {phone_number}: {message}")
        # TODO: Implement Twilio integration
        return True


class PushNotificationHandler:
    """Handle push notifications (placeholder for Firebase integration)."""

    async def send(
        self,
        device_token: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a push notification."""
        logger.info(f"Push notification to {device_token}: {title}")
        # TODO: Implement Firebase Cloud Messaging integration
        return True


# Singleton handlers
email_handler = EmailNotificationHandler()
websocket_handler = WebSocketNotificationHandler()
sms_handler = SMSNotificationHandler()
push_handler = PushNotificationHandler()
