"""WebSocket route handlers for different message types."""

import json
import logging
from typing import Any, Dict

from fastapi import WebSocket

from app.utils.websocket import manager
from app.realtime.events import event_bus

logger = logging.getLogger(__name__)


async def handle_websocket_message(
    websocket: WebSocket,
    user_id: int,
    raw_data: str,
) -> None:
    """Route incoming WebSocket messages to appropriate handlers.

    Expected message format:
        {"type": "...", "payload": {...}}
    """
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        await websocket.send_text(
            json.dumps({"type": "error", "message": "Invalid JSON"})
        )
        return

    msg_type = data.get("type", "unknown")
    payload = data.get("payload", {})

    handler = MESSAGE_HANDLERS.get(msg_type, _handle_unknown)
    await handler(websocket, user_id, payload)


async def _handle_ping(
    websocket: WebSocket, user_id: int, payload: Dict[str, Any]
) -> None:
    """Respond to a ping with pong."""
    await websocket.send_text(json.dumps({"type": "pong"}))


async def _handle_subscribe(
    websocket: WebSocket, user_id: int, payload: Dict[str, Any]
) -> None:
    """Subscribe to real-time events for a resource."""
    channel = payload.get("channel")
    if not channel:
        await websocket.send_text(
            json.dumps({"type": "error", "message": "channel required"})
        )
        return

    logger.info(f"User {user_id} subscribed to channel '{channel}'")
    await websocket.send_text(
        json.dumps({"type": "subscribed", "channel": channel})
    )


async def _handle_agent_input(
    websocket: WebSocket, user_id: int, payload: Dict[str, Any]
) -> None:
    """Handle interactive agent input from the user."""
    await event_bus.publish("agent.user_input", {
        "user_id": user_id,
        "input": payload,
    })
    await websocket.send_text(
        json.dumps({"type": "ack", "message": "Input received"})
    )


async def _handle_unknown(
    websocket: WebSocket, user_id: int, payload: Dict[str, Any]
) -> None:
    """Handle unknown message types."""
    await websocket.send_text(
        json.dumps({"type": "error", "message": "Unknown message type"})
    )


# Route table: message type -> handler
MESSAGE_HANDLERS = {
    "ping": _handle_ping,
    "subscribe": _handle_subscribe,
    "agent_input": _handle_agent_input,
}
