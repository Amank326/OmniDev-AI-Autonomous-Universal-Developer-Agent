"""
Real-time Alerts Service - WebSocket-based alert delivery and management
Phase 27: Advanced Notifications & Real-time Alerts System
"""

import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Set, Callable
import json


class AlertDeliveryStatus(Enum):
    """Alert delivery status"""
    QUEUED = "queued"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


class PushStrategy(Enum):
    """Alert push strategies"""
    IMMEDIATE = "immediate"
    BATCH = "batch"
    THROTTLED = "throttled"


@dataclass
class AlertQueueItem:
    """Item in alert delivery queue"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alert_id: str = ""
    user_id: str = ""
    destination: str = ""  # WebSocket connection, device, etc.
    payload: Dict[str, Any] = field(default_factory=dict)
    status: AlertDeliveryStatus = AlertDeliveryStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    delivery_attempts: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class AlertSubscription:
    """User subscription to alert rules"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    rule_id: str = ""
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AlertBatch:
    """Batched alerts for delivery"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    alert_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    status: AlertDeliveryStatus = AlertDeliveryStatus.QUEUED


@dataclass
class WebSocketConnection:
    """Active WebSocket connection"""
    connection_id: str = ""
    user_id: str = ""
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    subscribed_rules: Set[str] = field(default_factory=set)
    is_active: bool = True


class RealTimeAlertsService:
    """Service for real-time alert delivery via WebSocket"""

    def __init__(self):
        self.alert_queue: Dict[str, AlertQueueItem] = {}
        self.subscriptions: Dict[str, AlertSubscription] = {}
        self.websocket_connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.alert_batches: Dict[str, AlertBatch] = {}
        self.delivery_callbacks: Dict[str, Callable] = {}
        self.alert_history: Dict[str, List[Dict[str, Any]]] = {}
        self.undelivered_alerts: Dict[str, List[AlertQueueItem]] = {}

    def create_subscription(self, user_id: str, rule_id: str) -> AlertSubscription:
        """Create alert subscription for user"""
        subscription = AlertSubscription(user_id=user_id, rule_id=rule_id)
        self.subscriptions[subscription.id] = subscription

        # Subscribe to rule for all user connections
        if user_id in self.user_connections:
            for conn_id in self.user_connections[user_id]:
                if conn_id in self.websocket_connections:
                    self.websocket_connections[conn_id].subscribed_rules.add(rule_id)

        return subscription

    def remove_subscription(self, subscription_id: str) -> bool:
        """Remove alert subscription"""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            return True
        return False

    def register_websocket_connection(
        self,
        connection_id: str,
        user_id: str
    ) -> WebSocketConnection:
        """Register new WebSocket connection"""
        connection = WebSocketConnection(
            connection_id=connection_id,
            user_id=user_id
        )

        self.websocket_connections[connection_id] = connection

        # Add to user's connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)

        # Subscribe to user's alert rules
        user_subscriptions = [
            s for s in self.subscriptions.values()
            if s.user_id == user_id and s.enabled
        ]
        for sub in user_subscriptions:
            connection.subscribed_rules.add(sub.rule_id)

        # Deliver any pending alerts
        if user_id in self.undelivered_alerts:
            pending = self.undelivered_alerts[user_id]
            for alert_item in pending:
                self.queue_alert_delivery(alert_item.alert_id, user_id, alert_item.payload)

        return connection

    def unregister_websocket_connection(self, connection_id: str) -> bool:
        """Unregister WebSocket connection"""
        if connection_id not in self.websocket_connections:
            return False

        connection = self.websocket_connections[connection_id]
        user_id = connection.user_id

        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)

        del self.websocket_connections[connection_id]
        return True

    def queue_alert_delivery(
        self,
        alert_id: str,
        user_id: str,
        payload: Dict[str, Any],
        push_strategy: PushStrategy = PushStrategy.IMMEDIATE
    ) -> AlertQueueItem:
        """Queue alert for delivery"""
        queue_item = AlertQueueItem(
            alert_id=alert_id,
            user_id=user_id,
            destination=user_id,
            payload=payload
        )

        self.alert_queue[queue_item.id] = queue_item

        # If immediate strategy, deliver now
        if push_strategy == PushStrategy.IMMEDIATE:
            self.deliver_alert(queue_item.id)
        # If batch strategy, add to batch
        elif push_strategy == PushStrategy.BATCH:
            self._add_to_batch(user_id, alert_id)

        return queue_item

    def deliver_alert(self, queue_item_id: str) -> bool:
        """Deliver queued alert to user"""
        queue_item = self.alert_queue.get(queue_item_id)
        if not queue_item:
            return False

        user_id = queue_item.user_id

        # Check if user has active connections
        if user_id not in self.user_connections or not self.user_connections[user_id]:
            # Store as undelivered for later delivery
            if user_id not in self.undelivered_alerts:
                self.undelivered_alerts[user_id] = []
            if queue_item not in self.undelivered_alerts[user_id]:
                self.undelivered_alerts[user_id].append(queue_item)
            return False

        # Send to all active connections
        delivered = False
        for conn_id in self.user_connections[user_id]:
            connection = self.websocket_connections.get(conn_id)
            if connection and connection.is_active:
                try:
                    # Emit via WebSocket
                    self._emit_alert(connection, queue_item.payload)
                    delivered = True
                    queue_item.sent_at = datetime.utcnow()
                    queue_item.status = AlertDeliveryStatus.DELIVERED
                except Exception as e:
                    queue_item.error_message = str(e)
                    queue_item.delivery_attempts += 1

        if delivered:
            # Remove from undelivered if it was there
            if user_id in self.undelivered_alerts:
                self.undelivered_alerts[user_id] = [
                    a for a in self.undelivered_alerts[user_id]
                    if a.id != queue_item_id
                ]
            # Record in history
            if user_id not in self.alert_history:
                self.alert_history[user_id] = []
            self.alert_history[user_id].append({
                "alert_id": queue_item.alert_id,
                "delivered_at": queue_item.sent_at.isoformat(),
                "payload": queue_item.payload
            })
            return True
        else:
            # Schedule retry
            if queue_item.delivery_attempts < queue_item.max_retries:
                # Exponential backoff: 30s, 2m, 5m
                retry_delays = [30, 120, 300]
                delay_seconds = retry_delays[min(queue_item.delivery_attempts, 2)]
                queue_item.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
                return False
            else:
                # Max retries exceeded
                queue_item.status = AlertDeliveryStatus.FAILED
                return False

    def _emit_alert(self, connection: WebSocketConnection, payload: Dict[str, Any]) -> None:
        """Emit alert via WebSocket (callback-based)"""
        if "alert_push" in self.delivery_callbacks:
            self.delivery_callbacks["alert_push"](connection.connection_id, payload)

    def _add_to_batch(self, user_id: str, alert_id: str) -> None:
        """Add alert to batch for later delivery"""
        # Find existing batch for user
        batch = next(
            (b for b in self.alert_batches.values()
             if b.user_id == user_id and b.status == AlertDeliveryStatus.QUEUED),
            None
        )

        if batch:
            batch.alert_ids.append(alert_id)
        else:
            batch = AlertBatch(user_id=user_id, alert_ids=[alert_id])
            self.alert_batches[batch.id] = batch

    def deliver_batches(self, max_age_seconds: int = 300) -> Dict[str, int]:
        """Deliver batched alerts that are ready"""
        results = {"delivered": 0, "failed": 0}
        cutoff_time = datetime.utcnow() - timedelta(seconds=max_age_seconds)

        batches_to_deliver = [
            b for b in self.alert_batches.values()
            if b.status == AlertDeliveryStatus.QUEUED and b.created_at <= cutoff_time
        ]

        for batch in batches_to_deliver:
            payload = {"type": "alert_batch", "alerts": batch.alert_ids}
            queue_item = AlertQueueItem(
                user_id=batch.user_id,
                destination=batch.user_id,
                payload=payload
            )
            if self.deliver_alert(queue_item.id):
                batch.status = AlertDeliveryStatus.DELIVERED
                batch.delivered_at = datetime.utcnow()
                results["delivered"] += 1
            else:
                results["failed"] += 1

        return results

    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Mark alert as acknowledged"""
        # Find queue item
        queue_item = next(
            (q for q in self.alert_queue.values()
             if q.alert_id == alert_id and q.user_id == user_id),
            None
        )

        if queue_item:
            queue_item.status = AlertDeliveryStatus.ACKNOWLEDGED
            return True
        return False

    def heartbeat_connection(self, connection_id: str) -> bool:
        """Update connection heartbeat"""
        if connection_id in self.websocket_connections:
            self.websocket_connections[connection_id].last_heartbeat = datetime.utcnow()
            return True
        return False

    def cleanup_stale_connections(self, timeout_seconds: int = 300) -> int:
        """Remove stale connections"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=timeout_seconds)
        stale_connections = [
            conn_id for conn_id, conn in self.websocket_connections.items()
            if conn.last_heartbeat < cutoff_time
        ]

        for conn_id in stale_connections:
            self.unregister_websocket_connection(conn_id)

        return len(stale_connections)

    def get_connection_status(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get WebSocket connection status"""
        conn = self.websocket_connections.get(connection_id)
        if not conn:
            return None

        return {
            "connection_id": conn.connection_id,
            "user_id": conn.user_id,
            "connected_at": conn.connected_at.isoformat(),
            "last_heartbeat": conn.last_heartbeat.isoformat(),
            "is_active": conn.is_active,
            "subscribed_rules": list(conn.subscribed_rules),
            "pending_alerts": len([
                q for q in self.alert_queue.values()
                if q.user_id == conn.user_id and q.status == AlertDeliveryStatus.QUEUED
            ])
        }

    def get_user_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all connections for user"""
        conn_ids = self.user_connections.get(user_id, set())
        return [
            self.get_connection_status(conn_id)
            for conn_id in conn_ids
            if self.get_connection_status(conn_id)
        ]

    def get_delivery_statistics(self) -> Dict[str, int]:
        """Get delivery statistics"""
        stats = {
            "queued": len([q for q in self.alert_queue.values() if q.status == AlertDeliveryStatus.QUEUED]),
            "delivered": len([q for q in self.alert_queue.values() if q.status == AlertDeliveryStatus.DELIVERED]),
            "failed": len([q for q in self.alert_queue.values() if q.status == AlertDeliveryStatus.FAILED]),
            "acknowledged": len([q for q in self.alert_queue.values() if q.status == AlertDeliveryStatus.ACKNOWLEDGED]),
            "active_connections": len(self.websocket_connections),
            "total_subscriptions": len(self.subscriptions),
            "pending_undelivered": sum(len(v) for v in self.undelivered_alerts.values()),
        }
        return stats

    def register_delivery_callback(self, event_name: str, callback: Callable) -> None:
        """Register callback for delivery events"""
        self.delivery_callbacks[event_name] = callback

    def retry_failed_alerts(self) -> int:
        """Retry failed and pending alert deliveries"""
        retried = 0
        failed_items = [
            q for q in self.alert_queue.values()
            if q.status in [AlertDeliveryStatus.QUEUED, AlertDeliveryStatus.FAILED]
            and (q.next_retry_at is None or q.next_retry_at <= datetime.utcnow())
        ]

        for queue_item in failed_items:
            if self.deliver_alert(queue_item.id):
                retried += 1

        return retried
