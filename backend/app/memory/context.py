"""Context memory for maintaining agent state and conversation history."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from collections import defaultdict

logger = logging.getLogger(__name__)


class ContextMemory:
    """In-memory context store for agents.

    Provides short-term memory for agent conversations and task context.
    For production, replace with Redis-backed storage.
    """

    def __init__(self, max_history: int = 100):
        """Initialize context memory.

        Args:
            max_history: Maximum number of entries to keep per context.
        """
        self.max_history = max_history
        self._store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def add(self, context_id: str, entry: Dict[str, Any]) -> None:
        """Add an entry to a context.

        Args:
            context_id: Unique context identifier (e.g., user_id + agent_name).
            entry: Data entry to store.
        """
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._store[context_id].append(entry)

        # Trim to max_history
        if len(self._store[context_id]) > self.max_history:
            self._store[context_id] = self._store[context_id][-self.max_history:]

    def get(self, context_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent entries from a context.

        Args:
            context_id: Unique context identifier.
            limit: Maximum number of entries to return.

        Returns:
            List of recent context entries.
        """
        return self._store.get(context_id, [])[-limit:]

    def get_all(self, context_id: str) -> List[Dict[str, Any]]:
        """Get all entries for a context.

        Args:
            context_id: Unique context identifier.

        Returns:
            All entries for the context.
        """
        return self._store.get(context_id, [])

    def set_metadata(self, context_id: str, metadata: Dict[str, Any]) -> None:
        """Set metadata for a context.

        Args:
            context_id: Unique context identifier.
            metadata: Metadata dictionary.
        """
        self._metadata[context_id] = metadata

    def get_metadata(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a context.

        Args:
            context_id: Unique context identifier.

        Returns:
            Metadata dictionary or None.
        """
        return self._metadata.get(context_id)

    def clear(self, context_id: str) -> None:
        """Clear all entries for a context.

        Args:
            context_id: Unique context identifier.
        """
        self._store.pop(context_id, None)
        self._metadata.pop(context_id, None)

    def clear_all(self) -> None:
        """Clear all contexts."""
        self._store.clear()
        self._metadata.clear()

    @property
    def active_contexts(self) -> List[str]:
        """Get list of active context IDs."""
        return list(self._store.keys())


# Global context memory instance
context_memory = ContextMemory()
