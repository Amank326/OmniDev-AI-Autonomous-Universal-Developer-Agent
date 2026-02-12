"""
Optimization WebSocket Handler
Real-time optimization event broadcasting and monitoring.
"""

from dataclasses import dataclass
from typing import Dict, Set, Optional, List, Callable, Any
from enum import Enum
from threading import RLock
from collections import defaultdict
from datetime import datetime
import json


class OptimizationEventType(Enum):
    """Optimization event types"""
    JOB_STARTED = "job_started"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    PASS_COMPLETED = "pass_completed"
    OPTIMIZATION_STARTED = "optimization_started"
    OPTIMIZATION_COMPLETED = "optimization_completed"
    CACHE_HIT = "cache_hit"
    ACCELERATION_READY = "acceleration_ready"
    ANOMALY_DETECTED = "anomaly_detected"
    RECOMMENDATION_GENERATED = "recommendation_generated"


@dataclass
class WebSocketConnection:
    """WebSocket client connection"""
    client_id: str
    workspace_id: str
    connected_at: datetime
    subscriptions: Set[str]  # Event types subscribed to
    room_subscriptions: Set[str]  # Rooms subscribed to (e.g., model_id specific)
    last_heartbeat: datetime


class OptimizationWebSocketHandler:
    """
    WebSocket handler for optimization events.
    Manages real-time event broadcasting for model optimization, quantization,
    and acceleration operations.
    """

    def __init__(self):
        """Initialize WebSocket handler"""
        self.clients: Dict[str, WebSocketConnection] = {}
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # event_type -> {client_ids}
        self.room_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # room -> {client_ids}
        self.lock = RLock()

    # Connection Management
    def handle_connect(self, client_id: str, workspace_id: str) -> str:
        """Handle client connection"""
        with self.lock:
            connection = WebSocketConnection(
                client_id=client_id,
                workspace_id=workspace_id,
                connected_at=datetime.utcnow(),
                subscriptions=set(),
                room_subscriptions=set(),
                last_heartbeat=datetime.utcnow()
            )

            self.clients[client_id] = connection

            # Auto-subscribe workspace room
            workspace_room = f"workspace_{workspace_id}"
            self.room_subscriptions[workspace_room].add(client_id)
            connection.room_subscriptions.add(workspace_room)

            return client_id

    def handle_disconnect(self, client_id: str) -> bool:
        """Handle client disconnection"""
        with self.lock:
            if client_id not in self.clients:
                return False

            connection = self.clients[client_id]

            # Remove from subscriptions
            for event_type in list(connection.subscriptions):
                self.subscriptions[event_type].discard(client_id)

            # Remove from room subscriptions
            for room in list(connection.room_subscriptions):
                self.room_subscriptions[room].discard(client_id)

            del self.clients[client_id]
            return True

    def handle_subscribe(self, client_id: str, event_type: str) -> bool:
        """Subscribe client to event type"""
        with self.lock:
            if client_id not in self.clients:
                return False

            connection = self.clients[client_id]
            connection.subscriptions.add(event_type)
            self.subscriptions[event_type].add(client_id)
            return True

    def handle_unsubscribe(self, client_id: str, event_type: str) -> bool:
        """Unsubscribe client from event type"""
        with self.lock:
            if client_id not in self.clients:
                return False

            connection = self.clients[client_id]
            connection.subscriptions.discard(event_type)
            self.subscriptions[event_type].discard(client_id)
            return True

    def handle_subscribe_room(self, client_id: str, room: str) -> bool:
        """Subscribe client to room"""
        with self.lock:
            if client_id not in self.clients:
                return False

            connection = self.clients[client_id]
            connection.room_subscriptions.add(room)
            self.room_subscriptions[room].add(client_id)
            return True

    def handle_unsubscribe_room(self, client_id: str, room: str) -> bool:
        """Unsubscribe client from room"""
        with self.lock:
            if client_id not in self.clients:
                return False

            connection = self.clients[client_id]
            connection.room_subscriptions.discard(room)
            self.room_subscriptions[room].discard(client_id)
            return True

    def handle_heartbeat(self, client_id: str) -> Dict[str, Any]:
        """Handle client heartbeat"""
        with self.lock:
            if client_id not in self.clients:
                return {'status': 'disconnected'}

            connection = self.clients[client_id]
            connection.last_heartbeat = datetime.utcnow()

            return {
                'status': 'connected',
                'server_time': datetime.utcnow().isoformat(),
                'connected_clients': len(self.clients)
            }

    # Event Broadcasting
    def broadcast_job_started(
        self,
        job_id: str,
        model_id: str,
        model_version: int,
        optimization_type: str,
        workspace_id: str
    ) -> None:
        """Broadcast job started event"""
        event = {
            'type': OptimizationEventType.JOB_STARTED.value,
            'job_id': job_id,
            'model_id': model_id,
            'model_version': model_version,
            'optimization_type': optimization_type,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        self._broadcast_to_subscribers('job_started', event, workspace_id)
        self._broadcast_to_room(f"model_{model_id}", event)

    def broadcast_job_progress(
        self,
        job_id: str,
        model_id: str,
        progress_percent: int,
        status: str,
        workspace_id: str
    ) -> None:
        """Broadcast job progress event"""
        event = {
            'type': OptimizationEventType.JOB_PROGRESS.value,
            'job_id': job_id,
            'model_id': model_id,
            'progress_percent': progress_percent,
            'status': status,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        self._broadcast_to_subscribers('job_progress', event, workspace_id)
        self._broadcast_to_room(f"job_{job_id}", event)

    def broadcast_job_completed(
        self,
        job_id: str,
        model_id: str,
        optimization_type: str,
        metrics: Dict[str, Any],
        workspace_id: str
    ) -> None:
        """Broadcast job completed event"""
        event = {
            'type': OptimizationEventType.JOB_COMPLETED.value,
            'job_id': job_id,
            'model_id': model_id,
            'optimization_type': optimization_type,
            'metrics': metrics,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        self._broadcast_to_subscribers('job_completed', event, workspace_id)
        self._broadcast_to_room(f"model_{model_id}", event)

    def broadcast_job_failed(
        self,
        job_id: str,
        model_id: str,
        error_message: str,
        workspace_id: str
    ) -> None:
        """Broadcast job failed event"""
        event = {
            'type': OptimizationEventType.JOB_FAILED.value,
            'job_id': job_id,
            'model_id': model_id,
            'error_message': error_message,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        self._broadcast_to_subscribers('job_failed', event, workspace_id)
        self._broadcast_to_room(f"model_{model_id}", event)

    def broadcast_pass_completed(
        self,
        optimization_id: str,
        pass_id: str,
        model_id: str,
        optimization_type: str,
        workspace_id: str
    ) -> None:
        """Broadcast optimization pass completion"""
        event = {
            'type': OptimizationEventType.PASS_COMPLETED.value,
            'optimization_id': optimization_id,
            'pass_id': pass_id,
            'model_id': model_id,
            'optimization_type': optimization_type,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        self._broadcast_to_subscribers('pass_completed', event, workspace_id)
        self._broadcast_to_room(f"optimization_{optimization_id}", event)

    def broadcast_cache_hit(
        self,
        request_id: str,
        model_id: str,
        cache_key: str,
        workspace_id: str
    ) -> None:
        """Broadcast cache hit event from acceleration"""
        event = {
            'type': OptimizationEventType.CACHE_HIT.value,
            'request_id': request_id,
            'model_id': model_id,
            'cache_key': cache_key,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        self._broadcast_to_subscribers('cache_hit', event, workspace_id)

    def broadcast_acceleration_ready(
        self,
        batch_id: str,
        batch_size: int,
        latency_ms: float,
        workspace_id: str
    ) -> None:
        """Broadcast acceleration batch ready event"""
        event = {
            'type': OptimizationEventType.ACCELERATION_READY.value,
            'batch_id': batch_id,
            'batch_size': batch_size,
            'latency_ms': latency_ms,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        self._broadcast_to_subscribers('acceleration_ready', event, workspace_id)

    def broadcast_anomaly_detected(
        self,
        anomaly_id: str,
        model_id: str,
        metric_name: str,
        anomaly_value: float,
        baseline_value: float,
        confidence: float,
        workspace_id: str
    ) -> None:
        """Broadcast anomaly detection event from optimization"""
        event = {
            'type': OptimizationEventType.ANOMALY_DETECTED.value,
            'anomaly_id': anomaly_id,
            'model_id': model_id,
            'metric_name': metric_name,
            'anomaly_value': anomaly_value,
            'baseline_value': baseline_value,
            'confidence': confidence,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        self._broadcast_to_subscribers('anomaly_detected', event, workspace_id)
        self._broadcast_to_room(f"model_{model_id}", event)

    def broadcast_recommendation_generated(
        self,
        recommendation_id: str,
        model_id: str,
        optimization_type: str,
        priority: str,
        expected_improvement_percent: float,
        workspace_id: str
    ) -> None:
        """Broadcast optimization recommendation"""
        event = {
            'type': OptimizationEventType.RECOMMENDATION_GENERATED.value,
            'recommendation_id': recommendation_id,
            'model_id': model_id,
            'optimization_type': optimization_type,
            'priority': priority,
            'expected_improvement_percent': expected_improvement_percent,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        self._broadcast_to_subscribers('recommendation_generated', event, workspace_id)
        self._broadcast_to_room(f"model_{model_id}", event)

    # Utility Methods
    def _broadcast_to_subscribers(
        self,
        event_type: str,
        event: Dict[str, Any],
        workspace_id: str
    ) -> None:
        """Broadcast to all subscribers of event type in workspace"""
        with self.lock:
            client_ids = self.subscriptions.get(event_type, set())

            for client_id in list(client_ids):
                if client_id in self.clients:
                    client = self.clients[client_id]
                    if client.workspace_id == workspace_id:
                        self._send_to_client(client_id, event)

    def _broadcast_to_room(self, room: str, event: Dict[str, Any]) -> None:
        """Broadcast to all clients in room"""
        with self.lock:
            client_ids = self.room_subscriptions.get(room, set())

            for client_id in list(client_ids):
                if client_id in self.clients:
                    self._send_to_client(client_id, event)

    def _broadcast_to_client(self, client_id: str, event: Dict[str, Any]) -> bool:
        """Broadcast to specific client"""
        with self.lock:
            if client_id not in self.clients:
                return False

            self._send_to_client(client_id, event)
            return True

    def _send_to_client(self, client_id: str, event: Dict[str, Any]) -> None:
        """Send event to client (override in actual implementation)"""
        # This would use Socket.IO or WebSocket emit in real implementation
        pass

    # Statistics
    def get_connected_clients(self) -> int:
        """Get number of connected clients"""
        with self.lock:
            return len(self.clients)

    def get_workspace_clients(self, workspace_id: str) -> int:
        """Get number of connected clients for workspace"""
        with self.lock:
            return sum(
                1 for c in self.clients.values()
                if c.workspace_id == workspace_id
            )

    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get subscription statistics"""
        with self.lock:
            return {
                'total_clients': len(self.clients),
                'subscriptions_by_type': {
                    event_type: len(client_ids)
                    for event_type, client_ids in self.subscriptions.items()
                },
                'rooms': {
                    room: len(client_ids)
                    for room, client_ids in self.room_subscriptions.items()
                }
            }

    def health_check(self) -> Dict[str, Any]:
        """Health check for WebSocket handler"""
        with self.lock:
            now = datetime.utcnow()
            stale_clients = sum(
                1 for c in self.clients.values()
                if (now - c.last_heartbeat).total_seconds() > 60
            )

            return {
                'status': 'healthy',
                'connected_clients': len(self.clients),
                'stale_clients': stale_clients,
                'active_subscriptions': len(self.subscriptions),
                'active_rooms': len(self.room_subscriptions),
                'timestamp': now.isoformat()
            }

    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client connection info"""
        with self.lock:
            if client_id not in self.clients:
                return None

            client = self.clients[client_id]
            return {
                'client_id': client_id,
                'workspace_id': client.workspace_id,
                'connected_at': client.connected_at.isoformat(),
                'last_heartbeat': client.last_heartbeat.isoformat(),
                'subscriptions': list(client.subscriptions),
                'rooms': list(client.room_subscriptions)
            }

    def cleanup_stale_clients(self, heartbeat_timeout_seconds: int = 120) -> int:
        """Remove clients that haven't sent heartbeat"""
        with self.lock:
            now = datetime.utcnow()
            stale_client_ids = [
                client_id for client_id, client in self.clients.items()
                if (now - client.last_heartbeat).total_seconds() > heartbeat_timeout_seconds
            ]

            for client_id in stale_client_ids:
                self.handle_disconnect(client_id)

            return len(stale_client_ids)
