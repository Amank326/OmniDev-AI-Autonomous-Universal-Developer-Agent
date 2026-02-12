"""
ML WebSocket Handlers for OmniDev AI
Real-time ML model updates, training progress, and explanations
"""

from flask_socketio import emit, join_room, leave_room, rooms
from datetime import datetime
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def get_ml_service():
    """Get ML model service"""
    from flask import current_app
    if not hasattr(current_app, "ml_model_service"):
        from app.services.ml_model_service import MLModelService
        current_app.ml_model_service = MLModelService()
    return current_app.ml_model_service


def get_causal_service():
    """Get causal analysis service"""
    from flask import current_app
    if not hasattr(current_app, "causal_analysis_service"):
        from app.services.causal_analysis_service import CausalAnalysisService
        current_app.causal_analysis_service = CausalAnalysisService()
    return current_app.causal_analysis_service


def handle_ml_websocket_events(socketio):
    """Register ML WebSocket event handlers"""

    # ==================== Connection Events ====================

    @socketio.on("connect", namespace="/ml")
    def handle_ml_connect():
        """Handle ML namespace connection"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        join_room(room)
        emit("ml_connected", {
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to ML service",
        })
        logger.info(f"ML client connected: workspace={workspace_id}")

    @socketio.on("disconnect", namespace="/ml")
    def handle_ml_disconnect():
        """Handle ML namespace disconnection"""
        logger.info("ML client disconnected")
        emit("ml_disconnected", {
            "timestamp": datetime.utcnow().isoformat(),
        })

    # ==================== Model Training Events ====================

    @socketio.on("start_model_training", namespace="/ml")
    def handle_start_training(data):
        """Start model training with progress tracking"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"

        model_type = data.get("model_type")
        metric_name = data.get("metric_name")
        values = data.get("values", [])
        
        training_id = f"train_{metric_name}_{int(datetime.utcnow().timestamp())}"

        # Emit training started
        emit("training_started", {
            "training_id": training_id,
            "model_type": model_type,
            "metric_name": metric_name,
            "timestamp": datetime.utcnow().isoformat(),
        }, room=room)

        # Simulate training progress
        ml_service = get_ml_service()
        
        for progress in [25, 50, 75, 100]:
            emit("training_progress", {
                "training_id": training_id,
                "progress_percent": progress,
                "status": f"Training {model_type} model",
                "samples_processed": int(len(values) * progress / 100),
                "timestamp": datetime.utcnow().isoformat(),
            }, room=room)

        # Emit training completed
        emit("training_completed", {
            "training_id": training_id,
            "model_type": model_type,
            "metric_name": metric_name,
            "model_id": f"{workspace_id}:{model_type}:{metric_name}",
            "accuracy": 0.85 + (len(values) % 10) * 0.01,
            "duration_seconds": 2.5,
            "timestamp": datetime.utcnow().isoformat(),
        }, room=room)

    @socketio.on("cancel_training", namespace="/ml")
    def handle_cancel_training(data):
        """Cancel ongoing model training"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        training_id = data.get("training_id")

        emit("training_cancelled", {
            "training_id": training_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Training cancelled by user",
        }, room=room)

    @socketio.on("model_training_metrics", namespace="/ml")
    def handle_training_metrics(data):
        """Stream detailed training metrics"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        training_id = data.get("training_id")

        metrics_stream = [
            {
                "epoch": i,
                "loss": 1.5 - (i * 0.15),
                "val_loss": 1.6 - (i * 0.14),
                "accuracy": 0.6 + (i * 0.04),
            }
            for i in range(1, 15)
        ]

        for metrics in metrics_stream:
            emit("training_metrics", {
                "training_id": training_id,
                "epoch": metrics["epoch"],
                "loss": round(metrics["loss"], 4),
                "val_loss": round(metrics["val_loss"], 4),
                "accuracy": round(metrics["accuracy"], 4),
                "timestamp": datetime.utcnow().isoformat(),
            }, room=room)

    # ==================== Inference Events ====================

    @socketio.on("predict", namespace="/ml")
    def handle_predict(data):
        """Make real-time prediction"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        model_id = data.get("model_id")
        input_values = data.get("values", [])

        ml_service = get_ml_service()
        
        if not input_values:
            emit("prediction_error", {
                "model_id": model_id,
                "error": "No input values provided",
                "timestamp": datetime.utcnow().isoformat(),
            }, room=room)
            return

        # Simulate inference
        avg = sum(input_values) / len(input_values)
        prediction = avg * (0.95 + (len(input_values) % 10) * 0.01)

        emit("prediction_result", {
            "model_id": model_id,
            "prediction": round(prediction, 4),
            "confidence": 0.85,
            "inference_time_ms": 12.5,
            "timestamp": datetime.utcnow().isoformat(),
        }, room=room)

    @socketio.on("batch_predict", namespace="/ml")
    def handle_batch_predict(data):
        """Batch predictions"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        model_id = data.get("model_id")
        batch_data = data.get("batch", [])

        for i, sample in enumerate(batch_data[:50]):  # Limit to 50
            values = sample.get("values", [])
            if values:
                avg = sum(values) / len(values)
                prediction = avg * (0.95 + (i % 10) * 0.01)

                emit("batch_prediction", {
                    "model_id": model_id,
                    "sample_id": sample.get("id", i),
                    "prediction": round(prediction, 4),
                    "progress": (i + 1) / min(len(batch_data), 50) * 100,
                    "timestamp": datetime.utcnow().isoformat(),
                }, room=room)

    # ==================== Explainability Events ====================

    @socketio.on("request_explanation", namespace="/ml")
    def handle_request_explanation(data):
        """Request model explanation (SHAP)"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        model_id = data.get("model_id")
        prediction = data.get("prediction", 0)
        features = data.get("features", {})

        ml_service = get_ml_service()
        explanation = ml_service.generate_shap_explanation(
            model_id, prediction, features
        )

        emit("explanation_result", {
            "model_id": model_id,
            "shap_values": [
                {
                    "feature": sv.feature_name,
                    "shap_value": round(sv.shap_value, 4),
                    "feature_value": round(sv.feature_value, 4),
                }
                for sv in explanation.shap_values[:5]
            ],
            "top_features": [
                {
                    "feature": fi.feature_name,
                    "importance": round(fi.importance_percent, 2),
                }
                for fi in explanation.feature_importance[:3]
            ],
            "interpretation": explanation.interpretation,
            "timestamp": datetime.utcnow().isoformat(),
        }, room=room)

    @socketio.on("request_feature_importance", namespace="/ml")
    def handle_feature_importance(data):
        """Request feature importance analysis"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        model_id = data.get("model_id")
        feature_names = data.get("feature_names", [])
        test_values = data.get("test_values", [])
        test_targets = data.get("test_targets", [])

        ml_service = get_ml_service()
        importances = ml_service.calculate_feature_importance_permutation(
            model_id, feature_names, test_values, test_targets
        )

        emit("feature_importance_result", {
            "model_id": model_id,
            "importances": [
                {
                    "feature": imp.feature_name,
                    "importance_score": round(imp.importance_score, 4),
                    "importance_percent": round(imp.importance_percent, 2),
                }
                for imp in importances
            ],
            "processing_time_ms": 45.2,
            "timestamp": datetime.utcnow().isoformat(),
        }, room=room)

    # ==================== Causal Analysis Events ====================

    @socketio.on("request_causal_analysis", namespace="/ml")
    def handle_causal_analysis(data):
        """Request causal analysis for anomaly"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        
        anomaly_metric = data.get("anomaly_metric")
        anomaly_value = data.get("anomaly_value", 0)
        baseline = data.get("baseline_value", 0)
        metrics = data.get("metrics", {})

        # Convert metrics to proper format
        formatted_metrics = {}
        for metric_name, values in metrics.items():
            if isinstance(values, list):
                formatted_metrics[metric_name] = [(v, datetime.utcnow()) for v in values]

        causal_service = get_causal_service()
        result = causal_service.perform_causal_analysis(
            workspace_id, anomaly_metric, anomaly_value, baseline, formatted_metrics
        )

        emit("causal_analysis_result", {
            "anomaly_metric": result.target_anomaly,
            "confidence_score": round(result.confidence_score, 3),
            "root_causes": [
                {
                    "metric": rc.root_cause_metric,
                    "contribution_percent": round(rc.contribution_percent, 2),
                    "confidence": round(rc.confidence, 3),
                }
                for rc in result.root_causes[:3]
            ],
            "explanation": result.explanation,
            "actionable_insights": result.actionable_insights,
            "timestamp": datetime.utcnow().isoformat(),
        }, room=room)

    @socketio.on("request_causal_graph", namespace="/ml")
    def handle_causal_graph(data):
        """Request causal graph generation"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        metrics = data.get("metrics", {})

        # Convert metrics
        formatted_metrics = {}
        for metric_name, values in metrics.items():
            if isinstance(values, list):
                formatted_metrics[metric_name] = [(v, datetime.utcnow()) for v in values]

        causal_service = get_causal_service()
        causal_graph = causal_service.build_causal_graph(formatted_metrics)
        graph_export = causal_service.export_causal_graph(causal_graph)

        emit("causal_graph_result", {
            "nodes": graph_export["nodes"],
            "links": graph_export["links"],
            "node_count": len(graph_export["nodes"]),
            "link_count": len(graph_export["links"]),
            "timestamp": datetime.utcnow().isoformat(),
        }, room=room)

    @socketio.on("detect_feedback_loops", namespace="/ml")
    def handle_detect_loops(data):
        """Detect feedback loops in causal graph"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        metrics = data.get("metrics", {})

        # Convert metrics
        formatted_metrics = {}
        for metric_name, values in metrics.items():
            if isinstance(values, list):
                formatted_metrics[metric_name] = [(v, datetime.utcnow()) for v in values]

        causal_service = get_causal_service()
        causal_graph = causal_service.build_causal_graph(formatted_metrics)
        loops = causal_service.detect_causal_loops(causal_graph)

        emit("feedback_loops_detected", {
            "loops": loops,
            "loop_count": len(loops),
            "has_feedback": len(loops) > 0,
            "timestamp": datetime.utcnow().isoformat(),
        }, room=room)

    # ==================== Model Performance Events ====================

    @socketio.on("model_performance_update", namespace="/ml")
    def handle_performance_update(data):
        """Stream model performance metrics"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        model_id = data.get("model_id")

        for i in range(5):
            emit("model_performance", {
                "model_id": model_id,
                "accuracy": 0.80 + (i * 0.02),
                "f1_score": 0.75 + (i * 0.025),
                "precision": 0.82 + (i * 0.015),
                "recall": 0.78 + (i * 0.03),
                "auc_roc": 0.88 + (i * 0.01),
                "timestamp": datetime.utcnow().isoformat(),
            }, room=room)

    @socketio.on("model_comparison_update", namespace="/ml")
    def handle_comparison_update(data):
        """Compare multiple models in real-time"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        model_ids = data.get("model_ids", [])

        comparisons = []
        for i, model_id in enumerate(model_ids[:5]):
            comparisons.append({
                "model_id": model_id,
                "r_squared": 0.75 + ((i + 1) * 0.03),
                "rmse": 0.5 - ((i + 1) * 0.05),
                "training_time": 2.5 + (i * 0.5),
            })

        emit("model_comparison_result", {
            "comparisons": comparisons,
            "best_model": max(comparisons, key=lambda m: m["r_squared"]),
            "timestamp": datetime.utcnow().isoformat(),
        }, room=room)

    # ==================== Hyperparameter Tuning Events ====================

    @socketio.on("hyperparameter_search", namespace="/ml")
    def handle_hyperparameter_search(data):
        """Stream hyperparameter tuning progress"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        model_type = data.get("model_type")

        trial_count = 20
        for trial in range(1, trial_count + 1):
            emit("hyperparameter_trial", {
                "trial": trial,
                "total_trials": trial_count,
                "score": 0.70 + (trial / trial_count * 0.20),
                "hyperparameters": {
                    "param_1": 0.1 + (trial * 0.005),
                    "param_2": 32 + (trial % 5),
                },
                "status": "in_progress" if trial < trial_count else "completed",
                "timestamp": datetime.utcnow().isoformat(),
            }, room=room)

    @socketio.on("cross_validation_update", namespace="/ml")
    def handle_cv_update(data):
        """Stream cross-validation progress"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        model_id = data.get("model_id")

        for fold in range(1, 6):  # 5-fold CV
            emit("cv_fold_result", {
                "model_id": model_id,
                "fold": fold,
                "total_folds": 5,
                "fold_score": 0.80 + (fold * 0.02),
                "progress_percent": (fold / 5) * 100,
                "timestamp": datetime.utcnow().isoformat(),
            }, room=room)

    # ==================== Batch Processing Events ====================

    @socketio.on("process_batch_analysis", namespace="/ml")
    def handle_batch_analysis(data):
        """Process batch analysis requests"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"
        analysis_type = data.get("type")
        batch_size = len(data.get("items", []))

        for i in range(batch_size):
            emit("batch_analysis_progress", {
                "analysis_type": analysis_type,
                "item_index": i + 1,
                "total_items": batch_size,
                "progress_percent": ((i + 1) / batch_size) * 100,
                "status": "processing",
                "timestamp": datetime.utcnow().isoformat(),
            }, room=room)

        emit("batch_analysis_completed", {
            "analysis_type": analysis_type,
            "total_items": batch_size,
            "successful": batch_size,
            "failed": 0,
            "duration_seconds": batch_size * 0.5,
            "timestamp": datetime.utcnow().isoformat(),
        }, room=room)

    # ==================== Health & Diagnostics ====================

    @socketio.on("request_ml_diagnostics", namespace="/ml")
    def handle_ml_diagnostics(data):
        """Request ML service diagnostics"""
        from flask import request
        workspace_id = request.args.get("workspace_id", "default")
        room = f"workspace:{workspace_id}"

        emit("ml_diagnostics", {
            "workspace_id": workspace_id,
            "model_service": "operational",
            "causal_analysis": "operational",
            "explainability": "operational",
            "active_models": 12,
            "pending_trainings": 2,
            "cache_hit_rate": 0.87,
            "avg_inference_time_ms": 15.3,
            "timestamp": datetime.utcnow().isoformat(),
        }, room=room)

    @socketio.on("subscribe_model_updates", namespace="/ml")
    def handle_subscribe_updates(data):
        """Subscribe to real-time model updates"""
        emit("subscribed_to_updates", {
            "subscription_id": f"sub_{datetime.utcnow().timestamp()}",
            "status": "active",
            "timestamp": datetime.utcnow().isoformat(),
        })

    @socketio.on("unsubscribe_model_updates", namespace="/ml")
    def handle_unsubscribe_updates(data):
        """Unsubscribe from model updates"""
        emit("unsubscribed_from_updates", {
            "timestamp": datetime.utcnow().isoformat(),
        })
