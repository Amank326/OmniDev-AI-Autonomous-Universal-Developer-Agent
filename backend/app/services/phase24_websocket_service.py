"""
Phase 24: WebSocket Service
Real-time bi-directional communication with room/channel subscriptions
"""

from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
import uuid


class MessageType(Enum):
    """WebSocket message types"""
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    BROADCAST = "broadcast"
    DIRECT = "direct"
    HEARTBEAT = "heartbeat"
    ACKNOWLEDGE = "acknowledge"
    ERROR = "error"
    PRESENCE = "presence"
    METRIC_UPDATE = "metric_update"
    ALERT = "alert"


class ConnectionStatus(Enum):
    """Connection status states"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SUBSCRIBED = "subscribed"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: MessageType
    room: str
    data: Dict
    sender_id: str
    timestamp: datetime
    message_id: str = None
    requires_ack: bool = False

    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())

    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "room": self.room,
            "data": self.data,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "requires_ack": self.requires_ack,
        }


@dataclass
class WebSocketConnection:
    """Represents a WebSocket connection"""
    connection_id: str
    user_id: str
    client_ip: str
    connected_at: datetime
    last_heartbeat: datetime
    subscribed_rooms: Set[str]
    status: ConnectionStatus
    latency_ms: float = 0.0
    message_queue: List[WebSocketMessage] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.message_queue is None:
            self.message_queue = []
        if self.metadata is None:
            self.metadata = {}


class WebSocketService:
    """
    WebSocket connection management service
    Handles real-time bi-directional communication with rooms/channels
    """

    def __init__(self, db_session=None):
        self.db_session = db_session
        self.connections: Dict[str, WebSocketConnection] = {}
        self.rooms: Dict[str, Set[str]] = {}  # room_name -> connection_ids
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.presence_tracking: Dict[str, Dict] = {}  # user_id -> presence info
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 60  # seconds

    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================

    def connect(self, user_id: str, client_ip: str, metadata: Dict = None) -> WebSocketConnection:
        """
        Establish new WebSocket connection
        
        Args:
            user_id: User ID
            client_ip: Client IP address
            metadata: Connection metadata (user agent, etc)
        
        Returns:
            WebSocketConnection object
        """
        connection_id = str(uuid.uuid4())
        now = datetime.utcnow()

        connection = WebSocketConnection(
            connection_id=connection_id,
            user_id=user_id,
            client_ip=client_ip,
            connected_at=now,
            last_heartbeat=now,
            subscribed_rooms=set(),
            status=ConnectionStatus.CONNECTED,
            metadata=metadata or {},
        )

        self.connections[connection_id] = connection
        self._track_presence(user_id, "connected", connection_id)

        return connection

    def disconnect(self, connection_id: str, reason: str = "user_disconnect") -> bool:
        """
        Close WebSocket connection
        
        Args:
            connection_id: Connection ID
            reason: Disconnection reason
        
        Returns:
            Success status
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]

        # Unsubscribe from all rooms
        for room in list(connection.subscribed_rooms):
            self.unsubscribe(connection_id, room)

        # Remove presence tracking
        self._untrack_presence(connection.user_id, connection_id)

        # Remove connection
        del self.connections[connection_id]

        return True

    def get_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """Get connection by ID"""
        return self.connections.get(connection_id)

    def get_user_connections(self, user_id: str) -> List[WebSocketConnection]:
        """Get all connections for a user"""
        return [c for c in self.connections.values() if c.user_id == user_id]

    def get_active_connections(self) -> List[WebSocketConnection]:
        """Get all active connections"""
        return list(self.connections.values())

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.connections)

    # ========================================================================
    # ROOM/CHANNEL MANAGEMENT
    # ========================================================================

    def subscribe(self, connection_id: str, room: str) -> bool:
        """
        Subscribe connection to room/channel
        
        Args:
            connection_id: Connection ID
            room: Room name
        
        Returns:
            Success status
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        connection.subscribed_rooms.add(room)

        if room not in self.rooms:
            self.rooms[room] = set()

        self.rooms[room].add(connection_id)
        connection.status = ConnectionStatus.SUBSCRIBED

        return True

    def unsubscribe(self, connection_id: str, room: str) -> bool:
        """
        Unsubscribe connection from room
        
        Args:
            connection_id: Connection ID
            room: Room name
        
        Returns:
            Success status
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        connection.subscribed_rooms.discard(room)

        if room in self.rooms:
            self.rooms[room].discard(connection_id)
            if not self.rooms[room]:
                del self.rooms[room]

        return True

    def get_room_subscribers(self, room: str) -> List[str]:
        """Get all connections subscribed to room"""
        return list(self.rooms.get(room, set()))

    def get_room_count(self, room: str) -> int:
        """Get number of subscribers in room"""
        return len(self.rooms.get(room, set()))

    def get_all_rooms(self) -> Dict[str, int]:
        """Get all rooms and subscriber counts"""
        return {room: len(ids) for room, ids in self.rooms.items()}

    # ========================================================================
    # MESSAGE BROADCASTING
    # ========================================================================

    def broadcast_to_room(self, room: str, message: WebSocketMessage) -> int:
        """
        Broadcast message to all connections in room
        
        Args:
            room: Room name
            message: WebSocketMessage
        
        Returns:
            Number of connections message was sent to
        """
        if room not in self.rooms:
            return 0

        connection_ids = list(self.rooms[room])
        sent_count = 0

        for connection_id in connection_ids:
            if self._send_message(connection_id, message):
                sent_count += 1

        return sent_count

    def broadcast_to_all(self, message: WebSocketMessage) -> int:
        """
        Broadcast message to all connections
        
        Args:
            message: WebSocketMessage
        
        Returns:
            Number of connections message was sent to
        """
        sent_count = 0

        for connection_id in list(self.connections.keys()):
            if self._send_message(connection_id, message):
                sent_count += 1

        return sent_count

    def send_direct(self, connection_id: str, message: WebSocketMessage) -> bool:
        """
        Send direct message to specific connection
        
        Args:
            connection_id: Target connection ID
            message: WebSocketMessage
        
        Returns:
            Success status
        """
        return self._send_message(connection_id, message)

    def send_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """
        Send message to all connections of a user
        
        Args:
            user_id: User ID
            message: WebSocketMessage
        
        Returns:
            Number of connections message was sent to
        """
        user_connections = self.get_user_connections(user_id)
        sent_count = 0

        for connection in user_connections:
            if self._send_message(connection.connection_id, message):
                sent_count += 1

        return sent_count

    def _send_message(self, connection_id: str, message: WebSocketMessage) -> bool:
        """Internal method to send message to connection"""
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        connection.message_queue.append(message)

        return True

    def get_pending_messages(self, connection_id: str) -> List[Dict]:
        """Get all pending messages for connection"""
        if connection_id not in self.connections:
            return []

        connection = self.connections[connection_id]
        messages = [msg.to_dict() for msg in connection.message_queue]
        connection.message_queue = []

        return messages

    # ========================================================================
    # HEARTBEAT & HEALTH
    # ========================================================================

    def send_heartbeat(self, connection_id: str) -> bool:
        """
        Send heartbeat to connection (keep-alive)
        
        Args:
            connection_id: Connection ID
        
        Returns:
            Success status
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        connection.last_heartbeat = datetime.utcnow()

        heartbeat = WebSocketMessage(
            type=MessageType.HEARTBEAT,
            room="system",
            data={"timestamp": datetime.utcnow().isoformat()},
            sender_id="system",
            timestamp=datetime.utcnow(),
        )

        return self._send_message(connection_id, heartbeat)

    def send_heartbeats_to_all(self) -> int:
        """Send heartbeat to all active connections"""
        sent_count = 0

        for connection_id in list(self.connections.keys()):
            if self.send_heartbeat(connection_id):
                sent_count += 1

        return sent_count

    def check_connection_health(self, connection_id: str) -> bool:
        """
        Check if connection is still healthy
        
        Args:
            connection_id: Connection ID
        
        Returns:
            True if connection is healthy
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        last_heartbeat_age = (datetime.utcnow() - connection.last_heartbeat).total_seconds()

        return last_heartbeat_age < self.connection_timeout

    def cleanup_stale_connections(self) -> int:
        """
        Remove connections that haven't sent heartbeat
        
        Returns:
            Number of connections removed
        """
        stale_connections = []

        for connection_id, connection in self.connections.items():
            if not self.check_connection_health(connection_id):
                stale_connections.append(connection_id)

        for connection_id in stale_connections:
            self.disconnect(connection_id, "timeout")

        return len(stale_connections)

    def update_latency(self, connection_id: str, latency_ms: float) -> bool:
        """
        Update connection latency metric
        
        Args:
            connection_id: Connection ID
            latency_ms: Latency in milliseconds
        
        Returns:
            Success status
        """
        if connection_id not in self.connections:
            return False

        connection = self.connections[connection_id]
        connection.latency_ms = latency_ms

        return True

    # ========================================================================
    # PRESENCE TRACKING
    # ========================================================================

    def _track_presence(self, user_id: str, status: str, connection_id: str):
        """Track user presence"""
        if user_id not in self.presence_tracking:
            self.presence_tracking[user_id] = {}

        self.presence_tracking[user_id] = {
            "status": status,
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }

        # Broadcast presence change
        presence_msg = WebSocketMessage(
            type=MessageType.PRESENCE,
            room="presence",
            data={
                "user_id": user_id,
                "status": status,
                "presence": self.presence_tracking[user_id],
            },
            sender_id="system",
            timestamp=datetime.utcnow(),
        )
        self.broadcast_to_room("presence", presence_msg)

    def _untrack_presence(self, user_id: str, connection_id: str):
        """Untrack user presence"""
        if user_id in self.presence_tracking:
            del self.presence_tracking[user_id]

            # Broadcast presence change
            presence_msg = WebSocketMessage(
                type=MessageType.PRESENCE,
                room="presence",
                data={
                    "user_id": user_id,
                    "status": "disconnected",
                },
                sender_id="system",
                timestamp=datetime.utcnow(),
            )
            self.broadcast_to_room("presence", presence_msg)

    def get_user_presence(self, user_id: str) -> Optional[Dict]:
        """Get user presence info"""
        return self.presence_tracking.get(user_id)

    def get_all_presence(self) -> Dict:
        """Get all user presence info"""
        return self.presence_tracking.copy()

    def set_user_activity(self, user_id: str):
        """Update user last activity timestamp"""
        if user_id in self.presence_tracking:
            self.presence_tracking[user_id]["last_activity"] = datetime.utcnow().isoformat()

    # ========================================================================
    # MESSAGE HANDLERS
    # ========================================================================

    def register_handler(self, message_type: MessageType, handler: Callable):
        """
        Register handler for message type
        
        Args:
            message_type: MessageType to handle
            handler: Callable handler function
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []

        self.message_handlers[message_type].append(handler)

    def handle_message(self, connection_id: str, message_data: Dict) -> bool:
        """
        Handle incoming message
        
        Args:
            connection_id: Connection ID
            message_data: Message data dict
        
        Returns:
            Success status
        """
        try:
            message_type = MessageType(message_data.get("type", "broadcast"))

            if message_type in self.message_handlers:
                for handler in self.message_handlers[message_type]:
                    handler(connection_id, message_data)

            return True
        except Exception as e:
            return False

    # ========================================================================
    # ACKNOWLEDGEMENT & RELIABILITY
    # ========================================================================

    def request_acknowledgement(self, connection_id: str, message: WebSocketMessage) -> bool:
        """
        Send message requesting acknowledgement
        
        Args:
            connection_id: Connection ID
            message: WebSocketMessage
        
        Returns:
            Success status
        """
        message.requires_ack = True
        return self._send_message(connection_id, message)

    def acknowledge_message(self, connection_id: str, message_id: str) -> bool:
        """
        Send acknowledgement for received message
        
        Args:
            connection_id: Connection ID
            message_id: Message ID to acknowledge
        
        Returns:
            Success status
        """
        ack_message = WebSocketMessage(
            type=MessageType.ACKNOWLEDGE,
            room="system",
            data={"acknowledged_message_id": message_id},
            sender_id="system",
            timestamp=datetime.utcnow(),
        )

        return self._send_message(connection_id, ack_message)

    # ========================================================================
    # CONNECTION STATISTICS & METRICS
    # ========================================================================

    def get_connection_stats(self, connection_id: str) -> Optional[Dict]:
        """
        Get connection statistics
        
        Args:
            connection_id: Connection ID
        
        Returns:
            Statistics dict or None
        """
        if connection_id not in self.connections:
            return None

        connection = self.connections[connection_id]
        connection_age = (datetime.utcnow() - connection.connected_at).total_seconds()

        return {
            "connection_id": connection_id,
            "user_id": connection.user_id,
            "client_ip": connection.client_ip,
            "status": connection.status.value,
            "connection_age_seconds": connection_age,
            "latency_ms": connection.latency_ms,
            "subscribed_rooms": list(connection.subscribed_rooms),
            "room_count": len(connection.subscribed_rooms),
            "pending_messages": len(connection.message_queue),
            "last_heartbeat": connection.last_heartbeat.isoformat(),
        }

    def get_system_stats(self) -> Dict:
        """Get overall WebSocket system statistics"""
        total_connections = len(self.connections)
        total_rooms = len(self.rooms)
        total_subscribers = sum(len(ids) for ids in self.rooms.values())
        avg_latency = (
            sum(c.latency_ms for c in self.connections.values()) / total_connections
            if total_connections > 0
            else 0
        )

        return {
            "active_connections": total_connections,
            "active_rooms": total_rooms,
            "total_subscribers": total_subscribers,
            "avg_latency_ms": avg_latency,
            "presence_tracking_count": len(self.presence_tracking),
            "total_pending_messages": sum(len(c.message_queue) for c in self.connections.values()),
        }

    # ========================================================================
    # ERROR HANDLING
    # ========================================================================

    def send_error(self, connection_id: str, error_code: str, error_message: str) -> bool:
        """
        Send error message to connection
        
        Args:
            connection_id: Connection ID
            error_code: Error code
            error_message: Error message
        
        Returns:
            Success status
        """
        error_msg = WebSocketMessage(
            type=MessageType.ERROR,
            room="system",
            data={
                "error_code": error_code,
                "error_message": error_message,
            },
            sender_id="system",
            timestamp=datetime.utcnow(),
        )

        if connection_id in self.connections:
            self.connections[connection_id].status = ConnectionStatus.ERROR

        return self._send_message(connection_id, error_msg)

    # ========================================================================
    # CLEANUP & MANAGEMENT
    # ========================================================================

    def clear_empty_rooms(self) -> int:
        """
        Remove empty rooms
        
        Returns:
            Number of rooms cleared
        """
        empty_rooms = [room for room, ids in self.rooms.items() if not ids]

        for room in empty_rooms:
            del self.rooms[room]

        return len(empty_rooms)

    def reset_service(self):
        """Reset WebSocket service (testing only)"""
        self.connections = {}
        self.rooms = {}
        self.message_handlers = {}
        self.presence_tracking = {}
