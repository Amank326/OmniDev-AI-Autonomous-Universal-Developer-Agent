"""
Phase 10: Workflow Analytics Service
Aggregated metrics and performance tracking for workflows and automations
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class WorkflowAnalyticsService:
    """
    Track and analyze workflow and automation performance metrics
    Generates reports and identifies bottlenecks
    """

    def __init__(self):
        self.executions = []  # Execution records
        self.daily_stats = {}  # {date: {workflow_id: stats}}
        self.workflow_trends = {}  # {workflow_id: [daily_stats]}

    def record_execution(self, execution_data: Dict[str, Any]):
        """Record a workflow or automation execution"""
        record = {
            "id": execution_data.get("id"),
            "workflow_id": execution_data.get("workflow_id"),
            "rule_id": execution_data.get("rule_id"),
            "status": execution_data.get("status"),
            "start_time": execution_data.get("start_time"),
            "end_time": execution_data.get("end_time"),
            "execution_time": execution_data.get("execution_time", 0),
            "node_metrics": execution_data.get("node_metrics", {}),
            "error": execution_data.get("error"),
            "input_size": len(str(execution_data.get("input_data", {}))) if execution_data.get("input_data") else 0,
            "output_size": len(str(execution_data.get("output_data", {}))) if execution_data.get("output_data") else 0,
            "retry_count": execution_data.get("retries", 0),
        }

        self.executions.append(record)
        self._update_daily_stats(record)

    def _update_daily_stats(self, execution: Dict):
        """Update daily statistics"""
        workflow_id = execution.get("workflow_id") or execution.get("rule_id")
        if not workflow_id:
            return

        date = execution.get("start_time").date() if execution.get("start_time") else datetime.now(timezone.utc).date()
        date_key = str(date)

        if date_key not in self.daily_stats:
            self.daily_stats[date_key] = {}

        if workflow_id not in self.daily_stats[date_key]:
            self.daily_stats[date_key][workflow_id] = self._init_stats()

        stats = self.daily_stats[date_key][workflow_id]

        # Update counts
        stats["total_executions"] += 1

        if execution.get("status") == "success":
            stats["successful_executions"] += 1
        elif execution.get("status") == "failed":
            stats["failed_executions"] += 1
        elif execution.get("status") == "timeout":
            stats["timeout_executions"] += 1

        # Update timing stats
        exec_time = execution.get("execution_time", 0)
        if exec_time > 0:
            stats["total_time"] += exec_time
            if exec_time < stats["min_execution_time"] or stats["min_execution_time"] == 0:
                stats["min_execution_time"] = exec_time
            if exec_time > stats["max_execution_time"]:
                stats["max_execution_time"] = exec_time

        # Update error tracking
        if execution.get("error"):
            stats["error_count"] += 1
            error_type = type(execution.get("error")).__name__
            stats["error_types"][error_type] = stats["error_types"].get(error_type, 0) + 1

        # Update resource usage
        stats["total_input_bytes"] += execution.get("input_size", 0)
        stats["total_output_bytes"] += execution.get("output_size", 0)
        stats["total_retries"] += execution.get("retry_count", 0)

    def _init_stats(self) -> Dict:
        """Initialize daily stats structure"""
        return {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "timeout_executions": 0,
            "total_time": 0.0,
            "min_execution_time": float("inf"),
            "max_execution_time": 0.0,
            "error_count": 0,
            "error_types": {},
            "total_input_bytes": 0,
            "total_output_bytes": 0,
            "total_retries": 0,
        }

    def calculate_success_rate(self, workflow_id: str, days: int = 7) -> float:
        """Calculate success rate for a workflow"""
        executions = self._get_recent_executions(workflow_id, days)

        if not executions:
            return 0.0

        successful = sum(1 for e in executions if e["status"] == "success")
        return (successful / len(executions)) * 100

    def calculate_avg_execution_time(self, workflow_id: str, days: int = 7) -> float:
        """Calculate average execution time"""
        executions = self._get_recent_executions(workflow_id, days)

        if not executions:
            return 0.0

        total_time = sum(e.get("execution_time", 0) for e in executions)
        return total_time / len(executions)

    def get_bottlenecks(self, workflow_id: str, limit: int = 5) -> List[Dict]:
        """Identify slowest nodes in a workflow"""
        executions = self._get_recent_executions(workflow_id, days=7)

        node_times = defaultdict(list)
        node_errors = defaultdict(int)

        for execution in executions:
            node_metrics = execution.get("node_metrics", {})
            for node_id, metrics in node_metrics.items():
                if isinstance(metrics, dict):
                    exec_time = metrics.get("execution_time", 0)
                    if exec_time > 0:
                        node_times[node_id].append(exec_time)
                    if metrics.get("error"):
                        node_errors[node_id] += 1

        # Calculate average times
        node_avgs = [
            {
                "node_id": node_id,
                "avg_time": sum(times) / len(times),
                "executions": len(times),
                "error_count": node_errors.get(node_id, 0),
            }
            for node_id, times in node_times.items()
        ]

        # Sort by average time
        return sorted(node_avgs, key=lambda x: x["avg_time"], reverse=True)[:limit]

    def get_error_analysis(self, workflow_id: str, days: int = 7) -> Dict:
        """Analyze errors in workflow executions"""
        executions = self._get_recent_executions(workflow_id, days)

        errors = defaultdict(int)
        error_timeline = []

        for execution in executions:
            if execution.get("error"):
                error_type = type(execution.get("error")).__name__
                errors[error_type] += 1
                error_timeline.append({
                    "timestamp": execution.get("end_time"),
                    "error": error_type,
                })

        return {
            "total_errors": sum(errors.values()),
            "error_types": dict(errors),
            "error_rate": self._calculate_error_rate(executions),
            "timeline": error_timeline,
            "most_common": max(errors.items(), key=lambda x: x[1])[0] if errors else None,
        }

    def _calculate_error_rate(self, executions: List[Dict]) -> float:
        """Calculate error rate percentage"""
        if not executions:
            return 0.0

        errors = sum(1 for e in executions if e.get("error"))
        return (errors / len(executions)) * 100

    def generate_report(self, workflow_id: str, days: int = 7) -> Dict:
        """Generate comprehensive analytics report"""
        executions = self._get_recent_executions(workflow_id, days)

        if not executions:
            return {
                "workflow_id": workflow_id,
                "period_days": days,
                "summary": {
                    "total_executions": 0,
                    "success_rate": 0.0,
                    "message": "No executions in period",
                }
            }

        return {
            "workflow_id": workflow_id,
            "period_days": days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_executions": len(executions),
                "successful": sum(1 for e in executions if e["status"] == "success"),
                "failed": sum(1 for e in executions if e["status"] == "failed"),
                "success_rate": self.calculate_success_rate(workflow_id, days),
                "avg_execution_time": self.calculate_avg_execution_time(workflow_id, days),
            },
            "performance": {
                "min_time": min(e.get("execution_time", 0) for e in executions),
                "max_time": max(e.get("execution_time", 0) for e in executions),
                "median_time": self._calculate_median([e.get("execution_time", 0) for e in executions]),
                "95th_percentile": self._calculate_percentile([e.get("execution_time", 0) for e in executions], 95),
            },
            "errors": self.get_error_analysis(workflow_id, days),
            "bottlenecks": self.get_bottlenecks(workflow_id),
            "recommendations": self._generate_recommendations(workflow_id, executions),
        }

    def _generate_recommendations(self, workflow_id: str, executions: List[Dict]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        success_rate = self.calculate_success_rate(workflow_id)
        if success_rate < 95:
            recommendations.append(f"Success rate is {success_rate:.1f}%. Review error logs and improve error handling.")

        avg_time = self.calculate_avg_execution_time(workflow_id)
        if avg_time > 60:
            recommendations.append(f"Average execution time is {avg_time:.1f}s. Consider optimizing slow steps.")

        error_rate = self._calculate_error_rate(executions)
        if error_rate > 5:
            recommendations.append("Error rate exceeds 5%. Add retry logic or improve condition checks.")

        bottlenecks = self.get_bottlenecks(workflow_id, limit=1)
        if bottlenecks:
            node = bottlenecks[0]
            recommendations.append(f"Node {node['node_id']} is slow ({node['avg_time']:.2f}s). Consider parallelization.")

        return recommendations

    def get_trend_data(self, workflow_id: str, days: int = 30) -> List[Dict]:
        """Get trend data over time"""
        trends = []

        for i in range(days, 0, -1):
            date = (datetime.now(timezone.utc) - timedelta(days=i)).date()
            date_key = str(date)

            if date_key in self.daily_stats and workflow_id in self.daily_stats[date_key]:
                stats = self.daily_stats[date_key][workflow_id]
                trends.append({
                    "date": date_key,
                    "total_executions": stats["total_executions"],
                    "success_rate": (stats["successful_executions"] / stats["total_executions"] * 100) if stats["total_executions"] > 0 else 0,
                    "avg_time": (stats["total_time"] / stats["total_executions"]) if stats["total_executions"] > 0 else 0,
                    "error_rate": (stats["error_count"] / stats["total_executions"] * 100) if stats["total_executions"] > 0 else 0,
                })

        return trends

    def export_metrics(self, workflow_id: str, format: str = "json") -> Dict | str:
        """Export metrics in various formats"""
        report = self.generate_report(workflow_id)

        if format.lower() == "json":
            import json
            return json.dumps(report, default=str, indent=2)
        elif format.lower() == "csv":
            return self._convert_to_csv(report)
        else:
            return report

    def _convert_to_csv(self, report: Dict) -> str:
        """Convert report to CSV format"""
        csv_lines = [
            "Metric,Value",
            f"Total Executions,{report['summary']['total_executions']}",
            f"Success Rate,{report['summary']['success_rate']:.2f}%",
            f"Failed,{report['summary']['failed']}",
            f"Avg Execution Time,{report['summary']['avg_execution_time']:.2f}s",
        ]
        return "\n".join(csv_lines)

    def _get_recent_executions(self, workflow_id: str, days: int = 7) -> List[Dict]:
        """Get executions from the last N days"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)

        return [
            e for e in self.executions
            if (e.get("workflow_id") == workflow_id or e.get("rule_id") == workflow_id)
            and e.get("start_time")
            and e["start_time"] >= cutoff_time
        ]

    @staticmethod
    def _calculate_median(values: List[float]) -> float:
        """Calculate median value"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 1:
            return sorted_values[n // 2]
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2

    @staticmethod
    def _calculate_percentile(values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_summary_stats(self) -> Dict:
        """Get overall system statistics"""
        if not self.executions:
            return {
                "total_executions": 0,
                "total_workflows": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
            }

        total = len(self.executions)
        successful = sum(1 for e in self.executions if e["status"] == "success")
        total_time = sum(e.get("execution_time", 0) for e in self.executions)
        unique_workflows = len(set(e.get("workflow_id") for e in self.executions if e.get("workflow_id")))

        return {
            "total_executions": total,
            "total_workflows": unique_workflows,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "avg_execution_time": total_time / total if total > 0 else 0,
            "total_errors": sum(1 for e in self.executions if e.get("error")),
            "total_retries": sum(e.get("retry_count", 0) for e in self.executions),
        }
