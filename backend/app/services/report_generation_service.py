"""
Report Generation Service for OmniDev AI
Generates comprehensive reports in multiple formats
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json


class ReportType(str, Enum):
    """Types of reports"""
    TASK_SUMMARY = "task_summary"
    AGENT_PERFORMANCE = "agent_performance"
    SYSTEM_HEALTH = "system_health"
    TRENDS = "trends"
    ALERTS = "alerts"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Report output formats"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"


@dataclass
class ReportConfig:
    """Report configuration"""
    name: str
    report_type: ReportType
    time_period_days: int = 7
    include_sections: List[str] = None
    filters: Dict = None
    format: ReportFormat = ReportFormat.JSON


class ReportGenerator:
    """Service for generating reports"""

    def __init__(self):
        """Initialize report generator"""
        self.generated_reports: Dict[str, Dict] = {}
        self.report_templates = self._init_templates()

    def _init_templates(self) -> Dict:
        """Initialize report templates"""
        return {
            ReportType.TASK_SUMMARY: {
                "title": "Task Summary Report",
                "sections": ["overview", "status_breakdown", "timeline", "top_performers"],
            },
            ReportType.AGENT_PERFORMANCE: {
                "title": "Agent Performance Report",
                "sections": ["agent_stats", "workload", "success_rates", "trends"],
            },
            ReportType.SYSTEM_HEALTH: {
                "title": "System Health Report",
                "sections": ["overall_health", "component_status", "resource_usage", "alerts"],
            },
            ReportType.TRENDS: {
                "title": "Trends Analysis Report",
                "sections": ["metric_trends", "patterns", "forecasts", "recommendations"],
            },
        }

    def generate_report(
        self,
        report_config: ReportConfig,
        metrics_data: Dict,
        system_data: Dict,
    ) -> Dict:
        """
        Generate comprehensive report
        
        Args:
            report_config: Report configuration
            metrics_data: Metrics to include
            system_data: System data
            
        Returns:
            Generated report
        """
        report = {
            "id": self._generate_report_id(),
            "name": report_config.name,
            "type": report_config.report_type.value,
            "generated_at": datetime.utcnow().isoformat(),
            "time_period_days": report_config.time_period_days,
            "format": report_config.format.value,
            "sections": {},
            "summary": {},
        }

        # Generate sections
        if report_config.report_type == ReportType.TASK_SUMMARY:
            report["sections"] = self._generate_task_summary(metrics_data, report_config)
        elif report_config.report_type == ReportType.AGENT_PERFORMANCE:
            report["sections"] = self._generate_agent_performance(metrics_data, report_config)
        elif report_config.report_type == ReportType.SYSTEM_HEALTH:
            report["sections"] = self._generate_system_health(system_data, report_config)
        elif report_config.report_type == ReportType.TRENDS:
            report["sections"] = self._generate_trends(metrics_data, report_config)

        # Generate summary
        report["summary"] = self._generate_summary(report)

        # Store report
        self.generated_reports[report["id"]] = report

        return report

    def _generate_task_summary(self, metrics: Dict, config: ReportConfig) -> Dict:
        """Generate task summary report sections"""
        sections = {}

        # Overview
        sections["overview"] = {
            "total_tasks": metrics.get("total_tasks", 0),
            "completed_tasks": metrics.get("completed_tasks", 0),
            "failed_tasks": metrics.get("failed_tasks", 0),
            "pending_tasks": metrics.get("pending_tasks", 0),
            "success_rate": metrics.get("success_rate", 0),
        }

        # Status breakdown
        sections["status_breakdown"] = {
            "completed": metrics.get("completed_tasks", 0),
            "running": metrics.get("running_tasks", 0),
            "failed": metrics.get("failed_tasks", 0),
            "pending": metrics.get("pending_tasks", 0),
        }

        # Timeline
        sections["timeline"] = {
            "period_start": (datetime.utcnow() - timedelta(days=config.time_period_days)).isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "days": config.time_period_days,
        }

        # Top performers (agents)
        sections["top_performers"] = metrics.get("top_agents", [])

        return sections

    def _generate_agent_performance(self, metrics: Dict, config: ReportConfig) -> Dict:
        """Generate agent performance report sections"""
        sections = {}

        # Agent stats
        sections["agent_stats"] = {
            "total_agents": metrics.get("total_agents", 0),
            "active_agents": metrics.get("active_agents", 0),
            "agents": metrics.get("agent_details", []),
        }

        # Workload distribution
        sections["workload"] = {
            "avg_tasks_per_agent": metrics.get("avg_tasks_per_agent", 0),
            "tasks_completed": metrics.get("tasks_completed", 0),
            "tasks_failed": metrics.get("tasks_failed", 0),
        }

        # Success rates
        sections["success_rates"] = {
            "overall_success_rate": metrics.get("overall_success_rate", 0),
            "by_agent": metrics.get("agent_success_rates", {}),
        }

        # Trends
        sections["trends"] = {
            "agents_with_improving_performance": [],
            "agents_with_declining_performance": [],
        }

        return sections

    def _generate_system_health(self, system_data: Dict, config: ReportConfig) -> Dict:
        """Generate system health report sections"""
        sections = {}

        # Overall health
        sections["overall_health"] = {
            "status": "healthy" if system_data.get("avg_success_rate", 0) > 80 else "degraded",
            "success_rate": system_data.get("avg_success_rate", 0),
            "uptime_percent": system_data.get("uptime_percent", 100),
        }

        # Component status
        sections["component_status"] = {
            "notification_service": system_data.get("notification_status", "operational"),
            "orchestration_service": system_data.get("orchestration_status", "operational"),
            "analytics_service": system_data.get("analytics_status", "operational"),
        }

        # Resource usage
        sections["resource_usage"] = {
            "avg_cpu_percent": system_data.get("avg_cpu_percent", 0),
            "avg_memory_percent": system_data.get("avg_memory_percent", 0),
            "storage_available_gb": system_data.get("storage_available_gb", 0),
        }

        # Alerts
        sections["alerts"] = {
            "critical_alerts": system_data.get("critical_alerts", []),
            "warning_alerts": system_data.get("warning_alerts", []),
        }

        return sections

    def _generate_trends(self, metrics: Dict, config: ReportConfig) -> Dict:
        """Generate trends analysis report sections"""
        sections = {}

        # Metric trends
        sections["metric_trends"] = {
            "task_completion_trend": metrics.get("task_completion_trend", "stable"),
            "agent_efficiency_trend": metrics.get("agent_efficiency_trend", "stable"),
            "system_load_trend": metrics.get("system_load_trend", "stable"),
        }

        # Patterns
        sections["patterns"] = {
            "peak_activity_hours": metrics.get("peak_hours", []),
            "busiest_days": metrics.get("busiest_days", []),
            "common_failure_patterns": metrics.get("failure_patterns", []),
        }

        # Forecasts
        sections["forecasts"] = {
            "expected_completion_rate_next_week": 0.95,
            "expected_task_volume_next_week": metrics.get("weekly_task_volume", 1000),
        }

        # Recommendations
        sections["recommendations"] = self._generate_recommendations(metrics)

        return sections

    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Generate report recommendations"""
        recommendations = []

        if metrics.get("success_rate", 100) < 90:
            recommendations.append("Investigate task failures - success rate below 90%")

        if metrics.get("avg_task_duration", 0) > 3600:
            recommendations.append("Review task execution times - optimize long-running tasks")

        if metrics.get("pending_tasks", 0) > 100:
            recommendations.append("Clear pending tasks queue - consider adding more agents")

        if metrics.get("failed_agents", 0) > 0:
            recommendations.append("Address agent failures - check logs for error causes")

        return recommendations

    def _generate_summary(self, report: Dict) -> Dict:
        """Generate report summary"""
        sections = report.get("sections", {})
        summary = {
            "key_metrics": {},
            "highlights": [],
            "areas_of_concern": [],
        }

        # Extract key metrics
        if sections:
            first_section = list(sections.values())[0]
            if isinstance(first_section, dict):
                summary["key_metrics"] = {
                    k: v for k, v in first_section.items()
                    if isinstance(v, (int, float, str))
                }

        return summary

    def _generate_report_id(self) -> str:
        """Generate unique report ID"""
        from uuid import uuid4
        return str(uuid4())

    def format_report(self, report: Dict, format_type: ReportFormat) -> str:
        """
        Format report for output
        
        Args:
            report: Report dictionary
            format_type: Output format
            
        Returns:
            Formatted report as string
        """
        if format_type == ReportFormat.JSON:
            return json.dumps(report, indent=2, default=str)
        elif format_type == ReportFormat.CSV:
            return self._format_as_csv(report)
        elif format_type == ReportFormat.MARKDOWN:
            return self._format_as_markdown(report)
        elif format_type == ReportFormat.HTML:
            return self._format_as_html(report)
        
        return json.dumps(report, default=str)

    def _format_as_csv(self, report: Dict) -> str:
        """Format report as CSV"""
        lines = [
            f"Report Name,{report.get('name', 'Unknown')}",
            f"Report Type,{report.get('type', 'Unknown')}",
            f"Generated,{report.get('generated_at', 'Unknown')}",
            "",
            "Section,Key,Value",
        ]

        for section_name, section_data in report.get("sections", {}).items():
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    if not isinstance(value, (list, dict)):
                        lines.append(f"{section_name},{key},{value}")

        return "\n".join(lines)

    def _format_as_markdown(self, report: Dict) -> str:
        """Format report as Markdown"""
        lines = [
            f"# {report.get('name', 'Report')}",
            "",
            f"**Type:** {report.get('type', 'Unknown')}\n",
            f"**Generated:** {report.get('generated_at', 'Unknown')}\n",
            "",
        ]

        for section_name, section_data in report.get("sections", {}).items():
            lines.append(f"## {section_name.replace('_', ' ').title()}")
            lines.append("")

            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    if not isinstance(value, (list, dict)):
                        lines.append(f"- **{key}:** {value}")
            lines.append("")

        return "\n".join(lines)

    def _format_as_html(self, report: Dict) -> str:
        """Format report as HTML"""
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            f"<title>{report.get('name', 'Report')}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1 { color: #333; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{report.get('name', 'Report')}</h1>",
            f"<p><strong>Type:</strong> {report.get('type', 'Unknown')}</p>",
            f"<p><strong>Generated:</strong> {report.get('generated_at', 'Unknown')}</p>",
        ]

        for section_name, section_data in report.get("sections", {}).items():
            html.append(f"<h2>{section_name.replace('_', ' ').title()}</h2>")

            if isinstance(section_data, dict):
                html.append("<table>")
                html.append("<tr><th>Key</th><th>Value</th></tr>")
                for key, value in section_data.items():
                    if not isinstance(value, (list, dict)):
                        html.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
                html.append("</table>")

        html.extend(["</body>", "</html>"])

        return "\n".join(html)

    def get_report(self, report_id: str) -> Optional[Dict]:
        """Get generated report by ID"""
        return self.generated_reports.get(report_id)

    def list_reports(self) -> List[Dict]:
        """List all generated reports"""
        return [
            {
                "id": report_id,
                "name": report.get("name"),
                "type": report.get("type"),
                "generated_at": report.get("generated_at"),
            }
            for report_id, report in self.generated_reports.items()
        ]

    def delete_report(self, report_id: str) -> bool:
        """Delete a report"""
        if report_id in self.generated_reports:
            del self.generated_reports[report_id]
            return True
        return False

    def export_report(self, report_id: str, format_type: ReportFormat) -> Optional[str]:
        """Export report in specified format"""
        report = self.get_report(report_id)
        if not report:
            return None

        return self.format_report(report, format_type)

    def cleanup_old_reports(self, days: int = 30) -> int:
        """Remove reports older than specified days"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        removed_count = 0

        for report_id, report in list(self.generated_reports.items()):
            generated_at = datetime.fromisoformat(report.get("generated_at", ""))
            if generated_at < cutoff_time:
                del self.generated_reports[report_id]
                removed_count += 1

        return removed_count
