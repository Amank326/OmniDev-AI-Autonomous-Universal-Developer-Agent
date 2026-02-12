"""
Custom Dashboard Builder Service
Building and managing custom observability dashboards
Phase 43: Advanced Analytics & ML Features
"""

import json
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import threading


class WidgetType(Enum):
    """Types of dashboard widgets"""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    GAUGE = "gauge"
    STAT = "stat"
    TABLE = "table"
    LOGS = "logs"
    TRACES = "traces"
    HEATMAP = "heatmap"
    ALERTS = "alerts"
    METRIC = "metric"


class ChartType(Enum):
    """Chart types for visualization"""
    LINE = "line"
    BAR = "bar"
    AREA = "area"
    SCATTER = "scatter"
    PIE = "pie"
    GAUGE = "gauge"
    STAT = "stat"


class DashboardTheme(Enum):
    """Dashboard themes"""
    LIGHT = "light"
    DARK = "dark"
    CUSTOM = "custom"


@dataclass
class ChartConfig:
    """Configuration for chart widget"""
    chart_type: ChartType
    title: str
    metric_names: List[str]
    time_range_hours: int = 24
    refresh_interval_seconds: int = 30
    colors: List[str] = field(default_factory=lambda: ["#1f77b4", "#ff7f0e", "#2ca02c"])
    stacked: bool = False
    show_legend: bool = True
    show_grid: bool = True
    axis_label_x: str = "Time"
    axis_label_y: str = "Value"

    def to_dict(self):
        return {
            "chart_type": self.chart_type.value,
            "title": self.title,
            "metric_names": self.metric_names,
            "time_range_hours": self.time_range_hours,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "colors": self.colors,
            "stacked": self.stacked,
            "show_legend": self.show_legend,
            "show_grid": self.show_grid,
            "axis_label_x": self.axis_label_x,
            "axis_label_y": self.axis_label_y,
        }


@dataclass
class TableConfig:
    """Configuration for table widget"""
    title: str
    source: str  # "logs", "traces", "metrics"
    columns: List[str]
    filters: Dict[str, str] = field(default_factory=dict)
    sort_by: str = "timestamp"
    sort_order: str = "desc"
    page_size: int = 50
    show_pagination: bool = True

    def to_dict(self):
        return {
            "title": self.title,
            "source": self.source,
            "columns": self.columns,
            "filters": self.filters,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "page_size": self.page_size,
            "show_pagination": self.show_pagination,
        }


@dataclass
class DashboardWidget:
    """Widget on a dashboard"""
    id: str
    widget_type: WidgetType
    title: str
    position_x: int
    position_y: int
    width: int
    height: int
    config: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "widget_type": self.widget_type.value,
            "title": self.title,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "width": self.width,
            "height": self.height,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class DashboardLayout:
    """Layout configuration for dashboard"""
    grid_cols: int = 12
    grid_rows: int = 24
    gap_pixels: int = 10
    show_grid: bool = False

    def to_dict(self):
        return {
            "grid_cols": self.grid_cols,
            "grid_rows": self.grid_rows,
            "gap_pixels": self.gap_pixels,
            "show_grid": self.show_grid,
        }


@dataclass
class Dashboard:
    """Dashboard configuration and metadata"""
    id: str
    name: str
    description: str
    owner_id: str
    widgets: List[DashboardWidget] = field(default_factory=list)
    layout: DashboardLayout = field(default_factory=DashboardLayout)
    theme: DashboardTheme = DashboardTheme.LIGHT
    is_public: bool = False
    tags: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    view_count: int = 0
    refresh_interval_seconds: int = 30

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "widgets": [w.to_dict() for w in self.widgets],
            "layout": self.layout.to_dict(),
            "theme": self.theme.value,
            "is_public": self.is_public,
            "tags": self.tags,
            "variables": self.variables,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "view_count": self.view_count,
            "refresh_interval_seconds": self.refresh_interval_seconds,
        }


@dataclass
class DashboardTemplate:
    """Pre-built dashboard template"""
    id: str
    name: str
    category: str
    description: str
    preview_url: str
    widgets_config: List[Dict[str, Any]]
    layout_config: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "preview_url": self.preview_url,
            "created_at": self.created_at.isoformat(),
        }


class DashboardBuilder:
    """Builds and manages custom dashboards"""

    def __init__(self):
        self.dashboards: Dict[str, Dashboard] = {}
        self.templates: Dict[str, DashboardTemplate] = {}
        self.callbacks: List[Callable] = []
        self.lock = threading.RLock()
        self._initialize_templates()

    def _initialize_templates(self) -> None:
        """Initialize built-in dashboard templates"""
        with self.lock:
            # System Metrics Template
            self.templates["system_metrics"] = DashboardTemplate(
                id="system_metrics",
                name="System Metrics",
                category="System",
                description="Monitor CPU, memory, disk, and network usage",
                preview_url="/api/v1/dashboards/templates/system_metrics/preview",
                widgets_config=[
                    {
                        "type": "line_chart",
                        "title": "CPU Usage (%)",
                        "metrics": ["cpu_usage_percent"],
                        "time_range": 24,
                    },
                    {
                        "type": "line_chart",
                        "title": "Memory Usage (%)",
                        "metrics": ["memory_usage_percent"],
                        "time_range": 24,
                    },
                    {
                        "type": "line_chart",
                        "title": "Disk Usage (%)",
                        "metrics": ["disk_usage_percent"],
                        "time_range": 24,
                    },
                ],
                layout_config={"grid_cols": 12, "grid_rows": 24},
            )

            # API Metrics Template
            self.templates["api_metrics"] = DashboardTemplate(
                id="api_metrics",
                name="API Metrics",
                category="Application",
                description="Monitor API request rates, latency, and errors",
                preview_url="/api/v1/dashboards/templates/api_metrics/preview",
                widgets_config=[
                    {
                        "type": "line_chart",
                        "title": "Request Rate",
                        "metrics": ["api_requests_total"],
                    },
                    {
                        "type": "line_chart",
                        "title": "Request Latency (ms)",
                        "metrics": ["api_request_duration_ms"],
                    },
                    {
                        "type": "line_chart",
                        "title": "Error Rate",
                        "metrics": ["api_errors_total"],
                    },
                ],
                layout_config={"grid_cols": 12, "grid_rows": 24},
            )

            # Alerts Template
            self.templates["alerts_overview"] = DashboardTemplate(
                id="alerts_overview",
                name="Alerts Overview",
                category="Alerting",
                description="View active alerts and historical trends",
                preview_url="/api/v1/dashboards/templates/alerts_overview/preview",
                widgets_config=[
                    {
                        "type": "alerts",
                        "title": "Active Alerts",
                    },
                    {
                        "type": "bar_chart",
                        "title": "Alerts by Severity",
                    },
                ],
                layout_config={"grid_cols": 12, "grid_rows": 24},
            )

    def create_dashboard(
        self, name: str, description: str, owner_id: str, from_template: Optional[str] = None
    ) -> Dashboard:
        """Create new dashboard"""
        with self.lock:
            dashboard_id = str(uuid.uuid4())

            if from_template and from_template in self.templates:
                template = self.templates[from_template]
                dashboard = Dashboard(
                    id=dashboard_id,
                    name=name,
                    description=description,
                    owner_id=owner_id,
                    layout=DashboardLayout(**template.layout_config),
                )

                # Add widgets from template
                for widget_config in template.widgets_config:
                    widget_id = str(uuid.uuid4())
                    widget = DashboardWidget(
                        id=widget_id,
                        widget_type=WidgetType.LINE_CHART,
                        title=widget_config.get("title", "Widget"),
                        position_x=0,
                        position_y=0,
                        width=6,
                        height=6,
                        config=widget_config,
                    )
                    dashboard.widgets.append(widget)
            else:
                dashboard = Dashboard(
                    id=dashboard_id,
                    name=name,
                    description=description,
                    owner_id=owner_id,
                )

            self.dashboards[dashboard_id] = dashboard

            # Notify callbacks
            self._notify_callbacks({
                "event": "dashboard_created",
                "dashboard_id": dashboard_id,
                "name": name,
            })

            return dashboard

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID"""
        with self.lock:
            dashboard = self.dashboards.get(dashboard_id)
            if dashboard:
                dashboard.view_count += 1
            return dashboard

    def update_dashboard(self, dashboard_id: str, **kwargs) -> bool:
        """Update dashboard"""
        with self.lock:
            dashboard = self.dashboards.get(dashboard_id)
            if not dashboard:
                return False

            for key, value in kwargs.items():
                if hasattr(dashboard, key) and key != "id":
                    setattr(dashboard, key, value)

            dashboard.updated_at = datetime.now()

            self._notify_callbacks({
                "event": "dashboard_updated",
                "dashboard_id": dashboard_id,
            })

            return True

    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete dashboard"""
        with self.lock:
            if dashboard_id in self.dashboards:
                del self.dashboards[dashboard_id]

                self._notify_callbacks({
                    "event": "dashboard_deleted",
                    "dashboard_id": dashboard_id,
                })

                return True
            return False

    def add_widget(
        self,
        dashboard_id: str,
        widget_type: WidgetType,
        title: str,
        config: Dict[str, Any],
        position_x: int = 0,
        position_y: int = 0,
        width: int = 6,
        height: int = 6,
    ) -> Optional[DashboardWidget]:
        """Add widget to dashboard"""
        with self.lock:
            dashboard = self.dashboards.get(dashboard_id)
            if not dashboard:
                return None

            widget_id = str(uuid.uuid4())
            widget = DashboardWidget(
                id=widget_id,
                widget_type=widget_type,
                title=title,
                position_x=position_x,
                position_y=position_y,
                width=width,
                height=height,
                config=config,
            )

            dashboard.widgets.append(widget)
            dashboard.updated_at = datetime.now()

            self._notify_callbacks({
                "event": "widget_added",
                "dashboard_id": dashboard_id,
                "widget_id": widget_id,
            })

            return widget

    def update_widget(
        self, dashboard_id: str, widget_id: str, **kwargs
    ) -> bool:
        """Update widget configuration"""
        with self.lock:
            dashboard = self.dashboards.get(dashboard_id)
            if not dashboard:
                return False

            widget = None
            for w in dashboard.widgets:
                if w.id == widget_id:
                    widget = w
                    break

            if not widget:
                return False

            for key, value in kwargs.items():
                if hasattr(widget, key) and key != "id":
                    setattr(widget, key, value)

            widget.updated_at = datetime.now()
            dashboard.updated_at = datetime.now()

            return True

    def remove_widget(self, dashboard_id: str, widget_id: str) -> bool:
        """Remove widget from dashboard"""
        with self.lock:
            dashboard = self.dashboards.get(dashboard_id)
            if not dashboard:
                return False

            dashboard.widgets = [w for w in dashboard.widgets if w.id != widget_id]
            dashboard.updated_at = datetime.now()

            return True

    def list_dashboards(
        self, owner_id: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[Dashboard]:
        """List dashboards"""
        with self.lock:
            dashboards = list(self.dashboards.values())

            if owner_id:
                dashboards = [d for d in dashboards if d.owner_id == owner_id]

            if tags:
                dashboards = [d for d in dashboards if any(t in d.tags for t in tags)]

            return sorted(dashboards, key=lambda d: d.updated_at, reverse=True)

    def get_templates(self, category: Optional[str] = None) -> List[DashboardTemplate]:
        """Get dashboard templates"""
        with self.lock:
            templates = list(self.templates.values())

            if category:
                templates = [t for t in templates if t.category == category]

            return templates

    def export_dashboard(self, dashboard_id: str) -> Optional[str]:
        """Export dashboard as JSON"""
        with self.lock:
            dashboard = self.dashboards.get(dashboard_id)
            if not dashboard:
                return None

            return json.dumps(dashboard.to_dict(), indent=2)

    def import_dashboard(self, owner_id: str, dashboard_json: str) -> Optional[Dashboard]:
        """Import dashboard from JSON"""
        try:
            data = json.loads(dashboard_json)
            dashboard_id = str(uuid.uuid4())

            dashboard = Dashboard(
                id=dashboard_id,
                name=data.get("name", "Imported Dashboard"),
                description=data.get("description", ""),
                owner_id=owner_id,
                theme=DashboardTheme[data.get("theme", "LIGHT").upper()],
                is_public=data.get("is_public", False),
                tags=data.get("tags", []),
            )

            # Import widgets
            for widget_data in data.get("widgets", []):
                widget = DashboardWidget(
                    id=str(uuid.uuid4()),
                    widget_type=WidgetType[widget_data["widget_type"].upper()],
                    title=widget_data["title"],
                    position_x=widget_data["position_x"],
                    position_y=widget_data["position_y"],
                    width=widget_data["width"],
                    height=widget_data["height"],
                    config=widget_data["config"],
                )
                dashboard.widgets.append(widget)

            with self.lock:
                self.dashboards[dashboard_id] = dashboard

            return dashboard
        except Exception as e:
            print(f"Error importing dashboard: {e}")
            return None

    def get_dashboard_statistics(self) -> Dict[str, Any]:
        """Get dashboard builder statistics"""
        with self.lock:
            total_views = sum(d.view_count for d in self.dashboards.values())
            total_widgets = sum(len(d.widgets) for d in self.dashboards.values())

            return {
                "total_dashboards": len(self.dashboards),
                "total_widgets": total_widgets,
                "total_views": total_views,
                "total_templates": len(self.templates),
                "avg_widgets_per_dashboard": (
                    total_widgets / len(self.dashboards) if self.dashboards else 0
                ),
            }

    def register_callback(self, callback: Callable) -> None:
        """Register callback for dashboard events"""
        with self.lock:
            self.callbacks.append(callback)

    def _notify_callbacks(self, event: Dict[str, Any]) -> None:
        """Notify all callbacks"""
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in dashboard callback: {e}")


# Global singleton
_dashboard_builder = None


def get_dashboard_builder() -> DashboardBuilder:
    """Get or create dashboard builder singleton"""
    global _dashboard_builder
    if _dashboard_builder is None:
        _dashboard_builder = DashboardBuilder()
    return _dashboard_builder
