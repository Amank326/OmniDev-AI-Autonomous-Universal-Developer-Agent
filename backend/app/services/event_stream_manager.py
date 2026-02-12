"""
Event Stream Manager - Central event broking and streaming platform
Provides unified interface for Kafka, RabbitMQ, and other event brokers
"""

import json
import time
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import hashlib


class StreamProvider(Enum):
    """Supported event stream providers"""
    KAFKA = "kafka"
    RABBITMQ = "rabbitmq"
    PUBSUB = "pubsub"
    KINESIS = "kinesis"
    IN_MEMORY = "in_memory"  # For testing/development


class MessageFormat(Enum):
    """Message encoding formats"""
    JSON = "json"
    PROTOBUF = "protobuf"
    AVRO = "avro"
    BINARY = "binary"
    STRING = "string"


class ConsumerModel(Enum):
    """Consumer delivery models"""
    AT_LEAST_ONCE = "at_least_once"
    AT_MOST_ONCE = "at_most_once"
    EXACTLY_ONCE = "exactly_once"


@dataclass
class StreamMessage:
    """Event message in stream"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    partition: int = 0
    offset: int = -1
    key: Optional[str] = None
    value: Any = None
    timestamp: float = field(default_factory=time.time)
    headers: Dict[str, str] = field(default_factory=dict)
    format: MessageFormat = MessageFormat.JSON
    schema_id: Optional[str] = None
    
    def to_bytes(self) -> bytes:
        """Serialize message to bytes"""
        if self.format == MessageFormat.JSON:
            data = {
                "message_id": self.message_id,
                "topic": self.topic,
                "key": self.key,
                "value": self.value,
                "timestamp": self.timestamp,
                "headers": self.headers,
            }
            return json.dumps(data).encode('utf-8')
        elif self.format == MessageFormat.STRING:
            return str(self.value).encode('utf-8')
        else:
            return bytes(self.value) if isinstance(self.value, bytes) else str(self.value).encode('utf-8')
    
    @classmethod
    def from_bytes(cls, data: bytes, topic: str, fmt: MessageFormat = MessageFormat.JSON) -> 'StreamMessage':
        """Deserialize message from bytes"""
        if fmt == MessageFormat.JSON:
            parsed = json.loads(data.decode('utf-8'))
            return cls(
                message_id=parsed.get("message_id", str(uuid.uuid4())),
                topic=topic,
                key=parsed.get("key"),
                value=parsed.get("value"),
                timestamp=parsed.get("timestamp", time.time()),
                headers=parsed.get("headers", {}),
                format=fmt
            )
        else:
            return cls(topic=topic, value=data, format=fmt)


@dataclass
class TopicConfig:
    """Topic configuration"""
    name: str
    partitions: int = 3
    replication_factor: int = 1
    retention_ms: int = 604800000  # 7 days
    compression_type: str = "snappy"
    min_in_sync_replicas: int = 1
    cleanup_policy: str = "delete"  # delete or compact
    segment_ms: int = 86400000  # 1 day
    max_message_bytes: int = 1048576  # 1 MB
    format: MessageFormat = MessageFormat.JSON


@dataclass
class ConsumerGroup:
    """Consumer group configuration"""
    group_id: str
    topic: str
    partitions: Set[int] = field(default_factory=set)
    consumer_model: ConsumerModel = ConsumerModel.AT_LEAST_ONCE
    max_poll_records: int = 500
    session_timeout_ms: int = 10000
    heartbeat_interval_ms: int = 3000
    max_poll_interval_ms: int = 300000
    created_at: float = field(default_factory=time.time)


@dataclass
class StreamIndex:
    """Indexing configuration for stream data"""
    index_name: str
    topic: str
    field_names: List[str]
    index_type: str = "hash"  # hash, btree, inverted
    ttl_seconds: Optional[int] = None


@dataclass
class StreamStatistics:
    """Stream performance statistics"""
    messages_published: int = 0
    messages_consumed: int = 0
    bytes_published: int = 0
    bytes_consumed: int = 0
    topics: int = 0
    consumer_groups: int = 0
    avg_message_size: float = 0.0
    publish_rate_mps: float = 0.0  # messages per second
    consume_rate_mps: float = 0.0
    avg_latency_ms: float = 0.0


class StreamPartition:
    """In-memory partition for message storage"""
    
    def __init__(self, partition_id: int, max_size: int = 10000):
        self.partition_id = partition_id
        self.messages: deque = deque(maxlen=max_size)
        self.offset = 0
        self.lock = threading.RLock()
    
    def append(self, message: StreamMessage) -> int:
        """Add message and return offset"""
        with self.lock:
            message.partition = self.partition_id
            message.offset = self.offset
            self.messages.append(message)
            self.offset += 1
            return self.offset - 1
    
    def get_messages(self, offset: int, limit: int = 100) -> List[StreamMessage]:
        """Get messages starting from offset"""
        with self.lock:
            if offset >= self.offset:
                return []
            
            start_idx = max(0, offset - (self.offset - len(self.messages)))
            return list(self.messages)[start_idx:start_idx + limit]
    
    def get_latest(self, limit: int = 100) -> List[StreamMessage]:
        """Get latest messages"""
        with self.lock:
            return list(self.messages)[-limit:] if self.messages else []


class StreamTopic:
    """Stream topic with partitions"""
    
    def __init__(self, config: TopicConfig):
        self.config = config
        self.partitions = {
            i: StreamPartition(i) for i in range(config.partitions)
        }
        self.offset_counter = 0
        self.created_at = time.time()
        self.lock = threading.RLock()
        self.indexes: Dict[str, StreamIndex] = {}
    
    def publish(self, message: StreamMessage, partition: Optional[int] = None) -> Tuple[int, int]:
        """Publish message to topic, returns (partition, offset)"""
        with self.lock:
            if partition is None:
                # Partition by key hash if exists
                if message.key:
                    partition = hash(message.key) % self.config.partitions
                else:
                    partition = self.offset_counter % self.config.partitions
                    self.offset_counter += 1
            
            partition = partition % len(self.partitions)
            offset = self.partitions[partition].append(message)
            return partition, offset
    
    def get_messages(self, partition: int, offset: int, limit: int = 100) -> List[StreamMessage]:
        """Get messages from partition"""
        if partition not in self.partitions:
            return []
        return self.partitions[partition].get_messages(offset, limit)
    
    def get_all_messages(self, limit: int = 1000) -> List[StreamMessage]:
        """Get messages from all partitions"""
        messages = []
        with self.lock:
            for partition in self.partitions.values():
                messages.extend(partition.get_latest(limit // len(self.partitions)))
        return sorted(messages, key=lambda m: m.timestamp)
    
    def create_index(self, index: StreamIndex) -> None:
        """Create searchable index"""
        with self.lock:
            self.indexes[index.index_name] = index
    
    def search_index(self, index_name: str, query: Dict[str, Any]) -> List[StreamMessage]:
        """Search using index"""
        if index_name not in self.indexes:
            return []
        
        results = []
        for messages in [p.get_latest(1000) for p in self.partitions.values()]:
            for msg in messages:
                if self._matches_query(msg, query):
                    results.append(msg)
        return results
    
    def _matches_query(self, message: StreamMessage, query: Dict[str, Any]) -> bool:
        """Check if message matches query"""
        if not isinstance(message.value, dict):
            return False
        
        for key, expected_value in query.items():
            if key not in message.value:
                return False
            if message.value[key] != expected_value:
                return False
        return True


class StreamConsumer:
    """Consumer for reading from topics"""
    
    def __init__(self, group: ConsumerGroup):
        self.group = group
        self.offsets: Dict[int, int] = defaultdict(int)  # partition -> offset
        self.lock = threading.RLock()
        self.callbacks: List[Callable] = []
        self.is_active = True
    
    def poll(self, topic: StreamTopic, max_records: int = 100) -> List[StreamMessage]:
        """Poll for messages"""
        messages = []
        with self.lock:
            for partition_id in self.group.partitions:
                if partition_id not in topic.partitions:
                    continue
                
                offset = self.offsets[partition_id]
                partition_messages = topic.get_messages(partition_id, offset, max_records)
                
                for msg in partition_messages:
                    messages.append(msg)
                    self.offsets[partition_id] = msg.offset + 1
        
        return messages
    
    def commit_offset(self, partition: int, offset: int) -> None:
        """Commit consumed offset"""
        with self.lock:
            self.offsets[partition] = offset + 1
    
    def seek_offset(self, partition: int, offset: int) -> None:
        """Seek to specific offset"""
        with self.lock:
            self.offsets[partition] = offset
    
    def seek_beginning(self) -> None:
        """Seek to beginning of all partitions"""
        with self.lock:
            for partition in self.group.partitions:
                self.offsets[partition] = 0
    
    def assign_partitions(self, partitions: Set[int]) -> None:
        """Assign partitions to consumer"""
        with self.lock:
            self.group.partitions = partitions
            for p in partitions:
                if p not in self.offsets:
                    self.offsets[p] = 0
    
    def register_callback(self, callback: Callable[[List[StreamMessage]], None]) -> None:
        """Register message callback"""
        with self.lock:
            self.callbacks.append(callback)


class EventStreamManager:
    """Central event stream manager"""
    
    def __init__(self, provider: StreamProvider = StreamProvider.IN_MEMORY):
        self.provider = provider
        self.topics: Dict[str, StreamTopic] = {}
        self.consumer_groups: Dict[str, StreamConsumer] = {}
        self.subscriptions: Dict[str, List[Callable]] = defaultdict(list)
        self.stats = StreamStatistics()
        self.lock = threading.RLock()
        self.callbacks: List[Callable] = []
        
        # Message deduplication
        self.seen_messages: Set[str] = set()
        self.dedup_window_size = 10000
    
    def create_topic(self, config: TopicConfig) -> bool:
        """Create new topic"""
        with self.lock:
            if config.name in self.topics:
                return False
            
            self.topics[config.name] = StreamTopic(config)
            self.stats.topics += 1
            self._trigger_callback("topic_created", config.name, config)
            return True
    
    def delete_topic(self, topic_name: str) -> bool:
        """Delete topic"""
        with self.lock:
            if topic_name not in self.topics:
                return False
            
            del self.topics[topic_name]
            self.stats.topics -= 1
            self._trigger_callback("topic_deleted", topic_name)
            return True
    
    def get_topic(self, topic_name: str) -> Optional[StreamTopic]:
        """Get topic"""
        with self.lock:
            return self.topics.get(topic_name)
    
    def list_topics(self) -> List[str]:
        """List all topics"""
        with self.lock:
            return list(self.topics.keys())
    
    def publish(self, topic_name: str, message: StreamMessage,
               partition: Optional[int] = None) -> Optional[Tuple[int, int]]:
        """Publish message to topic"""
        with self.lock:
            if topic_name not in self.topics:
                return None
            
            # Deduplication check
            msg_hash = hashlib.md5(message.to_bytes()).hexdigest()
            if msg_hash in self.seen_messages:
                return None
            
            self._manage_dedup_window(msg_hash)
            
            message.topic = topic_name
            topic = self.topics[topic_name]
            partition_id, offset = topic.publish(message, partition)
            
            self.stats.messages_published += 1
            self.stats.bytes_published += len(message.to_bytes())
            
            # Trigger subscriptions
            for callback in self.subscriptions[topic_name]:
                try:
                    callback(message)
                except Exception:
                    pass
            
            self._trigger_callback("message_published", topic_name, partition_id, offset)
            return partition_id, offset
    
    def _manage_dedup_window(self, msg_hash: str) -> None:
        """Manage deduplication window size"""
        self.seen_messages.add(msg_hash)
        if len(self.seen_messages) > self.dedup_window_size:
            # Remove oldest by clearing and starting fresh
            self.seen_messages.clear()
    
    def publish_batch(self, topic_name: str, messages: List[StreamMessage]) -> List[Tuple[int, int]]:
        """Publish multiple messages"""
        results = []
        for msg in messages:
            result = self.publish(topic_name, msg)
            if result:
                results.append(result)
        return results
    
    def subscribe(self, topic_name: str, callback: Callable[[StreamMessage], None]) -> str:
        """Subscribe to topic"""
        with self.lock:
            sub_id = str(uuid.uuid4())
            self.subscriptions[topic_name].append(callback)
            self._trigger_callback("subscription_created", topic_name, sub_id)
            return sub_id
    
    def unsubscribe(self, topic_name: str, callback: Callable) -> bool:
        """Unsubscribe from topic"""
        with self.lock:
            if callback in self.subscriptions[topic_name]:
                self.subscriptions[topic_name].remove(callback)
                return True
            return False
    
    # Consumer group management
    def create_consumer_group(self, group_config: ConsumerGroup) -> bool:
        """Create consumer group"""
        with self.lock:
            if group_config.group_id in self.consumer_groups:
                return False
            
            topic = self.topics.get(group_config.topic)
            if not topic:
                return False
            
            # Auto-assign partitions round-robin
            group_config.partitions = set(range(topic.config.partitions))
            
            consumer = StreamConsumer(group_config)
            self.consumer_groups[group_config.group_id] = consumer
            self.stats.consumer_groups += 1
            
            self._trigger_callback("consumer_group_created", group_config.group_id)
            return True
    
    def get_consumer_group(self, group_id: str) -> Optional[StreamConsumer]:
        """Get consumer group"""
        with self.lock:
            return self.consumer_groups.get(group_id)
    
    def delete_consumer_group(self, group_id: str) -> bool:
        """Delete consumer group"""
        with self.lock:
            if group_id not in self.consumer_groups:
                return False
            
            del self.consumer_groups[group_id]
            self.stats.consumer_groups -= 1
            self._trigger_callback("consumer_group_deleted", group_id)
            return True
    
    def poll_messages(self, group_id: str, max_records: int = 100) -> List[StreamMessage]:
        """Poll messages for consumer group"""
        consumer = self.get_consumer_group(group_id)
        if not consumer:
            return []
        
        topic = self.topics.get(consumer.group.topic)
        if not topic:
            return []
        
        messages = consumer.poll(topic, max_records)
        self.stats.messages_consumed += len(messages)
        self.stats.bytes_consumed += sum(len(m.to_bytes()) for m in messages)
        
        self._trigger_callback("messages_polled", group_id, len(messages))
        return messages
    
    def commit_offsets(self, group_id: str, offsets: Dict[int, int]) -> bool:
        """Commit offsets for consumer group"""
        consumer = self.get_consumer_group(group_id)
        if not consumer:
            return False
        
        for partition, offset in offsets.items():
            consumer.commit_offset(partition, offset)
        
        return True
    
    # Querying interface
    def read_topic(self, topic_name: str, partition: int, offset: int,
                  limit: int = 100) -> List[StreamMessage]:
        """Read messages from topic partition"""
        topic = self.get_topic(topic_name)
        if not topic:
            return []
        
        return topic.get_messages(partition, offset, limit)
    
    def get_latest_messages(self, topic_name: str, limit: int = 100) -> List[StreamMessage]:
        """Get latest messages from all partitions"""
        topic = self.get_topic(topic_name)
        if not topic:
            return []
        
        return topic.get_all_messages(limit)
    
    def search_messages(self, topic_name: str, query: Dict[str, Any]) -> List[StreamMessage]:
        """Search messages in topic"""
        topic = self.get_topic(topic_name)
        if not topic:
            return []
        
        results = []
        for partition in topic.partitions.values():
            for msg in partition.get_latest(1000):
                if isinstance(msg.value, dict) and all(
                    k in msg.value and msg.value[k] == v for k, v in query.items()
                ):
                    results.append(msg)
        
        return results
    
    def create_index(self, topic_name: str, index: StreamIndex) -> bool:
        """Create index on topic"""
        topic = self.get_topic(topic_name)
        if not topic:
            return False
        
        topic.create_index(index)
        self._trigger_callback("index_created", topic_name, index.index_name)
        return True
    
    # Monitoring and metrics
    def get_topic_stats(self, topic_name: str) -> Optional[Dict[str, Any]]:
        """Get topic statistics"""
        topic = self.get_topic(topic_name)
        if not topic:
            return None
        
        total_messages = sum(len(p.messages) for p in topic.partitions.values())
        total_bytes = sum(sum(len(m.to_bytes()) for m in p.messages) 
                         for p in topic.partitions.values())
        
        return {
            "topic": topic_name,
            "partitions": len(topic.partitions),
            "messages": total_messages,
            "bytes": total_bytes,
            "avg_message_size": total_bytes / total_messages if total_messages > 0 else 0,
            "created_at": topic.created_at,
        }
    
    def get_consumer_group_lag(self, group_id: str) -> Optional[Dict[int, int]]:
        """Get consumer group lag per partition"""
        consumer = self.get_consumer_group(group_id)
        if not consumer:
            return None
        
        topic = self.topics.get(consumer.group.topic)
        if not topic:
            return None
        
        lag = {}
        for partition_id in consumer.group.partitions:
            if partition_id not in topic.partitions:
                continue
            
            current_offset = consumer.offsets.get(partition_id, 0)
            latest_offset = topic.partitions[partition_id].offset
            lag[partition_id] = latest_offset - current_offset
        
        return lag
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        with self.lock:
            total_messages = self.stats.messages_published + self.stats.messages_consumed
            total_bytes = self.stats.bytes_published + self.stats.bytes_consumed
            
            return {
                "messages_published": self.stats.messages_published,
                "messages_consumed": self.stats.messages_consumed,
                "total_messages": total_messages,
                "bytes_published": self.stats.bytes_published,
                "bytes_consumed": self.stats.bytes_consumed,
                "total_bytes": total_bytes,
                "topics": self.stats.topics,
                "consumer_groups": self.stats.consumer_groups,
                "avg_message_size": total_bytes / total_messages if total_messages > 0 else 0,
                "subscriptions": sum(len(subs) for subs in self.subscriptions.values()),
                "dedup_window_size": len(self.seen_messages),
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
    
    def flush(self) -> None:
        """Flush all buffers"""
        with self.lock:
            for topic in self.topics.values():
                for partition in topic.partitions.values():
                    # Clear old messages
                    if len(partition.messages) > 5000:
                        while len(partition.messages) > 3000:
                            partition.messages.popleft()


# Singleton instance
_stream_manager: Optional[EventStreamManager] = None


def get_stream_manager(provider: StreamProvider = StreamProvider.IN_MEMORY) -> EventStreamManager:
    """Get or create singleton stream manager"""
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = EventStreamManager(provider)
    return _stream_manager


def reset_stream_manager() -> None:
    """Reset stream manager (for testing)"""
    global _stream_manager
    _stream_manager = None
