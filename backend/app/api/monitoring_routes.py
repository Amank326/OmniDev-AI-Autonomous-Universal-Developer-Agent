"""
Phase 34: Monitoring Routes
Flask Blueprint for REST API endpoints for enterprise monitoring and observability

Provides comprehensive monitoring endpoints for:
- Logging: Search, aggregate, retrieve logs with filtering and pagination
- Tracing: Get traces, search traces, retrieve trace metrics
- Metrics: Record, retrieve, aggregate metrics with filtering
- Alerts: Create and retrieve metric-based alerts
- Status: Service health and status endpoints

Authentication: X-Workspace-ID header (required on all endpoints)
Base URL: /api/v1/monitoring
"""

from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from functools import wraps

logger = logging.getLogger(__name__)

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/v1/monitoring')

# Service instances (injected via app context)
logger_service = None
tracer_service = None
metrics_service = None


def get_workspace_id() -> str:
    """Extract workspace ID from request headers"""
    workspace_id = request.headers.get('X-Workspace-ID')
    if not workspace_id:
        return jsonify({'error': 'X-Workspace-ID header required'}), 400
    return workspace_id


def require_workspace(f):
    """Decorator to require workspace ID header"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        workspace_id = request.headers.get('X-Workspace-ID')
        if not workspace_id:
            return jsonify({'error': 'X-Workspace-ID header required'}), 400
        return f(workspace_id=workspace_id, *args, **kwargs)
    return decorated_function


def register_monitoring_services(logger_svc, tracer_svc, metrics_svc) -> None:
    """Register service instances with blueprint"""
    global logger_service, tracer_service, metrics_service
    logger_service = logger_svc
    tracer_service = tracer_svc
    metrics_service = metrics_svc
    logger.info("Monitoring services registered")


# ==================== LOGGING ENDPOINTS ====================

@monitoring_bp.route('/logs/search', methods=['POST'])
@require_workspace
def search_logs(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Search logs with advanced filtering
    
    Request body:
    {
        "levels": ["ERROR", "WARNING"],
        "categories": ["API", "DATABASE"],
        "search_text": "timeout",
        "start_time": timestamp,
        "end_time": timestamp,
        "limit": 100,
        "offset": 0
    }
    
    Returns: {logs: [], total: int, timestamp: str}
    """
    if not logger_service:
        return jsonify({'error': 'Logger service unavailable'}), 503
    
    try:
        data = request.get_json() or {}
        filter_obj = logger_service.LogFilter(
            levels=data.get('levels', []),
            categories=data.get('categories', []),
            workspace_id=workspace_id,
            source_component=data.get('source_component'),
            user_id=data.get('user_id'),
            tags=data.get('tags', []),
            search_text=data.get('search_text'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            min_duration_ms=data.get('min_duration_ms')
        )
        
        logs = logger_service.search(filter_obj)
        limit = data.get('limit', 100)
        offset = data.get('offset', 0)
        
        return jsonify({
            'logs': logs[offset:offset+limit],
            'total': len(logs),
            'limit': limit,
            'offset': offset,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Log search failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


@monitoring_bp.route('/logs/get', methods=['GET'])
@require_workspace
def get_logs(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get logs with pagination
    
    Query parameters:
    - limit: Number of logs to retrieve (default: 100)
    - offset: Number of logs to skip (default: 0)
    - level: Filter by level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns: {logs: [], total: int, limit: int, offset: int}
    """
    if not logger_service:
        return jsonify({'error': 'Logger service unavailable'}), 503
    
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        level = request.args.get('level')
        
        filter_obj = logger_service.LogFilter(
            workspace_id=workspace_id,
            levels=[level] if level else []
        )
        
        logs = logger_service.search(filter_obj)
        paginated = logs[offset:offset+limit]
        
        return jsonify({
            'logs': paginated,
            'total': len(logs),
            'limit': limit,
            'offset': offset
        }), 200
    except Exception as e:
        logger.error(f"Get logs failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


@monitoring_bp.route('/logs/aggregate', methods=['POST'])
@require_workspace
def aggregate_logs(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get aggregated log statistics
    
    Request body:
    {
        "levels": ["ERROR"],
        "start_time": timestamp,
        "end_time": timestamp
    }
    
    Returns: {by_level: dict, by_category: dict, total: int, errors: int}
    """
    if not logger_service:
        return jsonify({'error': 'Logger service unavailable'}), 503
    
    try:
        data = request.get_json() or {}
        filter_obj = logger_service.LogFilter(
            workspace_id=workspace_id,
            levels=data.get('levels', []),
            start_time=data.get('start_time'),
            end_time=data.get('end_time')
        )
        
        aggregation = logger_service.aggregate(filter_obj)
        
        return jsonify({
            'aggregation': aggregation.__dict__ if hasattr(aggregation, '__dict__') else aggregation,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Log aggregation failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


@monitoring_bp.route('/logs/session/<session_id>', methods=['GET'])
@require_workspace
def get_session_logs(workspace_id: str, session_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get logs for a specific session
    
    Returns: {logs: [], session_id: str, count: int}
    """
    if not logger_service:
        return jsonify({'error': 'Logger service unavailable'}), 503
    
    try:
        logs = logger_service.get_session_logs(session_id)
        
        return jsonify({
            'logs': logs,
            'session_id': session_id,
            'count': len(logs)
        }), 200
    except Exception as e:
        logger.error(f"Get session logs failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


@monitoring_bp.route('/logs/request/<request_id>', methods=['GET'])
@require_workspace
def get_request_logs(workspace_id: str, request_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get logs for a specific request
    
    Returns: {logs: [], request_id: str, count: int}
    """
    if not logger_service:
        return jsonify({'error': 'Logger service unavailable'}), 503
    
    try:
        logs = logger_service.get_request_logs(request_id)
        
        return jsonify({
            'logs': logs,
            'request_id': request_id,
            'count': len(logs)
        }), 200
    except Exception as e:
        logger.error(f"Get request logs failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


# ==================== TRACING ENDPOINTS ====================

@monitoring_bp.route('/traces/get/<trace_id>', methods=['GET'])
@require_workspace
def get_trace(workspace_id: str, trace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Retrieve complete trace with all spans
    
    Returns: {trace: {...}, span_count: int, duration_ms: float}
    """
    if not tracer_service:
        return jsonify({'error': 'Tracing service unavailable'}), 503
    
    try:
        trace = tracer_service.get_trace(trace_id)
        if not trace:
            return jsonify({'error': 'Trace not found'}), 404
        
        return jsonify({
            'trace': trace.__dict__ if hasattr(trace, '__dict__') else trace,
            'span_count': len(trace.spans) if hasattr(trace, 'spans') else 0,
            'duration_ms': trace.duration_ms if hasattr(trace, 'duration_ms') else 0
        }), 200
    except Exception as e:
        logger.error(f"Get trace failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


@monitoring_bp.route('/traces/search', methods=['POST'])
@require_workspace
def search_traces(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Search traces with advanced filtering
    
    Request body:
    {
        "service_names": ["auth-service"],
        "min_duration_ms": 500,
        "status": "ERROR",
        "start_time": timestamp,
        "end_time": timestamp,
        "limit": 50
    }
    
    Returns: {traces: [], total: int}
    """
    if not tracer_service:
        return jsonify({'error': 'Tracing service unavailable'}), 503
    
    try:
        data = request.get_json() or {}
        filter_obj = tracer_service.TraceFilter(
            span_kinds=data.get('span_kinds', []),
            service_names=data.get('service_names', []),
            min_duration_ms=data.get('min_duration_ms'),
            status=data.get('status'),
            workspace_id=workspace_id,
            start_time=data.get('start_time'),
            min_spans=data.get('min_spans'),
            error_only=data.get('error_only', False)
        )
        
        traces = tracer_service.search_traces(filter_obj)
        
        return jsonify({
            'traces': traces[:data.get('limit', 50)],
            'total': len(traces)
        }), 200
    except Exception as e:
        logger.error(f"Search traces failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


@monitoring_bp.route('/traces/metrics', methods=['POST'])
@require_workspace
def get_trace_metrics(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get aggregated trace metrics
    
    Request body:
    {
        "service_names": ["auth-service"],
        "start_time": timestamp,
        "end_time": timestamp
    }
    
    Returns: {metrics: {...}, timestamp: str}
    """
    if not tracer_service:
        return jsonify({'error': 'Tracing service unavailable'}), 503
    
    try:
        data = request.get_json() or {}
        filter_obj = tracer_service.TraceFilter(
            workspace_id=workspace_id,
            service_names=data.get('service_names', []),
            start_time=data.get('start_time'),
            end_time=data.get('end_time')
        )
        
        metrics = tracer_service.get_trace_metrics(filter_obj)
        
        return jsonify({
            'metrics': metrics.__dict__ if hasattr(metrics, '__dict__') else metrics,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Get trace metrics failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


# ==================== METRICS ENDPOINTS ====================

@monitoring_bp.route('/metrics/record', methods=['POST'])
@require_workspace
def record_metric(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Record a new metric value
    
    Request body:
    {
        "metric_name": "api.request.duration",
        "value": 125.5,
        "metric_type": "HISTOGRAM",
        "unit": "ms",
        "labels": {"endpoint": "/api/users", "method": "GET"}
    }
    
    Returns: {metric_name: str, recorded: bool}
    """
    if not metrics_service:
        return jsonify({'error': 'Metrics service unavailable'}), 503
    
    try:
        data = request.get_json() or {}
        metric_name = data.get('metric_name')
        value = data.get('value')
        
        if not metric_name or value is None:
            return jsonify({'error': 'metric_name and value required'}), 400
        
        metrics_service.record_metric(
            metric_name=metric_name,
            value=value,
            workspace_id=workspace_id,
            metric_type=data.get('metric_type', 'GAUGE'),
            unit=data.get('unit'),
            labels=data.get('labels', {})
        )
        
        return jsonify({
            'metric_name': metric_name,
            'recorded': True,
            'value': value
        }), 200
    except Exception as e:
        logger.error(f"Record metric failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


@monitoring_bp.route('/metrics/get', methods=['GET'])
@require_workspace
def get_metrics(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get metrics with optional filtering
    
    Query parameters:
    - metric_name: Optional metric name filter
    - limit: Max results (default: 100)
    - offset: Pagination offset (default: 0)
    
    Returns: {metrics: [], total: int, limit: int, offset: int}
    """
    if not metrics_service:
        return jsonify({'error': 'Metrics service unavailable'}), 503
    
    try:
        metric_name = request.args.get('metric_name')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if metric_name:
            metric = metrics_service.get_metric(workspace_id, metric_name)
            metrics_list = [metric] if metric else []
        else:
            metric_filter = metrics_service.MetricFilter(
                workspace_id=workspace_id
            )
            metrics_list = metrics_service.get_metrics(metric_filter)
        
        paginated = metrics_list[offset:offset+limit]
        
        return jsonify({
            'metrics': paginated if isinstance(paginated, list) else [paginated],
            'total': len(metrics_list),
            'limit': limit,
            'offset': offset
        }), 200
    except Exception as e:
        logger.error(f"Get metrics failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


@monitoring_bp.route('/metrics/aggregate', methods=['POST'])
@require_workspace
def aggregate_metric(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Aggregate metric over time period
    
    Request body:
    {
        "metric_name": "api.request.duration",
        "period": "MINUTE",
        "start_time": timestamp,
        "end_time": timestamp
    }
    
    Returns: {metric_name: str, aggregation: {...}}
    """
    if not metrics_service:
        return jsonify({'error': 'Metrics service unavailable'}), 503
    
    try:
        data = request.get_json() or {}
        metric_name = data.get('metric_name')
        period = data.get('period', 'MINUTE')
        
        if not metric_name:
            return jsonify({'error': 'metric_name required'}), 400
        
        aggregation = metrics_service.aggregate_metric(
            workspace_id=workspace_id,
            metric_name=metric_name,
            period=period,
            start_time=data.get('start_time'),
            end_time=data.get('end_time')
        )
        
        return jsonify({
            'metric_name': metric_name,
            'period': period,
            'aggregation': aggregation.__dict__ if hasattr(aggregation, '__dict__') else aggregation
        }), 200
    except Exception as e:
        logger.error(f"Aggregate metric failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


@monitoring_bp.route('/metrics/comparison', methods=['POST'])
@require_workspace
def get_metric_comparison(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Compare metric against baseline or threshold
    
    Request body:
    {
        "metric_name": "api.request.duration",
        "comparison_type": "baseline"  # or "threshold"
    }
    
    Returns: {metric_name: str, comparison: {...}}
    """
    if not metrics_service:
        return jsonify({'error': 'Metrics service unavailable'}), 503
    
    try:
        data = request.get_json() or {}
        metric_name = data.get('metric_name')
        
        if not metric_name:
            return jsonify({'error': 'metric_name required'}), 400
        
        comparison = metrics_service.get_metric_comparison(
            workspace_id=workspace_id,
            metric_name=metric_name
        )
        
        return jsonify({
            'metric_name': metric_name,
            'comparison': comparison
        }), 200
    except Exception as e:
        logger.error(f"Get metric comparison failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


# ==================== ALERTS ENDPOINTS ====================

@monitoring_bp.route('/alerts/create', methods=['POST'])
@require_workspace
def create_alert(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Create metric-based alert
    
    Request body:
    {
        "metric_name": "api.request.duration",
        "condition": ">",
        "threshold": 1000,
        "duration_seconds": 60,
        "severity": "HIGH",
        "notification_channels": ["email", "slack"]
    }
    
    Returns: {alert_id: str, metric_name: str}
    """
    if not metrics_service:
        return jsonify({'error': 'Metrics service unavailable'}), 503
    
    try:
        data = request.get_json() or {}
        metric_name = data.get('metric_name')
        
        if not metric_name:
            return jsonify({'error': 'metric_name required'}), 400
        
        alert = metrics_service.create_alert(
            metric_name=metric_name,
            condition=data.get('condition', '>'),
            threshold=data.get('threshold'),
            workspace_id=workspace_id,
            duration_seconds=data.get('duration_seconds', 60),
            severity=data.get('severity', 'MEDIUM')
        )
        
        return jsonify({
            'alert_id': alert.alert_id if hasattr(alert, 'alert_id') else str(alert),
            'metric_name': metric_name,
            'created': True
        }), 201
    except Exception as e:
        logger.error(f"Create alert failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


@monitoring_bp.route('/alerts/get', methods=['GET'])
@require_workspace
def get_alerts(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get metric alerts
    
    Query parameters:
    - status: Filter by status (ACTIVE, RESOLVED)
    - limit: Max results (default: 50)
    
    Returns: {alerts: [], total: int}
    """
    if not metrics_service:
        return jsonify({'error': 'Metrics service unavailable'}), 503
    
    try:
        status_filter = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        
        # Get alert events from metrics service
        alert_events = metrics_service.get_alert_events(workspace_id)
        
        if status_filter and alert_events:
            alert_events = [a for a in alert_events if getattr(a, 'status', None) == status_filter]
        
        return jsonify({
            'alerts': alert_events[:limit] if alert_events else [],
            'total': len(alert_events) if alert_events else 0
        }), 200
    except Exception as e:
        logger.error(f"Get alerts failed: {str(e)}")
        return jsonify({'error': str(e)}), 400


# ==================== STATUS ENDPOINTS ====================

@monitoring_bp.route('/status/logs', methods=['GET'])
@require_workspace
def get_logs_status(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get logger service status
    
    Returns: {status: str, capabilities: [...], timestamp: str}
    """
    if not logger_service:
        return jsonify({'status': 'unavailable'}), 503
    
    return jsonify({
        'status': 'healthy',
        'service': 'EnterpriseLoggerService',
        'capabilities': [
            'structured_logging',
            'multiple_sinks',
            'log_retention',
            'search_and_filter',
            'aggregation'
        ],
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@monitoring_bp.route('/status/tracing', methods=['GET'])
@require_workspace
def get_tracing_status(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get tracing service status
    
    Returns: {status: str, capabilities: [...], timestamp: str}
    """
    if not tracer_service:
        return jsonify({'status': 'unavailable'}), 503
    
    return jsonify({
        'status': 'healthy',
        'service': 'DistributedTracingService',
        'capabilities': [
            'distributed_tracing',
            'critical_path_analysis',
            'service_dependency_mapping',
            'configurable_sampling',
            'span_linking'
        ],
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@monitoring_bp.route('/status/metrics', methods=['GET'])
@require_workspace
def get_metrics_status(workspace_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get metrics service status
    
    Returns: {status: str, capabilities: [...], timestamp: str}
    """
    if not metrics_service:
        return jsonify({'status': 'unavailable'}), 503
    
    return jsonify({
        'status': 'healthy',
        'service': 'ComprehensiveMetricsService',
        'capabilities': [
            'multi_type_metrics',
            'time_series_aggregation',
            'alert_conditions',
            'baseline_comparison',
            'cardinality_management'
        ],
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@monitoring_bp.route('/health', methods=['GET'])
def health_check() -> Tuple[Dict[str, Any], int]:
    """
    Health check for monitoring system
    
    Returns: {status: str, services: {...}, timestamp: str}
    """
    return jsonify({
        'status': 'healthy',
        'services': {
            'logging': logger_service is not None,
            'tracing': tracer_service is not None,
            'metrics': metrics_service is not None
        },
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200
