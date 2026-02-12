"""
Performance Optimizer Service - Phase 39
Query optimization, resource allocation, and bottleneck detection.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set, Callable
from datetime import datetime, timedelta
import threading
import time
import json
import logging

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Types of optimizations."""
    QUERY = "query"
    INDEX = "index"
    CACHE = "cache"
    CONNECTION_POOL = "connection_pool"
    BATCH_OPERATION = "batch_operation"
    COMPRESSION = "compression"
    PARTITIONING = "partitioning"


class QueryType(Enum):
    """Database query types."""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    JOIN = "join"
    AGGREGATE = "aggregate"


class IndexType(Enum):
    """Database index types."""
    B_TREE = "b_tree"
    HASH = "hash"
    BITMAP = "bitmap"
    FULL_TEXT = "full_text"
    GIN = "gin"
    GIST = "gist"


@dataclass
class QueryMetrics:
    """Query performance metrics."""
    query_id: str
    query_type: QueryType
    query_text: str
    execution_time_ms: float
    rows_affected: int
    rows_scanned: int
    cpu_time_ms: float
    io_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    uses_index: bool = False
    full_table_scan: bool = False
    slow_query: bool = False
    threshold_ms: float = 100.0
    
    def __post_init__(self):
        """Calculate metrics."""
        self.slow_query = self.execution_time_ms > self.threshold_ms
        self.cpu_vs_io_ratio = self.cpu_time_ms / max(self.io_time_ms, 1)


@dataclass
class IndexRecommendation:
    """Query index recommendation."""
    recommendation_id: str
    table: str
    columns: List[str]
    index_type: IndexType
    estimated_improvement_percent: float
    estimated_size_bytes: int
    maintenance_overhead_percent: float
    priority: str  # low, medium, high, critical
    reason: str
    estimated_query_time_ms: float  # After optimization


@dataclass
class BottleneckAnalysis:
    """Performance bottleneck analysis."""
    bottleneck_id: str
    metric: str  # cpu, memory, disk_io, network, lock
    severity: str  # low, medium, high, critical
    current_value: float
    threshold: float
    deviation_percent: float
    affected_queries: List[str]
    affected_resources: List[str]
    duration_seconds: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CacheRecommendation:
    """Caching recommendation."""
    recommendation_id: str
    resource: str
    context: str
    cache_hit_ratio: float
    cache_miss_cost_ms: float
    estimated_improvement_percent: float
    recommended_ttl_seconds: int
    estimated_memory_bytes: int
    priority: str  # low, medium, high, critical


@dataclass
class OptimizationResult:
    """Result of optimization."""
    optimization_id: str
    optimization_type: OptimizationType
    status: str  # proposed, implemented, in_progress, failed
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement_percent: float
    effort_level: str  # low, medium, high
    estimated_cost: float
    actual_cost: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    implementation_notes: str = ""


class QueryAnalyzer:
    """Analyzes database queries for optimization opportunities."""
    
    def __init__(self):
        """Initialize query analyzer."""
        self.query_history: List[QueryMetrics] = []
        self.lock = threading.RLock()
    
    def analyze_query(self, query_text: str, metrics: QueryMetrics) -> Tuple[bool, List[str]]:
        """Analyze query and return optimization suggestions."""
        issues = []
        
        # Full table scan detection
        if metrics.full_table_scan:
            issues.append(f"Full table scan on {metrics.rows_scanned} rows - consider adding index")
        
        # Slow query detection
        if metrics.slow_query:
            issues.append(f"Slow query: {metrics.execution_time_ms:.2f}ms (threshold: {metrics.threshold_ms}ms)")
        
        # High I/O usage
        if metrics.io_time_ms > metrics.cpu_time_ms * 2:
            issues.append("High I/O time - consider caching or materialized view")
        
        # Missing index
        if not metrics.uses_index and metrics.query_type in [QueryType.SELECT, QueryType.JOIN]:
            issues.append("Query not using index - index creation recommended")
        
        # Large result set
        if metrics.rows_affected > 10000:
            issues.append(f"Large result set ({metrics.rows_affected} rows) - consider pagination or partitioning")
        
        return len(issues) == 0, issues
    
    def record_query(self, metrics: QueryMetrics) -> None:
        """Record query metrics."""
        with self.lock:
            self.query_history.append(metrics)
            # Keep last 10000 queries
            if len(self.query_history) > 10000:
                self.query_history = self.query_history[-10000:]
    
    def get_slowest_queries(self, limit: int = 10, hours: int = 24) -> List[QueryMetrics]:
        """Get slowest queries."""
        with self.lock:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            recent = [q for q in self.query_history if q.timestamp > cutoff]
            return sorted(recent, key=lambda q: q.execution_time_ms, reverse=True)[:limit]
    
    def get_most_executed_queries(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently executed queries."""
        with self.lock:
            query_counts: Dict[str, int] = {}
            for q in self.query_history:
                query_counts[q.query_text] = query_counts.get(q.query_text, 0) + 1
            
            sorted_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)
            return sorted_queries[:limit]


class IndexOptimizer:
    """Recommends and manages database indexes."""
    
    def __init__(self):
        """Initialize index optimizer."""
        self.recommendations: Dict[str, IndexRecommendation] = {}
        self.implemented_indexes: Set[str] = set()
        self.lock = threading.RLock()
    
    def analyze_queries_for_indexes(self, queries: List[QueryMetrics]) -> List[IndexRecommendation]:
        """Analyze queries and recommend indexes."""
        with self.lock:
            recommendations = []
            
            # Group queries by table
            table_queries: Dict[str, List[QueryMetrics]] = {}
            for q in queries:
                # Simple table extraction (in production, use SQL parser)
                table = q.query_text.split("FROM")[1].split()[0] if "FROM" in q.query_text.upper() else "unknown"
                if table not in table_queries:
                    table_queries[table] = []
                table_queries[table].append(q)
            
            # Analyze each table
            for table, table_qs in table_queries.items():
                slow_qs = [q for q in table_qs if q.slow_query]
                
                if slow_qs:
                    avg_execution_time = sum(q.execution_time_ms for q in slow_qs) / len(slow_qs)
                    improvement = avg_execution_time * 0.6  # Typical 60% improvement
                    
                    rec = IndexRecommendation(
                        recommendation_id=f"idx_{table}_rec",
                        table=table,
                        columns=["id", "created_at"],  # Common columns
                        index_type=IndexType.B_TREE,
                        estimated_improvement_percent=60.0,
                        estimated_size_bytes=1024 * 100,
                        maintenance_overhead_percent=2.5,
                        priority="high" if avg_execution_time > 500 else "medium",
                        reason=f"Optimize {len(slow_qs)} slow queries",
                        estimated_query_time_ms=avg_execution_time * 0.4
                    )
                    recommendations.append(rec)
                    self.recommendations[rec.recommendation_id] = rec
            
            return recommendations
    
    def get_recommendations(self, priority_filter: Optional[str] = None) -> List[IndexRecommendation]:
        """Get index recommendations."""
        with self.lock:
            recs = list(self.recommendations.values())
            if priority_filter:
                recs = [r for r in recs if r.priority == priority_filter]
            return sorted(recs, key=lambda r: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(r.priority, 4))


class CacheOptimizer:
    """Recommends caching strategies."""
    
    def __init__(self):
        """Initialize cache optimizer."""
        self.cache_analysis: Dict[str, Dict[str, Any]] = {}
        self.recommendations: Dict[str, CacheRecommendation] = {}
        self.lock = threading.RLock()
    
    def analyze_cache_performance(self, resource: str, hits: int, misses: int, 
                                 avg_miss_latency_ms: float) -> CacheRecommendation:
        """Analyze cache performance and recommend optimization."""
        with self.lock:
            total = hits + misses
            hit_ratio = hits / total if total > 0 else 0
            
            # Determine if caching is beneficial
            improvement = (misses / total) * avg_miss_latency_ms * 0.8  # 80% improvement typical
            
            priority = "critical" if hit_ratio < 0.3 else "high" if hit_ratio < 0.5 else "low"
            
            rec = CacheRecommendation(
                recommendation_id=f"cache_{resource}_rec",
                resource=resource,
                context=f"Optimize {resource} access pattern",
                cache_hit_ratio=hit_ratio,
                cache_miss_cost_ms=avg_miss_latency_ms,
                estimated_improvement_percent=improvement / avg_miss_latency_ms * 100 if avg_miss_latency_ms > 0 else 0,
                recommended_ttl_seconds=3600,  # 1 hour default
                estimated_memory_bytes=1024 * 50,  # 50 KB estimate
                priority=priority
            )
            
            self.recommendations[rec.recommendation_id] = rec
            return rec
    
    def get_recommendations(self, priority_filter: Optional[str] = None) -> List[CacheRecommendation]:
        """Get caching recommendations."""
        with self.lock:
            recs = list(self.recommendations.values())
            if priority_filter:
                recs = [r for r in recs if r.priority == priority_filter]
            return sorted(recs, key=lambda r: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(r.priority, 4))


class BottleneckDetector:
    """Detects performance bottlenecks."""
    
    def __init__(self):
        """Initialize bottleneck detector."""
        self.metrics_history: Dict[str, List[Tuple[datetime, float]]] = {}
        self.thresholds = {
            'cpu': 80.0,
            'memory': 85.0,
            'disk_io': 90.0,
            'network': 85.0,
            'query_latency': 500.0  # ms
        }
        self.lock = threading.RLock()
    
    def record_metric(self, metric_name: str, value: float) -> None:
        """Record performance metric."""
        with self.lock:
            if metric_name not in self.metrics_history:
                self.metrics_history[metric_name] = []
            
            self.metrics_history[metric_name].append((datetime.utcnow(), value))
            
            # Keep last 1 hour of data
            cutoff = datetime.utcnow() - timedelta(hours=1)
            self.metrics_history[metric_name] = [
                (ts, v) for ts, v in self.metrics_history[metric_name]
                if ts > cutoff
            ]
    
    def detect_bottlenecks(self) -> List[BottleneckAnalysis]:
        """Detect current bottlenecks."""
        with self.lock:
            bottlenecks = []
            
            for metric_name, threshold in self.thresholds.items():
                if metric_name not in self.metrics_history:
                    continue
                
                recent_values = [v for ts, v in self.metrics_history[metric_name]
                               if ts > datetime.utcnow() - timedelta(minutes=5)]
                
                if not recent_values:
                    continue
                
                avg_value = sum(recent_values) / len(recent_values)
                
                if avg_value > threshold:
                    severity = "critical" if avg_value > threshold * 1.2 else "high"
                    
                    bottleneck = BottleneckAnalysis(
                        bottleneck_id=f"bn_{metric_name}_{int(datetime.utcnow().timestamp())}",
                        metric=metric_name,
                        severity=severity,
                        current_value=avg_value,
                        threshold=threshold,
                        deviation_percent=(avg_value - threshold) / threshold * 100,
                        affected_queries=[],
                        affected_resources=["primary_database", "cache_layer"],
                        duration_seconds=300
                    )
                    bottlenecks.append(bottleneck)
            
            return bottlenecks


class PerformanceOptimizer:
    """Main performance optimization service."""
    
    def __init__(self):
        """Initialize performance optimizer."""
        self.query_analyzer = QueryAnalyzer()
        self.index_optimizer = IndexOptimizer()
        self.cache_optimizer = CacheOptimizer()
        self.bottleneck_detector = BottleneckDetector()
        self.optimizations: Dict[str, OptimizationResult] = {}
        self.lock = threading.RLock()
    
    def analyze_performance(self, queries: List[QueryMetrics]) -> Dict[str, Any]:
        """
        Analyze overall workflow performance from execution history
        Returns performance analysis with optimization suggestions
        """
        logger.info(f"Analyzing performance for workflow {workflow_id}")

        if not executions:
            return {"status": "no_data", "suggestions": []}

        # Extract metrics
        total_duration = sum(e.get("duration", 0) for e in executions)
        avg_duration = total_duration / len(executions) if executions else 0
        success_count = len([e for e in executions if e.get("status") == "success"])
        success_rate = success_count / len(executions) if executions else 0

        # Analyze nodes
        node_metrics = self._analyze_node_performance(executions)

        # Find bottlenecks
        bottlenecks = self._identify_bottlenecks(node_metrics, executions)

        # Find parallelization opportunities
        parallelization = self._find_parallelization_opportunities(executions)

        # Generate recommendations
        recommendations = self._generate_optimization_recommendations(
            bottlenecks, parallelization, node_metrics
        )

        analysis = {
            "workflow_id": workflow_id,
            "total_executions": len(executions),
            "avg_duration": round(avg_duration, 2),
            "success_rate": round(success_rate, 2),
            "bottlenecks": bottlenecks,
            "parallelization_opportunities": parallelization,
            "recommendations": recommendations,
            "node_metrics": node_metrics,
        }

        self.workflow_analytics[workflow_id] = analysis
        return analysis

    def _analyze_node_performance(self, executions: List[Dict]) -> Dict[str, Dict]:
        """Analyze performance metrics for each node"""
        node_metrics = defaultdict(lambda: {
            "durations": [],
            "statuses": [],
            "errors": [],
        })

        for execution in executions:
            nodes = execution.get("nodes", [])
            for node in nodes:
                node_id = node.get("id")
                node_metrics[node_id]["durations"].append(node.get("duration", 0))
                node_metrics[node_id]["statuses"].append(node.get("status"))
                if node.get("error"):
                    node_metrics[node_id]["errors"].append(node.get("error"))

        # Calculate statistics for each node
        result = {}
        for node_id, metrics in node_metrics.items():
            durations = metrics["durations"]
            result[node_id] = {
                "avg_duration": np.mean(durations) if durations else 0,
                "min_duration": np.min(durations) if durations else 0,
                "max_duration": np.max(durations) if durations else 0,
                "std_duration": np.std(durations) if durations else 0,
                "success_rate": len([s for s in metrics["statuses"] if s == "success"]) / len(metrics["statuses"]) if metrics["statuses"] else 0,
                "error_count": len(metrics["errors"]),
                "common_errors": self._get_top_errors(metrics["errors"], top=3),
            }

        return result

    def _identify_bottlenecks(self, node_metrics: Dict, executions: List) -> List[Dict]:
        """Identify performance bottlenecks"""
        bottlenecks = []

        # Find slow nodes
        if node_metrics:
            max_avg_duration = max(
                (m["avg_duration"] for m in node_metrics.values()),
                default=0
            )

            for node_id, metrics in node_metrics.items():
                # Slow node (>80th percentile of all nodes)
                if metrics["avg_duration"] > max_avg_duration * 0.8:
                    bottlenecks.append({
                        "type": "slow_action",
                        "node_id": node_id,
                        "avg_duration": round(metrics["avg_duration"], 2),
                        "severity": "high" if metrics["avg_duration"] > max_avg_duration * 0.9 else "medium",
                        "impact": f"{(metrics['avg_duration'] / max_avg_duration * 100):.0f}% of max node time",
                    })

                # Unreliable node (high failure rate)
                if metrics["success_rate"] < (1 - self.bottleneck_thresholds["high_failure"]):
                    bottlenecks.append({
                        "type": "unreliable_action",
                        "node_id": node_id,
                        "success_rate": round(metrics["success_rate"], 2),
                        "failure_rate": round(1 - metrics["success_rate"], 2),
                        "error_count": metrics["error_count"],
                        "severity": "high",
                    })

                # High variance node (unpredictable performance)
                if metrics["std_duration"] > metrics["avg_duration"] * self.bottleneck_thresholds["high_variance"]:
                    bottlenecks.append({
                        "type": "high_variance",
                        "node_id": node_id,
                        "avg_duration": round(metrics["avg_duration"], 2),
                        "std_duration": round(metrics["std_duration"], 2),
                        "severity": "medium",
                        "recommendation": "Add retry logic or implement circuit breaker pattern",
                    })

        return bottlenecks

    def _find_parallelization_opportunities(self, executions: List[Dict]) -> List[Dict]:
        """Find opportunities to parallelize sequential steps"""
        opportunities = []

        if not executions:
            return opportunities

        # Get node order from first execution
        execution = executions[0]
        nodes = execution.get("nodes", [])

        # Group consecutive nodes by their independence
        for i in range(len(nodes) - 1):
            current_node = nodes[i]
            next_node = nodes[i + 1]

            # Check if nodes are independent
            if self._are_nodes_independent(current_node, next_node, execution):
                opportunities.append({
                    "type": "parallel_execution",
                    "nodes": [current_node.get("id"), next_node.get("id")],
                    "potential_speedup": 1.8,  # Rough estimate
                    "reason": "Nodes don't share dependencies",
                    "complexity": "medium",
                })

        return opportunities[:5]  # Return top 5

    def _are_nodes_independent(self, node1: Dict, node2: Dict, execution: Dict) -> bool:
        """Check if two nodes are independent and can run in parallel"""
        # Get output variables from node1
        outputs1 = set(node1.get("output_variables", []))

        # Get input variables from node2
        inputs2 = set(node2.get("input_variables", []))

        # If node2 uses outputs from node1, they're dependent
        return len(outputs1 & inputs2) == 0

    def _generate_optimization_recommendations(self, bottlenecks: List,
                                               parallelization: List,
                                               node_metrics: Dict) -> List[str]:
        """Generate actionable optimization recommendations"""
        recommendations = []

        # Recommendations for slow nodes
        slow_nodes = [b for b in bottlenecks if b.get("type") == "slow_action"]
        if slow_nodes:
            recommendations.append(
                f"Optimize {len(slow_nodes)} slow node(s): {', '.join(b.get('node_id') for b in slow_nodes[:3])}"
            )

        # Recommendations for unreliable nodes
        unreliable_nodes = [b for b in bottlenecks if b.get("type") == "unreliable_action"]
        if unreliable_nodes:
            recommendations.append(
                "Add retry logic and circuit breaker patterns for unreliable nodes"
            )

        # Parallelization recommendations
        if parallelization:
            recommendations.append(
                f"Parallelize {len(parallelization)} node sequence(s) for ~50% speedup"
            )

        # Caching recommendations
        frequently_slow = [
            (node_id, metrics)
            for node_id, metrics in node_metrics.items()
            if metrics["avg_duration"] > 5
        ]
        if frequently_slow:
            recommendations.append(
                f"Consider caching results for {len(frequently_slow)} slow operations"
            )

        # Timeout optimization
        high_variance = [
            b for b in bottlenecks if b.get("type") == "high_variance"
        ]
        if high_variance:
            recommendations.append(
                "Increase timeouts for high-variance operations"
            )

        return recommendations

    def _get_top_errors(self, errors: List[str], top: int = 3) -> List[Tuple[str, int]]:
        """Get most common errors"""
        from collections import Counter
        error_counts = Counter(errors)
        return error_counts.most_common(top)

    def optimize_timeout_settings(self, node_metrics: Dict) -> Dict[str, int]:
        """
        Suggest optimal timeout settings for each node
        Based on observed durations with safety margin
        """
        timeouts = {}

        for node_id, metrics in node_metrics.items():
            avg_duration = metrics["avg_duration"]
            max_duration = metrics["max_duration"]
            std_duration = metrics["std_duration"]

            # Timeout = max observed + 2 standard deviations + safety margin
            suggested_timeout = max_duration + (2 * std_duration) + 5  # +5s safety
            suggested_timeout = max(suggested_timeout, avg_duration * 1.5)  # At least 1.5x average

            timeouts[node_id] = int(suggested_timeout)

        return timeouts

    def optimize_retry_strategy(self, node_metrics: Dict) -> Dict[str, Dict]:
        """
        Suggest retry strategies for unreliable nodes
        Returns retry configuration (count, delay, backoff)
        """
        strategies = {}

        for node_id, metrics in node_metrics.items():
            success_rate = metrics["success_rate"]

            if success_rate < 0.9:
                failures = 1 - success_rate
                needed_retries = int(np.ceil(np.log(0.05) / np.log(failures)))

                strategies[node_id] = {
                    "max_retries": min(needed_retries, 5),
                    "initial_delay": 1,
                    "max_delay": 30,
                    "backoff_multiplier": 2,
                    "reason": f"Success rate is {success_rate*100:.0f}%",
                }

        return strategies

    def get_optimization_impact(self, optimization: Dict) -> Dict:
        """Estimate impact of applying an optimization"""
        optimization_type = optimization.get("type")

        if optimization_type == "parallelize":
            return {
                "estimated_speedup": 1.8,
                "effort": "medium",
                "risk": "low",
            }
        elif optimization_type == "cache":
            return {
                "estimated_speedup": 2.5,
                "effort": "low",
                "risk": "low",
            }
        elif optimization_type == "optimize_action":
            return {
                "estimated_speedup": 1.3,
                "effort": "high",
                "risk": "medium",
            }
        elif optimization_type == "add_retry":
            return {
                "estimated_reliability_improvement": 0.15,
                "effort": "low",
                "risk": "very_low",
            }

        return {"effort": "unknown", "risk": "unknown"}

    def apply_optimizations(self, workflow_id: str, optimizations: List[Dict]) -> Dict:
        """
        Apply multiple optimizations to a workflow
        Returns updated workflow configuration
        """
        result = {
            "workflow_id": workflow_id,
            "applied": [],
            "failed": [],
            "estimated_improvement": 1.0,
        }

        for optimization in optimizations:
            try:
                # Apply optimization (stub implementation)
                result["applied"].append(optimization)
                impact = self.get_optimization_impact(optimization)
                result["estimated_improvement"] *= (
                    impact.get("estimated_speedup", 1.0)
                )
            except Exception as e:
                result["failed"].append({
                    "optimization": optimization,
                    "error": str(e),
                })

        result["estimated_improvement"] = round(
            result["estimated_improvement"], 2
        )
        return result

    def generate_performance_report(self, workflow_id: str) -> str:
        """Generate human-readable performance report"""
        analysis = self.workflow_analytics.get(workflow_id)

        if not analysis:
            return "No performance data available"

        report = f"""
Performance Report: {workflow_id}

Summary:
- Total Executions: {analysis['total_executions']}
- Average Duration: {analysis['avg_duration']}s
- Success Rate: {analysis['success_rate']*100:.1f}%

Bottlenecks ({len(analysis['bottlenecks'])})::
"""
        for bottleneck in analysis['bottlenecks'][:5]:
            report += f"- {bottleneck['type']}: {bottleneck.get('node_id')} (Severity: {bottleneck.get('severity')})\n"

        report += f"\nOptimization Opportunities ({len(analysis['parallelization_opportunities'])}):\n"
        for opp in analysis['parallelization_opportunities'][:3]:
            report += f"- {opp['reason']} (Speedup: {opp.get('potential_speedup')}x)\n"

        report += f"\nRecommendations:\n"
        for rec in analysis['recommendations']:
            report += f"- {rec}\n"

        return report
