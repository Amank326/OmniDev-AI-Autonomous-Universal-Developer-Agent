"""Base Agent Class - Foundation for all specialized agents"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Abstract base class for all agents in OmniDev AI"""
    
    def __init__(self, name: str, memory=None):
        self.name = name
        self.memory = memory
        self.task_history: List[Dict] = []
        self.capabilities: List[str] = []
        self.status = "idle"
        self.created_at = datetime.now()
    
    @abstractmethod
    async def process(self, task: str, context: Dict) -> Dict:
        """Process a task and return result"""
        pass
    
    async def execute(self, task: str, context: Dict) -> Dict:
        """Execute task with logging and history"""
        logger.info(f"[{self.name}] Starting task: {task}")
        self.status = "executing"
        
        try:
            result = await self.process(task, context)
            self.status = "idle"
            
            # Store in history
            self.task_history.append({
                "task": task,
                "status": "success",
                "result": result,
                "timestamp": datetime.now()
            })
            
            logger.info(f"[{self.name}] Task completed successfully")
            return result
            
        except Exception as e:
            self.status = "error"
            logger.error(f"[{self.name}] Error: {str(e)}")
            
            self.task_history.append({
                "task": task,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            })
            
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name
            }
    
    async def store_memory(self, key: str, value: Any):
        """Store information in memory system"""
        if self.memory:
            await self.memory.store(f"{self.name}:{key}", value)
    
    async def retrieve_memory(self, key: str) -> Optional[Any]:
        """Retrieve information from memory system"""
        if self.memory:
            return await self.memory.retrieve(f"{self.name}:{key}")
        return None
    
    def get_status(self) -> Dict:
        """Get agent status"""
        return {
            "name": self.name,
            "status": self.status,
            "capabilities": self.capabilities,
            "task_count": len(self.task_history),
            "created_at": self.created_at.isoformat()
        }
