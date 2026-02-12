"""
Phase 26: Workspace Service
Workspace configuration, templates, snapshots, exports
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import uuid

# ========================================================================
# DATACLASSES
# ========================================================================

@dataclass
class WorkspaceTemplate:
    """Pre-built workspace configuration template"""
    template_id: str
    name: str
    description: str
    category: str  # analytics, financial, marketing, sales, ops
    metrics: List[Dict] = field(default_factory=list)
    dashboard_layout: Dict = field(default_factory=dict)
    default_insights: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    dashboard_id: str
    workspace_id: str
    name: str
    description: str
    layout: Dict  # Grid layout configuration
    metrics: List[str]  # Metric IDs
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class WorkspaceSnapshot:
    """Workspace configuration snapshot"""
    snapshot_id: str
    workspace_id: str
    timestamp: datetime
    metrics_count: int
    dashboards_count: int
    members_count: int
    configuration: Dict
    created_by: str

@dataclass
class MetricTemplate:
    """Template for commonly used metrics"""
    template_id: str
    name: str
    description: str
    metric_type: str
    calculation: Dict
    category: str


# ========================================================================
# WORKSPACE SERVICE
# ========================================================================

class WorkspaceService:
    """Manages workspace configuration and templates"""
    
    def __init__(self):
        self.templates: Dict[str, WorkspaceTemplate] = {}
        self.dashboards: Dict[str, DashboardConfig] = {}
        self.snapshots: Dict[str, WorkspaceSnapshot] = {}
        self.metric_templates: Dict[str, MetricTemplate] = {}
        self._initialize_default_templates()
    
    
    # ====================================================================
    # TEMPLATES
    # ====================================================================
    
    def _initialize_default_templates(self) -> None:
        """Initialize default workspace templates"""
        templates = [
            {
                "name": "E-commerce Analytics",
                "category": "ecommerce",
                "description": "Track sales, conversion, and customer metrics",
                "metrics": [
                    {"name": "Revenue", "type": "aggregate"},
                    {"name": "Conversion Rate", "type": "funnel"},
                    {"name": "AOV", "type": "aggregate"},
                    {"name": "Customer Retention", "type": "retention"}
                ]
            },
            {
                "name": "SaaS Metrics",
                "category": "saas",
                "description": "Monitor MRR, churn, and engagement",
                "metrics": [
                    {"name": "MRR", "type": "aggregate"},
                    {"name": "Churn Rate", "type": "aggregate"},
                    {"name": "NPS", "type": "survey"},
                    {"name": "DAU/MAU", "type": "time_series"}
                ]
            },
            {
                "name": "Marketing Dashboard",
                "category": "marketing",
                "description": "Campaign performance and funnel analysis",
                "metrics": [
                    {"name": "Impressions", "type": "aggregate"},
                    {"name": "CTR", "type": "aggregate"},
                    {"name": "Leads Generated", "type": "funnel"},
                    {"name": "CAC", "type": "aggregate"}
                ]
            }
        ]
        
        for tmpl in templates:
            template_id = str(uuid.uuid4())
            self.templates[template_id] = WorkspaceTemplate(
                template_id=template_id,
                name=tmpl["name"],
                category=tmpl["category"],
                description=tmpl["description"],
                metrics=tmpl["metrics"]
            )
    
    def get_templates(self, category: Optional[str] = None) -> List[WorkspaceTemplate]:
        """Get workspace templates"""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[WorkspaceTemplate]:
        """Get specific template"""
        return self.templates.get(template_id)
    
    def create_custom_template(self, name: str, category: str,
                              description: str, metrics: List[Dict]) -> WorkspaceTemplate:
        """Create custom workspace template"""
        template_id = str(uuid.uuid4())
        
        template = WorkspaceTemplate(
            template_id=template_id,
            name=name,
            category=category,
            description=description,
            metrics=metrics
        )
        
        self.templates[template_id] = template
        return template
    
    
    # ====================================================================
    # DASHBOARDS
    # ====================================================================
    
    def create_dashboard(self, workspace_id: str, name: str,
                        description: str, layout: Dict,
                        metrics: List[str], created_by: str) -> DashboardConfig:
        """Create workspace dashboard"""
        dashboard_id = str(uuid.uuid4())
        
        dashboard = DashboardConfig(
            dashboard_id=dashboard_id,
            workspace_id=workspace_id,
            name=name,
            description=description,
            layout=layout,
            metrics=metrics,
            created_by=created_by
        )
        
        self.dashboards[dashboard_id] = dashboard
        return dashboard
    
    def get_dashboard(self, dashboard_id: str) -> Optional[DashboardConfig]:
        """Get dashboard"""
        return self.dashboards.get(dashboard_id)
    
    def get_workspace_dashboards(self, workspace_id: str) -> List[DashboardConfig]:
        """Get all dashboards in workspace"""
        return [d for d in self.dashboards.values()
               if d.workspace_id == workspace_id]
    
    def update_dashboard(self, dashboard_id: str, name: Optional[str] = None,
                        description: Optional[str] = None,
                        layout: Optional[Dict] = None,
                        metrics: Optional[List[str]] = None) -> Optional[DashboardConfig]:
        """Update dashboard"""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return None
        
        if name:
            dashboard.name = name
        if description is not None:
            dashboard.description = description
        if layout:
            dashboard.layout = layout
        if metrics:
            dashboard.metrics = metrics
        
        dashboard.updated_at = datetime.utcnow()
        return dashboard
    
    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete dashboard"""
        if dashboard_id in self.dashboards:
            del self.dashboards[dashboard_id]
            return True
        return False
    
    
    # ====================================================================
    # SNAPSHOTS
    # ====================================================================
    
    def create_snapshot(self, workspace_id: str, metrics_count: int,
                       dashboards_count: int, members_count: int,
                       configuration: Dict, created_by: str) -> WorkspaceSnapshot:
        """Create workspace configuration snapshot"""
        snapshot_id = str(uuid.uuid4())
        
        snapshot = WorkspaceSnapshot(
            snapshot_id=snapshot_id,
            workspace_id=workspace_id,
            timestamp=datetime.utcnow(),
            metrics_count=metrics_count,
            dashboards_count=dashboards_count,
            members_count=members_count,
            configuration=configuration,
            created_by=created_by
        )
        
        self.snapshots[snapshot_id] = snapshot
        return snapshot
    
    def get_snapshot(self, snapshot_id: str) -> Optional[WorkspaceSnapshot]:
        """Get snapshot"""
        return self.snapshots.get(snapshot_id)
    
    def get_workspace_snapshots(self, workspace_id: str) -> List[WorkspaceSnapshot]:
        """Get all snapshots for workspace"""
        snapshots = [s for s in self.snapshots.values()
                    if s.workspace_id == workspace_id]
        
        # Sort by timestamp descending
        return sorted(snapshots, key=lambda s: s.timestamp, reverse=True)
    
    def restore_snapshot(self, snapshot_id: str) -> Optional[Dict]:
        """Restore from snapshot"""
        snapshot = self.snapshots.get(snapshot_id)
        if not snapshot:
            return None
        
        return snapshot.configuration
    
    
    # ====================================================================
    # METRIC TEMPLATES
    # ====================================================================
    
    def create_metric_template(self, name: str, description: str,
                              metric_type: str, calculation: Dict,
                              category: str) -> MetricTemplate:
        """Create reusable metric template"""
        template_id = str(uuid.uuid4())
        
        template = MetricTemplate(
            template_id=template_id,
            name=name,
            description=description,
            metric_type=metric_type,
            calculation=calculation,
            category=category
        )
        
        self.metric_templates[template_id] = template
        return template
    
    def get_metric_templates(self, category: Optional[str] = None) -> List[MetricTemplate]:
        """Get metric templates"""
        templates = list(self.metric_templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates
    
    def get_metric_template(self, template_id: str) -> Optional[MetricTemplate]:
        """Get metric template"""
        return self.metric_templates.get(template_id)
    
    
    # ====================================================================
    # SEARCH & DISCOVERY
    # ====================================================================
    
    def search_templates(self, query: str) -> List[WorkspaceTemplate]:
        """Search templates by name/description"""
        query = query.lower()
        return [t for t in self.templates.values()
               if query in t.name.lower() or query in t.description.lower()]
    
    def search_dashboards(self, workspace_id: str, query: str) -> List[DashboardConfig]:
        """Search dashboards in workspace"""
        query = query.lower()
        dashboards = self.get_workspace_dashboards(workspace_id)
        
        return [d for d in dashboards
               if query in d.name.lower() or query in d.description.lower()]
    
    
    # ====================================================================
    # EXPORT/IMPORT
    # ====================================================================
    
    def export_workspace_config(self, workspace_id: str) -> Dict:
        """Export workspace configuration"""
        dashboards = self.get_workspace_dashboards(workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "exported_at": datetime.utcnow().isoformat(),
            "dashboards": [
                {
                    "name": d.name,
                    "description": d.description,
                    "layout": d.layout,
                    "metrics": d.metrics
                }
                for d in dashboards
            ]
        }
    
    def import_workspace_config(self, workspace_id: str, config: Dict,
                               created_by: str) -> List[DashboardConfig]:
        """Import workspace configuration"""
        imported = []
        
        for dashboard_config in config.get("dashboards", []):
            dashboard = self.create_dashboard(
                workspace_id=workspace_id,
                name=dashboard_config["name"],
                description=dashboard_config["description"],
                layout=dashboard_config["layout"],
                metrics=dashboard_config["metrics"],
                created_by=created_by
            )
            imported.append(dashboard)
        
        return imported
