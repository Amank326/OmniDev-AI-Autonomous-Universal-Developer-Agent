"""
Message Queue Service - Reliable message queuing with persistence and retry logic
Supports task queues, delayed messages, dead letter handling
"""

import json
import time
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import heapq


class MessagePriority(Enum):
    """Message delivery priority"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


class MessageState(Enum):
    """Message processing state"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    DELAYED = "delayed"


class DeliveryStrategy(Enum):
    """Message delivery strategy"""
    FIFO = "fifo"  # First-in-first-out
    LIFO = "lifo"  # Last-in-first-out (stack)
    PRIORITY = "priority"  # Priority queue
    WEIGHTED = "weighted"  # Weighted round-robin


@dataclass
class QueueMessage:
    """Message in queue"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    queue_name: str = ""
    payload: Any = None
    priority: MessagePriority = MessagePriority.NORMAL
    state: MessageState = MessageState.QUEUED
    created_at: float = field(default_factory=time.time)
    scheduled_time: Optional[float] = None  # For delayed messages
    expires_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    attempt_times: List[float] = field(default_factory=list)
    error_message: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if message has expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def is_ready(self) -> bool:
        """Check if message is ready to process"""
        if self.is_expired():
            return False
        if self.scheduled_time is None:
            return self.state == MessageState.QUEUED
        return time.time() >= self.scheduled_time and self.state == MessageState.QUEUED
    
    def can_retry(self) -> bool:
        """Check if message can be retried"""
        return self.retry_count < self.max_retries


@dataclass
class QueueConfig:
    """Queue configuration"""
    name: str
    delivery_strategy: DeliveryStrategy = DeliveryStrategy.FIFO
    max_size: int = 100000
    max_message_size: int = 1048576  # 1 MB
    default_ttl_seconds: int = 86400  # 24 hours
    enable_persistence: bool = False
    enable_deduplication: bool = False
    max_consumers: int = 10
    visibility_timeout_seconds: int = 30


@dataclass
class QueueConsumer:
    """Queue consumer"""
    consumer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    queue_name: str = ""
    is_active: bool = True
    max_concurrent_messages: int = 1
    current_processing: int = 0
    processed_count: int = 0
    failed_count: int = 0
    error_rate: float = 0.0
    created_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)


@dataclass
class DeadLetterEntry:
    """Dead letter queue entry"""
    message_id: str
    queue_name: str
    message: QueueMessage
    failed_count: int
    created_at: float
    reason: str


@dataclass
class QueueStatistics:
    """Queue statistics"""
    total_messages: int = 0
    processed_messages: int = 0
    failed_messages: int = 0
    delayed_messages: int = 0
    avg_processing_time_ms: float = 0.0
    throughput_mps: float = 0.0  # messages per second
    error_rate: float = 0.0
    queue_depth: int = 0


class PriorityQueue:
    """Priority-based message queue"""
    
    def __init__(self, config: QueueConfig):
        self.config = config
        self.queue: List[Tuple[int, str, QueueMessage]] = []  # (priority, timestamp, message)
        self.message_index: Dict[str, QueueMessage] = {}
        self.lock = threading.RLock()
    
    def put(self, message: QueueMessage) -> bool:
        """Add message to queue"""
        with self.lock:
            if len(self.queue) >= self.config.max_size:
                return False
            
            priority = message.priority.value
            heapq.heappush(self.queue, (priority, message.created_at, message.message_id))
            self.message_index[message.message_id] = message
            return True
    
    def get(self) -> Optional[QueueMessage]:
        """Get next message"""
        with self.lock:
            while self.queue:
                priority, _, msg_id = heapq.heappop(self.queue)
                if msg_id in self.message_index:
                    message = self.message_index[msg_id]
                    if message.is_ready():
                        message.state = MessageState.PROCESSING
                        return message
            return None
    
    def size(self) -> int:
        """Get queue size"""
        with self.lock:
            return len(self.message_index)
    
    def peek(self) -> Optional[QueueMessage]:
        """Peek at next message without removing"""
        with self.lock:
            for _, _, msg_id in self.queue:
                if msg_id in self.message_index:
                    return self.message_index[msg_id]
            return None
    
    def remove(self, message_id: str) -> bool:
        """Remove message from queue"""
        with self.lock:
            if message_id in self.message_index:
                del self.message_index[message_id]
                return True
            return False


class FifoQueue:
    """First-in-first-out message queue"""
    
    def __init__(self, config: QueueConfig):
        self.config = config
        self.queue: deque = deque(maxlen=config.max_size)
        self.message_index: Dict[str, QueueMessage] = {}
        self.lock = threading.RLock()
    
    def put(self, message: QueueMessage) -> bool:
        """Add message to queue"""
        with self.lock:
            if len(self.queue) >= self.config.max_size:
                return False
            
            self.queue.append(message.message_id)
            self.message_index[message.message_id] = message
            return True
    
    def get(self) -> Optional[QueueMessage]:
        """Get next message"""
        with self.lock:
            while self.queue:
                msg_id = self.queue.popleft()
                if msg_id in self.message_index:
                    message = self.message_index[msg_id]
                    if message.is_ready():
                        message.state = MessageState.PROCESSING
                        return message
            return None
    
    def size(self) -> int:
        """Get queue size"""
        with self.lock:
            return len(self.message_index)


class LifoQueue:
    """Last-in-first-out message queue (stack)"""
    
    def __init__(self, config: QueueConfig):
        self.config = config
        self.queue: deque = deque(maxlen=config.max_size)
        self.message_index: Dict[str, QueueMessage] = {}
        self.lock = threading.RLock()
    
    def put(self, message: QueueMessage) -> bool:
        """Add message to queue"""
        with self.lock:
            if len(self.queue) >= self.config.max_size:
                return False
            
            self.queue.append(message.message_id)
            self.message_index[message.message_id] = message
            return True
    
    def get(self) -> Optional[QueueMessage]:
        """Get next message (from end)"""
        with self.lock:
            while self.queue:
                msg_id = self.queue.pop()
                if msg_id in self.message_index:
                    message = self.message_index[msg_id]
                    if message.is_ready():
                        message.state = MessageState.PROCESSING
                        return message
            return None
    
    def size(self) -> int:
        """Get queue size"""
        with self.lock:
            return len(self.message_index)


class MessageQueue:
    """Managed message queue with retry, persistence, DLQ"""
    
    def __init__(self, config: QueueConfig):
        self.config = config
        
        # Select queue implementation
        if config.delivery_strategy == DeliveryStrategy.PRIORITY:
            self.queue = PriorityQueue(config)
        elif config.delivery_strategy == DeliveryStrategy.LIFO:
            self.queue = LifoQueue(config)
        else:
            self.queue = FifoQueue(config)
        
        self.delayed_queue: Dict[str, QueueMessage] = {}
        self.dead_letter_queue: Dict[str, DeadLetterEntry] = {}
        self.processing: Dict[str, QueueMessage] = {}
        self.consumers: Dict[str, QueueConsumer] = {}
        self.stats = QueueStatistics()
        self.lock = threading.RLock()
        self.callbacks: List[Callable] = []
        
        # Deduplication
        self.seen_messages: set = set()
    
    def enqueue(self, payload: Any, priority: MessagePriority = MessagePriority.NORMAL,
               ttl_seconds: Optional[int] = None, delay_seconds: int = 0,
               max_retries: int = 3, tags: Optional[Dict] = None) -> Optional[str]:
        """Enqueue message"""
        with self.lock:
            message = QueueMessage(
                message_id=str(uuid.uuid4()),
                queue_name=self.config.name,
                payload=payload,
                priority=priority,
                max_retries=max_retries,
                tags=tags or {},
            )
            
            # Set TTL
            ttl = ttl_seconds or self.config.default_ttl_seconds
            message.expires_at = time.time() + ttl
            
            # Handle delayed messages
            if delay_seconds > 0:
                message.scheduled_time = time.time() + delay_seconds
                message.state = MessageState.DELAYED
                self.delayed_queue[message.message_id] = message
                self.stats.delayed_messages += 1
                self._trigger_callback("message_delayed", message.message_id)
            else:
                # Add to main queue
                if not self.queue.put(message):
                    self._trigger_callback("queue_full", self.config.name)
                    return None
            
            self.stats.total_messages += 1
            self._trigger_callback("message_enqueued", message.message_id)
            return message.message_id
    
    def dequeue(self, consumer_id: Optional[str] = None) -> Optional[QueueMessage]:
        """Dequeue message for processing"""
        with self.lock:
            # Try to get from main queue
            message = self.queue.get()
            
            # If nothing, check delayed queue
            if not message:
                self._process_delayed_queue()
                message = self.queue.get()
            
            if message:
                message.state = MessageState.PROCESSING
                message.attempt_times.append(time.time())
                self.processing[message.message_id] = message
                
                if consumer_id:
                    if consumer_id not in self.consumers:
                        self.consumers[consumer_id] = QueueConsumer(
                            consumer_id=consumer_id,
                            queue_name=self.config.name
                        )
                
                self._trigger_callback("message_dequeued", message.message_id)
                return message
            
            return None
    
    def _process_delayed_queue(self) -> None:
        """Move ready delayed messages to main queue"""
        ready_messages = []
        
        for msg_id, message in self.delayed_queue.items():
            if message.is_ready():
                ready_messages.append(msg_id)
        
        for msg_id in ready_messages:
            message = self.delayed_queue.pop(msg_id)
            message.state = MessageState.QUEUED
            self.queue.put(message)
            self.stats.delayed_messages -= 1
    
    def complete(self, message_id: str) -> bool:
        """Mark message as completed"""
        with self.lock:
            if message_id not in self.processing:
                return False
            
            message = self.processing.pop(message_id)
            message.state = MessageState.COMPLETED
            self.queue.remove(message_id)
            self.stats.processed_messages += 1
            
            self._trigger_callback("message_completed", message_id)
            return True
    
    def fail(self, message_id: str, error: str) -> bool:
        """Mark message as failed and retry or DLQ"""
        with self.lock:
            if message_id not in self.processing:
                return False
            
            message = self.processing.pop(message_id)
            message.retry_count += 1
            message.error_message = error
            
            if message.can_retry():
                # Re-queue with exponential backoff
                backoff = min(2 ** message.retry_count, 3600)  # Max 1 hour
                message.scheduled_time = time.time() + backoff
                message.state = MessageState.DELAYED
                self.delayed_queue[message_id] = message
                self.stats.delayed_messages += 1
                self._trigger_callback("message_retried", message_id, message.retry_count)
            else:
                # Move to dead letter queue
                dlq_entry = DeadLetterEntry(
                    message_id=message_id,
                    queue_name=self.config.name,
                    message=message,
                    failed_count=message.retry_count,
                    created_at=time.time(),
                    reason=error
                )
                self.dead_letter_queue[message_id] = dlq_entry
                message.state = MessageState.DEAD_LETTER
                self.stats.failed_messages += 1
                self._trigger_callback("message_dead_lettered", message_id)
            
            return True
    
    def get_queue_depth(self) -> int:
        """Get number of messages waiting"""
        with self.lock:
            return self.queue.size() + len(self.delayed_queue) + len(self.processing)
    
    def peek_message(self) -> Optional[QueueMessage]:
        """Peek at next message without removing"""
        with self.lock:
            return self.queue.peek()
    
    def get_message_status(self, message_id: str) -> Optional[str]:
        """Get message status"""
        with self.lock:
            if message_id in self.processing:
                return "processing"
            elif message_id in self.delayed_queue:
                return "delayed"
            elif message_id in self.dead_letter_queue:
                return "dead_letter"
            else:
                # Check main queue
                return "queued"
    
    def get_dead_letter_messages(self, limit: int = 100) -> List[DeadLetterEntry]:
        """Get entries from dead letter queue"""
        with self.lock:
            return list(self.dead_letter_queue.values())[:limit]
    
    def retry_dead_letter_message(self, message_id: str) -> bool:
        """Retry message from DLQ"""
        with self.lock:
            if message_id not in self.dead_letter_queue:
                return False
            
            dlq_entry = self.dead_letter_queue.pop(message_id)
            message = dlq_entry.message
            message.state = MessageState.QUEUED
            message.retry_count = 0
            message.error_message = None
            
            self.queue.put(message)
            self.stats.failed_messages -= 1
            
            self._trigger_callback("dead_letter_retried", message_id)
            return True
    
    def register_consumer(self, consumer_id: str, max_concurrent: int = 1) -> QueueConsumer:
        """Register consumer"""
        with self.lock:
            consumer = QueueConsumer(
                consumer_id=consumer_id,
                queue_name=self.config.name,
                max_concurrent_messages=max_concurrent
            )
            self.consumers[consumer_id] = consumer
            return consumer
    
    def get_consumers(self) -> List[QueueConsumer]:
        """Get all consumers"""
        with self.lock:
            return list(self.consumers.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self.lock:
            return {
                "queue": self.config.name,
                "total_messages": self.stats.total_messages,
                "processed_messages": self.stats.processed_messages,
                "failed_messages": self.stats.failed_messages,
                "delayed_messages": self.stats.delayed_messages,
                "queue_depth": self.get_queue_depth(),
                "dead_letter_count": len(self.dead_letter_queue),
                "consumers": len(self.consumers),
                "error_rate": self.stats.error_rate,
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


class MessageQueueManager:
    """Manager for multiple message queues"""
    
    def __init__(self):
        self.queues: Dict[str, MessageQueue] = {}
        self.lock = threading.RLock()
        self.callbacks: List[Callable] = []
    
    def create_queue(self, config: QueueConfig) -> bool:
        """Create new queue"""
        with self.lock:
            if config.name in self.queues:
                return False
            
            self.queues[config.name] = MessageQueue(config)
            self._trigger_callback("queue_created", config.name)
            return True
    
    def get_queue(self, queue_name: str) -> Optional[MessageQueue]:
        """Get queue"""
        with self.lock:
            return self.queues.get(queue_name)
    
    def delete_queue(self, queue_name: str) -> bool:
        """Delete queue"""
        with self.lock:
            if queue_name not in self.queues:
                return False
            
            del self.queues[queue_name]
            self._trigger_callback("queue_deleted", queue_name)
            return True
    
    def list_queues(self) -> List[str]:
        """List all queues"""
        with self.lock:
            return list(self.queues.keys())
    
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
_queue_manager: Optional[MessageQueueManager] = None


def get_queue_manager() -> MessageQueueManager:
    """Get or create singleton queue manager"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = MessageQueueManager()
    return _queue_manager


def reset_queue_manager() -> None:
    """Reset queue manager (for testing)"""
    global _queue_manager
    _queue_manager = None
