"""Agent model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, JSON, Text
import enum

from app.core.database import Base


class AgentStatus(str, enum.Enum):
    """Agent execution status."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(str, enum.Enum):
    """Types of AI agents."""

    CODE_ANALYZER = "code_analyzer"
    CODE_GENERATOR = "code_generator"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    CUSTOM = "custom"


class Agent(Base):
    """AI Agent model."""

    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    agent_type = Column(SQLEnum(AgentType), nullable=False)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.IDLE)
    description = Column(Text, nullable=True)
    configuration = Column(JSON, nullable=True)
    capabilities = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run = Column(DateTime, nullable=True)


class AgentTask(Base):
    """Agent task execution model."""

    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, index=True, nullable=False)
    task_name = Column(String, nullable=False)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.IDLE)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
