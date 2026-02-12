"""
Advanced ML WebSocket Handlers for OmniDev AI
Real-time ML predictions, anomaly detection, and automation updates
"""

from flask_socketio import Namespace, emit, join_room, leave_room
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading
import time


class AdvancedMLNamespace(Namespace):
    """WebSocket namespace for advanced ML features (/ml_advanced)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscriptions: Dict[str, set] = {}  # workspace -> set of subscribed event types
        self.streaming_sessions: Dict[str, bool] = {}  # session_id -> active
        self.ml_service = None
        self.anomaly_service = None

    def on_connect(self):
        """Handle client connection"""
        try:
            workspace_id = self.get_workspace_id()
            if not workspace_id:
                self.disconnect()
                return

            if not hasattr(self, 'ml_service'):
                from app.services.advanced_ml_service import AdvancedMLService
                self.ml_service = AdvancedMLService()

            if not hasattr(self, 'anomaly_service'):
                from app.services.anomaly_detection_service import AnomalyDetectionService
                self.anomaly_service = AnomalyDetectionService()

            join_room(workspace_id)
            self.subscriptions[workspace_id] = set()

            emit('ml_connected', {
                'workspace_id': workspace_id,
                'timestamp': datetime.utcnow().isoformat(),
                'message': 'Connected to ML advanced features',
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    def on_disconnect(self):
        """Handle client disconnection"""
        try:
            workspace_id = self.get_workspace_id()
            if workspace_id:
                leave_room(workspace_id)
                if workspace_id in self.subscriptions:
                    del self.subscriptions[workspace_id]

                # Stop any active streaming
                for sid in list(self.streaming_sessions.keys()):
                    if workspace_id in sid:
                        self.streaming_sessions[sid] = False

        except Exception as e:
            print(f"Disconnect error: {e}")

    def get_workspace_id(self) -> Optional[str]:
        """Extract workspace ID from session/request"""
        # In production, get from authenticated session
        return self.request.args.get('workspace_id') or 'default_workspace'

    # ========================================================================
    # PREDICTION EVENTS (4 event types)
    # ========================================================================

    def on_predict_metric(self, data):
        """
        Request metric prediction
        
        Emits:
        - prediction_result: Single metric prediction
        """
        try:
            workspace_id = self.get_workspace_id()
            metric_name = data.get('metric_name')
            forecast_hours = data.get('forecast_hours', 168)
            model_type = data.get('model_type', 'ensemble')

            prediction = self.ml_service.predict_metric(
                workspace_id=workspace_id,
                metric_name=metric_name,
                forecast_hours=forecast_hours,
                model_type=model_type,
            )

            if prediction:
                emit('prediction_result', {
                    'prediction_id': prediction.prediction_id,
                    'metric': metric_name,
                    'predicted_value': prediction.predicted_value,
                    'lower_bound': prediction.lower_bound,
                    'upper_bound': prediction.upper_bound,
                    'confidence': prediction.confidence,
                    'confidence_level': prediction.confidence_level.value,
                    'model_type': model_type,
                    'mape': prediction.mape,
                })
            else:
                emit('error', {'message': f'Unable to predict {metric_name} - insufficient data'})

        except Exception as e:
            emit('error', {'message': str(e)})

    def on_stream_predictions(self, data):
        """
        Stream continuous predictions for metric
        
        Emits:
        - prediction_update: Prediction every X seconds
        """
        try:
            workspace_id = self.get_workspace_id()
            metric_name = data.get('metric_name')
            interval_seconds = data.get('interval_seconds', 30)
            stop_after_minutes = data.get('stop_after_minutes', 60)

            session_id = f"{workspace_id}:stream:{int(time.time())}"
            self.streaming_sessions[session_id] = True

            def stream_predictions():
                start_time = time.time()
                max_duration = stop_after_minutes * 60

                while self.streaming_sessions.get(session_id, False):
                    if time.time() - start_time > max_duration:
                        break

                    prediction = self.ml_service.predict_metric(
                        workspace_id=workspace_id,
                        metric_name=metric_name,
                    )

                    if prediction:
                        self.emit('prediction_update', {
                            'metric': metric_name,
                            'predicted_value': prediction.predicted_value,
                            'confidence': prediction.confidence,
                            'timestamp': datetime.utcnow().isoformat(),
                        }, room=workspace_id)

                    time.sleep(interval_seconds)

                self.emit('prediction_stream_stopped', {
                    'metric': metric_name,
                    'reason': 'Duration limit reached',
                }, room=workspace_id)

            thread = threading.Thread(target=stream_predictions, daemon=True)
            thread.start()

            emit('prediction_stream_started', {
                'metric': metric_name,
                'interval_seconds': interval_seconds,
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    def on_get_batch_predictions(self, data):
        """
        Get predictions for multiple metrics
        
        Emits:
        - batch_predictions: All metric predictions
        """
        try:
            workspace_id = self.get_workspace_id()
            metrics = data.get('metrics', [])
            forecast_hours = data.get('forecast_hours', 168)

            predictions = []
            for metric in metrics:
                pred = self.ml_service.predict_metric(
                    workspace_id=workspace_id,
                    metric_name=metric,
                    forecast_hours=forecast_hours,
                )
                if pred:
                    predictions.append({
                        'metric': metric,
                        'predicted_value': pred.predicted_value,
                        'confidence': pred.confidence,
                        'confidence_level': pred.confidence_level.value,
                    })

            emit('batch_predictions', {
                'predictions': predictions,
                'count': len(predictions),
                'timestamp': datetime.utcnow().isoformat(),
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    def on_model_metrics(self, data):
        """
        Get ML model performance metrics
        
        Emits:
        - model_performance: Model metrics
        """
        try:
            workspace_id = self.get_workspace_id()
            model_type = data.get('model_type', 'ensemble')

            metrics = self.ml_service.get_model_performance(
                workspace_id=workspace_id,
                model_type=model_type,
            )

            if metrics:
                emit('model_performance', {
                    'model_type': metrics.model_type.value,
                    'accuracy': metrics.accuracy,
                    'precision': metrics.precision,
                    'recall': metrics.recall,
                    'f1_score': metrics.f1_score,
                    'mape': metrics.mape,
                    'rmse': metrics.rmse,
                    'r_squared': metrics.r_squared,
                    'last_training': metrics.last_training_date.isoformat(),
                })
            else:
                emit('error', {'message': f'Model {model_type} not found'})

        except Exception as e:
            emit('error', {'message': str(e)})

    # ========================================================================
    # ANOMALY DETECTION EVENTS (4 event types)
    # ========================================================================

    def on_detect_anomalies(self, data):
        """
        Detect anomalies across metrics
        
        Emits:
        - anomalies_detected: List of detected anomalies
        """
        try:
            workspace_id = self.get_workspace_id()
            metrics = data.get('metrics', {})
            historical = data.get('historical', {})
            sensitivity = data.get('sensitivity', 'medium')

            anomalies = self.anomaly_service.detect_anomalies_comprehensive(
                workspace_id=workspace_id,
                metrics=metrics,
                historical_data=historical,
            )

            emit('anomalies_detected', {
                'count': len(anomalies),
                'anomalies': [
                    {
                        'anomaly_id': a.anomaly_id,
                        'metrics': a.metrics_affected,
                        'severity': a.severity.value,
                        'impact_score': a.impact_score,
                        'affected_services': a.affected_services,
                    }
                    for a in anomalies
                ],
                'timestamp': datetime.utcnow().isoformat(),
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    def on_stream_anomalies(self, data):
        """
        Stream anomaly detection updates
        
        Emits:
        - anomaly_alert: When anomaly detected
        """
        try:
            workspace_id = self.get_workspace_id()
            interval_seconds = data.get('interval_seconds', 60)

            session_id = f"{workspace_id}:anomaly_stream:{int(time.time())}"
            self.streaming_sessions[session_id] = True

            self.subscriptions[workspace_id].add('anomalies')

            emit('anomaly_stream_started', {
                'interval_seconds': interval_seconds,
                'timestamp': datetime.utcnow().isoformat(),
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    def on_analyze_root_cause(self, data):
        """
        Analyze root cause of anomaly
        
        Emits:
        - root_cause_analysis: Analysis result
        """
        try:
            workspace_id = self.get_workspace_id()
            anomaly_id = data.get('anomaly_id')
            anomaly = data.get('anomaly')
            event_log = data.get('event_log')

            rca = self.anomaly_service.analyze_root_cause(
                workspace_id=workspace_id,
                anomaly_id=anomaly_id,
                anomaly=anomaly,
                event_log=event_log,
            )

            emit('root_cause_analysis', {
                'analysis_id': rca.analysis_id,
                'anomaly_id': rca.anomaly_id,
                'primary_root_cause': rca.primary_root_cause.value,
                'confidence': rca.confidence_score,
                'root_causes': [
                    {
                        'type': rc['type'],
                        'description': rc['description'],
                        'confidence': rc['confidence_score'],
                    }
                    for rc in rca.root_causes
                ],
                'evidence': rca.evidence,
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    def on_get_patterns(self, data):
        """
        Get recurring anomaly patterns
        
        Emits:
        - anomaly_patterns: List of patterns
        """
        try:
            workspace_id = self.get_workspace_id()
            lookback_days = data.get('lookback_days', 30)

            patterns = self.anomaly_service.detect_anomaly_patterns(
                workspace_id=workspace_id,
                lookback_days=lookback_days,
            )

            emit('anomaly_patterns', {
                'patterns': [
                    {
                        'pattern_id': p.pattern_id,
                        'name': p.pattern_name,
                        'metrics': p.metrics_involved,
                        'frequency': p.occurrence_frequency,
                        'occurrences': p.occurrences_count,
                        'seasonal': p.seasonal,
                    }
                    for p in patterns
                ],
                'count': len(patterns),
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    # ========================================================================
    # AUTOMATION EVENTS (3 event types)
    # ========================================================================

    def on_generate_remediation(self, data):
        """
        Generate remediation plan
        
        Emits:
        - remediation_plan: Action plan
        """
        try:
            workspace_id = self.get_workspace_id()
            anomaly = data.get('anomaly')
            root_cause = data.get('root_cause')

            remediations = self.anomaly_service.generate_remediation_plan(
                workspace_id=workspace_id,
                anomaly=anomaly,
                root_cause=root_cause,
            )

            emit('remediation_plan', {
                'remediations': [
                    {
                        'remediation_id': r.remediation_id,
                        'action_type': r.action_type,
                        'description': r.action_description,
                        'automatic': r.automatic,
                        'estimated_time': r.estimated_resolution_time_minutes,
                        'risk_level': r.risk_level,
                        'steps': r.steps,
                    }
                    for r in remediations
                ],
                'count': len(remediations),
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    def on_execute_remediation(self, data):
        """
        Execute remediation action
        
        Emits:
        - remediation_started: Execution started
        - remediation_progress: Progress updates
        """
        try:
            workspace_id = self.get_workspace_id()
            remediation_id = data.get('remediation_id')
            force = data.get('force', False)

            emit('remediation_started', {
                'remediation_id': remediation_id,
                'status': 'in_progress',
                'started_at': datetime.utcnow().isoformat(),
                'estimated_completion': (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            })

            # Simulate progress updates
            for progress in [25, 50, 75, 100]:
                time.sleep(1)  # In production, replace with actual work
                emit('remediation_progress', {
                    'remediation_id': remediation_id,
                    'progress_percent': progress,
                    'status_message': f'Step {progress // 25} of 4 complete',
                })

            emit('remediation_completed', {
                'remediation_id': remediation_id,
                'status': 'completed',
                'completed_at': datetime.utcnow().isoformat(),
                'result': 'success',
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    def on_automation_status(self, data):
        """
        Get status of scheduled automation actions
        
        Emits:
        - automation_status: Status report
        """
        try:
            workspace_id = self.get_workspace_id()

            actions = self.ml_service.scheduled_actions.get(workspace_id, [])

            pending = [a for a in actions if not a.auto_approved]
            auto_approved = [a for a in actions if a.auto_approved]

            emit('automation_status', {
                'pending_actions': len(pending),
                'auto_approved_actions': len(auto_approved),
                'next_action': {
                    'action_id': pending[0].action_id,
                    'type': pending[0].action_type,
                    'scheduled': pending[0].scheduled_at.isoformat(),
                } if pending else None,
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    # ========================================================================
    # INSIGHTS EVENTS (2 event types)
    # ========================================================================

    def on_get_insights(self, data):
        """
        Get actionable insights from ML analysis
        
        Emits:
        - insights_update: Actionable insights
        """
        try:
            workspace_id = self.get_workspace_id()

            insights = self.ml_service.get_actionable_insights(workspace_id=workspace_id)

            emit('insights_update', {
                'insights': insights,
                'timestamp': datetime.utcnow().isoformat(),
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    def on_subscribe_alerts(self, data):
        """
        Subscribe to alert notifications
        
        Emits:
        - alert: When critical event occurs
        """
        try:
            workspace_id = self.get_workspace_id()
            alert_types = data.get('alert_types', [
                'critical_anomaly',
                'auto_remediation',
                'health_degradation',
            ])

            if workspace_id not in self.subscriptions:
                self.subscriptions[workspace_id] = set()

            self.subscriptions[workspace_id].update(alert_types)

            emit('subscribed_to_alerts', {
                'alert_types': alert_types,
                'timestamp': datetime.utcnow().isoformat(),
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    # ========================================================================
    # MANAGEMENT EVENTS
    # ========================================================================

    def on_stop_stream(self, data):
        """Stop active streaming"""
        try:
            workspace_id = self.get_workspace_id()
            stream_type = data.get('stream_type')

            for sid in list(self.streaming_sessions.keys()):
                if workspace_id in sid and (not stream_type or stream_type in sid):
                    self.streaming_sessions[sid] = False

            emit('stream_stopped', {
                'stream_type': stream_type or 'all',
                'workspace_id': workspace_id,
            })

        except Exception as e:
            emit('error', {'message': str(e)})

    def on_unsubscribe(self, data):
        """Unsubscribe from events"""
        try:
            workspace_id = self.get_workspace_id()
            event_types = data.get('event_types', [])

            if workspace_id in self.subscriptions:
                for event_type in event_types:
                    self.subscriptions[workspace_id].discard(event_type)

            emit('unsubscribed', {
                'event_types': event_types,
            })

        except Exception as e:
            emit('error', {'message': str(e)})
