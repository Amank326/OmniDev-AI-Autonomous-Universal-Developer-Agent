"""
Causal Analysis Service for OmniDev AI
Root cause identification and causal inference for anomalies
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import math


class CausalRelation(str, Enum):
    """Types of causal relationships detected"""
    DIRECT = "direct"
    INDIRECT = "indirect"
    CONFOUNDING = "confounding"
    MEDIATION = "mediation"
    INTERACTION = "interaction"


class CausalStrength(str, Enum):
    """Strength of causal effect"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class CausalLink:
    """A causal relationship between two variables"""
    source_metric: str
    target_metric: str
    relation_type: CausalRelation
    strength: float  # 0-1 scale
    confidence: float  # 0-1 scale
    lag_periods: int  # Time lag in periods
    description: str
    supporting_evidence: List[str]


@dataclass
class RootCause:
    """Identified root cause for an anomaly"""
    anomaly_id: str
    root_cause_metric: str
    root_cause_value: float
    contribution_percent: float  # Percentage contribution to anomaly
    causal_path: List[CausalLink]  # Chain of causality
    confidence: float
    direct_effect: float  # Direct impact score
    indirect_effect: float  # Indirect impact score
    identified_at: datetime
    description: str
    recommended_actions: List[str]


@dataclass
class CausalGraphNode:
    """Node in causal graph"""
    metric_name: str
    current_value: float
    baseline_value: float
    anomalies_count: int
    outgoing_edges: List[str]  # Metrics this causes
    incoming_edges: List[str]  # Metrics causing this


@dataclass
class CausalAnalysisResult:
    """Complete causal analysis result"""
    analysis_timestamp: datetime
    target_anomaly: str
    root_causes: List[RootCause]
    causal_graph: Dict[str, CausalGraphNode]
    primary_causal_path: List[str]  # Sequence of metrics
    confidence_score: float
    explanation: str
    actionable_insights: List[str]


class CausalAnalysisService:
    """Service for causal analysis and root cause identification"""

    def __init__(self):
        """Initialize causal analysis service"""
        self.causal_graphs: Dict[str, Dict] = {}
        self.causal_relationships: Dict[str, List[CausalLink]] = {}
        self.root_causes: Dict[str, List[RootCause]] = {}
        # Known causal relationships (configurable)
        self.predefined_relationships = {
            'cpu_usage': ['throughput', 'latency', 'error_rate'],
            'memory_usage': ['gc_pause_time', 'latency', 'throughput'],
            'error_rate': ['retry_count', 'latency_p99', 'task_failures'],
            'task_queue_depth': ['latency', 'throughput'],
            'network_latency': ['api_response_time', 'database_query_time'],
        }

    def build_causal_graph(
        self,
        metrics: Dict[str, List[Tuple[float, datetime]]],
        window_size: int = 20,
    ) -> Dict[str, CausalGraphNode]:
        """
        Build a causal graph from metric data
        
        Args:
            metrics: Dictionary of metric_name -> data_points
            window_size: Window for correlation calculation
            
        Returns:
            Causal graph as dictionary of nodes
        """
        causal_graph = {}

        # Create nodes for each metric
        for metric_name, data_points in metrics.items():
            if len(data_points) == 0:
                continue

            values = [v for v, _ in data_points]
            current = values[-1]
            baseline = sum(values[::2]) / len(values[::2]) if len(values) > 1 else values[0]

            node = CausalGraphNode(
                metric_name=metric_name,
                current_value=current,
                baseline_value=baseline,
                anomalies_count=0,
                outgoing_edges=[],
                incoming_edges=[],
            )
            causal_graph[metric_name] = node

        # Build edges based on known relationships and correlations
        for source_metric, target_metrics in self.predefined_relationships.items():
            if source_metric in causal_graph:
                for target_metric in target_metrics:
                    if target_metric in causal_graph:
                        # Check for correlation
                        if source_metric in metrics and target_metric in metrics:
                            correlation = self._calculate_correlation(
                                metrics[source_metric],
                                metrics[target_metric],
                                window_size,
                            )
                            if correlation > 0.5:  # Significant correlation
                                causal_graph[source_metric].outgoing_edges.append(target_metric)
                                causal_graph[target_metric].incoming_edges.append(source_metric)

        return causal_graph

    def identify_root_causes(
        self,
        anomaly_metric: str,
        anomaly_value: float,
        baseline_value: float,
        metrics: Dict[str, List[Tuple[float, datetime]]],
        causal_graph: Dict[str, CausalGraphNode],
    ) -> List[RootCause]:
        """
        Identify root causes for an anomaly
        
        Args:
            anomaly_metric: Metric with the anomaly
            anomaly_value: Observed anomalous value
            baseline_value: Normal baseline value
            metrics: All metric data
            causal_graph: Pre-built causal graph
            
        Returns:
            List of identified root causes
        """
        root_causes = []

        # Backward search through causal graph
        visited = set()
        path_queue = [(anomaly_metric, [], 1.0)]  # (metric, path, strength)

        while path_queue:
            current_metric, path, accumulated_strength = path_queue.pop(0)

            if current_metric in visited or len(path) > 5:
                continue
            visited.add(current_metric)

            # Check incoming edges (causes)
            if current_metric in causal_graph:
                node = causal_graph[current_metric]
                for cause_metric in node.incoming_edges:
                    if cause_metric in metrics:
                        cause_data = metrics[cause_metric]
                        if len(cause_data) > 0:
                            cause_values = [v for v, _ in cause_data]
                            cause_current = cause_values[-1]
                            cause_baseline = sum(cause_values) / len(cause_values)

                            # Check if cause metric is abnormal
                            deviation = abs(cause_current - cause_baseline)
                            if deviation > 0:
                                # Calculate contribution
                                correlation = self._calculate_correlation(
                                    metrics[cause_metric],
                                    metrics[anomaly_metric],
                                    min(10, len(cause_values)),
                                )
                                contribution = (correlation ** 2) * accumulated_strength

                                if contribution > 0.1:  # Significant contribution
                                    new_path = path + [cause_metric]

                                    # Create root cause
                                    if not any(
                                        rc.root_cause_metric == cause_metric
                                        for rc in root_causes
                                    ):
                                        root_cause = RootCause(
                                            anomaly_id=f"{anomaly_metric}_anomaly",
                                            root_cause_metric=cause_metric,
                                            root_cause_value=cause_current,
                                            contribution_percent=contribution * 100,
                                            causal_path=self._build_causal_path(
                                                new_path, metrics
                                            ),
                                            confidence=correlation,
                                            direct_effect=deviation / (cause_baseline + 0.001),
                                            indirect_effect=0.0,
                                            identified_at=datetime.utcnow(),
                                            description=f"{cause_metric} deviated {deviation:.2f} from baseline {cause_baseline:.2f}",
                                            recommended_actions=[
                                                f"Investigate {cause_metric} anomaly",
                                                f"Check logs for {cause_metric} changes",
                                                f"Review {cause_metric} recent configurations",
                                            ],
                                        )
                                        root_causes.append(root_cause)

                                    # Continue backward search
                                    path_queue.append(
                                        (cause_metric, new_path, contribution)
                                    )

        # Sort by contribution
        root_causes.sort(key=lambda rc: rc.contribution_percent, reverse=True)
        return root_causes

    def perform_causal_analysis(
        self,
        workspace_id: str,
        anomaly_metric: str,
        anomaly_value: float,
        baseline_value: float,
        metrics: Dict[str, List[Tuple[float, datetime]]],
    ) -> CausalAnalysisResult:
        """
        Perform complete causal analysis
        
        Args:
            workspace_id: Workspace identifier
            anomaly_metric: Metric with anomaly
            anomaly_value: Anomalous value
            baseline_value: Baseline value
            metrics: All metric data
            
        Returns:
            Complete causal analysis result
        """
        # Build causal graph
        causal_graph = self.build_causal_graph(metrics)

        # Identify root causes
        root_causes = self.identify_root_causes(
            anomaly_metric, anomaly_value, baseline_value, metrics, causal_graph
        )

        # Extract primary causal path
        primary_path = []
        if root_causes:
            primary_path = [anomaly_metric] + root_causes[0].causal_path
            primary_path = [m for path in primary_path for m in (path if isinstance(path, list) else [path])][:5]

        # Build explanation
        explanation = self._build_explanation(anomaly_metric, root_causes)

        # Generate insights
        insights = self._generate_insights(root_causes, metrics)

        # Calculate overall confidence
        overall_confidence = (
            sum(rc.confidence * rc.contribution_percent / 100 for rc in root_causes)
            / len(root_causes)
            if root_causes
            else 0.0
        )

        result = CausalAnalysisResult(
            analysis_timestamp=datetime.utcnow(),
            target_anomaly=anomaly_metric,
            root_causes=root_causes,
            causal_graph=causal_graph,
            primary_causal_path=primary_path,
            confidence_score=overall_confidence,
            explanation=explanation,
            actionable_insights=insights,
        )

        # Cache result
        self.root_causes[f"{workspace_id}:{anomaly_metric}"] = root_causes

        return result

    def detect_causal_loops(
        self,
        causal_graph: Dict[str, CausalGraphNode],
    ) -> List[List[str]]:
        """
        Detect feedback loops in causal graph
        
        Args:
            causal_graph: Causal graph structure
            
        Returns:
            List of detected loops (metric sequences)
        """
        loops = []

        def dfs(current, path, visited):
            visited.add(current)
            path.append(current)

            if current in causal_graph:
                for next_metric in causal_graph[current].outgoing_edges:
                    if next_metric in path:
                        # Found a loop
                        loop_start = path.index(next_metric)
                        loop = path[loop_start:] + [next_metric]
                        if loop not in loops:
                            loops.append(loop)
                    elif next_metric not in visited:
                        dfs(next_metric, path.copy(), visited.copy())

        for metric in causal_graph:
            dfs(metric, [], set())

        return loops

    def quantify_causal_effect(
        self,
        cause_metric: str,
        effect_metric: str,
        metrics: Dict[str, List[Tuple[float, datetime]]],
        window_size: int = 10,
    ) -> Dict:
        """
        Quantify causal effect magnitude
        
        Args:
            cause_metric: Potential cause metric
            effect_metric: Potential effect metric
            metrics: Metric data
            window_size: Moving window size
            
        Returns:
            Effect quantification dict
        """
        if cause_metric not in metrics or effect_metric not in metrics:
            return {"effect_size": 0.0, "direction": "unknown"}

        cause_data = metrics[cause_metric]
        effect_data = metrics[effect_metric]

        if len(cause_data) < window_size or len(effect_data) < window_size:
            return {"effect_size": 0.0, "direction": "unknown"}

        cause_values = [v for v, _ in cause_data]
        effect_values = [v for v, _ in effect_data]

        # Calculate effect size using correlation and lag
        max_effect = 0.0
        best_lag = 0
        direction = "positive" if cause_values[-1] > sum(cause_values) / len(cause_values) else "negative"

        for lag in range(0, min(window_size, len(cause_values) // 2)):
            if lag == 0:
                segment_cause = cause_values[-window_size:]
                segment_effect = effect_values[-window_size:]
            else:
                segment_cause = cause_values[-(window_size + lag):-lag]
                segment_effect = effect_values[-window_size:]

            if len(segment_cause) == len(segment_effect):
                correlation = self._calculate_correlation(
                    [(v, None) for v in segment_cause],
                    [(v, None) for v in segment_effect],
                    window_size,
                )
                if abs(correlation) > max_effect:
                    max_effect = abs(correlation)
                    best_lag = lag

        return {
            "effect_size": max_effect,
            "direction": direction,
            "best_lag_periods": best_lag,
            "confidence": max_effect,
        }

    def _calculate_correlation(
        self,
        data1: List[Tuple[float, datetime]],
        data2: List[Tuple[float, datetime]],
        min_points: int = 2,
    ) -> float:
        """Calculate Pearson correlation between two data series"""
        values1 = [v for v, _ in data1]
        values2 = [v for v, _ in data2]

        if len(values1) < min_points or len(values2) < min_points:
            return 0.0

        min_len = min(len(values1), len(values2))
        values1 = values1[-min_len:]
        values2 = values2[-min_len:]

        mean1 = sum(values1) / len(values1)
        mean2 = sum(values2) / len(values2)

        numerator = sum((values1[i] - mean1) * (values2[i] - mean2) for i in range(len(values1)))
        denom1 = sum((v - mean1) ** 2 for v in values1)
        denom2 = sum((v - mean2) ** 2 for v in values2)

        denominator = math.sqrt(denom1 * denom2) if denom1 > 0 and denom2 > 0 else 0.001

        return numerator / denominator if denominator > 0 else 0.0

    def _build_causal_path(
        self,
        path: List[str],
        metrics: Dict[str, List[Tuple[float, datetime]]],
    ) -> List[CausalLink]:
        """Build causal links for a path"""
        links = []
        for i in range(len(path) - 1):
            source = path[i]
            target = path[i + 1]

            if source in metrics and target in metrics:
                correlation = self._calculate_correlation(
                    metrics[source], metrics[target]
                )
                links.append(
                    CausalLink(
                        source_metric=source,
                        target_metric=target,
                        relation_type=CausalRelation.DIRECT,
                        strength=abs(correlation),
                        confidence=0.7,
                        lag_periods=1,
                        description=f"{source} directly affects {target}",
                        supporting_evidence=[f"Correlation: {correlation:.3f}"],
                    )
                )

        return links

    def _build_explanation(
        self,
        anomaly_metric: str,
        root_causes: List[RootCause],
    ) -> str:
        """Generate human-readable explanation"""
        if not root_causes:
            return f"No identifiable root causes found for {anomaly_metric} anomaly."

        primary_cause = root_causes[0]
        explanation = (
            f"The {anomaly_metric} anomaly was primarily caused by {primary_cause.root_cause_metric} "
            f"({primary_cause.contribution_percent:.1f}% contribution). "
        )

        if len(root_causes) > 1:
            secondary_causes = ", ".join(
                f"{rc.root_cause_metric} ({rc.contribution_percent:.1f}%)"
                for rc in root_causes[1:3]
            )
            explanation += f"Secondary factors: {secondary_causes}. "

        explanation += (
            f"Root cause analysis confidence: {primary_cause.confidence * 100:.1f}%"
        )

        return explanation

    def _generate_insights(
        self,
        root_causes: List[RootCause],
        metrics: Dict[str, List[Tuple[float, datetime]]],
    ) -> List[str]:
        """Generate actionable insights"""
        insights = []

        for i, root_cause in enumerate(root_causes[:3]):
            insight = (
                f"{i + 1}. {root_cause.root_cause_metric.replace('_', ' ').title()} "
                f"is contributing {root_cause.contribution_percent:.1f}% to the anomaly. "
            )
            insights.append(insight)

            if root_cause.recommended_actions:
                insights.append(f"   → Recommended: {root_cause.recommended_actions[0]}")

        return insights

    def get_causal_analysis(
        self,
        workspace_id: str,
        anomaly_metric: str,
    ) -> Optional[CausalAnalysisResult]:
        """Retrieve cached causal analysis"""
        return None  # Would retrieve from cache in production

    def export_causal_graph(
        self,
        causal_graph: Dict[str, CausalGraphNode],
    ) -> Dict:
        """Export causal graph as JSON"""
        return {
            "nodes": [
                {
                    "id": metric,
                    "label": metric.replace("_", " "),
                    "current_value": node.current_value,
                    "baseline_value": node.baseline_value,
                    "anomalies": node.anomalies_count,
                }
                for metric, node in causal_graph.items()
            ],
            "links": [
                {"source": metric, "target": target}
                for metric, node in causal_graph.items()
                for target in node.outgoing_edges
            ],
        }
