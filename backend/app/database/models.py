"""SQLAlchemy ORM Models"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
import uuid

# Create base class
Base = declarative_base()


class ProjectStatus(str, enum.Enum):
    """Project status enum"""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    ARCHIVED = "archived"


class TaskStatus(str, enum.Enum):
    """Task status enum"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, enum.Enum):
    """Agent type enum"""
    PLANNER = "planner"
    CODE = "code"
    WEB = "web"
    DEVOPS = "devops"


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="assigned_to", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="created_by", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class Project(Base):
    """Project model"""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    project_type = Column(String(100), nullable=False)  # web, mobile, api, automation, etc.
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PLANNING, index=True)
    tech_stack = Column(JSON, nullable=True)  # List of technologies
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="assigned_project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.title}>"


class Task(Base):
    """Task model"""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high, 4=critical
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    assigned_to_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    agent_type = Column(Enum(AgentType), nullable=True)  # Which agent handles this
    
    # Task execution data
    context = Column(JSON, nullable=True)  # Task context/configuration
    result = Column(JSON, nullable=True)  # Task result/output
    error = Column(Text, nullable=True)  # Error message if failed
    progress = Column(Float, default=0.0)  # Progress percentage (0-100)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    assigned_to = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.title}>"


class Agent(Base):
    """Agent model - tracks agent activity"""
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)  # PlannerAgent, CodeAgent, etc.
    agent_type = Column(Enum(AgentType), nullable=False, index=True)
    status = Column(String(50), default="idle", index=True)  # idle, busy, error
    assigned_project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    
    # Statistics
    tasks_processed = Column(Integer, default=0)
    files_generated = Column(Integer, default=0)
    components_created = Column(Integer, default=0)
    deployments = Column(Integer, default=0)
    success_rate = Column(Float, default=100.0)
    
    # Last activity
    last_activity = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_project = relationship("Project", back_populates="agents")

    def __repr__(self):
        return f"<Agent {self.name}>"


class Memory(Base):
    """Vector Memory model - stores embeddings for semantic search"""
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Memory content
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # Vector embedding for semantic search
    meta_info = Column(JSON, nullable=True)  # Additional metadata
    
    # Classification
    memory_type = Column(String(100), nullable=True)  # code, design, deployment, etc.
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = relationship("User", back_populates="memories")

    def __repr__(self):
        return f"<Memory {self.memory_type}>"
