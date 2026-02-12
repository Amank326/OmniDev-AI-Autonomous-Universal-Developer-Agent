"""
Inference Acceleration Service
Handles GPU acceleration, batching, caching, and runtime performance optimization.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
import numpy as np
from threading import RLock
from collections import deque
import time
from datetime import datetime


class AccelerationBackend(Enum):
    """GPU/Acceleration backends"""
    CUDA = "cuda"
    OPENCL = "opencl"
    METAL = "metal"
    VULKAN = "vulkan"
    DIRECTX = "directx"
    OPENVINO = "openvino"
    TENSORRT = "tensorrt"


class CachingStrategy(Enum):
    """Inference result caching strategies"""
    LRU = "lru"                          # Least Recently Used
    LFU = "lfu"                          # Least Frequently Used
    FIFO = "fifo"                        # First In First Out
    SEMANTIC = "semantic"                # Semantic similarity-based
    ADAPTIVE = "adaptive"                # Adaptive based on access patterns


class BatchingStrategy(Enum):
    """Request batching strategies"""
    IMMEDIATE = "immediate"              # Batch immediately available requests
    ADAPTIVE = "adaptive"                # Adaptive batching by latency
    TIME_WINDOW = "time_window"          # Batch within time window
    PRIORITY = "priority"                # Priority-based batching


class PerformanceProfiler(Enum):
    """Performance profiling modes"""
    DISABLED = "disabled"
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass
class CacheConfig:
    """Cache configuration"""
    strategy: CachingStrategy
    max_entries: int = 10000
    max_size_mb: int = 512
    ttl_seconds: int = 3600
    enable_semantic_caching: bool = False
    similarity_threshold: float = 0.95


@dataclass
class BatchingConfig:
    """Batching configuration"""
    strategy: BatchingStrategy
    max_batch_size: int = 32
    max_wait_time_ms: int = 100
    min_batch_size: int = 1
    target_latency_ms: float = 50.0
    enable_dynamic_batching: bool = True


@dataclass
class AccelerationConfig:
    """Acceleration configuration"""
    backend: AccelerationBackend
    gpu_id: int = 0
    enable_fp16: bool = False
    enable_tf32: bool = False
    enable_graph_capture: bool = False
    kernel_cache_size_mb: int = 256
    memory_pool_size_mb: int = 1024
    enable_async_execution: bool = True


@dataclass
class InferenceProfile:
    """Per-inference performance profile"""
    request_id: str
    model_id: str
    model_version: int
    batch_size: int
    input_size_bytes: int
    output_size_bytes: int
    total_latency_ms: float
    compute_latency_ms: float
    memory_latency_ms: float
    io_latency_ms: float
    cache_hit: bool
    accelerator_used: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CachedInference:
    """Cached inference result"""
    cache_key: str
    input_hash: str
    output_data: np.ndarray
    output_metadata: Dict[str, Any]
    timestamp: datetime
    access_count: int = 0
    last_access: Optional[datetime] = None


@dataclass
class AccelerationStats:
    """Acceleration service statistics"""
    total_inferences: int
    cache_hits: int
    cache_misses: int
    batched_requests: int
    avg_batch_size: float
    avg_total_latency_ms: float
    avg_compute_latency_ms: float
    memory_latency_ms: float
    cache_hit_rate_percent: float
    gpu_utilization_percent: float
    memory_utilization_percent: float
    batching_efficiency_percent: float


class InferenceAccelerationService:
    """
    Runtime inference acceleration service.
    Provides GPU acceleration, intelligent caching, request batching,
    and performance profiling for low-latency inference.
    """

    def __init__(
        self,
        cache_config: Optional[CacheConfig] = None,
        batching_config: Optional[BatchingConfig] = None,
        acceleration_config: Optional[AccelerationConfig] = None
    ):
        """Initialize acceleration service"""
        self.cache_config = cache_config or CacheConfig(strategy=CachingStrategy.LRU)
        self.batching_config = batching_config or BatchingConfig(strategy=BatchingStrategy.ADAPTIVE)
        self.acceleration_config = acceleration_config or AccelerationConfig(backend=AccelerationBackend.CUDA)

        # Cache management
        self.inference_cache: Dict[str, CachedInference] = {}
        self.cache_order: deque = deque()  # For LRU/FIFO
        self.cache_frequency: Dict[str, int] = {}  # For LFU

        # Batching
        self.request_queue: deque = deque()
        self.active_batches: Dict[str, List[Dict[str, Any]]] = {}
        self.batch_counter: int = 0

        # Profiling
        self.inference_profiles: deque = deque(maxlen=100000)
        self.model_profiles: Dict[str, List[InferenceProfile]] = {}
        self.performance_tracker: Dict[str, Any] = {}

        # State
        self.lock = RLock()
        self.gpu_memory_used_mb: float = 0.0
        self.gpu_memory_total_mb: float = self.acceleration_config.memory_pool_size_mb

        # Callbacks
        self.callbacks: Dict[str, Callable] = {
            'inference_completed': None,
            'batch_created': None,
            'cache_hit': None,
            'cache_miss': None,
            'acceleration_ready': None
        }

    def submit_inference_request(
        self,
        request_id: str,
        model_id: str,
        model_version: int,
        input_data: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit inference request for acceleration.
        
        Returns:
            Response with status, result or queue info
        """
        with self.lock:
            # Check cache
            cache_key = self._compute_cache_key(model_id, model_version, input_data)
            cached_result = self._check_cache(cache_key)

            if cached_result:
                self._trigger_callback('cache_hit', {
                    'request_id': request_id,
                    'model_id': model_id,
                    'cache_key': cache_key
                })

                return {
                    'request_id': request_id,
                    'status': 'completed',
                    'source': 'cache',
                    'output': cached_result.output_data,
                    'output_metadata': cached_result.output_metadata,
                    'latency_ms': 1.0
                }

            self._trigger_callback('cache_miss', {
                'request_id': request_id,
                'model_id': model_id
            })

            # Add to batching queue
            request_entry = {
                'request_id': request_id,
                'model_id': model_id,
                'model_version': model_version,
                'input_data': input_data,
                'metadata': metadata or {},
                'cache_key': cache_key,
                'submit_time': time.time()
            }

            self.request_queue.append(request_entry)

            # Check if batch ready
            batch_id = self._check_batch_ready()

            return {
                'request_id': request_id,
                'status': 'queued',
                'queue_position': len(self.request_queue),
                'batch_id': batch_id
            }

    def execute_batch(
        self,
        batch_id: str,
        requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute batch of inference requests on accelerator.
        
        Returns:
            Batch execution result with per-request outputs
        """
        with self.lock:
            if not requests:
                return {'batch_id': batch_id, 'results': []}

            batch_start_time = time.time()
            results = []

            # Extract batch inputs
            batch_inputs = np.stack([r['input_data'] for r in requests])
            batch_size = len(requests)

            # Simulate GPU acceleration
            compute_start = time.time()
            batch_outputs = self._accelerated_inference(
                batch_inputs,
                requests[0]['model_id'],
                requests[0]['model_version']
            )
            compute_time = (time.time() - compute_start) * 1000  # Convert to ms

            # Process results
            for idx, request in enumerate(requests):
                request_id = request['request_id']
                output = batch_outputs[idx] if batch_outputs is not None else None

                # Cache result
                if output is not None:
                    cache_entry = CachedInference(
                        cache_key=request['cache_key'],
                        input_hash=str(hash(request['input_data'].tobytes())),
                        output_data=output,
                        output_metadata={'batch_id': batch_id, 'batch_position': idx},
                        timestamp=datetime.utcnow()
                    )
                    self._store_in_cache(cache_entry)

                result = {
                    'request_id': request_id,
                    'batch_id': batch_id,
                    'status': 'completed' if output is not None else 'failed',
                    'output': output,
                    'latency_ms': compute_time / batch_size
                }

                results.append(result)

                # Record profile
                profile = InferenceProfile(
                    request_id=request_id,
                    model_id=request['model_id'],
                    model_version=request['model_version'],
                    batch_size=batch_size,
                    input_size_bytes=request['input_data'].nbytes,
                    output_size_bytes=output.nbytes if output is not None else 0,
                    total_latency_ms=compute_time / batch_size,
                    compute_latency_ms=compute_time / batch_size,
                    memory_latency_ms=0.5,
                    io_latency_ms=0.1,
                    cache_hit=False,
                    accelerator_used=self.acceleration_config.backend.value
                )
                self.inference_profiles.append(profile)
                self._record_model_profile(profile)

                # Trigger callback
                self._trigger_callback('inference_completed', {
                    'request_id': request_id,
                    'batch_id': batch_id,
                    'latency_ms': compute_time / batch_size
                })

            # Update batch tracking
            batch_duration = (time.time() - batch_start_time) * 1000
            self.active_batches[batch_id] = results

            self._trigger_callback('batch_created', {
                'batch_id': batch_id,
                'batch_size': batch_size,
                'duration_ms': batch_duration
            })

            return {
                'batch_id': batch_id,
                'batch_size': batch_size,
                'results': results,
                'total_latency_ms': batch_duration
            }

    def get_acceleration_status(self) -> Dict[str, Any]:
        """Get current acceleration service status"""
        with self.lock:
            return {
                'backend': self.acceleration_config.backend.value,
                'gpu_id': self.acceleration_config.gpu_id,
                'gpu_memory_used_mb': self.gpu_memory_used_mb,
                'gpu_memory_total_mb': self.gpu_memory_total_mb,
                'gpu_memory_utilization_percent': (
                    self.gpu_memory_used_mb / self.gpu_memory_total_mb * 100
                    if self.gpu_memory_total_mb > 0 else 0
                ),
                'pending_requests': len(self.request_queue),
                'active_batches': len(self.active_batches),
                'cache_size_entries': len(self.inference_cache),
                'queue_config': {
                    'batching_strategy': self.batching_config.strategy.value,
                    'max_batch_size': self.batching_config.max_batch_size,
                    'cache_strategy': self.cache_config.strategy.value
                }
            }

    def clear_cache(self, model_id: Optional[str] = None) -> int:
        """
        Clear inference cache.
        
        Returns:
            Number of entries cleared
        """
        with self.lock:
            if model_id:
                # Clear cache for specific model
                keys_to_remove = [k for k in self.inference_cache.keys() if model_id in k]
                for k in keys_to_remove:
                    del self.inference_cache[k]
                    self.cache_order.discard(k)
                return len(keys_to_remove)
            else:
                # Clear all cache
                cleared = len(self.inference_cache)
                self.inference_cache.clear()
                self.cache_order.clear()
                self.cache_frequency.clear()
                return cleared

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_accesses = sum(self.cache_frequency.values())
            hits = sum(1 for e in self.inference_cache.values() if e.access_count > 0)
            
            return {
                'cache_entries': len(self.inference_cache),
                'max_entries': self.cache_config.max_entries,
                'total_cache_accesses': total_accesses,
                'cache_hits': hits,
                'hit_rate_percent': (hits / total_accesses * 100) if total_accesses > 0 else 0,
                'avg_entry_age_seconds': self._calculate_avg_age(),
                'strategy': self.cache_config.strategy.value
            }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        with self.lock:
            if not self.inference_profiles:
                return {}

            recent_profiles = list(self.inference_profiles)[-1000:]  # Last 1000

            latencies = [p.total_latency_ms for p in recent_profiles]
            compute_latencies = [p.compute_latency_ms for p in recent_profiles]
            batches_processed = len(set(p.batch_size for p in recent_profiles))

            return {
                'total_inferences': len(self.inference_profiles),
                'recent_inferences': len(recent_profiles),
                'avg_latency_ms': float(np.mean(latencies)) if latencies else 0.0,
                'p50_latency_ms': float(np.percentile(latencies, 50)) if latencies else 0.0,
                'p95_latency_ms': float(np.percentile(latencies, 95)) if latencies else 0.0,
                'p99_latency_ms': float(np.percentile(latencies, 99)) if latencies else 0.0,
                'avg_compute_latency_ms': float(np.mean(compute_latencies)) if compute_latencies else 0.0,
                'avg_batch_size': float(np.mean([p.batch_size for p in recent_profiles])) if recent_profiles else 0.0,
                'batches_processed': batches_processed,
                'backend': self.acceleration_config.backend.value
            }

    def get_model_performance(self, model_id: str) -> Dict[str, Any]:
        """Get performance statistics for specific model"""
        with self.lock:
            if model_id not in self.model_profiles:
                return {}

            profiles = self.model_profiles[model_id]
            if not profiles:
                return {}

            latencies = [p.total_latency_ms for p in profiles]

            return {
                'model_id': model_id,
                'total_inferences': len(profiles),
                'avg_latency_ms': float(np.mean(latencies)),
                'p50_latency_ms': float(np.percentile(latencies, 50)),
                'p99_latency_ms': float(np.percentile(latencies, 99)),
                'avg_batch_size': float(np.mean([p.batch_size for p in profiles])),
                'total_data_processed_mb': float(np.sum([p.input_size_bytes for p in profiles]) / 1024 / 1024)
            }

    def health_check(self) -> Dict[str, Any]:
        """Health check for acceleration service"""
        with self.lock:
            return {
                'status': 'healthy',
                'backend': self.acceleration_config.backend.value,
                'gpu_available': True,
                'memory_available': self.gpu_memory_used_mb < self.gpu_memory_total_mb * 0.9,
                'queue_healthy': len(self.request_queue) < 100000,
                'cache_healthy': len(self.inference_cache) < self.cache_config.max_entries * 0.95,
                'timestamp': datetime.utcnow().isoformat()
            }

    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register callback for acceleration events"""
        if event_type in self.callbacks:
            self.callbacks[event_type] = callback

    # Private methods
    def _compute_cache_key(
        self,
        model_id: str,
        model_version: int,
        input_data: np.ndarray
    ) -> str:
        """Compute cache key from input"""
        input_hash = hash(input_data.tobytes())
        return f"{model_id}_{model_version}_{input_hash}"

    def _check_cache(self, cache_key: str) -> Optional[CachedInference]:
        """Check if result exists in cache"""
        if cache_key not in self.inference_cache:
            return None

        cached = self.inference_cache[cache_key]

        # Check TTL
        age_seconds = (datetime.utcnow() - cached.timestamp).total_seconds()
        if age_seconds > self.cache_config.ttl_seconds:
            del self.inference_cache[cache_key]
            return None

        # Update access info
        cached.access_count += 1
        cached.last_access = datetime.utcnow()
        self.cache_frequency[cache_key] = self.cache_frequency.get(cache_key, 0) + 1

        return cached

    def _store_in_cache(self, entry: CachedInference) -> None:
        """Store inference result in cache"""
        if len(self.inference_cache) >= self.cache_config.max_entries:
            self._evict_cache_entry()

        self.inference_cache[entry.cache_key] = entry
        self.cache_order.append(entry.cache_key)
        self.cache_frequency[entry.cache_key] = 1

    def _evict_cache_entry(self) -> None:
        """Evict entry from cache based on strategy"""
        if not self.inference_cache:
            return

        if self.cache_config.strategy == CachingStrategy.LRU:
            # Remove least recently used
            if self.cache_order:
                key_to_remove = self.cache_order[0]
                if key_to_remove in self.inference_cache:
                    del self.inference_cache[key_to_remove]

        elif self.cache_config.strategy == CachingStrategy.LFU:
            # Remove least frequently used
            min_key = min(self.cache_frequency, key=self.cache_frequency.get)
            if min_key in self.inference_cache:
                del self.inference_cache[min_key]
                del self.cache_frequency[min_key]

    def _check_batch_ready(self) -> Optional[str]:
        """Check if batch is ready for execution"""
        if len(self.request_queue) >= self.batching_config.max_batch_size:
            batch_id = f"batch_{self.batch_counter}_{int(time.time())}"
            self.batch_counter += 1
            return batch_id
        return None

    def _accelerated_inference(
        self,
        batch_input: np.ndarray,
        model_id: str,
        model_version: int
    ) -> np.ndarray:
        """Execute inference using acceleration backend"""
        # Simulate GPU inference
        batch_size = batch_input.shape[0]
        output_shape = (batch_size, 64)  # Mock output shape
        return np.random.randn(*output_shape).astype(np.float32)

    def _record_model_profile(self, profile: InferenceProfile) -> None:
        """Record inference profile for model"""
        if profile.model_id not in self.model_profiles:
            self.model_profiles[profile.model_id] = deque(maxlen=10000)
        self.model_profiles[profile.model_id].append(profile)

    def _calculate_avg_age(self) -> float:
        """Calculate average age of cache entries"""
        if not self.inference_cache:
            return 0.0
        ages = [
            (datetime.utcnow() - e.timestamp).total_seconds()
            for e in self.inference_cache.values()
        ]
        return float(np.mean(ages)) if ages else 0.0

    def _trigger_callback(self, event_type: str, data: Dict[str, Any]) -> None:
        """Trigger event callback"""
        if event_type in self.callbacks and self.callbacks[event_type]:
            try:
                self.callbacks[event_type](data)
            except Exception as e:
                print(f"Error triggering callback for {event_type}: {e}")
