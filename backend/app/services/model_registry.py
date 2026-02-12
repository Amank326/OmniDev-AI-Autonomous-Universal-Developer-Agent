"""
Model Registry Service - Manage ML model versions, metadata, and lifecycle.

Supports model versioning, production/staging promotion, A/B testing, performance tracking,
and rollback capabilities across model versions and artifacts.
"""

import time
import json
import hashlib
from enum import Enum
from typing import Dict, List, Optional, Tuple, Callable, Any, BinaryIO
from dataclasses import dataclass, field
from threading import RLock
from collections import defaultdict, deque
from datetime import datetime


class ModelStatus(Enum):
    """Status of a model version."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class MetricType(Enum):
    """Types of performance metrics."""
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1 = "f1"
    AUC = "auc"
    MSE = "mse"
    RMSE = "rmse"
    MAE = "mae"
    MAPE = "mape"
    LOGLOSS = "logloss"


class ArtifactType(Enum):
    """Types of model artifacts."""
    MODEL = "model"
    WEIGHTS = "weights"
    CONFIG = "config"
    FEATURES = "features"
    SCALER = "scaler"
    ENCODER = "encoder"
    METADATA = "metadata"


@dataclass
class PerformanceMetric:
    """Performance metric for a model."""
    metric_type: MetricType
    value: float
    timestamp: float = field(default_factory=time.time)
    dataset: str = ""
    split: str = ""  # train, test, validation
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelArtifact:
    """Model artifact (weights, config, etc)."""
    artifact_id: str
    artifact_type: ArtifactType
    path: str
    size_bytes: int
    checksum: str
    uploaded_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelMetadata:
    """Metadata for model version."""
    model_name: str
    version: str
    status: ModelStatus
    framework: str  # sklearn, xgboost, pytorch, tensorflow
    task_type: str  # classification, regression, clustering
    created_at: float = field(default_factory=time.time)
    trained_at: Optional[float] = None
    promoted_at: Optional[float] = None
    description: str = ""
    author: str = ""
    feature_set: str = ""
    training_config: Dict[str, Any] = field(default_factory=dict)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: List[PerformanceMetric] = field(default_factory=list)
    artifacts: List[ModelArtifact] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Other model versions this depends on


@dataclass
class ABTestConfig:
    """A/B test configuration."""
    test_id: str
    model_a: str  # version
    model_b: str  # version
    traffic_split: float  # % for model_a, rest for model_b
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    winner: Optional[str] = None  # winning model version
    metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)  # model -> metric -> value


@dataclass
class ModelPromotion:
    """Record of model promotion."""
    model_version: str
    from_status: ModelStatus
    to_status: ModelStatus
    promoted_at: float = field(default_factory=time.time)
    promoted_by: str = ""
    reason: str = ""
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class PredictionLog:
    """Log of predictions for monitoring."""
    model_version: str
    prediction: Any
    confidence: Optional[float] = None
    input_features: Dict[str, Any] = field(default_factory=dict)
    actual_value: Optional[Any] = None
    timestamp: float = field(default_factory=time.time)
    request_id: str = ""


class ModelVersion:
    """Represents a specific version of a model."""
    
    def __init__(self, metadata: ModelMetadata):
        self.metadata = metadata
        self.lock = RLock()
    
    def add_metric(self, metric: PerformanceMetric) -> None:
        """Add performance metric."""
        with self.lock:
            self.metadata.performance_metrics.append(metric)
    
    def add_artifact(self, artifact: ModelArtifact) -> None:
        """Add model artifact."""
        with self.lock:
            self.metadata.artifacts.append(artifact)
    
    def get_best_metric(self, metric_type: MetricType, split: str = "test") -> Optional[float]:
        """Get best value for metric type."""
        with self.lock:
            matching = [m.value for m in self.metadata.performance_metrics 
                       if m.metric_type == metric_type and m.split == split]
            return max(matching) if matching else None
    
    def get_all_metrics(self) -> Dict[str, float]:
        """Get all metrics as dict."""
        with self.lock:
            return {m.metric_type.value: m.value for m in self.metadata.performance_metrics}
    
    def promote(self, to_status: ModelStatus, promoted_by: str = "", reason: str = "") -> ModelPromotion:
        """Promote model to new status."""
        with self.lock:
            from_status = self.metadata.status
            self.metadata.status = to_status
            
            if to_status == ModelStatus.PRODUCTION:
                self.metadata.promoted_at = time.time()
            
            return ModelPromotion(
                model_version=self.metadata.version,
                from_status=from_status,
                to_status=to_status,
                promoted_by=promoted_by,
                reason=reason,
                metrics=self.get_all_metrics()
            )
    
    def add_tag(self, tag: str) -> None:
        """Add tag to model."""
        with self.lock:
            if tag not in self.metadata.tags:
                self.metadata.tags.append(tag)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        with self.lock:
            return {
                "model_name": self.metadata.model_name,
                "version": self.metadata.version,
                "status": self.metadata.status.value,
                "framework": self.metadata.framework,
                "task_type": self.metadata.task_type,
                "created_at": self.metadata.created_at,
                "trained_at": self.metadata.trained_at,
                "promoted_at": self.metadata.promoted_at,
                "description": self.metadata.description,
                "author": self.metadata.author,
                "feature_set": self.metadata.feature_set,
                "metrics": self.get_all_metrics(),
                "tags": self.metadata.tags,
                "artifact_count": len(self.metadata.artifacts)
            }


class ModelRegistry:
    """Central model registry for managing versions and artifacts."""
    
    def __init__(self):
        self.models: Dict[str, Dict[str, ModelVersion]] = defaultdict(dict)  # model_name -> version -> ModelVersion
        self.production_models: Dict[str, str] = {}  # model_name -> version
        self.ab_tests: Dict[str, ABTestConfig] = {}
        self.promotion_history: List[ModelPromotion] = []
        self.prediction_logs: deque = deque(maxlen=100000)
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = RLock()
        self.statistics = {
            "models_registered": 0,
            "versions_created": 0,
            "promotions": 0,
            "ab_tests_created": 0,
            "predictions_logged": 0,
            "artifacts_stored": 0
        }
    
    def register_model(self, model_name: str, version: str, framework: str, 
                      task_type: str, author: str = "", description: str = "") -> Optional[ModelVersion]:
        """Register new model version."""
        with self.lock:
            if version in self.models[model_name]:
                return None  # Version already exists
            
            metadata = ModelMetadata(
                model_name=model_name,
                version=version,
                status=ModelStatus.DEVELOPMENT,
                framework=framework,
                task_type=task_type,
                author=author,
                description=description
            )
            
            model_version = ModelVersion(metadata)
            self.models[model_name][version] = model_version
            self.statistics["models_registered"] += 1
            self.statistics["versions_created"] += 1
            self._trigger_callback("model_registered", model_name, version)
        
        return model_version
    
    def get_model_version(self, model_name: str, version: str) -> Optional[ModelVersion]:
        """Get specific model version."""
        with self.lock:
            return self.models.get(model_name, {}).get(version)
    
    def get_model_versions(self, model_name: str, status: Optional[ModelStatus] = None) -> List[ModelVersion]:
        """Get all versions of a model, optionally filtered by status."""
        with self.lock:
            versions = list(self.models.get(model_name, {}).values())
            if status:
                versions = [v for v in versions if v.metadata.status == status]
            return versions
    
    def get_production_model(self, model_name: str) -> Optional[ModelVersion]:
        """Get production version of model."""
        with self.lock:
            version = self.production_models.get(model_name)
            if version:
                return self.models.get(model_name, {}).get(version)
        return None
    
    def add_performance_metric(self, model_name: str, version: str, metric: PerformanceMetric) -> bool:
        """Add performance metric to model."""
        model = self.get_model_version(model_name, version)
        if not model:
            return False
        
        model.add_metric(metric)
        self._trigger_callback("metric_added", model_name, version, metric.metric_type.value)
        return True
    
    def upload_artifact(self, model_name: str, version: str, artifact: ModelArtifact) -> bool:
        """Upload model artifact."""
        model = self.get_model_version(model_name, version)
        if not model:
            return False
        
        with self.lock:
            model.add_artifact(artifact)
            self.statistics["artifacts_stored"] += 1
        
        self._trigger_callback("artifact_uploaded", model_name, version, artifact.artifact_type.value)
        return True
    
    def promote_model(self, model_name: str, version: str, to_status: ModelStatus,
                     promoted_by: str = "", reason: str = "") -> Optional[ModelPromotion]:
        """Promote model to new status."""
        model = self.get_model_version(model_name, version)
        if not model:
            return None
        
        promotion = model.promote(to_status, promoted_by, reason)
        
        with self.lock:
            self.promotion_history.append(promotion)
            if to_status == ModelStatus.PRODUCTION:
                self.production_models[model_name] = version
            self.statistics["promotions"] += 1
        
        self._trigger_callback("model_promoted", model_name, version, to_status.value)
        return promotion
    
    def create_ab_test(self, test_id: str, model_a: str, model_b: str, traffic_split: float) -> Optional[ABTestConfig]:
        """Create A/B test between two models."""
        # Format: model_name:version
        parts_a = model_a.split(":")
        parts_b = model_b.split(":")
        
        if len(parts_a) != 2 or len(parts_b) != 2:
            return None
        
        model_a_obj = self.get_model_version(parts_a[0], parts_a[1])
        model_b_obj = self.get_model_version(parts_b[0], parts_b[1])
        
        if not model_a_obj or not model_b_obj:
            return None
        
        with self.lock:
            ab_test = ABTestConfig(
                test_id=test_id,
                model_a=model_a,
                model_b=model_b,
                traffic_split=max(0.0, min(1.0, traffic_split))
            )
            self.ab_tests[test_id] = ab_test
            self.statistics["ab_tests_created"] += 1
        
        self._trigger_callback("ab_test_created", test_id, model_a, model_b)
        return ab_test
    
    def get_ab_test(self, test_id: str) -> Optional[ABTestConfig]:
        """Get A/B test configuration."""
        with self.lock:
            return self.ab_tests.get(test_id)
    
    def end_ab_test(self, test_id: str, winner: str) -> bool:
        """End A/B test and declare winner."""
        with self.lock:
            if test_id not in self.ab_tests:
                return False
            
            ab_test = self.ab_tests[test_id]
            ab_test.ended_at = time.time()
            ab_test.winner = winner
        
        self._trigger_callback("ab_test_ended", test_id, winner)
        return True
    
    def log_prediction(self, model_name: str, version: str, log: PredictionLog) -> None:
        """Log prediction for monitoring."""
        log.model_version = f"{model_name}:{version}"
        with self.lock:
            self.prediction_logs.append(log)
            self.statistics["predictions_logged"] += 1
    
    def get_prediction_logs(self, model_name: str, version: str, limit: int = 1000) -> List[PredictionLog]:
        """Get recent prediction logs for model."""
        with self.lock:
            target_version = f"{model_name}:{version}"
            return [log for log in self.prediction_logs if log.model_version == target_version][-limit:]
    
    def rollback_model(self, model_name: str, to_version: str) -> bool:
        """Rollback to previous production model."""
        model = self.get_model_version(model_name, to_version)
        if not model:
            return False
        
        # Set new version to production
        return self.promote_model(model_name, to_version, ModelStatus.PRODUCTION, 
                                 reason="Rollback") is not None
    
    def get_model_comparison(self, model_name: str, versions: List[str]) -> Dict[str, Dict[str, Any]]:
        """Compare multiple model versions."""
        comparison = {}
        for version in versions:
            model = self.get_model_version(model_name, version)
            if model:
                comparison[version] = model.to_dict()
        return comparison
    
    def get_promotion_history(self, model_name: str, limit: int = 100) -> List[ModelPromotion]:
        """Get promotion history for model."""
        with self.lock:
            return [p for p in self.promotion_history if p.model_version.startswith(model_name)][-limit:]
    
    def get_all_models(self) -> Dict[str, List[str]]:
        """Get all registered models and their versions."""
        with self.lock:
            return {name: list(versions.keys()) for name, versions in self.models.items()}
    
    def get_model_lineage(self, model_name: str, version: str) -> Dict[str, Any]:
        """Get model lineage and dependencies."""
        model = self.get_model_version(model_name, version)
        if not model:
            return {}
        
        return {
            "model": f"{model_name}:{version}",
            "created_at": model.metadata.created_at,
            "trained_at": model.metadata.trained_at,
            "feature_set": model.metadata.feature_set,
            "framework": model.metadata.framework,
            "task_type": model.metadata.task_type,
            "dependencies": model.metadata.dependencies,
            "artifact_count": len(model.metadata.artifacts),
            "metric_count": len(model.metadata.performance_metrics)
        }
    
    def delete_model_version(self, model_name: str, version: str) -> bool:
        """Delete model version (archived)."""
        model = self.get_model_version(model_name, version)
        if not model:
            return False
        
        with self.lock:
            # Don't actually delete, just archive
            model.metadata.status = ModelStatus.ARCHIVED
        
        self._trigger_callback("model_archived", model_name, version)
        return True
    
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
        """Get registry statistics."""
        with self.lock:
            total_versions = sum(len(v) for v in self.models.values())
            production_count = len(self.production_models)
            return {
                **self.statistics,
                "total_models": len(self.models),
                "total_versions": total_versions,
                "production_models": production_count,
                "active_ab_tests": len([t for t in self.ab_tests.values() if t.ended_at is None])
            }


# Singleton instance
_model_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get or create model registry instance."""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry
