"""
Vector Store Service - Efficient Vector Storage and Indexing
Provides multiple indexing strategies for fast similarity search.
"""

from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Dict, List, Optional, Tuple, Set, Any, Callable
import hashlib
import time
import numpy as np
from datetime import datetime


class IndexStrategy(Enum):
    """Vector indexing strategies."""
    FLAT = "flat"              # Brute force search
    HNSW = "hnsw"              # Hierarchical Navigable Small World
    IVF = "ivf"                # Inverted File with Product Quantization
    LSH = "lsh"                # Locality Sensitive Hashing
    ANNOY = "annoy"            # Approximate Nearest Neighbors
    FAISS = "faiss"            # Facebook AI Similarity Search


class IndexStatus(Enum):
    """Status of index."""
    IDLE = "idle"
    BUILDING = "building"
    OPTIMIZING = "optimizing"
    READY = "ready"
    ERROR = "error"


class VectorStorageBackend(Enum):
    """Backend storage options."""
    MEMORY = "memory"           # In-memory storage
    DISK = "disk"               # Disk-based storage
    HYBRID = "hybrid"           # In-memory + disk
    REDIS = "redis"             # Redis cluster
    ELASTIC = "elastic"         # Elasticsearch


@dataclass
class VectorMetadata:
    """Metadata associated with a vector."""
    vector_id: str
    text_id: str
    collection: str
    timestamp: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    source: str = ""
    embedding_model: str = ""
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorWithMetadata:
    """Vector with associated metadata."""
    vector_id: str
    vector: List[float]
    metadata: VectorMetadata
    indexed: bool = False
    indexed_time: Optional[float] = None


@dataclass
class IndexConfig:
    """Configuration for vector index."""
    strategy: IndexStrategy
    backend: VectorStorageBackend
    metric: str = "cosine"
    dimension: int = 384
    ef_construction: int = 200  # HNSW parameter
    max_m: int = 16              # HNSW parameter
    nlist: int = 100             # IVF parameter
    nprobe: int = 10             # IVF parameter
    num_hash_tables: int = 10    # LSH parameter
    hash_size: int = 21          # LSH parameter
    max_vectors: int = 1000000
    batch_insert_size: int = 1000


@dataclass
class CollectionConfig:
    """Configuration for vector collection."""
    name: str
    dimension: int
    metric: str = "cosine"
    indexed: bool = True
    metadata_filtering: bool = True
    auto_commit: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class SearchResult:
    """Result from vector search."""
    vector_id: str
    metadata: VectorMetadata
    distance: float
    similarity: float
    rank: int


@dataclass
class QuantizationStats:
    """Statistics for quantization."""
    original_size_bytes: int
    quantized_size_bytes: int
    compression_ratio: float
    precision_loss_percent: float


@dataclass
class IndexStatistics:
    """Index statistics."""
    num_vectors: int
    num_indexed_vectors: int
    index_size_mb: float
    avg_query_time_ms: float
    index_status: IndexStatus
    last_optimized: Optional[float] = None
    total_queries: int = 0
    total_inserts: int = 0


class VectorStore:
    """Service for efficient vector storage and similarity search."""

    def __init__(self, index_config: IndexConfig):
        """Initialize vector store."""
        self._lock = RLock()
        self._config = index_config
        self._collections: Dict[str, CollectionConfig] = {}
        self._vectors: Dict[str, VectorWithMetadata] = {}
        self._indices: Dict[str, List[str]] = defaultdict(list)  # collection -> vector_ids
        self._metadata_index: Dict[str, Set[str]] = defaultdict(set)  # tag -> vector_ids
        self._text_id_index: Dict[str, str] = {}  # text_id -> vector_id
        
        # Index statistics
        self._index_stats: Dict[str, IndexStatistics] = {}
        self._query_times: deque = deque(maxlen=1000)
        
        # Quantization cache
        self._quantized_vectors: Dict[str, np.ndarray] = {}
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            'vector_inserted': [],
            'vector_deleted': [],
            'index_built': [],
            'collection_created': [],
            'search_completed': [],
        }
        
        # Statistics
        self._stats = {
            'total_inserts': 0,
            'total_deletes': 0,
            'total_searches': 0,
            'avg_query_time_ms': 0.0,
            'total_vectors': 0,
        }

    def create_collection(self, collection_config: CollectionConfig) -> bool:
        """Create a new vector collection."""
        with self._lock:
            if collection_config.name in self._collections:
                return False

            self._collections[collection_config.name] = collection_config
            self._index_stats[collection_config.name] = IndexStatistics(
                num_vectors=0,
                num_indexed_vectors=0,
                index_size_mb=0.0,
                avg_query_time_ms=0.0,
                index_status=IndexStatus.IDLE,
            )
            self._trigger_callback('collection_created', collection=collection_config.name)
            return True

    def get_collection(self, collection: str) -> Optional[CollectionConfig]:
        """Get collection configuration."""
        with self._lock:
            return self._collections.get(collection)

    def insert_vector(
        self,
        vector: List[float],
        text_id: str,
        collection: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Insert a vector into collection."""
        with self._lock:
            if collection not in self._collections:
                return None

            if len(vector) != self._collections[collection].dimension:
                return None

            vector_id = hashlib.sha256(
                f"{text_id}_{time.time()}".encode()
            ).hexdigest()[:16]

            vec_metadata = VectorMetadata(
                vector_id=vector_id,
                text_id=text_id,
                collection=collection,
                tags=tags or [],
                custom_metadata=metadata or {},
            )

            vec_with_meta = VectorWithMetadata(
                vector_id=vector_id,
                vector=vector,
                metadata=vec_metadata,
            )

            self._vectors[vector_id] = vec_with_meta
            self._indices[collection].append(vector_id)
            self._text_id_index[text_id] = vector_id

            # Index tags
            for tag in (tags or []):
                self._metadata_index[tag].add(vector_id)

            self._stats['total_inserts'] += 1
            self._stats['total_vectors'] += 1
            
            if self._index_stats[collection]:
                self._index_stats[collection].num_vectors += 1
                self._index_stats[collection].total_inserts += 1

            self._trigger_callback(
                'vector_inserted',
                vector_id=vector_id,
                collection=collection,
            )

            return vector_id

    def batch_insert_vectors(
        self,
        vectors: List[Tuple[str, List[float]]],  # (text_id, vector) pairs
        collection: str,
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        tags_list: Optional[List[List[str]]] = None,
    ) -> List[str]:
        """Insert multiple vectors."""
        with self._lock:
            inserted_ids = []
            for i, (text_id, vector) in enumerate(vectors):
                metadata = metadata_list[i] if metadata_list else None
                tags = tags_list[i] if tags_list else None
                
                vec_id = self.insert_vector(
                    vector=vector,
                    text_id=text_id,
                    collection=collection,
                    metadata=metadata,
                    tags=tags,
                )
                if vec_id:
                    inserted_ids.append(vec_id)

            return inserted_ids

    def delete_vector(self, vector_id: str) -> bool:
        """Delete vector by ID."""
        with self._lock:
            if vector_id not in self._vectors:
                return False

            vec = self._vectors[vector_id]
            collection = vec.metadata.collection

            del self._vectors[vector_id]
            if vec_id in self._indices[collection]:
                self._indices[collection].remove(vec_id)

            # Remove from tag indices
            for tag in vec.metadata.tags:
                self._metadata_index[tag].discard(vec_id)

            # Remove from text_id index
            text_id = vec.metadata.text_id
            if text_id in self._text_id_index:
                del self._text_id_index[text_id]

            self._stats['total_deletes'] += 1
            self._stats['total_vectors'] -= 1
            
            if self._index_stats[collection]:
                self._index_stats[collection].num_vectors -= 1

            self._trigger_callback('vector_deleted', vector_id=vector_id)
            return True

    def search(
        self,
        query_vector: List[float],
        collection: str,
        top_k: int = 10,
        metric: str = "cosine",
        filters: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0,
    ) -> List[SearchResult]:
        """Search for similar vectors."""
        with self._lock:
            if collection not in self._collections:
                return []

            start_time = time.time()
            query_vec = np.array(query_vector, dtype=np.float32)
            similarities = []

            # Get vectors to search
            vector_ids = self._indices[collection]
            
            # Apply filters if provided
            if filters:
                filtered_ids = self._apply_filters(filters)
                vector_ids = [vid for vid in vector_ids if vid in filtered_ids]

            # Compute similarities
            for vec_id in vector_ids:
                vec = self._vectors[vec_id]
                target_vec = np.array(vec.vector, dtype=np.float32)

                if metric == "cosine":
                    similarity = np.dot(query_vec, target_vec) / (
                        np.linalg.norm(query_vec) * np.linalg.norm(target_vec) + 1e-8
                    )
                elif metric == "euclidean":
                    similarity = -np.linalg.norm(query_vec - target_vec)
                elif metric == "manhattan":
                    similarity = -np.sum(np.abs(query_vec - target_vec))
                else:
                    continue

                if similarity >= min_similarity:
                    similarities.append((vec_id, similarity))

            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Build results
            results = []
            for rank, (vec_id, similarity) in enumerate(similarities[:top_k]):
                vec = self._vectors[vec_id]
                result = SearchResult(
                    vector_id=vec_id,
                    metadata=vec.metadata,
                    distance=-similarity if metric == "cosine" else similarity,
                    similarity=float(similarity),
                    rank=rank + 1,
                )
                results.append(result)

            # Track query time
            query_time = (time.time() - start_time) * 1000
            self._query_times.append(query_time)
            self._stats['total_searches'] += 1
            self._stats['avg_query_time_ms'] = np.mean(list(self._query_times))

            if self._index_stats[collection]:
                self._index_stats[collection].total_queries += 1
                self._index_stats[collection].avg_query_time_ms = self._stats['avg_query_time_ms']

            self._trigger_callback(
                'search_completed',
                collection=collection,
                query_time_ms=query_time,
                results_count=len(results),
            )

            return results

    def search_by_text_id(
        self,
        text_id: str,
        collection: str,
        top_k: int = 10,
        metric: str = "cosine",
    ) -> List[SearchResult]:
        """Search similar vectors by text ID."""
        with self._lock:
            if text_id not in self._text_id_index:
                return []

            vector_id = self._text_id_index[text_id]
            if vector_id not in self._vectors:
                return []

            query_vector = self._vectors[vector_id].vector
            
            # Exclude the query vector itself
            results = self.search(
                query_vector=query_vector,
                collection=collection,
                top_k=top_k + 1,  # Get one extra since we'll exclude self
                metric=metric,
            )

            # Filter out self
            return [r for r in results if r.vector_id != vector_id][:top_k]

    def build_index(self, collection: str) -> bool:
        """Build/optimize index for collection."""
        with self._lock:
            if collection not in self._collections:
                return False

            if self._index_stats[collection]:
                self._index_stats[collection].index_status = IndexStatus.BUILDING

            # Mock index building
            if self._index_stats[collection]:
                self._index_stats[collection].index_status = IndexStatus.READY
                self._index_stats[collection].last_optimized = time.time()

            self._trigger_callback('index_built', collection=collection)
            return True

    def quantize_vector(
        self,
        vector_id: str,
        target_type: np.dtype = np.int8,
    ) -> bool:
        """Quantize vector to reduce memory."""
        with self._lock:
            if vector_id not in self._vectors:
                return False

            vector = np.array(self._vectors[vector_id].vector, dtype=np.float32)
            
            # Min-max quantization to target type range
            v_min = np.min(vector)
            v_max = np.max(vector)
            
            if target_type == np.int8:
                quantized = ((vector - v_min) / (v_max - v_min + 1e-8) * 255 - 128).astype(np.int8)
            elif target_type == np.uint8:
                quantized = ((vector - v_min) / (v_max - v_min + 1e-8) * 255).astype(np.uint8)
            elif target_type == np.float16:
                quantized = vector.astype(np.float16)
            else:
                return False

            self._quantized_vectors[vector_id] = quantized
            return True

    def get_vector(self, vector_id: str) -> Optional[VectorWithMetadata]:
        """Get vector by ID."""
        with self._lock:
            return self._vectors.get(vector_id)

    def get_vectors_by_tag(self, tag: str) -> List[VectorWithMetadata]:
        """Get all vectors with specific tag."""
        with self._lock:
            vector_ids = self._metadata_index.get(tag, set())
            return [self._vectors[vid] for vid in vector_ids if vid in self._vectors]

    def get_vectors_by_collection(self, collection: str) -> List[VectorWithMetadata]:
        """Get all vectors in collection."""
        with self._lock:
            vector_ids = self._indices.get(collection, [])
            return [self._vectors[vid] for vid in vector_ids if vid in self._vectors]

    def update_vector_metadata(
        self,
        vector_id: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """Update vector metadata."""
        with self._lock:
            if vector_id not in self._vectors:
                return False

            vec = self._vectors[vector_id]
            vec.metadata.custom_metadata.update(metadata)
            return True

    def add_tags(self, vector_id: str, tags: List[str]) -> bool:
        """Add tags to vector."""
        with self._lock:
            if vector_id not in self._vectors:
                return False

            vec = self._vectors[vector_id]
            for tag in tags:
                if tag not in vec.metadata.tags:
                    vec.metadata.tags.append(tag)
                self._metadata_index[tag].add(vector_id)
            return True

    def remove_tags(self, vector_id: str, tags: List[str]) -> bool:
        """Remove tags from vector."""
        with self._lock:
            if vector_id not in self._vectors:
                return False

            vec = self._vectors[vector_id]
            for tag in tags:
                if tag in vec.metadata.tags:
                    vec.metadata.tags.remove(tag)
                self._metadata_index[tag].discard(vector_id)
            return True

    def delete_collection(self, collection: str) -> bool:
        """Delete entire collection."""
        with self._lock:
            if collection not in self._collections:
                return False

            # Delete all vectors in collection
            vector_ids = list(self._indices[collection])
            for vec_id in vector_ids:
                self.delete_vector(vec_id)

            del self._collections[collection]
            del self._indices[collection]
            if collection in self._index_stats:
                del self._index_stats[collection]

            return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get store statistics."""
        with self._lock:
            stats_per_collection = {}
            for collection, config in self._collections.items():
                stats_per_collection[collection] = {
                    'vectors': len(self._indices[collection]),
                    'indexed': (
                        self._index_stats[collection].num_indexed_vectors
                        if collection in self._index_stats
                        else 0
                    ),
                    'status': (
                        self._index_stats[collection].index_status.value
                        if collection in self._index_stats
                        else 'unknown'
                    ),
                }

            return {
                'total_vectors': self._stats['total_vectors'],
                'total_inserts': self._stats['total_inserts'],
                'total_deletes': self._stats['total_deletes'],
                'total_searches': self._stats['total_searches'],
                'avg_query_time_ms': self._stats['avg_query_time_ms'],
                'collections': stats_per_collection,
                'total_collections': len(self._collections),
                'quantized_vectors': len(self._quantized_vectors),
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
                    pass

    def _apply_filters(self, filters: Dict[str, Any]) -> Set[str]:
        """Apply metadata filters to vector IDs."""
        result_set = None

        for filter_key, filter_value in filters.items():
            matching_ids = set()
            
            # Handle tag filters
            if filter_key == "tags":
                if isinstance(filter_value, list):
                    for tag in filter_value:
                        matching_ids.update(self._metadata_index.get(tag, set()))
                else:
                    matching_ids = self._metadata_index.get(filter_value, set())

            if result_set is None:
                result_set = matching_ids
            else:
                result_set = result_set.intersection(matching_ids)

        return result_set if result_set else set(self._vectors.keys())
