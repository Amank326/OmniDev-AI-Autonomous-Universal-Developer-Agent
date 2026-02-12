"""
Embeddings Service - Text to Vector Conversion
Handles generating and managing embeddings for semantic search and RAG.
"""

from abc import ABC, abstractmethod
from collections import deque, OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Dict, List, Optional, Tuple, Any, Callable
import hashlib
import time
import numpy as np
from datetime import datetime


class EmbeddingModel(Enum):
    """Supported embedding models."""
    OPENAI_ADA = "text-embedding-ada-002"
    OPENAI_3_SMALL = "text-embedding-3-small"
    OPENAI_3_LARGE = "text-embedding-3-large"
    SENTENCE_BERT = "sentence-bert"
    COHERE = "cohere"
    HUGGINGFACE_DISTILBERT = "distilbert-base-uncased"
    HUGGINGFACE_MINILM = "minilm-l6-v2"
    BAAI_BGE_SMALL = "bge-small-en-v1.5"
    BAAI_BGE_LARGE = "bge-large-en-v1.5"
    JINA_AI = "jina-ai-embeddings-v3"


class EmbeddingDimension(Enum):
    """Embedding dimensions by model."""
    SMALL = 384      # For fast models like MiniLM
    MEDIUM = 768     # For medium models like DistilBERT, Cohere
    LARGE = 1024     # For larger models
    XLARGE = 1536    # For OpenAI ada and 3-small
    XXLARGE = 3072   # For OpenAI 3-large


class NormalizationMethod(Enum):
    """Vector normalization strategies."""
    NONE = "none"
    L2 = "l2"          # Euclidean normalization
    L1 = "l1"          # Manhattan normalization
    COSINE = "cosine"  # Cosine normalization (unit norm)
    MINMAX = "minmax"  # Min-max normalization to [0, 1]


class SimilarityMetric(Enum):
    """Distance/similarity metrics for embeddings."""
    COSINE = "cosine"      # Cosine similarity
    EUCLIDEAN = "euclidean" # L2 distance
    MANHATTAN = "manhattan" # L1 distance
    DOT_PRODUCT = "dot_product"  # Dot product
    CHEBYSHEV = "chebyshev" # Max distance


class QuantizationType(Enum):
    """Vector quantization strategies."""
    FLOAT32 = "float32"     # Full precision
    FLOAT16 = "float16"     # Half precision
    INT8 = "int8"           # 8-bit quantization
    BINARY = "binary"       # 1-bit quantization


@dataclass
class Embedding:
    """Single embedding vector."""
    text_id: str
    text: str
    vector: List[float]
    model: EmbeddingModel
    dimension: int
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    normalized: bool = False
    quantized: bool = False


@dataclass
class EmbeddingBatch:
    """Batch of embeddings."""
    batch_id: str
    embeddings: List[Embedding]
    created_at: float = field(default_factory=time.time)
    status: str = "pending"  # pending, processing, completed, failed
    error: Optional[str] = None


@dataclass
class EmbeddingModel_Config:
    """Configuration for embedding model."""
    model: EmbeddingModel
    dimension: EmbeddingDimension
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    batch_size: int = 32
    max_input_length: int = 8192
    timeout_seconds: int = 30
    normalize: NormalizationMethod = NormalizationMethod.L2
    quantization: QuantizationType = QuantizationType.FLOAT32
    cache_embeddings: bool = True


@dataclass
class EmbeddingCache_Config:
    """Configuration for embedding cache."""
    max_cache_size: int = 100000
    ttl_seconds: int = 86400  # 24 hours
    enable_l1_memory: bool = True
    enable_l2_disk: bool = True
    l1_max_size: int = 10000
    l2_path: str = "./embedding_cache"


@dataclass
class EmbeddingSimilarity:
    """Result of similarity comparison."""
    text_id_1: str
    text_id_2: str
    similarity_score: float
    metric: SimilarityMetric
    timestamp: float = field(default_factory=time.time)


@dataclass
class DimensionalityReduction:
    """Dimensionality reduction configuration."""
    method: str  # pca, tsne, umap
    target_dimensions: int = 2
    preserves_distance: bool = False
    computation_time_ms: float = 0.0


class EmbeddingsService:
    """Service for generating and managing text embeddings."""

    def __init__(self):
        """Initialize embeddings service."""
        self._lock = RLock()
        self._models: Dict[str, EmbeddingModel_Config] = {}
        self._embeddings: Dict[str, Embedding] = {}
        self._embedding_cache: OrderedDict = OrderedDict()  # LRU cache
        self._batches: Dict[str, EmbeddingBatch] = {}
        self._similarity_cache: Dict[str, float] = {}
        self._model_stats: Dict[str, Dict[str, int]] = {}
        self._text_to_embeddings: Dict[str, str] = {}  # text hash to embedding id
        self._cache_config = EmbeddingCache_Config()
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            'embedding_generated': [],
            'batch_processed': [],
            'cache_hit': [],
            'cache_miss': [],
            'model_registered': [],
        }
        
        # Statistics
        self._stats = {
            'total_embeddings_generated': 0,
            'total_tokens_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'batches_processed': 0,
            'avg_generation_time_ms': 0.0,
        }

    def register_model(self, model_config: EmbeddingModel_Config) -> bool:
        """Register a new embedding model."""
        with self._lock:
            model_name = model_config.model.value
            self._models[model_name] = model_config
            self._model_stats[model_name] = {
                'embeddings_count': 0,
                'avg_time_ms': 0.0,
                'errors': 0,
            }
            self._trigger_callback('model_registered', model_name=model_name)
            return True

    def get_model(self, model: EmbeddingModel) -> Optional[EmbeddingModel_Config]:
        """Get registered model configuration."""
        with self._lock:
            return self._models.get(model.value)

    def generate_embedding(
        self,
        text: str,
        text_id: Optional[str] = None,
        model: EmbeddingModel = EmbeddingModel.SENTENCE_BERT,
        metadata: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Optional[Embedding]:
        """Generate embedding for text."""
        with self._lock:
            if not text:
                return None

            # Generate text ID if not provided
            if not text_id:
                text_id = hashlib.sha256(text.encode()).hexdigest()[:16]

            # Check cache
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if use_cache and text_hash in self._text_to_embeddings:
                cached_id = self._text_to_embeddings[text_hash]
                if cached_id in self._embeddings:
                    self._stats['cache_hits'] += 1
                    self._trigger_callback('cache_hit', text_id=text_id)
                    return self._embeddings[cached_id]

            # Generate embedding (mock)
            vector = self._mock_generate_vector(text, model)
            
            embedding = Embedding(
                text_id=text_id,
                text=text,
                vector=vector,
                model=model,
                dimension=len(vector),
                metadata=metadata or {},
            )

            self._embeddings[text_id] = embedding
            self._text_to_embeddings[text_hash] = text_id
            self._embedding_cache[text_id] = embedding
            
            # Maintain cache size
            if len(self._embedding_cache) > self._cache_config.max_cache_size:
                evicted_id, _ = self._embedding_cache.popitem(last=False)
                del self._embeddings[evicted_id]

            self._stats['cache_misses'] += 1
            self._stats['total_embeddings_generated'] += 1
            self._trigger_callback('embedding_generated', text_id=text_id, model=model.value)
            
            return embedding

    def batch_generate_embeddings(
        self,
        texts: List[str],
        model: EmbeddingModel = EmbeddingModel.SENTENCE_BERT,
        batch_size: int = 32,
    ) -> Optional[EmbeddingBatch]:
        """Generate embeddings for multiple texts."""
        with self._lock:
            if not texts:
                return None

            batch_id = hashlib.sha256(
                f"{time.time()}_{len(texts)}".encode()
            ).hexdigest()[:16]
            
            batch = EmbeddingBatch(batch_id=batch_id, embeddings=[])

            for i, text in enumerate(texts):
                embedding = self.generate_embedding(
                    text=text,
                    text_id=f"{batch_id}_{i}",
                    model=model,
                    use_cache=False,  # Process all in batch
                )
                if embedding:
                    batch.embeddings.append(embedding)

            batch.status = "completed"
            self._batches[batch_id] = batch
            self._stats['batches_processed'] += 1
            self._trigger_callback('batch_processed', batch_id=batch_id, count=len(batch.embeddings))
            
            return batch

    def normalize_embedding(
        self,
        embedding: Embedding,
        method: NormalizationMethod = NormalizationMethod.L2,
    ) -> Optional[Embedding]:
        """Normalize embedding vector."""
        with self._lock:
            if not embedding:
                return None

            vector = np.array(embedding.vector, dtype=np.float32)

            if method == NormalizationMethod.L2:
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
            elif method == NormalizationMethod.L1:
                norm = np.sum(np.abs(vector))
                if norm > 0:
                    vector = vector / norm
            elif method == NormalizationMethod.COSINE:
                vector = vector / (np.linalg.norm(vector) + 1e-8)
            elif method == NormalizationMethod.MINMAX:
                min_val = np.min(vector)
                max_val = np.max(vector)
                if max_val > min_val:
                    vector = (vector - min_val) / (max_val - min_val)

            embedding.vector = vector.tolist()
            embedding.normalized = True
            return embedding

    def quantize_embedding(
        self,
        embedding: Embedding,
        quantization_type: QuantizationType = QuantizationType.INT8,
    ) -> Optional[Embedding]:
        """Quantize embedding to reduce memory."""
        with self._lock:
            if not embedding:
                return None

            vector = np.array(embedding.vector, dtype=np.float32)

            if quantization_type == QuantizationType.FLOAT32:
                pass  # Already float32
            elif quantization_type == QuantizationType.FLOAT16:
                vector = vector.astype(np.float16)
            elif quantization_type == QuantizationType.INT8:
                # Scale to [-128, 127]
                v_min = np.min(vector)
                v_max = np.max(vector)
                if v_max > v_min:
                    vector = ((vector - v_min) / (v_max - v_min) * 255 - 128).astype(np.int8)
            elif quantization_type == QuantizationType.BINARY:
                # Binarize: > 0 = 1, else 0
                vector = (vector > 0).astype(np.uint8)

            embedding.vector = vector.tolist()
            embedding.quantized = True
            return embedding

    def compute_similarity(
        self,
        embedding_id_1: str,
        embedding_id_2: str,
        metric: SimilarityMetric = SimilarityMetric.COSINE,
    ) -> Optional[float]:
        """Compute similarity between two embeddings."""
        with self._lock:
            if embedding_id_1 not in self._embeddings or embedding_id_2 not in self._embeddings:
                return None

            # Check cache
            cache_key = f"{embedding_id_1}_{embedding_id_2}_{metric.value}"
            if cache_key in self._similarity_cache:
                return self._similarity_cache[cache_key]

            v1 = np.array(self._embeddings[embedding_id_1].vector, dtype=np.float32)
            v2 = np.array(self._embeddings[embedding_id_2].vector, dtype=np.float32)

            if metric == SimilarityMetric.COSINE:
                score = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
            elif metric == SimilarityMetric.EUCLIDEAN:
                score = -np.linalg.norm(v1 - v2)  # Negate for similarity
            elif metric == SimilarityMetric.MANHATTAN:
                score = -np.sum(np.abs(v1 - v2))  # Negate for similarity
            elif metric == SimilarityMetric.DOT_PRODUCT:
                score = np.dot(v1, v2)
            elif metric == SimilarityMetric.CHEBYSHEV:
                score = -np.max(np.abs(v1 - v2))  # Negate for similarity
            else:
                return None

            score = float(score)
            self._similarity_cache[cache_key] = score
            
            # Limit cache
            if len(self._similarity_cache) > 10000:
                self._similarity_cache.pop(next(iter(self._similarity_cache)))

            return score

    def find_similar_embeddings(
        self,
        embedding_id: str,
        top_k: int = 10,
        metric: SimilarityMetric = SimilarityMetric.COSINE,
        min_similarity: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """Find similar embeddings."""
        with self._lock:
            if embedding_id not in self._embeddings:
                return []

            similarities = []
            for other_id in self._embeddings:
                if other_id == embedding_id:
                    continue
                score = self.compute_similarity(embedding_id, other_id, metric)
                if score is not None and score >= min_similarity:
                    similarities.append((other_id, score))

            # Sort by similarity (descending) and return top-k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]

    def reduce_dimensionality(
        self,
        embedding_id: str,
        target_dimensions: int = 2,
        method: str = "pca",
    ) -> Optional[List[float]]:
        """Reduce embedding dimensions for visualization."""
        with self._lock:
            if embedding_id not in self._embeddings:
                return None

            embedding = self._embeddings[embedding_id]
            vector = np.array(embedding.vector, dtype=np.float32).reshape(1, -1)

            if method == "pca":
                # Simplified PCA: take first N components after sorting by variance
                mean = np.mean(vector)
                centered = vector - mean
                U, S, Vt = np.linalg.svd(centered, full_matrices=False)
                reduced = np.dot(centered, Vt[:target_dimensions, :].T)
            elif method == "tsne":
                # Mock t-SNE: random projection for demo
                reduced = np.random.randn(1, target_dimensions)
            elif method == "umap":
                # Mock UMAP: random projection for demo
                reduced = np.random.randn(1, target_dimensions)
            else:
                return None

            return reduced[0].tolist()

    def get_embedding(self, embedding_id: str) -> Optional[Embedding]:
        """Retrieve embedding by ID."""
        with self._lock:
            return self._embeddings.get(embedding_id)

    def get_embeddings_by_model(self, model: EmbeddingModel) -> List[Embedding]:
        """Get all embeddings for a specific model."""
        with self._lock:
            return [e for e in self._embeddings.values() if e.model == model]

    def delete_embedding(self, embedding_id: str) -> bool:
        """Delete embedding."""
        with self._lock:
            if embedding_id in self._embeddings:
                del self._embeddings[embedding_id]
                if embedding_id in self._embedding_cache:
                    del self._embedding_cache[embedding_id]
                return True
            return False

    def clear_cache(self) -> int:
        """Clear embedding cache and return count cleared."""
        with self._lock:
            count = len(self._embedding_cache)
            self._embedding_cache.clear()
            return count

    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        with self._lock:
            cache_hit_rate = (
                self._stats['cache_hits'] /
                (self._stats['cache_hits'] + self._stats['cache_misses'])
                if (self._stats['cache_hits'] + self._stats['cache_misses']) > 0
                else 0.0
            )
            
            return {
                'total_embeddings': len(self._embeddings),
                'total_embeddings_generated': self._stats['total_embeddings_generated'],
                'total_tokens_processed': self._stats['total_tokens_processed'],
                'cache_hits': self._stats['cache_hits'],
                'cache_misses': self._stats['cache_misses'],
                'cache_hit_rate': cache_hit_rate,
                'batches_processed': self._stats['batches_processed'],
                'registered_models': len(self._models),
                'cached_similarities': len(self._similarity_cache),
                'avg_generation_time_ms': self._stats['avg_generation_time_ms'],
                'model_stats': self._model_stats,
            }

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for event."""
        with self._lock:
            if event in self._callbacks:
                self._callbacks[event].append(callback)

    def _trigger_callback(self, event: str, **kwargs) -> None:
        """Trigger callbacks for event."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(**kwargs)
                except Exception:
                    pass  # Silently ignore callback errors

    def _mock_generate_vector(self, text: str, model: EmbeddingModel) -> List[float]:
        """Generate mock embedding vector (deterministic based on text)."""
        # Use hash to generate deterministic but different vectors
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(seed % (2**32))
        
        # Determine vector size based on model
        size_map = {
            EmbeddingModel.OPENAI_ADA: 1536,
            EmbeddingModel.OPENAI_3_SMALL: 1536,
            EmbeddingModel.OPENAI_3_LARGE: 3072,
            EmbeddingModel.SENTENCE_BERT: 384,
            EmbeddingModel.COHERE: 768,
            EmbeddingModel.HUGGINGFACE_DISTILBERT: 768,
            EmbeddingModel.HUGGINGFACE_MINILM: 384,
            EmbeddingModel.BAAI_BGE_SMALL: 384,
            EmbeddingModel.BAAI_BGE_LARGE: 1024,
            EmbeddingModel.JINA_AI: 768,
        }
        
        size = size_map.get(model, 384)
        vector = np.random.randn(size).astype(np.float32).tolist()
        
        return vector
