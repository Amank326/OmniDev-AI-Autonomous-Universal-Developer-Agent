"""
Performance Analytics Service
System-level performance metrics and resource utilization analysis.
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import RLock
from collections import deque
import uuid
import statistics


class PerformanceMetricType(Enum):
    """Types of performance metrics."""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    GPU_MEMORY = "gpu_memory"
    NETWORK_BANDWIDTH = "network_bandwidth"
    DISK_IO = "disk_io"
    QUEUE_LENGTH = "queue_length"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"


class ResourceType(Enum):
    """Resource types."""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    NETWORK = "network"
    DISK = "disk"


class BottleneckType(Enum):
    """Types of performance bottlenecks."""
    CPU_BOUND = "cpu_bound"
    MEMORY_BOUND = "memory_bound"
    IO_BOUND = "io_bound"
    NETWORK_BOUND = "network_bound"
    GPU_BOUND = "gpu_bound"


@dataclass
class ResourceUtilization:
    """Current resource utilization."""
    timestamp: datetime
    resource_type: ResourceType
    utilization_percent: float
    absolute_value: float
    unit: str


@dataclass
class LatencyProfile:
    """Latency breakdown for request processing."""
    request_id: str
    timestamp: datetime
    total_latency_ms: float
    queue_wait_ms: float
    preprocessing_ms: float
    model_inference_ms: float
    postprocessing_ms: float
    network_overhead_ms: float
    other_ms: float


@dataclass
class ThroughputMetrics:
    """Throughput measurements."""
    timestamp: datetime
    requests_per_second: float
    successful_requests: int
    failed_requests: int
    total_tokens_processed: int
    total_data_bytes: int
    period_seconds: float


@dataclass
class PerformanceBottleneck:
    """Identified performance bottleneck."""
    bottleneck_id: str
    detected_at: datetime
    bottleneck_type: BottleneckType
    affected_models: List[str]
    metrics: Dict[str, float]
    severity: str  # "low" | "medium" | "high" | "critical"
    description: str
    recommendation: str


@dataclass
class PerformanceOptimization:
    """Performance optimization opportunity."""
    optimization_id: str
    identified_at: datetime
    bottleneck_id: str
    optimization_type: str
    estimated_improvement_percent: float
    estimated_cost: float
    implementation_effort: str  # "low" | "medium" | "high"
    priority: str  # "low" | "medium" | "high" | "critical"
    description: str


@dataclass
class EndToEndLatency:
    """Request end-to-end latency breakdown."""
    request_id: str
    model_id: str
    batch_size: int
    latency_percentiles: Dict[str, float]  # {p50, p95, p99: latency_ms}
    upstream_latency_ms: float
    model_latency_ms: float
    downstream_latency_ms: float


@dataclass
class SystemHealthScore:
    """Overall system health score."""
    timestamp: datetime
    overall_score: float  # 0-100
    cpu_health: float
    memory_health: float
    gpu_health: float
    network_health: float
    model_health: float
    trend: str  # "improving" | "degrading" | "stable"
    critical_issues: List[str]


class PerformanceAnalyticsService:
    """Service for system-level performance analytics."""

    def __init__(self, max_observations: int = 100000):
        """Initialize service."""
        self._lock = RLock()
        self.max_observations = max_observations
        
        # Storage
        self.resource_history: Dict[ResourceType, deque] = {
            resource_type: deque(maxlen=max_observations)
            for resource_type in ResourceType
        }
        self.latency_profiles: deque = deque(maxlen=max_observations)
        self.throughput_history: deque = deque(maxlen=10000)
        self.bottlenecks: Dict[str, PerformanceBottleneck] = {}
        self.optimizations: Dict[str, PerformanceOptimization] = {}
        self.health_history: deque = deque(maxlen=1000)
        
        # Event callbacks
        self.callbacks: Dict[str, List] = {
            'resource_alert': [],
            'bottleneck_detected': [],
            'optimization_identified': [],
            'health_degraded': []
        }

    def record_resource_utilization(
        self,
        resource_type: ResourceType,
        utilization_percent: float,
        absolute_value: float = 0.0,
        unit: str = "%"
    ) -> str:
        """Record resource utilization measurement."""
        with self._lock:
            util = ResourceUtilization(
                timestamp=datetime.utcnow(),
                resource_type=resource_type,
                utilization_percent=utilization_percent,
                absolute_value=absolute_value,
                unit=unit
            )
            
            self.resource_history[resource_type].append(util)
            
            # Trigger alert if high utilization
            if utilization_percent > 85:
                for callback in self.callbacks['resource_alert']:
                    callback(resource_type, utilization_percent)
            
            return f"{resource_type.value}_{datetime.utcnow().isoformat()}"

    def record_latency_profile(
        self,
        request_id: str,
        total_latency_ms: float,
        queue_wait_ms: float = 0,
        preprocessing_ms: float = 0,
        model_inference_ms: float = 0,
        postprocessing_ms: float = 0,
        network_overhead_ms: float = 0
    ) -> str:
        """Record detailed latency profile."""
        with self._lock:
            other_ms = total_latency_ms - (queue_wait_ms + preprocessing_ms + model_inference_ms + 
                                           postprocessing_ms + network_overhead_ms)
            
            profile = LatencyProfile(
                request_id=request_id,
                timestamp=datetime.utcnow(),
                total_latency_ms=total_latency_ms,
                queue_wait_ms=queue_wait_ms,
                preprocessing_ms=preprocessing_ms,
                model_inference_ms=model_inference_ms,
                postprocessing_ms=postprocessing_ms,
                network_overhead_ms=network_overhead_ms,
                other_ms=max(0, other_ms)
            )
            
            self.latency_profiles.append(profile)
            return request_id

    def record_throughput(
        self,
        requests_per_second: float,
        successful_requests: int,
        failed_requests: int,
        total_tokens: int = 0,
        total_data_bytes: int = 0,
        period_seconds: float = 60.0
    ) -> str:
        """Record throughput metrics."""
        with self._lock:
            metrics = ThroughputMetrics(
                timestamp=datetime.utcnow(),
                requests_per_second=requests_per_second,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                total_tokens_processed=total_tokens,
                total_data_bytes=total_data_bytes,
                period_seconds=period_seconds
            )
            
            self.throughput_history.append(metrics)
            return f"throughput_{datetime.utcnow().isoformat()}"

    def detect_bottlenecks(
        self,
        lookback_minutes: int = 30
    ) -> List[PerformanceBottleneck]:
        """Detect performance bottlenecks."""
        with self._lock:
            bottlenecks = []
            cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
            
            # Analyze CPU bottleneck
            cpu_samples = [util for util in self.resource_history[ResourceType.CPU]
                          if util.timestamp >= cutoff_time]
            if cpu_samples:
                avg_cpu = statistics.mean(util.utilization_percent for util in cpu_samples)
                if avg_cpu > 80:
                    bottleneck = PerformanceBottleneck(
                        bottleneck_id=str(uuid.uuid4()),
                        detected_at=datetime.utcnow(),
                        bottleneck_type=BottleneckType.CPU_BOUND,
                        affected_models=[],  # Would be populated from inference records
                        metrics={"avg_cpu_usage": avg_cpu, "peak_cpu_usage": max(util.utilization_percent for util in cpu_samples)},
                        severity="high" if avg_cpu > 90 else "medium",
                        description=f"CPU utilization averaging {avg_cpu:.1f}% over last {lookback_minutes} minutes",
                        recommendation="Consider model optimization, parallel processing, or hardware upgrade"
                    )
                    bottlenecks.append(bottleneck)
                    self.bottlenecks[bottleneck.bottleneck_id] = bottleneck
                    for callback in self.callbacks['bottleneck_detected']:
                        callback(bottleneck)
            
            # Analyze Memory bottleneck
            mem_samples = [util for util in self.resource_history[ResourceType.MEMORY]
                          if util.timestamp >= cutoff_time]
            if mem_samples:
                avg_mem = statistics.mean(util.utilization_percent for util in mem_samples)
                if avg_mem > 85:
                    bottleneck = PerformanceBottleneck(
                        bottleneck_id=str(uuid.uuid4()),
                        detected_at=datetime.utcnow(),
                        bottleneck_type=BottleneckType.MEMORY_BOUND,
                        affected_models=[],
                        metrics={"avg_memory_usage": avg_mem, "peak_memory_usage": max(util.utilization_percent for util in mem_samples)},
                        severity="high" if avg_mem > 95 else "medium",
                        description=f"Memory utilization averaging {avg_mem:.1f}% over last {lookback_minutes} minutes",
                        recommendation="Reduce batch size, implement memory optimization, or add more RAM"
                    )
                    bottlenecks.append(bottleneck)
                    self.bottlenecks[bottleneck.bottleneck_id] = bottleneck
                    for callback in self.callbacks['bottleneck_detected']:
                        callback(bottleneck)
            
            # Analyze GPU bottleneck
            gpu_samples = [util for util in self.resource_history[ResourceType.GPU]
                          if util.timestamp >= cutoff_time]
            if gpu_samples:
                avg_gpu = statistics.mean(util.utilization_percent for util in gpu_samples)
                if avg_gpu > 90:
                    bottleneck = PerformanceBottleneck(
                        bottleneck_id=str(uuid.uuid4()),
                        detected_at=datetime.utcnow(),
                        bottleneck_type=BottleneckType.GPU_BOUND,
                        affected_models=[],
                        metrics={"avg_gpu_usage": avg_gpu, "peak_gpu_usage": max(util.utilization_percent for util in gpu_samples)},
                        severity="medium",
                        description=f"GPU utilization averaging {avg_gpu:.1f}% over last {lookback_minutes} minutes",
                        recommendation="GPU is fully utilized; consider multi-GPU setup or model sharding"
                    )
                    bottlenecks.append(bottleneck)
                    self.bottlenecks[bottleneck.bottleneck_id] = bottleneck
                    for callback in self.callbacks['bottleneck_detected']:
                        callback(bottleneck)
            
            return bottlenecks

    def identify_optimizations(
        self,
        lookback_minutes: int = 30
    ) -> List[PerformanceOptimization]:
        """Identify performance optimization opportunities."""
        with self._lock:
            optimizations = []
            
            # Detect those bottlenecks first
            bottlenecks = self.detect_bottlenecks(lookback_minutes)
            
            for bottleneck in bottlenecks:
                if bottleneck.bottleneck_type == BottleneckType.CPU_BOUND:
                    opt = PerformanceOptimization(
                        optimization_id=str(uuid.uuid4()),
                        identified_at=datetime.utcnow(),
                        bottleneck_id=bottleneck.bottleneck_id,
                        optimization_type="CPU_OPTIMIZATION",
                        estimated_improvement_percent=25,
                        estimated_cost=0,
                        implementation_effort="medium",
                        priority="high",
                        description="Implement kernel fusion, vectorization, or operator optimization"
                    )
                    optimizations.append(opt)
                    self.optimizations[opt.optimization_id] = opt
                
                elif bottleneck.bottleneck_type == BottleneckType.MEMORY_BOUND:
                    opt = PerformanceOptimization(
                        optimization_id=str(uuid.uuid4()),
                        identified_at=datetime.utcnow(),
                        bottleneck_id=bottleneck.bottleneck_id,
                        optimization_type="MEMORY_OPTIMIZATION",
                        estimated_improvement_percent=30,
                        estimated_cost=0,
                        implementation_effort="medium",
                        priority="high",
                        description="Apply model quantization, pruning, or gradient checkpointing"
                    )
                    optimizations.append(opt)
                    self.optimizations[opt.optimization_id] = opt
                
                elif bottleneck.bottleneck_type == BottleneckType.GPU_BOUND:
                    opt = PerformanceOptimization(
                        optimization_id=str(uuid.uuid4()),
                        identified_at=datetime.utcnow(),
                        bottleneck_id=bottleneck.bottleneck_id,
                        optimization_type="GPU_OPTIMIZATION",
                        estimated_improvement_percent=40,
                        estimated_cost=500,  # Estimated hardware cost
                        implementation_effort="high",
                        priority="medium",
                        description="Add additional GPU, implement model sharding, or use inference acceleration"
                    )
                    optimizations.append(opt)
                    self.optimizations[opt.optimization_id] = opt
            
            # Trigger callbacks
            for opt in optimizations:
                for callback in self.callbacks['optimization_identified']:
                    callback(opt)
            
            return optimizations

    def analyze_latency_distribution(
        self,
        model_id: Optional[str] = None,
        lookback_minutes: int = 60
    ) -> Dict[str, Any]:
        """Analyze latency distribution and bottlenecks."""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
            profiles = [p for p in self.latency_profiles if p.timestamp >= cutoff_time]
            
            if not profiles:
                return {}
            
            total_latencies = [p.total_latency_ms for p in profiles]
            queue_waits = [p.queue_wait_ms for p in profiles]
            preprocessing_times = [p.preprocessing_ms for p in profiles]
            inference_times = [p.model_inference_ms for p in profiles]
            postprocessing_times = [p.postprocessing_ms for p in profiles]
            network_times = [p.network_overhead_ms for p in profiles]
            
            # Find bottleneck phase
            avg_times = {
                "queue_wait": statistics.mean(queue_waits),
                "preprocessing": statistics.mean(preprocessing_times),
                "model_inference": statistics.mean(inference_times),
                "postprocessing": statistics.mean(postprocessing_times),
                "network_overhead": statistics.mean(network_times)
            }
            
            bottleneck_phase = max(avg_times, key=avg_times.get)
            
            return {
                "total_requests": len(profiles),
                "latency_percentiles": {
                    "p50": statistics.median(total_latencies),
                    "p95": sorted(total_latencies)[int(len(total_latencies) * 0.95)],
                    "p99": sorted(total_latencies)[int(len(total_latencies) * 0.99)]
                },
                "phase_breakdown_percent": {
                    "queue_wait": (avg_times["queue_wait"] / statistics.mean(total_latencies) * 100),
                    "preprocessing": (avg_times["preprocessing"] / statistics.mean(total_latencies) * 100),
                    "model_inference": (avg_times["model_inference"] / statistics.mean(total_latencies) * 100),
                    "postprocessing": (avg_times["postprocessing"] / statistics.mean(total_latencies) * 100),
                    "network_overhead": (avg_times["network_overhead"] / statistics.mean(total_latencies) * 100)
                },
                "bottleneck_phase": bottleneck_phase,
                "bottleneck_percentage": (avg_times[bottleneck_phase] / statistics.mean(total_latencies) * 100)
            }

    def get_throughput_trend(
        self,
        lookback_hours: int = 24
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get throughput trends."""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            metrics = [m for m in self.throughput_history if m.timestamp >= cutoff_time]
            
            trend_data = []
            for metric in metrics:
                trend_data.append({
                    "timestamp": metric.timestamp.isoformat(),
                    "requests_per_second": metric.requests_per_second,
                    "success_rate": (metric.successful_requests / (metric.successful_requests + metric.failed_requests) * 100) 
                                   if (metric.successful_requests + metric.failed_requests) > 0 else 0,
                    "tokens_per_second": metric.total_tokens_processed / metric.period_seconds if metric.period_seconds > 0 else 0,
                    "data_gb_per_sec": metric.total_data_bytes / (1024**3) / metric.period_seconds if metric.period_seconds > 0 else 0
                })
            
            return {
                "trend_data": trend_data,
                "avg_rps": statistics.mean(m.requests_per_second for m in metrics) if metrics else 0,
                "peak_rps": max((m.requests_per_second for m in metrics), default=0),
                "min_rps": min((m.requests_per_second for m in metrics), default=0)
            }

    def compute_health_score(self) -> SystemHealthScore:
        """Compute overall system health score."""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(minutes=30)
            
            # CPU health (100 = ideal at 50% utilization)
            cpu_samples = [util.utilization_percent for util in self.resource_history[ResourceType.CPU]
                          if util.timestamp >= cutoff_time]
            cpu_avg = statistics.mean(cpu_samples) if cpu_samples else 50
            cpu_health = max(0, 100 - abs(cpu_avg - 50) * 1.5)
            
            # Memory health (100 = ideal at 60% utilization)
            mem_samples = [util.utilization_percent for util in self.resource_history[ResourceType.MEMORY]
                          if util.timestamp >= cutoff_time]
            mem_avg = statistics.mean(mem_samples) if mem_samples else 60
            mem_health = max(0, 100 - abs(mem_avg - 60) * 2.0)
            
            # GPU health (100 = good utilization 70-90%)
            gpu_samples = [util.utilization_percent for util in self.resource_history[ResourceType.GPU]
                          if util.timestamp >= cutoff_time]
            gpu_avg = statistics.mean(gpu_samples) if gpu_samples else 0
            gpu_health = min(100, (gpu_avg / 80 * 100)) if gpu_samples else 50
            
            # Network health (100 = low utilization)
            net_samples = [util.utilization_percent for util in self.resource_history[ResourceType.NETWORK]
                          if util.timestamp >= cutoff_time]
            net_avg = statistics.mean(net_samples) if net_samples else 0
            net_health = max(0, 100 - net_avg)
            
            # Model health (based on error rate)
            throughput_samples = list(self.throughput_history)[-100:]
            model_health = 100
            if throughput_samples:
                avg_success_rate = statistics.mean(
                    (m.successful_requests / (m.successful_requests + m.failed_requests) * 100)
                    for m in throughput_samples if (m.successful_requests + m.failed_requests) > 0
                )
                model_health = avg_success_rate
            
            # Overall score
            overall_score = statistics.mean([cpu_health, mem_health, gpu_health, net_health, model_health])
            
            # Determine trend (compare with previous score)
            previous_health = self.health_history[-1].overall_score if self.health_history else overall_score
            trend = "improving" if overall_score > previous_health else "degrading" if overall_score < previous_health else "stable"
            
            # Critical issues
            critical_issues = []
            if cpu_health < 30:
                critical_issues.append("CPU under extreme stress")
            if mem_health < 30:
                critical_issues.append("Memory critically low")
            if gpu_health > 95:
                critical_issues.append("GPU fully saturated")
            if model_health < 90:
                critical_issues.append(f"High error rate ({100-model_health:.1f}%)")
            
            score = SystemHealthScore(
                timestamp=datetime.utcnow(),
                overall_score=overall_score,
                cpu_health=cpu_health,
                memory_health=mem_health,
                gpu_health=gpu_health,
                network_health=net_health,
                model_health=model_health,
                trend=trend,
                critical_issues=critical_issues
            )
            
            self.health_history.append(score)
            
            # Trigger alert if degraded
            if overall_score < 60:
                for callback in self.callbacks['health_degraded']:
                    callback(score)
            
            return score

    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        with self._lock:
            return {
                "latency_profiles_tracked": len(self.latency_profiles),
                "throughput_measurements": len(self.throughput_history),
                "bottlenecks_detected": len(self.bottlenecks),
                "optimizations_identified": len(self.optimizations),
                "health_snapshots": len(self.health_history),
                "resource_samples_per_type": {
                    resource_type.value: len(samples)
                    for resource_type, samples in self.resource_history.items()
                }
            }

    def health_check(self) -> Dict[str, Any]:
        """Health check status."""
        with self._lock:
            score = self.compute_health_score()
            return {
                "status": "healthy" if score.overall_score > 70 else "degraded",
                "service": "performance_analytics",
                "health_score": score.overall_score,
                "critical_issues": score.critical_issues,
                "timestamp": datetime.utcnow().isoformat()
            }


# Global service instance
_performance_service: Optional[PerformanceAnalyticsService] = None


def get_performance_service() -> PerformanceAnalyticsService:
    """Get or create service instance."""
    global _performance_service
    if _performance_service is None:
        _performance_service = PerformanceAnalyticsService()
    return _performance_service
