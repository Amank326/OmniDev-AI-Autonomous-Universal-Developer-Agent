"""
Phase 26: Collaboration WebSocket Handler
Real-time presence, live updates, activity streaming, notifications
"""

from socketio import emit, join_room, leave_room
from datetime import datetime
from typing import Dict, Optional, Set

# ========================================================================
# WEBSOCKET EVENT HANDLERS
# ========================================================================

class CollaborationWebSocketHandler:
    """Handles all WebSocket events for collaboration"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.user_rooms: Dict[str, Set[str]] = {}  # user_id -> {room_ids}
        self.room_users: Dict[str, Set[str]] = {}  # room_id -> {user_ids}
        self.user_presence: Dict[str, Dict] = {}   # user_id -> presence_info
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all WebSocket event handlers"""
        self.socketio.on('connect', self.on_connect)
        self.socketio.on('disconnect', self.on_disconnect)
        self.socketio.on('join_workspace', self.on_join_workspace)
        self.socketio.on('leave_workspace', self.on_leave_workspace)
        self.socketio.on('update_presence', self.on_update_presence)
        self.socketio.on('user_typing', self.on_user_typing)
        self.socketio.on('stop_typing', self.on_stop_typing)
        self.socketio.on('metric_created', self.on_metric_created)
        self.socketio.on('metric_updated', self.on_metric_updated)
        self.socketio.on('insight_generated', self.on_insight_generated)
        self.socketio.on('insight_shared', self.on_insight_shared)
        self.socketio.on('insight_commented', self.on_insight_commented)
        self.socketio.on('insight_reacted', self.on_insight_reacted)
        self.socketio.on('forecast_generated', self.on_forecast_generated)
        self.socketio.on('dashboard_updated', self.on_dashboard_updated)
        self.socketio.on('dashboard_shared', self.on_dashboard_shared)
        self.socketio.on('cursor_moved', self.on_cursor_moved)
        self.socketio.on('selection_changed', self.on_selection_changed)
        self.socketio.on('member_joined_workspace', self.on_member_joined)
        self.socketio.on('member_left_workspace', self.on_member_left)
        self.socketio.on('request_collaboration', self.on_request_collaboration)
        self.socketio.on('mention_user', self.on_mention_user)
        self.socketio.on('send_notification', self.on_send_notification)
        self.socketio.on('mark_notification_read', self.on_notification_read)
        self.socketio.on('pin_message', self.on_pin_message)
        self.socketio.on('unpin_message', self.on_unpin_message)
        self.socketio.on('emoji_reaction', self.on_emoji_reaction)
        self.socketio.on('request_metrics', self.on_request_metrics)
        self.socketio.on('stream_activity', self.on_stream_activity)
        self.socketio.on('request_presence_update', self.on_request_presence_update)
        self.socketio.on('bulk_update', self.on_bulk_update)
    
    
    # ====================================================================
    # CONNECTION LIFECYCLE
    # ====================================================================
    
    def on_connect(self):
        """Handle user connection"""
        return {
            'status': 'connected',
            'message': 'WebSocket connected successfully',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def on_disconnect(self):
        """Handle user disconnection"""
        # Cleanup user presence
        return {
            'status': 'disconnected',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    
    # ====================================================================
    # WORKSPACE PRESENCE
    # ====================================================================
    
    def on_join_workspace(self, data):
        """User joins workspace"""
        user_id = data['user_id']
        workspace_id = data['workspace_id']
        room_id = f"workspace:{workspace_id}"
        
        # Join Socket.IO room
        join_room(room_id)
        
        # Track membership
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        self.user_rooms[user_id].add(room_id)
        
        if room_id not in self.room_users:
            self.room_users[room_id] = set()
        self.room_users[room_id].add(user_id)
        
        # Broadcast presence update
        emit('user_joined_workspace', {
            'user_id': user_id,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'joined': True, 'workspace_id': workspace_id}
    
    def on_leave_workspace(self, data):
        """User leaves workspace"""
        user_id = data['user_id']
        workspace_id = data['workspace_id']
        room_id = f"workspace:{workspace_id}"
        
        # Leave Socket.IO room
        leave_room(room_id)
        
        # Update tracking
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(room_id)
        if room_id in self.room_users:
            self.room_users[room_id].discard(user_id)
        
        # Broadcast presence update
        emit('user_left_workspace', {
            'user_id': user_id,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'left': True, 'workspace_id': workspace_id}
    
    def on_update_presence(self, data):
        """Update user presence status"""
        user_id = data['user_id']
        workspace_id = data['workspace_id']
        status = data.get('status', 'active')
        current_view = data.get('current_view')
        
        # Store presence
        self.user_presence[user_id] = {
            'user_id': user_id,
            'workspace_id': workspace_id,
            'status': status,
            'current_view': current_view,
            'last_activity': datetime.utcnow().isoformat()
        }
        
        room_id = f"workspace:{workspace_id}"
        emit('presence_updated', self.user_presence[user_id], room=room_id)
        
        return {'presence_updated': True}
    
    
    # ====================================================================
    # COLLABORATIVE EDITING
    # ====================================================================
    
    def on_user_typing(self, data):
        """Broadcast that user is typing"""
        workspace_id = data['workspace_id']
        user_id = data['user_id']
        metric_id = data.get('metric_id')
        
        room_id = f"workspace:{workspace_id}"
        emit('user_typing', {
            'user_id': user_id,
            'metric_id': metric_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id, skip_sid=None)
        
        return {'typing': True}
    
    def on_stop_typing(self, data):
        """Broadcast typing stopped"""
        workspace_id = data['workspace_id']
        user_id = data['user_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('user_stopped_typing', {
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'stopped_typing': True}
    
    def on_cursor_moved(self, data):
        """Track cursor position for collaborative editing"""
        workspace_id = data['workspace_id']
        user_id = data['user_id']
        position = data['position']
        
        room_id = f"workspace:{workspace_id}"
        emit('cursor_moved', {
            'user_id': user_id,
            'position': position,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id, skip_sid=None)
        
        return {'cursor_updated': True}
    
    def on_selection_changed(self, data):
        """Track selection changes"""
        workspace_id = data['workspace_id']
        user_id = data['user_id']
        selection = data['selection']
        
        room_id = f"workspace:{workspace_id}"
        emit('selection_changed', {
            'user_id': user_id,
            'selection': selection,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id, skip_sid=None)
        
        return {'selection_updated': True}
    
    
    # ====================================================================
    # ANALYTICS EVENTS
    # ====================================================================
    
    def on_metric_created(self, data):
        """Broadcast metric creation"""
        workspace_id = data['workspace_id']
        metric_id = data['metric_id']
        created_by = data['created_by']
        
        room_id = f"workspace:{workspace_id}"
        emit('metric_created', {
            'metric_id': metric_id,
            'metric_name': data.get('metric_name'),
            'created_by': created_by,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'broadcast': True}
    
    def on_metric_updated(self, data):
        """Broadcast metric update"""
        workspace_id = data['workspace_id']
        metric_id = data['metric_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('metric_updated', {
            'metric_id': metric_id,
            'updated_by': data['updated_by'],
            'changes': data.get('changes', {}),
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'broadcast': True}
    
    def on_forecast_generated(self, data):
        """Broadcast forecast generation"""
        workspace_id = data['workspace_id']
        metric_id = data['metric_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('forecast_generated', {
            'metric_id': metric_id,
            'forecast_id': data.get('forecast_id'),
            'generated_by': data['generated_by'],
            'forecast_value': data.get('forecast_value'),
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'broadcast': True}
    
    
    # ====================================================================
    # INSIGHT EVENTS
    # ====================================================================
    
    def on_insight_generated(self, data):
        """Broadcast insight generation"""
        workspace_id = data['workspace_id']
        insight_id = data['insight_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('insight_generated', {
            'insight_id': insight_id,
            'title': data.get('title'),
            'generated_by': data['generated_by'],
            'severity': data.get('severity'),
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'broadcast': True}
    
    def on_insight_shared(self, data):
        """Broadcast insight sharing"""
        workspace_id = data['workspace_id']
        insight_id = data['insight_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('insight_shared', {
            'insight_id': insight_id,
            'shared_by': data['shared_by'],
            'visibility': data.get('visibility'),
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'broadcast': True}
    
    def on_insight_commented(self, data):
        """Broadcast insight comment"""
        workspace_id = data['workspace_id']
        insight_id = data['insight_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('insight_commented', {
            'insight_id': insight_id,
            'comment_id': data.get('comment_id'),
            'user_id': data['user_id'],
            'text': data.get('text'),
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'broadcast': True}
    
    def on_insight_reacted(self, data):
        """Broadcast insight reaction"""
        workspace_id = data['workspace_id']
        insight_id = data['insight_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('insight_reacted', {
            'insight_id': insight_id,
            'user_id': data['user_id'],
            'reaction': data.get('reaction'),
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'broadcast': True}
    
    
    # ====================================================================
    # DASHBOARD EVENTS
    # ====================================================================
    
    def on_dashboard_updated(self, data):
        """Broadcast dashboard update"""
        workspace_id = data['workspace_id']
        dashboard_id = data['dashboard_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('dashboard_updated', {
            'dashboard_id': dashboard_id,
            'updated_by': data['updated_by'],
            'changes': data.get('changes', {}),
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'broadcast': True}
    
    def on_dashboard_shared(self, data):
        """Broadcast dashboard sharing"""
        workspace_id = data['workspace_id']
        dashboard_id = data['dashboard_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('dashboard_shared', {
            'dashboard_id': dashboard_id,
            'shared_by': data['shared_by'],
            'shared_with': data.get('shared_with'),
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'broadcast': True}
    
    
    # ====================================================================
    # COLLABORATION FEATURES
    # ====================================================================
    
    def on_request_collaboration(self, data):
        """Request collaboration from team member"""
        workspace_id = data['workspace_id']
        requested_from = data['requested_from']
        
        # Emit to specific user
        emit('collaboration_requested', {
            'requested_by': data['requested_by'],
            'metric_id': data.get('metric_id'),
            'message': data.get('message'),
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"user:{requested_from}")
        
        return {'request_sent': True}
    
    def on_mention_user(self, data):
        """Mention user in comment/insight"""
        workspace_id = data['workspace_id']
        mentioned_user = data['mentioned_user']
        
        # Emit notification to mentioned user
        emit('user_mentioned', {
            'mentioned_by': data['mentioned_by'],
            'context': data.get('context'),
            'resource_id': data.get('resource_id'),
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"user:{mentioned_user}")
        
        return {'mention_sent': True}
    
    def on_send_notification(self, data):
        """Send notification to users"""
        recipient_ids = data.get('recipient_ids', [])
        
        for recipient in recipient_ids:
            emit('notification_received', {
                'title': data.get('title'),
                'message': data.get('message'),
                'type': data.get('type'),
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"user:{recipient}")
        
        return {'notifications_sent': True}
    
    def on_notification_read(self, data):
        """Mark notification as read"""
        workspace_id = data['workspace_id']
        notification_id = data['notification_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('notification_marked_read', {
            'notification_id': notification_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'marked_read': True}
    
    
    # ====================================================================
    # ACTIVITY TRACKING
    # ====================================================================
    
    def on_member_joined(self, data):
        """Member joined workspace"""
        workspace_id = data['workspace_id']
        user_id = data['user_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('member_joined', {
            'user_id': user_id,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'broadcast': True}
    
    def on_member_left(self, data):
        """Member left workspace"""
        workspace_id = data['workspace_id']
        user_id = data['user_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('member_left', {
            'user_id': user_id,
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'broadcast': True}
    
    def on_stream_activity(self, data):
        """Stream activity updates"""
        workspace_id = data['workspace_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('activity_update', {
            'user_id': data['user_id'],
            'action': data['action'],
            'resource': data.get('resource'),
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'stream_sent': True}
    
    
    # ====================================================================
    # UTILITY METHODS
    # ====================================================================
    
    def on_pin_message(self, data):
        """Pin message in workspace"""
        workspace_id = data['workspace_id']
        message_id = data['message_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('message_pinned', {
            'message_id': message_id,
            'pinned_by': data['pinned_by'],
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'pinned': True}
    
    def on_unpin_message(self, data):
        """Unpin message from workspace"""
        workspace_id = data['workspace_id']
        message_id = data['message_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('message_unpinned', {
            'message_id': message_id,
            'unpinned_by': data['unpinned_by'],
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'unpinned': True}
    
    def on_emoji_reaction(self, data):
        """Add emoji reaction to message"""
        workspace_id = data['workspace_id']
        message_id = data['message_id']
        
        room_id = f"workspace:{workspace_id}"
        emit('emoji_reacted', {
            'message_id': message_id,
            'user_id': data['user_id'],
            'emoji': data.get('emoji'),
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'reacted': True}
    
    def on_request_metrics(self, data):
        """Request metrics updates"""
        workspace_id = data['workspace_id']
        metric_ids = data.get('metric_ids', [])
        
        return {
            'metrics': metric_ids,
            'status': 'requested',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def on_request_presence_update(self, data):
        """Request current presence updates"""
        workspace_id = data['workspace_id']
        room_id = f"workspace:{workspace_id}"
        
        # Return current presence info for workspace
        presence_list = [
            p for p in self.user_presence.values()
            if p.get('workspace_id') == workspace_id
        ]
        
        emit('presence_list', {'users': presence_list})
        
        return {'presence_updated': True}
    
    def on_bulk_update(self, data):
        """Handle bulk updates"""
        workspace_id = data['workspace_id']
        updates = data.get('updates', [])
        
        room_id = f"workspace:{workspace_id}"
        emit('bulk_update_received', {
            'count': len(updates),
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {'bulk_processed': True, 'count': len(updates)}
