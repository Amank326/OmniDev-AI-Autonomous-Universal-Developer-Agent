"""
Phase 10: Workflow & Automation Models
Advanced automation system for OmniDev AI
Database models for workflows, rules, schedules, and analytics
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text, ForeignKey, Index, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import json
from enum import Enum as PyEnum

Base = declarative_base()


class WorkflowStatus(PyEnum):
    """Workflow execution status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


class ExecutionStatus(PyEnum):
    """Execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class NodeType(PyEnum):
    """Workflow node types"""
    START = "start"
    ACTION = "action"
    DECISION = "decision"
    PARALLEL = "parallel"
    WAIT = "wait"
    END = "end"


class TriggerType(PyEnum):
    """Automation rule trigger types"""
    EVENT = "event"
    TIME = "time"
    CONDITION = "condition"
    DATA = "data"
    WEBHOOK = "webhook"
    MANUAL = "manual"


class Workflow(Base):
    """Workflow definitions and metadata"""
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(36), nullable=False)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT)
    version = Column(Integer, default=1)
    
    # DAG structure
    nodes_count = Column(Integer, default=0)
    edges_count = Column(Integer, default=0)
    
    # Configuration
    config = Column(JSON, nullable=True)  # Workflow-level settings
    variables = Column(JSON, default={})  # Global variables
    
    # Execution stats
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    avg_execution_time = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_executed_at = Column(DateTime, nullable=True)
    
    # Relationships
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_workflow_user_id", "user_id"),
        Index("idx_workflow_status", "status"),
        Index("idx_workflow_created_at", "created_at"),
        Index("idx_workflow_user_status", "user_id", "status"),
    )


class WorkflowNode(Base):
    """Individual workflow steps/nodes"""
    __tablename__ = "workflow_nodes"

    id = Column(String(36), primary_key=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    node_type = Column(Enum(NodeType), nullable=False)
    action_type = Column(String(100), nullable=True)  # e.g., "send_email", "create_record"
    
    # Position for visual editor
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    
    # Configuration
    config = Column(JSON, nullable=True)  # Action-specific config
    input_mapping = Column(JSON, default={})  # Map previous outputs to inputs
    output_mapping = Column(JSON, default={})  # Define node outputs
    
    # Conditional execution
    condition = Column(Text, nullable=True)  # Python expression for branching
    
    # Error handling
    retry_count = Column(Integer, default=0)
    retry_delay = Column(Integer, default=60)  # seconds
    timeout = Column(Integer, default=300)  # seconds
    on_error = Column(String(50), default="fail")  # "fail", "retry", "skip", "continue"
    
    # Relationships
    workflow = relationship("Workflow", back_populates="nodes")
    outgoing_edges = relationship("WorkflowEdge", foreign_keys="WorkflowEdge.source_id", back_populates="source_node")
    incoming_edges = relationship("WorkflowEdge", foreign_keys="WorkflowEdge.target_id", back_populates="target_node")

    __table_args__ = (
        Index("idx_node_workflow_id", "workflow_id"),
        Index("idx_node_type", "node_type"),
        Index("idx_node_action", "action_type"),
    )


class WorkflowEdge(Base):
    """Connections between workflow nodes"""
    __tablename__ = "workflow_edges"

    id = Column(String(36), primary_key=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    source_id = Column(String(36), ForeignKey("workflow_nodes.id"), nullable=False)
    target_id = Column(String(36), ForeignKey("workflow_nodes.id"), nullable=False)
    
    # Edge metadata
    label = Column(String(255), nullable=True)  # e.g., "on success", "on failure"
    condition = Column(Text, nullable=True)  # Conditional edge expression
    
    # Relationships
    workflow = relationship("Workflow", back_populates="edges")
    source_node = relationship("WorkflowNode", foreign_keys=[source_id], back_populates="outgoing_edges")
    target_node = relationship("WorkflowNode", foreign_keys=[target_id], back_populates="incoming_edges")

    __table_args__ = (
        Index("idx_edge_workflow_id", "workflow_id"),
        Index("idx_edge_source_target", "source_id", "target_id"),
    )


class WorkflowExecution(Base):
    """Execution history and logs"""
    __tablename__ = "workflow_executions"

    id = Column(String(36), primary_key=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    trigger_type = Column(Enum(TriggerType), nullable=True)
    
    # Execution context
    input_data = Column(JSON, default={})
    variables = Column(JSON, default={})  # Runtime variables
    output_data = Column(JSON, default={})
    
    # Performance metrics
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)  # seconds
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_node_id = Column(String(36), nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Retry info
    retry_count = Column(Integer, default=0)
    parent_execution_id = Column(String(36), nullable=True)  # Parent for retry chains
    
    # Audit
    executed_by = Column(String(36), nullable=True)  # User ID or system
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    node_executions = relationship("NodeExecution", back_populates="execution", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_execution_workflow_id", "workflow_id"),
        Index("idx_execution_status", "status"),
        Index("idx_execution_created_at", "created_at"),
        Index("idx_execution_workflow_status", "workflow_id", "status"),
    )


class NodeExecution(Base):
    """Per-node execution tracking"""
    __tablename__ = "node_executions"

    id = Column(String(36), primary_key=True)
    execution_id = Column(String(36), ForeignKey("workflow_executions.id"), nullable=False)
    node_id = Column(String(36), nullable=False)
    
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    input_data = Column(JSON, default={})
    output_data = Column(JSON, default={})
    
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)
    
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    execution = relationship("WorkflowExecution", back_populates="node_executions")

    __table_args__ = (
        Index("idx_node_exec_execution_id", "execution_id"),
        Index("idx_node_exec_node_id", "node_id"),
    )


class AutomationRule(Base):
    """Trigger-based automation rules"""
    __tablename__ = "automation_rules"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(36), nullable=False)
    
    is_enabled = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    
    # Rule definition
    trigger_type = Column(Enum(TriggerType), nullable=False)
    trigger_config = Column(JSON, nullable=False)  # Trigger-specific config
    
    # Conditions
    conditions = Column(JSON, default=[])  # Array of condition objects
    condition_logic = Column(String(20), default="AND")  # "AND" or "OR"
    
    # Actions (can trigger workflow or execute directly)
    actions = Column(JSON, default=[])  # Array of action configs
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=True)
    
    # Execution limits
    max_executions_per_day = Column(Integer, nullable=True)
    max_concurrent = Column(Integer, default=1)
    execution_count_today = Column(Integer, default=0)
    
    # Stats
    total_triggers = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    last_triggered_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_rule_user_id", "user_id"),
        Index("idx_rule_enabled", "is_enabled"),
        Index("idx_rule_trigger_type", "trigger_type"),
        Index("idx_rule_user_enabled", "user_id", "is_enabled"),
    )


class ScheduledTask(Base):
    """Cron-based scheduled task execution"""
    __tablename__ = "scheduled_tasks"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(36), nullable=False)
    
    is_enabled = Column(Boolean, default=True)
    
    # Schedule definition
    cron_expression = Column(String(100), nullable=False)  # Cron format
    timezone = Column(String(50), default="UTC")
    next_execution = Column(DateTime, nullable=True)
    last_execution = Column(DateTime, nullable=True)
    
    # Task details
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=True)
    task_config = Column(JSON, nullable=True)
    
    # Execution tracking
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    avg_execution_time = Column(Float, default=0.0)
    
    # Retry policy
    max_retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=300)  # seconds
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_task_user_id", "user_id"),
        Index("idx_task_enabled", "is_enabled"),
        Index("idx_task_next_execution", "next_execution"),
        Index("idx_task_user_enabled", "user_id", "is_enabled"),
    )


class ActionLibrary(Base):
    """Available actions catalog"""
    __tablename__ = "action_library"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), unique=True, nullable=False)  # e.g., "send_email"
    display_name = Column(String(255), nullable=False)  # Human-readable name
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # "communication", "data", "workflow", etc
    
    # Implementation
    handler_module = Column(String(255), nullable=False)  # Python module path
    is_builtin = Column(Boolean, default=True)
    is_enabled = Column(Boolean, default=True)
    
    # Configuration schema
    required_params = Column(JSON, default=[])  # Required parameter names
    optional_params = Column(JSON, default=[])  # Optional parameter names
    input_schema = Column(JSON, nullable=True)  # JSON Schema for inputs
    output_schema = Column(JSON, nullable=True)  # JSON Schema for outputs
    
    # Documentation
    documentation = Column(Text, nullable=True)
    example_config = Column(JSON, nullable=True)
    
    # Stats
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_execution_time = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_action_name", "name"),
        Index("idx_action_category", "category"),
        Index("idx_action_enabled", "is_enabled"),
    )


class WorkflowAnalytics(Base):
    """Aggregated workflow performance metrics"""
    __tablename__ = "workflow_analytics"

    id = Column(String(36), primary_key=True)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    
    # Time window
    date = Column(DateTime, nullable=False)  # Day granularity
    
    # Execution metrics
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    timeout_executions = Column(Integer, default=0)
    
    # Performance
    avg_execution_time = Column(Float, default=0.0)
    min_execution_time = Column(Float, default=0.0)
    max_execution_time = Column(Float, default=0.0)
    
    # Per-node metrics
    node_metrics = Column(JSON, default={})  # {node_id: {executions, avg_time, errors}}
    
    # Errors
    error_count = Column(Integer, default=0)
    error_types = Column(JSON, default={})  # {error_type: count}
    
    # Resource usage
    total_cpu_time = Column(Float, default=0.0)
    total_memory_bytes = Column(Integer, default=0)
    
    # Cost estimation
    estimated_cost = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_analytics_workflow_id", "workflow_id"),
        Index("idx_analytics_date", "date"),
        Index("idx_analytics_workflow_date", "workflow_id", "date"),
    )
