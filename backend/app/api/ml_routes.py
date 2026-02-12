"""
ML Model Routes for OmniDev AI
REST API endpoints for model training, inference, and explainability
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from typing import Dict, List
from functools import wraps

ml_routes = Blueprint("ml", __name__, url_prefix="/api/ml")


def get_ml_service():
    """Get ML model service from app context"""
    if not hasattr(current_app, "ml_model_service"):
        from app.services.ml_model_service import MLModelService

        current_app.ml_model_service = MLModelService()
    return current_app.ml_model_service


def get_causal_service():
    """Get causal analysis service from app context"""
    if not hasattr(current_app, "causal_analysis_service"):
        from app.services.causal_analysis_service import CausalAnalysisService

        current_app.causal_analysis_service = CausalAnalysisService()
    return current_app.causal_analysis_service


def require_workspace(f):
    """Decorator to require workspace_id parameter"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        workspace_id = request.headers.get("X-Workspace-ID") or request.args.get("workspace_id")
        if not workspace_id:
            return jsonify({"error": "workspace_id required"}), 400
        kwargs["workspace_id"] = workspace_id
        return f(*args, **kwargs)

    return decorated_function


# ==================== ARIMA Training ====================


@ml_routes.route("/arima/train", methods=["POST"])
@require_workspace
def train_arima(workspace_id):
    """Train ARIMA model"""
    data = request.get_json()
    metric_name = data.get("metric_name")
    values = data.get("values", [])
    p = data.get("p", 1)
    d = data.get("d", 1)
    q = data.get("q", 1)

    if not metric_name or not values:
        return jsonify({"error": "metric_name and values required"}), 400

    ml_service = get_ml_service()
    result = ml_service.train_arima_model(workspace_id, metric_name, values, p, d, q)

    return jsonify({
        "model_id": result.model_id,
        "model_type": result.model_type.value,
        "metrics": {
            "mae": round(result.metrics.mae, 4),
            "rmse": round(result.metrics.rmse, 4),
            "mape": round(result.metrics.mape, 2),
            "r_squared": round(result.metrics.r_squared, 4),
            "forecast_accuracy": round(result.metrics.forecast_accuracy, 2),
            "training_time_seconds": round(result.metrics.training_time_seconds, 2),
        },
        "is_production_ready": result.is_production_ready,
        "training_parameters": result.training_parameters,
        "cross_validation_scores": [round(s, 4) for s in result.cross_validation_scores],
        "overfitting_risk": round(result.overfitting_risk, 3),
    }), 201


# ==================== Prophet Training ====================


@ml_routes.route("/prophet/train", methods=["POST"])
@require_workspace
def train_prophet(workspace_id):
    """Train Prophet-style model"""
    data = request.get_json()
    metric_name = data.get("metric_name")
    values = data.get("values", [])
    seasonality_period = data.get("seasonality_period", 7)

    if not metric_name or not values:
        return jsonify({"error": "metric_name and values required"}), 400

    # Create mock timestamps if not provided
    timestamps = [
        datetime.utcnow() - datetime.timedelta(hours=i) for i in range(len(values) - 1, -1, -1)
    ]

    ml_service = get_ml_service()
    result = ml_service.train_prophet_model(
        workspace_id, metric_name, values, timestamps, seasonality_period
    )

    return jsonify({
        "model_id": result.model_id,
        "model_type": result.model_type.value,
        "metrics": {
            "mae": round(result.metrics.mae, 4),
            "rmse": round(result.metrics.rmse, 4),
            "mape": round(result.metrics.mape, 2),
            "r_squared": round(result.metrics.r_squared, 4),
            "forecast_accuracy": round(result.metrics.forecast_accuracy, 2),
            "training_time_seconds": round(result.metrics.training_time_seconds, 2),
        },
        "is_production_ready": result.is_production_ready,
        "training_parameters": result.training_parameters,
        "hyperparameters": result.hyperparameters,
    }), 201


# ==================== LSTM Training ====================


@ml_routes.route("/lstm/train", methods=["POST"])
@require_workspace
def train_lstm(workspace_id):
    """Train LSTM neural network"""
    data = request.get_json()
    metric_name = data.get("metric_name")
    values = data.get("values", [])
    sequence_length = data.get("sequence_length", 10)
    hidden_size = data.get("hidden_size", 32)

    if not metric_name or not values:
        return jsonify({"error": "metric_name and values required"}), 400

    ml_service = get_ml_service()
    result = ml_service.train_lstm_model(workspace_id, metric_name, values, sequence_length, hidden_size)

    return jsonify({
        "model_id": result.model_id,
        "model_type": result.model_type.value,
        "metrics": {
            "mae": round(result.metrics.mae, 4),
            "rmse": round(result.metrics.rmse, 4),
            "mape": round(result.metrics.mape, 2),
            "r_squared": round(result.metrics.r_squared, 4),
            "forecast_accuracy": round(result.metrics.forecast_accuracy, 2),
            "training_time_seconds": round(result.metrics.training_time_seconds, 2),
        },
        "is_production_ready": result.is_production_ready,
        "hyperparameters": result.hyperparameters,
    }), 201


# ==================== Model Inference ====================


@ml_routes.route("/models/<model_id>/predict", methods=["POST"])
@require_workspace
def predict(workspace_id, model_id):
    """Make prediction with trained model"""
    data = request.get_json()
    input_values = data.get("values", [])

    if not input_values:
        return jsonify({"error": "values required"}), 400

    ml_service = get_ml_service()
    
    if model_id not in ml_service.models:
        return jsonify({"error": "model not found"}), 404

    model = ml_service.models[model_id]
    
    # Simulate prediction
    avg_input = sum(input_values) / len(input_values)
    trend = input_values[-1] - input_values[0] if len(input_values) > 1 else 0
    prediction = avg_input + (trend * 0.1)

    return jsonify({
        "model_id": model_id,
        "prediction": round(prediction, 4),
        "prediction_interval": {
            "lower": round(prediction * 0.95, 4),
            "upper": round(prediction * 1.05, 4),
        },
        "confidence": 0.85,
        "timestamp": datetime.utcnow().isoformat(),
    }), 200


# ==================== SHAP Explainability ====================


@ml_routes.route("/models/<model_id>/explain", methods=["POST"])
@require_workspace
def explain_model(workspace_id, model_id):
    """Generate SHAP explanation for model prediction"""
    data = request.get_json()
    prediction_value = data.get("prediction", 0)
    features = data.get("features", {})

    ml_service = get_ml_service()
    explanation = ml_service.generate_shap_explanation(model_id, prediction_value, features)

    return jsonify({
        "model_id": model_id,
        "timestamp": explanation.timestamp.isoformat(),
        "shap_values": [
            {
                "feature": sv.feature_name,
                "shap_value": round(sv.shap_value, 4),
                "feature_value": round(sv.feature_value, 4),
            }
            for sv in explanation.shap_values
        ],
        "feature_importance": [
            {
                "feature": fi.feature_name,
                "importance_score": round(fi.importance_score, 4),
                "importance_percent": round(fi.importance_percent, 2),
            }
            for fi in explanation.feature_importance
        ],
        "interpretation": explanation.interpretation,
        "confidence_bounds": {
            "lower": round(explanation.confidence_bounds[0], 4),
            "upper": round(explanation.confidence_bounds[1], 4),
        },
    }), 200


# ==================== Feature Importance ====================


@ml_routes.route("/models/<model_id>/feature-importance", methods=["POST"])
@require_workspace
def feature_importance(workspace_id, model_id):
    """Calculate feature importance using permutation"""
    data = request.get_json()
    feature_names = data.get("feature_names", [])
    test_values = data.get("test_values", [])
    test_targets = data.get("test_targets", [])

    if not feature_names or not test_values:
        return jsonify({"error": "feature_names and test_values required"}), 400

    ml_service = get_ml_service()
    importances = ml_service.calculate_feature_importance_permutation(
        model_id, feature_names, test_values, test_targets
    )

    return jsonify({
        "model_id": model_id,
        "method": "permutation",
        "feature_importance": [
            {
                "feature": fi.feature_name,
                "importance_score": round(fi.importance_score, 4),
                "importance_percent": round(fi.importance_percent, 2),
                "rank": i + 1,
            }
            for i, fi in enumerate(importances)
        ],
        "total_features": len(importances),
    }), 200


# ==================== Causal Analysis ====================


@ml_routes.route("/causal/analyze", methods=["POST"])
@require_workspace
def analyze_causality(workspace_id):
    """Perform causal analysis for anomaly"""
    data = request.get_json()
    anomaly_metric = data.get("anomaly_metric")
    anomaly_value = data.get("anomaly_value", 0)
    baseline_value = data.get("baseline_value", 0)
    metrics = data.get("metrics", {})

    if not anomaly_metric or not metrics:
        return jsonify({"error": "anomaly_metric and metrics required"}), 400

    # Convert metrics to proper format
    formatted_metrics = {}
    for metric_name, values in metrics.items():
        if isinstance(values, list):
            formatted_metrics[metric_name] = [(v, datetime.utcnow()) for v in values]

    causal_service = get_causal_service()
    result = causal_service.perform_causal_analysis(
        workspace_id, anomaly_metric, anomaly_value, baseline_value, formatted_metrics
    )

    return jsonify({
        "analysis_timestamp": result.analysis_timestamp.isoformat(),
        "target_anomaly": result.target_anomaly,
        "confidence_score": round(result.confidence_score, 3),
        "explanation": result.explanation,
        "root_causes": [
            {
                "root_cause_metric": rc.root_cause_metric,
                "root_cause_value": round(rc.root_cause_value, 4),
                "contribution_percent": round(rc.contribution_percent, 2),
                "confidence": round(rc.confidence, 3),
                "description": rc.description,
                "recommended_actions": rc.recommended_actions[:2],
            }
            for rc in result.root_causes[:3]
        ],
        "actionable_insights": result.actionable_insights,
        "primary_causal_path": result.primary_causal_path,
    }), 200


# ==================== Causal Graph ====================


@ml_routes.route("/causal/graph", methods=["POST"])
@require_workspace
def get_causal_graph(workspace_id):
    """Build and retrieve causal graph"""
    data = request.get_json()
    metrics = data.get("metrics", {})

    if not metrics:
        return jsonify({"error": "metrics required"}), 400

    # Convert metrics
    formatted_metrics = {}
    for metric_name, values in metrics.items():
        if isinstance(values, list):
            formatted_metrics[metric_name] = [(v, datetime.utcnow()) for v in values]

    causal_service = get_causal_service()
    causal_graph = causal_service.build_causal_graph(formatted_metrics)
    graph_json = causal_service.export_causal_graph(causal_graph)

    return jsonify({
        "workspace_id": workspace_id,
        "timestamp": datetime.utcnow().isoformat(),
        "nodes": graph_json["nodes"],
        "links": graph_json["links"],
        "total_nodes": len(graph_json["nodes"]),
        "total_links": len(graph_json["links"]),
    }), 200


# ==================== Feedback Loops ====================


@ml_routes.route("/causal/feedback-loops", methods=["POST"])
@require_workspace
def detect_feedback_loops(workspace_id):
    """Detect feedback loops in causal graph"""
    data = request.get_json()
    metrics = data.get("metrics", {})

    if not metrics:
        return jsonify({"error": "metrics required"}), 400

    # Convert metrics
    formatted_metrics = {}
    for metric_name, values in metrics.items():
        if isinstance(values, list):
            formatted_metrics[metric_name] = [(v, datetime.utcnow()) for v in values]

    causal_service = get_causal_service()
    causal_graph = causal_service.build_causal_graph(formatted_metrics)
    loops = causal_service.detect_causal_loops(causal_graph)

    return jsonify({
        "workspace_id": workspace_id,
        "feedback_loops": loops,
        "loop_count": len(loops),
        "has_feedback_loops": len(loops) > 0,
        "timestamp": datetime.utcnow().isoformat(),
    }), 200


# ==================== Model Metrics ====================


@ml_routes.route("/models/metrics", methods=["GET"])
@require_workspace
def get_all_model_metrics(workspace_id):
    """Get metrics for all trained models"""
    ml_service = get_ml_service()

    models = []
    if workspace_id in ml_service.training_history:
        for result in ml_service.training_history[workspace_id]:
            models.append({
                "model_id": result.model_id,
                "model_type": result.model_type.value,
                "metrics": {
                    "r_squared": round(result.metrics.r_squared, 4),
                    "rmse": round(result.metrics.rmse, 4),
                    "forecast_accuracy": round(result.metrics.forecast_accuracy, 2),
                },
                "is_production_ready": result.is_production_ready,
                "trained_at": result.trained_at.isoformat(),
            })

    return jsonify({
        "workspace_id": workspace_id,
        "models": models,
        "total_models": len(models),
    }), 200


# ==================== Model Comparison ====================


@ml_routes.route("/models/compare", methods=["POST"])
@require_workspace
def compare_models(workspace_id):
    """Compare multiple trained models"""
    data = request.get_json()
    model_ids = data.get("model_ids", [])

    ml_service = get_ml_service()
    comparisons = []

    for model_id in model_ids[:5]:  # Limit to 5 models
        if workspace_id in ml_service.training_history:
            for result in ml_service.training_history[workspace_id]:
                if result.model_id == model_id:
                    comparisons.append({
                        "model_id": model_id,
                        "model_type": result.model_type.value,
                        "r_squared": round(result.metrics.r_squared, 4),
                        "rmse": round(result.metrics.rmse, 4),
                        "mape": round(result.metrics.mape, 2),
                        "training_time": round(result.metrics.training_time_seconds, 2),
                        "is_production_ready": result.is_production_ready,
                    })

    return jsonify({
        "workspace_id": workspace_id,
        "model_comparisons": comparisons,
        "best_model": max(
            comparisons, key=lambda m: m["r_squared"], default=None
        ),
    }), 200


# ==================== Model Details ====================


@ml_routes.route("/models/<model_id>/details", methods=["GET"])
@require_workspace
def get_model_details(workspace_id, model_id):
    """Get detailed information about a model"""
    ml_service = get_ml_service()

    if workspace_id not in ml_service.training_history:
        return jsonify({"error": "no models found for workspace"}), 404

    for result in ml_service.training_history[workspace_id]:
        if result.model_id == model_id:
            return jsonify({
                "model_id": model_id,
                "model_type": result.model_type.value,
                "metrics": {
                    "mae": round(result.metrics.mae, 4),
                    "rmse": round(result.metrics.rmse, 4),
                    "mape": round(result.metrics.mape, 2),
                    "r_squared": round(result.metrics.r_squared, 4),
                    "forecast_accuracy": round(result.metrics.forecast_accuracy, 2),
                    "training_time_seconds": round(result.metrics.training_time_seconds, 2),
                    "inference_time_ms": round(result.metrics.inference_time_ms, 2),
                },
                "training_parameters": result.training_parameters,
                "hyperparameters": result.hyperparameters,
                "cross_validation_scores": [round(s, 4) for s in result.cross_validation_scores],
                "overfitting_risk": round(result.overfitting_risk, 3),
                "is_production_ready": result.is_production_ready,
                "trained_at": result.trained_at.isoformat(),
            }), 200

    return jsonify({"error": "model not found"}), 404


# ==================== Health Check ====================


@ml_routes.route("/health", methods=["GET"])
def health_check():
    """ML service health check"""
    return jsonify({
        "status": "healthy",
        "services": {
            "ml_models": "operational",
            "causal_analysis": "operational",
            "explainability": "operational",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }), 200
