"""
Predictive Analytics Service for OmniDev AI
ML-based anomaly detection and predictive recommendations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class AnomalyType(str, Enum):
    """Types of anomalies detected"""
    STATISTICAL = "statistical"
    CONTEXTUAL = "contextual"
    COLLECTIVE = "collective"
    TREND_BREAK = "trend_break"


class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationType(str, Enum):
    """Types of recommendations"""
    RESOURCE_ALLOCATION = "resource_allocation"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    RISK_MITIGATION = "risk_mitigation"
    COST_OPTIMIZATION = "cost_optimization"
    CAPACITY_PLANNING = "capacity_planning"


@dataclass
class AnomalyDetection:
    """Single anomaly detection result"""
    timestamp: datetime
    metric_name: str
    observed_value: float
    expected_value: float
    deviation_score: float  # Standard deviations from mean
    anomaly_type: AnomalyType
    confidence: float
    severity: float  # 0-1 scale
    description: str


@dataclass
class Recommendation:
    """Predictive recommendation"""
    timestamp: datetime
    recommendation_type: RecommendationType
    description: str
    expected_impact: str
    priority: str  # low, medium, high
    estimated_improvement: float  # Percentage improvement
    estimated_cost: Optional[float]
    confidence: float
    actions: List[str]


@dataclass
class PredictionResult:
    """Complete prediction and recommendation result"""
    variable: str
    prediction_timestamp: datetime
    anomalies_detected: List[AnomalyDetection]
    recommendations: List[Recommendation]
    risk_assessment: Dict[str, float]
    performance_score: float
    generated_at: datetime


class PredictiveAnalyticsService:
    """Service for ML-based predictive analytics"""

    def __init__(self):
        """Initialize predictive analytics service"""
        self.predictions: Dict[str, PredictionResult] = {}
        self.anomaly_thresholds = {
            "statistical": 3.0,  # 3 sigma
            "trend_break": 2.5,
            "contextual": 2.0,
        }
        self.risk_cache = {}

    def detect_anomalies_statistical(
        self,
        metric_name: str,
        data_points: List[Tuple[float, datetime]],
        window_size: int = 20,
        z_score_threshold: float = 3.0,
    ) -> List[AnomalyDetection]:
        """
        Statistical anomaly detection using Z-score
        
        Args:
            metric_name: Name of the metric
            data_points: List of (value, timestamp) tuples
            window_size: Window for computing statistics
            z_score_threshold: Z-score threshold for anomaly
            
        Returns:
            List of detected anomalies
        """
        values = [v for v, _ in data_points]
        timestamps = [t for _, t in data_points]

        anomalies = []

        for i in range(window_size, len(values)):
            window = values[i - window_size:i]
            mean = sum(window) / len(window)
            variance = sum((v - mean) ** 2 for v in window) / len(window)
            std_dev = math.sqrt(variance)

            if std_dev > 0:
                z_score = abs((values[i] - mean) / std_dev)
                if z_score >= z_score_threshold:
                    anomalies.append(AnomalyDetection(
                        timestamp=timestamps[i],
                        metric_name=metric_name,
                        observed_value=values[i],
                        expected_value=mean,
                        deviation_score=z_score,
                        anomaly_type=AnomalyType.STATISTICAL,
                        confidence=min(0.95, (z_score / z_score_threshold) * 0.95),
                        severity=min(1.0, z_score / (z_score_threshold * 2)),
                        description=f"Value {values[i]:.2f} deviates {z_score:.2f} sigma from mean {mean:.2f}",
                    ))

        return anomalies

    def detect_anomalies_contextual(
        self,
        metric_name: str,
        data_points: List[Tuple[float, datetime]],
        context_features: Optional[Dict] = None,
    ) -> List[AnomalyDetection]:
        """
        Contextual anomaly detection considering external factors
        
        Args:
            metric_name: Name of the metric
            data_points: List of (value, timestamp) tuples
            context_features: Optional contextual information
            
        Returns:
            List of detected anomalies
        """
        values = [v for v, _ in data_points]
        timestamps = [t for _, t in data_points]

        anomalies = []

        if len(values) < 3:
            return anomalies

        # Calculate expected range based on historical patterns
        recent_values = values[-10:] if len(values) >= 10 else values
        avg = sum(recent_values) / len(recent_values)
        std = math.sqrt(sum((v - avg) ** 2 for v in recent_values) / len(recent_values))
        
        # Contextual bounds (wider than statistical)
        lower_bound = avg - (2.0 * std)
        upper_bound = avg + (2.0 * std)

        for i in range(len(values)):
            if values[i] < lower_bound or values[i] > upper_bound:
                deviation = abs(values[i] - avg) / std if std > 0 else 0
                
                anomalies.append(AnomalyDetection(
                    timestamp=timestamps[i],
                    metric_name=metric_name,
                    observed_value=values[i],
                    expected_value=avg,
                    deviation_score=deviation,
                    anomaly_type=AnomalyType.CONTEXTUAL,
                    confidence=0.80,
                    severity=min(1.0, abs(values[i] - avg) / (upper_bound - avg)) if upper_bound != avg else 0,
                    description=f"Contextual anomaly: {metric_name} = {values[i]:.2f} outside expected range [{lower_bound:.2f}, {upper_bound:.2f}]",
                ))

        return anomalies

    def detect_collective_anomalies(
        self,
        metric_name: str,
        data_points: List[Tuple[float, datetime]],
        window_size: int = 5,
    ) -> List[AnomalyDetection]:
        """
        Detect collective anomalies (patterns unusual in sequence)
        
        Args:
            metric_name: Name of the metric
            data_points: List of (value, timestamp) tuples
            window_size: Window size for pattern detection
            
        Returns:
            List of detected collective anomalies
        """
        values = [v for v, _ in data_points]
        timestamps = [t for _, t in data_points]

        anomalies = []

        if len(values) < window_size * 2:
            return anomalies

        # Compare consecutive windows
        for i in range(window_size, len(values) - window_size):
            window1 = values[i - window_size:i]
            window2 = values[i:i + window_size]

            mean1 = sum(window1) / len(window1)
            mean2 = sum(window2) / len(window2)

            # Detect sudden shifts
            shift = abs(mean2 - mean1) / mean1 if mean1 > 0 else 0

            if shift > 0.3:  # 30% shift threshold
                anomalies.append(AnomalyDetection(
                    timestamp=timestamps[i],
                    metric_name=metric_name,
                    observed_value=values[i],
                    expected_value=mean1,
                    deviation_score=shift,
                    anomaly_type=AnomalyType.COLLECTIVE,
                    confidence=0.85,
                    severity=min(1.0, shift / 0.5),
                    description=f"Collective anomaly: sudden shift from {mean1:.2f} to {mean2:.2f}",
                ))

        return anomalies

    def detect_trend_breaks(
        self,
        metric_name: str,
        data_points: List[Tuple[float, datetime]],
    ) -> List[AnomalyDetection]:
        """
        Detect breaks in established trends
        
        Args:
            metric_name: Name of the metric
            data_points: List of (value, timestamp) tuples
            
        Returns:
            List of detected trend breaks
        """
        values = [v for v, _ in data_points]
        timestamps = [t for _, t in data_points]

        anomalies = []

        if len(values) < 5:
            return anomalies

        # Calculate trend direction for different periods
        early_period = values[:len(values) // 2]
        late_period = values[len(values) // 2:]

        early_trend = (early_period[-1] - early_period[0]) / len(early_period)
        late_trend = (late_period[-1] - late_period[0]) / len(late_period)

        # Detect reversal or significant change
        trend_change = abs(late_trend - early_trend) / (abs(early_trend) + 0.001)

        if trend_change > 0.5:  # 50% trend change
            mid_point = len(values) // 2
            anomalies.append(AnomalyDetection(
                timestamp=timestamps[mid_point],
                metric_name=metric_name,
                observed_value=values[mid_point],
                expected_value=sum(early_period) / len(early_period),
                deviation_score=trend_change,
                anomaly_type=AnomalyType.TREND_BREAK,
                confidence=0.90,
                severity=min(1.0, trend_change / 1.0),
                description=f"Trend break: direction changed from {early_trend:.3f} to {late_trend:.3f}",
            ))

        return anomalies

    def assess_performance_risk(
        self,
        metrics: Dict[str, List[Tuple[float, datetime]]],
    ) -> Dict[str, float]:
        """
        Assess overall performance risk based on multiple metrics
        
        Args:
            metrics: Dictionary of metric_name -> data_points
            
        Returns:
            Risk assessment scores
        """
        risk_assessment = {
            "overall_risk": 0.0,
            "performance_risk": 0.0,
            "operational_risk": 0.0,
            "resource_risk": 0.0,
        }

        metric_count = len(metrics)
        if metric_count == 0:
            return risk_assessment

        performance_risks = []
        operational_risks = []
        resource_risks = []

        for metric_name, data_points in metrics.items():
            if not data_points:
                continue

            values = [v for v, _ in data_points]
            recent_values = values[-5:] if len(values) >= 5 else values

            # Calculate metric-specific risk
            avg = sum(recent_values) / len(recent_values)
            std = math.sqrt(sum((v - avg) ** 2 for v in recent_values) / len(recent_values))
            coefficient_of_variation = (std / avg) if avg > 0 else 0

            if "error" in metric_name.lower() or "failure" in metric_name.lower():
                operational_risks.append(min(1.0, avg / 100 + coefficient_of_variation))
            elif "time" in metric_name.lower() or "latency" in metric_name.lower():
                performance_risks.append(min(1.0, coefficient_of_variation))
            elif "resource" in metric_name.lower() or "memory" in metric_name.lower() or "cpu" in metric_name.lower():
                resource_risks.append(min(1.0, avg / 100 + coefficient_of_variation))

        # Aggregate risks
        if performance_risks:
            risk_assessment["performance_risk"] = sum(performance_risks) / len(performance_risks)
        if operational_risks:
            risk_assessment["operational_risk"] = sum(operational_risks) / len(operational_risks)
        if resource_risks:
            risk_assessment["resource_risk"] = sum(resource_risks) / len(resource_risks)

        # Overall risk
        risk_assessment["overall_risk"] = sum([
            risk_assessment["performance_risk"] * 0.35,
            risk_assessment["operational_risk"] * 0.40,
            risk_assessment["resource_risk"] * 0.25,
        ])

        return risk_assessment

    def generate_recommendations(
        self,
        risk_assessment: Dict[str, float],
        anomalies: List[AnomalyDetection],
        metrics: Dict[str, List[Tuple[float, datetime]]],
    ) -> List[Recommendation]:
        """
        Generate actionable recommendations based on analysis
        
        Args:
            risk_assessment: Risk scores
            anomalies: Detected anomalies
            metrics: Historical metrics data
            
        Returns:
            List of recommendations
        """
        recommendations = []

        # Resource allocation recommendations
        if risk_assessment.get("resource_risk", 0) > 0.7:
            recommendations.append(Recommendation(
                timestamp=datetime.utcnow(),
                recommendation_type=RecommendationType.RESOURCE_ALLOCATION,
                description="High resource contention detected. Consider scaling resources horizontally.",
                expected_impact="Reduce resource bottlenecks and improve throughput",
                priority="high",
                estimated_improvement=20.0,
                estimated_cost=100.0,  # Relative cost units
                confidence=0.85,
                actions=[
                    "Scale up container resources by 25%",
                    "Distribute load across more worker instances",
                    "Enable auto-scaling based on CPU/memory metrics",
                ],
            ))

        # Performance optimization
        if risk_assessment.get("performance_risk", 0) > 0.6:
            recommendations.append(Recommendation(
                timestamp=datetime.utcnow(),
                recommendation_type=RecommendationType.PERFORMANCE_OPTIMIZATION,
                description="Latency and response times show concerning patterns. Optimize query performance.",
                expected_impact="Reduce p99 latency by 30-40%",
                priority="high",
                estimated_improvement=35.0,
                estimated_cost=50.0,
                confidence=0.80,
                actions=[
                    "Review and optimize slow database queries",
                    "Implement caching layer for frequently accessed data",
                    "Enable query result pagination",
                ],
            ))

        # Risk mitigation
        if len(anomalies) > 5:
            high_severity_anomalies = [a for a in anomalies if a.severity > 0.7]
            if high_severity_anomalies:
                recommendations.append(Recommendation(
                    timestamp=datetime.utcnow(),
                    recommendation_type=RecommendationType.RISK_MITIGATION,
                    description=f"Detected {len(high_severity_anomalies)} high-severity anomalies requiring attention.",
                    expected_impact="Prevent potential system failures and service disruptions",
                    priority="critical",
                    estimated_improvement=50.0,
                    estimated_cost=0.0,
                    confidence=0.95,
                    actions=[
                        "Investigate root causes of anomalies",
                        "Implement monitoring alerts for similar patterns",
                        "Review system logs for error conditions",
                    ],
                ))

        # Capacity planning
        operational_risk = risk_assessment.get("operational_risk", 0)
        if operational_risk > 0.5:
            recommendations.append(Recommendation(
                timestamp=datetime.utcnow(),
                recommendation_type=RecommendationType.CAPACITY_PLANNING,
                description="System is approaching capacity limits. Plan for expansion.",
                expected_impact="Ensure sustainable growth and avoid service degradation",
                priority="medium",
                estimated_improvement=15.0,
                estimated_cost=200.0,
                confidence=0.75,
                actions=[
                    "Conduct capacity planning analysis",
                    "Identify growth trends from metrics",
                    "Plan infrastructure expansion timeline",
                ],
            ))

        # Cost optimization
        if risk_assessment.get("resource_risk", 0) < 0.3:
            recommendations.append(Recommendation(
                timestamp=datetime.utcnow(),
                recommendation_type=RecommendationType.COST_OPTIMIZATION,
                description="Resource utilization is below optimal levels. Opportunity for cost reduction.",
                expected_impact="Reduce infrastructure costs by 15-20%",
                priority="low",
                estimated_improvement=18.0,
                estimated_cost=-30.0,  # Negative cost = savings
                confidence=0.70,
                actions=[
                    "Right-size container resources",
                    "Consolidate underutilized services",
                    "Enable more aggressive min replica scaling",
                ],
            ))

        return recommendations

    def calculate_performance_score(
        self,
        risk_assessment: Dict[str, float],
        anomalies: List[AnomalyDetection],
    ) -> float:
        """
        Calculate overall performance score (0-100)
        
        Args:
            risk_assessment: Risk scores
            anomalies: Detected anomalies
            
        Returns:
            Performance score
        """
        # Start with 100
        score = 100.0

        # Deduct for overall risk
        overall_risk = risk_assessment.get("overall_risk", 0)
        score -= overall_risk * 30

        # Deduct for anomalies
        high_severity_anomalies = len([a for a in anomalies if a.severity > 0.7])
        score -= high_severity_anomalies * 5

        medium_severity_anomalies = len([a for a in anomalies if 0.4 < a.severity <= 0.7])
        score -= medium_severity_anomalies * 2

        return max(0, min(100, score))

    def analyze(
        self,
        workspace_id: str,
        metric_name: str,
        metrics: Dict[str, List[Tuple[float, datetime]]],
    ) -> PredictionResult:
        """
        Complete predictive analysis
        
        Args:
            workspace_id: Workspace identifier
            metric_name: Primary metric being analyzed
            metrics: Dictionary of metric_name -> data_points
            
        Returns:
            Complete PredictionResult
        """
        all_anomalies = []

        # Run all anomaly detection methods
        if metric_name in metrics:
            data = metrics[metric_name]
            all_anomalies.extend(self.detect_anomalies_statistical(metric_name, data))
            all_anomalies.extend(self.detect_anomalies_contextual(metric_name, data))
            all_anomalies.extend(self.detect_collective_anomalies(metric_name, data))
            all_anomalies.extend(self.detect_trend_breaks(metric_name, data))

        # Assess risk
        risk_assessment = self.assess_performance_risk(metrics)

        # Generate recommendations
        recommendations = self.generate_recommendations(risk_assessment, all_anomalies, metrics)

        # Calculate performance score
        performance_score = self.calculate_performance_score(risk_assessment, all_anomalies)

        result = PredictionResult(
            variable=metric_name,
            prediction_timestamp=datetime.utcnow(),
            anomalies_detected=all_anomalies,
            recommendations=recommendations,
            risk_assessment=risk_assessment,
            performance_score=performance_score,
            generated_at=datetime.utcnow(),
        )

        # Cache result
        self.predictions[f"{workspace_id}:{metric_name}"] = result

        return result

    def get_prediction(
        self,
        workspace_id: str,
        metric_name: str,
    ) -> Optional[PredictionResult]:
        """Get cached prediction"""
        return self.predictions.get(f"{workspace_id}:{metric_name}")

    def clear_old_predictions(self, hours: int = 24) -> int:
        """Clear predictions older than specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        removed_count = 0

        for key, prediction in list(self.predictions.items()):
            if prediction.generated_at < cutoff_time:
                del self.predictions[key]
                removed_count += 1

        return removed_count
