"""
WebSocket Connection Manager for Real-time Updates

Manages WebSocket connections, broadcasts updates to connected clients,
and handles connection lifecycle events (connect, disconnect).

Classes:
    ConnectionManager: Manages WebSocket connections and broadcasts

Features:
    - Multi-room support (project-based, task-based, user-based)
    - Connection tracking and cleanup
    - Broadcast messaging with filtering
    - Connection state management
    - Error handling and logging
"""

import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    
    Uses room-based architecture where clients can subscribe to specific rooms:
    - project:{project_id} - Project updates
    - task:{task_id} - Task updates  
    - user:{user_id} - User-specific updates
    - global - Broadcast to all connected clients
    
    Attributes:
        active_connections: Dict mapping room names to sets of WebSocket connections
        connection_metadata: Dict storing metadata about connections (user_id, joined_at, etc.)
    
    Example:
        manager = ConnectionManager()
        
        # In endpoint
        async def websocket_endpoint(websocket: WebSocket):
            await manager.connect(websocket, room="project:123", user_id=456)
            try:
                while True:
                    data = await websocket.receive_text()
                    # Process data
            except WebSocketDisconnect:
                manager.disconnect(websocket, room="project:123")
    """
    
    def __init__(self):
        """Initialize connection manager with empty connections and metadata."""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(
        self, 
        websocket: WebSocket, 
        room: str,
        user_id: int
    ) -> None:
        """
        Accept and register a WebSocket connection to a specific room.
        
        Args:
            websocket: The WebSocket connection to register
            room: The room identifier (e.g., 'project:123', 'task:456')
            user_id: The user ID establishing the connection
        
        Raises:
            RuntimeError: If WebSocket acceptance fails
        
        Example:
            await manager.connect(websocket, "project:123", user_id=456)
        """
        try:
            await websocket.accept()
            
            # Create room if it doesn't exist
            if room not in self.active_connections:
                self.active_connections[room] = set()
            
            # Add connection to room
            self.active_connections[room].add(websocket)
            
            # Store metadata
            self.connection_metadata[websocket] = {
                "user_id": user_id,
                "room": room,
                "joined_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            logger.info(
                f"WebSocket connected",
                extra={
                    "user_id": user_id,
                    "room": room,
                    "total_in_room": len(self.active_connections[room]),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except RuntimeError as e:
            logger.error(f"Failed to accept WebSocket connection: {str(e)}")
            raise
    
    def disconnect(self, websocket: WebSocket, room: str) -> None:
        """
        Remove a WebSocket connection from a room.
        
        Args:
            websocket: The WebSocket connection to remove
            room: The room identifier
        
        Example:
            manager.disconnect(websocket, "project:123")
        """
        if room in self.active_connections:
            self.active_connections[room].discard(websocket)
            
            # Clean up empty rooms
            if len(self.active_connections[room]) == 0:
                del self.active_connections[room]
        
        # Remove metadata
        if websocket in self.connection_metadata:
            metadata = self.connection_metadata.pop(websocket)
            logger.info(
                f"WebSocket disconnected",
                extra={
                    "user_id": metadata.get("user_id"),
                    "room": room,
                    "duration": f"{(datetime.utcnow().isoformat())} - {metadata.get('joined_at')}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    async def broadcast_to_room(
        self,
        room: str,
        message: Dict[str, Any],
        exclude_user: Optional[int] = None
    ) -> int:
        """
        Broadcast a message to all connections in a specific room.
        
        Args:
            room: The room identifier
            message: The message dict to broadcast (will be JSON-encoded)
            exclude_user: Optional user_id to exclude from broadcast
        
        Returns:
            Number of messages successfully sent
        
        Example:
            await manager.broadcast_to_room(
                "project:123",
                {"type": "task_updated", "task_id": 456, "status": "completed"}
            )
        """
        if room not in self.active_connections:
            return 0
        
        sent_count = 0
        disconnected = []
        
        for connection in self.active_connections[room]:
            # Skip if exclude_user specified and matches
            metadata = self.connection_metadata.get(connection, {})
            if exclude_user and metadata.get("user_id") == exclude_user:
                continue
            
            try:
                message_with_timestamp = {
                    **message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "room": room
                }
                await connection.send_json(message_with_timestamp)
                sent_count += 1
                
            except RuntimeError:
                # Connection likely closed
                disconnected.append(connection)
            except Exception as e:
                logger.error(
                    f"Error broadcasting to connection in room {room}: {str(e)}"
                )
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn, room)
        
        logger.debug(
            f"Broadcast to room {room}: {sent_count} messages sent",
            extra={"room": room, "sent_count": sent_count}
        )
        
        return sent_count
    
    async def broadcast_to_user(
        self,
        user_id: int,
        message: Dict[str, Any]
    ) -> int:
        """
        Broadcast a message to all connections belonging to a specific user.
        
        Args:
            user_id: The user ID to broadcast to
            message: The message dict to broadcast
        
        Returns:
            Number of messages successfully sent
        
        Example:
            await manager.broadcast_to_user(
                456,
                {"type": "notification", "content": "Your project was shared"}
            )
        """
        sent_count = 0
        
        for connection, metadata in list(self.connection_metadata.items()):
            if metadata.get("user_id") == user_id:
                try:
                    message_with_timestamp = {
                        **message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await connection.send_json(message_with_timestamp)
                    sent_count += 1
                    
                except RuntimeError:
                    room = metadata.get("room")
                    if room:
                        self.disconnect(connection, room)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
        
        logger.debug(
            f"Broadcast to user {user_id}: {sent_count} messages sent",
            extra={"user_id": user_id, "sent_count": sent_count}
        )
        
        return sent_count
    
    async def broadcast_global(self, message: Dict[str, Any]) -> int:
        """
        Broadcast a message to all connected clients across all rooms.
        
        Args:
            message: The message dict to broadcast
        
        Returns:
            Total number of messages successfully sent
        
        Example:
            await manager.broadcast_global({
                "type": "system_notification",
                "content": "System maintenance scheduled"
            })
        """
        total_sent = 0
        
        for room in list(self.active_connections.keys()):
            sent = await self.broadcast_to_room(room, message)
            total_sent += sent
        
        logger.info(
            f"Global broadcast sent to {total_sent} connections",
            extra={"total_sent": total_sent, "rooms": len(self.active_connections)}
        )
        
        return total_sent
    
    def get_room_stats(self, room: str) -> Dict[str, Any]:
        """
        Get statistics about a specific room.
        
        Args:
            room: The room identifier
        
        Returns:
            Dict with connection count, user list, and room status
        
        Example:
            stats = manager.get_room_stats("project:123")
            # {"connections": 5, "users": [1, 2, 3], "room": "project:123"}
        """
        connections = self.active_connections.get(room, set())
        users = set()
        
        for conn in connections:
            metadata = self.connection_metadata.get(conn, {})
            if "user_id" in metadata:
                users.add(metadata["user_id"])
        
        return {
            "room": room,
            "connections": len(connections),
            "users": list(users),
            "user_count": len(users),
            "active": len(connections) > 0
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get overall statistics about all rooms and connections.
        
        Returns:
            Dict with total connections, rooms, and per-room stats
        
        Example:
            stats = manager.get_all_stats()
            # {"total_connections": 42, "total_rooms": 5, "rooms": {...}}
        """
        total_connections = sum(
            len(conns) for conns in self.active_connections.values()
        )
        
        rooms_stats = {
            room: self.get_room_stats(room)
            for room in self.active_connections.keys()
        }
        
        return {
            "total_connections": total_connections,
            "total_rooms": len(self.active_connections),
            "rooms": rooms_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def send_to_connection(
        self,
        websocket: WebSocket,
        message: Dict[str, Any]
    ) -> bool:
        """
        Send a message to a specific WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to send to
            message: The message dict to send
        
        Returns:
            True if sent successfully, False otherwise
        
        Example:
            success = await manager.send_to_connection(ws, {"type": "ping"})
        """
        try:
            message_with_timestamp = {
                **message,
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_json(message_with_timestamp)
            return True
        except RuntimeError:
            # Connection closed
            return False
        except Exception as e:
            logger.error(f"Error sending to connection: {str(e)}")
            return False


# Global connection manager instance
manager = ConnectionManager()
