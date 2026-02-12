"""
Prediction Service - Real-time and batch predictions with model serving, versioning, and fallback.

Supports multiple prediction modes (online, batch), model ensembles, A/B testing,
confidence scoring, and automatic fallback to stable models.
"""

import time
import json
from enum import Enum
from typing import Dict, List, Optional, Tuple, Callable, Any, Union
from dataclasses import dataclass, field
from threading import RLock
from collections import deque, defaultdict
from datetime import datetime


class PredictionMode(Enum):
    """Mode for generating predictions."""
    ONLINE = "online"  # Real-time single prediction
    BATCH = "batch"  # Batch processing
    STREAMING = "streaming"  # Continuous stream


class ConfidenceMethod(Enum):
    """Methods for computing prediction confidence."""
    SOFTMAX_ENTROPY = "softmax_entropy"
    MODEL_UNCERTAINTY = "model_uncertainty"
    ENSEMBLE_AGREEMENT = "ensemble_agreement"
    CONFIDENCE_SCORE = "confidence_score"


class PredictionStrategy(Enum):
    """Strategies for selecting models."""
    SINGLE = "single"  # Single production model
    ENSEMBLE = "ensemble"  # Weighted ensemble
    AB_TEST = "ab_test"  # A/B testing
    CHAMPION_CHALLENGER = "champion_challenger"  # Champion with challenger


class FallbackPolicy(Enum):
    """Policy when primary model fails."""
    PREVIOUS_VERSION = "previous_version"
    CACHED_RESULT = "cached_result"
    ENSEMBLE_FALLBACK = "ensemble_fallback"
    REJECT_PREDICTION = "reject_prediction"


@dataclass
class PredictionRequest:
    """Request for prediction."""
    request_id: str
    model_name: str
    model_version: Optional[str] = None  # If None, use production
    mode: PredictionMode = PredictionMode.ONLINE
    input_features: Dict[str, Any] = field(default_factory=dict)
    feature_set: str = ""
    return_confidence: bool = True
    return_explain: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class Prediction:
    """Prediction result."""
    request_id: str
    model_name: str
    model_version: str
    prediction: Any
    confidence: Optional[float] = None
    confidence_method: Optional[ConfidenceMethod] = None
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    explanation: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class BatchPredictionJob:
    """Batch prediction job."""
    job_id: str
    model_name: str
    model_version: str
    status: str = "pending"  # pending, running, completed, failed
    input_data_path: str = ""
    output_data_path: str = ""
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_seconds: float = 0.0
    error_message: str = ""


@dataclass
class EnsembleConfig:
    """Configuration for model ensemble."""
    ensemble_id: str
    model_versions: List[str]  # model_name:version
    weights: Dict[str, float] = field(default_factory=dict)
    aggregation_method: str = "weighted_average"  # weighted_average, voting, stacking
    fallback_to_best: bool = True


@dataclass
class ABTestConfig:
    """A/B testing configuration."""
    test_id: str
    control_model: str  # model_name:version
    treatment_model: str
    traffic_split: float = 0.5  # proportion to treatment
    duration_hours: int = 24
    success_criterion: str = ""  # metric name
    success_threshold: float = 0.0
    started_at: Optional[float] = None
    ended_at: Optional[float] = None


@dataclass
class PredictionMetric:
    """Metric about predictions."""
    metric_name: str
    value: float
    model_version: str
    timestamp: float = field(default_factory=time.time)


class PredictionServer:
    """Main prediction serving service."""
    
    def __init__(self):
        self.predictions_cache: deque = deque(maxlen=100000)
        self.batch_jobs: Dict[str, BatchPredictionJob] = {}
        self.ensembles: Dict[str, EnsembleConfig] = {}
        self.ab_tests: Dict[str, ABTestConfig] = {}
        self.fallback_policies: Dict[str, FallbackPolicy] = defaultdict(lambda: FallbackPolicy.CACHED_RESULT)
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = RLock()
        self.statistics = {
            "predictions_served": 0,
            "batch_jobs_completed": 0,
            "average_latency_ms": 0.0,
            "fallback_count": 0,
            "ensemble_predictions": 0,
            "ab_test_predictions": 0
        }
    
    def predict(self, request: PredictionRequest) -> Optional[Prediction]:
        """Generate prediction for request."""
        start_time = time.time()
        
        # Route request based on strategy
        if request.model_version and ":" in request.model_version:
            # Single model prediction
            prediction = self._single_model_prediction(request)
        else:
            # Use production model
            prediction = self._single_model_prediction(request)
        
        if prediction is None:
            # Apply fallback policy
            prediction = self._apply_fallback(request)
        
        if prediction:
            prediction.latency_ms = (time.time() - start_time) * 1000
            
            with self.lock:
                self.predictions_cache.append(prediction)
                self.statistics["predictions_served"] += 1
            
            self._trigger_callback("prediction_served", request.request_id, prediction)
            return prediction
        
        return None
    
    def _single_model_prediction(self, request: PredictionRequest) -> Optional[Prediction]:
        """Generate prediction from single model."""
        # Mock prediction (in real implementation, calls actual model)
        try:
            # Simulate model inference
            import numpy as np
            
            # Generate prediction based on input features
            feature_values = list(request.input_features.values())
            if feature_values:
                base_value = float(sum(feature_values)) / len(feature_values)
            else:
                base_value = 0.5
            
            # Add randomness for realism
            prediction_value = base_value + np.random.normal(0, 0.1)
            
            # Compute confidence (0-1 range)
            confidence = 0.7 + np.random.random() * 0.2
            
            prediction = Prediction(
                request_id=request.request_id,
                model_name=request.model_name,
                model_version=request.model_version or "production",
                prediction=prediction_value,
                confidence=confidence if request.return_confidence else None,
                confidence_method=ConfidenceMethod.SOFTMAX_ENTROPY if request.return_confidence else None
            )
            
            if request.return_explain:
                prediction.explanation = {
                    "top_features": {f: v for f, v in list(request.input_features.items())[:3]}
                }
            
            return prediction
        except Exception as e:
            return None
    
    def _apply_fallback(self, request: PredictionRequest) -> Optional[Prediction]:
        """Apply fallback policy when prediction fails."""
        policy = self.fallback_policies.get(request.model_name, FallbackPolicy.CACHED_RESULT)
        
        with self.lock:
            self.statistics["fallback_count"] += 1
        
        if policy == FallbackPolicy.CACHED_RESULT:
            # Return cached prediction
            for pred in reversed(self.predictions_cache):
                if pred.model_name == request.model_name:
                    return pred
        
        elif policy == FallbackPolicy.PREVIOUS_VERSION:
            # Would use previous model version (mock)
            pass
        
        self._trigger_callback("fallback_applied", request.request_id, policy.value)
        return None
    
    def predict_ensemble(self, request: PredictionRequest, ensemble_id: str) -> Optional[Prediction]:
        """Generate ensemble prediction."""
        ensemble = self.ensembles.get(ensemble_id)
        if not ensemble:
            return None
        
        # Get predictions from all models in ensemble
        predictions = []
        for model_version in ensemble.model_versions:
            ensemble_request = PredictionRequest(
                request_id=f"{request.request_id}_ensemble",
                model_name=request.model_name,
                model_version=model_version,
                input_features=request.input_features
            )
            pred = self._single_model_prediction(ensemble_request)
            if pred:
                predictions.append(pred)
        
        if not predictions:
            return None
        
        # Aggregate predictions using weights
        weights = [ensemble.weights.get(v, 1.0) for v in ensemble.model_versions]
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Weighted average
        aggregate_pred = sum(p.prediction * w for p, w in zip(predictions, weights))
        avg_confidence = sum(p.confidence * w for p, w in zip(predictions, weights) if p.confidence)
        
        ensemble_pred = Prediction(
            request_id=request.request_id,
            model_name=request.model_name,
            model_version=ensemble_id,
            prediction=aggregate_pred,
            confidence=avg_confidence,
            metadata={"ensemble_size": len(predictions)}
        )
        
        with self.lock:
            self.statistics["ensemble_predictions"] += 1
        
        self._trigger_callback("ensemble_prediction", request.request_id, ensemble_id)
        return ensemble_pred
    
    def predict_ab_test(self, request: PredictionRequest, test_id: str) -> Optional[Tuple[Prediction, str]]:
        """Generate prediction for A/B test, returns (Prediction, assigned_model)."""
        ab_test = self.ab_tests.get(test_id)
        if not ab_test:
            return None, None
        
        import numpy as np
        
        # Assign model based on traffic split
        if np.random.random() < ab_test.traffic_split:
            model_version = ab_test.treatment_model
        else:
            model_version = ab_test.control_model
        
        request.model_version = model_version
        prediction = self._single_model_prediction(request)
        
        if prediction:
            with self.lock:
                self.statistics["ab_test_predictions"] += 1
            self._trigger_callback("ab_test_prediction", request.request_id, test_id, model_version)
        
        return prediction, model_version
    
    def batch_predict(self, model_name: str, model_version: str, 
                     input_data_path: str, output_data_path: str) -> str:
        """Create batch prediction job."""
        job_id = f"batch_{int(time.time() * 1000)}"
        
        job = BatchPredictionJob(
            job_id=job_id,
            model_name=model_name,
            model_version=model_version,
            input_data_path=input_data_path,
            output_data_path=output_data_path
        )
        
        with self.lock:
            self.batch_jobs[job_id] = job
        
        # Start batch job in background (mock)
        def run_batch():
            with self.lock:
                job.status = "running"
                job.started_at = time.time()
            
            # Mock processing
            try:
                job.total_records = 1000  # Mock
                job.processed_records = 1000  # Mock
                job.status = "completed"
                job.completed_at = time.time()
                job.duration_seconds = job.completed_at - job.started_at
                
                with self.lock:
                    self.statistics["batch_jobs_completed"] += 1
                
                self._trigger_callback("batch_job_completed", job_id)
            except Exception as e:
                with self.lock:
                    job.status = "failed"
                    job.error_message = str(e)
        
        import threading
        thread = threading.Thread(target=run_batch, daemon=True)
        thread.start()
        
        return job_id
    
    def get_batch_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get batch job status."""
        with self.lock:
            job = self.batch_jobs.get(job_id)
            if job:
                return {
                    "job_id": job.job_id,
                    "status": job.status,
                    "processed": job.processed_records,
                    "total": job.total_records,
                    "duration_seconds": job.duration_seconds
                }
        return None
    
    def create_ensemble(self, ensemble_config: EnsembleConfig) -> str:
        """Create model ensemble."""
        with self.lock:
            self.ensembles[ensemble_config.ensemble_id] = ensemble_config
        
        self._trigger_callback("ensemble_created", ensemble_config.ensemble_id)
        return ensemble_config.ensemble_id
    
    def get_ensemble(self, ensemble_id: str) -> Optional[EnsembleConfig]:
        """Get ensemble configuration."""
        with self.lock:
            return self.ensembles.get(ensemble_id)
    
    def create_ab_test(self, ab_test_config: ABTestConfig) -> str:
        """Create A/B test."""
        with self.lock:
            self.ab_tests[ab_test_config.test_id] = ab_test_config
            ab_test_config.started_at = time.time()
        
        self._trigger_callback("ab_test_created", ab_test_config.test_id)
        return ab_test_config.test_id
    
    def get_ab_test(self, test_id: str) -> Optional[ABTestConfig]:
        """Get A/B test configuration."""
        with self.lock:
            return self.ab_tests.get(test_id)
    
    def end_ab_test(self, test_id: str) -> bool:
        """End A/B test."""
        with self.lock:
            ab_test = self.ab_tests.get(test_id)
            if ab_test:
                ab_test.ended_at = time.time()
                self._trigger_callback("ab_test_ended", test_id)
                return True
        return False
    
    def set_fallback_policy(self, model_name: str, policy: FallbackPolicy) -> None:
        """Set fallback policy for model."""
        with self.lock:
            self.fallback_policies[model_name] = policy
    
    def get_recent_predictions(self, model_name: Optional[str] = None, limit: int = 100) -> List[Prediction]:
        """Get recent predictions."""
        with self.lock:
            preds = list(self.predictions_cache)
            if model_name:
                preds = [p for p in preds if p.model_name == model_name]
            return preds[-limit:]
    
    def get_prediction_success_rate(self, model_name: str, window_seconds: int = 3600) -> float:
        """Get prediction success rate."""
        cutoff = time.time() - window_seconds
        
        with self.lock:
            recent = [p for p in self.predictions_cache 
                     if p.model_name == model_name and p.timestamp >= cutoff]
        
        if not recent:
            return 1.0
        
        successful = len([p for p in recent if p.prediction is not None])
        return successful / len(recent) if recent else 0.0
    
    def get_average_latency(self, model_name: str, window_seconds: int = 3600) -> float:
        """Get average prediction latency."""
        cutoff = time.time() - window_seconds
        
        with self.lock:
            recent = [p for p in self.predictions_cache 
                     if p.model_name == model_name and p.timestamp >= cutoff]
        
        if not recent:
            return 0.0
        
        return sum(p.latency_ms for p in recent) / len(recent) if recent else 0.0
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for events."""
        with self.lock:
            self.callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, *args, **kwargs) -> None:
        """Trigger callbacks for event."""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except:
                pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get prediction service statistics."""
        with self.lock:
            return {
                **self.statistics,
                "active_ensembles": len(self.ensembles),
                "active_ab_tests": len([t for t in self.ab_tests.values() if t.ended_at is None]),
                "cached_predictions": len(self.predictions_cache),
                "pending_batch_jobs": len([j for j in self.batch_jobs.values() if j.status == "pending" or j.status == "running"])
            }


# Singleton instance
_prediction_server: Optional[PredictionServer] = None


def get_prediction_server() -> PredictionServer:
    """Get or create prediction server instance."""
    global _prediction_server
    if _prediction_server is None:
        _prediction_server = PredictionServer()
    return _prediction_server
