"""
Anomaly Detection Service for OmniDev AI
ML-powered anomaly detection with root cause analysis and auto-remediation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import math
import numpy as np


class AnomalySeverity(str, Enum):
    """Anomaly severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RootCauseType(str, Enum):
    """Root cause types"""
    RESOURCE_SATURATION = "resource_saturation"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CONFIG_CHANGE = "config_change"
    EXTERNAL_FACTOR = "external_factor"
    SOFTWARE_ISSUE = "software_issue"
    UNKNOWN = "unknown"


class RemediationStatus(str, Enum):
    """Remediation action status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    AUTO_REMEDIATED = "auto_remediated"


@dataclass
class AnomalyDetail:
    """Detailed anomaly information"""
    anomaly_id: str
    metrics_affected: List[str]
    anomaly_types: List[str]
    severity: AnomalySeverity
    first_detected: datetime
    last_detected: datetime
    duration_hours: float
    impact_score: float
    affected_services: List[str]
    affected_users: int
    error_rate_increase_percent: float
    latency_increase_percent: float


@dataclass
class RootCauseAnalysis:
    """Root cause analysis result"""
    analysis_id: str
    anomaly_id: str
    root_causes: List[Dict]  # [{type, description, confidence_score}]
    primary_root_cause: RootCauseType
    confidence_score: float
    analysis_timestamp: datetime
    evidence: List[str]
    related_anomalies: List[str]


@dataclass
class RemediationAction:
    """Remediation action to resolve anomaly"""
    remediation_id: str
    anomaly_id: str
    root_cause_id: str
    action_type: str
    action_description: str
    severity: AnomalySeverity
    automatic: bool
    estimated_resolution_time_minutes: int
    risk_level: str
    steps: List[str]
    rollback_plan: str
    status: RemediationStatus
    initiated_at: Optional[datetime]
    completed_at: Optional[datetime]
    result_notes: str


@dataclass
class AnomalyPattern:
    """Recurring anomaly pattern"""
    pattern_id: str
    pattern_name: str
    metrics_involved: List[str]
    occurrence_frequency: str  # daily, weekly, monthly
    last_occurrence: datetime
    occurrences_count: int
    average_duration_hours: float
    average_impact_score: float
    seasonal: bool
    root_cause: Optional[RootCauseType]
    recommended_solution: str


@dataclass
class HealthScore:
    """System health score"""
    workspace_id: str
    score: float  # 0-100
    status: str  # healthy, degraded, critical
    metrics_analyzed: int
    anomalies_detected: int
    critical_anomalies: int
    trend: str  # improving, stable, degrading
    last_updated: datetime


class AnomalyDetectionService:
    """Service for ML-powered anomaly detection and root cause analysis"""

    def __init__(self):
        """Initialize anomaly detection service"""
        self.detected_anomalies: Dict[str, List[AnomalyDetail]] = {}
        self.root_causes: Dict[str, RootCauseAnalysis] = {}
        self.remediations: Dict[str, RemediationAction] = {}
        self.patterns: Dict[str, AnomalyPattern] = {}
        self.health_scores: Dict[str, HealthScore] = {}
        
        # Anomaly detection thresholds
        self.thresholds = {
            'cpu_utilization': 80,
            'memory_utilization': 85,
            'error_rate': 5,
            'latency_p99': 1000,  # ms
            'disk_utilization': 90,
            'network_saturation': 85,
        }

    def detect_anomalies_comprehensive(
        self,
        workspace_id: str,
        metrics: Dict[str, float],
        historical_data: Dict[str, List[float]],
    ) -> List[AnomalyDetail]:
        """
        Detect anomalies across multiple metrics
        
        Args:
            workspace_id: Workspace identifier
            metrics: Current metric values
            historical_data: Historical values per metric
            
        Returns:
            List of detected anomalies
        """
        anomalies = []

        for metric_name, current_value in metrics.items():
            if metric_name not in historical_data:
                continue

            historical = historical_data[metric_name]
            if len(historical) < 10:
                continue

            # Calculate statistics
            mean = np.mean(historical)
            std = np.std(historical)
            median = np.median(historical)
            q25 = np.percentile(historical, 25)
            q75 = np.percentile(historical, 75)
            iqr = q75 - q25

            # Multiple anomaly detection methods
            is_zscore_anomaly = abs(current_value - mean) > 3.0 * std
            is_iqr_anomaly = current_value < (q25 - 1.5 * iqr) or current_value > (q75 + 1.5 * iqr)
            is_threshold_anomaly = (
                metric_name in self.thresholds and 
                current_value > self.thresholds[metric_name]
            )
            is_isolation_anomaly = self._isolation_forest_detect(current_value, historical)

            # Combine methods (at least 2 methods must agree)
            methods_triggered = sum([
                is_zscore_anomaly,
                is_iqr_anomaly,
                is_threshold_anomaly,
                is_isolation_anomaly,
            ])

            if methods_triggered >= 2:
                # Determine severity
                if current_value > mean + (4 * std):
                    severity = AnomalySeverity.CRITICAL
                elif current_value > mean + (3 * std):
                    severity = AnomalySeverity.HIGH
                elif current_value > mean + (2 * std):
                    severity = AnomalySeverity.MEDIUM
                else:
                    severity = AnomalySeverity.LOW

                # Calculate impact
                percent_change = ((current_value - mean) / max(0.01, mean)) * 100
                impact_score = min(100, abs(percent_change))

                # Determine affected services
                affected_services = self._determine_affected_services(metric_name, severity)

                anomaly = AnomalyDetail(
                    anomaly_id=f"{workspace_id}:{metric_name}:{int(datetime.utcnow().timestamp())}",
                    metrics_affected=[metric_name],
                    anomaly_types=self._classify_anomaly_types(current_value, historical),
                    severity=severity,
                    first_detected=datetime.utcnow(),
                    last_detected=datetime.utcnow(),
                    duration_hours=0.0,
                    impact_score=round(impact_score, 2),
                    affected_services=affected_services,
                    affected_users=self._estimate_affected_users(severity),
                    error_rate_increase_percent=round(percent_change, 2) if "error" in metric_name else 0,
                    latency_increase_percent=round(percent_change, 2) if "latency" in metric_name else 0,
                )

                anomalies.append(anomaly)

        # Cache anomalies
        if workspace_id not in self.detected_anomalies:
            self.detected_anomalies[workspace_id] = []
        self.detected_anomalies[workspace_id].extend(anomalies)
        self.detected_anomalies[workspace_id] = self.detected_anomalies[workspace_id][-500:]

        return anomalies

    def _isolation_forest_detect(self, value: float, historical: List[float]) -> bool:
        """Simplified isolation forest anomaly detection"""
        if len(historical) < 5:
            return False
        
        # Calculate distances
        distances = [abs(value - h) for h in historical]
        mean_distance = np.mean(distances)
        
        # Anomaly if distance is significantly larger than average
        return mean_distance > np.std(distances) * 3

    def _classify_anomaly_types(
        self,
        current_value: float,
        historical: List[float],
    ) -> List[str]:
        """Classify the type of anomaly detected"""
        types = []
        
        mean = np.mean(historical)
        trend = historical[-1] - historical[0] if len(historical) > 1 else 0

        if current_value > mean * 1.5:
            types.append("spike")
        elif current_value < mean * 0.5:
            types.append("dip")

        if trend > 0 and current_value > historical[-1]:
            types.append("accelerating_trend")
        elif trend < 0 and current_value < historical[-1]:
            types.append("decelerating_trend")

        return types if types else ["outlier"]

    def _determine_affected_services(
        self,
        metric_name: str,
        severity: AnomalySeverity,
    ) -> List[str]:
        """Determine which services are affected by metric anomaly"""
        service_map = {
            'cpu': ['compute', 'ml_training', 'api_gateway'],
            'memory': ['cache', 'database', 'api_gateway'],
            'latency': ['api_gateway', 'database', 'cache'],
            'error': ['api_gateway', 'workers', 'scheduler'],
            'disk': ['database', 'storage', 'cache'],
            'network': ['api_gateway', 'cdn', 'load_balancer'],
        }

        services = []
        for key, svc_list in service_map.items():
            if key in metric_name:
                services = svc_list
                break

        if severity == AnomalySeverity.CRITICAL:
            return services
        elif severity == AnomalySeverity.HIGH:
            return services[:2] if len(services) > 1 else services
        else:
            return services[:1] if services else []

    def _estimate_affected_users(self, severity: AnomalySeverity) -> int:
        """Estimate number of affected users"""
        estimates = {
            AnomalySeverity.CRITICAL: 100,
            AnomalySeverity.HIGH: 50,
            AnomalySeverity.MEDIUM: 10,
            AnomalySeverity.LOW: 1,
            AnomalySeverity.INFO: 0,
        }
        return estimates.get(severity, 0)

    def analyze_root_cause(
        self,
        workspace_id: str,
        anomaly_id: str,
        anomaly: AnomalyDetail,
        event_log: Optional[List[Dict]] = None,
    ) -> RootCauseAnalysis:
        """
        Analyze root cause of anomaly
        
        Args:
            workspace_id: Workspace identifier
            anomaly_id: Anomaly to analyze
            anomaly: Anomaly details
            event_log: Optional event log
            
        Returns:
            Root cause analysis result
        """
        root_causes = []
        evidence = []

        # Check for recent configuration changes
        if event_log:
            for event in event_log[-10:]:  # Check last 10 events
                if event.get('type') == 'config_change':
                    root_causes.append({
                        'type': RootCauseType.CONFIG_CHANGE.value,
                        'description': f"Configuration change: {event.get('description')}",
                        'confidence_score': 0.75,
                        'timestamp': event.get('timestamp'),
                    })
                    evidence.append(f"Config change detected: {event.get('description')}")

        # Resource saturation check
        if "cpu" in anomaly.metrics_affected or "memory" in anomaly.metrics_affected:
            root_causes.append({
                'type': RootCauseType.RESOURCE_SATURATION.value,
                'description': "Resource saturation detected - insufficient CPU/memory capacity",
                'confidence_score': 0.60 if anomaly.impact_score > 50 else 0.40,
                'timestamp': anomaly.first_detected,
            })
            evidence.append(f"Metric exceeded threshold by {anomaly.impact_score}%")

        # Performance degradation check
        if "latency" in anomaly.metrics_affected or "error" in anomaly.metrics_affected:
            root_causes.append({
                'type': RootCauseType.PERFORMANCE_DEGRADATION.value,
                'description': "Application performance degradation detected",
                'confidence_score': 0.65,
                'timestamp': anomaly.first_detected,
            })
            evidence.append(f"Latency/error rate increased by {anomaly.latency_increase_percent}%")

        # If no clear root cause, mark as unknown
        if not root_causes:
            root_causes.append({
                'type': RootCauseType.UNKNOWN.value,
                'description': "Unable to determine root cause automatically - manual investigation required",
                'confidence_score': 0.30,
                'timestamp': anomaly.first_detected,
            })

        # Sort by confidence
        root_causes.sort(key=lambda x: x['confidence_score'], reverse=True)

        primary_cause_type = RootCauseType(root_causes[0]['type']) if root_causes else RootCauseType.UNKNOWN

        analysis = RootCauseAnalysis(
            analysis_id=f"{workspace_id}:rca:{int(datetime.utcnow().timestamp())}",
            anomaly_id=anomaly_id,
            root_causes=root_causes,
            primary_root_cause=primary_cause_type,
            confidence_score=round(root_causes[0]['confidence_score'], 3) if root_causes else 0.0,
            analysis_timestamp=datetime.utcnow(),
            evidence=evidence,
            related_anomalies=[],
        )

        # Cache
        self.root_causes[anomaly_id] = analysis

        return analysis

    def generate_remediation_plan(
        self,
        workspace_id: str,
        anomaly: AnomalyDetail,
        root_cause: RootCauseAnalysis,
    ) -> List[RemediationAction]:
        """
        Generate remediation plan for anomaly
        
        Args:
            workspace_id: Workspace identifier
            anomaly: Anomaly details
            root_cause: Root cause analysis
            
        Returns:
            List of remediation actions
        """
        actions = []

        # Generate actions based on root cause
        if root_cause.primary_root_cause == RootCauseType.RESOURCE_SATURATION:
            if "cpu" in anomaly.metrics_affected:
                actions.append(
                    RemediationAction(
                        remediation_id=f"{workspace_id}:rem_cpu:{int(datetime.utcnow().timestamp())}",
                        anomaly_id=anomaly.anomaly_id,
                        root_cause_id=root_cause.analysis_id,
                        action_type="scale_cpu",
                        action_description="Scale up CPU resources to handle increased load",
                        severity=anomaly.severity,
                        automatic=False,
                        estimated_resolution_time_minutes=30,
                        risk_level="low",
                        steps=[
                            "Review current CPU allocation",
                            "Determine new CPU requirement",
                            "Schedule maintenance window",
                            "Apply CPU scaling",
                            "Monitor metrics post-scaling",
                        ],
                        rollback_plan="Scale down to previous CPU allocation if performance doesn't improve",
                        status=RemediationStatus.PENDING,
                        initiated_at=None,
                        completed_at=None,
                        result_notes="",
                    )
                )

            if "memory" in anomaly.metrics_affected:
                actions.append(
                    RemediationAction(
                        remediation_id=f"{workspace_id}:rem_mem:{int(datetime.utcnow().timestamp())}",
                        anomaly_id=anomaly.anomaly_id,
                        root_cause_id=root_cause.analysis_id,
                        action_type="scale_memory",
                        action_description="Increase memory allocation to prevent OOM conditions",
                        severity=anomaly.severity,
                        automatic=anomaly.severity == AnomalySeverity.CRITICAL,
                        estimated_resolution_time_minutes=20,
                        risk_level="low",
                        steps=[
                            "Identify memory leak sources if present",
                            "Calculate required memory increase",
                            "Add buffer for growth (20%)",
                            "Apply memory scaling",
                            "Monitor for memory pressure",
                        ],
                        rollback_plan="Revert to previous memory allocation",
                        status=RemediationStatus.PENDING,
                        initiated_at=None,
                        completed_at=None,
                        result_notes="",
                    )
                )

        elif root_cause.primary_root_cause == RootCauseType.CONFIG_CHANGE:
            actions.append(
                RemediationAction(
                    remediation_id=f"{workspace_id}:rem_config:{int(datetime.utcnow().timestamp())}",
                    anomaly_id=anomaly.anomaly_id,
                    root_cause_id=root_cause.analysis_id,
                    action_type="rollback_config",
                    action_description="Rollback recent configuration change that caused anomaly",
                    severity=anomaly.severity,
                    automatic=False,
                    estimated_resolution_time_minutes=15,
                    risk_level="medium",
                    steps=[
                        "Identify recent config changes",
                        "Review change details and impact",
                        "Create backup of current config",
                        "Rollback to previous config",
                        "Validate system behavior",
                        "Schedule config review meeting",
                    ],
                    rollback_plan="Re-apply config changes if anomaly was unrelated",
                    status=RemediationStatus.PENDING,
                    initiated_at=None,
                    completed_at=None,
                    result_notes="",
                )
            )

        # Cache actions
        for action in actions:
            self.remediations[action.remediation_id] = action

        return actions

    def detect_anomaly_patterns(
        self,
        workspace_id: str,
        lookback_days: int = 30,
    ) -> List[AnomalyPattern]:
        """
        Detect recurring anomaly patterns
        
        Args:
            workspace_id: Workspace identifier
            lookback_days: Days of history to analyze
            
        Returns:
            List of detected patterns
        """
        patterns = []

        anomalies = self.detected_anomalies.get(workspace_id, [])

        # Group anomalies by metric
        by_metric = {}
        for anomaly in anomalies:
            for metric in anomaly.metrics_affected:
                if metric not in by_metric:
                    by_metric[metric] = []
                by_metric[metric].append(anomaly)

        # Detect patterns
        for metric, anomaly_list in by_metric.items():
            if len(anomaly_list) < 3:
                continue  # Need at least 3 occurrences

            # Sort by timestamp
            anomaly_list.sort(key=lambda x: x.first_detected)

            # Calculate time differences
            intervals = []
            for i in range(1, len(anomaly_list)):
                interval = (anomaly_list[i].first_detected - anomaly_list[i-1].first_detected).days
                intervals.append(interval)

            avg_interval = np.mean(intervals) if intervals else 0
            interval_std = np.std(intervals) if len(intervals) > 1 else 0

            # Classify frequency
            if avg_interval <= 1:
                frequency = "daily"
            elif avg_interval <= 7:
                frequency = "weekly"
            elif avg_interval <= 30:
                frequency = "monthly"
            else:
                frequency = "quarterly"

            # Check if seasonal (same hour/day of week)
            is_seasonal = self._check_seasonality(anomaly_list)

            # Calculate average duration
            avg_duration = np.mean([a.duration_hours for a in anomaly_list]) if anomaly_list else 0

            # Determine if there's a known root cause
            known_root_cause = None
            if metric in ['cpu', 'memory']:
                known_root_cause = RootCauseType.RESOURCE_SATURATION
            elif metric in ['latency', 'error_rate']:
                known_root_cause = RootCauseType.PERFORMANCE_DEGRADATION

            recommendation = self._generate_pattern_recommendation(metric, frequency, known_root_cause)

            pattern = AnomalyPattern(
                pattern_id=f"{workspace_id}:pattern_{metric}:{int(datetime.utcnow().timestamp())}",
                pattern_name=f"Recurring {metric} anomaly",
                metrics_involved=[metric],
                occurrence_frequency=frequency,
                last_occurrence=anomaly_list[-1].first_detected,
                occurrences_count=len(anomaly_list),
                average_duration_hours=avg_duration,
                average_impact_score=np.mean([a.impact_score for a in anomaly_list]),
                seasonal=is_seasonal,
                root_cause=known_root_cause,
                recommended_solution=recommendation,
            )

            patterns.append(pattern)

        # Cache patterns
        self.patterns[workspace_id] = {p.pattern_id: p for p in patterns}

        return patterns

    def _check_seasonality(self, anomalies: List[AnomalyDetail]) -> bool:
        """Check if anomalies follow seasonal pattern"""
        if len(anomalies) < 4:
            return False

        hours = [a.first_detected.hour for a in anomalies]
        weekdays = [a.first_detected.weekday() for a in anomalies]

        hour_variance = len(set(hours)) == 1
        weekday_pattern = len(set(weekdays)) <= 2

        return hour_variance or weekday_pattern

    def _generate_pattern_recommendation(
        self,
        metric: str,
        frequency: str,
        root_cause: Optional[RootCauseType],
    ) -> str:
        """Generate recommendation for anomaly pattern"""
        if root_cause == RootCauseType.RESOURCE_SATURATION:
            return f"Permanently increase {metric} capacity to prevent recurring anomalies"
        elif root_cause == RootCauseType.PERFORMANCE_DEGRADATION:
            return f"Analyze and optimize application performance for {metric}"
        elif frequency == "daily":
            return f"Implement daily scheduled maintenance or auto-scaling for {metric}"
        elif frequency == "weekly":
            return f"Implement weekly auto-scaling policy for {metric}"
        else:
            return f"Monitor {metric} pattern and implement preventive measures"

    def calculate_health_score(
        self,
        workspace_id: str,
        anomaly_details: Dict,
    ) -> HealthScore:
        """
        Calculate overall system health score
        
        Args:
            workspace_id: Workspace identifier
            anomaly_details: Anomaly statistics
            
        Returns:
            Health score
        """
        metrics_analyzed = anomaly_details.get('metrics_analyzed', 0)
        anomalies_detected = anomaly_details.get('total_anomalies', 0)
        critical_anomalies = anomaly_details.get('critical_anomalies', 0)

        # Score calculation (0-100)
        base_score = 100
        
        # Deduct for anomalies
        anomaly_penalty = min(40, anomalies_detected * 2)
        critical_penalty = min(30, critical_anomalies * 10)
        
        score = max(0, 100 - anomaly_penalty - critical_penalty)

        # Determine status
        if score >= 80:
            status = "healthy"
            trend = "improving"
        elif score >= 60:
            status = "degraded"
            trend = "stable"
        else:
            status = "critical"
            trend = "degrading"

        health = HealthScore(
            workspace_id=workspace_id,
            score=round(score, 1),
            status=status,
            metrics_analyzed=metrics_analyzed,
            anomalies_detected=anomalies_detected,
            critical_anomalies=critical_anomalies,
            trend=trend,
            last_updated=datetime.utcnow(),
        )

        # Cache
        self.health_scores[workspace_id] = health

        return health
