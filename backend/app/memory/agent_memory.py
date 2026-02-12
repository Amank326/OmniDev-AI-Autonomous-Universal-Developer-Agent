"""
Agent Memory Integration
========================

Shared memory across agents for collaboration and context awareness.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import Session

from app.database.config import SessionLocal, Base

logger = logging.getLogger(__name__)


class CollaborationMemory(Base):
    """Database model for team collaboration memory."""
    __tablename__ = "agent_collaboration_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(String(255), index=True)
    task_id = Column(String(255), index=True)
    agent_id = Column(String(255))
    message_type = Column(String(50))  # contribution, decision, solution, error
    content = Column(Text)
    reasoning = Column(Text, nullable=True)
    meta_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AgentMemoryEntry:
    """Entry in agent shared memory."""
    
    def __init__(
        self,
        agent_id: str,
        content: str,
        message_type: str = "contribution",
        reasoning: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize memory entry."""
        self.agent_id = agent_id
        self.content = content
        self.message_type = message_type
        self.reasoning = reasoning
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()


class AgentMemoryManager:
    """
    Manages shared memory for agent teams.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize agent memory manager."""
        self.db = db or SessionLocal()
        self.in_memory_cache: Dict[str, List[AgentMemoryEntry]] = {}
    
    # ========================================================================
    # Memory Operations
    # ========================================================================
    
    def store_memory(
        self,
        team_id: str,
        task_id: str,
        agent_id: str,
        content: str,
        message_type: str = "contribution",
        reasoning: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store memory in team context.
        
        Args:
            team_id: Team identifier
            task_id: Task identifier
            agent_id: Agent identifier
            content: Memory content
            message_type: Type of message
            reasoning: Agent reasoning
            metadata: Additional metadata
        
        Returns:
            True if stored successfully
        """
        try:
            # Store in database
            memory = CollaborationMemory(
                team_id=team_id,
                task_id=task_id,
                agent_id=agent_id,
                message_type=message_type,
                content=content,
                reasoning=reasoning,
                metadata=metadata or {},
            )
            self.db.add(memory)
            self.db.commit()
            
            # Store in in-memory cache
            cache_key = f"{team_id}:{task_id}"
            if cache_key not in self.in_memory_cache:
                self.in_memory_cache[cache_key] = []
            
            entry = AgentMemoryEntry(
                agent_id=agent_id,
                content=content,
                message_type=message_type,
                reasoning=reasoning,
                metadata=metadata,
            )
            self.in_memory_cache[cache_key].append(entry)
            
            logger.debug(f"Stored memory for {agent_id} in {team_id}:{task_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store memory: {str(e)}")
            self.db.rollback()
            return False
    
    def retrieve_memory(
        self,
        team_id: str,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        message_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve shared memory.
        
        Args:
            team_id: Team identifier
            task_id: Task identifier (optional)
            agent_id: Agent identifier (optional)
            message_type: Message type (optional)
            limit: Maximum results
        
        Returns:
            List of memory entries
        """
        try:
            query = self.db.query(CollaborationMemory).filter_by(team_id=team_id)
            
            if task_id:
                query = query.filter_by(task_id=task_id)
            if agent_id:
                query = query.filter_by(agent_id=agent_id)
            if message_type:
                query = query.filter_by(message_type=message_type)
            
            entries = query.order_by(CollaborationMemory.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "agent_id": e.agent_id,
                    "message_type": e.message_type,
                    "content": e.content,
                    "reasoning": e.reasoning,
                    "metadata": e.metadata,
                    "timestamp": e.created_at.isoformat(),
                }
                for e in entries
            ]
        
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {str(e)}")
            return []
    
    def get_team_context(
        self,
        team_id: str,
        task_id: str,
        include_reasoning: bool = False,
    ) -> str:
        """
        Get formatted team context string.
        
        Args:
            team_id: Team identifier
            task_id: Task identifier
            include_reasoning: Include agent reasoning
        
        Returns:
            Formatted context string
        """
        try:
            entries = self.retrieve_memory(team_id, task_id)
            
            context_parts = []
            for entry in reversed(entries):  # Chronological order
                agent = entry['agent_id']
                msg_type = entry['message_type']
                content = entry['content']
                
                part = f"{agent} ({msg_type}): {content}"
                if include_reasoning and entry['reasoning']:
                    part += f"\n  Reasoning: {entry['reasoning']}"
                
                context_parts.append(part)
            
            return "\n".join(context_parts)
        
        except Exception as e:
            logger.error(f"Failed to get team context: {str(e)}")
            return ""
    
    # ========================================================================
    # Collaboration Features
    # ========================================================================
    
    def get_agent_contributions(
        self,
        team_id: str,
        agent_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get agent's contributions to team."""
        return self.retrieve_memory(
            team_id=team_id,
            agent_id=agent_id,
            limit=limit,
        )
    
    def get_team_decisions(
        self,
        team_id: str,
        task_id: str,
    ) -> List[Dict[str, Any]]:
        """Get team decisions for task."""
        return self.retrieve_memory(
            team_id=team_id,
            task_id=task_id,
            message_type="decision",
        )
    
    def get_team_solutions(
        self,
        team_id: str,
        task_id: str,
    ) -> List[Dict[str, Any]]:
        """Get solutions proposed by team."""
        return self.retrieve_memory(
            team_id=team_id,
            task_id=task_id,
            message_type="solution",
        )
    
    def record_decision(
        self,
        team_id: str,
        task_id: str,
        deciding_agent: str,
        decision: str,
        reasoning: str = "",
        affected_agents: Optional[List[str]] = None,
    ) -> bool:
        """
        Record a team decision.
        
        Args:
            team_id: Team identifier
            task_id: Task identifier
            deciding_agent: Agent making decision
            decision: Decision text
            reasoning: Decision reasoning
            affected_agents: Agents affected by decision
        
        Returns:
            True if recorded successfully
        """
        return self.store_memory(
            team_id=team_id,
            task_id=task_id,
            agent_id=deciding_agent,
            content=decision,
            message_type="decision",
            reasoning=reasoning,
            metadata={"affected_agents": affected_agents or []},
        )
    
    def record_solution(
        self,
        team_id: str,
        task_id: str,
        agent_id: str,
        solution: str,
        confidence: float = 0.5,
    ) -> bool:
        """
        Record a proposed solution.
        
        Args:
            team_id: Team identifier
            task_id: Task identifier
            agent_id: Agent proposing solution
            solution: Solution description
            confidence: Confidence in solution (0-1)
        
        Returns:
            True if recorded successfully
        """
        return self.store_memory(
            team_id=team_id,
            task_id=task_id,
            agent_id=agent_id,
            content=solution,
            message_type="solution",
            metadata={"confidence": confidence},
        )
    
    def record_error(
        self,
        team_id: str,
        task_id: str,
        agent_id: str,
        error: str,
        recovery_suggestion: str = "",
    ) -> bool:
        """
        Record an error for team awareness.
        
        Args:
            team_id: Team identifier
            task_id: Task identifier
            agent_id: Agent that encountered error
            error: Error description
            recovery_suggestion: Suggestion for recovery
        
        Returns:
            True if recorded successfully
        """
        return self.store_memory(
            team_id=team_id,
            task_id=task_id,
            agent_id=agent_id,
            content=error,
            message_type="error",
            reasoning=recovery_suggestion,
        )
    
    # ========================================================================
    # Memory Management
    # ========================================================================
    
    def clear_old_memory(self, days: int = 30) -> int:
        """
        Clear memory older than specified days.
        
        Args:
            days: Days to keep
        
        Returns:
            Number of entries deleted
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            deleted = self.db.query(CollaborationMemory).filter(
                CollaborationMemory.created_at < cutoff
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleared {deleted} old memory entries")
            return deleted
        
        except Exception as e:
            logger.error(f"Failed to clear old memory: {str(e)}")
            self.db.rollback()
            return 0
    
    def get_memory_stats(self, team_id: Optional[str] = None) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            query = self.db.query(CollaborationMemory)
            if team_id:
                query = query.filter_by(team_id=team_id)
            
            total = query.count()
            by_type = {}
            
            for msg_type in ["contribution", "decision", "solution", "error"]:
                count = query.filter_by(message_type=msg_type).count()
                by_type[msg_type] = count
            
            return {
                "total_entries": total,
                "by_message_type": by_type,
                "cache_size": sum(len(v) for v in self.in_memory_cache.values()),
            }
        
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {}
    
    def close(self):
        """Close and cleanup."""
        if self.db:
            self.db.close()
            logger.info("Closed AgentMemoryManager")


# Global instance
agent_memory_manager = AgentMemoryManager()
