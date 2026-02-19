"""Agent schemas."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict

from app.models.agent import AgentStatus, AgentType


class AgentBase(BaseModel):
    """Base agent schema."""

    name: str
    agent_type: AgentType
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None


class AgentCreate(AgentBase):
    """Agent creation schema."""

    pass


class AgentUpdate(BaseModel):
    """Agent update schema."""

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AgentStatus] = None
    configuration: Optional[Dict[str, Any]] = None


class AgentResponse(AgentBase):
    """Agent response schema."""

    id: int
    status: AgentStatus
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AgentTaskCreate(BaseModel):
    """Agent task creation schema."""

    agent_id: int
    task_name: str
    input_data: Optional[Dict[str, Any]] = None


class AgentTaskResponse(BaseModel):
    """Agent task response schema."""

    id: int
    agent_id: int
    task_name: str
    status: AgentStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
