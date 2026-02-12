"""Agent endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.agent import Agent, AgentTask
from app.schemas.agent import (
    AgentCreate,
    AgentResponse,
    AgentUpdate,
    AgentTaskCreate,
    AgentTaskResponse,
)

router = APIRouter()


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent_data: AgentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new agent."""
    new_agent = Agent(**agent_data.model_dump())
    db.add(new_agent)
    await db.commit()
    await db.refresh(new_agent)
    return new_agent


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all agents."""
    result = await db.execute(select(Agent).offset(skip).limit(limit))
    agents = result.scalars().all()
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    """Get agent by ID."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    # Update fields
    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    await db.commit()
    await db.refresh(agent)
    return agent


@router.post("/tasks", response_model=AgentTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_task(
    task_data: AgentTaskCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create and execute an agent task."""
    # Verify agent exists
    result = await db.execute(select(Agent).where(Agent.id == task_data.agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    # Create task
    new_task = AgentTask(**task_data.model_dump())
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task


@router.get("/tasks/{task_id}", response_model=AgentTaskResponse)
async def get_agent_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get agent task by ID."""
    result = await db.execute(select(AgentTask).where(AgentTask.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task
