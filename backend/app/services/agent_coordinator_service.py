"""
Agent Coordinator Service for OmniDev AI
Manages multi-agent collaboration, task delegation, and resource allocation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
import json


class AgentStatus(str, Enum):
    """Agent operational states"""
    IDLE = "idle"
    BUSY = "busy"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class AgentCapability(str, Enum):
    """Agent skill classifications"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DEBUGGING = "debugging"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    DEVOPS = "devops"
    INTEGRATION = "integration"


class CollaborationType(str, Enum):
    """Types of agent collaboration"""
    SEQUENTIAL = "sequential"  # One after another
    PARALLEL = "parallel"  # Multiple simultaneously
    HIERARCHICAL = "hierarchical"  # Leader-follower model
    CONSENSUS = "consensus"  # Group decision making
    RELAY = "relay"  # Pass results along


@dataclass
class AgentMetrics:
    """Performance metrics for an agent"""
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    avg_task_duration_seconds: float = 0.0
    current_queue_size: int = 0
    success_rate: float = 100.0
    avg_cpu_usage: float = 0.0
    avg_memory_usage: float = 0.0
    last_activity: Optional[datetime] = None
    uptime_seconds: float = 0.0
    error_count_last_hour: int = 0


@dataclass
class Agent:
    """Agent entity for orchestration"""
    id: str
    name: str
    agent_type: str
    status: AgentStatus = AgentStatus.IDLE
    capabilities: List[AgentCapability] = field(default_factory=list)
    max_concurrent_tasks: int = 3
    current_task_count: int = 0
    current_tasks: List[str] = field(default_factory=list)
    available_memory_mb: int = 2048
    max_memory_mb: int = 4096
    api_endpoint: str = ""
    webhooks: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: Optional[datetime] = None
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    metadata: Dict = field(default_factory=dict)
    preferred_collaboration_type: CollaborationType = CollaborationType.SEQUENTIAL


@dataclass
class Collaboration:
    """Multi-agent collaboration session"""
    id: str
    name: str
    description: str
    agent_ids: List[str] = field(default_factory=list)
    task_id: str = ""
    collaboration_type: CollaborationType = CollaborationType.SEQUENTIAL
    status: str = "active"  # active, completed, failed, paused
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    metadata: Dict = field(default_factory=dict)


class AgentCoordinatorService:
    """Service for coordinating multi-agent operations"""

    def __init__(self):
        """Initialize agent coordinator"""
        self.agents: Dict[str, Agent] = {}
        self.collaborations: Dict[str, Collaboration] = {}
        self.agent_specializations: Dict[str, List[str]] = {}  # capability -> [agent_ids]
        self.collaboration_history: List[str] = []
        self.agent_communication: Dict[str, List[Dict]] = {}  # agent_id -> messages

    def register_agent(
        self,
        name: str,
        agent_type: str,
        capabilities: List[AgentCapability],
        max_concurrent_tasks: int = 3,
        available_memory_mb: int = 2048,
        api_endpoint: str = "",
        metadata: Optional[Dict] = None,
    ) -> Agent:
        """
        Register a new agent in the system
        
        Args:
            name: Agent display name
            agent_type: Type of agent (code_agent, devops_agent, etc.)
            capabilities: List of agent capabilities
            max_concurrent_tasks: Max parallel tasks
            available_memory_mb: Available memory
            api_endpoint: Agent API URL
            metadata: Additional metadata
            
        Returns:
            Registered Agent object
        """
        agent_id = str(uuid4())
        
        agent = Agent(
            id=agent_id,
            name=name,
            agent_type=agent_type,
            capabilities=capabilities,
            max_concurrent_tasks=max_concurrent_tasks,
            available_memory_mb=available_memory_mb,
            api_endpoint=api_endpoint,
            metadata=metadata or {},
        )
        
        self.agents[agent_id] = agent
        self.agent_communication[agent_id] = []
        
        # Index by capability
        for cap in capabilities:
            cap_str = cap.value if isinstance(cap, AgentCapability) else str(cap)
            if cap_str not in self.agent_specializations:
                self.agent_specializations[cap_str] = []
            self.agent_specializations[cap_str].append(agent_id)
        
        return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status"""
        agent = self.agents.get(agent_id)
        if agent:
            agent.status = status
            agent.last_heartbeat = datetime.utcnow()
            return True
        return False

    def find_agents_by_capability(self, capability: AgentCapability) -> List[Agent]:
        """Find all agents with a specific capability"""
        cap_str = capability.value if isinstance(capability, AgentCapability) else str(capability)
        agent_ids = self.agent_specializations.get(cap_str, [])
        agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]
        
        # Sort by: availability, then success rate, then recent activity
        return sorted(
            agents,
            key=lambda a: (
                -int(a.status == AgentStatus.IDLE),  # Idle first
                -a.metrics.success_rate,  # Higher success rate
                -(a.last_heartbeat or datetime.min).timestamp(),  # Recent activity
            ),
        )

    def find_best_agent_for_task(
        self,
        task_type: str,
        required_capability: Optional[AgentCapability] = None,
        memory_required_mb: int = 512,
    ) -> Optional[Agent]:
        """
        Find the best available agent for a task
        
        Args:
            task_type: Type of task
            required_capability: Required capability
            memory_required_mb: Memory requirements
            
        Returns:
            Best available Agent or None
        """
        candidates = []
        
        # Filter by capability
        if required_capability:
            candidates = self.find_agents_by_capability(required_capability)
        else:
            candidates = list(self.agents.values())
        
        # Filter by availability
        available = [
            a for a in candidates
            if (a.status != AgentStatus.OFFLINE
                and a.current_task_count < a.max_concurrent_tasks
                and a.available_memory_mb >= memory_required_mb)
        ]
        
        if not available:
            return None
        
        # Sort by: load, success rate, memory available
        return sorted(
            available,
            key=lambda a: (
                a.current_task_count,
                -a.metrics.success_rate,
                -a.available_memory_mb,
            ),
        )[0]

    def assign_task_to_agent(
        self,
        agent_id: str,
        task_id: str,
        memory_required_mb: int = 512,
    ) -> bool:
        """
        Assign a task to an agent
        
        Args:
            agent_id: Agent ID
            task_id: Task ID
            memory_required_mb: Memory requirements
            
        Returns:
            True if assignment successful
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        
        if agent.current_task_count >= agent.max_concurrent_tasks:
            return False
        
        if agent.available_memory_mb < memory_required_mb:
            return False
        
        agent.current_tasks.append(task_id)
        agent.current_task_count += 1
        agent.available_memory_mb -= memory_required_mb
        agent.status = AgentStatus.BUSY if agent.current_task_count > 0 else AgentStatus.IDLE
        
        return True

    def complete_agent_task(
        self,
        agent_id: str,
        task_id: str,
        memory_freed_mb: int = 512,
        success: bool = True,
    ) -> bool:
        """
        Mark task as complete for agent
        
        Args:
            agent_id: Agent ID
            task_id: Task ID
            memory_freed_mb: Memory to release
            success: Whether task succeeded
            
        Returns:
            True if successful
        """
        agent = self.agents.get(agent_id)
        if not agent or task_id not in agent.current_tasks:
            return False
        
        agent.current_tasks.remove(task_id)
        agent.current_task_count = max(0, agent.current_task_count - 1)
        agent.available_memory_mb = min(
            agent.max_memory_mb,
            agent.available_memory_mb + memory_freed_mb
        )
        
        if success:
            agent.metrics.total_tasks_completed += 1
        else:
            agent.metrics.total_tasks_failed += 1
        
        # Update success rate
        total_tasks = agent.metrics.total_tasks_completed + agent.metrics.total_tasks_failed
        if total_tasks > 0:
            agent.metrics.success_rate = (
                (agent.metrics.total_tasks_completed / total_tasks) * 100
            )
        
        agent.status = AgentStatus.IDLE if agent.current_task_count == 0 else AgentStatus.BUSY
        
        return True

    def create_collaboration(
        self,
        name: str,
        description: str,
        agent_ids: List[str],
        task_id: str = "",
        collaboration_type: CollaborationType = CollaborationType.SEQUENTIAL,
        metadata: Optional[Dict] = None,
    ) -> Optional[Collaboration]:
        """
        Create a multi-agent collaboration
        
        Args:
            name: Collaboration name
            description: Collaboration description
            agent_ids: List of agent IDs
            task_id: Associated task ID
            collaboration_type: How agents collaborate
            metadata: Additional metadata
            
        Returns:
            Collaboration object
        """
        # Validate agents exist
        for agent_id in agent_ids:
            if agent_id not in self.agents:
                return None
        
        collab_id = str(uuid4())
        
        collaboration = Collaboration(
            id=collab_id,
            name=name,
            description=description,
            agent_ids=agent_ids,
            task_id=task_id,
            collaboration_type=collaboration_type,
            metadata=metadata or {},
        )
        
        self.collaborations[collab_id] = collaboration
        return collaboration

    def get_collaboration(self, collab_id: str) -> Optional[Collaboration]:
        """Get collaboration by ID"""
        return self.collaborations.get(collab_id)

    def complete_collaboration(
        self,
        collab_id: str,
        result: Optional[Dict] = None,
    ) -> bool:
        """Mark collaboration as completed"""
        collab = self.collaborations.get(collab_id)
        if collab:
            collab.status = "completed"
            collab.completed_at = datetime.utcnow()
            collab.result = result
            self.collaboration_history.append(collab_id)
            return True
        return False

    def fail_collaboration(self, collab_id: str, error: str = "") -> bool:
        """Mark collaboration as failed"""
        collab = self.collaborations.get(collab_id)
        if collab:
            collab.status = "failed"
            collab.completed_at = datetime.utcnow()
            if collab.metadata is None:
                collab.metadata = {}
            collab.metadata["error"] = error
            self.collaboration_history.append(collab_id)
            return True
        return False

    def send_message(
        self,
        from_agent_id: str,
        to_agent_id: str,
        message_type: str,
        content: Dict,
    ) -> bool:
        """
        Send inter-agent message for collaboration
        
        Args:
            from_agent_id: Sender agent
            to_agent_id: Recipient agent
            message_type: Message type
            content: Message content
            
        Returns:
            True if sent successfully
        """
        if from_agent_id not in self.agents or to_agent_id not in self.agents:
            return False
        
        message = {
            "from_agent_id": from_agent_id,
            "to_agent_id": to_agent_id,
            "message_type": message_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if to_agent_id not in self.agent_communication:
            self.agent_communication[to_agent_id] = []
        
        self.agent_communication[to_agent_id].append(message)
        return True

    def get_messages_for_agent(self, agent_id: str) -> List[Dict]:
        """Get pending messages for agent"""
        return self.agent_communication.get(agent_id, [])

    def clear_agent_messages(self, agent_id: str) -> int:
        """Clear messages for agent and return count"""
        if agent_id in self.agent_communication:
            count = len(self.agent_communication[agent_id])
            self.agent_communication[agent_id] = []
            return count
        return 0

    def allocate_resources(
        self,
        agent_id: str,
        memory_mb: int = 0,
        cpu_percent: float = 0.0,
    ) -> bool:
        """
        Allocate additional resources to agent
        
        Args:
            agent_id: Agent ID
            memory_mb: Additional memory
            cpu_percent: Additional CPU percentage
            
        Returns:
            True if successful
        """
        agent = self.agents.get(agent_id)
        if agent:
            agent.available_memory_mb = min(
                agent.max_memory_mb,
                agent.available_memory_mb + memory_mb
            )
            if agent.metadata is None:
                agent.metadata = {}
            agent.metadata["allocated_cpu_percent"] = cpu_percent
            return True
        return False

    def get_agent_load(self, agent_id: str) -> Optional[float]:
        """Get agent load percentage (0-100)"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        # Calculate based on tasks and memory usage
        task_load = (agent.current_task_count / agent.max_concurrent_tasks) * 100
        memory_load = ((agent.max_memory_mb - agent.available_memory_mb) / agent.max_memory_mb) * 100
        
        return (task_load + memory_load) / 2

    def get_least_loaded_agent(
        self,
        agent_ids: Optional[List[str]] = None,
    ) -> Optional[Agent]:
        """Get least loaded agent from list"""
        agents = [self.agents[aid] for aid in (agent_ids or self.agents.keys()) if aid in self.agents]
        
        if not agents:
            return None
        
        loads = [(agent, self.get_agent_load(agent.id)) for agent in agents]
        loads = [(agent, load) for agent, load in loads if load is not None]
        
        if not loads:
            return None
        
        return min(loads, key=lambda x: x[1])[0]

    def get_system_health(self) -> Dict:
        """Get overall system health metrics"""
        if not self.agents:
            return {
                "total_agents": 0,
                "active_agents": 0,
                "offline_agents": 0,
                "avg_success_rate": 0.0,
                "total_load_percent": 0.0,
                "memory_usage_percent": 0.0,
            }
        
        agents = list(self.agents.values())
        active_agents = [a for a in agents if a.status != AgentStatus.OFFLINE]
        offline_agents = [a for a in agents if a.status == AgentStatus.OFFLINE]
        
        success_rates = [a.metrics.success_rate for a in agents]
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        
        loads = [self.get_agent_load(a.id) for a in agents]
        loads = [l for l in loads if l is not None]
        avg_load = sum(loads) / len(loads) if loads else 0
        
        total_max_memory = sum(a.max_memory_mb for a in agents)
        used_memory = sum(a.max_memory_mb - a.available_memory_mb for a in agents)
        memory_usage = (used_memory / total_max_memory * 100) if total_max_memory > 0 else 0
        
        return {
            "total_agents": len(agents),
            "active_agents": len(active_agents),
            "offline_agents": len(offline_agents),
            "total_tasks_running": sum(a.current_task_count for a in agents),
            "avg_success_rate": round(avg_success_rate, 2),
            "total_load_percent": round(avg_load, 2),
            "memory_usage_percent": round(memory_usage, 2),
            "collaborations_active": len([c for c in self.collaborations.values() if c.status == "active"]),
        }

    def get_agent_stats(self, agent_id: str) -> Optional[Dict]:
        """Get detailed stats for an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        return {
            "id": agent.id,
            "name": agent.name,
            "type": agent.agent_type,
            "status": agent.status.value,
            "capabilities": [c.value for c in agent.capabilities],
            "load_percent": self.get_agent_load(agent.id),
            "current_tasks": len(agent.current_tasks),
            "max_concurrent_tasks": agent.max_concurrent_tasks,
            "memory_available_mb": agent.available_memory_mb,
            "memory_max_mb": agent.max_memory_mb,
            "metrics": asdict(agent.metrics),
            "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
            "created_at": agent.created_at.isoformat(),
        }

    def get_all_agents_stats(self) -> Dict:
        """Get stats for all agents"""
        return {
            agent_id: self.get_agent_stats(agent_id)
            for agent_id in self.agents
        }

    def cleanup_offline_agents(self, offline_threshold_minutes: int = 5) -> List[str]:
        """Remove agents offline longer than threshold"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=offline_threshold_minutes)
        removed = []
        
        for agent_id, agent in list(self.agents.items()):
            if (agent.status == AgentStatus.OFFLINE
                and agent.last_heartbeat
                and agent.last_heartbeat < cutoff_time):
                del self.agents[agent_id]
                removed.append(agent_id)
        
        return removed
