"""
Phase 15: Agent Routes
- Agent discovery and search
- Agent deployment
- Workflow management
- Execution monitoring
- Cost and performance analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

# Service dependencies (injected from main.py)
agent_marketplace_svc = None
agent_orchestration_svc = None
agent_monitoring_svc = None


def set_agent_services(marketplace, orchestration, monitoring):
    """Inject services"""
    global agent_marketplace_svc, agent_orchestration_svc, agent_monitoring_svc
    agent_marketplace_svc = marketplace
    agent_orchestration_svc = orchestration
    agent_monitoring_svc = monitoring


# ============ DISCOVERY & SEARCH ============

@router.get("/search")
async def search_agents(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    min_rating: float = Query(0.0, ge=0.0, le=5.0, description="Minimum rating"),
    is_paid_only: bool = Query(False, description="Show only paid agents"),
    sort_by: str = Query("rating", regex="^(rating|downloads|trending|newest)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """Search agents with filters and sorting"""
    try:
        result = agent_marketplace_svc.search_agents(
            query=query,
            category=category,
            tags=tags,
            min_rating=min_rating,
            is_paid_only=is_paid_only,
            sort_by=sort_by,
            limit=limit,
            offset=offset
        )
        return {
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "slug": agent.slug,
                    "description": agent.description,
                    "category": agent.category,
                    "average_rating": agent.average_rating,
                    "downloads": agent.downloads,
                    "icon_url": agent.icon_url,
                    "is_verified": agent.is_verified
                }
                for agent in result["agents"]
            ],
            "total_count": result["total_count"],
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/featured")
async def get_featured_agents(limit: int = Query(10, ge=1, le=50)) -> Dict[str, Any]:
    """Get featured agents"""
    try:
        agents = agent_marketplace_svc.get_featured_agents(limit=limit)
        return {
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "slug": agent.slug,
                    "description": agent.description,
                    "average_rating": agent.average_rating,
                    "icon_url": agent.icon_url
                }
                for agent in agents
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending")
async def get_trending_agents(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50)
) -> Dict[str, Any]:
    """Get trending agents"""
    try:
        agents = agent_marketplace_svc.get_trending_agents(days=days, limit=limit)
        return {
            "agents": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "slug": agent.slug,
                    "description": agent.description,
                    "deployments": agent.deployments,
                    "average_rating": agent.average_rating
                }
                for agent in agents
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}")
async def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get agent details"""
    try:
        agent = agent_marketplace_svc.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "full_description": agent.full_description,
            "agent_type": agent.agent_type,
            "model_provider": agent.model_provider,
            "model_name": agent.model_name,
            "temperature": agent.temperature,
            "capabilities": agent.capabilities,
            "supported_integrations": agent.supported_integrations,
            "is_autonomous": agent.is_autonomous,
            "can_execute_code": agent.can_execute_code,
            "average_rating": agent.average_rating,
            "rating_count": agent.rating_count,
            "downloads": agent.downloads,
            "deployments": agent.deployments,
            "is_verified": agent.is_verified,
            "is_featured": agent.is_featured,
            "price": agent.price if agent.is_paid else 0.0,
            "documentation_url": agent.documentation_url,
            "example_prompts": agent.example_prompts
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ DEPLOYMENT MANAGEMENT ============

@router.post("/deployments")
async def create_deployment(
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Create a deployment of an agent"""
    try:
        deployment = agent_marketplace_svc.create_deployment(
            agent_id=body["agent_id"],
            user_id=x_user_id,
            name=body["name"],
            environment=body.get("environment", "production"),
            custom_system_prompt=body.get("custom_system_prompt"),
            custom_parameters=body.get("custom_parameters"),
            api_keys=body.get("api_keys")
        )
        return deployment
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/deployments")
async def list_deployments(
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get user's deployments"""
    try:
        deployments = agent_marketplace_svc.get_user_deployments(x_user_id)
        return {
            "deployments": [
                {
                    "id": d.id,
                    "agent_id": d.agent_id,
                    "name": d.name,
                    "environment": d.environment,
                    "is_active": d.is_active,
                    "created_at": d.created_at.isoformat()
                }
                for d in deployments
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/deployments/{deployment_id}")
async def update_deployment(
    deployment_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Update deployment configuration"""
    try:
        success = agent_marketplace_svc.update_deployment_config(
            deployment_id=deployment_id,
            custom_system_prompt=body.get("custom_system_prompt"),
            custom_parameters=body.get("custom_parameters")
        )
        if not success:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        return {"status": "updated", "deployment_id": deployment_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ RATINGS & REVIEWS ============

@router.post("/{agent_id}/ratings")
async def rate_agent(
    agent_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Submit rating for an agent"""
    try:
        rating = agent_marketplace_svc.rate_agent(
            agent_id=agent_id,
            user_id=x_user_id,
            rating=body["rating"],
            review_title=body.get("review_title"),
            review_text=body.get("review_text")
        )
        return rating
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_id}/reviews")
async def get_agent_reviews(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """Get reviews for an agent"""
    try:
        reviews = agent_marketplace_svc.get_agent_reviews(agent_id, limit=limit)
        return {
            "reviews": [
                {
                    "id": r.id,
                    "rating": r.rating,
                    "review_title": r.review_title,
                    "review_text": r.review_text,
                    "helpful_count": r.helpful_count,
                    "created_at": r.created_at.isoformat()
                }
                for r in reviews
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ WORKFLOW MANAGEMENT ============

@router.post("/workflows")
async def create_workflow(
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Create an agent workflow"""
    try:
        workflow = agent_orchestration_svc.create_workflow(
            name=body["name"],
            description=body.get("description", ""),
            user_id=x_user_id,
            agents=body["agents"],
            routing=body.get("routing")
        )
        return workflow
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workflows")
async def list_workflows(
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get user's workflows"""
    try:
        workflows = agent_orchestration_svc.list_user_workflows(x_user_id)
        return {
            "workflows": [
                {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "status": w.status,
                    "created_at": w.created_at.isoformat()
                }
                for w in workflows
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """Get workflow definition"""
    try:
        workflow = agent_orchestration_svc.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status,
            "definition": workflow.workflow_definition,
            "created_at": workflow.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    body: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Execute a workflow"""
    try:
        result = agent_orchestration_svc.execute_workflow(
            workflow_id=workflow_id,
            user_id=x_user_id,
            initial_input=body.get("input"),
            context=body.get("context")
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str) -> Dict[str, Any]:
    """Get workflow execution details"""
    try:
        execution = agent_orchestration_svc.get_workflow_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return {
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "input": execution.input_data,
            "output": execution.output_data,
            "error": execution.error_message,
            "created_at": execution.created_at.isoformat(),
            "started_at": execution.start_time.isoformat() if execution.start_time else None,
            "ended_at": execution.end_time.isoformat() if execution.end_time else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ MONITORING & ANALYTICS ============

@router.get("/{agent_id}/performance")
async def get_agent_performance(
    agent_id: str,
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """Get agent performance metrics"""
    try:
        performance = agent_monitoring_svc.get_agent_performance(agent_id, days=days)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/percentiles")
async def get_percentile_metrics(
    agent_id: str,
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """Get execution time percentiles"""
    try:
        metrics = agent_monitoring_svc.get_percentile_metrics(agent_id, days=days)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/health")
async def check_agent_health(agent_id: str) -> Dict[str, Any]:
    """Check agent health status"""
    try:
        health = agent_monitoring_svc.check_agent_health(agent_id)
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/health-history")
async def get_health_history(
    agent_id: str,
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """Get agent health history"""
    try:
        history = agent_monitoring_svc.get_agent_health_history(agent_id, days=days)
        return {"health_history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/costs")
async def get_cost_analytics(
    agent_id: str,
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """Get cost analytics"""
    try:
        analytics = agent_monitoring_svc.get_agent_cost_analytics(agent_id, days=days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/errors")
async def get_error_analytics(
    agent_id: str,
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """Get error analytics"""
    try:
        analytics = agent_monitoring_svc.get_error_analytics(agent_id, days=days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/stats")
async def get_agent_stats(agent_id: str) -> Dict[str, Any]:
    """Get comprehensive agent statistics"""
    try:
        stats = agent_marketplace_svc.get_agent_stats(agent_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ HEALTH CHECK ============

@router.get("/health/status")
async def agents_health_status() -> Dict[str, Any]:
    """Agent module health check"""
    return {
        "status": "healthy",
        "module": "agents",
        "timestamp": datetime.utcnow().isoformat()
    }
