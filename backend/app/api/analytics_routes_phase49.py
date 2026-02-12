"""
Phase 49: Enterprise Analytics & Business Intelligence API Routes

Provides REST API endpoints for:
- Business metrics and KPI tracking
- Business dashboards management
- ROI and cost analysis
- Predictive analytics and forecasting
- Business intelligence and insights
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from ..services.enterprise_analytics_service import (
    get_phase49_service,
    KPIDefinition,
    MetricType,
    DashboardWidget
)

router = APIRouter(prefix="/api/v1/analytics", tags=["enterprise-analytics"])
phase49_service = get_phase49_service()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class KPIDefinitionRequest(BaseModel):
    """KPI definition request"""
    name: str
    metric_type: str
    formula: str
    target: float
    threshold_warning: float
    threshold_critical: float
    refresh_interval: int
    owner: str


class KPIValueRequest(BaseModel):
    """KPI value recording request"""
    kpi_name: str
    value: float


class DashboardRequest(BaseModel):
    """Dashboard creation request"""
    name: str
    description: str


class DashboardWidgetRequest(BaseModel):
    """Widget addition request"""
    dashboard_name: str
    widget_id: str
    title: str
    widget_type: str
    data_source: str
    refresh_interval: int
    width: int
    height: int


class CostRecordRequest(BaseModel):
    """Cost record request"""
    category: str
    amount: float
    description: str


class ROICalculationRequest(BaseModel):
    """ROI calculation request"""
    investment: float
    returns: float
    period_days: int


class DataPointRequest(BaseModel):
    """Data point for forecasting"""
    metric_name: str
    value: float


class InsightRequest(BaseModel):
    """Insight generation request"""
    title: str
    description: str
    impact: str
    recommendation: str
    metric_source: str


class ReportRequest(BaseModel):
    """Report generation request"""
    report_name: str
    report_type: str


# ============================================================================
# BUSINESS METRICS & KPI ENDPOINTS
# ============================================================================

@router.post("/kpi/define")
async def define_kpi(request: KPIDefinitionRequest) -> Dict[str, Any]:
    """Define a new KPI"""
    try:
        metric_type = MetricType[request.metric_type.upper()]
        kpi_def = KPIDefinition(
            name=request.name,
            metric_type=metric_type,
            formula=request.formula,
            target=request.target,
            threshold_warning=request.threshold_warning,
            threshold_critical=request.threshold_critical,
            refresh_interval=request.refresh_interval,
            owner=request.owner
        )
        
        success = phase49_service.business_metrics.define_kpi(kpi_def)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to define KPI")
        
        return {
            "status": "success",
            "kpi_name": request.name,
            "message": "KPI defined successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kpi/record")
async def record_kpi_value(request: KPIValueRequest) -> Dict[str, Any]:
    """Record a KPI value"""
    try:
        success = phase49_service.business_metrics.record_kpi_value(
            request.kpi_name,
            request.value
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to record KPI value")
        
        return {
            "status": "success",
            "kpi_name": request.kpi_name,
            "value": request.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpi/{kpi_name}/status")
async def get_kpi_status(kpi_name: str) -> Dict[str, Any]:
    """Get current KPI status"""
    try:
        kpi_value = phase49_service.business_metrics.get_kpi_status(kpi_name)
        if not kpi_value:
            raise HTTPException(status_code=404, detail="KPI not found")
        
        return {
            "kpi_name": kpi_value.kpi_name,
            "current_value": kpi_value.current_value,
            "target_value": kpi_value.target_value,
            "variance": kpi_value.variance,
            "status": kpi_value.status,
            "trend": kpi_value.trend,
            "last_updated": kpi_value.last_updated.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpi/all")
async def get_all_kpis() -> Dict[str, Any]:
    """Get all KPIs"""
    try:
        kpis = phase49_service.business_metrics.get_all_kpis()
        return {
            "total": len(kpis),
            "kpis": {name: {
                "current_value": v.current_value,
                "target_value": v.target_value,
                "status": v.status,
                "trend": v.trend
            } for name, v in kpis.items()}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpi/{kpi_name}/history")
async def get_kpi_history(kpi_name: str, hours: int = 24) -> Dict[str, Any]:
    """Get KPI history"""
    try:
        history = phase49_service.business_metrics.get_kpi_history(kpi_name, hours)
        return {
            "kpi_name": kpi_name,
            "period_hours": hours,
            "data_points": len(history),
            "history": [{
                "value": h.current_value,
                "timestamp": h.last_updated.isoformat()
            } for h in history]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BUSINESS DASHBOARD ENDPOINTS
# ============================================================================

@router.post("/dashboards/create")
async def create_dashboard(request: DashboardRequest) -> Dict[str, Any]:
    """Create a business dashboard"""
    try:
        success = phase49_service.dashboard.create_dashboard(
            request.name,
            request.description
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create dashboard")
        
        return {
            "status": "success",
            "dashboard_name": request.name,
            "message": "Dashboard created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboards/widget/add")
async def add_dashboard_widget(request: DashboardWidgetRequest) -> Dict[str, Any]:
    """Add widget to dashboard"""
    try:
        widget = DashboardWidget(
            widget_id=request.widget_id,
            title=request.title,
            widget_type=request.widget_type,
            data_source=request.data_source,
            refresh_interval=request.refresh_interval,
            width=request.width,
            height=request.height
        )
        
        success = phase49_service.dashboard.add_widget(
            request.dashboard_name,
            widget
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add widget")
        
        return {
            "status": "success",
            "dashboard_name": request.dashboard_name,
            "widget_id": request.widget_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboards/{dashboard_name}")
async def get_dashboard(dashboard_name: str) -> Dict[str, Any]:
    """Get dashboard details"""
    try:
        dashboard = phase49_service.dashboard.get_dashboard(dashboard_name)
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")
        
        return {
            "name": dashboard["name"],
            "description": dashboard["description"],
            "widget_count": len(dashboard["widgets"]),
            "widgets": dashboard["widgets"],
            "created_at": dashboard["created_at"].isoformat(),
            "updated_at": dashboard["updated_at"].isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboards")
async def list_dashboards() -> Dict[str, Any]:
    """List all dashboards"""
    try:
        dashboards = phase49_service.dashboard.get_all_dashboards()
        return {
            "total": len(dashboards),
            "dashboards": [{
                "name": d["name"],
                "description": d["description"],
                "widget_count": len(d["widgets"])
            } for d in dashboards]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROI & COST ANALYSIS ENDPOINTS
# ============================================================================

@router.post("/costs/record")
async def record_cost(request: CostRecordRequest) -> Dict[str, Any]:
    """Record a cost"""
    try:
        success = phase49_service.roi_analysis.record_cost(
            request.category,
            request.amount,
            request.description
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to record cost")
        
        return {
            "status": "success",
            "category": request.category,
            "amount": request.amount
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roi/calculate")
async def calculate_roi(request: ROICalculationRequest) -> Dict[str, Any]:
    """Calculate ROI"""
    try:
        roi = phase49_service.roi_analysis.calculate_roi(
            request.investment,
            request.returns,
            request.period_days
        )
        
        if not roi:
            raise HTTPException(status_code=400, detail="Failed to calculate ROI")
        
        return {
            "investment": roi["investment"],
            "returns": roi["returns"],
            "roi_percent": roi["roi_percent"],
            "annualized_roi": roi["annualized_roi"],
            "payback_period_days": roi["payback_period_days"],
            "calculated_at": roi["calculated_at"].isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/analyze/{category}")
async def analyze_costs(category: str, days: int = 30) -> Dict[str, Any]:
    """Analyze costs in category"""
    try:
        analysis = phase49_service.roi_analysis.analyze_costs(category, days)
        if not analysis:
            raise HTTPException(status_code=404, detail="No cost data found")
        
        return {
            "category": analysis.category,
            "period_days": days,
            "total_cost": analysis.total_cost,
            "cost_per_unit": analysis.cost_per_unit,
            "trend": analysis.trend,
            "opportunities": analysis.opportunities,
            "projected_savings": analysis.projected_savings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PREDICTIVE ANALYTICS ENDPOINTS
# ============================================================================

@router.post("/forecast/data-point")
async def add_forecast_data(request: DataPointRequest) -> Dict[str, Any]:
    """Add data point for forecasting"""
    try:
        success = phase49_service.predictive_analytics.add_data_point(
            request.metric_name,
            request.value
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add data point")
        
        return {
            "status": "success",
            "metric_name": request.metric_name,
            "value": request.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forecast/{metric_name}")
async def forecast_metric(metric_name: str, periods: int = 7) -> Dict[str, Any]:
    """Generate forecast for metric"""
    try:
        forecast = phase49_service.predictive_analytics.forecast_simple(metric_name, periods)
        return {
            "metric_name": metric_name,
            "periods": periods,
            "forecast_points": len(forecast),
            "forecasts": forecast
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend/{metric_name}")
async def detect_trend(metric_name: str, window: int = 7) -> Dict[str, Any]:
    """Detect trend in metric"""
    try:
        trend = phase49_service.predictive_analytics.detect_trend(metric_name, window)
        return {
            "metric_name": metric_name,
            "window_size": window,
            "trend": trend
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BUSINESS INTELLIGENCE ENDPOINTS
# ============================================================================

@router.post("/insights/generate")
async def generate_insight(request: InsightRequest) -> Dict[str, Any]:
    """Generate a business insight"""
    try:
        success = phase49_service.business_intelligence.generate_insight(
            request.title,
            request.description,
            request.impact,
            request.recommendation,
            request.metric_source
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to generate insight")
        
        return {
            "status": "success",
            "insight_title": request.title,
            "message": "Insight generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/high-impact")
async def get_high_impact_insights(limit: int = 10) -> Dict[str, Any]:
    """Get high-impact insights"""
    try:
        insights = phase49_service.business_intelligence.get_high_impact_insights(limit)
        return {
            "total": len(insights),
            "insights": [{
                "title": i.title,
                "description": i.description,
                "impact": i.impact,
                "recommendation": i.recommendation,
                "metric_source": i.metric_source,
                "generated_at": i.generated_at.isoformat()
            } for i in insights]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/executive")
async def get_executive_summary() -> Dict[str, Any]:
    """Get executive summary"""
    try:
        summary = phase49_service.business_intelligence.generate_executive_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/generate")
async def generate_report(request: ReportRequest) -> Dict[str, Any]:
    """Generate comprehensive report"""
    try:
        success = phase49_service.business_intelligence.generate_report(
            request.report_name,
            request.report_type
        )
        if not success:
            raise HTTPException(status_code=400, detail="Failed to generate report")
        
        return {
            "status": "success",
            "report_name": request.report_name,
            "report_type": request.report_type,
            "message": "Report generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@router.get("/health")
async def analytics_health() -> Dict[str, Any]:
    """Analytics service health check"""
    return {
        "service": "enterprise-analytics",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/status")
async def analytics_status() -> Dict[str, Any]:
    """Get Phase 49 status"""
    return phase49_service.get_status()
