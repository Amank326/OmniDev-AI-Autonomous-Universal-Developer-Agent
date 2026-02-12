"""
Phase 35: Training WebSocket Handler
Real-time training progress, HPO updates, and model registry events

Events:
- training_started: Training job started
- epoch_update: End of epoch metrics
- convergence_check: Early stopping evaluation
- training_completed: Training finished
- trial_suggested: HPO trial ready
- trial_completed: HPO trial finished
- search_completed: HPO search done
- model_promoted: Model version promoted
- model_deprecated: Model version deprecated
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class TrainingWebSocketHandler:
    """
    WebSocket handler for real-time training and optimization updates
    """
    
    def __init__(self):
        """Initialize WebSocket handler"""
        self.clients: List[Dict[str, Any]] = []  # Connected clients
        self.subscriptions: Dict[str, List[str]] = defaultdict(list)  # Event -> client IDs
        self.room_subscriptions: Dict[str, List[str]] = defaultdict(list)  # Room -> client IDs
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = threading.RLock()
        
        logger.info("TrainingWebSocketHandler initialized")
    
    def handle_connect(self, client_id: str, workspace_id: str) -> Dict[str, Any]:
        """
        Handle client connection
        
        Args:
            client_id: Unique client ID
            workspace_id: Workspace ID
            
        Returns:
            Connection acknowledgment
        """
        with self.lock:
            client = {
                'client_id': client_id,
                'workspace_id': workspace_id,
                'connected_at': datetime.utcnow().timestamp(),
                'subscribed_events': set(),
                'subscribed_rooms': set()
            }
            self.clients.append(client)
            
            # Auto-subscribe to workspace room
            room = f"workspace_{workspace_id}"
            self.room_subscriptions[room].append(client_id)
            client['subscribed_rooms'].add(room)
        
        logger.info(f"Client connected: {client_id} (workspace: {workspace_id})")
        
        return {
            'type': 'connection_acknowledged',
            'client_id': client_id,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def handle_disconnect(self, client_id: str) -> None:
        """
        Handle client disconnection
        
        Args:
            client_id: Client ID
        """
        with self.lock:
            # Remove client
            self.clients = [c for c in self.clients if c['client_id'] != client_id]
            
            # Remove from all subscriptions
            for event_subs in self.subscriptions.values():
                if client_id in event_subs:
                    event_subs.remove(client_id)
            
            for room_subs in self.room_subscriptions.values():
                if client_id in room_subs:
                    room_subs.remove(client_id)
        
        logger.info(f"Client disconnected: {client_id}")
    
    def handle_subscribe(self, client_id: str, event_type: str) -> Dict[str, Any]:
        """
        Subscribe client to event type
        
        Args:
            client_id: Client ID
            event_type: Event type to subscribe to
            
        Returns:
            Subscription acknowledgment
        """
        with self.lock:
            client = next((c for c in self.clients if c['client_id'] == client_id), None)
            if not client:
                return {'error': f'Client {client_id} not found'}
            
            if event_type not in self.subscriptions[event_type]:
                self.subscriptions[event_type].append(client_id)
                client['subscribed_events'].add(event_type)
        
        logger.debug(f"Client {client_id} subscribed to {event_type}")
        
        return {
            'type': 'subscription_acknowledged',
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def handle_unsubscribe(self, client_id: str, event_type: str) -> Dict[str, Any]:
        """
        Unsubscribe client from event type
        
        Args:
            client_id: Client ID
            event_type: Event type
            
        Returns:
            Unsubscription acknowledgment
        """
        with self.lock:
            client = next((c for c in self.clients if c['client_id'] == client_id), None)
            if not client:
                return {'error': f'Client {client_id} not found'}
            
            if client_id in self.subscriptions[event_type]:
                self.subscriptions[event_type].remove(client_id)
                client['subscribed_events'].discard(event_type)
        
        logger.debug(f"Client {client_id} unsubscribed from {event_type}")
        
        return {
            'type': 'unsubscription_acknowledged',
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def handle_subscribe_room(self, client_id: str, room: str) -> Dict[str, Any]:
        """
        Subscribe client to room
        
        Args:
            client_id: Client ID
            room: Room name
            
        Returns:
            Room subscription acknowledgment
        """
        with self.lock:
            client = next((c for c in self.clients if c['client_id'] == client_id), None)
            if not client:
                return {'error': f'Client {client_id} not found'}
            
            if client_id not in self.room_subscriptions[room]:
                self.room_subscriptions[room].append(client_id)
                client['subscribed_rooms'].add(room)
        
        logger.debug(f"Client {client_id} subscribed to room {room}")
        
        return {
            'type': 'room_subscription_acknowledged',
            'room': room,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def handle_unsubscribe_room(self, client_id: str, room: str) -> Dict[str, Any]:
        """
        Unsubscribe client from room
        
        Args:
            client_id: Client ID
            room: Room name
            
        Returns:
            Room unsubscription acknowledgment
        """
        with self.lock:
            client = next((c for c in self.clients if c['client_id'] == client_id), None)
            if not client:
                return {'error': f'Client {client_id} not found'}
            
            if client_id in self.room_subscriptions[room]:
                self.room_subscriptions[room].remove(client_id)
                client['subscribed_rooms'].discard(room)
        
        logger.debug(f"Client {client_id} unsubscribed from room {room}")
        
        return {
            'type': 'room_unsubscription_acknowledged',
            'room': room,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def handle_heartbeat(self, client_id: str) -> Dict[str, Any]:
        """
        Handle client heartbeat
        
        Args:
            client_id: Client ID
            
        Returns:
            Heartbeat response
        """
        with self.lock:
            client = next((c for c in self.clients if c['client_id'] == client_id), None)
            if not client:
                return {'error': f'Client {client_id} not found'}
            
            client_count = len(self.clients)
        
        return {
            'type': 'heartbeat_ack',
            'client_id': client_id,
            'timestamp': datetime.utcnow().isoformat(),
            'server_time': datetime.utcnow().timestamp(),
            'active_clients': client_count
        }
    
    # ========================================================================
    # Event Broadcasting Methods
    # ========================================================================
    
    def broadcast_training_started(self, training_id: str, model_name: str,
                                   workspace_id: str) -> None:
        """Broadcast training started event"""
        event = {
            'type': 'training_started',
            'training_id': training_id,
            'model_name': model_name,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        self.broadcast_to_subscribers('training_started', event)
    
    def broadcast_epoch_update(self, training_id: str, epoch: int, metrics: Dict[str, float],
                              val_metrics: Dict[str, float], workspace_id: str) -> None:
        """Broadcast epoch metrics update"""
        event = {
            'type': 'epoch_update',
            'training_id': training_id,
            'epoch': epoch,
            'metrics': metrics,
            'val_metrics': val_metrics,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        self.broadcast_to_subscribers('epoch_update', event)
    
    def broadcast_convergence_check(self, training_id: str, should_stop: bool,
                                   reason: Optional[str], workspace_id: str) -> None:
        """Broadcast convergence check event"""
        event = {
            'type': 'convergence_check',
            'training_id': training_id,
            'should_stop': should_stop,
            'reason': reason,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        self.broadcast_to_subscribers('convergence_check', event)
    
    def broadcast_training_completed(self, training_id: str, status: str,
                                    duration_minutes: float, best_epoch: int,
                                    best_metrics: Dict[str, float], workspace_id: str) -> None:
        """Broadcast training completed event"""
        event = {
            'type': 'training_completed',
            'training_id': training_id,
            'status': status,
            'duration_minutes': duration_minutes,
            'best_epoch': best_epoch,
            'best_metrics': best_metrics,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        self.broadcast_to_subscribers('training_completed', event)
    
    def broadcast_trial_suggested(self, search_id: str, trial_id: str, trial_number: int,
                                 workspace_id: str) -> None:
        """Broadcast HPO trial suggestion"""
        event = {
            'type': 'trial_suggested',
            'search_id': search_id,
            'trial_id': trial_id,
            'trial_number': trial_number,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        self.broadcast_to_subscribers('trial_suggested', event)
    
    def broadcast_trial_completed(self, search_id: str, trial_id: str, trial_number: int,
                                 objective_value: float, is_best: bool, workspace_id: str) -> None:
        """Broadcast HPO trial completion"""
        event = {
            'type': 'trial_completed',
            'search_id': search_id,
            'trial_id': trial_id,
            'trial_number': trial_number,
            'objective_value': objective_value,
            'is_best': is_best,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        self.broadcast_to_subscribers('trial_completed', event)
    
    def broadcast_search_completed(self, search_id: str, total_trials: int,
                                  best_value: float, best_hyperparameters: Dict[str, Any],
                                  workspace_id: str) -> None:
        """Broadcast HPO search completion"""
        event = {
            'type': 'search_completed',
            'search_id': search_id,
            'total_trials': total_trials,
            'best_value': best_value,
            'best_hyperparameters': best_hyperparameters,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        self.broadcast_to_subscribers('search_completed', event)
    
    def broadcast_model_promoted(self, model_id: str, version: int, to_stage: str,
                                workspace_id: str) -> None:
        """Broadcast model promotion event"""
        event = {
            'type': 'model_promoted',
            'model_id': model_id,
            'version': version,
            'to_stage': to_stage,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        self.broadcast_to_subscribers('model_promoted', event)
    
    def broadcast_model_deprecated(self, model_id: str, version: int,
                                  message: Optional[str], workspace_id: str) -> None:
        """Broadcast model deprecation event"""
        event = {
            'type': 'model_deprecated',
            'model_id': model_id,
            'version': version,
            'message': message,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        self.broadcast_to_subscribers('model_deprecated', event)
    
    def broadcast_version_created(self, model_id: str, version: int, workspace_id: str) -> None:
        """Broadcast model version creation"""
        event = {
            'type': 'version_created',
            'model_id': model_id,
            'version': version,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.broadcast_to_room(f"workspace_{workspace_id}", event)
        self.broadcast_to_subscribers('version_created', event)
    
    # ========================================================================
    # Broadcast Methods
    # ========================================================================
    
    def broadcast_to_subscribers(self, event_type: str, event: Dict[str, Any]) -> None:
        """
        Broadcast event to all subscribers of event type
        
        Args:
            event_type: Event type
            event: Event data
        """
        with self.lock:
            client_ids = list(self.subscriptions.get(event_type, []))
        
        for client_id in client_ids:
            self._send_to_client(client_id, event)
        
        logger.debug(f"Event broadcasted to {len(client_ids)} subscribers: {event_type}")
    
    def broadcast_to_room(self, room: str, event: Dict[str, Any]) -> None:
        """
        Broadcast event to all clients in room
        
        Args:
            room: Room name
            event: Event data
        """
        with self.lock:
            client_ids = list(self.room_subscriptions.get(room, []))
        
        for client_id in client_ids:
            self._send_to_client(client_id, event)
        
        logger.debug(f"Event broadcasted to {len(client_ids)} clients in room {room}")
    
    def broadcast_to_client(self, client_id: str, event: Dict[str, Any]) -> None:
        """
        Send event to specific client
        
        Args:
            client_id: Client ID
            event: Event data
        """
        self._send_to_client(client_id, event)
    
    def _send_to_client(self, client_id: str, event: Dict[str, Any]) -> None:
        """
        Send event to client (mock implementation)
        
        Args:
            client_id: Client ID
            event: Event data
        """
        # In production, this would use Socket.IO emit
        logger.debug(f"Event sent to {client_id}: {event.get('type')}")
        
        # Trigger callbacks
        callbacks = list(self.callbacks.get('message', []))
        for callback in callbacks:
            try:
                callback({'client_id': client_id, 'event': event})
            except Exception as e:
                logger.error(f"Callback error: {str(e)}")
    
    # ========================================================================
    # Statistics and Management
    # ========================================================================
    
    def get_connected_clients(self) -> List[Dict[str, Any]]:
        """Get list of connected clients"""
        with self.lock:
            return [
                {
                    'client_id': c['client_id'],
                    'workspace_id': c['workspace_id'],
                    'connected_at': c['connected_at'],
                    'subscribed_events': len(c['subscribed_events']),
                    'subscribed_rooms': len(c['subscribed_rooms'])
                }
                for c in self.clients
            ]
    
    def get_workspace_clients(self, workspace_id: str) -> List[str]:
        """Get all client IDs in workspace"""
        with self.lock:
            return [c['client_id'] for c in self.clients if c['workspace_id'] == workspace_id]
    
    def get_subscription_stats(self) -> Dict[str, int]:
        """Get subscription statistics"""
        with self.lock:
            return {
                'total_clients': len(self.clients),
                'total_subscriptions': sum(len(subs) for subs in self.subscriptions.values()),
                'total_rooms': len(self.room_subscriptions),
                'events': {event: len(subs) for event, subs in self.subscriptions.items()}
            }
    
    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register callback for WebSocket events"""
        with self.lock:
            self.callbacks[event_type].append(callback)
    
    def health_check(self) -> Dict[str, Any]:
        """Get WebSocket handler health status"""
        with self.lock:
            return {
                'status': 'healthy',
                'connected_clients': len(self.clients),
                'total_subscriptions': sum(len(subs) for subs in self.subscriptions.values()),
                'total_rooms': len(self.room_subscriptions),
                'timestamp': datetime.utcnow().isoformat()
            }
