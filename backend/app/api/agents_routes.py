"""
Agent management and execution endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
from datetime import datetime
from app.database.config import get_db
from app.database.models import User
from app.auth.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentResponse(BaseModel):
    id: str
    name: str
    type: str
    description: str
    status: str
    
    class Config:
        from_attributes = True


class ExecutionRequest(BaseModel):
    agent_type: str  # 'planner', 'code', 'web', 'devops'
    input_data: dict
    project_id: str


@router.get("", response_model=List[AgentResponse])
async def list_agents(current_user: User = Depends(get_current_user)):
    """List all available AI agents"""
    agents = [
        {
            "id": "agent-planner",
            "name": "Planner Agent",
            "type": "planner",
            "description": "Analyzes tasks and creates execution plans",
            "status": "idle"
        },
        {
            "id": "agent-code",
            "name": "Code Agent",
            "type": "code",
            "description": "Generates and reviews code",
            "status": "idle"
        },
        {
            "id": "agent-web",
            "name": "Web Agent",
            "type": "web",
            "description": "Scrapes and analyzes web content",
            "status": "idle"
        },
        {
            "id": "agent-devops",
            "name": "DevOps Agent",
            "type": "devops",
            "description": "Manages deployments and infrastructure",
            "status": "idle"
        }
    ]
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, current_user: User = Depends(get_current_user)):
    """Get agent details"""
    agents_map = {
        "agent-planner": {
            "id": "agent-planner",
            "name": "Planner Agent",
            "type": "planner",
            "description": "Analyzes tasks and creates execution plans",
            "status": "idle"
        },
        "agent-code": {
            "id": "agent-code",
            "name": "Code Agent",
            "type": "code",
            "description": "Generates and reviews code",
            "status": "idle"
        },
        "agent-web": {
            "id": "agent-web",
            "name": "Web Agent",
            "type": "web",
            "description": "Scrapes and analyzes web content",
            "status": "idle"
        },
        "agent-devops": {
            "id": "agent-devops",
            "name": "DevOps Agent",
            "type": "devops",
            "description": "Manages deployments and infrastructure",
            "status": "idle"
        }
    }
    
    if agent_id not in agents_map:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agents_map[agent_id]


@router.post("/{agent_id}/execute")
async def execute_agent(
    agent_id: str,
    execution_data: ExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute an agent"""
    # Verify agent exists
    valid_agents = ["agent-planner", "agent-code", "agent-web", "agent-devops"]
    if agent_id not in valid_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Create execution record
    execution_id = str(uuid4())
    
    # For now, return immediate response
    # In production, this would queue the job in Celery
    return {
        "execution_id": execution_id,
        "agent_id": agent_id,
        "status": "queued",
        "created_at": datetime.utcnow(),
        "message": f"Agent execution queued. Execution ID: {execution_id}"
    }


@router.get("/{agent_id}/executions")
async def list_agent_executions(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List executions for an agent"""
    return {
        "agent_id": agent_id,
        "executions": [],
        "total": 0
    }


@router.get("/executions/{execution_id}")
async def get_execution_status(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get execution status"""
    return {
        "execution_id": execution_id,
        "status": "completed",
        "progress": 100,
        "result": {
            "success": True,
            "output": "Execution completed successfully"
        }
    }
