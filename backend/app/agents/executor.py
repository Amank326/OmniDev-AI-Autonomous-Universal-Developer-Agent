"""Agent executor for running agents asynchronously."""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.agents.base import BaseAgent
from app.agents.code_agents import CodeAnalyzerAgent, CodeGeneratorAgent, DocumentationAgent

logger = logging.getLogger(__name__)


class AgentExecutor:
    """Executor for managing and running agents."""

    def __init__(self):
        """Initialize agent executor."""
        self.agents: Dict[str, BaseAgent] = {}
        self._register_agents()

    def _register_agents(self):
        """Register available agents."""
        self.agents["code_analyzer"] = CodeAnalyzerAgent()
        self.agents["code_generator"] = CodeGeneratorAgent()
        self.agents["documentation"] = DocumentationAgent()

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get agent by name."""
        return self.agents.get(agent_name)

    async def execute_agent(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """Execute an agent with timeout."""
        agent = self.get_agent(agent_name)
        if not agent:
            return {
                "error": f"Agent '{agent_name}' not found",
                "timestamp": datetime.utcnow().isoformat(),
            }

        try:
            result = await asyncio.wait_for(
                agent.run(input_data),
                timeout=timeout,
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"Agent '{agent_name}' execution timed out")
            return {
                "error": "Agent execution timed out",
                "agent": agent_name,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Agent '{agent_name}' execution failed: {e}")
            return {
                "error": str(e),
                "agent": agent_name,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def list_agents(self) -> list:
        """List all available agents."""
        return list(self.agents.keys())


# Global agent executor instance
agent_executor = AgentExecutor()
