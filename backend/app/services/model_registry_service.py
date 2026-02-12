"""
Phase 35: Model Registry Service
Model versioning, metadata tracking, and release management

Features:
- Model artifact storage and versioning
- Model metadata and lineage tracking
- Model tags and annotations
- Release management and promotion
- Model deprecation handling
- Performance tracking across versions
- A/B test tracking
- Model comparison and diff
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import uuid
import threading
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model version status"""
    DRAFT = "draft"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class ReleaseStage(Enum):
    """Release stage"""
    DEV = "dev"
    STAGING = "staging"
    CANARY = "canary"
    PRODUCTION = "production"


@dataclass
class ModelArtifact:
    """Model artifact metadata"""
    artifact_id: str
    model_id: str
    version: int
    artifact_path: str  # Storage path
    artifact_size_bytes: int
    artifact_type: str  # weights, weights+config, full_model
    framework: str  # tensorflow, pytorch, sklearn, etc.
    framework_version: str
    created_at: float
    checksum: str  # Hash for integrity


@dataclass
class ModelMetrics:
    """Performance metrics for model version"""
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_roc: Optional[float] = None
    loss: Optional[float] = None
    custom_metrics: Dict[str, float] = field(default_factory=dict)
    test_dataset: Optional[str] = None
    evaluation_time: Optional[float] = None


@dataclass
class ModelInputOutput:
    """Input/output schema for model"""
    input_schema: Dict[str, Any]  # {feature_name: {type, shape, description}}
    output_schema: Dict[str, Any]  # {output_name: {type, shape, description}}
    example_input: Dict[str, Any]
    example_output: Dict[str, Any]


@dataclass
class ModelLineage:
    """Lineage information"""
    parent_model_id: Optional[str] = None
    parent_version: Optional[int] = None
    training_job_id: Optional[str] = None
    hyperparameter_search_id: Optional[str] = None
    dataset_version: Optional[str] = None
    code_version: Optional[str] = None  # Git commit hash
    training_timestamp: Optional[float] = None


@dataclass
class ModelVersion:
    """Complete model version"""
    model_id: str
    version: int
    name: str
    description: str
    status: ModelStatus
    artifact: ModelArtifact
    metrics: ModelMetrics
    input_output: ModelInputOutput
    lineage: ModelLineage
    tags: Dict[str, str] = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    created_by: Optional[str] = None
    updated_at: Optional[float] = None
    updated_by: Optional[str] = None
    deprecated_at: Optional[float] = None
    deprecation_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReleasePromotion:
    """Model promotion to release stage"""
    promotion_id: str
    model_id: str
    version: int
    from_stage: ReleaseStage
    to_stage: ReleaseStage
    promoted_at: float
    promoted_by: Optional[str] = None
    approval_status: str = "pending"  # pending, approved, rejected
    notes: Optional[str] = None


@dataclass
class ModelComparison:
    """Comparison between two model versions"""
    comparison_id: str
    model_id: str
    version1: int
    version2: int
    metrics_diff: Dict[str, Dict[str, float]]  # {metric: {v1, v2, diff, percent_change}}
    performance_improvement: float  # percentage
    recommendation: str  # same, upgrade, downgrade, not_comparable
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())


@dataclass
class ModelRegistry:
    """Main registry entry"""
    model_id: str
    workspace_id: str
    model_name: str
    description: Optional[str]
    task_type: str  # classification, regression, clustering, etc.
    framework: str
    created_at: float
    created_by: Optional[str]
    owner: Optional[str]


class ModelRegistryService:
    """
    Production-grade model registry with versioning and lineage tracking
    """
    
    def __init__(self, max_versions_per_model: int = 20):
        """
        Initialize registry service
        
        Args:
            max_versions_per_model: Maximum versions to keep per model
        """
        self.max_versions_per_model = max_versions_per_model
        
        self.registries: Dict[str, ModelRegistry] = {}
        self.versions: Dict[str, List[ModelVersion]] = defaultdict(list)  # model_id -> versions
        self.releases: Dict[str, ReleasePromotion] = {}
        self.release_mappings: Dict[str, Dict[str, int]] = defaultdict(dict)  # model_id -> {stage: version}
        self.comparisons: Dict[str, ModelComparison] = {}
        
        self.callbacks: Dict[str, List[callable]] = defaultdict(list)
        self.lock = threading.RLock()
        
        logger.info(f"ModelRegistryService initialized (max_versions: {max_versions_per_model})")
    
    def register_model(self, workspace_id: str, model_name: str, description: str,
                      task_type: str, framework: str,
                      created_by: Optional[str] = None,
                      owner: Optional[str] = None) -> str:
        """
        Register new model in registry
        
        Args:
            workspace_id: Workspace ID
            model_name: Model name
            description: Model description
            task_type: Task type (classification, regression, etc.)
            framework: ML framework
            created_by: Creator ID
            owner: Owner ID
            
        Returns:
            model_id: Unique model ID
        """
        model_id = str(uuid.uuid4())
        
        registry = ModelRegistry(
            model_id=model_id,
            workspace_id=workspace_id,
            model_name=model_name,
            description=description,
            task_type=task_type,
            framework=framework,
            created_at=datetime.utcnow().timestamp(),
            created_by=created_by,
            owner=owner
        )
        
        with self.lock:
            self.registries[model_id] = registry
            self.versions[model_id] = []
        
        logger.info(f"Model registered: {model_id} ({model_name})")
        self._broadcast_callback('model_registered', {
            'model_id': model_id,
            'model_name': model_name,
            'workspace_id': workspace_id
        })
        
        return model_id
    
    def create_version(self, model_id: str, artifact: ModelArtifact,
                      metrics: ModelMetrics, input_output: ModelInputOutput,
                      lineage: ModelLineage, created_by: Optional[str] = None,
                      tags: Optional[Dict[str, str]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Create new model version
        
        Args:
            model_id: Model ID
            artifact: Model artifact
            metrics: Performance metrics
            input_output: Input/output schema
            lineage: Training lineage
            created_by: Creator ID
            tags: Version tags
            metadata: Additional metadata
            
        Returns:
            version: Version number
        """
        with self.lock:
            if model_id not in self.registries:
                return -1
            
            current_versions = len(self.versions[model_id])
            version = current_versions + 1
            
            model_version = ModelVersion(
                model_id=model_id,
                version=version,
                name=f"{self.registries[model_id].model_name}_v{version}",
                description=f"Version {version}",
                status=ModelStatus.DRAFT,
                artifact=artifact,
                metrics=metrics,
                input_output=input_output,
                lineage=lineage,
                tags=tags or {},
                created_by=created_by,
                metadata=metadata or {}
            )
            
            self.versions[model_id].append(model_version)
            
            # Clean up old versions if needed
            if len(self.versions[model_id]) > self.max_versions_per_model:
                self.versions[model_id].pop(0)
        
        logger.info(f"Model version created: {model_id} v{version}")
        self._broadcast_callback('version_created', {
            'model_id': model_id,
            'version': version
        })
        
        return version
    
    def get_version(self, model_id: str, version: int) -> Optional[ModelVersion]:
        """Get specific model version"""
        with self.lock:
            versions = self.versions.get(model_id, [])
            for v in versions:
                if v.version == version:
                    return v
        return None
    
    def get_latest_version(self, model_id: str) -> Optional[ModelVersion]:
        """Get latest model version"""
        with self.lock:
            versions = self.versions.get(model_id, [])
            return versions[-1] if versions else None
    
    def get_all_versions(self, model_id: str, status: Optional[ModelStatus] = None) -> List[ModelVersion]:
        """Get all versions for model"""
        with self.lock:
            versions = self.versions.get(model_id, [])
            if status:
                versions = [v for v in versions if v.status == status]
            return list(versions)
    
    def list_models(self, workspace_id: str) -> List[ModelRegistry]:
        """List all models in workspace"""
        with self.lock:
            return [r for r in self.registries.values() if r.workspace_id == workspace_id]
    
    def update_version_status(self, model_id: str, version: int,
                             status: ModelStatus,
                             updated_by: Optional[str] = None) -> Dict[str, Any]:
        """Update version status"""
        with self.lock:
            model_version = self.get_version(model_id, version)
            if not model_version:
                return {'error': f'Version {version} not found'}
            
            model_version.status = status
            model_version.updated_at = datetime.utcnow().timestamp()
            model_version.updated_by = updated_by
            
            if status == ModelStatus.DEPRECATED:
                model_version.deprecated_at = datetime.utcnow().timestamp()
        
        logger.info(f"Version status updated: {model_id} v{version} -> {status.value}")
        
        return {
            'model_id': model_id,
            'version': version,
            'status': status.value
        }
    
    def add_tag(self, model_id: str, version: int, key: str, value: str) -> Dict[str, Any]:
        """Add tag to version"""
        with self.lock:
            model_version = self.get_version(model_id, version)
            if not model_version:
                return {'error': f'Version {version} not found'}
            
            model_version.tags[key] = value
        
        logger.debug(f"Tag added: {model_id} v{version} {key}={value}")
        return {'model_id': model_id, 'version': version, 'tag': key}
    
    def add_alias(self, model_id: str, version: int, alias: str) -> Dict[str, Any]:
        """Add alias to version"""
        with self.lock:
            model_version = self.get_version(model_id, version)
            if not model_version:
                return {'error': f'Version {version} not found'}
            
            if alias not in model_version.aliases:
                model_version.aliases.append(alias)
        
        logger.debug(f"Alias added: {model_id} v{version} -> {alias}")
        return {'model_id': model_id, 'version': version, 'alias': alias}
    
    def promote_version(self, model_id: str, version: int, to_stage: ReleaseStage,
                       promoted_by: Optional[str] = None, notes: Optional[str] = None) -> str:
        """
        Promote version to release stage
        
        Args:
            model_id: Model ID
            version: Version to promote
            to_stage: Target stage
            promoted_by: Promoter ID
            notes: Promotion notes
            
        Returns:
            promotion_id: Promotion record ID
        """
        with self.lock:
            model_version = self.get_version(model_id, version)
            if not model_version:
                return ''
            
            promotion_id = str(uuid.uuid4())
            from_stage = self._get_current_stage(model_id, version)
            
            promotion = ReleasePromotion(
                promotion_id=promotion_id,
                model_id=model_id,
                version=version,
                from_stage=from_stage,
                to_stage=to_stage,
                promoted_at=datetime.utcnow().timestamp(),
                promoted_by=promoted_by,
                notes=notes
            )
            
            self.releases[promotion_id] = promotion
            self.release_mappings[model_id][to_stage.value] = version
        
        logger.info(f"Version promoted: {model_id} v{version} -> {to_stage.value}")
        self._broadcast_callback('version_promoted', {
            'model_id': model_id,
            'version': version,
            'stage': to_stage.value
        })
        
        return promotion_id
    
    def _get_current_stage(self, model_id: str, version: int) -> ReleaseStage:
        """Get current release stage for version"""
        for stage, v in self.release_mappings[model_id].items():
            if v == version:
                return ReleaseStage[stage.upper()]
        return ReleaseStage.DEV
    
    def get_production_version(self, model_id: str) -> Optional[ModelVersion]:
        """Get current production version"""
        with self.lock:
            prod_version = self.release_mappings[model_id].get('production')
            if prod_version:
                return self.get_version(model_id, prod_version)
        return None
    
    def compare_versions(self, model_id: str, version1: int, version2: int) -> str:
        """
        Compare two versions
        
        Args:
            model_id: Model ID
            version1: First version
            version2: Second version
            
        Returns:
            comparison_id: Comparison record ID
        """
        with self.lock:
            v1 = self.get_version(model_id, version1)
            v2 = self.get_version(model_id, version2)
            
            if not v1 or not v2:
                return ''
            
            # Calculate metric differences
            metrics_diff = {}
            for metric in v1.metrics.custom_metrics.keys() | v2.metrics.custom_metrics.keys():
                val1 = v1.metrics.custom_metrics.get(metric, 0)
                val2 = v2.metrics.custom_metrics.get(metric, 0)
                diff = val2 - val1
                percent_change = (diff / val1 * 100) if val1 != 0 else 0
                
                metrics_diff[metric] = {
                    'v1': val1,
                    'v2': val2,
                    'diff': diff,
                    'percent_change': percent_change
                }
            
            # Determine recommendation
            improvement = sum(
                d.get('diff', 0) * (1 if d.get('percent_change', 0) > 0 else -1)
                for d in metrics_diff.values()
            )
            
            if improvement > 0:
                recommendation = 'upgrade'
            elif improvement < 0:
                recommendation = 'downgrade'
            else:
                recommendation = 'same'
            
            comparison_id = str(uuid.uuid4())
            comparison = ModelComparison(
                comparison_id=comparison_id,
                model_id=model_id,
                version1=version1,
                version2=version2,
                metrics_diff=metrics_diff,
                performance_improvement=improvement,
                recommendation=recommendation
            )
            
            self.comparisons[comparison_id] = comparison
        
        logger.info(f"Versions compared: {model_id} v{version1} vs v{version2}")
        
        return comparison_id
    
    def deprecate_version(self, model_id: str, version: int,
                         message: Optional[str] = None) -> Dict[str, Any]:
        """Deprecate a model version"""
        with self.lock:
            model_version = self.get_version(model_id, version)
            if not model_version:
                return {'error': f'Version {version} not found'}
            
            model_version.status = ModelStatus.DEPRECATED
            model_version.deprecation_message = message
            model_version.deprecated_at = datetime.utcnow().timestamp()
        
        logger.info(f"Version deprecated: {model_id} v{version}")
        
        return {
            'model_id': model_id,
            'version': version,
            'status': 'deprecated'
        }
    
    def search_models(self, workspace_id: str, query: str) -> List[ModelRegistry]:
        """Search models by name or description"""
        with self.lock:
            query_lower = query.lower()
            return [
                r for r in self.registries.values()
                if r.workspace_id == workspace_id and (
                    query_lower in r.model_name.lower() or
                    (r.description and query_lower in r.description.lower())
                )
            ]
    
    def get_model_lineage(self, model_id: str, version: int) -> Optional[ModelLineage]:
        """Get model lineage information"""
        model_version = self.get_version(model_id, version)
        return model_version.lineage if model_version else None
    
    def get_comparison(self, comparison_id: str) -> Optional[ModelComparison]:
        """Get comparison details"""
        with self.lock:
            return self.comparisons.get(comparison_id)
    
    def export_model_metadata(self, model_id: str, version: int) -> Dict[str, Any]:
        """Export model metadata as dict"""
        model_version = self.get_version(model_id, version)
        if not model_version:
            return {}
        
        return {
            'model_id': model_id,
            'version': version,
            'name': model_version.name,
            'status': model_version.status.value,
            'metrics': asdict(model_version.metrics),
            'artifact': asdict(model_version.artifact),
            'input_output': asdict(model_version.input_output),
            'tags': model_version.tags,
            'aliases': model_version.aliases
        }
    
    def register_callback(self, event_type: str, callback: callable) -> None:
        """Register callback for registry events"""
        with self.lock:
            self.callbacks[event_type].append(callback)
    
    def _broadcast_callback(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast callback"""
        with self.lock:
            callbacks = list(self.callbacks.get(event_type, []))
        
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Callback error: {str(e)}")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        with self.lock:
            total_versions = sum(len(versions) for versions in self.versions.values())
            
            return {
                'total_models': len(self.registries),
                'total_versions': total_versions,
                'total_comparisons': len(self.comparisons),
                'max_versions_per_model': self.max_versions_per_model,
                'timestamp': datetime.utcnow().isoformat()
            }
