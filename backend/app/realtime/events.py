"""Real-time event bus for pub/sub within the application."""

import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List, Set

logger = logging.getLogger(__name__)

# Type alias for async event handlers
EventHandler = Callable[..., Coroutine[Any, Any, None]]


class EventBus:
    """Simple async event bus for real-time event distribution.

    Usage:
        bus = EventBus()

        async def on_agent_complete(data):
            print(f"Agent finished: {data}")

        bus.subscribe("agent.complete", on_agent_complete)
        await bus.publish("agent.complete", {"agent_id": 1, "result": "ok"})
    """

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._wildcard_handlers: List[EventHandler] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to an event type."""
        if event_type == "*":
            self._wildcard_handlers.append(handler)
        else:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler to event '{event_type}'")

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe from an event type."""
        if event_type == "*":
            self._wildcard_handlers.remove(handler)
        elif event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    async def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event to all subscribed handlers."""
        handlers = self._handlers.get(event_type, []) + self._wildcard_handlers
        if not handlers:
            return

        tasks = []
        for handler in handlers:
            try:
                tasks.append(handler(event_type, data))
            except Exception as e:
                logger.error(f"Error creating task for handler on '{event_type}': {e}")

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Handler error on '{event_type}': {result}")

    def clear(self) -> None:
        """Remove all handlers."""
        self._handlers.clear()
        self._wildcard_handlers.clear()

    @property
    def event_types(self) -> Set[str]:
        """Return all registered event types."""
        return set(self._handlers.keys())


# Singleton event bus
event_bus = EventBus()
