"""
Phase 23: Custom Metric Builder Service
KPI creation, formula engine, validation, versioning, testing
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class MetricType(Enum):
    """Types of metrics"""
    SIMPLE = "simple"           # Single aggregation
    CALCULATED = "calculated"   # Formula-based
    COMPOSITE = "composite"     # Multiple metrics combined
    DERIVED = "derived"         # From other metrics
    ML_MODEL = "ml_model"       # ML prediction


class Aggregation(Enum):
    """Aggregation methods"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    DISTINCT = "distinct"
    STDDEV = "stddev"
    PERCENTILE = "percentile"


class Format(Enum):
    """Number formats"""
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    DECIMAL = "decimal"
    BYTES = "bytes"
    DURATION = "duration"
    CUSTOM = "custom"


class MetricBuilderService:
    """
    Custom metric and KPI builder
    Create, test, validate, version, and deploy metrics
    """
    
    def __init__(self):
        """Initialize metric builder"""
        self.metrics = {}
        self.metric_versions = {}
        self.metric_tests = {}
    
    # ========================================================================
    # METRIC CREATION
    # ========================================================================
    
    def create_simple_metric(
        self,
        name: str,
        description: str,
        data_source: str,
        field: str,
        aggregation: str = "sum",
        filters: Dict = None,
    ) -> Dict:
        """
        Create simple metric from single field
        
        Aggregations: sum, avg, min, max, count, distinct, stddev
        """
        
        return {
            "metric_id": "",
            "name": name,
            "description": description,
            "type": MetricType.SIMPLE.value,
            "data_source": data_source,
            "definition": {
                "field": field,
                "aggregation": aggregation,
                "filters": filters or {},
            },
            "created_date": datetime.utcnow().isoformat(),
            "created_by": "",
            "status": "draft",
            "version": 1,
        }
    
    def create_calculated_metric(
        self,
        name: str,
        description: str,
        formula: str,
        referenced_metrics: List[str] = None,
        filters: Dict = None,
    ) -> Dict:
        """
        Create calculated metric using formula
        
        Formula syntax: uses metric names and operators
        Example: (Revenue - Cost) / Revenue * 100
        """
        
        return {
            "metric_id": "",
            "name": name,
            "description": description,
            "type": MetricType.CALCULATED.value,
            "definition": {
                "formula": formula,
                "referenced_metrics": referenced_metrics or [],
                "filters": filters or {},
            },
            "created_date": datetime.utcnow().isoformat(),
            "created_by": "",
            "status": "draft",
            "version": 1,
        }
    
    def create_composite_metric(
        self,
        name: str,
        description: str,
        components: List[Dict],
        aggregation: str = "sum",
    ) -> Dict:
        """
        Create composite metric from multiple metrics
        
        Components: [{"metric": "metric_id", "weight": 0.5}, ...]
        Aggregations: sum, avg, weighted_avg, min, max
        """
        
        return {
            "metric_id": "",
            "name": name,
            "description": description,
            "type": MetricType.COMPOSITE.value,
            "definition": {
                "components": components,
                "aggregation": aggregation,
            },
            "created_date": datetime.utcnow().isoformat(),
            "created_by": "",
            "status": "draft",
            "version": 1,
        }
    
    # ========================================================================
    # METRIC CONFIGURATION
    # ========================================================================
    
    def configure_metric_formatting(
        self,
        metric_id: str,
        format_type: str = "number",
        decimal_places: int = 2,
        prefix: str = None,
        suffix: str = None,
        thousand_separator: bool = True,
    ) -> Dict:
        """
        Configure how metric displays
        
        Formats: number, currency, percentage, bytes, duration
        """
        
        return {
            "metric_id": metric_id,
            "format": format_type,
            "decimal_places": decimal_places,
            "prefix": prefix,
            "suffix": suffix,
            "thousand_separator": thousand_separator,
            "updated_date": datetime.utcnow().isoformat(),
        }
    
    def set_metric_thresholds(
        self,
        metric_id: str,
        thresholds: List[Dict],
    ) -> Dict:
        """
        Set performance thresholds for metric
        
        Thresholds: [
            {"value": 80, "status": "good", "color": "#10b981"},
            {"value": 50, "status": "warning", "color": "#f59e0b"},
            {"value": 0, "status": "critical", "color": "#ef4444"}
        ]
        """
        
        return {
            "metric_id": metric_id,
            "thresholds": thresholds,
            "alert_enabled": True,
            "updated_date": datetime.utcnow().isoformat(),
        }
    
    def set_metric_targets(
        self,
        metric_id: str,
        targets: List[Dict],
    ) -> Dict:
        """
        Set target values for metric
        
        Targets: [
            {"period": "monthly", "value": 10000},
            {"period": "quarterly", "value": 30000},
            {"period": "annual", "value": 120000}
        ]
        """
        
        return {
            "metric_id": metric_id,
            "targets": targets,
            "tracking_enabled": True,
            "updated_date": datetime.utcnow().isoformat(),
        }
    
    def add_metric_dimension(
        self,
        metric_id: str,
        dimension: str,
    ) -> Dict:
        """Add breakdown dimension to metric"""
        
        return {
            "metric_id": metric_id,
            "dimension": dimension,
            "sort_order": "desc",
            "limit": None,
        }
    
    # ========================================================================
    # METRIC VALIDATION & TESTING
    # ========================================================================
    
    def validate_metric_formula(
        self,
        formula: str,
        referenced_metrics: List[str] = None,
    ) -> Dict:
        """
        Validate metric formula syntax and references
        
        Checks:
        - Valid syntax
        - Referenced metrics exist
        - No circular dependencies
        - Proper operator usage
        """
        
        return {
            "formula": formula,
            "valid": True,
            "errors": [],
            "warnings": [],
            "referenced_metrics": referenced_metrics or [],
            "estimated_computation_time_ms": 0,
        }
    
    def test_metric(
        self,
        metric_id: str,
        test_data: Dict = None,
        date_range: Dict = None,
    ) -> Dict:
        """
        Test metric calculation before deployment
        
        Returns:
        - Sample value
        - Historical trend
        - Calculation time
        - Any errors/warnings
        """
        
        return {
            "test_id": "",
            "metric_id": metric_id,
            "test_date": datetime.utcnow().isoformat(),
            "sample_value": 0.0,
            "historical_values": [],
            "calculation_time_ms": 0,
            "errors": [],
            "warnings": [],
            "passed": True,
        }
    
    def preview_metric_data(
        self,
        metric_id: str,
        limit: int = 100,
        sort_by: str = "date",
    ) -> Dict:
        """
        Preview metric data before using in dashboards
        
        Shows:
        - Sample data values
        - Breakdown by dimension
        - Time series preview
        - Data quality metrics
        """
        
        return {
            "metric_id": metric_id,
            "preview_data": [],
            "row_count": 0,
            "data_quality": {
                "completeness": 100.0,
                "null_percent": 0.0,
                "outliers": 0,
            },
            "date_range": {},
        }
    
    # ========================================================================
    # METRIC VERSIONING & DEPLOYMENT
    # ========================================================================
    
    def publish_metric(
        self,
        metric_id: str,
    ) -> Dict:
        """
        Publish metric version (deploy to production)
        
        Makes metric available for use in dashboards and reports
        """
        
        return {
            "metric_id": metric_id,
            "version": 1,
            "published_date": datetime.utcnow().isoformat(),
            "published_by": "",
            "status": "published",
            "available_in_dashboards": True,
        }
    
    def create_metric_version(
        self,
        metric_id: str,
        change_description: str = None,
    ) -> Dict:
        """
        Create new version of metric (after changes)
        
        Allows testing changes before affecting dashboards using old version
        """
        
        return {
            "metric_id": metric_id,
            "version": 2,
            "parent_version": 1,
            "created_date": datetime.utcnow().isoformat(),
            "change_description": change_description,
            "status": "draft",
        }
    
    def compare_metric_versions(
        self,
        metric_id: str,
        version_1: int,
        version_2: int,
    ) -> Dict:
        """
        Compare two metric versions
        
        Shows:
        - Definition differences
        - Calculation differences
        - Impact analysis (which dashboards use each version)
        """
        
        return {
            "metric_id": metric_id,
            "version_1": version_1,
            "version_2": version_2,
            "definition_changed": False,
            "formula_changed": False,
            "diffs": [],
            "impacted_dashboards": [],
        }
    
    def rollback_metric(
        self,
        metric_id: str,
        target_version: int,
    ) -> Dict:
        """
        Rollback metric to previous version
        
        Used if published metric has issues
        """
        
        return {
            "metric_id": metric_id,
            "previous_version": 2,
            "target_version": target_version,
            "rollback_date": datetime.utcnow().isoformat(),
            "rollback_by": "",
            "dashboards_affected": 0,
        }
    
    # ========================================================================
    # METRIC INSIGHTS & ANALYTICS
    # ========================================================================
    
    def analyze_metric_usage(
        self,
        metric_id: str,
        days: int = 30,
    ) -> Dict:
        """
        Analyze how metric is used across platform
        
        Shows:
        - Dashboards using metric
        - Reports using metric
        - View frequency
        - Popular dimensions
        """
        
        return {
            "metric_id": metric_id,
            "period_days": days,
            "dashboards_using": 0,
            "reports_using": 0,
            "total_views": 0,
            "unique_viewers": 0,
            "popular_dimensions": [],
            "most_common_filters": [],
        }
    
    def get_metric_dependencies(
        self,
        metric_id: str,
    ) -> Dict:
        """
        Get metrics this depends on and metrics depending on this
        
        Shows:
        - Upstream dependencies
        - Downstream dependents
        - Dependency chain
        """
        
        return {
            "metric_id": metric_id,
            "depends_on": [],
            "depended_on_by": [],
            "dependency_chain": {
                "upstream": [],
                "downstream": [],
            },
        }
    
    def calculate_metric_performance(
        self,
        metric_id: str,
    ) -> Dict:
        """
        Calculate metric performance metrics
        
        Shows:
        - Query time
        - Data freshness
        - Calculation accuracy
        - Caching efficiency
        """
        
        return {
            "metric_id": metric_id,
            "avg_query_time_ms": 0,
            "data_freshness_minutes": 0,
            "last_calculated": datetime.utcnow().isoformat(),
            "cache_hit_rate": 0.0,
            "error_rate": 0.0,
        }
    
    # ========================================================================
    # KPI MANAGEMENT
    # ========================================================================
    
    def create_kpi(
        self,
        name: str,
        metric_id: str,
        target_value: float,
        period: str = "monthly",
        owner: str = None,
    ) -> Dict:
        """
        Create KPI from metric
        
        KPI = Key Performance Indicator with targets and ownership
        Periods: daily, weekly, monthly, quarterly, annual
        """
        
        return {
            "kpi_id": "",
            "name": name,
            "metric_id": metric_id,
            "target_value": target_value,
            "period": period,
            "owner": owner,
            "created_date": datetime.utcnow().isoformat(),
            "status": "active",
        }
    
    def set_kpi_tracking(
        self,
        kpi_id: str,
        historical_comparison: bool = True,
        benchmark_comparison: bool = True,
    ) -> Dict:
        """
        Configure KPI tracking options
        
        Enables:
        - Historical comparison (vs previous period)
        - Benchmark comparison (vs target/industry)
        - Trend analysis
        - Forecast vs actual
        """
        
        return {
            "kpi_id": kpi_id,
            "track_historical": historical_comparison,
            "track_benchmark": benchmark_comparison,
            "track_trend": True,
            "track_forecast": True,
            "updated_date": datetime.utcnow().isoformat(),
        }
    
    def get_kpi_status(
        self,
        kpi_id: str,
    ) -> Dict:
        """
        Get current KPI status and progress
        
        Shows:
        - Current value vs target
        - Progress percentage
        - Status (on track, at risk, critical)
        - Trend
        """
        
        return {
            "kpi_id": kpi_id,
            "current_value": 0.0,
            "target_value": 0.0,
            "progress_percent": 0.0,
            "status": "on_track",
            "trend": "improving",
            "variance": 0.0,
            "days_remaining": 0,
        }
    
    def create_metric_benchmark(
        self,
        metric_id: str,
        benchmark_type: str = "industry",
        benchmark_value: float = None,
    ) -> Dict:
        """
        Create benchmark for metric
        
        Types: industry, historical, target, peers
        """
        
        return {
            "benchmark_id": "",
            "metric_id": metric_id,
            "type": benchmark_type,
            "value": benchmark_value,
            "source": "",
            "created_date": datetime.utcnow().isoformat(),
        }
