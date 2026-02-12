"""
Embedding Engine Service
Converts text and data into vector embeddings using multiple models and strategies.
Supports batching, caching, dimension handling, and pooling strategies.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Tuple
import threading
import uuid
import time
from collections import deque
import hashlib
import json
import numpy as np
from datetime import datetime, timedelta


class EmbeddingModel(Enum):
    """Available embedding models"""
    SENTENCE_BERT_SMALL = "sentence-bert-small"
    SENTENCE_BERT_BASE = "sentence-bert-base"
    SENTENCE_BERT_LARGE = "sentence-bert-large"
    MULTILINGUAL_BERT = "multilingual-bert"
    OPENAI_ADA = "openai-ada"
    OPENAI_3_SMALL = "openai-3-small"
    OPENAI_3_LARGE = "openai-3-large"
    CUSTOM_FINE_TUNED = "custom-fine-tuned"


class PoolingStrategy(Enum):
    """Pooling strategies for sequence embeddings"""
    MEAN = "mean"
    MAX = "max"
    CLS_TOKEN = "cls_token"
    LAST_HIDDEN = "last_hidden"
    ATTENTION_WEIGHTED = "attention_weighted"
    WEIGHTED_MEAN = "weighted_mean"


class NormalizationMethod(Enum):
    """Embedding normalization methods"""
    L2 = "l2"
    L1 = "l1"
    UNIT_VARIANCE = "unit_variance"
    NONE = "none"
    ZERO_MEAN = "zero_mean"


class EmbeddingContentType(Enum):
    """Type of content being embedded"""
    TEXT = "text"
    DOCUMENT = "document"
    CODE = "code"
    IMAGE_DESCRIPTION = "image_description"
    AUDIO_TRANSCRIPT = "audio_transcript"
    QUERY = "query"
    SEMANTIC_CHUNK = "semantic_chunk"
    STRUCTURED_DATA = "structured_data"


class DimensionHandling(Enum):
    """Methods for handling dimension mismatches"""
    TRUNCATE = "truncate"
    PAD_ZEROS = "pad_zeros"
    INTERPOLATE = "interpolate"
    PRINCIPAL_COMPONENTS = "principal_components"


@dataclass
class EmbeddingConfig:
    """Configuration for embedding engine"""
    model: EmbeddingModel = EmbeddingModel.SENTENCE_BERT_BASE
    dimension: int = 384
    pooling_strategy: PoolingStrategy = PoolingStrategy.MEAN
    normalization: NormalizationMethod = NormalizationMethod.L2
    batch_size: int = 32
    max_sequence_length: int = 512
    cache_enabled: bool = True
    cache_ttl_hours: float = 24.0
    precision: str = "float32"
    include_metadata: bool = True
    timeout_seconds: int = 60


@dataclass
class Embedding:
    """Individual embedding representation"""
    embedding_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vector: List[float] = field(default_factory=list)
    dimension: int = 0
    content_type: EmbeddingContentType = EmbeddingContentType.TEXT
    source_text: str = ""
    source_hash: str = ""
    model_used: str = ""
    pooling_strategy: str = ""
    normalization_method: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "embedding_id": self.embedding_id,
            "vector": self.vector,
            "dimension": self.dimension,
            "content_type": self.content_type.value,
            "model_used": self.model_used,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class BatchEmbeddingRequest:
    """Batch embedding request"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    texts: List[str] = field(default_factory=list)
    content_types: List[EmbeddingContentType] = field(default_factory=list)
    metadata_list: List[Dict[str, Any]] = field(default_factory=list)
    priority: int = 0
    timeout_seconds: int = 60


@dataclass
class EmbeddingBatch:
    """Result of batch embedding"""
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    embeddings: List[Embedding] = field(default_factory=list)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0
    total_texts: int = 0
    successful_embeddings: int = 0


@dataclass
class EmbeddingModelMetrics:
    """Metrics for embedding model"""
    model_name: str = ""
    embeddings_generated: int = 0
    total_processing_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    failed_embeddings: int = 0
    avg_latency_ms: float = 0.0


@dataclass
class CacheEntry:
    """Cache entry for embeddings"""
    embedding: Embedding
    created_at: datetime = field(default_factory=datetime.utcnow)
    ttl_hours: float = 24.0
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        expiry_time = self.created_at + timedelta(hours=self.ttl_hours)
        return datetime.utcnow() > expiry_time


class EmbeddingEngine:
    """Main embedding generation and management service"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.config = EmbeddingConfig()
        self.embedding_cache: Dict[str, CacheEntry] = {}
        self.model_instances: Dict[str, Any] = {}
        self.embedding_history: deque = deque(maxlen=10000)
        self.batch_queue: deque = deque()
        self.metrics: Dict[str, EmbeddingModelMetrics] = {}
        self.callbacks: List[Callable] = []
        self._lock = threading.RLock()
        self.background_thread = None
        self.running = False

    def configure(self, config: EmbeddingConfig) -> None:
        """Configure embedding engine"""
        with self._lock:
            self.config = config
            if config.model.value not in self.metrics:
                self.metrics[config.model.value] = EmbeddingModelMetrics(
                    model_name=config.model.value
                )

    def start(self) -> None:
        """Start background worker threads"""
        if not self.running:
            self.running = True
            self.background_thread = threading.Thread(
                target=self._background_worker,
                daemon=True
            )
            self.background_thread.start()

    def stop(self) -> None:
        """Stop background worker"""
        self.running = False
        if self.background_thread:
            self.background_thread.join(timeout=5)

    def _background_worker(self) -> None:
        """Background worker for processing and cache cleanup"""
        while self.running:
            try:
                # Process batch queue if available
                if len(self.batch_queue) > 0:
                    batch_request = self.batch_queue.popleft()
                    self._process_batch(batch_request)

                # Clean expired cache entries
                with self._lock:
                    expired_keys = [
                        k for k, v in self.embedding_cache.items()
                        if v.is_expired()
                    ]
                    for key in expired_keys:
                        del self.embedding_cache[key]

                time.sleep(1)
            except Exception as e:
                self._trigger_callback({"error": str(e), "type": "background_worker_error"})

    def _process_batch(self, batch_request: BatchEmbeddingRequest) -> None:
        """Process batch embedding request"""
        start_time = time.time()
        batch = EmbeddingBatch(batch_id=batch_request.request_id)

        for i, text in enumerate(batch_request.texts):
            content_type = batch_request.content_types[i] if i < len(batch_request.content_types) else EmbeddingContentType.TEXT
            metadata = batch_request.metadata_list[i] if i < len(batch_request.metadata_list) else {}

            embedding = self.create_embedding(
                text=text,
                content_type=content_type,
                metadata=metadata
            )
            if embedding:
                batch.embeddings.append(embedding)
                batch.successful_embeddings += 1

        batch.total_texts = len(batch_request.texts)
        batch.processing_time_ms = (time.time() - start_time) * 1000
        batch.status = "completed"

        # Store in history
        with self._lock:
            self.embedding_history.append(batch)

        self._trigger_callback({"type": "batch_completed", "batch_id": batch.batch_id})

    def create_embedding(
        self,
        text: str,
        content_type: EmbeddingContentType = EmbeddingContentType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Embedding]:
        """Create single embedding"""
        if not text or len(text.strip()) == 0:
            return None

        # Check cache
        text_hash = self._hash_text(text)
        if self.config.cache_enabled:
            cached = self._get_cached_embedding(text_hash)
            if cached:
                return cached

        try:
            # Generate embedding vector
            vector = self._generate_vector(text)
            if not vector:
                return None

            # Apply normalization
            normalized_vector = self._apply_normalization(vector)

            # Create embedding
            embedding = Embedding(
                vector=normalized_vector,
                dimension=len(normalized_vector),
                content_type=content_type,
                source_text=text[:200],
                source_hash=text_hash,
                model_used=self.config.model.value,
                pooling_strategy=self.config.pooling_strategy.value,
                normalization_method=self.config.normalization.value,
                metadata=metadata or {}
            )

            # Cache it
            if self.config.cache_enabled:
                with self._lock:
                    self.embedding_cache[text_hash] = CacheEntry(
                        embedding=embedding,
                        ttl_hours=self.config.cache_ttl_hours
                    )

            # Update metrics
            self._update_metrics(text)

            # Store in history
            with self._lock:
                self.embedding_history.append(embedding)

            return embedding

        except Exception as e:
            self._trigger_callback({"error": str(e), "type": "embedding_generation_error"})
            self._update_failed_metric()
            return None

    def batch_embed(
        self,
        texts: List[str],
        content_types: Optional[List[EmbeddingContentType]] = None,
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        priority: int = 0
    ) -> str:
        """Queue batch embedding request"""
        if not texts:
            return ""

        if content_types is None:
            content_types = [EmbeddingContentType.TEXT] * len(texts)

        if metadata_list is None:
            metadata_list = [{} for _ in texts]

        batch_request = BatchEmbeddingRequest(
            texts=texts,
            content_types=content_types,
            metadata_list=metadata_list,
            priority=priority
        )

        with self._lock:
            self.batch_queue.append(batch_request)

        return batch_request.request_id

    def _generate_vector(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector - simulated version"""
        # In production, this would call actual embedding model
        # For now, generate consistent pseudo-random vector from text hash
        text_bytes = text.encode('utf-8')
        hash_obj = hashlib.sha256(text_bytes)

        # Generate deterministic vector from hash
        vector = []
        hash_hex = hash_obj.hexdigest()

        for i in range(self.config.dimension):
            # Use hash to generate pseudo-random values
            chunk = hash_hex[(i * 8) % len(hash_hex):(i * 8 + 8) % len(hash_hex)]
            if len(chunk) < 8:
                chunk = chunk + hash_hex[:8-len(chunk)]
            value = int(chunk, 16) % 1000 / 1000.0  # 0-1 range
            value = (value - 0.5) * 2  # -1 to 1 range
            vector.append(value)

        return vector

    def _apply_normalization(self, vector: List[float]) -> List[float]:
        """Apply normalization to vector"""
        if self.config.normalization == NormalizationMethod.NONE:
            return vector

        vec_array = np.array(vector)

        if self.config.normalization == NormalizationMethod.L2:
            norm = np.linalg.norm(vec_array)
            if norm > 0:
                vec_array = vec_array / norm

        elif self.config.normalization == NormalizationMethod.L1:
            norm = np.sum(np.abs(vec_array))
            if norm > 0:
                vec_array = vec_array / norm

        elif self.config.normalization == NormalizationMethod.UNIT_VARIANCE:
            vec_array = (vec_array - np.mean(vec_array)) / (np.std(vec_array) + 1e-8)

        elif self.config.normalization == NormalizationMethod.ZERO_MEAN:
            vec_array = vec_array - np.mean(vec_array)

        return vec_array.tolist()

    def _hash_text(self, text: str) -> str:
        """Hash text for cache key"""
        return hashlib.md5(text.encode()).hexdigest()

    def _get_cached_embedding(self, text_hash: str) -> Optional[Embedding]:
        """Retrieve cached embedding"""
        with self._lock:
            if text_hash in self.embedding_cache:
                entry = self.embedding_cache[text_hash]
                if not entry.is_expired():
                    entry.access_count += 1
                    entry.last_accessed = datetime.utcnow()

                    model_name = self.config.model.value
                    if model_name in self.metrics:
                        self.metrics[model_name].cache_hits += 1

                    return entry.embedding
                else:
                    del self.embedding_cache[text_hash]
        return None

    def _update_metrics(self, text: str) -> None:
        """Update generation metrics"""
        with self._lock:
            model_name = self.config.model.value
            if model_name not in self.metrics:
                self.metrics[model_name] = EmbeddingModelMetrics(model_name=model_name)

            metric = self.metrics[model_name]
            metric.embeddings_generated += 1
            metric.cache_misses += 1

    def _update_failed_metric(self) -> None:
        """Update failed embedding metric"""
        with self._lock:
            model_name = self.config.model.value
            if model_name in self.metrics:
                self.metrics[model_name].failed_embeddings += 1

    def resize_embedding(
        self,
        embedding: Embedding,
        target_dimension: int,
        method: DimensionHandling = DimensionHandling.TRUNCATE
    ) -> Embedding:
        """Resize embedding to different dimension"""
        vector = embedding.vector
        current_dim = len(vector)

        if current_dim == target_dimension:
            return embedding

        new_vector = vector.copy()

        if method == DimensionHandling.TRUNCATE:
            new_vector = vector[:target_dimension]

        elif method == DimensionHandling.PAD_ZEROS:
            if target_dimension > current_dim:
                new_vector = vector + [0.0] * (target_dimension - current_dim)
            else:
                new_vector = vector[:target_dimension]

        elif method == DimensionHandling.INTERPOLATE:
            new_vector = self._interpolate_vector(vector, target_dimension)

        elif method == DimensionHandling.PRINCIPAL_COMPONENTS:
            new_vector = self._pca_reduce(vector, target_dimension)

        resized = Embedding(
            vector=new_vector,
            dimension=target_dimension,
            content_type=embedding.content_type,
            source_text=embedding.source_text,
            model_used=embedding.model_used,
            metadata=embedding.metadata
        )
        return resized

    def _interpolate_vector(self, vector: List[float], target_dim: int) -> List[float]:
        """Interpolate vector to target dimension"""
        if not vector or target_dim <= 0:
            return [0.0] * target_dim

        indices = np.linspace(0, len(vector) - 1, target_dim)
        interpolated = np.interp(indices, np.arange(len(vector)), vector)
        return interpolated.tolist()

    def _pca_reduce(self, vector: List[float], target_dim: int) -> List[float]:
        """PCA reduction for dimension reduction"""
        # Simplified PCA - in production use sklearn
        vec_array = np.array(vector)
        if target_dim >= len(vector):
            return vector

        # Center the data
        centered = vec_array - np.mean(vec_array)

        # Compute covariance (simplified)
        cov = np.outer(centered, centered)

        # Simple truncation of least important components
        return vec_array[:target_dim].tolist()

    def get_embedding_statistics(self) -> Dict[str, Any]:
        """Get embedding engine statistics"""
        with self._lock:
            total_embeddings = len(self.embedding_history)
            cache_size = len(self.embedding_cache)

            return {
                "total_embeddings_generated": total_embeddings,
                "cache_size": cache_size,
                "models_metrics": {
                    name: {
                        "embeddings_generated": m.embeddings_generated,
                        "cache_hits": m.cache_hits,
                        "cache_misses": m.cache_misses,
                        "failed_embeddings": m.failed_embeddings,
                        "hit_rate": m.cache_hits / max(1, m.cache_hits + m.cache_misses)
                    }
                    for name, m in self.metrics.items()
                },
                "batch_queue_size": len(self.batch_queue),
                "cache_enabled": self.config.cache_enabled,
                "model": self.config.model.value,
                "dimension": self.config.dimension
            }

    def clear_cache(self) -> int:
        """Clear embedding cache"""
        with self._lock:
            count = len(self.embedding_cache)
            self.embedding_cache.clear()
        return count

    def get_recent_embeddings(self, limit: int = 100) -> List[Embedding]:
        """Get recently created embeddings"""
        with self._lock:
            return list(self.embedding_history)[-limit:]

    def register_callback(self, callback: Callable) -> None:
        """Register callback for embedding events"""
        with self._lock:
            if callback not in self.callbacks:
                self.callbacks.append(callback)

    def unregister_callback(self, callback: Callable) -> None:
        """Unregister callback"""
        with self._lock:
            if callback in self.callbacks:
                self.callbacks.remove(callback)

    def _trigger_callback(self, event: Dict[str, Any]) -> None:
        """Trigger registered callbacks"""
        with self._lock:
            callbacks = self.callbacks.copy()

        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                pass

    def compute_similarity(self, embedding1: Embedding, embedding2: Embedding) -> float:
        """Compute cosine similarity between embeddings"""
        if len(embedding1.vector) != len(embedding2.vector):
            return 0.0

        vec1 = np.array(embedding1.vector)
        vec2 = np.array(embedding2.vector)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def get_embedding_by_id(self, embedding_id: str) -> Optional[Embedding]:
        """Retrieve embedding by ID from history"""
        with self._lock:
            for emb in self.embedding_history:
                if emb.embedding_id == embedding_id:
                    return emb
        return None

    def find_similar_embeddings(
        self,
        query_embedding: Embedding,
        top_k: int = 10,
        min_similarity: float = 0.0
    ) -> List[Tuple[Embedding, float]]:
        """Find similar embeddings in history"""
        similarities = []

        with self._lock:
            for emb in self.embedding_history:
                similarity = self.compute_similarity(query_embedding, emb)
                if similarity >= min_similarity:
                    similarities.append((emb, similarity))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
