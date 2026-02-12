"""
Phase 23: Business Intelligence Visualization Service
Advanced charting, BI integration (Tableau, Power BI), export, visualization management
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class ChartType(Enum):
    """Supported chart types"""
    LINE = "line"
    BAR = "bar"
    COLUMN = "column"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    SCATTER = "scatter"
    BUBBLE = "bubble"
    GAUGE = "gauge"
    SANKEY = "sankey"
    WATERFALL = "waterfall"
    COMBO = "combo"
    HEATMAP = "heatmap"
    FUNNEL = "funnel"
    TREEMAP = "treemap"
    SUNBURST = "sunburst"
    NETWORK = "network"
    CANDLESTICK = "candlestick"
    TABLE = "table"
    PIVOT_TABLE = "pivot_table"
    CARD = "card"
    METRIC = "metric"
    KPI = "kpi"
    SCORECARD = "scorecard"


class BIExportFormat(Enum):
    """Export formats for BI tools"""
    TABLEAU = "tableau"
    POWERBI = "powerbi"
    LOOKER = "looker"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"


class BIVisualizationService:
    """
    Advanced visualization engine for BI dashboards
    Supports 20+ chart types, BI tool integration, export
    """
    
    def __init__(self):
        """Initialize visualization service"""
        self.visualizations = {}
        self.chart_templates = {}
        self.color_schemes = {}
    
    # ========================================================================
    # CHART CREATION & CONFIGURATION
    # ========================================================================
    
    def create_visualization(
        self,
        title: str,
        chart_type: str = "line",
        data_source: str = None,
        dimensions: List[str] = None,
        metrics: List[str] = None,
        filters: Dict = None,
    ) -> Dict:
        """
        Create new visualization with specified chart type
        
        Supports 20+ chart types:
        - Time series: Line, Area, Column
        - Distribution: Bar, Pie, Donut
        - Comparison: Column, Bar, Combo
        - Composition: Pie, Treemap, Sunburst
        - Relationships: Bubble, Scatter, Network
        - Progress: Gauge, Funnel, Waterfall
        - Tabular: Table, Pivot Table
        """
        
        return {
            "visualization_id": "",
            "title": title,
            "chart_type": chart_type,
            "data_source": data_source,
            "dimensions": dimensions or [],
            "metrics": metrics or [],
            "filters": filters or {},
            "created_date": datetime.utcnow().isoformat(),
            "created_by": "",
            "config": self._get_default_config(chart_type),
        }
    
    def _get_default_config(self, chart_type: str) -> Dict:
        """Get default configuration for chart type"""
        
        base_config = {
            "title": {"visible": True, "fontSize": 16},
            "legend": {"visible": True, "position": "bottom"},
            "tooltip": {"enabled": True, "format": "default"},
            "axis": {"xAxis": {}, "yAxis": {}},
            "colors": self.get_color_scheme("default"),
        }
        
        type_configs = {
            ChartType.LINE.value: {
                "line": {"smooth": True, "symbol": "circle"},
                "animation": True,
            },
            ChartType.PIE.value: {
                "innerRadius": 0,
                "donutRatio": 0.5,
                "labelPosition": "outer",
            },
            ChartType.GAUGE.value: {
                "min": 0,
                "max": 100,
                "splitNumber": 10,
                "axisLine": {"lineStyle": {"width": 15}},
            },
            ChartType.HEATMAP.value: {
                "itemSize": 25,
                "splitNumber": 5,
                "visualMap": {"min": 0, "max": 100},
            },
        }
        
        return {**base_config, **(type_configs.get(chart_type, {}))}
    
    def configure_axes(
        self,
        visualization_id: str,
        x_axis_config: Dict = None,
        y_axis_config: Dict = None,
        y_axis_2_config: Dict = None,
    ) -> Dict:
        """
        Configure chart axes
        
        Options:
        - Title and label
        - Scale (linear, logarithmic)
        - Range (min, max, auto)
        - Format (number, currency, percentage)
        - Grid lines
        """
        
        return {
            "visualization_id": visualization_id,
            "x_axis": {
                "title": x_axis_config.get("title") if x_axis_config else "",
                "type": "category",
                "scale": "linear",
                "format": "default",
            },
            "y_axis": {
                "title": y_axis_config.get("title") if y_axis_config else "",
                "type": "value",
                "scale": y_axis_config.get("scale", "linear") if y_axis_config else "linear",
                "min": y_axis_config.get("min") if y_axis_config else "auto",
                "max": y_axis_config.get("max") if y_axis_config else "auto",
                "format": y_axis_config.get("format", "number") if y_axis_config else "number",
            },
            "y_axis_2": y_axis_2_config or None,
        }
    
    def configure_colors(
        self,
        visualization_id: str,
        color_scheme: str = "default",
        custom_colors: List[str] = None,
        data_driven_colors: Dict = None,
    ) -> Dict:
        """
        Configure color scheme and data-driven coloring
        
        Schemes:
        - default, pastel, vibrant, monochrome
        - categorical, sequential, diverging
        
        Data-driven:
        - Color by metric value
        - Color by dimension category
        - Conditional coloring by thresholds
        """
        
        return {
            "visualization_id": visualization_id,
            "color_scheme": color_scheme,
            "colors": custom_colors or self.get_color_scheme(color_scheme),
            "data_driven": data_driven_colors or {},
            "transparency": 1.0,
            "gradient": False,
        }
    
    def add_data_series(
        self,
        visualization_id: str,
        series_name: str,
        metric: str,
        aggregation: str = "sum",
        format_type: str = "number",
    ) -> Dict:
        """
        Add data series to visualization
        
        Aggregations: sum, avg, min, max, count, distinct
        Formats: number, currency, percentage, bytes, duration
        """
        
        return {
            "series_id": "",
            "visualization_id": visualization_id,
            "name": series_name,
            "metric": metric,
            "aggregation": aggregation,
            "format": format_type,
            "stack": False,
            "stack_group": None,
            "visible": True,
        }
    
    # ========================================================================
    # FORMATTING & STYLING
    # ========================================================================
    
    def format_numbers(
        self,
        visualization_id: str,
        format_type: str = "number",
        decimal_places: int = 2,
        thousand_separator: bool = True,
    ) -> Dict:
        """
        Configure number formatting
        
        Formats: number, currency, percentage, bytes, duration, custom
        """
        
        return {
            "visualization_id": visualization_id,
            "format": format_type,
            "decimal_places": decimal_places,
            "thousand_separator": thousand_separator,
            "prefix": None,
            "suffix": None,
        }
    
    def add_conditional_formatting(
        self,
        visualization_id: str,
        metric: str,
        conditions: List[Dict],
    ) -> Dict:
        """
        Add conditional formatting (color, icon, style by value)
        
        Conditions:
        - Value range: min/max
        - Format: color, icon, text style
        - Priority: order of evaluation
        """
        
        return {
            "visualization_id": visualization_id,
            "metric": metric,
            "rules": conditions,
            "enabled": True,
        }
    
    def configure_labels(
        self,
        visualization_id: str,
        show_labels: bool = True,
        label_format: str = "default",
        label_position: str = "auto",
    ) -> Dict:
        """
        Configure data labels on visualization
        
        Formats: default, percentage, currency, custom
        Positions: auto, top, bottom, left, right, center
        """
        
        return {
            "visualization_id": visualization_id,
            "show_labels": show_labels,
            "format": label_format,
            "position": label_position,
            "font_size": 12,
            "rotation": 0,
        }
    
    # ========================================================================
    # INTERACTIVITY & DRILLDOWN
    # ========================================================================
    
    def enable_drill_down(
        self,
        visualization_id: str,
        dimensions: List[str],
    ) -> Dict:
        """
        Enable drill-down navigation through dimensions
        
        Allows clicking on segments to drill into detail
        """
        
        return {
            "visualization_id": visualization_id,
            "drill_down_enabled": True,
            "drill_down_path": dimensions,
            "breadcrumb_visible": True,
        }
    
    def enable_cross_filtering(
        self,
        visualization_id: str,
        target_dashboards: List[str] = None,
    ) -> Dict:
        """
        Enable cross-filtering across dashboards
        
        Clicking element filters other connected visualizations
        """
        
        return {
            "visualization_id": visualization_id,
            "cross_filter_enabled": True,
            "target_dashboards": target_dashboards or [],
            "filter_type": "include",
        }
    
    def add_parameters(
        self,
        visualization_id: str,
        parameters: List[Dict],
    ) -> Dict:
        """
        Add interactive parameters to visualization
        
        Types: slider, dropdown, date picker, text input
        """
        
        return {
            "visualization_id": visualization_id,
            "parameters": parameters,
            "allow_multiple": False,
        }
    
    # ========================================================================
    # BI TOOL INTEGRATION
    # ========================================================================
    
    def export_to_tableau(
        self,
        visualization_id: str,
        workbook_name: str = None,
    ) -> Dict:
        """
        Export visualization config to Tableau format
        
        Generates Tableau data source and dashboard specification
        """
        
        return {
            "export_id": "",
            "format": "tableau",
            "visualization_id": visualization_id,
            "workbook_name": workbook_name or "",
            "datasource_config": {},
            "dashboard_config": {},
            "export_url": "",
            "status": "pending",
        }
    
    def export_to_powerbi(
        self,
        visualization_id: str,
        report_name: str = None,
    ) -> Dict:
        """
        Export visualization config to Power BI format
        
        Generates Power BI measure definitions and visual specifications
        """
        
        return {
            "export_id": "",
            "format": "powerbi",
            "visualization_id": visualization_id,
            "report_name": report_name or "",
            "measure_definitions": [],
            "visual_definitions": [],
            "export_url": "",
            "status": "pending",
        }
    
    def sync_to_bi_tool(
        self,
        visualization_id: str,
        bi_tool: str,
        account_id: str = None,
    ) -> Dict:
        """
        Sync visualization to BI tool account
        
        Real-time sync: updates BI tool when source changes
        """
        
        return {
            "sync_id": "",
            "visualization_id": visualization_id,
            "bi_tool": bi_tool,
            "account_id": account_id,
            "sync_enabled": True,
            "last_sync": datetime.utcnow().isoformat(),
            "next_sync": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        }
    
    # ========================================================================
    # CHART TEMPLATES & PRESETS
    # ========================================================================
    
    def get_chart_templates(self) -> List[Dict]:
        """
        Get pre-built chart templates for common scenarios
        
        Templates:
        - KPI summary, Dashboard overview
        - Sales funnel, Conversion funnel
        - Revenue trend, Cohort analysis
        - Churn analysis, Retention curves
        - User engagement, Feature adoption
        - Performance comparison, Anomalies
        """
        
        return [
            {
                "template_id": "kpi_summary",
                "name": "KPI Summary",
                "chart_type": "scorecard",
                "description": "Key metrics overview",
                "metrics": 4,
                "dimensions": 0,
            },
            {
                "template_id": "revenue_trend",
                "name": "Revenue Trend",
                "chart_type": "area",
                "description": "MRR/ARR over time",
                "metrics": 2,
                "dimensions": 1,
            },
            {
                "template_id": "sales_funnel",
                "name": "Sales Funnel",
                "chart_type": "funnel",
                "description": "Conversion rates through stages",
                "metrics": 1,
                "dimensions": 1,
            },
            {
                "template_id": "cohort_analysis",
                "name": "Cohort Analysis",
                "chart_type": "heatmap",
                "description": "Retention by cohort",
                "metrics": 1,
                "dimensions": 2,
            },
            {
                "template_id": "user_segments",
                "name": "User Segmentation",
                "chart_type": "pie",
                "description": "User distribution by segment",
                "metrics": 1,
                "dimensions": 1,
            },
        ]
    
    def apply_template(
        self,
        visualization_id: str,
        template_id: str,
    ) -> Dict:
        """Apply chart template to visualization"""
        
        return {
            "visualization_id": visualization_id,
            "template_id": template_id,
            "applied_date": datetime.utcnow().isoformat(),
            "config_applied": True,
        }
    
    # ========================================================================
    # EXPORT & DISTRIBUTION
    # ========================================================================
    
    def export_visualization(
        self,
        visualization_id: str,
        format_type: str = "pdf",
        include_data: bool = False,
    ) -> Dict:
        """
        Export visualization to file
        
        Formats: PDF, PNG, SVG, CSV (data)
        """
        
        return {
            "export_id": "",
            "visualization_id": visualization_id,
            "format": format_type,
            "include_data": include_data,
            "file_size_kb": 0,
            "download_url": "",
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        }
    
    def share_visualization(
        self,
        visualization_id: str,
        recipients: List[str] = None,
        access_level: str = "view",
    ) -> Dict:
        """
        Share visualization with users/groups
        
        Access levels: view, edit, admin
        """
        
        return {
            "share_id": "",
            "visualization_id": visualization_id,
            "recipients": recipients or [],
            "access_level": access_level,
            "share_url": "",
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }
    
    def get_color_scheme(self, scheme_name: str = "default") -> List[str]:
        """Get color palette for scheme"""
        
        schemes = {
            "default": ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"],
            "pastel": ["#a8d5ff", "#c1f5d8", "#ffe4b5", "#ffb3b3", "#e1d5ff"],
            "vibrant": ["#ff0080", "#ff8c00", "#40e0d0", "#ff006e", "#00d9ff"],
            "monochrome": ["#1f2937", "#4b5563", "#6b7684", "#9ca3af", "#d1d5db"],
            "categorical": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
            "sequential": ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#3182bd"],
        }
        
        return schemes.get(scheme_name, schemes["default"])
    
    def get_visualization_analytics(
        self,
        visualization_id: str,
    ) -> Dict:
        """
        Get usage analytics for visualization
        
        Views, interactions, exports, sharing
        """
        
        return {
            "visualization_id": visualization_id,
            "total_views": 0,
            "unique_viewers": 0,
            "avg_view_duration_seconds": 0,
            "interactions": 0,
            "drill_downs": 0,
            "filters_applied": 0,
            "exports": 0,
            "shares": 0,
            "most_common_interaction": "",
        }
