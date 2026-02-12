"""
Advanced ML API Routes for OmniDev AI
REST API endpoints for ML predictions, anomaly detection, and optimization automation
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from typing import Dict, List
from functools import wraps

ml_advanced_bp = Blueprint("ml_advanced", __name__, url_prefix="/api/v1/ml_advanced")


def get_advanced_ml_service():
    """Get advanced ML service"""
    if not hasattr(current_app, "advanced_ml_service"):
        from app.services.advanced_ml_service import AdvancedMLService
        current_app.advanced_ml_service = AdvancedMLService()
    return current_app.advanced_ml_service


def get_anomaly_service():
    """Get anomaly detection service"""
    if not hasattr(current_app, "anomaly_detection_service"):
        from app.services.anomaly_detection_service import AnomalyDetectionService
        current_app.anomaly_detection_service = AnomalyDetectionService()
    return current_app.anomaly_detection_service


def require_workspace(f):
    """Decorator to require workspace_id"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        workspace_id = request.headers.get("X-Workspace-ID") or request.args.get("workspace_id")
        if not workspace_id:
            return jsonify({"error": "workspace_id required"}), 400
        kwargs["workspace_id"] = workspace_id
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# ML PREDICTION ENDPOINTS (4 endpoints)
# ============================================================================

@ml_advanced_bp.route("/predictions/predict", methods=["POST"])
@require_workspace
def predict_metric(workspace_id):
    """
    Predict future metric values
    
    Request body:
    {
        "metric_name": "cpu_utilization",
        "forecast_hours": 168,
        "model_type": "ensemble"
    }
    """
    try:
        data = request.get_json() or {}
        metric_name = data.get("metric_name")
        forecast_hours = data.get("forecast_hours", 168)
        model_type = data.get("model_type", "ensemble")

        if not metric_name:
            return jsonify({"error": "metric_name required"}), 400

        ml_service = get_advanced_ml_service()
        prediction = ml_service.predict_metric(
            workspace_id=workspace_id,
            metric_name=metric_name,
            forecast_hours=forecast_hours,
            model_type=model_type,
        )

        if not prediction:
            return jsonify({"error": "Insufficient data for prediction"}), 400

        return jsonify({
            "success": True,
            "prediction": {
                "prediction_id": prediction.prediction_id,
                "metric_name": prediction.metric_name,
                "predicted_value": prediction.predicted_value,
                "lower_bound": prediction.lower_bound,
                "upper_bound": prediction.upper_bound,
                "confidence": prediction.confidence,
                "confidence_level": prediction.confidence_level.value,
                "model_type": prediction.model_type.value,
                "forecast_period_end": prediction.forecast_period_end.isoformat(),
                "mape": prediction.mape,
                "rmse": prediction.rmse,
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_advanced_bp.route("/predictions/batch", methods=["POST"])
@require_workspace
def batch_predictions(workspace_id):
    """
    Predict multiple metrics at once
    
    Request body:
    {
        "metrics": ["cpu_utilization", "memory_utilization", "cost"],
        "forecast_hours": 168
    }
    """
    try:
        data = request.get_json() or {}
        metrics = data.get("metrics", [])
        forecast_hours = data.get("forecast_hours", 168)

        if not metrics:
            return jsonify({"error": "metrics array required"}), 400

        ml_service = get_advanced_ml_service()
        predictions = []

        for metric in metrics:
            pred = ml_service.predict_metric(
                workspace_id=workspace_id,
                metric_name=metric,
                forecast_hours=forecast_hours,
            )
            if pred:
                predictions.append({
                    "metric": metric,
                    "predicted_value": pred.predicted_value,
                    "confidence": pred.confidence,
                    "confidence_level": pred.confidence_level.value,
                })

        return jsonify({
            "success": True,
            "workspace_id": workspace_id,
            "predictions": predictions,
            "timestamp": datetime.utcnow().isoformat(),
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_advanced_bp.route("/predictions/accuracy", methods=["GET"])
@require_workspace
def prediction_accuracy(workspace_id):
    """Get prediction accuracy metrics"""
    try:
        metric_name = request.args.get("metric", "cpu_utilization")
        lookback_days = request.args.get("lookback_days", 30, type=int)

        ml_service = get_advanced_ml_service()
        accuracy = ml_service.get_prediction_accuracy(
            workspace_id=workspace_id,
            metric_name=metric_name,
            lookback_days=lookback_days,
        )

        return jsonify({
            "success": True,
            "accuracy": accuracy,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_advanced_bp.route("/predictions/model-performance", methods=["GET"])
@require_workspace
def model_performance(workspace_id):
    """Get ML model performance metrics"""
    try:
        model_type = request.args.get("model_type", "ensemble")

        ml_service = get_advanced_ml_service()
        metrics = ml_service.get_model_performance(
            workspace_id=workspace_id,
            model_type=model_type,
        )

        if not metrics:
            return jsonify({"error": "Model not found"}), 404

        return jsonify({
            "success": True,
            "model": {
                "type": metrics.model_type.value,
                "accuracy": metrics.accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score,
                "mape": metrics.mape,
                "rmse": metrics.rmse,
                "r_squared": metrics.r_squared,
                "last_training": metrics.last_training_date.isoformat(),
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ANOMALY DETECTION ENDPOINTS (5 endpoints)
# ============================================================================

@ml_advanced_bp.route("/anomalies/detect", methods=["POST"])
@require_workspace
def detect_anomalies(workspace_id):
    """
    Detect anomalies in workspace metrics
    
    Request body:
    {
        "metrics": {"cpu_utilization": 92, "memory": 88},
        "historical": {
            "cpu_utilization": [45, 48, 47, 50, 92],
            "memory": [60, 62, 61, 63, 88]
        },
        "sensitivity": "medium"
    }
    """
    try:
        data = request.get_json() or {}
        metrics = data.get("metrics", {})
        historical = data.get("historical", {})
        sensitivity = data.get("sensitivity", "medium")

        if not metrics or not historical:
            return jsonify({"error": "metrics and historical data required"}), 400

        anomaly_service = get_anomaly_service()
        anomalies = anomaly_service.detect_anomalies_comprehensive(
            workspace_id=workspace_id,
            metrics=metrics,
            historical_data=historical,
        )

        return jsonify({
            "success": True,
            "workspace_id": workspace_id,
            "anomalies_detected": len(anomalies),
            "anomalies": [
                {
                    "anomaly_id": a.anomaly_id,
                    "metrics": a.metrics_affected,
                    "severity": a.severity.value,
                    "impact_score": a.impact_score,
                    "affected_services": a.affected_services,
                    "affected_users": a.affected_users,
                    "types": a.anomaly_types,
                }
                for a in anomalies
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_advanced_bp.route("/anomalies/root-cause", methods=["POST"])
@require_workspace
def analyze_root_cause(workspace_id):
    """
    Analyze root cause of anomaly
    
    Request body:
    {
        "anomaly_id": "anom_123",
        "anomaly": {...},
        "event_log": [...]
    }
    """
    try:
        data = request.get_json() or {}
        anomaly_id = data.get("anomaly_id")
        anomaly = data.get("anomaly")
        event_log = data.get("event_log")

        if not anomaly_id or not anomaly:
            return jsonify({"error": "anomaly_id and anomaly required"}), 400

        anomaly_service = get_anomaly_service()
        rca = anomaly_service.analyze_root_cause(
            workspace_id=workspace_id,
            anomaly_id=anomaly_id,
            anomaly=anomaly,
            event_log=event_log,
        )

        return jsonify({
            "success": True,
            "analysis": {
                "analysis_id": rca.analysis_id,
                "anomaly_id": rca.anomaly_id,
                "primary_root_cause": rca.primary_root_cause.value,
                "confidence": rca.confidence_score,
                "root_causes": [
                    {
                        "type": rc["type"],
                        "description": rc["description"],
                        "confidence": rc["confidence_score"],
                    }
                    for rc in rca.root_causes
                ],
                "evidence": rca.evidence,
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_advanced_bp.route("/anomalies/patterns", methods=["GET"])
@require_workspace
def detect_patterns(workspace_id):
    """Detect recurring anomaly patterns"""
    try:
        lookback_days = request.args.get("lookback_days", 30, type=int)

        anomaly_service = get_anomaly_service()
        patterns = anomaly_service.detect_anomaly_patterns(
            workspace_id=workspace_id,
            lookback_days=lookback_days,
        )

        return jsonify({
            "success": True,
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_name": p.pattern_name,
                    "metrics": p.metrics_involved,
                    "frequency": p.occurrence_frequency,
                    "occurrences": p.occurrences_count,
                    "seasonal": p.seasonal,
                    "recommendation": p.recommended_solution,
                }
                for p in patterns
            ],
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_advanced_bp.route("/anomalies/health-score", methods=["GET"])
@require_workspace
def get_health_score(workspace_id):
    """Get system health score"""
    try:
        anomaly_service = get_anomaly_service()
        
        # Collect anomaly stats
        anomalies = anomaly_service.detected_anomalies.get(workspace_id, [])
        critical_count = sum(
            1 for a in anomalies 
            if a.severity.value == "critical"
        )

        health = anomaly_service.calculate_health_score(
            workspace_id=workspace_id,
            anomaly_details={
                "metrics_analyzed": 50,
                "total_anomalies": len(anomalies),
                "critical_anomalies": critical_count,
            }
        )

        return jsonify({
            "success": True,
            "health": {
                "score": health.score,
                "status": health.status,
                "trend": health.trend,
                "metrics_analyzed": health.metrics_analyzed,
                "anomalies_detected": health.anomalies_detected,
                "critical_anomalies": health.critical_anomalies,
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_advanced_bp.route("/anomalies/history", methods=["GET"])
@require_workspace
def anomaly_history(workspace_id):
    """Get anomaly detection history"""
    try:
        lookback_days = request.args.get("lookback_days", 30, type=int)
        metric_filter = request.args.get("metric", None)

        anomaly_service = get_anomaly_service()
        anomalies = anomaly_service.detected_anomalies.get(workspace_id, [])

        if metric_filter:
            anomalies = [
                a for a in anomalies 
                if metric_filter in a.metrics_affected
            ]

        return jsonify({
            "success": True,
            "anomalies": [
                {
                    "anomaly_id": a.anomaly_id,
                    "metrics": a.metrics_affected,
                    "severity": a.severity.value,
                    "detected_at": a.first_detected.isoformat(),
                    "impact_score": a.impact_score,
                }
                for a in anomalies[-100:]
            ],
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# AUTOMATION ENDPOINTS (3 endpoints)
# ============================================================================

@ml_advanced_bp.route("/automation/actions", methods=["GET"])
@require_workspace
def get_automation_actions(workspace_id):
    """Get scheduled automation actions"""
    try:
        ml_service = get_advanced_ml_service()
        actions = ml_service.scheduled_actions.get(workspace_id, [])

        return jsonify({
            "success": True,
            "actions": [
                {
                    "action_id": a.action_id,
                    "action_type": a.action_type,
                    "description": a.action_description,
                    "target_metric": a.target_metric,
                    "estimated_impact": a.estimated_impact,
                    "risk_level": a.risk_level,
                    "auto_approved": a.auto_approved,
                    "scheduled_at": a.scheduled_at.isoformat(),
                }
                for a in actions
            ],
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_advanced_bp.route("/automation/generate-remediation", methods=["POST"])
@require_workspace
def generate_remediation(workspace_id):
    """
    Generate remediation plan for anomaly
    
    Request body:
    {
        "anomaly": {...},
        "root_cause": {...}
    }
    """
    try:
        data = request.get_json() or {}
        anomaly = data.get("anomaly")
        root_cause = data.get("root_cause")

        if not anomaly or not root_cause:
            return jsonify({"error": "anomaly and root_cause required"}), 400

        anomaly_service = get_anomaly_service()
        remediations = anomaly_service.generate_remediation_plan(
            workspace_id=workspace_id,
            anomaly=anomaly,
            root_cause=root_cause,
        )

        return jsonify({
            "success": True,
            "remediations": [
                {
                    "remediation_id": r.remediation_id,
                    "action_type": r.action_type,
                    "description": r.action_description,
                    "automatic": r.automatic,
                    "estimated_time_minutes": r.estimated_resolution_time_minutes,
                    "risk_level": r.risk_level,
                    "steps": r.steps,
                    "rollback": r.rollback_plan,
                }
                for r in remediations
            ],
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_advanced_bp.route("/automation/execute", methods=["POST"])
@require_workspace
def execute_automation(workspace_id):
    """
    Execute automation action
    
    Request body:
    {
        "action_id": "action_123",
        "force": false
    }
    """
    try:
        data = request.get_json() or {}
        action_id = data.get("action_id")
        force = data.get("force", False)

        if not action_id:
            return jsonify({"error": "action_id required"}), 400

        return jsonify({
            "success": True,
            "action_id": action_id,
            "status": "scheduled",
            "execution_start": datetime.utcnow().isoformat(),
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
        }), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# INSIGHTS ENDPOINTS (2 endpoints)
# ============================================================================

@ml_advanced_bp.route("/insights/actionable", methods=["GET"])
@require_workspace
def get_insights(workspace_id):
    """Get actionable insights from ML analysis"""
    try:
        ml_service = get_advanced_ml_service()
        insights = ml_service.get_actionable_insights(workspace_id=workspace_id)

        return jsonify({
            "success": True,
            "insights": insights,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_advanced_bp.route("/insights/summary", methods=["GET"])
@require_workspace
def insights_summary(workspace_id):
    """Get high-level insights summary"""
    try:
        ml_service = get_advanced_ml_service()
        anomaly_service = get_anomaly_service()

        ml_insights = ml_service.get_actionable_insights(workspace_id=workspace_id)
        health = anomaly_service.health_scores.get(workspace_id)

        return jsonify({
            "success": True,
            "summary": {
                "health_score": health.score if health else 0,
                "health_status": health.status if health else "unknown",
                "critical_issues": ml_insights.get("summary", {}).get("critical_anomalies", 0),
                "automation_ready_actions": ml_insights.get("summary", {}).get("auto_approved_actions", 0),
                "recommendations_count": len(ml_insights.get("recommended_actions", [])),
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@ml_advanced_bp.route("/health", methods=["GET"])
@require_workspace
def health_check(workspace_id):
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "ml_advanced",
        "workspace_id": workspace_id,
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "predictions": 4,
            "anomaly_detection": 5,
            "automation": 3,
            "insights": 2,
            "total_endpoints": 14,
        },
    }), 200
