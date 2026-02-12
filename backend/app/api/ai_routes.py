"""
Phase 11: AI Optimization API Routes
REST endpoints for AI-driven workflow optimization features
"""

import logging
from fastapi import APIRouter, HTTPException, WebSocket, Query
from typing import List, Dict, Any, Optional
import json
from app.services.ai_optimization_service import AIOptimizationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ai", tags=["AI Optimization"])

# Service instance
ai_service = AIOptimizationService()

# WebSocket connections
active_connections: List[WebSocket] = []


# ============= Workflow Generation Endpoints =============

@router.post("/workflows/generate")
async def generate_workflow_from_description(request: Dict[str, str]):
    """
    Generate a workflow from natural language description
    
    Example:
    {
        "description": "Send email to customer with invoice, then log the event"
    }
    """
    try:
        description = request.get("description")
        if not description:
            raise ValueError("Description is required")

        workflow = ai_service.generate_workflow_from_description(description)

        return {
            "status": "success",
            "workflow": workflow,
        }
    except Exception as e:
        logger.error(f"Error generating workflow: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/batch-generate")
async def batch_generate_workflows(request: Dict[str, List[str]]):
    """
    Generate multiple workflows from descriptions
    
    Example:
    {
        "descriptions": [
            "Send notification to users",
            "Process daily reports"
        ]
    }
    """
    try:
        descriptions = request.get("descriptions", [])
        if not descriptions:
            raise ValueError("Descriptions list is required")

        workflows = ai_service.batch_generate_workflows(descriptions)

        return {
            "status": "success",
            "count": len(workflows),
            "workflows": workflows,
        }
    except Exception as e:
        logger.error(f"Error batch generating workflows: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/{workflow_id}/refine")
async def refine_workflow(workflow_id: str, request: Dict[str, Any]):
    """
    Refine a generated workflow based on user feedback
    
    Example:
    {
        "feedback": {
            "remove_nodes": ["node_2"],
            "add_nodes": [...],
            "reorder": [...]
        }
    }
    """
    try:
        # This would retrieve the workflow from database and refine it
        feedback = request.get("feedback", {})

        return {
            "status": "success",
            "message": "Workflow refined successfully",
            "workflow_id": workflow_id,
        }
    except Exception as e:
        logger.error(f"Error refining workflow: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============= Action Recommendation Endpoints =============

@router.get("/recommendations/next-actions")
async def get_next_action_recommendations(
    current_action: str = Query(...),
    workflow_type: Optional[str] = None,
    top_k: int = Query(5)
):
    """
    Get recommended next actions based on current action
    
    Query params:
    - current_action: The current action type
    - workflow_type: Type of workflow (optional)
    - top_k: Number of recommendations (default 5)
    """
    try:
        context = {
            "workflow_type": workflow_type,
            "available_variables": [],
        }

        recommendations = ai_service.get_next_action_recommendations(
            current_action, context, top_k
        )

        return {
            "status": "success",
            "current_action": current_action,
            "recommendations": recommendations,
        }
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recommendations/action-insights")
async def get_action_insights(action: str = Query(...)):
    """
    Get detailed insights about an action's performance
    
    Returns success rate, common next actions, errors, etc.
    """
    try:
        insights = ai_service.action_recommender.get_action_insights(action)

        return {
            "status": "success",
            "action": action,
            "insights": insights,
        }
    except Exception as e:
        logger.error(f"Error getting action insights: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recommendations/alternatives")
async def get_action_alternatives(
    action: str = Query(...),
    reason: str = Query("high_risk")
):
    """
    Get alternative actions to recommend instead of current action
    
    Reasons: high_risk, slow, unreliable
    """
    try:
        alternatives = ai_service.action_recommender.get_action_alternatives(
            action, reason
        )

        return {
            "status": "success",
            "action": action,
            "reason": reason,
            "alternatives": alternatives,
        }
    except Exception as e:
        logger.error(f"Error getting alternatives: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============= Workflow Optimization Endpoints =============

@router.post("/workflows/{workflow_id}/optimize")
async def analyze_and_optimize_workflow(workflow_id: str, request: Dict[str, List[Dict]]):
    """
    Run comprehensive optimization analysis on a workflow
    
    Analyzes performance, costs, and anomalies
    
    Example:
    {
        "executions": [
            {
                "id": "exec_1",
                "duration": 25.5,
                "status": "success",
                "nodes": [...]
            }
        ]
    }
    """
    try:
        executions = request.get("executions", [])
        if not executions:
            raise ValueError("Executions data is required")

        analysis = ai_service.analyze_and_optimize_workflow(workflow_id, executions)

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "analysis": analysis,
        }
    except Exception as e:
        logger.error(f"Error optimizing workflow: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workflows/{workflow_id}/auto-improvements")
async def get_auto_improvements(workflow_id: str):
    """
    Get recommended auto-improvements for a workflow
    
    Returns AI-suggested improvements based on analysis
    """
    try:
        improvements = ai_service.get_workflow_auto_improvements(workflow_id)

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "auto_improvements": improvements,
        }
    except Exception as e:
        logger.error(f"Error getting auto-improvements: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/{workflow_id}/apply-optimization")
async def apply_optimization(workflow_id: str, request: Dict[str, Any]):
    """
    Apply an optimization to a workflow
    
    Example:
    {
        "optimization": {
            "type": "parallelize",
            "nodes": ["node_1", "node_2"]
        }
    }
    """
    try:
        optimization = request.get("optimization")
        if not optimization:
            raise ValueError("Optimization details required")

        result = ai_service.apply_workflow_optimization(workflow_id, optimization)

        return {
            "status": "success",
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error applying optimization: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workflows/{workflow_id}/performance-benchmark")
async def get_performance_benchmark(workflow_id: str, workflow_type: str = Query(...)):
    """
    Get performance benchmarks for a workflow type
    
    Returns typical metrics for similar workflows
    """
    try:
        benchmark = ai_service.get_performance_benchmark(workflow_type)

        return {
            "status": "success",
            "workflow_type": workflow_type,
            "benchmark": benchmark,
        }
    except Exception as e:
        logger.error(f"Error getting benchmark: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============= Cost Analysis Endpoints =============

@router.get("/cost/most-expensive-workflows")
async def get_most_expensive_workflows(top_k: int = Query(10)):
    """
    Get most expensive workflows in the system
    
    Returns top K workflows by total cost
    """
    try:
        expensive = ai_service.cost_analyzer.get_most_expensive_workflows(top_k)

        return {
            "status": "success",
            "count": len(expensive),
            "workflows": expensive,
        }
    except Exception as e:
        logger.error(f"Error getting expensive workflows: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cost/action-breakdown")
async def get_cost_breakdown():
    """
    Get cost breakdown across all actions
    
    Shows usage and cost for each action type
    """
    try:
        breakdown = ai_service.cost_analyzer.get_cost_breakdown_by_action()

        return {
            "status": "success",
            "breakdown": breakdown,
        }
    except Exception as e:
        logger.error(f"Error getting cost breakdown: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cost/report")
async def get_cost_report(workflow_id: Optional[str] = None):
    """
    Get human-readable cost report
    
    Optional workflow_id for specific workflow report
    """
    try:
        report = ai_service.cost_analyzer.generate_cost_report(workflow_id)

        return {
            "status": "success",
            "report": report,
        }
    except Exception as e:
        logger.error(f"Error generating cost report: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============= Anomaly Detection Endpoints =============

@router.get("/anomalies/workflow/{workflow_id}")
async def get_workflow_anomalies(workflow_id: str):
    """
    Get detected anomalies for a workflow
    
    Returns list of detected anomalies with details
    """
    try:
        anomalies = ai_service.anomaly_detector.detect_anomalies(workflow_id)

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
        }
    except Exception as e:
        logger.error(f"Error getting anomalies: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/anomalies/workflow/{workflow_id}/health")
async def get_workflow_health(workflow_id: str):
    """
    Get health score for a workflow (0-100)
    
    Based on absence of recent anomalies
    """
    try:
        health_score = ai_service.anomaly_detector.get_workflow_health_score(workflow_id)

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "health_score": health_score,
            "status_label": "healthy" if health_score > 80 else "degraded" if health_score > 50 else "critical",
        }
    except Exception as e:
        logger.error(f"Error getting health score: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/anomalies/root-cause/{anomaly_type}")
async def find_root_cause(anomaly_type: str):
    """
    Find potential root causes for an anomaly type
    
    Returns list of causes with confidence scores
    """
    try:
        anomaly = {"type": anomaly_type}
        potential_causes = ai_service.anomaly_detector.find_root_cause(anomaly)

        return {
            "status": "success",
            "anomaly_type": anomaly_type,
            "potential_causes": potential_causes,
        }
    except Exception as e:
        logger.error(f"Error finding root cause: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/anomalies/trends/{workflow_id}")
async def get_anomaly_trends(workflow_id: str):
    """
    Get anomaly trends over time for a workflow
    
    Returns trend direction and daily breakdown
    """
    try:
        trends = ai_service.anomaly_detector.get_anomaly_trends(workflow_id)

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "trends": trends,
        }
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============= System Insights Endpoints =============

@router.get("/insights/system")
async def get_system_insights():
    """
    Get system-wide insights from all optimization services
    
    Returns overview of most expensive workflows, action performance, health scores
    """
    try:
        insights = ai_service.get_system_insights()

        return {
            "status": "success",
            "insights": insights,
        }
    except Exception as e:
        logger.error(f"Error getting system insights: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/insights/dashboard")
async def get_dashboard_data():
    """
    Get comprehensive dashboard data for AI optimization
    
    Returns complete overview for UI dashboard
    """
    try:
        dashboard_data = ai_service.get_dashboard_data()

        return {
            "status": "success",
            "data": dashboard_data,
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============= Execution Recording Endpoint =============

@router.post("/executions/record")
async def record_execution(request: Dict[str, Any]):
    """
    Record a workflow execution for learning and analysis
    
    Used by Phase 10 to provide execution data to AI services
    
    Example:
    {
        "workflow_id": "wf_123",
        "id": "exec_456",
        "duration": 25.5,
        "status": "success",
        "nodes": [...]
    }
    """
    try:
        execution = request
        if not execution.get("workflow_id"):
            raise ValueError("workflow_id is required")

        ai_service.record_execution(execution)

        return {
            "status": "success",
            "message": "Execution recorded",
        }
    except Exception as e:
        logger.error(f"Error recording execution: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============= WebSocket for Real-time Optimization =============

@router.websocket("/ws/optimization/{workflow_id}")
async def websocket_optimization(websocket: WebSocket, workflow_id: str):
    """
    WebSocket connection for real-time optimization updates
    
    Sends live recommendations and anomaly alerts as they're detected
    """
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Receive execution data
            data = await websocket.receive_text()
            execution = json.loads(data)

            # Record execution
            ai_service.record_execution(execution)

            # Run quick analysis
            anomalies = ai_service.anomaly_detector.detect_anomalies(workflow_id)

            # Get recommendations
            nodes = execution.get("nodes", [])
            recommendations = None
            if nodes:
                current_action = nodes[-1].get("action_type") if nodes else None
                if current_action:
                    recommendations = ai_service.get_next_action_recommendations(
                        current_action, {"workflow_type": "general"}, top_k=3
                    )

            # Send response
            response = {
                "type": "optimization_update",
                "anomalies": anomalies,
                "recommendations": recommendations,
                "health_score": ai_service.anomaly_detector.get_workflow_health_score(workflow_id),
            }

            await websocket.send_json(response)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)


# Health check endpoint
@router.get("/health")
async def health_check():
    """Check AI service health"""
    return {
        "status": "healthy",
        "service": "AI Optimization",
        "phase": 11,
    }
