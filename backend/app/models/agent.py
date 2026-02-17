"""Agent model."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


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
    CODE_REVIEWER = "code_reviewer"
    DOCUMENTATION = "documentation"
    DEBUGGER = "debugger"
    REFACTORER = "refactorer"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DEPLOYER = "deployer"
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
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    last_run = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    tasks = relationship("AgentTask", back_populates="agent", cascade="all, delete-orphan")


class AgentTask(Base):
    """Agent task execution model."""

    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), index=True, nullable=False)
    task_name = Column(String, nullable=False)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.IDLE)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="tasks")
