"""
Notification WebSocket Handler - Real-time alert and notification delivery
Phase 27: Advanced Notifications & Real-time Alerts System
"""

from datetime import datetime
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from .services.realtime_alerts_service import RealTimeAlertsService, PushStrategy
from .services.notification_preference_service import NotificationPreferenceService
from .services.alert_rules_engine import AlertRulesEngine
from .services.notification_service import NotificationService

# Initialize services
realtime_service = RealTimeAlertsService()
preference_service = NotificationPreferenceService()
alert_engine = AlertRulesEngine()
notification_service = NotificationService()


class NotificationWebSocketHandler:
    """WebSocket handler for real-time notifications and alerts"""

    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.user_rooms = {}  # user_id -> set of room names
        self.room_users = {}  # room_name -> set of user_ids
        self.user_presence = {}  # user_id -> presence_status
        self.pending_notifications = {}  # user_id -> list of notifications

    def register_handlers(self):
        """Register all WebSocket event handlers"""

        # Connection handlers
        @self.socketio.on('connect')
        def handle_connect():
            from flask_socketio import request
            connection_id = request.sid
            user_id = request.args.get('user_id')

            if not user_id:
                return False

            # Register connection
            realtime_service.register_websocket_connection(connection_id, user_id)

            # Join user's personal room
            join_room(f"user:{user_id}")

            # Store user room mapping
            if user_id not in self.user_rooms:
                self.user_rooms[user_id] = set()
            self.user_rooms[user_id].add(f"user:{user_id}")

            # Emit connection success
            emit('connection_established', {
                'connection_id': connection_id,
                'timestamp': datetime.utcnow().isoformat()
            })

            return True

        @self.socketio.on('disconnect')
        def handle_disconnect():
            from flask_socketio import request
            connection_id = request.sid
            realtime_service.unregister_websocket_connection(connection_id)

        # ============================================================
        # SUBSCRIPTION & ROOM MANAGEMENT (5)
        # ============================================================

        @self.socketio.on('subscribe_to_rule')
        def handle_subscribe_to_rule(data):
            """Subscribe to specific alert rule"""
            user_id = data.get('user_id')
            rule_id = data.get('rule_id')

            subscription = realtime_service.create_subscription(user_id, rule_id)

            # Join rule-specific room
            rule_room = f"rule:{rule_id}"
            join_room(rule_room)

            if user_id not in self.user_rooms:
                self.user_rooms[user_id] = set()
            self.user_rooms[user_id].add(rule_room)

            emit('subscription_confirmed', {
                'subscription_id': subscription.id,
                'rule_id': rule_id,
                'timestamp': datetime.utcnow().isoformat()
            })

        @self.socketio.on('unsubscribe_from_rule')
        def handle_unsubscribe_from_rule(data):
            """Unsubscribe from alert rule"""
            user_id = data.get('user_id')
            subscription_id = data.get('subscription_id')

            realtime_service.remove_subscription(subscription_id)
            leave_room(f"rule:{data.get('rule_id')}")

            emit('unsubscribed', {'subscription_id': subscription_id})

        @self.socketio.on('join_workspace')
        def handle_join_workspace(data):
            """Join workspace room"""
            user_id = data.get('user_id')
            workspace_id = data.get('workspace_id')

            room = f"workspace:{workspace_id}"
            join_room(room)

            if user_id not in self.user_rooms:
                self.user_rooms[user_id] = set()
            self.user_rooms[user_id].add(room)

            # Broadcast user joined
            self.socketio.emit(
                'user_joined_workspace',
                {'user_id': user_id, 'workspace_id': workspace_id},
                room=room,
                skip_sid=None
            )

        @self.socketio.on('leave_workspace')
        def handle_leave_workspace(data):
            """Leave workspace room"""
            user_id = data.get('user_id')
            workspace_id = data.get('workspace_id')

            room = f"workspace:{workspace_id}"
            leave_room(room)

            self.user_rooms[user_id].discard(room)

            self.socketio.emit(
                'user_left_workspace',
                {'user_id': user_id, 'workspace_id': workspace_id},
                room=room,
                skip_sid=None
            )

        @self.socketio.on('list_subscriptions')
        def handle_list_subscriptions(data):
            """Get user's subscriptions"""
            user_id = data.get('user_id')

            subscriptions = [
                {
                    'subscription_id': s.id,
                    'rule_id': s.rule_id,
                    'enabled': s.enabled,
                    'created_at': s.created_at.isoformat()
                }
                for s in realtime_service.subscriptions.values()
                if s.user_id == user_id
            ]

            emit('subscriptions_list', {
                'subscriptions': subscriptions,
                'count': len(subscriptions)
            })

        # ============================================================
        # ALERT DELIVERY & MANAGEMENT (9)
        # ============================================================

        @self.socketio.on('alert_triggered')
        def handle_alert_triggered(data):
            """Alert triggered event"""
            user_id = data.get('user_id')
            alert_id = data.get('alert_id')
            severity = data.get('severity', 'warning')
            rule_id = data.get('rule_id')

            # Check preferences
            from .services.notification_preference_service import AlertSeverity
            if preference_service.should_suppress_notification(user_id, None, AlertSeverity[severity.upper()]):
                emit('alert_suppressed', {'alert_id': alert_id})
                return

            # Queue for delivery
            payload = {
                'type': 'alert',
                'alert_id': alert_id,
                'severity': severity,
                'rule_id': rule_id,
                'timestamp': datetime.utcnow().isoformat()
            }

            queue_item = realtime_service.queue_alert_delivery(
                alert_id, user_id, payload, PushStrategy.IMMEDIATE
            )

            # Emit to user
            self.socketio.emit(
                'alert_delivered',
                payload,
                room=f"user:{user_id}"
            )

        @self.socketio.on('acknowledge_alert')
        def handle_acknowledge_alert(data):
            """Acknowledge alert"""
            user_id = data.get('user_id')
            alert_id = data.get('alert_id')

            realtime_service.acknowledge_alert(alert_id, user_id)
            alert_engine.acknowledge_alert(alert_id, user_id)

            # Broadcast acknowledgment
            self.socketio.emit(
                'alert_acknowledged',
                {'alert_id': alert_id, 'acknowledged_by': user_id},
                skip_sid=None
            )

        @self.socketio.on('resolve_alert')
        def handle_resolve_alert(data):
            """Resolve alert"""
            alert_id = data.get('alert_id')
            user_id = data.get('user_id')

            alert_engine.resolve_alert(alert_id)

            self.socketio.emit(
                'alert_resolved',
                {'alert_id': alert_id, 'resolved_at': datetime.utcnow().isoformat()},
                skip_sid=None
            )

        @self.socketio.on('escalate_alert')
        def handle_escalate_alert(data):
            """Escalate alert"""
            alert_id = data.get('alert_id')
            to_severity = data.get('to_severity', 'critical')

            # Broadcast escalation
            self.socketio.emit(
                'alert_escalated',
                {
                    'alert_id': alert_id,
                    'new_severity': to_severity,
                    'escalated_at': datetime.utcnow().isoformat()
                },
                skip_sid=None
            )

        @self.socketio.on('get_alert_details')
        def handle_get_alert_details(data):
            """Get alert details"""
            alert_id = data.get('alert_id')

            alert = next(
                (a for a in alert_engine.alerts.values() if a.id == alert_id),
                None
            )

            if alert:
                emit('alert_details', {
                    'id': alert.id,
                    'title': alert.title,
                    'message': alert.message,
                    'severity': alert.severity.value,
                    'status': alert.status.value,
                    'created_at': alert.created_at.isoformat(),
                })

        @self.socketio.on('batch_acknowledge_alerts')
        def handle_batch_acknowledge_alerts(data):
            """Acknowledge multiple alerts"""
            user_id = data.get('user_id')
            alert_ids = data.get('alert_ids', [])

            for alert_id in alert_ids:
                alert_engine.acknowledge_alert(alert_id, user_id)

            emit('batch_acknowledged', {
                'alert_count': len(alert_ids),
                'timestamp': datetime.utcnow().isoformat()
            })

        @self.socketio.on('request_pending_alerts')
        def handle_request_pending_alerts(data):
            """Request pending undelivered alerts"""
            user_id = data.get('user_id')

            pending = realtime_service.undelivered_alerts.get(user_id, [])

            # Try to deliver now
            for alert_item in pending:
                realtime_service.deliver_alert(alert_item.id)

            emit('pending_alerts', {
                'count': len(pending),
                'alerts': [
                    {
                        'alert_id': a.alert_id,
                        'payload': a.payload
                    }
                    for a in pending
                ]
            })

        @self.socketio.on('dismiss_notification')
        def handle_dismiss_notification(data):
            """Dismiss notification"""
            notification_id = data.get('notification_id')
            notification_service.delete_notification(notification_id)

            emit('notification_dismissed', {'notification_id': notification_id})

        # ============================================================
        # PREFERENCE MANAGEMENT (5)
        # ============================================================

        @self.socketio.on('update_dnd_preference')
        def handle_update_dnd_preference(data):
            """Update Do Not Disturb settings"""
            user_id = data.get('user_id')
            enabled = data.get('enabled', False)

            preference_service.enable_dnd(user_id, enabled)

            emit('dnd_preference_updated', {
                'enabled': enabled,
                'timestamp': datetime.utcnow().isoformat()
            })

        @self.socketio.on('update_channel_preference')
        def handle_update_channel_preference(data):
            """Update channel notification preference"""
            user_id = data.get('user_id')
            channel = data.get('channel')
            enabled = data.get('enabled')

            from .services.notification_preference_service import NotificationChannel
            preference_service.update_channel_preference(
                user_id, NotificationChannel[channel.upper()], enabled,
                data.get('priority', 1),
                data.get('min_severity', 'info')
            )

            emit('channel_preference_updated', {
                'channel': channel,
                'enabled': enabled,
                'timestamp': datetime.utcnow().isoformat()
            })

        @self.socketio.on('update_frequency_cap')
        def handle_update_frequency_cap(data):
            """Update notification frequency cap"""
            user_id = data.get('user_id')
            channel = data.get('channel')
            cap = data.get('cap', 10)

            from .services.notification_preference_service import NotificationChannel
            preference_service.set_frequency_cap(user_id, NotificationChannel[channel.upper()], cap)

            emit('frequency_cap_updated', {
                'channel': channel,
                'cap': cap
            })

        @self.socketio.on('add_muted_keyword')
        def handle_add_muted_keyword(data):
            """Add muted keyword"""
            user_id = data.get('user_id')
            keyword = data.get('keyword')

            preference_service.add_muted_keyword(user_id, keyword)

            emit('muted_keyword_added', {'keyword': keyword})

        @self.socketio.on('remove_muted_keyword')
        def handle_remove_muted_keyword(data):
            """Remove muted keyword"""
            user_id = data.get('user_id')
            keyword = data.get('keyword')

            preference_service.remove_muted_keyword(user_id, keyword)

            emit('muted_keyword_removed', {'keyword': keyword})

        # ============================================================
        # MONITORING & HEALTH (4)
        # ============================================================

        @self.socketio.on('heartbeat')
        def handle_heartbeat(data):
            """Connection heartbeat"""
            from flask_socketio import request
            connection_id = request.sid

            realtime_service.heartbeat_connection(connection_id)
            emit('heartbeat_ack', {'timestamp': datetime.utcnow().isoformat()})

        @self.socketio.on('request_connection_status')
        def handle_request_connection_status(data):
            """Get connection status"""
            from flask_socketio import request
            connection_id = request.sid

            status = realtime_service.get_connection_status(connection_id)

            emit('connection_status', status)

        @self.socketio.on('request_system_stats')
        def handle_request_system_stats(data):
            """Request real-time system stats"""
            stats = realtime_service.get_delivery_statistics()

            emit('system_stats', {
                'timestamp': datetime.utcnow().isoformat(),
                'stats': stats
            })

        @self.socketio.on('request_alert_timeline')
        def handle_request_alert_timeline(data):
            """Request alert timeline"""
            user_id = data.get('user_id')
            hours = data.get('hours', 24)

            timeline = alert_engine.get_alert_timeline(user_id, hours)

            emit('alert_timeline', {
                'count': len(timeline),
                'alerts': [
                    {
                        'id': a.id,
                        'title': a.title,
                        'severity': a.severity.value,
                        'created_at': a.created_at.isoformat()
                    }
                    for a in timeline
                ]
            })

        # ============================================================
        # TESTING & DEBUGGING (2)
        # ============================================================

        @self.socketio.on('test_alert')
        def handle_test_alert(data):
            """Send test alert for debugging"""
            user_id = data.get('user_id')

            payload = {
                'type': 'test_alert',
                'title': 'Test Alert',
                'message': 'This is a test alert',
                'severity': 'warning',
                'timestamp': datetime.utcnow().isoformat()
            }

            self.socketio.emit(
                'alert_delivered',
                payload,
                room=f"user:{user_id}"
            )

            emit('test_alert_sent', {'timestamp': datetime.utcnow().isoformat()})

        @self.socketio.on('get_diagnostics')
        def handle_get_diagnostics(data):
            """Get system diagnostics"""
            user_id = data.get('user_id')

            diagnostics = {
                'user_id': user_id,
                'connected_at': realtime_service.websocket_connections.get(
                    list(realtime_service.user_connections.get(user_id, []))[0] if user_id in realtime_service.user_connections else None
                ).connected_at.isoformat() if user_id in realtime_service.user_connections else None,
                'active_subscriptions': len([
                    s for s in realtime_service.subscriptions.values()
                    if s.user_id == user_id and s.enabled
                ]),
                'pending_alerts': len(realtime_service.undelivered_alerts.get(user_id, [])),
                'message': 'Diagnostics collected successfully'
            }

            emit('diagnostics', diagnostics)


def init_notification_websocket(socketio: SocketIO):
    """Initialize notification WebSocket handler"""
    handler = NotificationWebSocketHandler(socketio)
    handler.register_handlers()
    return handler
