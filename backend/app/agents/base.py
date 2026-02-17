"""Base autonomous agent class."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all autonomous agents."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize agent."""
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task."""
        pass

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        return True

    async def prepare_output(self, result: Any) -> Dict[str, Any]:
        """Prepare output data."""
        return {
            "agent": self.name,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run agent with error handling."""
        try:
            self.logger.info(f"Starting agent execution: {self.name}")

            # Validate input
            if not await self.validate_input(input_data):
                raise ValueError("Invalid input data")

            # Execute agent logic
            result = await self.execute(input_data)

            # Prepare output
            output = await self.prepare_output(result)

            self.logger.info(f"Agent execution completed: {self.name}")
            return output

        except Exception as e:
            self.logger.error(f"Agent execution failed: {e}")
            return {
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
