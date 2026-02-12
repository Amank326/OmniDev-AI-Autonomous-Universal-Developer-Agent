"""
Phase 48: Advanced Monitoring & Analytics Routes
API endpoints for system monitoring, analytics, and dashboards
"""

from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from app.services.advanced_monitoring_service import (
    advanced_monitoring, performance_analytics, real_time_dashboard,
    alert_management, analytics_reporting, MetricType, AlertSeverity, DashboardType
)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

# ==================== REQUEST/RESPONSE MODELS ====================

class MetricRequest(BaseModel):
    name: str
    value: float
    metric_type: str
    tags: Optional[Dict] = None
    unit: Optional[str] = None

class AlertRequest(BaseModel):
    alert_id: str
    name: str
    condition: str
    severity: str
    threshold: float
    duration: Optional[int] = 300

class DashboardRequest(BaseModel):
    dashboard_id: str
    title: str
    dashboard_type: str
    widgets: List[Dict]

class ReportRequest(BaseModel):
    report_type: str
    time_period: str
    metrics: List[str]

# ==================== METRICS ENDPOINTS ====================

@router.post("/metrics/record")
async def record_metric(metric: MetricRequest):
    """Record a system metric"""
    try:
        metric_type = MetricType[metric.metric_type.upper()]
        metric_id = advanced_monitoring.record_metric(
            name=metric.name,
            value=metric.value,
            metric_type=metric_type,
            tags=metric.tags,
            unit=metric.unit or ""
        )
        return {
            "success": True,
            "metric_id": metric_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/statistics/{metric_name}")
async def get_metric_statistics(metric_name: str, window_seconds: int = 3600):
    """Get metric statistics"""
    stats = advanced_monitoring.get_metric_statistics(metric_name, window_seconds)
    return stats

@router.get("/metrics/all")
async def list_all_metrics():
    """List all tracked metrics"""
    return {
        "metrics": list(advanced_monitoring.metrics.keys()),
        "count": len(advanced_monitoring.metrics),
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== PERFORMANCE ANALYSIS ====================

@router.post("/performance/analyze-latency")
async def analyze_latency(endpoint: str = Query(...), latencies: List[float] = Query(...)):
    """Analyze endpoint latency"""
    analysis = performance_analytics.analyze_latency(endpoint, latencies)
    return analysis

@router.post("/performance/detect-anomalies")
async def detect_anomalies(metric_name: str = Query(...), values: List[float] = Query(...)):
    """Detect anomalies in metric data"""
    anomalies = performance_analytics.detect_anomalies(metric_name, values)
    return {
        "metric": metric_name,
        "anomalies": anomalies,
        "count": len(anomalies),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/performance/suggestions")
async def get_improvement_suggestions(metric_p95_latency: Optional[float] = None):
    """Get performance improvement suggestions"""
    metrics = {"p95_latency": metric_p95_latency} if metric_p95_latency else {}
    suggestions = performance_analytics.calculate_improvement_suggestions(metrics)
    return {
        "suggestions": suggestions,
        "count": len(suggestions),
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== DASHBOARD ENDPOINTS ====================

@router.post("/dashboards/create")
async def create_dashboard(dashboard: DashboardRequest):
    """Create a new dashboard"""
    try:
        dashboard_type = DashboardType[dashboard.dashboard_type.upper()]
        dashboard_id = real_time_dashboard.create_dashboard(
            dashboard_id=dashboard.dashboard_id,
            dashboard_type=dashboard_type,
            title=dashboard.title,
            widgets=dashboard.widgets
        )
        return {
            "success": True,
            "dashboard_id": dashboard_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: str):
    """Get dashboard with current data"""
    dashboard = real_time_dashboard.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard

@router.post("/dashboards/{dashboard_id}/widget/{widget_id}")
async def update_widget(dashboard_id: str, widget_id: str, data: Dict):
    """Update widget data"""
    success = real_time_dashboard.update_widget_data(widget_id, data)
    return {
        "success": success,
        "widget_id": widget_id,
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== ALERT ENDPOINTS ====================

@router.post("/alerts/create")
async def create_alert(alert: AlertRequest):
    """Create alert rule"""
    try:
        severity = AlertSeverity[alert.severity.upper()]
        alert_id = alert_management.create_alert(
            alert_id=alert.alert_id,
            name=alert.name,
            condition=alert.condition,
            severity=severity,
            threshold=alert.threshold,
            duration=alert.duration
        )
        return {
            "success": True,
            "alert_id": alert_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/trigger")
async def trigger_alert(alert_id: str, value: float, context: Optional[Dict] = None):
    """Trigger an alert"""
    event_id = alert_management.trigger_alert(alert_id, value, context or {})
    if not event_id:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "success": True,
        "event_id": event_id,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/alerts/history")
async def get_alert_history(alert_id: Optional[str] = None, 
                           severity: Optional[str] = None,
                           limit: int = 100):
    """Get alert history"""
    alert_severity = None
    if severity:
        try:
            alert_severity = AlertSeverity[severity.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid severity")
    
    history = alert_management.get_alert_history(alert_id, alert_severity, limit)
    return {
        "alerts": history,
        "count": len(history),
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== REPORTING ENDPOINTS ====================

@router.post("/reports/generate")
async def generate_report(report: ReportRequest):
    """Generate analytics report"""
    report_id = analytics_reporting.generate_report(
        report_type=report.report_type,
        time_period=report.time_period,
        metrics_to_include=report.metrics
    )
    return {
        "success": True,
        "report_id": report_id,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get generated report"""
    report = analytics_reporting.reports.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get("/insights")
async def get_business_insights():
    """Get key business and performance insights"""
    insights = analytics_reporting.get_business_insights()
    return {
        "insights": insights,
        "count": len(insights),
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== HEALTH & STATUS ====================

@router.get("/health")
async def monitoring_health():
    """Health check for monitoring service"""
    return {
        "service": "monitoring",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/status")
async def monitoring_status():
    """Get monitoring service status"""
    return {
        "service": "advanced_monitoring",
        "status": "operational",
        "components": {
            "metrics": advanced_monitoring.get_statistics(),
            "performance": performance_analytics.get_statistics(),
            "dashboards": real_time_dashboard.get_statistics(),
            "alerts": alert_management.get_statistics(),
            "reporting": analytics_reporting.get_statistics(),
        },
        "timestamp": datetime.utcnow().isoformat()
    }
