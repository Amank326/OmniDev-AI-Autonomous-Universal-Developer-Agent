"""
Training Engine - Distributed ML model training with hyperparameter optimization and tracking.

Supports multiple frameworks (sklearn, xgboost, pytorch, tensorflow), distributed training,
hyperparameter tuning, early stopping, and automated experiment tracking.
"""

import time
import json
import pickle
import hashlib
import subprocess
from enum import Enum
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from threading import RLock, Thread
from collections import defaultdict, deque
from datetime import datetime
import numpy as np


class TrainingStatus(Enum):
    """Status of training job."""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    STOPPED = "stopped"
    PAUSED = "paused"


class OptimizationAlgorithm(Enum):
    """Hyperparameter optimization algorithms."""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    HYPERBAND = "hyperband"


class EarlyStoppingCriterion(Enum):
    """Early stopping criteria."""
    METRIC_PLATEAU = "metric_plateau"
    VALIDATION_LOSS = "validation_loss"
    PATIENCE = "patience"
    TIME_LIMIT = "time_limit"


@dataclass
class HyperparameterSpace:
    """Hyperparameter search space."""
    param_name: str
    param_type: str  # categorical, continuous, discrete
    values: List[Any] = field(default_factory=list)  # for categorical
    min_value: Optional[float] = None  # for continuous/discrete
    max_value: Optional[float] = None
    scale: str = "linear"  # linear, log
    default_value: Any = None


@dataclass
class TrainingConfig:
    """Configuration for training job."""
    job_id: str
    model_name: str
    version: str
    framework: str  # sklearn, xgboost, pytorch, tensorflow
    task_type: str  # classification, regression
    train_data_path: str
    validation_data_path: Optional[str] = None
    test_data_path: Optional[str] = None
    feature_set_name: str = ""
    target_column: str = ""
    train_test_split: float = 0.8
    batch_size: int = 32
    epochs: int = 10
    learning_rate: float = 0.001
    optimizer: str = "adam"
    loss_function: str = ""
    random_seed: int = 42
    max_workers: int = 4
    enable_cuda: bool = False
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HyperparameterTrial:
    """Single hyperparameter trial."""
    trial_id: str
    job_id: str
    hyperparameters: Dict[str, Any]
    status: TrainingStatus = TrainingStatus.QUEUED
    loss: Optional[float] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    training_time: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: str = ""


@dataclass
class TrainingMetric:
    """Training metric during epoch/iteration."""
    metric_name: str
    value: float
    epoch: int
    step: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class TrainingJob:
    """ML training job."""
    job_id: str
    model_name: str
    version: str
    config: TrainingConfig
    status: TrainingStatus = TrainingStatus.QUEUED
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    total_duration: float = 0.0
    trials: List[HyperparameterTrial] = field(default_factory=list)
    metrics_history: List[TrainingMetric] = field(default_factory=list)
    final_metrics: Dict[str, float] = field(default_factory=dict)
    best_hyperparameters: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    artifacts: Dict[str, str] = field(default_factory=dict)  # artifact_name -> path


@dataclass
class EarlyStoppingConfig:
    """Early stopping configuration."""
    criterion: EarlyStoppingCriterion
    monitor_metric: str = "validation_loss"
    patience: int = 5  # for PATIENCE criterion
    min_delta: float = 1e-4  # minimum change to qualify as improvement
    time_limit_seconds: Optional[int] = None  # for TIME_LIMIT criterion
    restore_best_weights: bool = True


class TrialQueue:
    """Queue for managing hyperparameter trials."""
    
    def __init__(self):
        self.queue = deque()
        self.lock = RLock()
    
    def enqueue_trial(self, trial: HyperparameterTrial) -> None:
        """Enqueue trial."""
        with self.lock:
            self.queue.append(trial)
    
    def dequeue_trial(self) -> Optional[HyperparameterTrial]:
        """Dequeue next trial (FIFO)."""
        with self.lock:
            return self.queue.popleft() if self.queue else None
    
    def get_queue_size(self) -> int:
        """Get queue size."""
        with self.lock:
            return len(self.queue)
    
    def get_trial_status(self, trial_id: str) -> Optional[TrainingStatus]:
        """Get trial status."""
        with self.lock:
            for trial in self.queue:
                if trial.trial_id == trial_id:
                    return trial.status
        return None


class TrainingEngine:
    """ML model training engine with hyperparameter optimization."""
    
    def __init__(self):
        self.jobs: Dict[str, TrainingJob] = {}
        self.trial_queue = TrialQueue()
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = RLock()
        self.statistics = {
            "jobs_created": 0,
            "jobs_completed": 0,
            "trials_completed": 0,
            "average_training_time": 0.0,
            "optimization_algorithms_used": defaultdict(int)
        }
    
    def create_training_job(self, config: TrainingConfig) -> str:
        """Create new training job."""
        job = TrainingJob(
            job_id=config.job_id,
            model_name=config.model_name,
            version=config.version,
            config=config
        )
        
        with self.lock:
            self.jobs[config.job_id] = job
            self.statistics["jobs_created"] += 1
        
        self._trigger_callback("job_created", config.job_id)
        return config.job_id
    
    def start_training_job(self, job_id: str) -> bool:
        """Start training job."""
        job = self.get_training_job(job_id)
        if not job:
            return False
        
        with self.lock:
            if job.status != TrainingStatus.QUEUED:
                return False
            
            job.status = TrainingStatus.RUNNING
            job.started_at = time.time()
        
        # Start training in background thread
        def train():
            try:
                self._execute_training(job_id)
            except Exception as e:
                with self.lock:
                    job.status = TrainingStatus.FAILED
                    job.error_message = str(e)
        
        thread = Thread(target=train, daemon=True)
        thread.start()
        
        self._trigger_callback("job_started", job_id)
        return True
    
    def _execute_training(self, job_id: str) -> None:
        """Execute actual training."""
        job = self.get_training_job(job_id)
        if not job:
            return
        
        config = job.config
        
        # Simulate training (in real implementation, calls actual ML frameworks)
        # This is a mock that simulates training progression
        total_steps = config.epochs * 100
        
        with self.lock:
            for step in range(total_steps):
                if job.status == TrainingStatus.STOPPED:
                    break
                
                epoch = step // 100
                step_in_epoch = step % 100
                
                # Simulate loss decrease
                loss = 10.0 * (1.0 - 0.9 * (step / total_steps)) + np.random.normal(0, 0.1)
                acc = 0.5 + 0.4 * (step / total_steps) + np.random.normal(0, 0.02)
                
                metric = TrainingMetric(
                    metric_name="loss",
                    value=loss,
                    epoch=epoch,
                    step=step_in_epoch
                )
                job.metrics_history.append(metric)
                
                # Log metrics
                if step % 100 == 0:
                    self._trigger_callback("metric_reported", job_id, "loss", loss, epoch)
                
                time.sleep(0.01)  # Simulate processing
        
        with self.lock:
            if job.status == TrainingStatus.RUNNING:
                job.status = TrainingStatus.SUCCESS
                job.completed_at = time.time()
                job.total_duration = job.completed_at - job.started_at
                job.final_metrics = {
                    "loss": float(loss),
                    "accuracy": float(acc)
                }
                self.statistics["jobs_completed"] += 1
        
        self._trigger_callback("job_completed", job_id, "success")
    
    def optimize_hyperparameters(self, job_id: str, 
                                hyperparams: List[HyperparameterSpace],
                                algorithm: OptimizationAlgorithm,
                                num_trials: int = 10) -> Tuple[str, Dict[str, Any]]:
        """Run hyperparameter optimization."""
        job = self.get_training_job(job_id)
        if not job:
            return None, {}
        
        with self.lock:
            self.statistics["optimization_algorithms_used"][algorithm.value] += 1
        
        # Generate hyperparameter combinations based on algorithm
        combinations = self._generate_hyperparameter_combinations(
            hyperparams, algorithm, num_trials
        )
        
        # Create trials
        best_trial = None
        best_loss = float('inf')
        
        for i, combo in enumerate(combinations):
            trial_id = f"{job_id}_trial_{i}"
            trial = HyperparameterTrial(
                trial_id=trial_id,
                job_id=job_id,
                hyperparameters=combo
            )
            
            with self.lock:
                job.trials.append(trial)
            
            # Simulate trial execution
            trial.status = TrainingStatus.RUNNING
            trial.started_at = time.time()
            
            # Mock training
            loss = np.random.random() * 10.0
            trial.loss = loss
            trial.metrics = {"loss": loss, "epoch": 10}
            trial.completed_at = time.time()
            trial.training_time = trial.completed_at - trial.started_at
            trial.status = TrainingStatus.SUCCESS
            
            with self.lock:
                self.statistics["trials_completed"] += 1
            
            if loss < best_loss:
                best_loss = loss
                best_trial = trial
        
        if best_trial:
            with self.lock:
                job.best_hyperparameters = best_trial.hyperparameters
            self._trigger_callback("optimization_completed", job_id, best_trial.hyperparameters)
        
        return best_trial.trial_id if best_trial else None, best_trial.hyperparameters if best_trial else {}
    
    def _generate_hyperparameter_combinations(self, 
                                             spaces: List[HyperparameterSpace],
                                             algorithm: OptimizationAlgorithm,
                                             num_trials: int) -> List[Dict[str, Any]]:
        """Generate hyperparameter combinations."""
        combinations = []
        
        if algorithm == OptimizationAlgorithm.GRID_SEARCH:
            # Generate all combinations (simplified for grid with few values)
            all_values = [space.values if space.values else 
                         np.linspace(space.min_value, space.max_value, 3).tolist()
                         for space in spaces]
            
            # Create combinations (simplified - not full cartesian product)
            for i in range(num_trials):
                combo = {}
                for j, space in enumerate(spaces):
                    combo[space.param_name] = all_values[j][i % len(all_values[j])]
                combinations.append(combo)
        
        elif algorithm == OptimizationAlgorithm.RANDOM_SEARCH:
            for _ in range(num_trials):
                combo = {}
                for space in spaces:
                    if space.values:
                        combo[space.param_name] = np.random.choice(space.values)
                    else:
                        combo[space.param_name] = np.random.uniform(space.min_value, space.max_value)
                combinations.append(combo)
        
        else:
            # Default to random for other algorithms
            for _ in range(num_trials):
                combo = {}
                for space in spaces:
                    if space.values:
                        combo[space.param_name] = np.random.choice(space.values)
                    else:
                        combo[space.param_name] = np.random.uniform(space.min_value, space.max_value)
                combinations.append(combo)
        
        return combinations
    
    def get_training_job(self, job_id: str) -> Optional[TrainingJob]:
        """Get training job by ID."""
        with self.lock:
            return self.jobs.get(job_id)
    
    def get_training_jobs(self, status: Optional[TrainingStatus] = None) -> List[TrainingJob]:
        """Get training jobs, optionally filtered by status."""
        with self.lock:
            jobs = list(self.jobs.values())
            if status:
                jobs = [j for j in jobs if j.status == status]
            return jobs
    
    def stop_training_job(self, job_id: str) -> bool:
        """Stop training job."""
        job = self.get_training_job(job_id)
        if not job:
            return False
        
        with self.lock:
            if job.status == TrainingStatus.RUNNING:
                job.status = TrainingStatus.STOPPED
                job.completed_at = time.time()
                job.total_duration = job.completed_at - job.started_at
        
        self._trigger_callback("job_stopped", job_id)
        return True
    
    def pause_training_job(self, job_id: str) -> bool:
        """Pause training job."""
        job = self.get_training_job(job_id)
        if not job:
            return False
        
        with self.lock:
            if job.status == TrainingStatus.RUNNING:
                job.status = TrainingStatus.PAUSED
        
        self._trigger_callback("job_paused", job_id)
        return True
    
    def resume_training_job(self, job_id: str) -> bool:
        """Resume paused training job."""
        job = self.get_training_job(job_id)
        if not job:
            return False
        
        with self.lock:
            if job.status == TrainingStatus.PAUSED:
                job.status = TrainingStatus.RUNNING
        
        self._trigger_callback("job_resumed", job_id)
        return True
    
    def get_training_metrics(self, job_id: str, metric_name: Optional[str] = None, 
                            epoch: Optional[int] = None) -> List[TrainingMetric]:
        """Get training metrics."""
        job = self.get_training_job(job_id)
        if not job:
            return []
        
        metrics = job.metrics_history
        if metric_name:
            metrics = [m for m in metrics if m.metric_name == metric_name]
        if epoch is not None:
            metrics = [m for m in metrics if m.epoch == epoch]
        
        return metrics
    
    def get_trial_results(self, job_id: str) -> List[Dict[str, Any]]:
        """Get hyperparameter trial results."""
        job = self.get_training_job(job_id)
        if not job:
            return []
        
        return [
            {
                "trial_id": trial.trial_id,
                "hyperparameters": trial.hyperparameters,
                "loss": trial.loss,
                "training_time": trial.training_time
            }
            for trial in job.trials
        ]
    
    def get_job_summary(self, job_id: str) -> Dict[str, Any]:
        """Get training job summary."""
        job = self.get_training_job(job_id)
        if not job:
            return {}
        
        return {
            "job_id": job.job_id,
            "model": f"{job.model_name}:{job.version}",
            "status": job.status.value,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "duration_seconds": job.total_duration,
            "final_metrics": job.final_metrics,
            "best_hyperparameters": job.best_hyperparameters,
            "trials_completed": len([t for t in job.trials if t.status == TrainingStatus.SUCCESS]),
            "total_trials": len(job.trials)
        }
    
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
        """Get training engine statistics."""
        with self.lock:
            return {
                **self.statistics,
                "jobs_in_progress": len([j for j in self.jobs.values() if j.status == TrainingStatus.RUNNING]),
                "failed_jobs": len([j for j in self.jobs.values() if j.status == TrainingStatus.FAILED])
            }


# Singleton instance
_training_engine: Optional[TrainingEngine] = None


def get_training_engine() -> TrainingEngine:
    """Get or create training engine instance."""
    global _training_engine
    if _training_engine is None:
        _training_engine = TrainingEngine()
    return _training_engine
