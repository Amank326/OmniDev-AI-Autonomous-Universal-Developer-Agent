"""
Optimization WebSocket Handlers for OmniDev AI
Real-time events for resource and cost optimization
"""

from flask import request, current_app
from flask_socketio import emit, join_room, leave_room, rooms
from datetime import datetime
from typing import Dict, List
import json


def register_optimization_websocket(socketio):
    """Register optimization WebSocket event handlers"""

    # ==================== Connection Events ====================

    @socketio.on("connect", namespace="/optimization")
    def handle_optimization_connect():
        """Handle optimization namespace connection"""
        workspace_id = request.args.get("workspace_id")
        if not workspace_id:
            return False

        join_room(f"workspace_{workspace_id}")
        emit("connected", {
            "status": "connected",
            "namespace": "/optimization",
            "timestamp": datetime.utcnow().isoformat(),
        })

    @socketio.on("disconnect", namespace="/optimization")
    def handle_optimization_disconnect():
        """Handle optimization namespace disconnection"""
        emit("disconnected", {
            "status": "disconnected",
            "timestamp": datetime.utcnow().isoformat(),
        })

    # ==================== Resource Analysis Events ====================

    @socketio.on("analyze_resources", namespace="/optimization")
    def handle_analyze_resources(data):
        """Analyze resources in real-time"""
        workspace_id = data.get("workspace_id")
        metrics = data.get("metrics", {})

        if not workspace_id or not metrics:
            emit("error", {"message": "workspace_id and metrics required"})
            return

        from app.services.resource_optimization_service import ResourceOptimizationService
        opt_service = ResourceOptimizationService()

        emit("analysis_started", {
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

        try:
            analysis = opt_service.perform_optimization_analysis(
                workspace_id, metrics, data.get("allocations", {})
            )

            emit("analysis_complete", {
                "workspace_id": workspace_id,
                "utilization": {
                    "cpu": round(analysis.current_utilization.cpu_utilization_percent, 2),
                    "memory": round(analysis.current_utilization.memory_utilization_percent, 2),
                    "bandwidth": round(analysis.current_utilization.bandwidth_utilization_percent, 2),
                    "disk": round(analysis.current_utilization.disk_utilization_percent, 2),
                    "bottleneck": analysis.current_utilization.bottle_neck_resource,
                },
                "efficiency_score": round(analysis.overall_efficiency_score, 3),
                "timestamp": datetime.utcnow().isoformat(),
            }, to=f"workspace_{workspace_id}")

        except Exception as e:
            emit("analysis_error", {"message": str(e)}, to=f"workspace_{workspace_id}")

    @socketio.on("stream_metrics", namespace="/optimization")
    def handle_stream_metrics(data):
        """Stream resource metrics continuously"""
        workspace_id = data.get("workspace_id")
        interval_seconds = data.get("interval_seconds", 5)

        if not workspace_id:
            emit("error", {"message": "workspace_id required"})
            return

        from app.services.resource_optimization_service import ResourceOptimizationService
        opt_service = ResourceOptimizationService()

        emit("streaming_started", {
            "workspace_id": workspace_id,
            "interval_seconds": interval_seconds,
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

    @socketio.on("stop_streaming", namespace="/optimization")
    def handle_stop_streaming(data):
        """Stop metric streaming"""
        workspace_id = data.get("workspace_id")

        emit("streaming_stopped", {
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

    # ==================== Recommendation Events ====================

    @socketio.on("get_recommendations", namespace="/optimization")
    def handle_get_recommendations(data):
        """Get optimization recommendations"""
        workspace_id = data.get("workspace_id")
        metrics = data.get("metrics", {})
        allocations = data.get("allocations", {})

        if not workspace_id or not metrics:
            emit("error", {"message": "workspace_id and metrics required"})
            return

        from app.services.resource_optimization_service import ResourceOptimizationService
        opt_service = ResourceOptimizationService()

        emit("recommendations_loading", {
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

        try:
            analysis = opt_service.perform_optimization_analysis(
                workspace_id, metrics, allocations
            )

            recommendations = [
                {
                    "id": rec.recommendation_id,
                    "type": rec.optimization_type.value,
                    "current": rec.current_allocation,
                    "recommended": rec.recommended_allocation,
                    "savings": round(rec.estimated_savings, 2),
                    "savings_percent": round(rec.savings_percentage, 1),
                    "confidence": round(rec.confidence_score, 3),
                    "complexity": rec.implementation_complexity,
                    "description": rec.description,
                }
                for rec in analysis.recommendations
            ]

            emit("recommendations_ready", {
                "workspace_id": workspace_id,
                "recommendations": recommendations,
                "total": len(recommendations),
                "total_savings": round(analysis.total_potential_savings, 2),
                "quick_wins": len(analysis.quick_wins),
                "timestamp": datetime.utcnow().isoformat(),
            }, to=f"workspace_{workspace_id}")

        except Exception as e:
            emit("recommendations_error", {"message": str(e)}, to=f"workspace_{workspace_id}")

    @socketio.on("apply_recommendation", namespace="/optimization")
    def handle_apply_recommendation(data):
        """Apply a recommendation"""
        workspace_id = data.get("workspace_id")
        recommendation_id = data.get("recommendation_id")

        if not workspace_id or not recommendation_id:
            emit("error", {"message": "workspace_id and recommendation_id required"})
            return

        from app.services.resource_optimization_service import ResourceOptimizationService
        opt_service = ResourceOptimizationService()

        emit("recommendation_applying", {
            "workspace_id": workspace_id,
            "recommendation_id": recommendation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

        try:
            result = opt_service.apply_optimization(workspace_id, recommendation_id)

            if result.get("status") == "success":
                emit("recommendation_applied", {
                    "workspace_id": workspace_id,
                    "recommendation_id": recommendation_id,
                    "estimated_savings": round(result.get("savings", 0), 2),
                    "timestamp": datetime.utcnow().isoformat(),
                }, to=f"workspace_{workspace_id}")
            else:
                emit("recommendation_failed", {
                    "workspace_id": workspace_id,
                    "recommendation_id": recommendation_id,
                    "reason": result.get("message"),
                }, to=f"workspace_{workspace_id}")

        except Exception as e:
            emit("recommendation_error", {
                "workspace_id": workspace_id,
                "message": str(e),
            }, to=f"workspace_{workspace_id}")

    # ==================== Capacity Forecasting Events ====================

    @socketio.on("forecast_capacity", namespace="/optimization")
    def handle_forecast_capacity(data):
        """Generate capacity forecast"""
        workspace_id = data.get("workspace_id")
        current_allocation = data.get("current_allocation", {})
        growth_rate = data.get("growth_rate", 0.02)
        months = data.get("months_ahead", 12)

        if not workspace_id or not current_allocation:
            emit("error", {"message": "workspace_id and current_allocation required"})
            return

        from app.services.resource_optimization_service import ResourceOptimizationService
        opt_service = ResourceOptimizationService()

        emit("forecast_starting", {
            "workspace_id": workspace_id,
            "months_ahead": months,
            "growth_rate": round(growth_rate, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

        try:
            forecast = opt_service.forecast_capacity_needs(
                workspace_id, growth_rate, current_allocation, months
            )

            emit("forecast_complete", {
                "workspace_id": workspace_id,
                "forecast": forecast,
                "growth_rate": round(growth_rate * 100, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }, to=f"workspace_{workspace_id}")

        except Exception as e:
            emit("forecast_error", {"message": str(e)}, to=f"workspace_{workspace_id}")

    @socketio.on("scaling_alert", namespace="/optimization")
    def handle_scaling_alert(data):
        """Check for scaling alerts"""
        workspace_id = data.get("workspace_id")
        threshold_percent = data.get("threshold_percent", 80)

        if not workspace_id:
            emit("error", {"message": "workspace_id required"})
            return

        emit("scaling_alert_check", {
            "workspace_id": workspace_id,
            "threshold": threshold_percent,
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

    # ==================== Cost Analysis Events ====================

    @socketio.on("analyze_costs", namespace="/optimization")
    def handle_analyze_costs(data):
        """Analyze costs"""
        workspace_id = data.get("workspace_id")
        period_days = data.get("period_days", 30)
        num_users = data.get("num_users", 10)

        if not workspace_id:
            emit("error", {"message": "workspace_id required"})
            return

        from app.services.cost_analysis_service import CostAnalysisService
        cost_service = CostAnalysisService()

        emit("cost_analysis_starting", {
            "workspace_id": workspace_id,
            "period_days": period_days,
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

        try:
            analysis = cost_service.analyze_costs(workspace_id, period_days, num_users)

            emit("cost_analysis_complete", {
                "workspace_id": workspace_id,
                "total_cost": round(analysis.total_cost, 2),
                "cost_per_user": round(analysis.cost_per_user, 2),
                "trend": analysis.cost_trend.value,
                "cost_by_category": {k: round(v, 2) for k, v in analysis.cost_by_category.items()},
                "optimization_potential": round(analysis.optimization_potential, 1),
                "timestamp": datetime.utcnow().isoformat(),
            }, to=f"workspace_{workspace_id}")

        except Exception as e:
            emit("cost_analysis_error", {"message": str(e)}, to=f"workspace_{workspace_id}")

    @socketio.on("cost_forecast", namespace="/optimization")
    def handle_cost_forecast(data):
        """Generate cost forecast"""
        workspace_id = data.get("workspace_id")
        months_ahead = data.get("months_ahead", 12)
        growth_rate = data.get("growth_rate", 0.02)

        if not workspace_id:
            emit("error", {"message": "workspace_id required"})
            return

        from app.services.cost_analysis_service import CostAnalysisService
        cost_service = CostAnalysisService()

        emit("forecast_starting", {
            "workspace_id": workspace_id,
            "months_ahead": months_ahead,
            "growth_rate": round(growth_rate * 100, 1),
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

        try:
            # Generate forecast (simplified)
            forecasted_growth = (1 + growth_rate) ** months_ahead
            emit("cost_forecast_complete", {
                "workspace_id": workspace_id,
                "months_ahead": months_ahead,
                "growth_multiplier": round(forecasted_growth, 3),
                "projected_growth_percent": round((forecasted_growth - 1) * 100, 1),
                "timestamp": datetime.utcnow().isoformat(),
            }, to=f"workspace_{workspace_id}")

        except Exception as e:
            emit("forecast_error", {"message": str(e)}, to=f"workspace_{workspace_id}")

    @socketio.on("cost_opportunities", namespace="/optimization")
    def handle_cost_opportunities(data):
        """Get cost optimization opportunities"""
        workspace_id = data.get("workspace_id")
        period_days = data.get("period_days", 30)

        if not workspace_id:
            emit("error", {"message": "workspace_id required"})
            return

        from app.services.cost_analysis_service import CostAnalysisService
        cost_service = CostAnalysisService()

        emit("opportunities_loading", {
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

        try:
            analysis = cost_service.analyze_costs(workspace_id, period_days, 10)

            opportunities = [
                {
                    "id": opp.opportunity_id,
                    "category": opp.category.value,
                    "current_spend": round(opp.current_spend, 2),
                    "recommended_spend": round(opp.recommended_spend, 2),
                    "potential_savings": round(opp.potential_savings, 2),
                    "savings_percent": round(opp.savings_percentage, 1),
                    "effort": opp.effort_level,
                    "payback_months": round(opp.payback_period_months, 1),
                    "risk": opp.risk_level,
                    "description": opp.description,
                }
                for opp in analysis.opportunities
            ]

            emit("opportunities_ready", {
                "workspace_id": workspace_id,
                "opportunities": opportunities,
                "total_count": len(opportunities),
                "total_potential_savings": round(
                    sum(opp.potential_savings for opp in analysis.opportunities), 2
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }, to=f"workspace_{workspace_id}")

        except Exception as e:
            emit("opportunities_error", {"message": str(e)}, to=f"workspace_{workspace_id}")

    # ==================== Notification Events ====================

    @socketio.on("budget_alert", namespace="/optimization")
    def handle_budget_alert(data):
        """Check budget alerts"""
        workspace_id = data.get("workspace_id")
        budget_limit = data.get("budget_limit", 10000)

        if not workspace_id:
            emit("error", {"message": "workspace_id required"})
            return

        emit("budget_check_triggered", {
            "workspace_id": workspace_id,
            "budget_limit": round(budget_limit, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

    @socketio.on("efficiency_alert", namespace="/optimization")
    def handle_efficiency_alert(data):
        """Check efficiency alerts"""
        workspace_id = data.get("workspace_id")
        threshold = data.get("efficiency_threshold", 0.70)

        if not workspace_id:
            emit("error", {"message": "workspace_id required"})
            return

        emit("efficiency_alert_triggered", {
            "workspace_id": workspace_id,
            "threshold": round(threshold, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

    # ==================== Health & Status Events ====================

    @socketio.on("request_status", namespace="/optimization")
    def handle_request_status(data):
        """Request optimization service status"""
        workspace_id = data.get("workspace_id")

        if not workspace_id:
            emit("error", {"message": "workspace_id required"})
            return

        emit("service_status", {
            "workspace_id": workspace_id,
            "resource_optimization_service": "operational",
            "cost_analysis_service": "operational",
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

    @socketio.on("subscribe", namespace="/optimization")
    def handle_subscribe(data):
        """Subscribe to optimization updates"""
        workspace_id = data.get("workspace_id")
        event_types = data.get("event_types", ["all"])

        if not workspace_id:
            emit("error", {"message": "workspace_id required"})
            return

        emit("subscribed", {
            "workspace_id": workspace_id,
            "event_types": event_types,
            "timestamp": datetime.utcnow().isoformat(),
        }, to=f"workspace_{workspace_id}")

    @socketio.on("unsubscribe", namespace="/optimization")
    def handle_unsubscribe(data):
        """Unsubscribe from optimization updates"""
        workspace_id = data.get("workspace_id")

        emit("unsubscribed", {
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
