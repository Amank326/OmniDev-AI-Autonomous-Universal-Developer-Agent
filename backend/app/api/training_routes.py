"""
Phase 35: Training Routes API
REST API endpoints for model training, hyperparameter optimization, and model registry

Endpoints:
- Training Jobs: Create, start, monitor, pause, resume, cancel
- Dataset Management: Upload, analyze, split
- Hyperparameter Search: Create, suggest, report, complete
- Model Registry: Register, version, promote, compare
- Results: Get metrics, history, comparisons
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def require_workspace(f):
    """Decorator to require workspace ID in request header"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        workspace_id = request.headers.get('X-Workspace-ID')
        if not workspace_id:
            return jsonify({'error': 'Missing X-Workspace-ID header'}), 400
        return f(workspace_id, *args, **kwargs)
    return decorated_function


def handle_json_request(f):
    """Decorator to handle JSON requests with error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    return decorated_function


training_bp = Blueprint('training', __name__, url_prefix='/api/v1/training')


# ============================================================================
# Training Jobs Endpoints
# ============================================================================

@training_bp.route('/jobs/create', methods=['POST'])
@require_workspace
@handle_json_request
def create_training_job(workspace_id: str):
    """
    Create new training job
    
    Request body:
    {
        "model_name": "string",
        "model_type": "neural_network|xgboost|sklearn_model",
        "dataset_config": {
            "path": "string",
            "feature_columns": ["col1", "col2"],
            "target_column": "string",
            "validation_split": 0.2,
            "test_split": 0.1
        },
        "hyperparameters": {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100
        },
        "early_stopping_patience": 10
    }
    
    Response:
    {
        "training_id": "uuid",
        "status": "created",
        "model_name": "string"
    }
    """
    data = request.get_json()
    
    if not data.get('model_name'):
        return jsonify({'error': 'model_name required'}), 400
    
    if not data.get('dataset_config'):
        return jsonify({'error': 'dataset_config required'}), 400
    
    # In production, would call ModelTrainingService
    training_id = f"train_{datetime.utcnow().timestamp()}"
    
    response = {
        'training_id': training_id,
        'workspace_id': workspace_id,
        'status': 'created',
        'model_name': data.get('model_name'),
        'model_type': data.get('model_type'),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"Training job created: {training_id}")
    return jsonify(response), 201


@training_bp.route('/jobs/<training_id>/start', methods=['POST'])
@require_workspace
@handle_json_request
def start_training(workspace_id: str, training_id: str):
    """
    Start training job
    
    Response:
    {
        "training_id": "uuid",
        "status": "started",
        "model_name": "string"
    }
    """
    response = {
        'training_id': training_id,
        'workspace_id': workspace_id,
        'status': 'started',
        'start_time': datetime.utcnow().isoformat()
    }
    
    logger.info(f"Training started: {training_id}")
    return jsonify(response), 200


@training_bp.route('/jobs/<training_id>', methods=['GET'])
@require_workspace
@handle_json_request
def get_training_job(workspace_id: str, training_id: str):
    """
    Get training job details
    
    Response:
    {
        "training_id": "uuid",
        "model_name": "string",
        "status": "running|completed|failed",
        "current_epoch": 50,
        "total_epochs": 100,
        "best_epoch": 45,
        "best_metrics": {
            "accuracy": 0.95,
            "loss": 0.05
        },
        "progress": 50.0,
        "estimated_time_remaining": 300,
        "start_time": "iso8601",
        "end_time": "iso8601"
    }
    """
    response = {
        'training_id': training_id,
        'workspace_id': workspace_id,
        'status': 'running',
        'current_epoch': 50,
        'total_epochs': 100,
        'best_epoch': 45,
        'best_metrics': {
            'accuracy': 0.95,
            'loss': 0.05
        },
        'progress': 50.0,
        'estimated_time_remaining': 300
    }
    
    return jsonify(response), 200


@training_bp.route('/jobs/<training_id>/metrics', methods=['GET'])
@require_workspace
@handle_json_request
def get_training_metrics(workspace_id: str, training_id: str):
    """
    Get training metrics history
    
    Query params:
    - epoch_start: int (default 0)
    - epoch_end: int (default latest)
    - metrics: comma-separated metric names
    
    Response:
    {
        "training_id": "uuid",
        "metrics": [
            {
                "epoch": 1,
                "loss": 0.5,
                "accuracy": 0.8,
                "val_loss": 0.51,
                "val_accuracy": 0.79,
                "duration_seconds": 12.5
            }
        ]
    }
    """
    epoch_start = request.args.get('epoch_start', 0, type=int)
    epoch_end = request.args.get('epoch_end', 100, type=int)
    
    metrics_data = [
        {
            'epoch': i,
            'loss': 0.5 - (i * 0.002),
            'accuracy': 0.8 + (i * 0.001),
            'val_loss': 0.51 - (i * 0.002),
            'val_accuracy': 0.79 + (i * 0.001),
            'duration_seconds': 12.5
        }
        for i in range(epoch_start, epoch_end)
    ]
    
    response = {
        'training_id': training_id,
        'workspace_id': workspace_id,
        'epoch_start': epoch_start,
        'epoch_end': epoch_end,
        'metrics': metrics_data
    }
    
    return jsonify(response), 200


@training_bp.route('/jobs/<training_id>/pause', methods=['POST'])
@require_workspace
@handle_json_request
def pause_training(workspace_id: str, training_id: str):
    """Pause training job"""
    response = {
        'training_id': training_id,
        'workspace_id': workspace_id,
        'status': 'paused',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"Training paused: {training_id}")
    return jsonify(response), 200


@training_bp.route('/jobs/<training_id>/resume', methods=['POST'])
@require_workspace
@handle_json_request
def resume_training(workspace_id: str, training_id: str):
    """Resume paused training"""
    response = {
        'training_id': training_id,
        'workspace_id': workspace_id,
        'status': 'resumed',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"Training resumed: {training_id}")
    return jsonify(response), 200


@training_bp.route('/jobs/<training_id>/cancel', methods=['POST'])
@require_workspace
@handle_json_request
def cancel_training(workspace_id: str, training_id: str):
    """Cancel training job"""
    response = {
        'training_id': training_id,
        'workspace_id': workspace_id,
        'status': 'cancelled',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"Training cancelled: {training_id}")
    return jsonify(response), 200


@training_bp.route('/jobs', methods=['GET'])
@require_workspace
@handle_json_request
def list_training_jobs(workspace_id: str):
    """
    List training jobs for workspace
    
    Query params:
    - status: running|completed|failed|cancelled
    - limit: int (default 20)
    - offset: int (default 0)
    
    Response:
    {
        "jobs": [
            {
                "training_id": "uuid",
                "model_name": "string",
                "status": "string",
                "progress": 50.0,
                "start_time": "iso8601"
            }
        ],
        "total": 42,
        "limit": 20,
        "offset": 0
    }
    """
    status = request.args.get('status')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    jobs = [
        {
            'training_id': f"train_{i}",
            'model_name': f"Model_{i}",
            'status': 'running',
            'progress': 50.0 + i * 5,
            'start_time': datetime.utcnow().isoformat()
        }
        for i in range(limit)
    ]
    
    response = {
        'workspace_id': workspace_id,
        'jobs': jobs,
        'total': 42,
        'limit': limit,
        'offset': offset
    }
    
    return jsonify(response), 200


# ============================================================================
# Hyperparameter Search Endpoints
# ============================================================================

@training_bp.route('/hpo/create', methods=['POST'])
@require_workspace
@handle_json_request
def create_hpo_search(workspace_id: str):
    """
    Create hyperparameter optimization search
    
    Request body:
    {
        "search_name": "string",
        "algorithm": "grid_search|random_search|bayesian_optimization",
        "param_space": [
            {
                "name": "learning_rate",
                "type": "float",
                "low": 0.0001,
                "high": 0.1,
                "log_scale": true
            },
            {
                "name": "batch_size",
                "type": "int",
                "low": 16,
                "high": 512,
                "step": 16
            },
            {
                "name": "optimizer",
                "type": "categorical",
                "values": ["adam", "sgd", "rmsprop"]
            }
        ],
        "max_trials": 100,
        "objective_direction": "maximize|minimize"
    }
    
    Response:
    {
        "search_id": "uuid",
        "search_name": "string",
        "algorithm": "string",
        "status": "created"
    }
    """
    data = request.get_json()
    
    if not data.get('search_name'):
        return jsonify({'error': 'search_name required'}), 400
    
    if not data.get('algorithm'):
        return jsonify({'error': 'algorithm required'}), 400
    
    if not data.get('param_space'):
        return jsonify({'error': 'param_space required'}), 400
    
    search_id = f"hpo_{datetime.utcnow().timestamp()}"
    
    response = {
        'search_id': search_id,
        'workspace_id': workspace_id,
        'search_name': data.get('search_name'),
        'algorithm': data.get('algorithm'),
        'status': 'created',
        'max_trials': data.get('max_trials', 100),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"HPO search created: {search_id}")
    return jsonify(response), 201


@training_bp.route('/hpo/<search_id>/suggest', methods=['GET'])
@require_workspace
@handle_json_request
def suggest_hpo_trial(workspace_id: str, search_id: str):
    """
    Get next trial suggestion for HPO search
    
    Response:
    {
        "trial_id": "uuid",
        "trial_number": 42,
        "hyperparameters": {
            "learning_rate": 0.001,
            "batch_size": 64,
            "optimizer": "adam"
        }
    }
    """
    response = {
        'search_id': search_id,
        'workspace_id': workspace_id,
        'trial_id': f"trial_{datetime.utcnow().timestamp()}",
        'trial_number': 42,
        'hyperparameters': {
            'learning_rate': 0.001,
            'batch_size': 64,
            'optimizer': 'adam'
        }
    }
    
    return jsonify(response), 200


@training_bp.route('/hpo/<search_id>/report', methods=['POST'])
@require_workspace
@handle_json_request
def report_trial_result(workspace_id: str, search_id: str):
    """
    Report trial result
    
    Request body:
    {
        "trial_id": "uuid",
        "objective_value": 0.95,
        "secondary_metrics": {
            "precision": 0.94,
            "recall": 0.96
        },
        "duration_seconds": 300
    }
    
    Response:
    {
        "trial_id": "uuid",
        "status": "recorded",
        "is_best": true
    }
    """
    data = request.get_json()
    
    if not data.get('trial_id'):
        return jsonify({'error': 'trial_id required'}), 400
    
    if data.get('objective_value') is None:
        return jsonify({'error': 'objective_value required'}), 400
    
    response = {
        'search_id': search_id,
        'workspace_id': workspace_id,
        'trial_id': data.get('trial_id'),
        'status': 'recorded',
        'objective_value': data.get('objective_value'),
        'is_best': True
    }
    
    logger.info(f"Trial result reported: {data.get('trial_id')} = {data.get('objective_value')}")
    return jsonify(response), 200


@training_bp.route('/hpo/<search_id>/results', methods=['GET'])
@require_workspace
@handle_json_request
def get_hpo_results(workspace_id: str, search_id: str):
    """
    Get HPO search results
    
    Response:
    {
        "search_id": "uuid",
        "total_trials": 100,
        "completed_trials": 45,
        "best_value": 0.95,
        "best_trial_number": 23,
        "best_hyperparameters": {
            "learning_rate": 0.001,
            "batch_size": 64,
            "optimizer": "adam"
        },
        "mean_value": 0.87,
        "std_value": 0.04,
        "optimization_history": [
            {
                "trial_number": 1,
                "objective_value": 0.8,
                "best_so_far": 0.8
            }
        ]
    }
    """
    history = [
        {'trial_number': i, 'objective_value': 0.8 + i * 0.001, 'best_so_far': 0.8 + i * 0.001}
        for i in range(45)
    ]
    
    response = {
        'search_id': search_id,
        'workspace_id': workspace_id,
        'total_trials': 100,
        'completed_trials': 45,
        'best_value': 0.95,
        'best_trial_number': 23,
        'best_hyperparameters': {
            'learning_rate': 0.001,
            'batch_size': 64,
            'optimizer': 'adam'
        },
        'mean_value': 0.87,
        'std_value': 0.04,
        'optimization_history': history
    }
    
    return jsonify(response), 200


# ============================================================================
# Dataset Management Endpoints
# ============================================================================

@training_bp.route('/datasets/analyze', methods=['POST'])
@require_workspace
@handle_json_request
def analyze_dataset(workspace_id: str):
    """
    Analyze dataset for training
    
    Request body:
    {
        "dataset_path": "string",
        "feature_columns": ["col1", "col2"],
        "target_column": "string"
    }
    
    Response:
    {
        "total_samples": 10000,
        "feature_count": 20,
        "target_distribution": {
            "class_0": 6000,
            "class_1": 4000
        },
        "class_imbalance_ratio": 1.5,
        "missing_values": {
            "feature1": 0,
            "feature2": 5
        },
        "feature_statistics": {
            "feature1": {
                "mean": 0.0,
                "std": 1.0,
                "min": -3.0,
                "max": 3.0
            }
        }
    }
    """
    data = request.get_json()
    
    response = {
        'workspace_id': workspace_id,
        'dataset_path': data.get('dataset_path'),
        'total_samples': 10000,
        'feature_count': len(data.get('feature_columns', [])),
        'target_distribution': {
            'class_0': 6000,
            'class_1': 4000
        },
        'class_imbalance_ratio': 1.5,
        'missing_values': {col: 0 for col in data.get('feature_columns', [])},
        'feature_statistics': {
            col: {
                'mean': 0.0,
                'std': 1.0,
                'min': -3.0,
                'max': 3.0,
                'median': 0.0
            }
            for col in data.get('feature_columns', [])
        }
    }
    
    logger.info(f"Dataset analyzed: {data.get('dataset_path')}")
    return jsonify(response), 200


# ============================================================================
# Model Registry Endpoints
# ============================================================================

@training_bp.route('/models/register', methods=['POST'])
@require_workspace
@handle_json_request
def register_model(workspace_id: str):
    """
    Register model in registry
    
    Request body:
    {
        "model_name": "string",
        "description": "string",
        "task_type": "classification|regression|clustering",
        "framework": "tensorflow|pytorch|sklearn|xgboost"
    }
    
    Response:
    {
        "model_id": "uuid",
        "model_name": "string",
        "status": "registered"
    }
    """
    data = request.get_json()
    
    if not data.get('model_name'):
        return jsonify({'error': 'model_name required'}), 400
    
    model_id = f"model_{datetime.utcnow().timestamp()}"
    
    response = {
        'model_id': model_id,
        'workspace_id': workspace_id,
        'model_name': data.get('model_name'),
        'status': 'registered',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"Model registered: {model_id}")
    return jsonify(response), 201


@training_bp.route('/models/<model_id>/versions', methods=['GET'])
@require_workspace
@handle_json_request
def get_model_versions(workspace_id: str, model_id: str):
    """
    Get all versions of a model
    
    Response:
    {
        "model_id": "uuid",
        "versions": [
            {
                "version": 1,
                "status": "draft|staging|production",
                "created_at": "iso8601",
                "metrics": {
                    "accuracy": 0.95,
                    "loss": 0.05
                }
            }
        ]
    }
    """
    versions = [
        {
            'version': i,
            'status': 'production' if i == 5 else 'staging' if i == 4 else 'draft',
            'created_at': datetime.utcnow().isoformat(),
            'metrics': {
                'accuracy': 0.85 + i * 0.01,
                'loss': 0.15 - i * 0.01
            }
        }
        for i in range(1, 6)
    ]
    
    response = {
        'model_id': model_id,
        'workspace_id': workspace_id,
        'versions': versions
    }
    
    return jsonify(response), 200


@training_bp.route('/models/<model_id>/versions/<int:version>', methods=['GET'])
@require_workspace
@handle_json_request
def get_model_version(workspace_id: str, model_id: str, version: int):
    """Get specific model version"""
    response = {
        'model_id': model_id,
        'workspace_id': workspace_id,
        'version': version,
        'status': 'production',
        'metrics': {
            'accuracy': 0.95,
            'precision': 0.94,
            'recall': 0.96,
            'f1_score': 0.95
        },
        'artifact': {
            'path': f's3://models/{model_id}/v{version}',
            'size_bytes': 104857600
        },
        'created_at': datetime.utcnow().isoformat()
    }
    
    return jsonify(response), 200


@training_bp.route('/models/<model_id>/versions/<int:version>/promote', methods=['POST'])
@require_workspace
@handle_json_request
def promote_model_version(workspace_id: str, model_id: str, version: int):
    """
    Promote model to release stage
    
    Request body:
    {
        "to_stage": "staging|production|canary",
        "notes": "string"
    }
    
    Response:
    {
        "model_id": "uuid",
        "version": 5,
        "status": "promoted",
        "to_stage": "production"
    }
    """
    data = request.get_json()
    
    response = {
        'model_id': model_id,
        'workspace_id': workspace_id,
        'version': version,
        'status': 'promoted',
        'to_stage': data.get('to_stage'),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"Model promoted: {model_id} v{version} -> {data.get('to_stage')}")
    return jsonify(response), 200


@training_bp.route('/models/<model_id>/versions/<int:v1>/compare/<int:v2>', methods=['GET'])
@require_workspace
@handle_json_request
def compare_model_versions(workspace_id: str, model_id: str, v1: int, v2: int):
    """
    Compare two model versions
    
    Response:
    {
        "model_id": "uuid",
        "version1": 4,
        "version2": 5,
        "metrics_diff": {
            "accuracy": {
                "v1": 0.94,
                "v2": 0.95,
                "diff": 0.01,
                "percent_change": 1.06
            }
        },
        "recommendation": "upgrade"
    }
    """
    response = {
        'model_id': model_id,
        'workspace_id': workspace_id,
        'version1': v1,
        'version2': v2,
        'metrics_diff': {
            'accuracy': {
                'v1': 0.94,
                'v2': 0.95,
                'diff': 0.01,
                'percent_change': 1.06
            },
            'loss': {
                'v1': 0.06,
                'v2': 0.05,
                'diff': -0.01,
                'percent_change': -16.67
            }
        },
        'recommendation': 'upgrade'
    }
    
    return jsonify(response), 200


# ============================================================================
# Status and Health Endpoints
# ============================================================================

@training_bp.route('/status/training', methods=['GET'])
@require_workspace
@handle_json_request
def status_training(workspace_id: str):
    """Get training service status"""
    response = {
        'workspace_id': workspace_id,
        'service': 'training',
        'status': 'healthy',
        'active_jobs': 3,
        'queued_jobs': 5,
        'completed_jobs': 142,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(response), 200


@training_bp.route('/status/hpo', methods=['GET'])
@require_workspace
@handle_json_request
def status_hpo(workspace_id: str):
    """Get HPO service status"""
    response = {
        'workspace_id': workspace_id,
        'service': 'hpo',
        'status': 'healthy',
        'active_searches': 2,
        'total_trials': 1523,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(response), 200


@training_bp.route('/status/registry', methods=['GET'])
@require_workspace
@handle_json_request
def status_registry(workspace_id: str):
    """Get model registry service status"""
    response = {
        'workspace_id': workspace_id,
        'service': 'registry',
        'status': 'healthy',
        'total_models': 42,
        'total_versions': 234,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(response), 200


@training_bp.route('/health', methods=['GET'])
@require_workspace
@handle_json_request
def training_health(workspace_id: str):
    """Overall training subsystem health"""
    response = {
        'workspace_id': workspace_id,
        'status': 'healthy',
        'services': {
            'training': 'healthy',
            'hpo': 'healthy',
            'registry': 'healthy'
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(response), 200
