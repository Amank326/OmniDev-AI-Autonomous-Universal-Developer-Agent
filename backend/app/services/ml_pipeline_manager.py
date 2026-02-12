"""
ML Pipeline Manager - Orchestrate complete ML workflows from data to production.

Manages end-to-end ML pipelines: data preparation, feature engineering, training,
evaluation, and deployment with scheduling and monitoring.
"""

import time
import json
from enum import Enum
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from threading import RLock, Thread
from collections import defaultdict, deque
from datetime import datetime


class PipelineStage(Enum):
    """Stages of ML pipeline."""
    DATA_PREP = "data_prep"
    FEATURE_ENGINEERING = "feature_engineering"
    TRAINING = "training"
    EVALUATION = "evaluation"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"


class PipelineStatus(Enum):
    """Overall status of pipeline execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL_SUCCESS = "partial_success"
    CANCELLED = "cancelled"


class StageStatus(Enum):
    """Status of individual pipeline stage."""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class TriggerType(Enum):
    """How pipeline is triggered."""
    MANUAL = "manual"
    SCHEDULE = "schedule"
    DATA_ARRIVAL = "data_arrival"
    METRIC_THRESHOLD = "metric_threshold"
    WEBHOOK = "webhook"


@dataclass
class StageConfig:
    """Configuration for a pipeline stage."""
    stage_name: str
    stage_type: PipelineStage
    enabled: bool = True
    skip_on_error: bool = False
    timeout_seconds: int = 3600
    retry_attempts: int = 1
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Stage names this depends on


@dataclass
class StageExecution:
    """Execution record for a pipeline stage."""
    execution_id: str
    stage_name: str
    status: StageStatus = StageStatus.QUEUED
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_seconds: float = 0.0
    error_message: str = ""
    metrics: Dict[str, float] = field(default_factory=dict)
    output_artifacts: Dict[str, str] = field(default_factory=dict)  # artifact_name -> path


@dataclass
class PipelineConfig:
    """Configuration for ML pipeline."""
    pipeline_name: str
    version: str
    description: str = ""
    stages: List[StageConfig] = field(default_factory=list)
    schedule_cron: Optional[str] = None
    trigger_type: TriggerType = TriggerType.MANUAL
    max_parallel_stages: int = 3
    auto_deploy_on_success: bool = False
    deployment_target: str = ""  # staging, production
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatasetConfig:
    """Dataset configuration for pipeline."""
    dataset_name: str
    path: str
    format: str  # csv, parquet, json
    size_bytes: int = 0
    row_count: int = 0
    column_count: int = 0
    schema: Dict[str, str] = field(default_factory=dict)  # column_name -> type
    created_at: float = field(default_factory=time.time)
    quality_score: float = 0.0


@dataclass
class PipelineExecution:
    """Record of a pipeline execution."""
    execution_id: str
    pipeline_name: str
    pipeline_version: str
    status: PipelineStatus = PipelineStatus.PENDING
    trigger_type: TriggerType = TriggerType.MANUAL
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    total_duration: float = 0.0
    stage_executions: List[StageExecution] = field(default_factory=list)
    final_metrics: Dict[str, float] = field(default_factory=dict)
    output_model_version: Optional[str] = None
    error_message: str = ""
    triggered_by: str = ""


class MLPipelineManager:
    """Orchestrate end-to-end ML pipelines."""
    
    def __init__(self):
        self.pipelines: Dict[str, PipelineConfig] = {}
        self.executions: Dict[str, PipelineExecution] = {}
        self.datasets: Dict[str, DatasetConfig] = {}
        self.execution_history: deque = deque(maxlen=10000)
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = RLock()
        self.statistics = {
            "pipelines_created": 0,
            "executions_started": 0,
            "executions_completed": 0,
            "success_rate": 0.0,
            "average_execution_time": 0.0,
            "datasets_registered": 0
        }
    
    def create_pipeline(self, config: PipelineConfig) -> str:
        """Create new ML pipeline."""
        with self.lock:
            if config.pipeline_name in self.pipelines:
                return None
            
            self.pipelines[config.pipeline_name] = config
            self.statistics["pipelines_created"] += 1
        
        self._trigger_callback("pipeline_created", config.pipeline_name, config.version)
        return config.pipeline_name
    
    def get_pipeline(self, pipeline_name: str) -> Optional[PipelineConfig]:
        """Get pipeline configuration."""
        with self.lock:
            return self.pipelines.get(pipeline_name)
    
    def register_dataset(self, dataset_config: DatasetConfig) -> str:
        """Register dataset for pipeline."""
        with self.lock:
            self.datasets[dataset_config.dataset_name] = dataset_config
            self.statistics["datasets_registered"] += 1
        
        self._trigger_callback("dataset_registered", dataset_config.dataset_name)
        return dataset_config.dataset_name
    
    def get_dataset(self, dataset_name: str) -> Optional[DatasetConfig]:
        """Get dataset configuration."""
        with self.lock:
            return self.datasets.get(dataset_name)
    
    def execute_pipeline(self, pipeline_name: str, trigger_type: TriggerType = TriggerType.MANUAL,
                        triggered_by: str = "", parameters: Optional[Dict] = None) -> Optional[str]:
        """Execute ML pipeline."""
        pipeline = self.get_pipeline(pipeline_name)
        if not pipeline:
            return None
        
        execution_id = f"{pipeline_name}_{int(time.time() * 1000)}"
        
        execution = PipelineExecution(
            execution_id=execution_id,
            pipeline_name=pipeline_name,
            pipeline_version=pipeline.version,
            trigger_type=trigger_type,
            triggered_by=triggered_by
        )
        
        with self.lock:
            self.executions[execution_id] = execution
            self.statistics["executions_started"] += 1
        
        # Execute pipeline asynchronously
        def run_pipeline():
            self._execute_pipeline_stages(execution_id)
        
        thread = Thread(target=run_pipeline, daemon=True)
        thread.start()
        
        self._trigger_callback("pipeline_execution_started", pipeline_name, execution_id)
        return execution_id
    
    def _execute_pipeline_stages(self, execution_id: str) -> None:
        """Execute all stages in pipeline."""
        execution = self.executions.get(execution_id)
        if not execution:
            return
        
        pipeline = self.get_pipeline(execution.pipeline_name)
        if not pipeline:
            return
        
        with self.lock:
            execution.status = PipelineStatus.RUNNING
            execution.started_at = time.time()
        
        # Build dependency graph and execute stages
        completed_stages = set()
        failed_stages = set()
        
        for stage_config in pipeline.stages:
            if not stage_config.enabled:
                stage_exec = StageExecution(
                    execution_id=execution_id,
                    stage_name=stage_config.stage_name,
                    status=StageStatus.SKIPPED
                )
                with self.lock:
                    execution.stage_executions.append(stage_exec)
                continue
            
            # Check dependencies
            if stage_config.dependencies:
                unmet = [d for d in stage_config.dependencies if d not in completed_stages]
                if unmet:
                    if stage_config.skip_on_error or not any(d in failed_stages for d in unmet):
                        # Skip this stage
                        stage_exec = StageExecution(
                            execution_id=execution_id,
                            stage_name=stage_config.stage_name,
                            status=StageStatus.SKIPPED
                        )
                        with self.lock:
                            execution.stage_executions.append(stage_exec)
                        continue
            
            # Execute stage
            stage_exec = self._execute_stage(execution_id, stage_config)
            
            with self.lock:
                execution.stage_executions.append(stage_exec)
            
            if stage_exec.status == StageStatus.SUCCESS:
                completed_stages.add(stage_config.stage_name)
            elif stage_exec.status == StageStatus.FAILED:
                failed_stages.add(stage_config.stage_name)
                if not stage_config.skip_on_error:
                    break
        
        # Finalize execution
        with self.lock:
            if failed_stages:
                execution.status = PipelineStatus.FAILED if not completed_stages else PipelineStatus.PARTIAL_SUCCESS
            else:
                execution.status = PipelineStatus.SUCCESS
            
            execution.completed_at = time.time()
            execution.total_duration = execution.completed_at - execution.started_at
            
            self.execution_history.append(copy_execution(execution))
            self.statistics["executions_completed"] += 1
        
        # Auto-deploy if enabled
        if pipeline.auto_deploy_on_success and execution.status == PipelineStatus.SUCCESS:
            self._trigger_callback("auto_deploy_triggered", execution_id, pipeline.deployment_target)
        
        self._trigger_callback("pipeline_execution_completed", execution_id, execution.status.value)
    
    def _execute_stage(self, execution_id: str, stage_config: StageConfig) -> StageExecution:
        """Execute single pipeline stage."""
        stage_exec = StageExecution(
            execution_id=execution_id,
            stage_name=stage_config.stage_name,
            status=StageStatus.RUNNING
        )
        
        stage_exec.started_at = time.time()
        
        try:
            # Simulate stage execution
            if stage_config.stage_type == PipelineStage.DATA_PREP:
                metrics = self._execute_data_prep(stage_config)
            elif stage_config.stage_type == PipelineStage.FEATURE_ENGINEERING:
                metrics = self._execute_feature_eng(stage_config)
            elif stage_config.stage_type == PipelineStage.TRAINING:
                metrics = self._execute_training(stage_config)
            elif stage_config.stage_type == PipelineStage.EVALUATION:
                metrics = self._execute_evaluation(stage_config)
            elif stage_config.stage_type == PipelineStage.VALIDATION:
                metrics = self._execute_validation(stage_config)
            elif stage_config.stage_type == PipelineStage.DEPLOYMENT:
                metrics = self._execute_deployment(stage_config)
            else:
                metrics = {}
            
            stage_exec.status = StageStatus.SUCCESS
            stage_exec.metrics = metrics
            
        except Exception as e:
            stage_exec.status = StageStatus.FAILED
            stage_exec.error_message = str(e)
        
        finally:
            stage_exec.completed_at = time.time()
            stage_exec.duration_seconds = stage_exec.completed_at - stage_exec.started_at
        
        self._trigger_callback("stage_completed", stage_config.stage_name, stage_exec.status.value)
        return stage_exec
    
    def _execute_data_prep(self, stage_config: StageConfig) -> Dict[str, float]:
        """Execute data preparation stage."""
        time.sleep(0.1)  # Simulate processing
        return {
            "rows_processed": 10000,
            "rows_cleaned": 9950,
            "missing_values_handled": 50
        }
    
    def _execute_feature_eng(self, stage_config: StageConfig) -> Dict[str, float]:
        """Execute feature engineering stage."""
        time.sleep(0.1)  # Simulate processing
        return {
            "features_created": 25,
            "features_selected": 15,
            "feature_importance_computed": 1.0
        }
    
    def _execute_training(self, stage_config: StageConfig) -> Dict[str, float]:
        """Execute training stage."""
        time.sleep(0.2)  # Simulate processing
        return {
            "epochs_completed": 10,
            "final_loss": 0.25,
            "train_accuracy": 0.92
        }
    
    def _execute_evaluation(self, stage_config: StageConfig) -> Dict[str, float]:
        """Execute evaluation stage."""
        time.sleep(0.1)  # Simulate processing
        return {
            "test_accuracy": 0.88,
            "precision": 0.90,
            "recall": 0.87,
            "f1_score": 0.88
        }
    
    def _execute_validation(self, stage_config: StageConfig) -> Dict[str, float]:
        """Execute validation stage."""
        time.sleep(0.1)  # Simulate processing
        return {
            "validation_passed": 1.0,
            "checks_passed": 5,
            "checks_total": 5
        }
    
    def _execute_deployment(self, stage_config: StageConfig) -> Dict[str, float]:
        """Execute deployment stage."""
        time.sleep(0.1)  # Simulate processing
        return {
            "deployment_successful": 1.0,
            "endpoints_created": 1,
            "replicas_ready": 3
        }
    
    def get_execution(self, execution_id: str) -> Optional[PipelineExecution]:
        """Get pipeline execution by ID."""
        with self.lock:
            return self.executions.get(execution_id)
    
    def get_execution_history(self, pipeline_name: str, limit: int = 50) -> List[PipelineExecution]:
        """Get execution history for pipeline."""
        with self.lock:
            return [e for e in self.execution_history if e.pipeline_name == pipeline_name][-limit:]
    
    def get_stage_execution(self, execution_id: str, stage_name: str) -> Optional[StageExecution]:
        """Get specific stage execution."""
        execution = self.get_execution(execution_id)
        if not execution:
            return None
        
        for stage in execution.stage_executions:
            if stage.stage_name == stage_name:
                return stage
        
        return None
    
    def cancel_pipeline_execution(self, execution_id: str) -> bool:
        """Cancel running pipeline execution."""
        execution = self.get_execution(execution_id)
        if not execution:
            return False
        
        with self.lock:
            if execution.status == PipelineStatus.RUNNING:
                execution.status = PipelineStatus.CANCELLED
                execution.completed_at = time.time()
                execution.total_duration = execution.completed_at - execution.started_at
        
        self._trigger_callback("pipeline_execution_cancelled", execution_id)
        return True
    
    def get_pipeline_summary(self, pipeline_name: str) -> Dict[str, Any]:
        """Get pipeline summary with execution stats."""
        pipeline = self.get_pipeline(pipeline_name)
        if not pipeline:
            return {}
        
        history = self.get_execution_history(pipeline_name)
        successful = len([e for e in history if e.status == PipelineStatus.SUCCESS])
        
        return {
            "pipeline_name": pipeline.pipeline_name,
            "version": pipeline.version,
            "stage_count": len(pipeline.stages),
            "total_executions": len(history),
            "successful_executions": successful,
            "success_rate": successful / len(history) if history else 0.0,
            "auto_deploy_enabled": pipeline.auto_deploy_on_success,
            "last_execution_id": history[-1].execution_id if history else None
        }
    
    def get_all_pipelines(self) -> List[str]:
        """Get all pipeline names."""
        with self.lock:
            return list(self.pipelines.keys())
    
    def delete_pipeline(self, pipeline_name: str) -> bool:
        """Delete pipeline."""
        with self.lock:
            if pipeline_name in self.pipelines:
                del self.pipelines[pipeline_name]
                self._trigger_callback("pipeline_deleted", pipeline_name)
                return True
        return False
    
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
        """Get pipeline manager statistics."""
        with self.lock:
            return {
                **self.statistics,
                "pipelines": len(self.pipelines),
                "datasets": len(self.datasets),
                "total_executions": len(self.execution_history),
                "running_executions": len([e for e in self.executions.values() if e.status == PipelineStatus.RUNNING])
            }


def copy_execution(execution: PipelineExecution) -> PipelineExecution:
    """Deep copy execution for history."""
    return PipelineExecution(
        execution_id=execution.execution_id,
        pipeline_name=execution.pipeline_name,
        pipeline_version=execution.pipeline_version,
        status=execution.status,
        trigger_type=execution.trigger_type,
        created_at=execution.created_at,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        total_duration=execution.total_duration,
        stage_executions=execution.stage_executions,
        final_metrics=execution.final_metrics,
        output_model_version=execution.output_model_version,
        error_message=execution.error_message,
        triggered_by=execution.triggered_by
    )


# Singleton instance
_ml_pipeline_manager: Optional[MLPipelineManager] = None


def get_ml_pipeline_manager() -> MLPipelineManager:
    """Get or create ML pipeline manager instance."""
    global _ml_pipeline_manager
    if _ml_pipeline_manager is None:
        _ml_pipeline_manager = MLPipelineManager()
    return _ml_pipeline_manager
