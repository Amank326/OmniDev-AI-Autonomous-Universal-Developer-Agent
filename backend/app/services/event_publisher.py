"""
Event Publisher - Multi-channel event publication with routing and filtering
Supports webhooks, SNS, email, HTTP, and custom handlers
"""

import json
import time
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import hashlib


class PublisherChannel(Enum):
    """Event publication channels"""
    WEBHOOK = "webhook"
    HTTP = "http"
    SNS = "sns"
    EMAIL = "email"
    SLACK = "slack"
    CUSTOM = "custom"
    WEBHOOK_BATCH = "webhook_batch"


class EventCategory(Enum):
    """Event categories for routing"""
    SYSTEM = "system"
    USER = "user"
    ALERT = "alert"
    METRIC = "metric"
    ERROR = "error"
    AUDIT = "audit"
    CUSTOM = "custom"


class DeliveryStatus(Enum):
    """Event delivery status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    DELIVERED = "delivered"
    BOUNCED = "bounced"


@dataclass
class EventRoute:
    """Routes events to channels based on conditions"""
    route_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    channel: PublisherChannel = PublisherChannel.WEBHOOK
    channel_config: Dict[str, Any] = field(default_factory=dict)
    filter_conditions: Dict[str, Any] = field(default_factory=dict)  # event type, severity, etc
    priority: int = 0  # Higher = routes first
    enabled: bool = True
    rate_limit: Optional[int] = None  # Max events per minute
    batching_enabled: bool = False
    batch_size: int = 10
    batch_timeout_seconds: int = 30
    retry_config: Dict[str, Any] = field(default_factory=dict)  # max_retries, backoff
    created_at: float = field(default_factory=time.time)


@dataclass
class PublishedEvent:
    """Event publication record"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    category: EventCategory = EventCategory.CUSTOM
    event_type: str = ""
    severity: str = "info"  # debug, info, warning, error, critical
    title: str = ""
    description: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_enriched: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "source": self.source,
            "category": self.category.value,
            "event_type": self.event_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class DeliveryRecord:
    """Event delivery attempt record"""
    delivery_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str = ""
    route_id: str = ""
    channel: PublisherChannel = PublisherChannel.WEBHOOK
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempt_count: int = 0
    max_attempts: int = 3
    first_attempt_time: Optional[float] = None
    last_attempt_time: Optional[float] = None
    success_time: Optional[float] = None
    error_message: Optional[str] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_retryable(self) -> bool:
        """Check if delivery can be retried"""
        return self.status in [DeliveryStatus.FAILED, DeliveryStatus.PENDING] and \
               self.attempt_count < self.max_attempts


@dataclass
class PublisherStatistics:
    """Publisher statistics"""
    total_events_published: int = 0
    total_events_delivered: int = 0
    total_events_failed: int = 0
    total_events_retried: int = 0
    avg_delivery_latency_ms: float = 0.0
    success_rate: float = 100.0
    channels_active: int = 0


class EventEnricher:
    """Enriches events with additional context"""
    
    def __init__(self):
        self.enrichers: Dict[str, Callable] = {}
        self.lock = threading.RLock()
    
    def register_enricher(self, name: str, enricher: Callable[[PublishedEvent], PublishedEvent]) -> None:
        """Register enricher function"""
        with self.lock:
            self.enrichers[name] = enricher
    
    def enrich(self, event: PublishedEvent) -> PublishedEvent:
        """Enrich event with all registered enrichers"""
        with self.lock:
            for enricher in self.enrichers.values():
                try:
                    event = enricher(event)
                except Exception:
                    pass
        
        event.is_enriched = True
        return event


class EventFilter:
    """Filters events based on conditions"""
    
    @staticmethod
    def matches(event: PublishedEvent, filter_conditions: Dict[str, Any]) -> bool:
        """Check if event matches filter condition"""
        for key, expected_value in filter_conditions.items():
            if key == "event_type":
                if event.event_type != expected_value:
                    return False
            elif key == "severity":
                if event.severity != expected_value:
                    return False
            elif key == "category":
                if event.category.value != expected_value:
                    return False
            elif key == "source":
                if event.source != expected_value:
                    return False
            elif key == "tags":
                # All specified tags must be present
                for tag_key, tag_value in expected_value.items():
                    if event.tags.get(tag_key) != tag_value:
                        return False
        
        return True


class RateLimiter:
    """Rate limiting per route"""
    
    def __init__(self, rate_limit: int, window_seconds: int = 60):
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self.event_times: deque = deque()
        self.lock = threading.RLock()
    
    def allow(self) -> bool:
        """Check if event is allowed by rate limit"""
        with self.lock:
            now = time.time()
            cutoff = now - self.window_seconds
            
            # Remove old entries
            while self.event_times and self.event_times[0] < cutoff:
                self.event_times.popleft()
            
            if len(self.event_times) < self.rate_limit:
                self.event_times.append(now)
                return True
            
            return False


class BatchCollector:
    """Collects events for batch publishing"""
    
    def __init__(self, batch_size: int, batch_timeout_seconds: int):
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds
        self.events: List[PublishedEvent] = []
        self.created_at = time.time()
        self.lock = threading.RLock()
    
    def add(self, event: PublishedEvent) -> Optional[List[PublishedEvent]]:
        """Add event and return batch if ready"""
        with self.lock:
            self.events.append(event)
            
            # Check if batch is full
            if len(self.events) >= self.batch_size:
                batch = self.events
                self.events = []
                self.created_at = time.time()
                return batch
            
            return None
    
    def get_batch_if_ready(self) -> Optional[List[PublishedEvent]]:
        """Get batch if timeout has elapsed"""
        with self.lock:
            if not self.events:
                return None
            
            if time.time() - self.created_at >= self.batch_timeout_seconds:
                batch = self.events
                self.events = []
                self.created_at = time.time()
                return batch
            
            return None


class EventPublisher:
    """Central event publisher with routing and delivery"""
    
    def __init__(self):
        self.routes: Dict[str, EventRoute] = {}
        self.deliveries: Dict[str, DeliveryRecord] = {}
        self.enricher = EventEnricher()
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.batch_collectors: Dict[str, BatchCollector] = {}
        self.channel_handlers: Dict[PublisherChannel, Callable] = {}
        self.stats = PublisherStatistics()
        self.lock = threading.RLock()
        self.callbacks: List[Callable] = []
        self.delivery_queue: List[DeliveryRecord] = []
        self.dead_letter_events: List[Tuple[PublishedEvent, str]] = []
    
    def register_channel_handler(self, channel: PublisherChannel,
                                handler: Callable[[EventRoute, PublishedEvent], bool]) -> None:
        """Register handler for channel"""
        with self.lock:
            self.channel_handlers[channel] = handler
    
    def create_route(self, name: str, channel: PublisherChannel,
                    channel_config: Dict, filter_conditions: Dict = None) -> str:
        """Create event route"""
        route = EventRoute(
            name=name,
            channel=channel,
            channel_config=channel_config,
            filter_conditions=filter_conditions or {},
        )
        
        with self.lock:
            self.routes[route.route_id] = route
            
            # Initialize rate limiter if set
            if route.rate_limit:
                self.rate_limiters[route.route_id] = RateLimiter(route.rate_limit)
            
            # Initialize batch collector if batching enabled
            if route.batching_enabled:
                self.batch_collectors[route.route_id] = BatchCollector(
                    route.batch_size,
                    route.batch_timeout_seconds
                )
        
        self._trigger_callback("route_created", route.route_id, name)
        return route.route_id
    
    def get_route(self, route_id: str) -> Optional[EventRoute]:
        """Get route"""
        with self.lock:
            return self.routes.get(route_id)
    
    def delete_route(self, route_id: str) -> bool:
        """Delete route"""
        with self.lock:
            if route_id not in self.routes:
                return False
            
            del self.routes[route_id]
            if route_id in self.rate_limiters:
                del self.rate_limiters[route_id]
            if route_id in self.batch_collectors:
                del self.batch_collectors[route_id]
        
        self._trigger_callback("route_deleted", route_id)
        return True
    
    def publish(self, event: PublishedEvent) -> str:
        """Publish event and route to channels"""
        start_time = time.time()
        
        # Enrich event
        event = self.enricher.enrich(event)
        
        with self.lock:
            self.stats.total_events_published += 1
        
        # Find matching routes
        matching_routes = []
        with self.lock:
            for route in sorted(self.routes.values(), key=lambda r: -r.priority):
                if not route.enabled:
                    continue
                
                if EventFilter.matches(event, route.filter_conditions):
                    matching_routes.append(route)
        
        # Route event to channels
        for route in matching_routes:
            # Check rate limit
            if route.route_id in self.rate_limiters:
                if not self.rate_limiters[route.route_id].allow():
                    self._trigger_callback("rate_limit_exceeded", route.route_id)
                    continue
            
            # Handle batching
            if route.batching_enabled:
                batch = self.batch_collectors[route.route_id].add(event)
                if batch:
                    for batch_event in batch:
                        self._deliver_event(batch_event, route)
            else:
                self._deliver_event(event, route)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        with self.lock:
            self.stats.avg_delivery_latency_ms = (
                (self.stats.avg_delivery_latency_ms + latency_ms) / 2
            )
        
        self._trigger_callback("event_published", event.event_id)
        return event.event_id
    
    def _deliver_event(self, event: PublishedEvent, route: EventRoute) -> None:
        """Deliver event via route"""
        delivery = DeliveryRecord(
            event_id=event.event_id,
            route_id=route.route_id,
            channel=route.channel,
            max_attempts=route.retry_config.get("max_retries", 3) + 1
        )
        
        with self.lock:
            self.deliveries[delivery.delivery_id] = delivery
        
        self._attempt_delivery(delivery, event, route)
    
    def _attempt_delivery(self, delivery: DeliveryRecord, event: PublishedEvent,
                         route: EventRoute) -> None:
        """Attempt to deliver event"""
        delivery.attempt_count += 1
        delivery.first_attempt_time = delivery.first_attempt_time or time.time()
        delivery.last_attempt_time = time.time()
        
        # Get channel handler
        handler = self.channel_handlers.get(route.channel)
        
        success = False
        if handler:
            try:
                success = handler(route, event)
            except Exception as e:
                delivery.error_message = str(e)
        
        if success:
            delivery.status = DeliveryStatus.DELIVERED
            delivery.success_time = time.time()
            with self.lock:
                self.stats.total_events_delivered += 1
            self._trigger_callback("event_delivered", delivery.event_id, route.route_id)
        else:
            if delivery.is_retryable():
                delivery.status = DeliveryStatus.RETRYING
                # Schedule retry with exponential backoff
                backoff = route.retry_config.get("backoff_multiplier", 2) ** (delivery.attempt_count - 1)
                retry_delay = min(backoff, 3600)  # Max 1 hour
                
                self._trigger_callback("event_delivery_retry", delivery.event_id, delivery.attempt_count)
                # In real implementation, schedule retry
            else:
                delivery.status = DeliveryStatus.FAILED
                with self.lock:
                    self.stats.total_events_failed += 1
                    self.dead_letter_events.append((event, delivery.error_message or "Max retries exceeded"))
                
                self._trigger_callback("event_delivery_failed", delivery.event_id, delivery.error_message)
    
    def get_delivery_status(self, delivery_id: str) -> Optional[DeliveryRecord]:
        """Get delivery status"""
        with self.lock:
            return self.deliveries.get(delivery_id)
    
    def get_dead_letter_events(self, limit: int = 100) -> List[Tuple[PublishedEvent, str]]:
        """Get failed events"""
        with self.lock:
            return self.dead_letter_events[-limit:]
    
    def retry_dead_letter_event(self, event_index: int) -> Optional[str]:
        """Retry delivery of dead letter event"""
        with self.lock:
            if event_index >= len(self.dead_letter_events):
                return None
            
            event, _ = self.dead_letter_events[event_index]
        
        return self.publish(event)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get publisher statistics"""
        with self.lock:
            delivered = self.stats.total_events_delivered
            published = self.stats.total_events_published
            success_rate = (delivered / published * 100) if published > 0 else 0.0
            
            return {
                "total_events_published": self.stats.total_events_published,
                "total_events_delivered": self.stats.total_events_delivered,
                "total_events_failed": self.stats.total_events_failed,
                "success_rate": success_rate,
                "avg_delivery_latency_ms": self.stats.avg_delivery_latency_ms,
                "routes_active": len([r for r in self.routes.values() if r.enabled]),
                "dead_letter_queue_size": len(self.dead_letter_events),
            }
    
    def register_callback(self, callback: Callable[[str, ...], None]) -> None:
        """Register event callback"""
        with self.lock:
            self.callbacks.append(callback)
    
    def _trigger_callback(self, event_type: str, *args, **kwargs) -> None:
        """Trigger callbacks"""
        for callback in self.callbacks:
            try:
                callback(event_type, *args, **kwargs)
            except Exception:
                pass


# Singleton instance
_event_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get or create singleton event publisher"""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    return _event_publisher


def reset_event_publisher() -> None:
    """Reset event publisher (for testing)"""
    global _event_publisher
    _event_publisher = None
