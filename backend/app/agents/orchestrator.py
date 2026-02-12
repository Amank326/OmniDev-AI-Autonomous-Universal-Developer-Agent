"""
Multi-Agent Orchestration Service
==================================

Coordinates multiple AI agents for collaborative task execution.
Handles task delegation, execution orchestration, and response synthesis.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session

from app.database.config import SessionLocal
from app.database.models import User, Project, Task
from app.agents.base_agent import BaseAgent
from app.agents.code_agent import CodeAgent
from app.agents.web_agent import WebAgent
from app.agents.devops_agent import DevOpsAgent
from app.analytics import analytics_service, ActivityType

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Roles agents can play in collaboration."""
    COORDINATOR = "coordinator"  # Directs team efforts
    EXECUTOR = "executor"  # Executes tasks
    VALIDATOR = "validator"  # Validates solutions
    REVIEWER = "reviewer"  # Reviews code/output
    ASSISTANT = "assistant"  # Provides support


class CollaborationMode(str, Enum):
    """Types of multi-agent collaboration."""
    SEQUENTIAL = "sequential"  # Agents work in sequence
    PARALLEL = "parallel"  # Agents work simultaneously
    HIERARCHICAL = "hierarchical"  # Team with leader
    CONSENSUS = "consensus"  # Agents vote on solution


@dataclass
class AgentTeamMember:
    """Member of an agent team."""
    agent_id: str
    agent_type: str
    name: str
    role: AgentRole
    capabilities: List[str]
    is_available: bool = True
    success_rate: float = 0.0
    tasks_completed: int = 0


@dataclass
class CollaborationTask:
    """Task for agent collaboration."""
    task_id: str
    description: str
    project_id: Optional[int]
    user_id: int
    mode: CollaborationMode
    team_members: List[str]  # Agent IDs
    priority: str = "normal"
    deadline: Optional[datetime] = None
    context: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.context is None:
            self.context = {}


@dataclass
class AgentResponse:
    """Response from an agent in collaboration."""
    agent_id: str
    agent_type: str
    status: str  # success, error, timeout
    response: str
    reasoning: str = ""
    metadata: Dict[str, Any] = None
    execution_time_ms: float = 0
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AgentOrchestrator:
    """
    Orchestrates multiple AI agents for collaborative execution.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize orchestrator."""
        self.db = db or SessionLocal()
        self.available_agents: Dict[str, BaseAgent] = {}
        self.agent_teams: Dict[str, Dict[str, AgentTeamMember]] = {}
        self.active_tasks: Dict[str, CollaborationTask] = {}
        self.collaboration_history: List[Dict[str, Any]] = []
        
        # Initialize agents
        self._initialize_agents()
    
    # ========================================================================
    # Agent Management
    # ========================================================================
    
    def _initialize_agents(self) -> None:
        """Initialize available agents."""
        try:
            # Initialize different agent types
            self.available_agents["code"] = CodeAgent()
            self.available_agents["web"] = WebAgent()
            self.available_agents["devops"] = DevOpsAgent()
            
            logger.info(f"Initialized {len(self.available_agents)} agents")
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
    
    def register_agent(self, agent_id: str, agent: BaseAgent) -> bool:
        """
        Register an agent for orchestration.
        
        Args:
            agent_id: Unique agent identifier
            agent: Agent instance
        
        Returns:
            True if registered successfully
        """
        try:
            self.available_agents[agent_id] = agent
            logger.info(f"Registered agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {str(e)}")
            return False
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents with capabilities."""
        agents = []
        for agent_id, agent in self.available_agents.items():
            agents.append({
                "agent_id": agent_id,
                "agent_type": type(agent).__name__,
                "name": getattr(agent, "name", agent_id),
                "is_available": True,
            })
        return agents
    
    # ========================================================================
    # Team Management
    # ========================================================================
    
    def create_team(
        self,
        team_id: str,
        agents: List[Tuple[str, AgentRole]],
    ) -> bool:
        """
        Create a team of agents.
        
        Args:
            team_id: Unique team identifier
            agents: List of (agent_id, role) tuples
        
        Returns:
            True if team created successfully
        """
        try:
            team = {}
            for agent_id, role in agents:
                if agent_id not in self.available_agents:
                    logger.warning(f"Agent {agent_id} not available")
                    continue
                
                agent = self.available_agents[agent_id]
                team[agent_id] = AgentTeamMember(
                    agent_id=agent_id,
                    agent_type=type(agent).__name__,
                    name=getattr(agent, "name", agent_id),
                    role=role,
                    capabilities=getattr(agent, "capabilities", []),
                )
            
            self.agent_teams[team_id] = team
            logger.info(f"Created team {team_id} with {len(team)} agents")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create team {team_id}: {str(e)}")
            return False
    
    def get_team(self, team_id: str) -> Optional[Dict[str, AgentTeamMember]]:
        """Get team information."""
        return self.agent_teams.get(team_id)
    
    def get_best_agent_for_task(
        self,
        task_description: str,
        required_capabilities: List[str] = None,
    ) -> Optional[str]:
        """
        Find best agent for a task based on capabilities.
        
        Args:
            task_description: Task description
            required_capabilities: Required capabilities
        
        Returns:
            Best agent ID or None
        """
        if not required_capabilities:
            required_capabilities = []
        
        best_agent = None
        best_score = -1
        
        for agent_id, agent in self.available_agents.items():
            capabilities = getattr(agent, "capabilities", [])
            
            # Score based on capability match
            matches = sum(1 for cap in required_capabilities if cap in capabilities)
            score = matches if matches > 0 else 0
            
            if score > best_score:
                best_score = score
                best_agent = agent_id
        
        return best_agent
    
    # ========================================================================
    # Task Execution
    # ========================================================================
    
    async def execute_collaborative_task(
        self,
        task_id: str,
        description: str,
        user_id: int,
        mode: CollaborationMode = CollaborationMode.PARALLEL,
        team_id: Optional[str] = None,
        project_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a task using multiple agents.
        
        Args:
            task_id: Task identifier
            description: Task description
            user_id: User ID
            mode: Collaboration mode
            team_id: Team to use (or auto-select)
            project_id: Project ID
            context: Task context
        
        Returns:
            Collaboration result with all responses
        """
        try:
            logger.info(f"Starting collaborative task {task_id}: {description}")
            
            # Create collaboration task
            collab_task = CollaborationTask(
                task_id=task_id,
                description=description,
                user_id=user_id,
                project_id=project_id,
                mode=mode,
                team_members=[],
                context=context or {},
            )
            
            # Get team for execution
            if team_id and team_id in self.agent_teams:
                team = self.agent_teams[team_id]
            else:
                # Auto-select agents
                team = self._select_team_for_task(description)
            
            if not team:
                # Fallback to available agents
                team = {
                    agent_id: AgentTeamMember(
                        agent_id=agent_id,
                        agent_type=type(agent).__name__,
                        name=getattr(agent, "name", agent_id),
                        role=AgentRole.EXECUTOR,
                        capabilities=getattr(agent, "capabilities", []),
                    )
                    for agent_id, agent in self.available_agents.items()
                }
            
            collab_task.team_members = list(team.keys())
            self.active_tasks[task_id] = collab_task
            
            # Execute based on mode
            if mode == CollaborationMode.PARALLEL:
                responses = await self._execute_parallel(task_id, team, description, context)
            elif mode == CollaborationMode.SEQUENTIAL:
                responses = await self._execute_sequential(task_id, team, description, context)
            elif mode == CollaborationMode.HIERARCHICAL:
                responses = await self._execute_hierarchical(task_id, team, description, context)
            elif mode == CollaborationMode.CONSENSUS:
                responses = await self._execute_consensus(task_id, team, description, context)
            else:
                responses = []
            
            # Synthesize final response
            final_response = self._synthesize_responses(responses, mode)
            
            # Log activity
            analytics_service.log_user_activity(
                user_id=user_id,
                activity_type=ActivityType.RUN_AGENT,
                description=f"Collaborative task: {description}",
                project_id=project_id,
                success=final_response["status"] == "success",
                metadata={
                    "task_id": task_id,
                    "mode": mode.value,
                    "agents": len(team),
                },
            )
            
            # Store history
            self.collaboration_history.append({
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "mode": mode.value,
                "team_size": len(team),
                "status": final_response["status"],
            })
            
            return final_response
        
        except Exception as e:
            logger.error(f"Failed to execute collaborative task: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "task_id": task_id,
            }
    
    async def _execute_parallel(
        self,
        task_id: str,
        team: Dict[str, AgentTeamMember],
        description: str,
        context: Optional[Dict[str, Any]],
    ) -> List[AgentResponse]:
        """Execute task in parallel mode."""
        import asyncio
        
        responses = []
        tasks = []
        
        for agent_id in team.keys():
            agent = self.available_agents.get(agent_id)
            if agent:
                tasks.append(self._execute_agent(agent_id, agent, description, context))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter valid responses
        valid_responses = [r for r in responses if isinstance(r, AgentResponse)]
        
        return valid_responses
    
    async def _execute_sequential(
        self,
        task_id: str,
        team: Dict[str, AgentTeamMember],
        description: str,
        context: Optional[Dict[str, Any]],
    ) -> List[AgentResponse]:
        """Execute task in sequential mode."""
        responses = []
        accumulated_context = context or {}
        
        for agent_id in team.keys():
            agent = self.available_agents.get(agent_id)
            if agent:
                response = await self._execute_agent(
                    agent_id,
                    agent,
                    description,
                    accumulated_context,
                )
                responses.append(response)
                
                # Update context with agent's response
                accumulated_context[f"{agent_id}_response"] = response.response
        
        return responses
    
    async def _execute_hierarchical(
        self,
        task_id: str,
        team: Dict[str, AgentTeamMember],
        description: str,
        context: Optional[Dict[str, Any]],
    ) -> List[AgentResponse]:
        """Execute task in hierarchical mode with coordinator."""
        responses = []
        
        # Find coordinator
        coordinator_id = None
        for agent_id, member in team.items():
            if member.role == AgentRole.COORDINATOR:
                coordinator_id = agent_id
                break
        
        if not coordinator_id:
            coordinator_id = list(team.keys())[0]
        
        coordinator = self.available_agents.get(coordinator_id)
        
        # Coordinator directs task
        if coordinator:
            coord_response = await self._execute_agent(
                coordinator_id,
                coordinator,
                f"Coordinate this task: {description}",
                context,
            )
            responses.append(coord_response)
            
            # Other agents execute coordinator's plan
            for agent_id in team.keys():
                if agent_id != coordinator_id:
                    agent = self.available_agents.get(agent_id)
                    if agent:
                        response = await self._execute_agent(
                            agent_id,
                            agent,
                            description,
                            context,
                        )
                        responses.append(response)
        
        return responses
    
    async def _execute_consensus(
        self,
        task_id: str,
        team: Dict[str, AgentTeamMember],
        description: str,
        context: Optional[Dict[str, Any]],
    ) -> List[AgentResponse]:
        """Execute task with consensus mode (agents vote)."""
        import asyncio
        
        responses = []
        tasks = []
        
        # All agents execute task
        for agent_id in team.keys():
            agent = self.available_agents.get(agent_id)
            if agent:
                tasks.append(self._execute_agent(agent_id, agent, description, context))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        valid_responses = [r for r in responses if isinstance(r, AgentResponse)]
        
        return valid_responses
    
    async def _execute_agent(
        self,
        agent_id: str,
        agent: BaseAgent,
        task: str,
        context: Optional[Dict[str, Any]],
    ) -> AgentResponse:
        """Execute a single agent."""
        import time
        
        try:
            start_time = time.time()
            
            # Execute agent
            result = await agent.execute(
                task=task,
                context=context or {},
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return AgentResponse(
                agent_id=agent_id,
                agent_type=type(agent).__name__,
                status="success",
                response=result.get("response", ""),
                reasoning=result.get("reasoning", ""),
                metadata=result.get("metadata", {}),
                execution_time_ms=execution_time,
            )
        
        except Exception as e:
            logger.error(f"Agent {agent_id} execution failed: {str(e)}")
            return AgentResponse(
                agent_id=agent_id,
                agent_type=type(agent).__name__,
                status="error",
                response=str(e),
                execution_time_ms=0,
            )
    
    # ========================================================================
    # Response Synthesis
    # ========================================================================
    
    def _synthesize_responses(
        self,
        responses: List[AgentResponse],
        mode: CollaborationMode,
    ) -> Dict[str, Any]:
        """
        Synthesize responses from multiple agents.
        
        Args:
            responses: List of agent responses
            mode: Collaboration mode used
        
        Returns:
            Synthesized final response
        """
        if not responses:
            return {
                "status": "error",
                "error": "No responses from agents",
                "agents": [],
            }
        
        # Check if all succeeded
        successful = [r for r in responses if r.status == "success"]
        failed = [r for r in responses if r.status != "success"]
        
        # Synthesize based on mode
        if mode == CollaborationMode.CONSENSUS:
            # Majority vote
            final_response = successful[0].response if successful else responses[0].response
        elif mode == CollaborationMode.HIERARCHICAL:
            # Coordinator response + execution
            final_response = "\n\n".join([r.response for r in responses])
        else:
            # Combine all responses
            final_response = "\n\n".join([r.response for r in responses])
        
        return {
            "status": "success" if len(successful) > 0 else "partial",
            "final_response": final_response,
            "agents_succeeded": len(successful),
            "agents_failed": len(failed),
            "total_agents": len(responses),
            "individual_responses": [asdict(r) for r in responses],
            "execution_time_ms": sum(r.execution_time_ms for r in responses),
        }
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def _select_team_for_task(
        self,
        task_description: str,
    ) -> Optional[Dict[str, AgentTeamMember]]:
        """Select best team for task."""
        if not self.available_agents:
            return None
        
        # Simple strategy: use all available agents
        team = {}
        for agent_id, agent in self.available_agents.items():
            team[agent_id] = AgentTeamMember(
                agent_id=agent_id,
                agent_type=type(agent).__name__,
                name=getattr(agent, "name", agent_id),
                role=AgentRole.EXECUTOR,
                capabilities=getattr(agent, "capabilities", []),
            )
        
        return team if team else None
    
    def get_collaboration_history(
        self,
        user_id: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get collaboration history."""
        history = self.collaboration_history
        
        if user_id:
            history = [h for h in history if h.get("user_id") == user_id]
        
        return history[-limit:]
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get active collaboration tasks."""
        return [
            {
                "task_id": t.task_id,
                "description": t.description,
                "mode": t.mode.value,
                "team_size": len(t.team_members),
                "created_at": t.created_at.isoformat(),
            }
            for t in self.active_tasks.values()
        ]
    
    def close(self):
        """Close service and clean up."""
        if self.db:
            self.db.close()
            logger.info("Closed AgentOrchestrator")


# Global orchestrator instance
agent_orchestrator = AgentOrchestrator()
