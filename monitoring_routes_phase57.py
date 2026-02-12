"""
Phase 57: Monitoring & Observability - API Routes
RESTful endpoints for health checks, metrics, tracing,
alerts, and system observability (18+ endpoints).
"""

from fastapi import APIRouter, HTTPException, Query, Header, BackgroundTasks
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

from monitoring_service_phase57 import (
    get_health_check_service, reset_health_check_service,
    get_metrics_collector, reset_metrics_collector,
    get_distributed_tracer, reset_distributed_tracer,
    get_alert_manager, reset_alert_manager,
    HealthStatus, MetricType, AlertSeverity, TraceLevel
)


# ===================== PYDANTIC MODELS =====================

class HealthCheckRequest(BaseModel):
    """Health check registration request."""
    service_name: str
    check_endpoint: Optional[str] = None


class MetricRecordRequest(BaseModel):
    """Metric recording request."""
    name: str
    value: float
    metric_type: str = "gauge"
    labels: Dict[str, str] = {}


class TraceStartRequest(BaseModel):
    """Start trace request."""
    trace_id: Optional[str] = None
    service: str


class TraceSpanRequest(BaseModel):
    """Add span to trace request."""
    trace_id: str
    operation: str
    service: str
    parent_span_id: Optional[str] = None
    tags: Dict[str, Any] = {}


class AlertCreateRequest(BaseModel):
    """Create alert request."""
    service: str
    severity: str
    message: str
    metric_name: str
    threshold: float
    current_value: float
    metadata: Dict[str, Any] = {}


# ===================== ROUTER =====================

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


# ===================== HEALTH CHECK ENDPOINTS =====================

@router.get("/health")
async def system_health() -> Dict[str, Any]:
    """Get overall system health status."""
    try:
        service = get_health_check_service()
        overall = service.get_overall_status()
        
        return {
            'status': overall.value,
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                name: result.to_dict() 
                for name, result in [(svc, service.get_service_status(svc)) 
                                   for svc in service.checks.keys()]
                if result
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{service_name}")
async def service_health(service_name: str) -> Dict[str, Any]:
    """Get specific service health status."""
    try:
        service = get_health_check_service()
        result = service.get_service_status(service_name)
        
        if not result:
            raise HTTPException(status_code=404, detail="Service not found")
        
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/check/{service_name}")
async def run_health_check(service_name: str) -> Dict[str, Any]:
    """Run health check for specific service."""
    try:
        service = get_health_check_service()
        result = service.run_check(service_name)
        
        if not result:
            raise HTTPException(status_code=404, detail="Health check not registered")
        
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/check-all")
async def run_all_health_checks() -> Dict[str, Any]:
    """Run all health checks."""
    try:
        service = get_health_check_service()
        results = service.run_all_checks()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'checks': len(results),
            'results': {name: result.to_dict() for name, result in results.items()}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================== METRICS ENDPOINTS =====================

@router.post("/metrics")
async def record_metric(request: MetricRecordRequest) -> Dict[str, str]:
    """Record a metric."""
    try:
        collector = get_metrics_collector()
        
        try:
            metric_type = MetricType(request.metric_type)
        except ValueError:
            metric_type = MetricType.GAUGE
        
        success = collector.record_metric(
            name=request.name,
            value=request.value,
            metric_type=metric_type,
            labels=request.labels
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to record metric")
        
        return {'success': True, 'metric': request.name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{metric_name}")
async def get_metric_summary(metric_name: str) -> Dict[str, Any]:
    """Get metric summary statistics."""
    try:
        collector = get_metrics_collector()
        summary = collector.get_metric_summary(metric_name)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Metric not found")
        
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_all_metrics(limit: int = Query(100, ge=1, le=1000)) -> Dict[str, Any]:
    """Get all metrics."""
    try:
        collector = get_metrics_collector()
        metrics = collector.get_all_metrics()
        
        return {
            'total': len(metrics),
            'metrics': metrics[-limit:] if len(metrics) > limit else metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/counter")
async def record_counter(name: str, increment: float = 1.0,
                        labels: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Record counter metric."""
    try:
        collector = get_metrics_collector()
        collector.record_counter(name, increment, labels or {})
        
        return {'success': True, 'type': 'counter', 'name': name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/gauge")
async def record_gauge(name: str, value: float,
                      labels: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Record gauge metric."""
    try:
        collector = get_metrics_collector()
        collector.record_gauge(name, value, labels or {})
        
        return {'success': True, 'type': 'gauge', 'name': name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/timer")
async def record_timer(name: str, duration_ms: float,
                      labels: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Record timer metric."""
    try:
        collector = get_metrics_collector()
        collector.record_timer(name, duration_ms, labels or {})
        
        return {'success': True, 'type': 'timer', 'name': name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================== DISTRIBUTED TRACING ENDPOINTS =====================

@router.post("/traces")
async def start_trace(request: TraceStartRequest) -> Dict[str, str]:
    """Start new distributed trace."""
    try:
        tracer = get_distributed_tracer()
        trace_id = tracer.start_trace(request.trace_id)
        
        return {
            'trace_id': trace_id,
            'service': request.service,
            'started_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/traces/{trace_id}/spans")
async def add_trace_span(trace_id: str, request: TraceSpanRequest) -> Dict[str, str]:
    """Add span to trace."""
    try:
        tracer = get_distributed_tracer()
        span_id = tracer.add_span(
            trace_id=trace_id,
            operation=request.operation,
            service=request.service,
            parent_span_id=request.parent_span_id,
            tags=request.tags
        )
        
        return {
            'trace_id': trace_id,
            'span_id': span_id,
            'operation': request.operation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/traces/{trace_id}/spans/{span_id}/end")
async def end_trace_span(trace_id: str, span_id: str,
                        status: str = "success") -> Dict[str, str]:
    """End trace span."""
    try:
        tracer = get_distributed_tracer()
        success = tracer.end_span(trace_id, span_id, status)
        
        if not success:
            raise HTTPException(status_code=404, detail="Span not found")
        
        return {'trace_id': trace_id, 'span_id': span_id, 'status': status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str) -> Dict[str, Any]:
    """Get complete trace."""
    try:
        tracer = get_distributed_tracer()
        spans = tracer.get_trace(trace_id)
        
        if not spans:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        return {
            'trace_id': trace_id,
            'span_count': len(spans),
            'spans': [span.to_dict() for span in spans]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================== ALERT ENDPOINTS =====================

@router.post("/alerts")
async def create_alert(request: AlertCreateRequest) -> Dict[str, Any]:
    """Create new alert."""
    try:
        manager = get_alert_manager()
        
        try:
            severity = AlertSeverity(request.severity)
        except ValueError:
            severity = AlertSeverity.WARNING
        
        alert = manager.create_alert(
            service=request.service,
            severity=severity,
            message=request.message,
            metric_name=request.metric_name,
            threshold=request.threshold,
            current_value=request.current_value,
            metadata=request.metadata
        )
        
        return alert.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_active_alerts(severity: Optional[str] = None) -> Dict[str, Any]:
    """Get active alerts."""
    try:
        manager = get_alert_manager()
        
        severity_filter = None
        if severity:
            try:
                severity_filter = AlertSeverity(severity)
            except ValueError:
                pass
        
        alerts = manager.get_active_alerts(severity_filter)
        
        return {
            'total': len(alerts),
            'alerts': [alert.to_dict() for alert in alerts]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str) -> Dict[str, str]:
    """Resolve alert."""
    try:
        manager = get_alert_manager()
        success = manager.resolve_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {'success': True, 'alert_id': alert_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/history")
async def get_alert_history(limit: int = Query(100, ge=1, le=1000)) -> Dict[str, Any]:
    """Get alert history."""
    try:
        manager = get_alert_manager()
        history = manager.get_alert_history(limit)
        
        return {
            'total': len(history),
            'alerts': [alert.to_dict() for alert in history]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================== STATISTICS & DASHBOARD =====================

@router.get("/statistics")
async def get_monitoring_statistics() -> Dict[str, Any]:
    """Get monitoring system statistics."""
    try:
        return {
            'health_checks': get_health_check_service().get_statistics(),
            'metrics': get_metrics_collector().get_statistics(),
            'traces': get_distributed_tracer().get_statistics(),
            'alerts': get_alert_manager().get_statistics(),
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard() -> Dict[str, Any]:
    """Get monitoring dashboard data."""
    try:
        health_service = get_health_check_service()
        metrics_collector = get_metrics_collector()
        alert_manager = get_alert_manager()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'system_health': {
                'status': health_service.get_overall_status().value,
                'services': list(health_service.checks.keys())
            },
            'metrics_summary': {
                'total_metrics': len(metrics_collector.metrics),
                'total_data_points': sum(len(v) for v in metrics_collector.metrics.values())
            },
            'alerts_summary': {
                'active': len(alert_manager.alerts),
                'critical': len([a for a in alert_manager.alerts.values() 
                               if a.severity == AlertSeverity.CRITICAL]),
                'warning': len([a for a in alert_manager.alerts.values() 
                              if a.severity == AlertSeverity.WARNING])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================== SYSTEM ENDPOINTS =====================

@router.get("/monitoring/health")
async def monitoring_service_health() -> Dict[str, str]:
    """Check monitoring service health."""
    return {
        'status': 'operational',
        'health_checks': 'operational',
        'metrics': 'operational',
        'tracing': 'operational',
        'alerts': 'operational',
        'endpoints': '18+'
    }


@router.post("/test/reset")
async def reset_monitoring_services() -> Dict[str, str]:
    """Reset all monitoring services (for testing)."""
    reset_health_check_service()
    reset_metrics_collector()
    reset_distributed_tracer()
    reset_alert_manager()
    
    return {'success': True, 'message': 'All monitoring services reset'}
