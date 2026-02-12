"""
Feature Engineering Service - Extract and transform features from raw events for ML models.

Supports time-based features, windowed aggregations, feature scaling, selection, and importance analysis.
Integrates with event stream and aggregation services for real-time feature computation.
"""

import time
import statistics
import numpy as np
from enum import Enum
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from threading import RLock
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json


class FeatureType(Enum):
    """Types of features that can be extracted."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    AGGREGATED = "aggregated"
    BEHAVIORAL = "behavioral"
    INTERACTION = "interaction"


class AggregationMethod(Enum):
    """Methods for aggregating features over windows."""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    STDDEV = "stddev"
    P50 = "p50"
    P95 = "p95"
    P99 = "p99"
    DISTINCT_COUNT = "distinct_count"


class ScalingMethod(Enum):
    """Feature scaling methods."""
    NONE = "none"
    MIN_MAX = "min_max"
    STANDARD = "standard"
    LOG = "log"
    ROBUST = "robust"


class FeatureImportanceMethod(Enum):
    """Methods for computing feature importance."""
    VARIANCE = "variance"
    CORRELATION = "correlation"
    MUTUAL_INFO = "mutual_info"
    PERMUTATION = "permutation"
    SHAP = "shap"


@dataclass
class FeatureDefinition:
    """Defines how to extract a feature from events."""
    feature_name: str
    feature_type: FeatureType
    source_field: Optional[str] = None
    transformations: List[Callable] = field(default_factory=list)
    aggregation: Optional[AggregationMethod] = None
    window_size: Optional[int] = None  # in seconds
    scaling: ScalingMethod = ScalingMethod.NONE
    required: bool = True
    default_value: Any = None
    description: str = ""


@dataclass
class Feature:
    """Computed feature value."""
    feature_name: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureVector:
    """Vector of features for a single entity."""
    entity_id: str
    features: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureEngineering:
    """Output from feature engineering."""
    source: str
    entity_id: str
    features: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    versions: Dict[str, str] = field(default_factory=dict)  # feature versions


@dataclass
class ScalingParams:
    """Parameters for feature scaling."""
    method: ScalingMethod
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    mean: Optional[float] = None
    stddev: Optional[float] = None
    q1: Optional[float] = None
    q3: Optional[float] = None


@dataclass
class FeatureImportance:
    """Feature importance scores."""
    feature_name: str
    importance_score: float
    method: FeatureImportanceMethod
    timestamp: float = field(default_factory=time.time)


class FeatureWindow:
    """Time-based window for aggregating feature values."""
    
    def __init__(self, window_size: int):
        """window_size in seconds."""
        self.window_size = window_size
        self.values = deque(maxlen=1000)
        self.lock = RLock()
    
    def add_value(self, value: float, timestamp: Optional[float] = None) -> None:
        """Add value to window."""
        if timestamp is None:
            timestamp = time.time()
        with self.lock:
            self.values.append((value, timestamp))
    
    def get_current_values(self) -> List[float]:
        """Get values within current window."""
        now = time.time()
        cutoff = now - self.window_size
        with self.lock:
            return [v for v, t in self.values if t >= cutoff]
    
    def aggregate(self, method: AggregationMethod) -> Optional[float]:
        """Compute aggregation over window."""
        values = self.get_current_values()
        if not values:
            return None
        
        if method == AggregationMethod.SUM:
            return sum(values)
        elif method == AggregationMethod.AVG:
            return sum(values) / len(values)
        elif method == AggregationMethod.MIN:
            return min(values)
        elif method == AggregationMethod.MAX:
            return max(values)
        elif method == AggregationMethod.COUNT:
            return float(len(values))
        elif method == AggregationMethod.STDDEV:
            return statistics.stdev(values) if len(values) > 1 else 0.0
        elif method == AggregationMethod.P50:
            return np.percentile(values, 50)
        elif method == AggregationMethod.P95:
            return np.percentile(values, 95)
        elif method == AggregationMethod.P99:
            return np.percentile(values, 99)
        elif method == AggregationMethod.DISTINCT_COUNT:
            return float(len(set(values)))
        
        return None


class FeatureSet:
    """Collection of features with metadata."""
    
    def __init__(self, set_name: str):
        self.set_name = set_name
        self.features: Dict[str, FeatureDefinition] = {}
        self.windows: Dict[str, Dict[str, FeatureWindow]] = {}  # entity_id -> feature_name -> window
        self.scaling_params: Dict[str, ScalingParams] = {}
        self.lock = RLock()
    
    def register_feature(self, definition: FeatureDefinition) -> None:
        """Register feature definition."""
        with self.lock:
            self.features[definition.feature_name] = definition
    
    def update_feature_values(self, entity_id: str, feature_name: str, value: float) -> None:
        """Update windowed value for feature."""
        if feature_name not in self.features:
            return
        
        definition = self.features[feature_name]
        if definition.aggregation is None or definition.window_size is None:
            return
        
        with self.lock:
            if entity_id not in self.windows:
                self.windows[entity_id] = {}
            if feature_name not in self.windows[entity_id]:
                self.windows[entity_id][feature_name] = FeatureWindow(definition.window_size)
            
            self.windows[entity_id][feature_name].add_value(value)
    
    def get_feature_value(self, entity_id: str, feature_name: str) -> Optional[Any]:
        """Get current feature value (aggregated if windowed)."""
        if feature_name not in self.features:
            return None
        
        definition = self.features[feature_name]
        
        with self.lock:
            if entity_id in self.windows and feature_name in self.windows[entity_id]:
                window = self.windows[entity_id][feature_name]
                return window.aggregate(definition.aggregation) if definition.aggregation else None
        
        return definition.default_value
    
    def get_all_features(self, entity_id: str) -> Dict[str, Any]:
        """Get all feature values for entity."""
        features = {}
        with self.lock:
            for feature_name in self.features:
                value = self.get_feature_value(entity_id, feature_name)
                if value is not None:
                    features[feature_name] = value
        return features
    
    def set_scaling_params(self, feature_name: str, params: ScalingParams) -> None:
        """Set scaling parameters for feature."""
        with self.lock:
            self.scaling_params[feature_name] = params
    
    def scale_value(self, feature_name: str, value: float) -> float:
        """Apply scaling to feature value."""
        if feature_name not in self.scaling_params:
            return value
        
        params = self.scaling_params[feature_name]
        
        if params.method == ScalingMethod.NONE:
            return value
        elif params.method == ScalingMethod.MIN_MAX:
            if params.min_val is None or params.max_val is None:
                return value
            range_val = params.max_val - params.min_val
            if range_val == 0:
                return 0.0
            return (value - params.min_val) / range_val
        elif params.method == ScalingMethod.STANDARD:
            if params.mean is None or params.stddev is None:
                return value
            if params.stddev == 0:
                return 0.0
            return (value - params.mean) / params.stddev
        elif params.method == ScalingMethod.LOG:
            return np.log(max(value, 1e-10))
        elif params.method == ScalingMethod.ROBUST:
            if params.q1 is None or params.q3 is None:
                return value
            iqr = params.q3 - params.q1
            if iqr == 0:
                return 0.0
            median = (params.q1 + params.q3) / 2
            return (value - median) / iqr
        
        return value


class FeatureEngineer:
    """Main feature engineering service."""
    
    def __init__(self):
        self.feature_sets: Dict[str, FeatureSet] = {}
        self.feature_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.preprocessing_stats: Dict[str, Dict[str, float]] = {}
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = RLock()
        self.statistics = {
            "feature_sets_created": 0,
            "features_registered": 0,
            "features_computed": 0,
            "entities_processed": 0,
            "average_computation_time_ms": 0.0
        }
    
    def create_feature_set(self, set_name: str) -> str:
        """Create new feature set."""
        with self.lock:
            if set_name in self.feature_sets:
                return set_name
            
            self.feature_sets[set_name] = FeatureSet(set_name)
            self.statistics["feature_sets_created"] += 1
            self._trigger_callback("feature_set_created", set_name)
        
        return set_name
    
    def register_feature(self, set_name: str, definition: FeatureDefinition) -> bool:
        """Register feature in set."""
        with self.lock:
            if set_name not in self.feature_sets:
                return False
            
            self.feature_sets[set_name].register_feature(definition)
            self.statistics["features_registered"] += 1
            self._trigger_callback("feature_registered", set_name, definition.feature_name)
        
        return True
    
    def extract_features_from_event(self, set_name: str, event: Dict[str, Any]) -> Optional[FeatureVector]:
        """Extract features from single event."""
        if set_name not in self.feature_sets:
            return None
        
        start_time = time.time()
        feature_set = self.feature_sets[set_name]
        entity_id = event.get("entity_id", event.get("user_id", "unknown"))
        features = {}
        
        with self.lock:
            for feature_name, definition in feature_set.features.items():
                value = self._extract_single_feature(definition, event)
                if value is not None:
                    # Apply scaling if configured
                    if isinstance(value, (int, float)):
                        value = feature_set.scale_value(feature_name, value)
                    features[feature_name] = value
                    
                    # Update windowed values
                    if definition.aggregation and definition.window_size:
                        if isinstance(value, (int, float)):
                            feature_set.update_feature_values(entity_id, feature_name, value)
            
            # Store in history
            self.feature_history[set_name].append({
                "entity_id": entity_id,
                "features": features,
                "timestamp": time.time()
            })
            
            self.statistics["features_computed"] += 1
            self.statistics["entities_processed"] += 1
        
        elapsed_ms = (time.time() - start_time) * 1000
        self.statistics["average_computation_time_ms"] = elapsed_ms
        
        return FeatureVector(
            entity_id=entity_id,
            features=features,
            timestamp=time.time()
        )
    
    def _extract_single_feature(self, definition: FeatureDefinition, event: Dict[str, Any]) -> Optional[Any]:
        """Extract single feature from event."""
        value = event.get(definition.source_field) if definition.source_field else event
        
        if value is None:
            return definition.default_value
        
        # Apply transformations
        for transform in definition.transformations:
            try:
                value = transform(value)
            except:
                return definition.default_value
        
        # Extract temporal features
        if definition.feature_type == FeatureType.TEMPORAL:
            if isinstance(value, (int, float)):
                value = self._extract_temporal_features(value, definition.feature_name)
        
        return value
    
    def _extract_temporal_features(self, timestamp: float, feature_name: str) -> Optional[Any]:
        """Extract temporal features from timestamp."""
        try:
            dt = datetime.fromtimestamp(timestamp)
            
            if "hour" in feature_name.lower():
                return float(dt.hour)
            elif "day_of_week" in feature_name.lower():
                return float(dt.weekday())
            elif "is_weekend" in feature_name.lower():
                return 1.0 if dt.weekday() >= 5 else 0.0
            elif "month" in feature_name.lower():
                return float(dt.month)
            elif "day_of_month" in feature_name.lower():
                return float(dt.day)
            elif "quarter" in feature_name.lower():
                return float((dt.month - 1) // 3 + 1)
            elif "is_business_hour" in feature_name.lower():
                return 1.0 if 9 <= dt.hour < 17 else 0.0
        except:
            pass
        
        return None
    
    def compute_feature_importance(self, set_name: str, method: FeatureImportanceMethod = FeatureImportanceMethod.VARIANCE) -> List[FeatureImportance]:
        """Compute feature importance scores."""
        if set_name not in self.feature_sets:
            return []
        
        importance_list = []
        feature_set = self.feature_sets[set_name]
        history = self.feature_history.get(set_name, [])
        
        if not history:
            return []
        
        # Collect all feature values
        feature_values = defaultdict(list)
        for record in history:
            for fname, fvalue in record.get("features", {}).items():
                if isinstance(fvalue, (int, float)):
                    feature_values[fname].append(fvalue)
        
        # Compute importance based on method
        for feature_name, values in feature_values.items():
            if not values:
                continue
            
            if method == FeatureImportanceMethod.VARIANCE:
                importance = statistics.variance(values) if len(values) > 1 else 0.0
            elif method == FeatureImportanceMethod.CORRELATION:
                # Simple: correlation with first feature as target
                importance = abs(np.corrcoef(values, range(len(values)))[0, 1]) if len(values) > 1 else 0.0
            else:
                importance = 1.0 / (1.0 + len(values))
            
            importance_list.append(FeatureImportance(
                feature_name=feature_name,
                importance_score=importance,
                method=method
            ))
        
        # Sort by importance
        importance_list.sort(key=lambda x: x.importance_score, reverse=True)
        return importance_list
    
    def compute_scaling_statistics(self, set_name: str, method: ScalingMethod = ScalingMethod.STANDARD) -> Dict[str, ScalingParams]:
        """Compute scaling parameters from historical data."""
        if set_name not in self.feature_sets:
            return {}
        
        feature_set = self.feature_sets[set_name]
        history = self.feature_history.get(set_name, [])
        params_dict = {}
        
        # Collect feature statistics
        feature_values = defaultdict(list)
        for record in history:
            for fname, fvalue in record.get("features", {}).items():
                if isinstance(fvalue, (int, float)):
                    feature_values[fname].append(fvalue)
        
        # Compute scaling parameters
        for feature_name, values in feature_values.items():
            if not values:
                continue
            
            if method == ScalingMethod.MIN_MAX:
                params = ScalingParams(
                    method=method,
                    min_val=min(values),
                    max_val=max(values)
                )
            elif method == ScalingMethod.STANDARD:
                params = ScalingParams(
                    method=method,
                    mean=statistics.mean(values),
                    stddev=statistics.stdev(values) if len(values) > 1 else 1.0
                )
            elif method == ScalingMethod.ROBUST:
                sorted_vals = sorted(values)
                q1_idx = len(sorted_vals) // 4
                q3_idx = 3 * len(sorted_vals) // 4
                params = ScalingParams(
                    method=method,
                    q1=sorted_vals[q1_idx],
                    q3=sorted_vals[q3_idx]
                )
            else:
                params = ScalingParams(method=ScalingMethod.NONE)
            
            feature_set.set_scaling_params(feature_name, params)
            params_dict[feature_name] = params
        
        return params_dict
    
    def get_feature_set(self, set_name: str) -> Optional[FeatureSet]:
        """Get feature set by name."""
        with self.lock:
            return self.feature_sets.get(set_name)
    
    def delete_feature_set(self, set_name: str) -> bool:
        """Delete feature set."""
        with self.lock:
            if set_name in self.feature_sets:
                del self.feature_sets[set_name]
                if set_name in self.feature_history:
                    del self.feature_history[set_name]
                self._trigger_callback("feature_set_deleted", set_name)
                return True
        return False
    
    def get_feature_history(self, set_name: str, limit: int = 100) -> List[Dict]:
        """Get recent feature computations."""
        with self.lock:
            history = self.feature_history.get(set_name, [])
            return list(history)[-limit:]
    
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
        """Get service statistics."""
        with self.lock:
            return {
                **self.statistics,
                "feature_sets": len(self.feature_sets),
                "total_features": sum(len(fs.features) for fs in self.feature_sets.values())
            }


# Singleton instance
_feature_engineer: Optional[FeatureEngineer] = None


def get_feature_engineer() -> FeatureEngineer:
    """Get or create feature engineer instance."""
    global _feature_engineer
    if _feature_engineer is None:
        _feature_engineer = FeatureEngineer()
    return _feature_engineer
