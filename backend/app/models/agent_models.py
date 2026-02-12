"""
Phase 15: AI Agent Marketplace Models
- AIAgent: Autonomous agent definitions
- AgentCapability: Supported operations
- AgentCredential: Security & API keys
- AgentPerformance: Metrics and stats
- AgentExecution: Execution history and logs
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database.config import Base
from datetime import datetime
import enum


class AIAgent(Base):
    __tablename__ = "ai_agents"
    
    id = Column(String(50), primary_key=True)
    author_id = Column(String(50), ForeignKey("template_authors.id"))
    
    # Basic Info
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True)
    description = Column(Text, nullable=False)
    full_description = Column(Text)
    icon_url = Column(String(500))
    
    # Agent Type & Capabilities
    agent_type = Column(String(50))  # assistant, analyst, developer, orchestrator, custom
    version = Column(String(50), default="1.0.0")
    latest_version = Column(String(50), default="1.0.0")
    
    # AI Model Configuration
    model_provider = Column(String(50))  # openai, anthropic, local, custom
    model_name = Column(String(100))  # gpt-4, claude-3, etc.
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)
    system_prompt = Column(Text)
    
    # Capabilities
    capabilities = Column(JSON, default=list)  # ["code_generation", "analysis", "planning"]
    supported_integrations = Column(JSON, default=list)  # ["slack", "email", "github"]
    required_permissions = Column(JSON, default=list)
    
    # Agent Behavior
    is_autonomous = Column(Boolean, default=False)  # Can act independently
    can_make_decisions = Column(Boolean, default=False)
    can_execute_code = Column(Boolean, default=False)
    can_access_external_apis = Column(Boolean, default=False)
    requires_human_approval = Column(Boolean, default=True)
    
    # Tags & Metadata
    tags = Column(JSON, default=list)
    category = Column(String(50))  # coding, analysis, automation, content, research
    industry_tags = Column(JSON, default=list)  # fintech, healthcare, marketing
    
    # Stats
    downloads = Column(Integer, default=0)
    deployments = Column(Integer, default=0)
    executions = Column(Integer, default=0)
    rating_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    
    # Performance
    average_execution_time = Column(Float, default=0.0)  # seconds
    success_rate = Column(Float, default=0.0)  # percentage
    error_rate = Column(Float, default=0.0)  # percentage
    
    # Visibility & Status
    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Monetization
    is_paid = Column(Boolean, default=False)
    price = Column(Float, default=0.0)
    revenue_share_percent = Column(Float, default=50.0)
    
    # Cost Configuration
    base_cost_per_execution = Column(Float, default=0.0)
    token_cost_per_1k = Column(Float, default=0.0)  # For LLM tokens
    
    # Documentation
    documentation_url = Column(String(500))
    example_prompts = Column(JSON, default=list)  # ["Analyze this code", "Generate documentation"]
    quickstart_guide = Column(Text)
    
    # Licensing
    license_type = Column(String(50), default="MIT")
    source_code_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    
    author = relationship("TemplateAuthor", foreign_keys=[author_id])
    capabilities_rel = relationship("AgentCapability", back_populates="agent", cascade="all, delete-orphan")
    credentials = relationship("AgentCredential", back_populates="agent", cascade="all, delete-orphan")
    performance = relationship("AgentPerformance", back_populates="agent", cascade="all, delete-orphan")
    executions = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan")
    ratings = relationship("AgentRating", back_populates="agent", cascade="all, delete-orphan")
    deployments = relationship("AgentDeployment", back_populates="agent", cascade="all, delete-orphan")


class AgentCapability(Base):
    __tablename__ = "agent_capabilities"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    
    # Capability Definition
    name = Column(String(100), nullable=False)
    slug = Column(String(100))
    description = Column(Text)
    
    # Capability Type
    capability_type = Column(String(50))  # action, analysis, generation, decision, integration
    
    # Input/Output Schema
    input_schema = Column(JSON)  # {properties: {}, required: []}
    output_schema = Column(JSON)
    
    # Configuration
    requires_api_key = Column(Boolean, default=False)
    api_provider = Column(String(50))  # github, slack, email, etc.
    
    # Performance
    average_execution_time = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("AIAgent", back_populates="capabilities_rel")


class AgentCredential(Base):
    __tablename__ = "agent_credentials"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    user_id = Column(String(50), nullable=False)  # Credential owner
    
    # Credential Info
    credential_type = Column(String(50))  # api_key, oauth, basic_auth, token
    provider = Column(String(50))  # github, openai, slack, email
    
    # Encrypted Values
    credential_value = Column(Text, nullable=False)  # Encrypted
    refresh_token = Column(Text)  # For OAuth
    
    # Metadata
    scope = Column(JSON, default=list)  # Permissions/scopes
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Usage
    last_used_at = Column(DateTime)
    usage_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    agent = relationship("AIAgent", back_populates="credentials")


class AgentPerformance(Base):
    __tablename__ = "agent_performance"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    
    # Time Period
    metric_date = Column(String(10))  # YYYY-MM-DD
    metric_hour = Column(Integer)  # 0-23, optional for hourly metrics
    
    # Execution Metrics
    execution_count = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    
    # Timing
    total_execution_time = Column(Float, default=0.0)  # seconds
    average_execution_time = Column(Float, default=0.0)
    min_execution_time = Column(Float, default=0.0)
    max_execution_time = Column(Float, default=0.0)
    
    # Tokens (for LLM-based agents)
    input_tokens_used = Column(Integer, default=0)
    output_tokens_used = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    
    # Cost
    estimated_cost = Column(Float, default=0.0)
    
    # Quality
    success_rate = Column(Float, default=0.0)  # percentage
    error_rate = Column(Float, default=0.0)
    average_rating = Column(Float, default=0.0)  # from user feedback
    
    # Users
    unique_users = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("AIAgent", back_populates="performance")


class AgentExecution(Base):
    __tablename__ = "agent_executions"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    user_id = Column(String(50), nullable=False)
    deployment_id = Column(String(50), ForeignKey("agent_deployments.id"))
    
    # Execution Request
    prompt = Column(Text, nullable=False)  # User query/request
    execution_type = Column(String(50))  # direct, scheduled, triggered, chained
    
    # Execution Details
    status = Column(String(50), default="pending")  # pending, running, completed, failed, timeout
    
    # Input/Output
    input_data = Column(JSON)  # Structured input if provided
    output = Column(Text)  # Result/response from agent
    output_data = Column(JSON)  # Structured output if applicable
    
    # Execution Metrics
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_seconds = Column(Float)  # Execution duration
    
    # Tokens & Cost
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    
    # Error Tracking
    error_message = Column(Text)
    error_type = Column(String(100))  # timeout, api_error, validation_error, etc.
    stacktrace = Column(Text)
    
    # Feedback
    user_rating = Column(Integer)  # 1-5 stars
    user_feedback = Column(Text)
    was_useful = Column(Boolean)
    
    # Context
    context_data = Column(JSON, default=dict)  # External context passed to agent
    conversation_id = Column(String(50))  # For multi-turn conversations
    
    # Approval
    required_approval = Column(Boolean, default=False)
    approved_by = Column(String(50))
    approval_timestamp = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("AIAgent", back_populates="executions")


class AgentRating(Base):
    __tablename__ = "agent_ratings"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    user_id = Column(String(50), nullable=False)
    
    # Rating
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review_title = Column(String(200))
    review_text = Column(Text)
    
    # Quality Dimensions
    usefulness = Column(Integer)  # 1-5
    accuracy = Column(Integer)  # 1-5
    speed = Column(Integer)  # 1-5
    reliability = Column(Integer)  # 1-5
    
    # Useful Signals
    helpful_count = Column(Integer, default=0)
    verified_user = Column(Boolean, default=False)  # User actually used agent
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("AIAgent", back_populates="ratings")


class AgentDeployment(Base):
    __tablename__ = "agent_deployments"
    
    id = Column(String(50), primary_key=True)
    agent_id = Column(String(50), ForeignKey("ai_agents.id"), nullable=False)
    user_id = Column(String(50), nullable=False)
    
    # Deployment Config
    name = Column(String(200), nullable=False)
    version = Column(String(50))
    
    # Environment
    environment = Column(String(50))  # development, staging, production
    
    # Custom Configuration
    custom_system_prompt = Column(Text)  # User-customized system prompt
    custom_parameters = Column(JSON, default=dict)  # {temperature, max_tokens, etc}
    
    # Resources
    allocated_tokens_monthly = Column(Integer)  # Rate limiting
    api_keys_configured = Column(JSON, default=list)  # Which credentials set up
    
    # Endpoints
    webhook_url = Column(String(500))  # Callback for async execution
    callback_url = Column(String(500))  # Notification URL
    
    # Monitoring
    is_active = Column(Boolean, default=True)
    error_alert_threshold = Column(Integer, default=5)  # Alert after N errors
    
    # Usage
    total_executions = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_execution_at = Column(DateTime)
    
    agent = relationship("AIAgent", back_populates="deployments")
