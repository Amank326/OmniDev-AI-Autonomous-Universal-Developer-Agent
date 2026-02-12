"""
Phase 34: Monitoring WebSocket Handler
Real-time event streaming for logs, traces, metrics, and alerts

Provides real-time WebSocket streaming for:
- Log events: New logs, aggregated statistics
- Trace events: New traces, span completions, critical path updates
- Metric events: Metric recordings, aggregations, threshold breaches
- Alert events: New alerts, alert state changes, resolutions

Namespace: /monitoring
Authentication: X-Workspace-ID in initial connection query

Events:
- log_event: Real-time log events
- trace_event: Real-time trace events
- metric_update: Metric value updates
- alert_notification: Alert state changes
"""

from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask import request
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import uuid
from threading import Lock

logger = logging.getLogger(__name__)

# Service instances (injected via app context)
logger_service = None
tracer_service = None
metrics_service = None

# Connected clients tracker
connected_clients: Dict[str, Dict[str, Any]] = {}
clients_lock = Lock()


@dataclass
class ClientConnection:
    """Track connected client information"""
    client_id: str
    workspace_id: str
    connected_at: float
    subscriptions: List[str]  # ["logs", "traces", "metrics", "alerts"]
    last_heartbeat: float
    

class MonitoringWebSocketHandler:
    """
    WebSocket handler for real-time monitoring events
    
    Manages client connections, subscriptions, and broadcasting of monitoring events
    """
    
    def __init__(self, socketio: SocketIO):
        """
        Initialize WebSocket handler
        
        Args:
            socketio: Flask-SocketIO instance
        """
        self.socketio = socketio
        self.subscriptions: Dict[str, List[str]] = {}  # client_id -> [subscriptions]
        self.clients: Dict[str, ClientConnection] = {}
        self.lock = Lock()
        
    def register_services(self, logger_svc, tracer_svc, metrics_svc) -> None:
        """Register monitoring service instances"""
        global logger_service, tracer_service, metrics_service
        logger_service = logger_svc
        tracer_service = tracer_svc
        metrics_service = metrics_svc
        logger.info("WebSocket services registered")
        
    def handle_connect(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle client connection
        
        Args:
            data: Connection data with workspace_id
            
        Returns: Connection confirmation with client_id
        """
        workspace_id = request.headers.get('X-Workspace-ID')
        if not workspace_id:
            return {'error': 'X-Workspace-ID header required'}, False
        
        client_id = str(uuid.uuid4())
        connection = ClientConnection(
            client_id=client_id,
            workspace_id=workspace_id,
            connected_at=datetime.utcnow().timestamp(),
            subscriptions=[],
            last_heartbeat=datetime.utcnow().timestamp()
        )
        
        with self.lock:
            self.clients[client_id] = connection
            self.subscriptions[client_id] = []
        
        # Join workspace room for broadcasting
        join_room(f"workspace_{workspace_id}")
        
        logger.info(f"Client {client_id} connected to workspace {workspace_id}")
        
        return {
            'client_id': client_id,
            'workspace_id': workspace_id,
            'connected_at': connection.connected_at,
            'status': 'connected'
        }
        
    def handle_disconnect(self) -> None:
        """Handle client disconnection"""
        client_id = request.sid
        
        with self.lock:
            if client_id in self.clients:
                connection = self.clients.pop(client_id)
                self.subscriptions.pop(client_id, None)
                logger.info(f"Client {client_id} disconnected from {connection.workspace_id}")
                
    def handle_subscribe(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle subscription to event types
        
        Args:
            data: {
                "events": ["logs", "traces", "metrics", "alerts"]
            }
        """
        client_id = request.sid
        
        if client_id not in self.clients:
            return {'error': 'Client not connected'}, False
        
        events = data.get('events', [])
        valid_events = ['logs', 'traces', 'metrics', 'alerts']
        subscribed = [e for e in events if e in valid_events]
        
        with self.lock:
            if client_id in self.subscriptions:
                self.subscriptions[client_id].extend(subscribed)
                self.clients[client_id].subscriptions = list(set(self.subscriptions[client_id]))
        
        logger.info(f"Client {client_id} subscribed to {subscribed}")
        
        return {
            'subscribed_to': subscribed,
            'all_subscriptions': self.subscriptions.get(client_id, [])
        }
        
    def handle_unsubscribe(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle unsubscription from event types
        
        Args:
            data: {
                "events": ["logs", "traces"]
            }
        """
        client_id = request.sid
        
        if client_id not in self.clients:
            return {'error': 'Client not connected'}, False
        
        events = data.get('events', [])
        
        with self.lock:
            if client_id in self.subscriptions:
                self.subscriptions[client_id] = [
                    e for e in self.subscriptions[client_id] if e not in events
                ]
                self.clients[client_id].subscriptions = self.subscriptions[client_id]
        
        logger.info(f"Client {client_id} unsubscribed from {events}")
        
        return {
            'unsubscribed_from': events,
            'remaining_subscriptions': self.subscriptions.get(client_id, [])
        }
        
    def handle_heartbeat(self) -> Dict[str, Any]:
        """Handle client heartbeat"""
        client_id = request.sid
        
        with self.lock:
            if client_id in self.clients:
                self.clients[client_id].last_heartbeat = datetime.utcnow().timestamp()
        
        return {'heartbeat': True}
        
    def broadcast_log_event(self, workspace_id: str, log_entry: Any) -> None:
        """
        Broadcast new log event to subscribed clients
        
        Args:
            workspace_id: Target workspace
            log_entry: Log entry object
        """
        room = f"workspace_{workspace_id}"
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'log': log_entry.__dict__ if hasattr(log_entry, '__dict__') else log_entry,
            'type': 'log_event'
        }
        
        self.socketio.emit('log_event', event_data, room=room)
        
    def broadcast_trace_event(self, workspace_id: str, trace_data: Any, event_type: str) -> None:
        """
        Broadcast trace event (new trace, span completion, critical path update)
        
        Args:
            workspace_id: Target workspace
            trace_data: Trace or span object
            event_type: 'trace_started', 'span_completed', 'critical_path_updated'
        """
        room = f"workspace_{workspace_id}"
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'trace': trace_data.__dict__ if hasattr(trace_data, '__dict__') else trace_data,
            'event_type': event_type,
            'type': 'trace_event'
        }
        
        self.socketio.emit('trace_event', event_data, room=room)
        
    def broadcast_metric_update(self, workspace_id: str, metric_name: str, value: float, 
                               labels: Dict[str, str] = None) -> None:
        """
        Broadcast metric update event
        
        Args:
            workspace_id: Target workspace
            metric_name: Metric name
            value: Recorded value
            labels: Optional metric labels
        """
        room = f"workspace_{workspace_id}"
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'metric_name': metric_name,
            'value': value,
            'labels': labels or {},
            'type': 'metric_update'
        }
        
        self.socketio.emit('metric_update', event_data, room=room)
        
    def broadcast_metric_aggregation(self, workspace_id: str, metric_name: str, 
                                    aggregation: Any, period: str) -> None:
        """
        Broadcast aggregated metric event
        
        Args:
            workspace_id: Target workspace
            metric_name: Metric name
            aggregation: Aggregated metrics object
            period: Aggregation period (MINUTE, HOUR, DAY, etc.)
        """
        room = f"workspace_{workspace_id}"
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'metric_name': metric_name,
            'aggregation': aggregation.__dict__ if hasattr(aggregation, '__dict__') else aggregation,
            'period': period,
            'type': 'metric_aggregation'
        }
        
        self.socketio.emit('metric_aggregation', event_data, room=room)
        
    def broadcast_alert_notification(self, workspace_id: str, alert_event: Any) -> None:
        """
        Broadcast alert event (new alert, state change, resolution)
        
        Args:
            workspace_id: Target workspace
            alert_event: Alert event object
        """
        room = f"workspace_{workspace_id}"
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'alert': alert_event.__dict__ if hasattr(alert_event, '__dict__') else alert_event,
            'type': 'alert_notification'
        }
        
        self.socketio.emit('alert_notification', event_data, room=room)
        
    def broadcast_dashboard_update(self, workspace_id: str, dashboard_data: Dict[str, Any]) -> None:
        """
        Broadcast dashboard summary update
        
        Args:
            workspace_id: Target workspace
            dashboard_data: Dashboard summary (logs count, traces count, metrics count, active alerts)
        """
        room = f"workspace_{workspace_id}"
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'dashboard': dashboard_data,
            'type': 'dashboard_update'
        }
        
        self.socketio.emit('dashboard_update', event_data, room=room)
        
    def get_client_stats(self) -> Dict[str, Any]:
        """Get WebSocket client statistics"""
        with self.lock:
            total_clients = len(self.clients)
            subscriptions_summary = {}
            
            for client_id, subs in self.subscriptions.items():
                for sub in subs:
                    subscriptions_summary[sub] = subscriptions_summary.get(sub, 0) + 1
        
        return {
            'total_connected': total_clients,
            'subscriptions': subscriptions_summary,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific client"""
        with self.lock:
            if client_id not in self.clients:
                return None
            
            client = self.clients[client_id]
            return {
                'client_id': client.client_id,
                'workspace_id': client.workspace_id,
                'connected_at': client.connected_at,
                'subscriptions': client.subscriptions,
                'last_heartbeat': client.last_heartbeat
            }


def setup_monitoring_websocket(socketio: SocketIO) -> MonitoringWebSocketHandler:
    """
    Setup monitoring WebSocket handler with event handlers
    
    Args:
        socketio: Flask-SocketIO instance
        
    Returns: Configured MonitoringWebSocketHandler instance
    """
    handler = MonitoringWebSocketHandler(socketio)
    
    # Connection/disconnection handlers
    @socketio.on('connect', namespace='/monitoring')
    def on_connect(data=None):
        """Handle client connection"""
        result = handler.handle_connect(data or {})
        emit('connect_response', result, namespace='/monitoring')
        return result
    
    @socketio.on('disconnect', namespace='/monitoring')
    def on_disconnect():
        """Handle client disconnection"""
        handler.handle_disconnect()
    
    # Subscription handlers
    @socketio.on('subscribe', namespace='/monitoring')
    def on_subscribe(data):
        """Handle subscription to event types"""
        result = handler.handle_subscribe(data)
        emit('subscribe_response', result, namespace='/monitoring')
        return result
    
    @socketio.on('unsubscribe', namespace='/monitoring')
    def on_unsubscribe(data):
        """Handle unsubscription from event types"""
        result = handler.handle_unsubscribe(data)
        emit('unsubscribe_response', result, namespace='/monitoring')
        return result
    
    # Heartbeat handler
    @socketio.on('heartbeat', namespace='/monitoring')
    def on_heartbeat():
        """Handle client heartbeat"""
        result = handler.handle_heartbeat()
        emit('heartbeat_response', result, namespace='/monitoring')
        return result
    
    # Statistics handler
    @socketio.on('get_stats', namespace='/monitoring')
    def on_get_stats(data=None):
        """Get WebSocket statistics"""
        stats = handler.get_client_stats()
        emit('stats_response', stats, namespace='/monitoring')
        return stats
    
    return handler


# Global handler instance (initialized in main.py)
monitoring_ws_handler = None


def initialize_monitoring_websocket(socketio: SocketIO) -> None:
    """Initialize global monitoring WebSocket handler"""
    global monitoring_ws_handler
    monitoring_ws_handler = setup_monitoring_websocket(socketio)
    logger.info("Monitoring WebSocket handler initialized")


def register_ws_services(logger_svc, tracer_svc, metrics_svc) -> None:
    """Register services with WebSocket handler"""
    if monitoring_ws_handler:
        monitoring_ws_handler.register_services(logger_svc, tracer_svc, metrics_svc)


def broadcast_log_event(workspace_id: str, log_entry: Any) -> None:
    """Broadcast log event to connected clients"""
    if monitoring_ws_handler:
        monitoring_ws_handler.broadcast_log_event(workspace_id, log_entry)


def broadcast_trace_event(workspace_id: str, trace_data: Any, event_type: str) -> None:
    """Broadcast trace event to connected clients"""
    if monitoring_ws_handler:
        monitoring_ws_handler.broadcast_trace_event(workspace_id, trace_data, event_type)


def broadcast_metric_update(workspace_id: str, metric_name: str, value: float, 
                           labels: Dict[str, str] = None) -> None:
    """Broadcast metric update to connected clients"""
    if monitoring_ws_handler:
        monitoring_ws_handler.broadcast_metric_update(workspace_id, metric_name, value, labels)


def broadcast_metric_aggregation(workspace_id: str, metric_name: str, 
                                aggregation: Any, period: str) -> None:
    """Broadcast metric aggregation to connected clients"""
    if monitoring_ws_handler:
        monitoring_ws_handler.broadcast_metric_aggregation(workspace_id, metric_name, aggregation, period)


def broadcast_alert_notification(workspace_id: str, alert_event: Any) -> None:
    """Broadcast alert notification to connected clients"""
    if monitoring_ws_handler:
        monitoring_ws_handler.broadcast_alert_notification(workspace_id, alert_event)


def broadcast_dashboard_update(workspace_id: str, dashboard_data: Dict[str, Any]) -> None:
    """Broadcast dashboard update to connected clients"""
    if monitoring_ws_handler:
        monitoring_ws_handler.broadcast_dashboard_update(workspace_id, dashboard_data)


def get_ws_client_stats() -> Dict[str, Any]:
    """Get WebSocket client statistics"""
    if monitoring_ws_handler:
        return monitoring_ws_handler.get_client_stats()
    return {'error': 'WebSocket handler not initialized'}


def get_ws_client_info(client_id: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific WebSocket client"""
    if monitoring_ws_handler:
        return monitoring_ws_handler.get_client_info(client_id)
    return None
