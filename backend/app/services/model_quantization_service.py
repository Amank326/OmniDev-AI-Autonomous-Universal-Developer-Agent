"""
Model Quantization Service
Handles model quantization, pruning, distillation, and compression strategies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
import numpy as np
from threading import RLock
import json
import time
from datetime import datetime


class QuantizationType(Enum):
    """Quantization method types"""
    INT8 = "int8"
    INT4 = "int4"
    FP16 = "fp16"
    FP32 = "fp32"
    MIXED = "mixed"
    DYNAMIC = "dynamic"
    STATIC = "static"


class PruningStrategy(Enum):
    """Model pruning strategies"""
    WEIGHT_PRUNING = "weight_pruning"          # Remove small weights
    STRUCTURED_PRUNING = "structured_pruning"  # Remove entire channels/filters
    LAYER_PRUNING = "layer_pruning"            # Remove entire layers
    MAGNITUDE_PRUNING = "magnitude_pruning"    # Prune by magnitude
    LOTTERY_TICKET = "lottery_ticket"          # Lottery ticket hypothesis


class DistillationMethod(Enum):
    """Knowledge distillation methods"""
    RESPONSE_BASED = "response_based"    # Mimic final output
    FEATURE_BASED = "feature_based"      # Match intermediate features
    RELATION_BASED = "relation_based"    # Match feature relationships
    ATTENTION_BASED = "attention_based"  # Transfer attention maps


class CompressionBackend(Enum):
    """Compression backends"""
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    ONNX = "onnx"
    TFLITE = "tflite"
    TENSORRT = "tensorrt"
    OPENVINO = "openvino"


@dataclass
class QuantizationConfig:
    """Quantization configuration"""
    quantization_type: QuantizationType
    bits: int = 8
    symmetric: bool = True
    per_channel: bool = True
    calibration_samples: int = 100
    calibration_dataset: Optional[List[np.ndarray]] = None
    min_val: float = -1.0
    max_val: float = 1.0
    scale_per_layer: bool = False
    preserve_accuracy_threshold: float = 0.99  # Min 99% accuracy retention


@dataclass
class PruningConfig:
    """Pruning configuration"""
    strategy: PruningStrategy
    sparsity_target: float = 0.5  # Target sparsity (0.0-1.0)
    fine_tune_epochs: int = 10
    fine_tune_lr: float = 0.0001
    magnitude_threshold: float = 1e-4
    structured_unit: str = "channel"  # channel or filter or block
    iterative_steps: int = 5


@dataclass
class DistillationConfig:
    """Knowledge distillation configuration"""
    method: DistillationMethod
    temperature: float = 4.0
    alpha: float = 0.5  # Weight between distillation and regular loss
    teacher_model_id: str = ""
    teacher_model_version: int = 1
    training_epochs: int = 50
    batch_size: int = 32
    learning_rate: float = 0.001


@dataclass
class ModelOptimizationJob:
    """Model optimization job tracking"""
    job_id: str
    model_id: str
    model_version: int
    optimization_type: str  # quantization, pruning, distillation, combined
    config: Dict[str, Any]
    status: str = "queued"  # queued, processing, completed, failed
    progress_percent: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    original_size_bytes: int = 0
    optimized_size_bytes: int = 0
    original_latency_ms: float = 0.0
    optimized_latency_ms: float = 0.0
    accuracy_drop_percent: float = 0.0
    compression_ratio: float = 1.0
    error_message: Optional[str] = None
    artifacts: Dict[str, str] = field(default_factory=dict)  # model_path, config_path


@dataclass
class QuantizationResult:
    """Quantization result metrics"""
    quantization_type: QuantizationType
    bits: int
    original_size_bytes: int
    quantized_size_bytes: int
    compression_ratio: float
    accuracy_drop_percent: float
    latency_improvement_percent: float
    memory_reduction_percent: float
    scale_factors: Dict[str, List[float]]
    zero_points: Dict[str, List[int]]
    quantization_params: Dict[str, Any]


@dataclass
class PruningResult:
    """Pruning result metrics"""
    strategy: PruningStrategy
    initial_sparsity: float
    final_sparsity: float
    parameters_removed: int
    accuracy_drop_percent: float
    latency_improvement_percent: float
    memory_reduction_percent: float
    flops_reduction_percent: float
    pruned_layers: List[str]


@dataclass
class DistillationResult:
    """Distillation result metrics"""
    method: DistillationMethod
    temperature: float
    teacher_model_version: int
    student_size_reduction_percent: float
    accuracy_drop_percent: float
    inference_speedup_percent: float
    training_time_hours: float
    knowledge_transfer_metric: float


@dataclass
class OptimizationMetrics:
    """Comprehensive optimization metrics"""
    job_id: str
    model_id: str
    model_version: int
    total_optimization_time_seconds: float
    quantization_results: Optional[QuantizationResult] = None
    pruning_results: Optional[PruningResult] = None
    distillation_results: Optional[DistillationResult] = None
    cumulative_compression_ratio: float = 1.0
    cumulative_speedup_percent: float = 0.0
    cumulative_accuracy_drop_percent: float = 0.0


class ModelQuantizationService:
    """
    Service for model quantization, pruning, distillation, and compression.
    Provides multiple optimization strategies with comprehensive metrics tracking.
    """

    def __init__(self, max_concurrent_jobs: int = 5):
        """Initialize quantization service"""
        self.max_concurrent_jobs = max_concurrent_jobs
        self.active_jobs: Dict[str, ModelOptimizationJob] = {}
        self.completed_jobs: Dict[str, ModelOptimizationJob] = {}
        self.job_metrics: Dict[str, OptimizationMetrics] = {}
        self.optimization_history: Dict[str, List[ModelOptimizationJob]] = {}
        self.lock = RLock()

        # Callbacks for event system
        self.callbacks: Dict[str, Callable] = {
            'job_started': None,
            'job_progress': None,
            'job_completed': None,
            'job_failed': None,
            'optimization_applied': None
        }

    def quantize_model(
        self,
        model_id: str,
        model_version: int,
        artifact_path: str,
        config: QuantizationConfig,
        job_id: str = None
    ) -> str:
        """
        Quantize model using specified configuration.
        
        Args:
            model_id: Model identifier
            model_version: Model version number
            artifact_path: Path to model artifact
            config: Quantization configuration
            job_id: Optional job ID (auto-generated if None)
            
        Returns:
            Job ID for tracking
        """
        with self.lock:
            if job_id is None:
                job_id = f"quant_{model_id}_{model_version}_{int(time.time())}"

            if len(self.active_jobs) >= self.max_concurrent_jobs:
                raise RuntimeError(f"Maximum concurrent jobs ({self.max_concurrent_jobs}) reached")

            job = ModelOptimizationJob(
                job_id=job_id,
                model_id=model_id,
                model_version=model_version,
                optimization_type="quantization",
                config=self._config_to_dict(config),
                status="queued"
            )

            self.active_jobs[job_id] = job
            self._add_to_history(model_id, job)

            # Trigger callback
            self._trigger_callback('job_started', {
                'job_id': job_id,
                'model_id': model_id,
                'model_version': model_version,
                'optimization_type': 'quantization'
            })

            return job_id

    def prune_model(
        self,
        model_id: str,
        model_version: int,
        artifact_path: str,
        config: PruningConfig,
        job_id: str = None
    ) -> str:
        """
        Prune model using specified strategy.
        
        Args:
            model_id: Model identifier
            model_version: Model version number
            artifact_path: Path to model artifact
            config: Pruning configuration
            job_id: Optional job ID (auto-generated if None)
            
        Returns:
            Job ID for tracking
        """
        with self.lock:
            if job_id is None:
                job_id = f"prune_{model_id}_{model_version}_{int(time.time())}"

            if len(self.active_jobs) >= self.max_concurrent_jobs:
                raise RuntimeError(f"Maximum concurrent jobs ({self.max_concurrent_jobs}) reached")

            job = ModelOptimizationJob(
                job_id=job_id,
                model_id=model_id,
                model_version=model_version,
                optimization_type="pruning",
                config=self._config_to_dict(config),
                status="queued"
            )

            self.active_jobs[job_id] = job
            self._add_to_history(model_id, job)

            self._trigger_callback('job_started', {
                'job_id': job_id,
                'model_id': model_id,
                'optimization_type': 'pruning'
            })

            return job_id

    def distill_model(
        self,
        student_model_id: str,
        student_model_version: int,
        artifact_path: str,
        config: DistillationConfig,
        job_id: str = None
    ) -> str:
        """
        Distill student model from teacher model.
        
        Args:
            student_model_id: Student model identifier
            student_model_version: Student model version
            artifact_path: Path to student model artifact
            config: Distillation configuration
            job_id: Optional job ID
            
        Returns:
            Job ID for tracking
        """
        with self.lock:
            if job_id is None:
                job_id = f"distill_{student_model_id}_{student_model_version}_{int(time.time())}"

            if len(self.active_jobs) >= self.max_concurrent_jobs:
                raise RuntimeError(f"Maximum concurrent jobs ({self.max_concurrent_jobs}) reached")

            job = ModelOptimizationJob(
                job_id=job_id,
                model_id=student_model_id,
                model_version=student_model_version,
                optimization_type="distillation",
                config=self._config_to_dict(config),
                status="queued"
            )

            self.active_jobs[job_id] = job
            self._add_to_history(student_model_id, job)

            self._trigger_callback('job_started', {
                'job_id': job_id,
                'model_id': student_model_id,
                'optimization_type': 'distillation'
            })

            return job_id

    def update_job_progress(
        self,
        job_id: str,
        progress_percent: int,
        status: str = "processing"
    ) -> Optional[ModelOptimizationJob]:
        """Update optimization job progress"""
        with self.lock:
            if job_id not in self.active_jobs:
                return None

            job = self.active_jobs[job_id]
            job.progress_percent = progress_percent
            job.status = status
            if job.start_time is None:
                job.start_time = datetime.utcnow()

            self._trigger_callback('job_progress', {
                'job_id': job_id,
                'progress_percent': progress_percent,
                'status': status
            })

            return job

    def complete_job(
        self,
        job_id: str,
        result_metrics: OptimizationMetrics,
        optimized_artifact_path: str
    ) -> Optional[ModelOptimizationJob]:
        """Mark optimization job as completed with metrics"""
        with self.lock:
            if job_id not in self.active_jobs:
                return None

            job = self.active_jobs[job_id]
            job.status = "completed"
            job.progress_percent = 100
            job.end_time = datetime.utcnow()

            # Store metrics
            self.job_metrics[job_id] = result_metrics

            # Move to completed
            self.completed_jobs[job_id] = job
            del self.active_jobs[job_id]

            # Calculate compression ratio
            if result_metrics.quantization_results:
                job.compression_ratio = result_metrics.quantization_results.compression_ratio
                job.original_size_bytes = result_metrics.quantization_results.original_size_bytes
                job.optimized_size_bytes = result_metrics.quantization_results.quantized_size_bytes
                job.accuracy_drop_percent = result_metrics.quantization_results.accuracy_drop_percent

            job.artifacts['optimized_model'] = optimized_artifact_path

            # Calculate execution time
            if job.start_time and job.end_time:
                duration_seconds = (job.end_time - job.start_time).total_seconds()
                result_metrics.total_optimization_time_seconds = duration_seconds

            self._trigger_callback('job_completed', {
                'job_id': job_id,
                'model_id': job.model_id,
                'optimization_type': job.optimization_type,
                'compression_ratio': job.compression_ratio,
                'accuracy_drop_percent': job.accuracy_drop_percent
            })

            return job

    def fail_job(self, job_id: str, error_message: str) -> Optional[ModelOptimizationJob]:
        """Mark optimization job as failed"""
        with self.lock:
            if job_id not in self.active_jobs:
                return None

            job = self.active_jobs[job_id]
            job.status = "failed"
            job.error_message = error_message
            job.end_time = datetime.utcnow()

            # Move to completed
            self.completed_jobs[job_id] = job
            del self.active_jobs[job_id]

            self._trigger_callback('job_failed', {
                'job_id': job_id,
                'model_id': job.model_id,
                'error': error_message
            })

            return job

    def get_job(self, job_id: str) -> Optional[ModelOptimizationJob]:
        """Get optimization job by ID"""
        with self.lock:
            return self.active_jobs.get(job_id) or self.completed_jobs.get(job_id)

    def get_job_metrics(self, job_id: str) -> Optional[OptimizationMetrics]:
        """Get detailed metrics for completed optimization job"""
        with self.lock:
            return self.job_metrics.get(job_id)

    def get_model_optimization_history(
        self,
        model_id: str,
        limit: int = 50
    ) -> List[ModelOptimizationJob]:
        """Get optimization history for a model"""
        with self.lock:
            history = self.optimization_history.get(model_id, [])
            return history[-limit:]

    def get_active_jobs(self) -> List[ModelOptimizationJob]:
        """Get all active optimization jobs"""
        with self.lock:
            return list(self.active_jobs.values())

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics"""
        with self.lock:
            total_jobs = len(self.completed_jobs) + len(self.active_jobs)
            completed = len(self.completed_jobs)
            active = len(self.active_jobs)
            failed = sum(1 for j in self.completed_jobs.values() if j.status == "failed")

            # Calculate average improvements
            successful_jobs = [j for j in self.completed_jobs.values() if j.status == "completed"]
            
            avg_compression = np.mean([j.compression_ratio for j in successful_jobs]) if successful_jobs else 1.0
            avg_accuracy_drop = np.mean([j.accuracy_drop_percent for j in successful_jobs]) if successful_jobs else 0.0
            total_time = sum((j.end_time - j.start_time).total_seconds() for j in successful_jobs if j.start_time and j.end_time)

            # Optimization type breakdown
            type_breakdown = {}
            for job in self.completed_jobs.values():
                opt_type = job.optimization_type
                if opt_type not in type_breakdown:
                    type_breakdown[opt_type] = 0
                type_breakdown[opt_type] += 1

            return {
                'total_jobs': total_jobs,
                'completed_jobs': completed,
                'active_jobs': active,
                'failed_jobs': failed,
                'success_rate': completed / total_jobs if total_jobs > 0 else 0,
                'avg_compression_ratio': float(avg_compression),
                'avg_accuracy_drop_percent': float(avg_accuracy_drop),
                'total_optimization_time_hours': total_time / 3600,
                'optimization_type_breakdown': type_breakdown
            }

    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register callback for optimization events"""
        if event_type in self.callbacks:
            self.callbacks[event_type] = callback

    def health_check(self) -> Dict[str, Any]:
        """Health check for quantization service"""
        with self.lock:
            return {
                'status': 'healthy',
                'active_jobs': len(self.active_jobs),
                'max_concurrent_jobs': self.max_concurrent_jobs,
                'completed_jobs': len(self.completed_jobs),
                'queue_available': len(self.active_jobs) < self.max_concurrent_jobs,
                'timestamp': datetime.utcnow().isoformat()
            }

    # Private methods
    def _config_to_dict(self, config: Any) -> Dict[str, Any]:
        """Convert config dataclass to dictionary"""
        if isinstance(config, dict):
            return config
        return {
            k: v.value if isinstance(v, Enum) else v
            for k, v in config.__dict__.items()
            if not k.startswith('_')
        }

    def _add_to_history(self, model_id: str, job: ModelOptimizationJob) -> None:
        """Add job to model optimization history"""
        if model_id not in self.optimization_history:
            self.optimization_history[model_id] = []
        self.optimization_history[model_id].append(job)

    def _trigger_callback(self, event_type: str, data: Dict[str, Any]) -> None:
        """Trigger event callback if registered"""
        if event_type in self.callbacks and self.callbacks[event_type]:
            try:
                self.callbacks[event_type](data)
            except Exception as e:
                print(f"Error triggering callback for {event_type}: {e}")
