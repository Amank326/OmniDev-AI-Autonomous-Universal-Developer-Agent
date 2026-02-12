"""
WebSocket Connection Manager
Handles WebSocket connections, rooms, and message broadcasting
"""

import json
import logging
from typing import Dict, List, Set
from datetime import datetime
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""

    def __init__(self):
        """Initialize connection manager"""
        # {room_id: {connection_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # {connection_id: user_id}
        self.connection_users: Dict[str, str] = {}
        # {room_id: {user_id}}
        self.room_users: Dict[str, Set[str]] = {}
        # Track message history per room (last 50 messages)
        self.message_history: Dict[str, List[dict]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        room_id: str,
        user_id: str,
        connection_id: str,
    ):
        """Accept WebSocket connection and add to room"""
        await websocket.accept()
        
        # Add to active connections
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
            self.room_users[room_id] = set()
            self.message_history[room_id] = []

        self.active_connections[room_id][connection_id] = websocket
        self.connection_users[connection_id] = user_id
        self.room_users[room_id].add(user_id)

        logger.info(
            f"Client {user_id} connected to room {room_id} "
            f"(connection_id: {connection_id})"
        )

        # Broadcast user joined message
        await self.broadcast_to_room(
            room_id=room_id,
            message={
                "type": "user_joined",
                "user_id": user_id,
                "room_id": room_id,
                "timestamp": datetime.now().isoformat(),
                "active_users": list(self.room_users[room_id]),
                "active_count": len(self.room_users[room_id]),
            },
            exclude_connection=None,  # Include sender
        )

    def disconnect(self, room_id: str, connection_id: str):
        """Remove connection from room"""
        if room_id in self.active_connections:
            if connection_id in self.active_connections[room_id]:
                del self.active_connections[room_id][connection_id]
                user_id = self.connection_users.pop(connection_id, None)

                # If user has no more connections in this room, remove from room_users
                user_connections = [
                    cid
                    for cid, uid in self.connection_users.items()
                    if uid == user_id and cid in self.active_connections.get(room_id, {})
                ]
                if not user_connections and user_id:
                    self.room_users[room_id].discard(user_id)

                logger.info(
                    f"Client {user_id} disconnected from room {room_id} "
                    f"(connection_id: {connection_id})"
                )

    async def broadcast_to_room(
        self,
        room_id: str,
        message: dict,
        exclude_connection: str = None,
    ):
        """Broadcast message to all connections in room"""
        if room_id not in self.active_connections:
            return

        # Add to message history
        message_with_timestamp = {
            **message,
            "timestamp": datetime.now().isoformat(),
        }
        self.message_history[room_id].append(message_with_timestamp)
        # Keep only last 50 messages
        if len(self.message_history[room_id]) > 50:
            self.message_history[room_id] = self.message_history[room_id][-50:]

        disconnected = []
        for connection_id, websocket in self.active_connections[room_id].items():
            if exclude_connection and connection_id == exclude_connection:
                continue

            try:
                await websocket.send_json(message_with_timestamp)
            except Exception as e:
                logger.error(
                    f"Error sending message to {connection_id} in room {room_id}: {e}"
                )
                disconnected.append(connection_id)

        # Clean up disconnected
        for connection_id in disconnected:
            self.disconnect(room_id, connection_id)

    async def send_to_connection(
        self, room_id: str, connection_id: str, message: dict
    ):
        """Send message to specific connection"""
        if (
            room_id in self.active_connections
            and connection_id in self.active_connections[room_id]
        ):
            try:
                await self.active_connections[room_id][connection_id].send_json(
                    message
                )
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(room_id, connection_id)

    async def send_to_user(
        self, room_id: str, user_id: str, message: dict
    ):
        """Send message to all connections of a specific user"""
        sent_count = 0
        if room_id not in self.active_connections:
            return sent_count

        for connection_id, websocket in self.active_connections[room_id].items():
            if self.connection_users.get(connection_id) == user_id:
                try:
                    await websocket.send_json(message)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error sending message to {connection_id}: {e}")

        return sent_count

    async def broadcast_to_all_rooms(self, message: dict):
        """Broadcast message to all active rooms"""
        for room_id in self.active_connections:
            await self.broadcast_to_room(room_id, message)

    def get_room_users(self, room_id: str) -> List[str]:
        """Get list of active users in room"""
        return list(self.room_users.get(room_id, set()))

    def get_room_user_count(self, room_id: str) -> int:
        """Get number of active users in room"""
        return len(self.room_users.get(room_id, set()))

    def get_room_connection_count(self, room_id: str) -> int:
        """Get number of active connections in room"""
        return len(self.active_connections.get(room_id, {}))

    def get_message_history(self, room_id: str, limit: int = 50) -> List[dict]:
        """Get message history for room"""
        messages = self.message_history.get(room_id, [])
        return messages[-limit:] if limit else messages

    def get_stats(self) -> dict:
        """Get WebSocket statistics"""
        total_connections = sum(
            len(conns) for conns in self.active_connections.values()
        )
        total_rooms = len(self.active_connections)
        total_users = len(set(self.connection_users.values()))

        room_stats = {}
        for room_id, connections in self.active_connections.items():
            room_stats[room_id] = {
                "connections": len(connections),
                "users": list(self.room_users.get(room_id, set())),
                "user_count": len(self.room_users.get(room_id, set())),
            }

        return {
            "total_connections": total_connections,
            "total_rooms": total_rooms,
            "total_users": total_users,
            "rooms": room_stats,
        }


# Global connection manager instance
manager = ConnectionManager()
