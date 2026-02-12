"""
ML Model Serving Service
Handles model loading, inference execution, caching, and performance monitoring.
Supports multiple ML frameworks (TensorFlow, PyTorch, Scikit-learn, ONNX).
"""

import asyncio
import json
import logging
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from abc import ABC, abstractmethod
from threading import RLock
import numpy as np
from collections import deque
import struct

logger = logging.getLogger(__name__)


# ===================== ENUMS =====================

class ServingBackend(Enum):
    """Supported ML framework backends"""
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    SKLEARN = "sklearn"
    ONNX = "onnx"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    CUSTOM = "custom"


class InferenceStatus(Enum):
    """Status of inference request"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ModelLoadStatus(Enum):
    """Model loading status"""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    FAILED = "failed"


class PredictionType(Enum):
    """Type of prediction output"""
    CLASSIFICATION = "classification"  # Discrete labels
    REGRESSION = "regression"  # Continuous values
    CLUSTERING = "clustering"  # Cluster assignments
    RANKING = "ranking"  # Ranked items
    SEQUENCE = "sequence"  # Sequence output
    EMBEDDING = "embedding"  # Vector embeddings


class LatencyBucket(Enum):
    """Latency histogram buckets (milliseconds)"""
    FAST = 10  # < 10ms
    MEDIUM = 50  # 10-50ms
    SLOW = 100  # 50-100ms
    VERY_SLOW = 500  # 100-500ms
    TIMEOUT = 1000  # > 500ms


# ===================== DATACLASSES =====================

@dataclass
class InferenceInput:
    """Inference input data"""
    request_id: str
    model_id: str
    model_version: int
    features: Dict[str, Any]
    batch_id: Optional[str] = None
    priority: int = 0  # 0=normal, 1=high, -1=low
    timeout_ms: float = 30000
    return_confidence: bool = False
    return_embedding: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceOutput:
    """Inference output result"""
    request_id: str
    model_id: str
    model_version: int
    prediction: Any
    prediction_type: PredictionType
    confidence_scores: Optional[Dict[str, float]] = None
    latency_ms: float = 0.0
    served_by_replica: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())


@dataclass
class ModelCache:
    """Cached model instance"""
    model_id: str
    model_version: int
    backend: ServingBackend
    model_object: Any
    artifact_path: str
    loaded_at: float
    last_access_at: float
    access_count: int = 0
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceRequest:
    """Queued inference request"""
    request_id: str
    inference_input: InferenceInput
    created_at: float
    status: InferenceStatus = InferenceStatus.QUEUED
    result: Optional[InferenceOutput] = None
    error_message: Optional[str] = None
    processing_started_at: Optional[float] = None
    processing_completed_at: Optional[float] = None


@dataclass
class PerformanceMetrics:
    """Model serving performance metrics"""
    model_id: str
    model_version: int
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    mean_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    throughput_rps: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


@dataclass
class BatchInferenceJob:
    """Batch inference job"""
    batch_id: str
    model_id: str
    model_version: int
    requests: List[InferenceRequest] = field(default_factory=list)
    results: Dict[str, InferenceOutput] = field(default_factory=dict)
    status: InferenceStatus = InferenceStatus.QUEUED
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    completed_at: Optional[float] = None


@dataclass
class ModelServingConfig:
    """Configuration for model serving"""
    model_id: str
    model_version: int
    backend: ServingBackend
    artifact_path: str
    workspace_id: str
    prediction_type: PredictionType
    batch_size: int = 32
    max_queue_size: int = 1000
    inference_timeout_ms: float = 30000
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    enable_batching: bool = True
    batch_timeout_ms: float = 100
    enable_gpu: bool = True
    num_replicas: int = 1
    min_batch_size: int = 1


@dataclass
class ModelReplica:
    """Model serving replica instance"""
    replica_id: str
    model_id: str
    model_version: int
    status: ModelLoadStatus = ModelLoadStatus.NOT_LOADED
    model_cache: Optional[ModelCache] = None
    processed_requests: int = 0
    active_requests: int = 0
    avg_latency_ms: float = 0.0
    error_count: int = 0
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    last_heartbeat: float = field(default_factory=lambda: datetime.utcnow().timestamp())


@dataclass
class InferenceRouting:
    """Routing decision for inference"""
    replica_id: str
    model_version: int
    backend: ServingBackend
    load_score: float  # 0-1, lower is better
    estimated_latency_ms: float
    available_capacity: int


# ===================== MODEL LOADING BACKENDS =====================

class ModelBackend(ABC):
    """Abstract base class for model backends"""
    
    @abstractmethod
    def load_model(self, artifact_path: str) -> Any:
        """Load model from artifact"""
        pass
    
    @abstractmethod
    def unload_model(self, model: Any) -> None:
        """Unload model from memory"""
        pass
    
    @abstractmethod
    def predict(self, model: Any, features: Dict[str, Any]) -> Any:
        """Run inference"""
        pass
    
    @abstractmethod
    def get_model_size(self, model: Any) -> int:
        """Get model size in bytes"""
        pass


class TensorFlowBackend(ModelBackend):
    """TensorFlow model backend"""
    
    def load_model(self, artifact_path: str) -> Any:
        try:
            import tensorflow as tf
            return tf.keras.models.load_model(artifact_path)
        except Exception as e:
            logger.error(f"Failed to load TensorFlow model: {e}")
            raise
    
    def unload_model(self, model: Any) -> None:
        del model
    
    def predict(self, model: Any, features: Dict[str, Any]) -> Any:
        import numpy as np
        # Convert dict to array based on model input signature
        if isinstance(features, dict):
            input_data = np.array([list(features.values())])
        else:
            input_data = np.array([features])
        
        predictions = model.predict(input_data, verbose=0)
        return predictions[0].tolist() if hasattr(predictions, 'tolist') else predictions
    
    def get_model_size(self, model: Any) -> int:
        import os
        total_size = 0
        for weight in model.weights:
            total_size += weight.numpy().nbytes
        return total_size


class PyTorchBackend(ModelBackend):
    """PyTorch model backend"""
    
    def load_model(self, artifact_path: str) -> Any:
        try:
            import torch
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model = torch.load(artifact_path, map_location=device)
            model.eval()
            return model
        except Exception as e:
            logger.error(f"Failed to load PyTorch model: {e}")
            raise
    
    def unload_model(self, model: Any) -> None:
        del model
    
    def predict(self, model: Any, features: Dict[str, Any]) -> Any:
        import torch
        try:
            device = next(model.parameters()).device
            if isinstance(features, dict):
                input_data = torch.tensor([list(features.values())], dtype=torch.float32).to(device)
            else:
                input_data = torch.tensor([features], dtype=torch.float32).to(device)
            
            with torch.no_grad():
                output = model(input_data)
            
            return output[0].cpu().numpy().tolist() if hasattr(output, 'cpu') else output
        except Exception as e:
            logger.error(f"PyTorch inference failed: {e}")
            raise
    
    def get_model_size(self, model: Any) -> int:
        total_size = 0
        for param in model.parameters():
            total_size += param.data.numpy().nbytes
        return total_size


class SklearnBackend(ModelBackend):
    """Scikit-learn model backend"""
    
    def load_model(self, artifact_path: str) -> Any:
        try:
            import pickle
            with open(artifact_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load Sklearn model: {e}")
            raise
    
    def unload_model(self, model: Any) -> None:
        del model
    
    def predict(self, model: Any, features: Dict[str, Any]) -> Any:
        import numpy as np
        if isinstance(features, dict):
            input_data = np.array([list(features.values())])
        else:
            input_data = np.array([features])
        
        predictions = model.predict(input_data)
        return predictions[0].tolist() if hasattr(predictions, 'tolist') else predictions
    
    def get_model_size(self, model: Any) -> int:
        import pickle
        return len(pickle.dumps(model))


class ONNXBackend(ModelBackend):
    """ONNX model backend"""
    
    def load_model(self, artifact_path: str) -> Any:
        try:
            import onnxruntime as ort
            return ort.InferenceSession(artifact_path)
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}")
            raise
    
    def unload_model(self, model: Any) -> None:
        del model
    
    def predict(self, model: Any, features: Dict[str, Any]) -> Any:
        import numpy as np
        if isinstance(features, dict):
            input_data = np.array([list(features.values())], dtype=np.float32)
        else:
            input_data = np.array([features], dtype=np.float32)
        
        input_name = model.get_inputs()[0].name
        output = model.run(None, {input_name: input_data})
        return output[0][0].tolist() if isinstance(output[0], np.ndarray) else output[0]
    
    def get_model_size(self, model: Any) -> int:
        return 0  # Placeholder


# ===================== MODEL SERVING SERVICE =====================

class ModelServingService:
    """
    Orchestrates ML model serving with caching, inference, batching, and monitoring.
    Supports multiple backends and implements request queuing and load balancing.
    """
    
    def __init__(self, max_cache_size_mb: int = 10000, enable_batching: bool = True):
        self.max_cache_size_mb = max_cache_size_mb
        self.enable_batching = enable_batching
        
        # Model management
        self.model_configs: Dict[str, Dict[int, ModelServingConfig]] = {}  # model_id -> {version -> config}
        self.model_replicas: Dict[str, List[ModelReplica]] = {}  # model_id -> [replicas]
        self.model_cache: Dict[Tuple[str, int], ModelCache] = {}  # (model_id, version) -> cache
        
        # Inference queues and tracking
        self.inference_queue: deque = deque(maxlen=10000)
        self.inference_requests: Dict[str, InferenceRequest] = {}  # request_id -> request
        self.batch_jobs: Dict[str, BatchInferenceJob] = {}  # batch_id -> job
        
        # Performance metrics
        self.performance_metrics: Dict[Tuple[str, int], PerformanceMetrics] = {}  # (model_id, version) -> metrics
        self.latency_history: Dict[Tuple[str, int], deque] = {}  # (model_id, version) -> latencies
        
        # Backends
        self.backends: Dict[ServingBackend, ModelBackend] = {
            ServingBackend.TENSORFLOW: TensorFlowBackend(),
            ServingBackend.PYTORCH: PyTorchBackend(),
            ServingBackend.SKLEARN: SklearnBackend(),
            ServingBackend.ONNX: ONNXBackend()
        }
        
        # Thread safety
        self.lock = RLock()
        
        # Callbacks
        self.callbacks: Dict[str, List[Callable]] = {
            'model_loaded': [],
            'model_unloaded': [],
            'inference_completed': [],
            'inference_failed': [],
            'batch_completed': []
        }
        
        # Monitoring
        self.current_cache_size_mb = 0
        self.total_requests = 0
        self.total_errors = 0
    
    def register_serving_config(self, config: ModelServingConfig) -> str:
        """Register model serving configuration"""
        with self.lock:
            if config.model_id not in self.model_configs:
                self.model_configs[config.model_id] = {}
            
            self.model_configs[config.model_id][config.model_version] = config
            
            # Initialize metrics
            metrics_key = (config.model_id, config.model_version)
            self.performance_metrics[metrics_key] = PerformanceMetrics(
                model_id=config.model_id,
                model_version=config.model_version
            )
            self.latency_history[metrics_key] = deque(maxlen=10000)
            
            # Create replicas
            if config.model_id not in self.model_replicas:
                self.model_replicas[config.model_id] = []
            
            for i in range(config.num_replicas):
                replica_id = f"{config.model_id}_{config.model_version}_replica_{i}"
                replica = ModelReplica(
                    replica_id=replica_id,
                    model_id=config.model_id,
                    model_version=config.model_version
                )
                self.model_replicas[config.model_id].append(replica)
            
            logger.info(f"Registered serving config for {config.model_id} v{config.model_version}")
            return f"{config.model_id}_{config.model_version}"
    
    def load_model(self, model_id: str, model_version: int, artifact_path: str,
                  backend: ServingBackend) -> bool:
        """Load model into cache"""
        with self.lock:
            cache_key = (model_id, model_version)
            
            # Check if already loaded
            if cache_key in self.model_cache:
                logger.info(f"Model {model_id} v{model_version} already loaded")
                self.model_cache[cache_key].last_access_at = datetime.utcnow().timestamp()
                return True
            
            try:
                backend_impl = self.backends.get(backend)
                if not backend_impl:
                    logger.error(f"Unsupported backend: {backend}")
                    return False
                
                # Load model
                logger.info(f"Loading model {model_id} v{model_version} from {artifact_path}")
                model_object = backend_impl.load_model(artifact_path)
                
                # Get model size
                model_size_bytes = backend_impl.get_model_size(model_object)
                model_size_mb = model_size_bytes / (1024 * 1024)
                
                # Check cache size
                if self.current_cache_size_mb + model_size_mb > self.max_cache_size_mb:
                    logger.warning("Cache full, evicting oldest model")
                    self._evict_lru_model()
                
                # Create cache entry
                cache = ModelCache(
                    model_id=model_id,
                    model_version=model_version,
                    backend=backend,
                    model_object=model_object,
                    artifact_path=artifact_path,
                    loaded_at=datetime.utcnow().timestamp(),
                    last_access_at=datetime.utcnow().timestamp(),
                    size_bytes=model_size_bytes
                )
                
                self.model_cache[cache_key] = cache
                self.current_cache_size_mb += model_size_mb
                
                # Update replica status
                if model_id in self.model_replicas:
                    for replica in self.model_replicas[model_id]:
                        if replica.model_version == model_version:
                            replica.status = ModelLoadStatus.LOADED
                            replica.model_cache = cache
                
                logger.info(f"Loaded {model_id} v{model_version} ({model_size_mb:.2f} MB)")
                self._trigger_callback('model_loaded', {'model_id': model_id, 'version': model_version})
                return True
            
            except Exception as e:
                logger.error(f"Failed to load model {model_id} v{model_version}: {e}")
                if model_id in self.model_replicas:
                    for replica in self.model_replicas[model_id]:
                        if replica.model_version == model_version:
                            replica.status = ModelLoadStatus.FAILED
                return False
    
    def unload_model(self, model_id: str, model_version: int) -> bool:
        """Unload model from cache"""
        with self.lock:
            cache_key = (model_id, model_version)
            
            if cache_key not in self.model_cache:
                return False
            
            try:
                cache = self.model_cache[cache_key]
                backend = self.backends[cache.backend]
                backend.unload_model(cache.model_object)
                
                self.current_cache_size_mb -= (cache.size_bytes / (1024 * 1024))
                del self.model_cache[cache_key]
                
                # Update replica status
                if model_id in self.model_replicas:
                    for replica in self.model_replicas[model_id]:
                        if replica.model_version == model_version:
                            replica.status = ModelLoadStatus.NOT_LOADED
                            replica.model_cache = None
                
                logger.info(f"Unloaded {model_id} v{model_version}")
                self._trigger_callback('model_unloaded', {'model_id': model_id, 'version': model_version})
                return True
            
            except Exception as e:
                logger.error(f"Failed to unload model {model_id} v{model_version}: {e}")
                return False
    
    def predict(self, inference_input: InferenceInput) -> Optional[InferenceOutput]:
        """Execute synchronous inference"""
        request_id = inference_input.request_id
        model_id = inference_input.model_id
        model_version = inference_input.model_version
        
        start_time = time.time()
        
        try:
            with self.lock:
                cache_key = (model_id, model_version)
                
                # Check model loaded
                if cache_key not in self.model_cache:
                    raise RuntimeError(f"Model {model_id} v{model_version} not loaded")
                
                cache = self.model_cache[cache_key]
                cache.access_count += 1
                cache.last_access_at = datetime.utcnow().timestamp()
                
                backend = self.backends[cache.backend]
            
            # Perform inference
            prediction = backend.predict(cache.model_object, inference_input.features)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Update metrics
            self._update_metrics(model_id, model_version, latency_ms, success=True)
            
            # Create output
            output = InferenceOutput(
                request_id=request_id,
                model_id=model_id,
                model_version=model_version,
                prediction=prediction,
                prediction_type=self._get_prediction_type(model_id, model_version),
                latency_ms=latency_ms
            )
            
            self._trigger_callback('inference_completed', {
                'request_id': request_id,
                'model_id': model_id,
                'latency_ms': latency_ms
            })
            
            return output
        
        except Exception as e:
            logger.error(f"Inference failed for {request_id}: {e}")
            self._update_metrics(model_id, model_version, 0, success=False)
            self._trigger_callback('inference_failed', {
                'request_id': request_id,
                'model_id': model_id,
                'error': str(e)
            })
            return None
    
    def predict_async(self, inference_input: InferenceInput) -> str:
        """Queue inference request asynchronously"""
        request_id = inference_input.request_id
        
        request = InferenceRequest(
            request_id=request_id,
            inference_input=inference_input,
            created_at=datetime.utcnow().timestamp()
        )
        
        with self.lock:
            self.inference_queue.append(request)
            self.inference_requests[request_id] = request
            self.total_requests += 1
        
        return request_id
    
    def get_inference_result(self, request_id: str) -> Optional[InferenceOutput]:
        """Get result of async inference"""
        with self.lock:
            if request_id not in self.inference_requests:
                return None
            
            request = self.inference_requests[request_id]
            return request.result
    
    def batch_predict(self, batch_id: str, requests: List[InferenceInput]) -> str:
        """Submit batch inference job"""
        batch_job = BatchInferenceJob(
            batch_id=batch_id,
            model_id=requests[0].model_id if requests else '',
            model_version=requests[0].model_version if requests else 0
        )
        
        with self.lock:
            for inference_input in requests:
                request = InferenceRequest(
                    request_id=inference_input.request_id,
                    inference_input=inference_input,
                    created_at=datetime.utcnow().timestamp()
                )
                batch_job.requests.append(request)
            
            self.batch_jobs[batch_id] = batch_job
        
        # Process batch
        self._process_batch(batch_id)
        
        return batch_id
    
    def get_batch_result(self, batch_id: str) -> Optional[BatchInferenceJob]:
        """Get batch inference results"""
        with self.lock:
            return self.batch_jobs.get(batch_id)
    
    def _process_batch(self, batch_id: str) -> None:
        """Process batch inference job"""
        with self.lock:
            if batch_id not in self.batch_jobs:
                return
            
            batch_job = self.batch_jobs[batch_id]
            batch_job.status = InferenceStatus.PROCESSING
        
        try:
            for request in batch_job.requests:
                result = self.predict(request.inference_input)
                if result:
                    batch_job.results[request.request_id] = result
            
            with self.lock:
                batch_job.status = InferenceStatus.COMPLETED
                batch_job.completed_at = datetime.utcnow().timestamp()
            
            self._trigger_callback('batch_completed', {
                'batch_id': batch_id,
                'results_count': len(batch_job.results)
            })
        
        except Exception as e:
            logger.error(f"Batch processing failed {batch_id}: {e}")
            with self.lock:
                batch_job.status = InferenceStatus.FAILED
    
    def get_performance_metrics(self, model_id: str, model_version: int) -> Optional[PerformanceMetrics]:
        """Get performance metrics for model"""
        with self.lock:
            metrics_key = (model_id, model_version)
            return self.performance_metrics.get(metrics_key)
    
    def _update_metrics(self, model_id: str, model_version: int, latency_ms: float, success: bool) -> None:
        """Update performance metrics"""
        with self.lock:
            metrics_key = (model_id, model_version)
            
            if metrics_key not in self.performance_metrics:
                return
            
            metrics = self.performance_metrics[metrics_key]
            metrics.total_requests += 1
            
            if success:
                metrics.successful_requests += 1
                
                # Update latency stats
                if metrics_key in self.latency_history:
                    self.latency_history[metrics_key].append(latency_ms)
                    
                    latencies = list(self.latency_history[metrics_key])
                    latencies.sort()
                    
                    metrics.mean_latency_ms = np.mean(latencies)
                    metrics.p50_latency_ms = np.percentile(latencies, 50)
                    metrics.p95_latency_ms = np.percentile(latencies, 95)
                    metrics.p99_latency_ms = np.percentile(latencies, 99)
                    metrics.min_latency_ms = latencies[0]
                    metrics.max_latency_ms = latencies[-1]
            else:
                metrics.failed_requests += 1
            
            metrics.error_rate = metrics.failed_requests / max(metrics.total_requests, 1)
    
    def _evict_lru_model(self) -> None:
        """Evict least recently used model from cache"""
        if not self.model_cache:
            return
        
        lru_key = min(self.model_cache.keys(),
                      key=lambda k: self.model_cache[k].last_access_at)
        
        cache = self.model_cache[lru_key]
        self.unload_model(cache.model_id, cache.model_version)
    
    def _get_prediction_type(self, model_id: str, model_version: int) -> PredictionType:
        """Get prediction type for model"""
        if model_id in self.model_configs and model_version in self.model_configs[model_id]:
            config = self.model_configs[model_id][model_version]
            return config.prediction_type
        
        return PredictionType.CLASSIFICATION
    
    def _trigger_callback(self, event_type: str, data: Dict[str, Any]) -> None:
        """Trigger registered callbacks"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register callback for event"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        
        self.callbacks[event_type].append(callback)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        with self.lock:
            return {
                'total_requests': self.total_requests,
                'total_errors': self.total_errors,
                'models_loaded': len(self.model_cache),
                'cache_size_mb': self.current_cache_size_mb,
                'max_cache_size_mb': self.max_cache_size_mb,
                'pending_requests': len(self.inference_queue),
                'pending_batches': len(self.batch_jobs),
                'total_replicas': sum(len(replicas) for replicas in self.model_replicas.values()),
                'timestamp': datetime.utcnow().timestamp()
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check endpoint"""
        with self.lock:
            loaded_models = len(self.model_cache)
            total_capacity = sum(
                len(self.model_configs.get(m_id, {}))
                for m_id in self.model_configs
            )
            
            return {
                'status': 'healthy' if loaded_models > 0 else 'unhealthy',
                'models_loaded': loaded_models,
                'models_expected': total_capacity,
                'cache_usage_percent': (self.current_cache_size_mb / self.max_cache_size_mb * 100) if self.max_cache_size_mb > 0 else 0,
                'queue_length': len(self.inference_queue),
                'timestamp': datetime.utcnow().timestamp()
            }
