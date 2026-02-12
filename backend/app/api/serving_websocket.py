"""
Model Serving WebSocket Handler
Real-time event broadcasting for model serving events.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Set, Any, Callable, Optional
from threading import RLock
from collections import defaultdict

logger = logging.getLogger(__name__)


# ===================== DATACLASSES =====================

@dataclass
class WebSocketConnection:
    """WebSocket client connection"""
    client_id: str
    workspace_id: str
    connected_at: float
    subscriptions: Set[str] = None  # event types
    room_subscriptions: Set[str] = None  # rooms
    
    def __post_init__(self):
        if self.subscriptions is None:
            self.subscriptions = set()
        if self.room_subscriptions is None:
            self.room_subscriptions = set()


# ===================== SERVING WEBSOCKET HANDLER =====================

class ServingWebSocketHandler:
    """
    Manages WebSocket connections and broadcasts real-time serving events.
    Supports event-based and room-based subscriptions with workspace isolation.
    """
    
    def __init__(self):
        # Connection management
        self.connected_clients: Dict[str, WebSocketConnection] = {}
        
        # Subscription management
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # event_type -> client_ids
        self.room_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # room -> client_ids
        
        # Thread safety
        self.lock = RLock()
        
        # Callbacks
        self.callbacks: Dict[str, List[Callable]] = {}
    
    # ===================== CONNECTION MANAGEMENT =====================
    
    def handle_connect(self, client_id: str, workspace_id: str) -> None:
        """Handle client connection"""
        with self.lock:
            connection = WebSocketConnection(
                client_id=client_id,
                workspace_id=workspace_id,
                connected_at=datetime.utcnow().timestamp()
            )
            
            self.connected_clients[client_id] = connection
            
            # Auto-subscribe to workspace room
            workspace_room = f"workspace_{workspace_id}"
            self.room_subscriptions[workspace_room].add(client_id)
            connection.room_subscriptions.add(workspace_room)
            
            logger.info(f"Client {client_id} connected (workspace: {workspace_id})")
    
    def handle_disconnect(self, client_id: str) -> None:
        """Handle client disconnection"""
        with self.lock:
            if client_id not in self.connected_clients:
                return
            
            connection = self.connected_clients[client_id]
            
            # Remove from subscriptions
            for event_type in list(connection.subscriptions):
                self.subscriptions[event_type].discard(client_id)
            
            # Remove from rooms
            for room in list(connection.room_subscriptions):
                self.room_subscriptions[room].discard(client_id)
            
            del self.connected_clients[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    def handle_subscribe(self, client_id: str, event_type: str) -> None:
        """Subscribe client to event type"""
        with self.lock:
            if client_id not in self.connected_clients:
                return
            
            self.subscriptions[event_type].add(client_id)
            self.connected_clients[client_id].subscriptions.add(event_type)
            
            logger.debug(f"Client {client_id} subscribed to {event_type}")
    
    def handle_unsubscribe(self, client_id: str, event_type: str) -> None:
        """Unsubscribe client from event type"""
        with self.lock:
            if client_id not in self.connected_clients:
                return
            
            self.subscriptions[event_type].discard(client_id)
            self.connected_clients[client_id].subscriptions.discard(event_type)
            
            logger.debug(f"Client {client_id} unsubscribed from {event_type}")
    
    def handle_subscribe_room(self, client_id: str, room: str) -> None:
        """Subscribe client to room"""
        with self.lock:
            if client_id not in self.connected_clients:
                return
            
            self.room_subscriptions[room].add(client_id)
            self.connected_clients[client_id].room_subscriptions.add(room)
            
            logger.debug(f"Client {client_id} joined room {room}")
    
    def handle_unsubscribe_room(self, client_id: str, room: str) -> None:
        """Unsubscribe client from room"""
        with self.lock:
            if client_id not in self.connected_clients:
                return
            
            self.room_subscriptions[room].discard(client_id)
            self.connected_clients[client_id].room_subscriptions.discard(room)
            
            logger.debug(f"Client {client_id} left room {room}")
    
    def handle_heartbeat(self, client_id: str) -> Dict[str, Any]:
        """Handle client heartbeat"""
        with self.lock:
            if client_id not in self.connected_clients:
                return {'error': 'Client not found'}
            
            return {
                'server_time': datetime.utcnow().timestamp(),
                'active_clients': len(self.connected_clients),
                'status': 'alive'
            }
    
    # ===================== EVENT BROADCASTING =====================
    
    def broadcast_prediction_completed(self, request_id: str, endpoint_id: str,
                                       model_id: str, model_version: int,
                                       latency_ms: float, workspace_id: str) -> None:
        """Broadcast prediction completion event"""
        event = {
            'type': 'prediction_completed',
            'request_id': request_id,
            'endpoint_id': endpoint_id,
            'model_id': model_id,
            'model_version': model_version,
            'latency_ms': latency_ms,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        logger.debug(f"Broadcasted prediction_completed: {request_id}")
    
    def broadcast_batch_completed(self, batch_id: str, endpoint_id: str,
                                 results_count: int, duration_ms: float,
                                 workspace_id: str) -> None:
        """Broadcast batch completion event"""
        event = {
            'type': 'batch_completed',
            'batch_id': batch_id,
            'endpoint_id': endpoint_id,
            'results_count': results_count,
            'duration_ms': duration_ms,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        logger.debug(f"Broadcasted batch_completed: {batch_id}")
    
    def broadcast_alert_triggered(self, alert_id: str, endpoint_id: str,
                                 severity: str, metric_name: str,
                                 current_value: float, threshold: float,
                                 workspace_id: str) -> None:
        """Broadcast alert triggered event"""
        event = {
            'type': 'alert_triggered',
            'alert_id': alert_id,
            'endpoint_id': endpoint_id,
            'severity': severity,
            'metric_name': metric_name,
            'current_value': current_value,
            'threshold': threshold,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_subscribers('alert_triggered', event)
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        logger.info(f"Broadcasted alert_triggered: {alert_id}")
    
    def broadcast_deployment_progress(self, deployment_id: str, endpoint_id: str,
                                     current_traffic: float, target_traffic: float,
                                     progress_percent: float, workspace_id: str) -> None:
        """Broadcast deployment progress event"""
        event = {
            'type': 'deployment_progress',
            'deployment_id': deployment_id,
            'endpoint_id': endpoint_id,
            'current_traffic': current_traffic,
            'target_traffic': target_traffic,
            'progress_percent': progress_percent,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_subscribers('deployment_progress', event)
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        logger.debug(f"Broadcasted deployment_progress: {deployment_id}")
    
    def broadcast_deployment_completed(self, deployment_id: str, endpoint_id: str,
                                      new_model_version: int, workspace_id: str) -> None:
        """Broadcast deployment completion event"""
        event = {
            'type': 'deployment_completed',
            'deployment_id': deployment_id,
            'endpoint_id': endpoint_id,
            'new_model_version': new_model_version,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_subscribers('deployment_completed', event)
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        logger.info(f"Broadcasted deployment_completed: {deployment_id}")
    
    def broadcast_deployment_rolled_back(self, deployment_id: str, endpoint_id: str,
                                        reason: str, workspace_id: str) -> None:
        """Broadcast deployment rollback event"""
        event = {
            'type': 'deployment_rolled_back',
            'deployment_id': deployment_id,
            'endpoint_id': endpoint_id,
            'reason': reason,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_subscribers('deployment_rolled_back', event)
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        logger.warning(f"Broadcasted deployment_rolled_back: {deployment_id}")
    
    def broadcast_model_loaded(self, endpoint_id: str, model_id: str,
                              model_version: int, workspace_id: str) -> None:
        """Broadcast model loaded event"""
        event = {
            'type': 'model_loaded',
            'endpoint_id': endpoint_id,
            'model_id': model_id,
            'model_version': model_version,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        logger.debug(f"Broadcasted model_loaded: {model_id} v{model_version}")
    
    def broadcast_model_unloaded(self, endpoint_id: str, model_id: str,
                                model_version: int, workspace_id: str) -> None:
        """Broadcast model unloaded event"""
        event = {
            'type': 'model_unloaded',
            'endpoint_id': endpoint_id,
            'model_id': model_id,
            'model_version': model_version,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        logger.debug(f"Broadcasted model_unloaded: {model_id} v{model_version}")
    
    def broadcast_endpoint_health_changed(self, endpoint_id: str, new_status: str,
                                         unhealthy_instances: List[str],
                                         workspace_id: str) -> None:
        """Broadcast endpoint health change event"""
        event = {
            'type': 'endpoint_health_changed',
            'endpoint_id': endpoint_id,
            'new_status': new_status,
            'unhealthy_instances': unhealthy_instances,
            'unhealthy_count': len(unhealthy_instances),
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_subscribers('endpoint_health_changed', event)
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        logger.warning(f"Broadcasted endpoint_health_changed: {endpoint_id}")
    
    def broadcast_anomaly_detected(self, anomaly_id: str, endpoint_id: str,
                                  metric_name: str, value: float, baseline: float,
                                  confidence: float, workspace_id: str) -> None:
        """Broadcast anomaly detected event"""
        event = {
            'type': 'anomaly_detected',
            'anomaly_id': anomaly_id,
            'endpoint_id': endpoint_id,
            'metric_name': metric_name,
            'value': value,
            'baseline': baseline,
            'deviation_percent': ((value - baseline) / baseline * 100) if baseline != 0 else 0,
            'confidence': confidence,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_subscribers('anomaly_detected', event)
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        logger.warning(f"Broadcasted anomaly_detected: {anomaly_id}")
    
    def broadcast_sla_violated(self, violation_id: str, sla_id: str, endpoint_id: str,
                              violation_type: str, expected_value: float,
                              actual_value: float, workspace_id: str) -> None:
        """Broadcast SLA violation event"""
        event = {
            'type': 'sla_violated',
            'violation_id': violation_id,
            'sla_id': sla_id,
            'endpoint_id': endpoint_id,
            'violation_type': violation_type,
            'expected_value': expected_value,
            'actual_value': actual_value,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_subscribers('sla_violated', event)
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        logger.critical(f"Broadcasted sla_violated: {violation_id}")
    
    # ===================== BROADCAST METHODS =====================
    
    def broadcast_to_subscribers(self, event_type: str, event: Dict[str, Any]) -> None:
        """Broadcast to all subscribers of event type"""
        with self.lock:
            client_ids = list(self.subscriptions.get(event_type, set()))
        
        for client_id in client_ids:
            self._send_to_client(client_id, event)
    
    def broadcast_to_room(self, room: str, event: Dict[str, Any]) -> None:
        """Broadcast to all clients in room"""
        with self.lock:
            client_ids = list(self.room_subscriptions.get(room, set()))
        
        for client_id in client_ids:
            self._send_to_client(client_id, event)
    
    def broadcast_to_client(self, client_id: str, event: Dict[str, Any]) -> None:
        """Broadcast to specific client"""
        self._send_to_client(client_id, event)
    
    def _send_to_client(self, client_id: str, event: Dict[str, Any]) -> None:
        """Send event to client (implementation depends on transport)"""
        # This would integrate with actual WebSocket or Socket.IO implementation
        # For now, just log
        logger.debug(f"Sending {event.get('type')} to {client_id}")
        
        # Trigger callback for testing
        callback_type = event.get('type')
        if callback_type in self.callbacks:
            for callback in self.callbacks[callback_type]:
                try:
                    callback({'client_id': client_id, 'event': event})
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    # ===================== STATISTICS & MONITORING =====================
    
    def get_connected_clients(self) -> List[Dict[str, Any]]:
        """Get list of connected clients"""
        with self.lock:
            return [
                {
                    'client_id': client_id,
                    'workspace_id': conn.workspace_id,
                    'subscriptions': len(conn.subscriptions),
                    'rooms': len(conn.room_subscriptions),
                    'connected_at': conn.connected_at
                }
                for client_id, conn in self.connected_clients.items()
            ]
    
    def get_workspace_clients(self, workspace_id: str) -> List[str]:
        """Get client IDs in workspace"""
        with self.lock:
            workspace_room = f"workspace_{workspace_id}"
            return list(self.room_subscriptions.get(workspace_room, set()))
    
    def get_subscription_stats(self) -> Dict[str, int]:
        """Get subscription statistics"""
        with self.lock:
            return {
                'event_type': event_type,
                'subscriber_count': len(subscribers)
            } for event_type, subscribers in self.subscriptions.items()
        } if self.subscriptions else {}
    
    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        with self.lock:
            return {
                'status': 'healthy',
                'connected_clients': len(self.connected_clients),
                'subscription_count': sum(len(subs) for subs in self.subscriptions.values()),
                'room_count': len(self.room_subscriptions),
                'timestamp': datetime.utcnow().timestamp()
            }
    
    # ===================== CALLBACKS =====================
    
    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register callback for event type"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        
        self.callbacks[event_type].append(callback)
