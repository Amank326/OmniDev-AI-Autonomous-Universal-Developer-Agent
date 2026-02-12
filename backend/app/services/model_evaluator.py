"""
Model Evaluator - Comprehensive evaluation of model performance with drift detection and monitoring.

Computes classification/regression metrics, detects data drift, monitors model performance over time,
and identifies when retraining is needed.
"""

import time
import statistics
import numpy as np
from enum import Enum
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from threading import RLock
from collections import defaultdict, deque
from datetime import datetime


class EvaluationMetric(Enum):
    """Classification/regression metrics."""
    # Classification
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1 = "f1"
    ROC_AUC = "roc_auc"
    PR_AUC = "pr_auc"
    LOG_LOSS = "log_loss"
    CONFUSION_MATRIX = "confusion_matrix"
    
    # Regression
    MSE = "mse"
    RMSE = "rmse"
    MAE = "mae"
    MAPE = "mape"
    R2 = "r2"
    PEARSON_CORR = "pearson_corr"


class DriftType(Enum):
    """Types of data/concept drift."""
    COVARIATE_SHIFT = "covariate_shift"
    PRIOR_SHIFT = "prior_shift"
    CONCEPT_DRIFT = "concept_drift"
    NO_DRIFT = "no_drift"


class DriftDetectionMethod(Enum):
    """Methods for drift detection."""
    KL_DIVERGENCE = "kl_divergence"
    JS_DIVERGENCE = "js_divergence"
    KOLMOGOROV_SMIRNOV = "kolmogorov_smirnov"
    CHI_SQUARE = "chi_square"
    WASSERSTEIN = "wasserstein"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """Single metric measurement."""
    metric_name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    dataset: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ConfusionMatrixData:
    """Confusion matrix for classification."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    true_negatives: int = 0


@dataclass
class EvaluationResult:
    """Complete evaluation result."""
    model_version: str
    evaluation_timestamp: float = field(default_factory=time.time)
    dataset_name: str = ""
    sample_count: int = 0
    metrics: Dict[str, float] = field(default_factory=dict)
    per_class_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    confusion_matrices: Dict[str, ConfusionMatrixData] = field(default_factory=dict)
    threshold: float = 0.5
    notes: str = ""


@dataclass
class DriftAlert:
    """Alert for detected drift."""
    alert_id: str
    drift_type: DriftType
    severity: AlertSeverity
    message: str
    metric_name: str
    threshold_value: float
    actual_value: float
    detected_at: float = field(default_factory=time.time)
    model_version: str = ""


@dataclass
class RegressionMetrics:
    """Regression performance metrics."""
    mse: float
    rmse: float
    mae: float
    mape: float
    r2: float


@dataclass
class ClassificationMetrics:
    """Classification performance metrics."""
    accuracy: float
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    auc_roc: float = 0.0
    auc_pr: float = 0.0
    log_loss: float = 0.0


class ModelEvaluator:
    """Evaluate and monitor model performance."""
    
    def __init__(self):
        self.evaluations: Dict[str, EvaluationResult] = {}
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.drift_alerts: deque = deque(maxlen=10000)
        self.baseline_metrics: Dict[str, Dict[str, float]] = {}  # model_v -> metric -> value
        self.drift_thresholds: Dict[str, float] = defaultdict(lambda: 0.1)
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = RLock()
        self.statistics = {
            "evaluations_completed": 0,
            "drift_detections": 0,
            "alerts_triggered": 0,
            "average_model_accuracy": 0.0
        }
    
    def evaluate_model(self, predictions: List[Any], actuals: List[Any], 
                      model_version: str, dataset_name: str = "", 
                      task_type: str = "classification") -> Optional[EvaluationResult]:
        """Evaluate model predictions against actuals."""
        if len(predictions) != len(actuals):
            return None
        
        eval_id = f"{model_version}_{int(time.time() * 1000)}"
        
        if task_type == "classification":
            metrics = self._compute_classification_metrics(predictions, actuals)
        elif task_type == "regression":
            metrics = self._compute_regression_metrics(predictions, actuals)
        else:
            metrics = {}
        
        result = EvaluationResult(
            model_version=model_version,
            dataset_name=dataset_name,
            sample_count=len(predictions),
            metrics=metrics
        )
        
        with self.lock:
            self.evaluations[eval_id] = result
            self.statistics["evaluations_completed"] += 1
            
            # Store in metric history
            for metric_name, value in metrics.items():
                metric_point = MetricPoint(
                    metric_name=metric_name,
                    value=value,
                    dataset=dataset_name,
                    tags={"model_version": model_version}
                )
                self.metric_history[metric_name].append(metric_point)
        
        # Check for regression
        if model_version in self.baseline_metrics:
            self._check_metric_regression(model_version, metrics)
        else:
            # Set baseline
            with self.lock:
                self.baseline_metrics[model_version] = metrics.copy()
        
        self._trigger_callback("evaluation_completed", eval_id, metrics)
        return result
    
    def _compute_classification_metrics(self, predictions: List[Any], actuals: List[Any]) -> Dict[str, float]:
        """Compute classification metrics."""
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        
        accuracy = np.mean(predictions == actuals)
        
        # Binary classification metrics
        if len(np.unique(actuals)) == 2:
            tp = np.sum((predictions == 1) & (actuals == 1))
            fp = np.sum((predictions == 1) & (actuals == 0))
            fn = np.sum((predictions == 0) & (actuals == 1))
            tn = np.sum((predictions == 0) & (actuals == 0))
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        else:
            precision = recall = f1 = accuracy
        
        return {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1)
        }
    
    def _compute_regression_metrics(self, predictions: List[float], actuals: List[float]) -> Dict[str, float]:
        """Compute regression metrics."""
        predictions = np.array(predictions, dtype=float)
        actuals = np.array(actuals, dtype=float)
        
        mse = np.mean((predictions - actuals) ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(predictions - actuals))
        
        # MAPE: avoid division by zero
        nonzero_mask = actuals != 0
        if np.any(nonzero_mask):
            mape = np.mean(np.abs((predictions[nonzero_mask] - actuals[nonzero_mask]) / actuals[nonzero_mask]))
        else:
            mape = 0.0
        
        # R²
        ss_res = np.sum((actuals - predictions) ** 2)
        ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return {
            "mse": float(mse),
            "rmse": float(rmse),
            "mae": float(mae),
            "mape": float(mape),
            "r2": float(r2)
        }
    
    def _check_metric_regression(self, model_version: str, current_metrics: Dict[str, float]) -> None:
        """Check if metrics have regressed compared to baseline."""
        baseline = self.baseline_metrics.get(model_version, {})
        
        for metric_name, current_value in current_metrics.items():
            baseline_value = baseline.get(metric_name, current_value)
            
            # Determine if regression (lower is worse for accuracy, precision, recall, f1, auc, r2)
            negative_metrics = {"mse", "rmse", "mae", "mape", "log_loss"}
            positive_metrics = {"accuracy", "precision", "recall", "f1", "auc_roc", "auc_pr", "r2"}
            
            threshold = self.drift_thresholds.get(metric_name, 0.05)
            
            if metric_name in positive_metrics:
                regression = baseline_value - current_value > threshold
            elif metric_name in negative_metrics:
                regression = current_value - baseline_value > threshold
            else:
                regression = False
            
            if regression:
                self._trigger_callback("metric_regression_detected", model_version, metric_name, 
                                      baseline_value, current_value)
    
    def detect_data_drift(self, training_data: List[float], serving_data: List[float],
                         model_version: str, feature_name: str = "",
                         method: DriftDetectionMethod = DriftDetectionMethod.KOLMOGOROV_SMIRNOV) -> Optional[DriftAlert]:
        """Detect data drift using statistical test."""
        training_data = np.array(training_data, dtype=float)
        serving_data = np.array(serving_data, dtype=float)
        
        # Compute drift metric based on method
        if method == DriftDetectionMethod.KOLMOGOROV_SMIRNOV:
            # Simple KS-like statistic
            drift_stat = np.abs(np.mean(training_data) - np.mean(serving_data)) / (np.std(training_data) + 1e-10)
            threshold = 2.0
        elif method == DriftDetectionMethod.KL_DIVERGENCE:
            # Simple approximation
            drift_stat = np.abs(np.log(np.std(serving_data) / (np.std(training_data) + 1e-10)))
            threshold = 0.5
        else:
            drift_stat = abs(np.mean(serving_data) - np.mean(training_data))
            threshold = np.std(training_data) * 2
        
        drift_detected = drift_stat > threshold
        
        if drift_detected:
            alert_id = f"drift_{int(time.time() * 1000)}"
            alert = DriftAlert(
                alert_id=alert_id,
                drift_type=DriftType.COVARIATE_SHIFT,
                severity=AlertSeverity.WARNING if drift_stat < threshold * 2 else AlertSeverity.CRITICAL,
                message=f"Data drift detected in {feature_name}",
                metric_name=feature_name,
                threshold_value=threshold,
                actual_value=drift_stat,
                model_version=model_version
            )
            
            with self.lock:
                self.drift_alerts.append(alert)
                self.statistics["drift_detections"] += 1
            
            self._trigger_callback("data_drift_detected", model_version, feature_name, drift_stat, threshold)
            return alert
        
        return None
    
    def get_evaluation_summary(self, model_version: str) -> Dict[str, Any]:
        """Get evaluation summary for model."""
        evals = [e for e in self.evaluations.values() if e.model_version == model_version]
        
        if not evals:
            return {}
        
        latest_eval = evals[-1]
        
        return {
            "model_version": model_version,
            "total_evaluations": len(evals),
            "latest_eval_timestamp": latest_eval.evaluation_timestamp,
            "latest_metrics": latest_eval.metrics,
            "baseline_metrics": self.baseline_metrics.get(model_version, {})
        }
    
    def get_metric_trend(self, metric_name: str, model_version: Optional[str] = None,
                        limit: int = 100) -> List[MetricPoint]:
        """Get trend for specific metric."""
        with self.lock:
            points = list(self.metric_history.get(metric_name, []))
            if model_version:
                points = [p for p in points if p.tags.get("model_version") == model_version]
            return points[-limit:]
    
    def get_metric_statistics(self, metric_name: str, window_size: int = 100) -> Dict[str, float]:
        """Get statistics for metric over recent window."""
        points = self.get_metric_trend(metric_name, limit=window_size)
        
        if not points:
            return {}
        
        values = [p.value for p in points]
        
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "min": min(values),
            "max": max(values),
            "median": statistics.median(values)
        }
    
    def get_drift_alerts(self, model_version: Optional[str] = None, severity: Optional[AlertSeverity] = None,
                        limit: int = 100) -> List[DriftAlert]:
        """Get recent drift alerts."""
        with self.lock:
            alerts = list(self.drift_alerts)
            
            if model_version:
                alerts = [a for a in alerts if a.model_version == model_version]
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            
            return alerts[-limit:]
    
    def set_baseline_metrics(self, model_version: str, metrics: Dict[str, float]) -> None:
        """Set baseline metrics for model."""
        with self.lock:
            self.baseline_metrics[model_version] = metrics.copy()
    
    def set_drift_threshold(self, metric_name: str, threshold: float) -> None:
        """Set drift detection threshold for metric."""
        with self.lock:
            self.drift_thresholds[metric_name] = threshold
    
    def is_model_performing_well(self, model_version: str, min_accuracy: float = 0.8) -> bool:
        """Check if model is performing above threshold."""
        baseline = self.baseline_metrics.get(model_version, {})
        accuracy = baseline.get("accuracy", 0.0)
        return accuracy >= min_accuracy
    
    def should_retrain(self, model_version: str, 
                      metric_regression_threshold: float = 0.05) -> bool:
        """Determine if model should be retrained."""
        # Check recent metrics vs baseline
        evals = [e for e in self.evaluations.values() if e.model_version == model_version]
        
        if not evals:
            return False
        
        baseline = self.baseline_metrics.get(model_version, {})
        recent_metrics = evals[-1].metrics
        
        # If any metric has regressed beyond threshold, recommend retraining
        for metric_name in ["accuracy", "f1", "r2"]:
            if metric_name in baseline and metric_name in recent_metrics:
                regression = baseline[metric_name] - recent_metrics[metric_name]
                if regression > metric_regression_threshold:
                    return True
        
        return False
    
    def get_all_evaluations(self, model_version: Optional[str] = None) -> List[EvaluationResult]:
        """Get all evaluations."""
        evals = list(self.evaluations.values())
        if model_version:
            evals = [e for e in evals if e.model_version == model_version]
        return evals
    
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
        """Get evaluator statistics."""
        with self.lock:
            return {
                **self.statistics,
                "total_evaluations": len(self.evaluations),
                "total_drift_alerts": len(self.drift_alerts),
                "monitored_metrics": len(self.metric_history)
            }


# Singleton instance
_model_evaluator: Optional[ModelEvaluator] = None


def get_model_evaluator() -> ModelEvaluator:
    """Get or create model evaluator instance."""
    global _model_evaluator
    if _model_evaluator is None:
        _model_evaluator = ModelEvaluator()
    return _model_evaluator
