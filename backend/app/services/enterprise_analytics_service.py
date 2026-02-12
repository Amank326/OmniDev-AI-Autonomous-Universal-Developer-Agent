"""
Phase 49: Enterprise Analytics & Business Intelligence Services

This module provides comprehensive enterprise analytics and business intelligence capabilities:
- Advanced data analytics and reporting
- Custom metrics and KPI tracking  
- Business dashboards and visualizations
- ROI analysis and cost optimization
- Predictive analytics and forecasting
"""

import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


# ============================================================================
# 1. BUSINESS METRICS & KPI SERVICE
# ============================================================================

class MetricType(Enum):
    """Types of business metrics"""
    REVENUE = "revenue"
    COST = "cost"
    EFFICIENCY = "efficiency"
    CONVERSION = "conversion"
    RETENTION = "retention"
    GROWTH = "growth"
    ENGAGEMENT = "engagement"
    SATISFACTION = "satisfaction"


@dataclass
class KPIDefinition:
    """Key Performance Indicator definition"""
    name: str
    metric_type: MetricType
    formula: str
    target: float
    threshold_warning: float
    threshold_critical: float
    refresh_interval: int  # minutes
    owner: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KPIValue:
    """Current KPI value and status"""
    kpi_name: str
    current_value: float
    target_value: float
    variance: float
    status: str  # "healthy", "warning", "critical"
    trend: str  # "up", "down", "stable"
    last_updated: datetime = field(default_factory=datetime.utcnow)


class BusinessMetricsService:
    """Comprehensive business metrics and KPI tracking"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.kpis: Dict[str, KPIDefinition] = {}
        self.kpi_values: Dict[str, List[KPIValue]] = defaultdict(list)
        self.status = "initializing"
        
    def define_kpi(self, kpi: KPIDefinition) -> bool:
        """Define a new KPI"""
        with self._lock:
            try:
                self.kpis[kpi.name] = kpi
                self.kpi_values[kpi.name] = []
                logger.info(f"KPI defined: {kpi.name}")
                return True
            except Exception as e:
                logger.error(f"KPI definition error: {e}")
                return False
    
    def record_kpi_value(self, kpi_name: str, value: float) -> bool:
        """Record a KPI value"""
        with self._lock:
            try:
                if kpi_name not in self.kpis:
                    logger.warning(f"KPI not found: {kpi_name}")
                    return False
                
                kpi_def = self.kpis[kpi_name]
                variance = ((value - kpi_def.target) / kpi_def.target * 100) if kpi_def.target != 0 else 0
                
                if value >= kpi_def.threshold_critical:
                    status = "critical"
                elif value >= kpi_def.threshold_warning:
                    status = "warning"
                else:
                    status = "healthy"
                
                # Determine trend
                history = self.kpi_values[kpi_name]
                trend = "stable"
                if history:
                    last_value = history[-1].current_value
                    if value > last_value * 1.05:
                        trend = "up"
                    elif value < last_value * 0.95:
                        trend = "down"
                
                kpi_value = KPIValue(
                    kpi_name=kpi_name,
                    current_value=value,
                    target_value=kpi_def.target,
                    variance=variance,
                    status=status,
                    trend=trend
                )
                
                history.append(kpi_value)
                # Keep last 1000 records
                if len(history) > 1000:
                    history.pop(0)
                
                return True
            except Exception as e:
                logger.error(f"KPI value error: {e}")
                return False
    
    def get_kpi_status(self, kpi_name: str) -> Optional[KPIValue]:
        """Get current KPI status"""
        with self._lock:
            if kpi_name in self.kpi_values and self.kpi_values[kpi_name]:
                return self.kpi_values[kpi_name][-1]
            return None
    
    def get_all_kpis(self) -> Dict[str, KPIValue]:
        """Get all current KPI values"""
        with self._lock:
            return {name: values[-1] for name, values in self.kpi_values.items() if values}
    
    def get_kpi_history(self, kpi_name: str, hours: int = 24) -> List[KPIValue]:
        """Get KPI history for specified period"""
        with self._lock:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            return [v for v in self.kpi_values.get(kpi_name, []) if v.last_updated >= cutoff]


# ============================================================================
# 2. BUSINESS DASHBOARD SERVICE
# ============================================================================

@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    widget_id: str
    title: str
    widget_type: str  # "metric", "chart", "gauge", "table", "heatmap"
    data_source: str
    refresh_interval: int
    width: int  # grid columns
    height: int  # grid rows
    configuration: Dict[str, Any] = field(default_factory=dict)


class BusinessDashboardService:
    """Enterprise business dashboard management"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.dashboards: Dict[str, Dict] = {}
        self.status = "displaying"
        
    def create_dashboard(self, dashboard_name: str, description: str) -> bool:
        """Create a new business dashboard"""
        with self._lock:
            try:
                self.dashboards[dashboard_name] = {
                    "name": dashboard_name,
                    "description": description,
                    "widgets": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                logger.info(f"Dashboard created: {dashboard_name}")
                return True
            except Exception as e:
                logger.error(f"Dashboard creation error: {e}")
                return False
    
    def add_widget(self, dashboard_name: str, widget: DashboardWidget) -> bool:
        """Add widget to dashboard"""
        with self._lock:
            try:
                if dashboard_name not in self.dashboards:
                    return False
                
                self.dashboards[dashboard_name]["widgets"].append({
                    "id": widget.widget_id,
                    "title": widget.title,
                    "type": widget.widget_type,
                    "source": widget.data_source,
                    "refresh": widget.refresh_interval,
                    "size": {"width": widget.width, "height": widget.height}
                })
                self.dashboards[dashboard_name]["updated_at"] = datetime.utcnow()
                return True
            except Exception as e:
                logger.error(f"Widget add error: {e}")
                return False
    
    def get_dashboard(self, dashboard_name: str) -> Optional[Dict]:
        """Retrieve dashboard configuration"""
        with self._lock:
            return self.dashboards.get(dashboard_name)
    
    def get_all_dashboards(self) -> List[Dict]:
        """Get all dashboards"""
        with self._lock:
            return list(self.dashboards.values())


# ============================================================================
# 3. ROI & COST ANALYSIS SERVICE
# ============================================================================

@dataclass
class CostAnalysis:
    """Cost analysis results"""
    category: str
    total_cost: float
    cost_per_unit: float
    trend: str  # "increasing", "decreasing", "stable"
    opportunities: List[str] = field(default_factory=list)
    projected_savings: float = 0.0


class ROIAnalysisService:
    """ROI calculation and cost optimization analysis"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.cost_data: Dict[str, List[Dict]] = defaultdict(list)
        self.roi_metrics: Dict[str, Dict] = {}
        self.status = "analyzing"
        
    def record_cost(self, category: str, amount: float, description: str) -> bool:
        """Record cost data"""
        with self._lock:
            try:
                self.cost_data[category].append({
                    "amount": amount,
                    "description": description,
                    "timestamp": datetime.utcnow()
                })
                # Keep last 10000 records
                if len(self.cost_data[category]) > 10000:
                    self.cost_data[category].pop(0)
                return True
            except Exception as e:
                logger.error(f"Cost recording error: {e}")
                return False
    
    def calculate_roi(self, investment: float, returns: float, period_days: int) -> Dict:
        """Calculate ROI metrics"""
        try:
            roi_percent = ((returns - investment) / investment * 100) if investment != 0 else 0
            annualized_roi = (roi_percent * 365) / period_days if period_days > 0 else 0
            payback_period = (investment / (returns / period_days)) if returns > 0 else float('inf')
            
            return {
                "investment": investment,
                "returns": returns,
                "roi_percent": roi_percent,
                "annualized_roi": annualized_roi,
                "payback_period_days": payback_period,
                "calculated_at": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"ROI calculation error: {e}")
            return {}
    
    def analyze_costs(self, category: str, days: int = 30) -> Optional[CostAnalysis]:
        """Analyze costs in a category"""
        with self._lock:
            try:
                cutoff = datetime.utcnow() - timedelta(days=days)
                costs = [c for c in self.cost_data[category] if c["timestamp"] >= cutoff]
                
                if not costs:
                    return None
                
                total = sum(c["amount"] for c in costs)
                per_unit = total / len(costs) if costs else 0
                
                # Calculate trend
                if len(costs) > 1:
                    first_half = sum(c["amount"] for i, c in enumerate(costs) if i < len(costs)//2)
                    second_half = sum(c["amount"] for i, c in enumerate(costs) if i >= len(costs)//2)
                    if second_half > first_half * 1.1:
                        trend = "increasing"
                    elif second_half < first_half * 0.9:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                else:
                    trend = "stable"
                
                return CostAnalysis(
                    category=category,
                    total_cost=total,
                    cost_per_unit=per_unit,
                    trend=trend,
                    opportunities=["Review vendor contracts", "Optimize resource allocation"]
                )
            except Exception as e:
                logger.error(f"Cost analysis error: {e}")
                return None


# ============================================================================
# 4. PREDICTIVE ANALYTICS SERVICE
# ============================================================================

class PredictiveAnalyticsService:
    """Predictive analytics and forecasting"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.historical_data: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self.forecasts: Dict[str, List[Dict]] = {}
        self.status = "forecasting"
        
    def add_data_point(self, metric_name: str, value: float) -> bool:
        """Add data point for forecasting"""
        with self._lock:
            try:
                self.historical_data[metric_name].append((datetime.utcnow(), value))
                # Keep last 5000 points
                if len(self.historical_data[metric_name]) > 5000:
                    self.historical_data[metric_name].pop(0)
                return True
            except Exception as e:
                logger.error(f"Data point error: {e}")
                return False
    
    def forecast_simple(self, metric_name: str, periods: int = 7) -> List[Dict]:
        """Simple moving average forecast"""
        with self._lock:
            try:
                data = self.historical_data.get(metric_name, [])
                if len(data) < 2:
                    return []
                
                # Calculate moving average
                values = [v for _, v in data[-min(30, len(data)):]]
                avg = sum(values) / len(values)
                
                forecasts = []
                for i in range(1, periods + 1):
                    forecasts.append({
                        "period": i,
                        "forecast": avg,
                        "confidence": 0.75
                    })
                
                return forecasts
            except Exception as e:
                logger.error(f"Forecast error: {e}")
                return []
    
    def detect_trend(self, metric_name: str, window: int = 7) -> str:
        """Detect trend in metric"""
        with self._lock:
            try:
                data = self.historical_data.get(metric_name, [])
                if len(data) < window:
                    return "insufficient_data"
                
                values = [v for _, v in data[-window:]]
                if len(values) < 2:
                    return "stable"
                
                increase = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
                decrease = len(values) - 1 - increase
                
                if increase > decrease * 1.5:
                    return "uptrend"
                elif decrease > increase * 1.5:
                    return "downtrend"
                else:
                    return "stable"
            except Exception as e:
                logger.error(f"Trend detection error: {e}")
                return "error"


# ============================================================================
# 5. BUSINESS INTELLIGENCE SERVICE
# ============================================================================

@dataclass
class BIInsight:
    """Business intelligence insight"""
    title: str
    description: str
    impact: str  # "high", "medium", "low"
    recommendation: str
    metric_source: str
    generated_at: datetime = field(default_factory=datetime.utcnow)


class BusinessIntelligenceService:
    """Advanced business intelligence and insights"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self.insights: List[BIInsight] = []
        self.reports: Dict[str, Dict] = {}
        self.status = "analyzing"
        
    def generate_insight(self, title: str, description: str, 
                        impact: str, recommendation: str, 
                        metric_source: str) -> bool:
        """Generate a business insight"""
        with self._lock:
            try:
                insight = BIInsight(
                    title=title,
                    description=description,
                    impact=impact,
                    recommendation=recommendation,
                    metric_source=metric_source
                )
                self.insights.append(insight)
                # Keep last 1000 insights
                if len(self.insights) > 1000:
                    self.insights.pop(0)
                logger.info(f"Insight generated: {title}")
                return True
            except Exception as e:
                logger.error(f"Insight generation error: {e}")
                return False
    
    def get_high_impact_insights(self, limit: int = 10) -> List[BIInsight]:
        """Get high-impact insights"""
        with self._lock:
            return [i for i in self.insights if i.impact == "high"][:limit]
    
    def generate_executive_summary(self) -> Dict:
        """Generate executive summary"""
        with self._lock:
            try:
                high_impact = len([i for i in self.insights if i.impact == "high"])
                medium_impact = len([i for i in self.insights if i.impact == "medium"])
                low_impact = len([i for i in self.insights if i.impact == "low"])
                
                return {
                    "total_insights": len(self.insights),
                    "high_impact_insights": high_impact,
                    "medium_impact_insights": medium_impact,
                    "low_impact_insights": low_impact,
                    "top_insights": [vars(i) for i in self.get_high_impact_insights(5)],
                    "generated_at": datetime.utcnow()
                }
            except Exception as e:
                logger.error(f"Summary error: {e}")
                return {}
    
    def generate_report(self, report_name: str, report_type: str) -> bool:
        """Generate comprehensive report"""
        with self._lock:
            try:
                self.reports[report_name] = {
                    "name": report_name,
                    "type": report_type,
                    "summary": self.generate_executive_summary(),
                    "generated_at": datetime.utcnow()
                }
                logger.info(f"Report generated: {report_name}")
                return True
            except Exception as e:
                logger.error(f"Report generation error: {e}")
                return False


# ============================================================================
# PHASE 49 ORCHESTRATOR
# ============================================================================

class Phase49Service:
    """Phase 49: Enterprise Analytics & Business Intelligence Orchestrator"""
    
    def __init__(self):
        self.business_metrics = BusinessMetricsService()
        self.dashboard = BusinessDashboardService()
        self.roi_analysis = ROIAnalysisService()
        self.predictive_analytics = PredictiveAnalyticsService()
        self.business_intelligence = BusinessIntelligenceService()
        self.status = "operational"
        
    def initialize(self) -> bool:
        """Initialize Phase 49 services"""
        try:
            logger.info("Phase 49: Enterprise Analytics Services initialized")
            return True
        except Exception as e:
            logger.error(f"Phase 49 initialization error: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get Phase 49 status"""
        return {
            "phase": 49,
            "status": self.status,
            "services": {
                "business_metrics": self.business_metrics.status,
                "dashboards": self.dashboard.status,
                "roi_analysis": self.roi_analysis.status,
                "predictive_analytics": self.predictive_analytics.status,
                "business_intelligence": self.business_intelligence.status
            },
            "metrics": {
                "kpis_defined": len(self.business_metrics.kpis),
                "dashboards_created": len(self.dashboard.dashboards),
                "insights_generated": len(self.business_intelligence.insights),
                "reports_generated": len(self.business_intelligence.reports)
            }
        }


# Global singleton
_phase49_instance: Optional[Phase49Service] = None
_phase49_lock = threading.RLock()


def get_phase49_service() -> Phase49Service:
    """Get Phase 49 service instance (singleton)"""
    global _phase49_instance
    if _phase49_instance is None:
        with _phase49_lock:
            if _phase49_instance is None:
                _phase49_instance = Phase49Service()
                _phase49_instance.initialize()
    return _phase49_instance
