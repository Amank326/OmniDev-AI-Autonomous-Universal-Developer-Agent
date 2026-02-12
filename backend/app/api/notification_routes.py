"""
Notification API Routes - RESTful endpoints for notification management
Phase 27: Advanced Notifications & Real-time Alerts System
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, time
from .notification_service import NotificationService, NotificationType, NotificationChannel, NotificationStatus
from .alert_rules_engine import AlertRulesEngine, AlertSeverity, ConditionType, AlertStatus
from .notification_preference_service import NotificationPreferenceService
from .realtime_alerts_service import RealTimeAlertsService

# Initialize blueprint
notification_bp = Blueprint('notification', __name__, url_prefix='/api/v1/notification')

# Initialize services
notification_service = NotificationService()
alert_engine = AlertRulesEngine()
preference_service = NotificationPreferenceService()
realtime_service = RealTimeAlertsService()


# ============================================================
# NOTIFICATION ENDPOINTS (12)
# ============================================================

@notification_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get user notifications with filtering"""
    user_id = request.args.get('user_id')
    notification_type = request.args.get('notification_type')
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 50))

    notif_type = NotificationType[notification_type.upper()] if notification_type else None
    notifications = notification_service.get_user_notifications(user_id, notif_type, unread_only, limit)

    return jsonify({
        'status': 'success',
        'count': len(notifications),
        'data': [
            {
                'id': n.id,
                'type': n.notification_type.value,
                'title': n.content.title,
                'body': n.content.body,
                'status': n.status.value,
                'created_at': n.created_at.isoformat(),
                'read_at': n.read_at.isoformat() if n.read_at else None,
            }
            for n in notifications
        ]
    }), 200


@notification_bp.route('/notifications/<notification_id>', methods=['GET'])
def get_notification(notification_id):
    """Get specific notification"""
    notification = notification_service.get_notification(notification_id)

    if not notification:
        return jsonify({'error': 'Notification not found'}), 404

    return jsonify({
        'status': 'success',
        'data': {
            'id': notification.id,
            'type': notification.notification_type.value,
            'title': notification.content.title,
            'body': notification.content.body,
            'action_url': notification.content.action_url,
            'status': notification.status.value,
            'created_at': notification.created_at.isoformat(),
            'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
            'read_at': notification.read_at.isoformat() if notification.read_at else None,
        }
    }), 200


@notification_bp.route('/notifications', methods=['POST'])
def create_notification():
    """Create and send notification"""
    data = request.json
    user_id = data.get('user_id')
    notification_type = data.get('notification_type', 'system')
    title = data.get('title')
    body = data.get('body')
    channels = data.get('channels', ['in_app'])

    from .notification_service import NotificationContent
    content = NotificationContent(title=title, body=body)
    notification = notification_service.create_notification(
        user_id=user_id,
        notification_type=NotificationType[notification_type.upper()],
        content=content,
        channels=[NotificationChannel[ch.upper()] for ch in channels]
    )

    results = notification_service.send_notification(notification.id)

    return jsonify({
        'status': 'success',
        'id': notification.id,
        'delivery_status': results
    }), 201


@notification_bp.route('/notifications/<notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    """Mark notification as read"""
    success = notification_service.mark_as_read(notification_id)

    if not success:
        return jsonify({'error': 'Notification not found'}), 404

    return jsonify({'status': 'success', 'message': 'Notification marked as read'}), 200


@notification_bp.route('/notifications/<notification_id>/delivered', methods=['PUT'])
def mark_notification_delivered(notification_id):
    """Mark notification as delivered"""
    success = notification_service.mark_as_delivered(notification_id)

    if not success:
        return jsonify({'error': 'Notification not found'}), 404

    return jsonify({'status': 'success', 'message': 'Notification marked as delivered'}), 200


@notification_bp.route('/notifications/<notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete notification"""
    success = notification_service.delete_notification(notification_id)

    if not success:
        return jsonify({'error': 'Notification not found'}), 404

    return jsonify({'status': 'success', 'message': 'Notification deleted'}), 200


@notification_bp.route('/notifications/search', methods=['GET'])
def search_notifications():
    """Search notifications"""
    user_id = request.args.get('user_id')
    query = request.args.get('q', '')
    notification_type = request.args.get('notification_type')

    notif_type = NotificationType[notification_type.upper()] if notification_type else None
    results = notification_service.search_notifications(user_id, query, notif_type)

    return jsonify({
        'status': 'success',
        'count': len(results),
        'data': [
            {
                'id': n.id,
                'title': n.content.title,
                'body': n.content.body,
                'created_at': n.created_at.isoformat(),
            }
            for n in results
        ]
    }), 200


@notification_bp.route('/notifications/bulk-read', methods=['PUT'])
def bulk_mark_read():
    """Mark multiple notifications as read"""
    data = request.json
    user_id = data.get('user_id')
    notification_ids = data.get('notification_ids', [])

    count = notification_service.bulk_mark_read(user_id, notification_ids)

    return jsonify({
        'status': 'success',
        'marked_read': count
    }), 200


@notification_bp.route('/notifications/stats', methods=['GET'])
def get_notification_stats():
    """Get notification statistics"""
    user_id = request.args.get('user_id')
    stats = notification_service.get_notification_stats(user_id)

    return jsonify({
        'status': 'success',
        'data': stats
    }), 200


@notification_bp.route('/notifications/retry/<notification_id>', methods=['POST'])
def retry_notification(notification_id):
    """Retry failed notification"""
    success = notification_service.retry_failed_notification(notification_id)

    if not success:
        return jsonify({'error': 'Cannot retry notification'}), 400

    return jsonify({'status': 'success', 'message': 'Retry initiated'}), 200


@notification_bp.route('/notifications/cleanup', methods=['POST'])
def cleanup_old_notifications():
    """Clean up old notifications"""
    days = request.json.get('days', 90) if request.json else 90
    deleted = notification_service.cleanup_old_notifications(days)

    return jsonify({
        'status': 'success',
        'deleted_count': deleted
    }), 200


# ============================================================
# ALERT RULE ENDPOINTS (10)
# ============================================================

@notification_bp.route('/rules', methods=['GET'])
def list_alert_rules():
    """List alert rules"""
    enabled_only = request.args.get('enabled_only', 'false').lower() == 'true'
    rules = alert_engine.list_rules(enabled_only)

    return jsonify({
        'status': 'success',
        'count': len(rules),
        'data': [
            {
                'id': r.id,
                'name': r.name,
                'description': r.description,
                'severity': r.target_severity.value,
                'enabled': r.enabled,
                'created_at': r.created_at.isoformat(),
            }
            for r in rules
        ]
    }), 200


@notification_bp.route('/rules', methods=['POST'])
def create_alert_rule():
    """Create alert rule"""
    data = request.json
    from .alert_rules_engine import AlertCondition

    conditions = [
        AlertCondition(
            condition_type=ConditionType[c['condition_type'].upper()],
            field=c['field'],
            operator=c['operator'],
            value=c['value']
        )
        for c in data.get('conditions', [])
    ]

    rule = alert_engine.create_rule(
        name=data.get('name'),
        description=data.get('description'),
        conditions=conditions,
        target_severity=AlertSeverity[data.get('severity', 'warning').upper()],
        created_by=data.get('created_by'),
        logical_operator=data.get('logical_operator', 'AND'),
        cooldown_minutes=data.get('cooldown_minutes', 15),
        notification_channels=data.get('notification_channels', ['in_app'])
    )

    return jsonify({
        'status': 'success',
        'id': rule.id,
        'message': 'Alert rule created'
    }), 201


@notification_bp.route('/rules/<rule_id>', methods=['GET'])
def get_alert_rule(rule_id):
    """Get alert rule"""
    rule = alert_engine.rules.get(rule_id)

    if not rule:
        return jsonify({'error': 'Rule not found'}), 404

    return jsonify({
        'status': 'success',
        'data': {
            'id': rule.id,
            'name': rule.name,
            'description': rule.description,
            'severity': rule.target_severity.value,
            'enabled': rule.enabled,
            'conditions': [
                {
                    'type': c.condition_type.value,
                    'field': c.field,
                    'operator': c.operator,
                    'value': c.value
                }
                for c in rule.conditions
            ]
        }
    }), 200


@notification_bp.route('/rules/<rule_id>', methods=['PUT'])
def update_alert_rule(rule_id):
    """Update alert rule"""
    data = request.json
    rule = alert_engine.update_rule(rule_id, **data)

    if not rule:
        return jsonify({'error': 'Rule not found'}), 404

    return jsonify({'status': 'success', 'message': 'Rule updated'}), 200


@notification_bp.route('/rules/<rule_id>', methods=['DELETE'])
def delete_alert_rule(rule_id):
    """Delete alert rule"""
    success = alert_engine.delete_rule(rule_id)

    if not success:
        return jsonify({'error': 'Rule not found'}), 404

    return jsonify({'status': 'success', 'message': 'Rule deleted'}), 200


@notification_bp.route('/rules/<rule_id>/evaluate', methods=['POST'])
def evaluate_rule(rule_id):
    """Evaluate rule against data"""
    data = request.json.get('data', {})
    matched, details = alert_engine.evaluate_rule(rule_id, data)

    return jsonify({
        'status': 'success',
        'matched': matched,
        'details': details
    }), 200


@notification_bp.route('/rules/<rule_id>/trigger', methods=['POST'])
def trigger_alert_from_rule(rule_id):
    """Trigger alert from rule"""
    data = request.json
    alert = alert_engine.trigger_alert(
        rule_id=rule_id,
        user_id=data.get('user_id'),
        title=data.get('title'),
        message=data.get('message'),
        source=data.get('source', 'system'),
        data=data.get('data')
    )

    if not alert:
        return jsonify({'error': 'Cannot trigger alert'}), 400

    return jsonify({
        'status': 'success',
        'alert_id': alert.id
    }), 201


@notification_bp.route('/alerts', methods=['GET'])
def get_active_alerts():
    """Get active alerts for user"""
    user_id = request.args.get('user_id')
    severity = request.args.get('severity')

    sev = AlertSeverity[severity.upper()] if severity else None
    alerts = alert_engine.get_active_alerts(user_id, sev)

    return jsonify({
        'status': 'success',
        'count': len(alerts),
        'data': [
            {
                'id': a.id,
                'title': a.title,
                'message': a.message,
                'severity': a.severity.value,
                'status': a.status.value,
                'created_at': a.created_at.isoformat(),
            }
            for a in alerts
        ]
    }), 200


@notification_bp.route('/alerts/<alert_id>/acknowledge', methods=['PUT'])
def acknowledge_alert(alert_id):
    """Acknowledge alert"""
    data = request.json
    success = alert_engine.acknowledge_alert(alert_id, data.get('user_id'))

    if not success:
        return jsonify({'error': 'Alert not found'}), 404

    realtime_service.acknowledge_alert(alert_id, data.get('user_id'))

    return jsonify({'status': 'success', 'message': 'Alert acknowledged'}), 200


@notification_bp.route('/alerts/<alert_id>/resolve', methods=['PUT'])
def resolve_alert(alert_id):
    """Resolve alert"""
    success = alert_engine.resolve_alert(alert_id)

    if not success:
        return jsonify({'error': 'Alert not found'}), 404

    return jsonify({'status': 'success', 'message': 'Alert resolved'}), 200


@notification_bp.route('/alerts/timeline', methods=['GET'])
def get_alert_timeline():
    """Get alert timeline"""
    user_id = request.args.get('user_id')
    hours = int(request.args.get('hours', 24))

    alerts = alert_engine.get_alert_timeline(user_id, hours)

    return jsonify({
        'status': 'success',
        'count': len(alerts),
        'data': [
            {
                'id': a.id,
                'title': a.title,
                'severity': a.severity.value,
                'status': a.status.value,
                'created_at': a.created_at.isoformat(),
            }
            for a in alerts
        ]
    }), 200


# ============================================================
# PREFERENCE ENDPOINTS (8)
# ============================================================

@notification_bp.route('/preferences', methods=['GET'])
def get_preferences():
    """Get user notification preferences"""
    user_id = request.args.get('user_id')
    prefs = preference_service.get_or_create_preferences(user_id)

    return jsonify({
        'status': 'success',
        'data': preference_service.export_preferences(user_id)
    }), 200


@notification_bp.route('/preferences/channels/<channel>', methods=['PUT'])
def update_channel_preference(channel):
    """Update channel preference"""
    data = request.json
    user_id = data.get('user_id')

    success = preference_service.update_channel_preference(
        user_id=user_id,
        channel=NotificationChannel[channel.upper()],
        enabled=data.get('enabled', True),
        priority=data.get('priority', 1),
        min_severity=AlertSeverity[data.get('min_severity', 'info').upper()],
        frequency_cap=data.get('frequency_cap')
    )

    return jsonify({
        'status': 'success' if success else 'error',
        'message': 'Preference updated' if success else 'Failed to update'
    }), 200 if success else 400


@notification_bp.route('/preferences/dnd', methods=['PUT'])
def set_dnd_schedule():
    """Set Do Not Disturb schedule"""
    data = request.json
    user_id = data.get('user_id')

    start_time = datetime.fromisoformat(data.get('start_time', '22:00')).time()
    end_time = datetime.fromisoformat(data.get('end_time', '08:00')).time()

    dnd = preference_service.set_dnd_schedule(
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        allow_urgent=data.get('allow_urgent', True)
    )

    return jsonify({'status': 'success', 'dnd_id': dnd.id}), 200


@notification_bp.route('/preferences/dnd/toggle', methods=['PUT'])
def toggle_dnd():
    """Enable/disable Do Not Disturb"""
    data = request.json
    success = preference_service.enable_dnd(data.get('user_id'), data.get('enabled', False))

    return jsonify({'status': 'success' if success else 'error'}), 200 if success else 400


@notification_bp.route('/preferences/frequency-cap', methods=['PUT'])
def set_frequency_cap():
    """Set channel frequency cap"""
    data = request.json
    success = preference_service.set_frequency_cap(
        data.get('user_id'),
        NotificationChannel[data.get('channel').upper()],
        data.get('cap', 10)
    )

    return jsonify({'status': 'success' if success else 'error'}), 200 if success else 400


@notification_bp.route('/preferences/enable-global', methods=['PUT'])
def set_global_enable():
    """Enable/disable notifications globally"""
    data = request.json
    success = preference_service.enable_globally(data.get('user_id'), data.get('enabled', True))

    return jsonify({'status': 'success' if success else 'error'}), 200 if success else 400


@notification_bp.route('/preferences/keywords', methods=['POST'])
def add_keyword_to_follow():
    """Add keyword to follow"""
    data = request.json
    success = preference_service.add_keyword_to_follow(data.get('user_id'), data.get('keyword'))

    return jsonify({'status': 'success' if success else 'error'}), 200 if success else 400


@notification_bp.route('/preferences/muted-keywords', methods=['POST'])
def add_muted_keyword():
    """Add muted keyword"""
    data = request.json
    success = preference_service.add_muted_keyword(data.get('user_id'), data.get('keyword'))

    return jsonify({'status': 'success' if success else 'error'}), 200 if success else 400


# ============================================================
# REAL-TIME ALERT ENDPOINTS (5)
# ============================================================

@notification_bp.route('/realtime/subscribe', methods=['POST'])
def subscribe_to_rule():
    """Subscribe to alert rule"""
    data = request.json
    subscription = realtime_service.create_subscription(
        data.get('user_id'),
        data.get('rule_id')
    )

    return jsonify({
        'status': 'success',
        'subscription_id': subscription.id
    }), 201


@notification_bp.route('/realtime/unsubscribe/<subscription_id>', methods=['DELETE'])
def unsubscribe_from_rule(subscription_id):
    """Unsubscribe from alert rule"""
    success = realtime_service.remove_subscription(subscription_id)

    return jsonify({'status': 'success' if success else 'error'}), 200 if success else 404


@notification_bp.route('/realtime/connections/<user_id>', methods=['GET'])
def get_user_connections(user_id):
    """Get user WebSocket connections"""
    connections = realtime_service.get_user_connections(user_id)

    return jsonify({
        'status': 'success',
        'count': len(connections),
        'data': connections
    }), 200


@notification_bp.route('/realtime/stats', methods=['GET'])
def get_realtime_stats():
    """Get real-time alert statistics"""
    stats = realtime_service.get_delivery_statistics()

    return jsonify({
        'status': 'success',
        'data': stats
    }), 200


@notification_bp.route('/realtime/batch-deliver', methods=['POST'])
def batch_deliver_alerts():
    """Deliver batched alerts"""
    max_age = request.json.get('max_age_seconds', 300) if request.json else 300
    results = realtime_service.deliver_batches(max_age)

    return jsonify({
        'status': 'success',
        'data': results
    }), 200


# ============================================================
# UTILITY ENDPOINTS (2)
# ============================================================

@notification_bp.route('/health', methods=['GET'])
def notification_health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'notification',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@notification_bp.route('/stats', methods=['GET'])
def notification_system_stats():
    """System-wide statistics"""
    alert_stats = alert_engine.get_alert_statistics(request.args.get('user_id', ''))
    realtime_stats = realtime_service.get_delivery_statistics()

    return jsonify({
        'status': 'success',
        'alerts': alert_stats,
        'realtime': realtime_stats
    }), 200
