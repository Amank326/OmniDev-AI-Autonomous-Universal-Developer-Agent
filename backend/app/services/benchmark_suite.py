"""
Performance Benchmark Suite
Comprehensive performance testing and regression detection
Phase 41: CI/CD Pipeline & Automated Deployment
"""

import logging
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
from threading import RLock
import statistics

logger = logging.getLogger(__name__)


class BenchmarkCategory(Enum):
    """Benchmark categories"""
    API_LATENCY = "api_latency"
    DATABASE_QUERY = "database_query"
    CACHE_OPERATIONS = "cache_operations"
    AUTHENTICATION = "authentication"
    FILE_OPERATIONS = "file_operations"
    INTEGRATION = "integration"


class BenchmarkStatus(Enum):
    """Benchmark execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RegressionSeverity(Enum):
    """Regression severity levels"""
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    CRITICAL = "critical"


@dataclass
class BenchmarkMetric:
    """Individual benchmark metric"""
    iteration: int
    duration_ms: float
    memory_used_mb: float = 0.0
    cpu_percent: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BenchmarkResult:
    """Results of a benchmark"""
    name: str
    category: BenchmarkCategory
    iterations: int
    status: BenchmarkStatus
    metrics: List[BenchmarkMetric] = field(default_factory=list)
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def get_statistics(self) -> Dict[str, float]:
        """Calculate benchmark statistics"""
        if not self.metrics:
            return {}
        
        durations = [m.duration_ms for m in self.metrics]
        
        return {
            'min_ms': min(durations),
            'max_ms': max(durations),
            'mean_ms': statistics.mean(durations),
            'median_ms': statistics.median(durations),
            'stdev_ms': statistics.stdev(durations) if len(durations) > 1 else 0,
            'p95_ms': sorted(durations)[int(len(durations) * 0.95)],
            'p99_ms': sorted(durations)[int(len(durations) * 0.99)],
            'total_iterations': len(durations),
            'avg_memory_mb': statistics.mean([m.memory_used_mb for m in self.metrics])
        }


@dataclass
class BaselineSnapshot:
    """Baseline metrics for regression detection"""
    timestamp: datetime
    benchmarks: Dict[str, Dict[str, float]]  # benchmark_name -> metrics
    
    def get_baseline_metric(self, benchmark_name: str, metric_type: str) -> Optional[float]:
        """Get baseline metric value"""
        if benchmark_name in self.benchmarks:
            return self.benchmarks[benchmark_name].get(metric_type)
        return None


@dataclass
class RegressionReport:
    """Report of performance regressions"""
    timestamp: datetime
    baseline_snapshot: BaselineSnapshot
    current_results: List[BenchmarkResult]
    regressions: List[Dict[str, Any]] = field(default_factory=list)
    severity: RegressionSeverity = RegressionSeverity.NONE
    regression_count: int = 0
    regression_percentage_increase: float = 0.0


class BenchmarkSuite:
    """Manages and executes benchmarks"""
    
    def __init__(self, regression_threshold_percent: float = 10.0):
        self.regression_threshold = regression_threshold_percent
        self.benchmarks: Dict[str, BenchmarkResult] = {}
        self.baseline: Optional[BaselineSnapshot] = None
        self.history: List[List[BenchmarkResult]] = []
        self.callbacks: List[Callable] = []
        self.lock = RLock()

    def register_benchmark(self, name: str, category: BenchmarkCategory) -> BenchmarkResult:
        """Register a benchmark"""
        result = BenchmarkResult(
            name=name,
            category=category,
            iterations=0,
            status=BenchmarkStatus.PENDING
        )
        
        with self.lock:
            self.benchmarks[name] = result
        
        logger.info(f"Registered benchmark: {name}")
        return result

    def execute_benchmark(self, name: str, benchmark_fn: Callable, 
                         iterations: int = 100, **kwargs) -> BenchmarkResult:
        """Execute a benchmark"""
        with self.lock:
            result = self.benchmarks.get(name)
            if not result:
                logger.error(f"Benchmark {name} not registered")
                return None
        
        logger.info(f"Executing benchmark {name} with {iterations} iterations")
        result.status = BenchmarkStatus.RUNNING
        result.iterations = iterations
        
        try:
            for iteration in range(iterations):
                try:
                    # Measure execution time
                    start_time = time.perf_counter()
                    benchmark_fn(**kwargs)
                    end_time = time.perf_counter()
                    
                    duration_ms = (end_time - start_time) * 1000
                    
                    metric = BenchmarkMetric(
                        iteration=iteration,
                        duration_ms=duration_ms
                    )
                    
                    with self.lock:
                        result.metrics.append(metric)
                
                except Exception as e:
                    logger.error(f"Iteration {iteration} failed: {e}")
                    result.status = BenchmarkStatus.FAILED
                    result.error_message = str(e)
                    return result
            
            result.status = BenchmarkStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            
            # Trigger callbacks
            self._trigger_callbacks(result)
            
            logger.info(f"Benchmark {name} completed: {result.get_statistics()}")
            return result
        
        except Exception as e:
            logger.error(f"Benchmark execution error: {e}")
            result.status = BenchmarkStatus.FAILED
            result.error_message = str(e)
            return result

    def execute_suite(self, benchmark_names: Optional[List[str]] = None, 
                     iterations: int = 100, benchmark_fns: Dict[str, Callable] = None) -> List[BenchmarkResult]:
        """Execute multiple benchmarks"""
        if not benchmark_fns:
            benchmark_fns = {}
        
        if not benchmark_names:
            benchmark_names = list(self.benchmarks.keys())
        
        results = []
        for name in benchmark_names:
            if name in benchmark_fns:
                result = self.execute_benchmark(name, benchmark_fns[name], iterations)
                results.append(result)
        
        with self.lock:
            self.history.append(results)
        
        logger.info(f"Benchmark suite completed: {len(results)} benchmarks")
        return results

    def set_baseline(self, results: List[BenchmarkResult]) -> BaselineSnapshot:
        """Set baseline for regression detection"""
        benchmarks_dict = {}
        
        for result in results:
            stats = result.get_statistics()
            benchmarks_dict[result.name] = stats
        
        self.baseline = BaselineSnapshot(
            timestamp=datetime.utcnow(),
            benchmarks=benchmarks_dict
        )
        
        logger.info(f"Baseline set with {len(benchmarks_dict)} benchmarks")
        return self.baseline

    def detect_regressions(self, current_results: List[BenchmarkResult]) -> RegressionReport:
        """Detect performance regressions"""
        if not self.baseline:
            logger.warning("No baseline set, cannot detect regressions")
            return RegressionReport(
                timestamp=datetime.utcnow(),
                baseline_snapshot=None,
                current_results=current_results
            )
        
        regressions = []
        max_regression = 0.0
        
        for result in current_results:
            current_stats = result.get_statistics()
            baseline_metrics = self.baseline.get_baseline_metric(result.name, 'mean_ms')
            
            if baseline_metrics and 'mean_ms' in current_stats:
                current_mean = current_stats['mean_ms']
                baseline_mean = baseline_metrics
                
                percent_change = ((current_mean - baseline_mean) / baseline_mean) * 100
                
                if percent_change > self.regression_threshold:
                    regressions.append({
                        'benchmark': result.name,
                        'baseline_ms': baseline_mean,
                        'current_ms': current_mean,
                        'percent_change': percent_change,
                        'status': 'REGRESSION'
                    })
                    
                    max_regression = max(max_regression, percent_change)
        
        # Determine severity
        if max_regression >= 50:
            severity = RegressionSeverity.CRITICAL
        elif max_regression >= 25:
            severity = RegressionSeverity.MODERATE
        elif max_regression > 0:
            severity = RegressionSeverity.MINOR
        else:
            severity = RegressionSeverity.NONE
        
        report = RegressionReport(
            timestamp=datetime.utcnow(),
            baseline_snapshot=self.baseline,
            current_results=current_results,
            regressions=regressions,
            severity=severity,
            regression_count=len(regressions),
            regression_percentage_increase=max_regression
        )
        
        logger.info(f"Regression report: {severity.value}, {len(regressions)} regressions detected")
        return report

    def get_benchmark_history(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get benchmark history"""
        history = []
        
        with self.lock:
            for run in self.history[-limit:]:
                for result in run:
                    if result.name == name:
                        stats = result.get_statistics()
                        history.append({
                            'timestamp': result.completed_at.isoformat() if result.completed_at else None,
                            'stats': stats
                        })
        
        return history

    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics"""
        completed = 0
        failed = 0
        total_duration = 0.0
        
        with self.lock:
            for benchmark in self.benchmarks.values():
                if benchmark.status == BenchmarkStatus.COMPLETED:
                    completed += 1
                    stats = benchmark.get_statistics()
                    if 'mean_ms' in stats:
                        total_duration += stats['mean_ms']
                elif benchmark.status == BenchmarkStatus.FAILED:
                    failed += 1
        
        return {
            'total_benchmarks': len(self.benchmarks),
            'completed': completed,
            'failed': failed,
            'pending': len(self.benchmarks) - completed - failed,
            'total_duration_ms': total_duration,
            'regression_threshold_percent': self.regression_threshold
        }

    def export_results(self, results: List[BenchmarkResult], filename: str) -> bool:
        """Export results to file"""
        try:
            export_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'benchmarks': []
            }
            
            for result in results:
                export_data['benchmarks'].append({
                    'name': result.name,
                    'category': result.category.value,
                    'status': result.status.value,
                    'statistics': result.get_statistics()
                })
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Results exported to {filename}")
            return True
        
        except Exception as e:
            logger.error(f"Export error: {e}")
            return False

    def register_callback(self, callback: Callable[[BenchmarkResult], None]) -> None:
        """Register callback for benchmark completion"""
        with self.lock:
            self.callbacks.append(callback)

    def _trigger_callbacks(self, result: BenchmarkResult) -> None:
        """Trigger callbacks"""
        for callback in self.callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Callback error: {e}")


# Global benchmark suite instance
_suite: Optional[BenchmarkSuite] = None


def get_benchmark_suite(regression_threshold: float = 10.0) -> BenchmarkSuite:
    """Get or create benchmark suite instance"""
    global _suite
    if _suite is None:
        _suite = BenchmarkSuite(regression_threshold_percent=regression_threshold)
    return _suite


# Standard benchmark implementations

def api_latency_benchmark(endpoint: str = "http://localhost:5000/api/v1/health") -> None:
    """Benchmark API latency"""
    try:
        import requests
        start = time.perf_counter()
        response = requests.get(endpoint, timeout=5)
        assert response.status_code == 200
    except Exception as e:
        logger.error(f"API latency benchmark error: {e}")
        raise


def database_query_benchmark(query: str = "SELECT 1") -> None:
    """Benchmark database query performance"""
    try:
        import psycopg2
        conn = psycopg2.connect("dbname=omnidev user=postgres")
        cursor = conn.cursor()
        cursor.execute(query)
        cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Database benchmark error: {e}")
        raise


def cache_operation_benchmark(key: str = "test_key", value: str = "test_value") -> None:
    """Benchmark cache operations"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.set(key, value)
        result = r.get(key)
        assert result == value.encode() or result == value
    except Exception as e:
        logger.error(f"Cache benchmark error: {e}")
        raise


def json_serialization_benchmark(data: Dict = None) -> None:
    """Benchmark JSON operations"""
    if data is None:
        data = {
            'id': 1,
            'name': 'test',
            'values': list(range(100)),
            'nested': {'key': 'value'}
        }
    
    serialized = json.dumps(data)
    deserialized = json.loads(serialized)
    assert deserialized == data


def string_operations_benchmark(text: str = "test" * 1000) -> None:
    """Benchmark string operations"""
    result = text.upper().lower().split()
    assert len(result) > 0
