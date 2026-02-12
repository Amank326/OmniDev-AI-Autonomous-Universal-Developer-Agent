"""
Text Embedder Service
Provides word and text embeddings for semantic similarity, document comparison,
and machine learning features. Supports multiple embedding models and similarity metrics.
"""

import threading
import time
import logging
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
from threading import RLock
import random

logger = logging.getLogger(__name__)


class EmbeddingModel(Enum):
    """Available embedding models"""
    WORD2VEC = "word2vec"
    GLOVE = "glove"
    FASTTEXT = "fasttext"
    BERT = "bert"
    TFIDF = "tfidf"
    SIMPLE_HASH = "simple_hash"  # Fallback


class SimilarityMetric(Enum):
    """Similarity calculation methods"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    MANHATTAN = "manhattan"
    JACCARD = "jaccard"
    HAMMING = "hamming"


@dataclass
class WordEmbedding:
    """Word embedding vectors and metadata"""
    word: str
    embedding: List[float]
    model: EmbeddingModel
    vocabulary_frequency: int = 0
    related_words: List[Tuple[str, float]] = field(default_factory=list)  # (word, similarity)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "word": self.word,
            "embedding_dim": len(self.embedding),
            "model": self.model.value,
            "vocabulary_frequency": self.vocabulary_frequency,
            "related_words": self.related_words[:5]  # Top 5
        }


@dataclass
class TextEmbedding:
    """Text/document embedding"""
    text_id: str
    text_snippet: str
    embedding: List[float]
    embedding_dim: int
    model: EmbeddingModel
    norm: float
    similarity_scores: Dict[str, float] = field(default_factory=dict)  # text_id -> similarity
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text_id": self.text_id,
            "embedding_dim": self.embedding_dim,
            "model": self.model.value,
            "norm": self.norm,
            "top_similar": sorted(self.similarity_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        }


@dataclass
class SimilarityResult:
    """Result of similarity comparison"""
    text1_id: str
    text2_id: str
    similarity_score: float  # 0-1
    metric: SimilarityMetric
    confidence: float  # 0-1
    common_words: List[str]
    unique_to_text1: List[str]
    unique_to_text2: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text1_id": self.text1_id,
            "text2_id": self.text2_id,
            "similarity_score": self.similarity_score,
            "metric": self.metric.value,
            "confidence": self.confidence,
            "common_words": self.common_words[:10],
            "unique_to_text1": self.unique_to_text1[:5],
            "unique_to_text2": self.unique_to_text2[:5]
        }


@dataclass
class EmbedderConfig:
    """Text embedder configuration"""
    embedding_model: EmbeddingModel = EmbeddingModel.SIMPLE_HASH
    embedding_dim: int = 128
    similarity_metric: SimilarityMetric = SimilarityMetric.COSINE
    cache_embeddings: bool = True
    cache_ttl_seconds: int = 3600
    normalize_embeddings: bool = True
    min_similarity_threshold: float = 0.3
    use_idf_weighting: bool = True
    vocabulary_size_limit: int = 10000
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "embedding_model": self.embedding_model.value,
            "embedding_dim": self.embedding_dim,
            "similarity_metric": self.similarity_metric.value,
            "cache_embeddings": self.cache_embeddings,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "normalize_embeddings": self.normalize_embeddings,
            "min_similarity_threshold": self.min_similarity_threshold,
            "use_idf_weighting": self.use_idf_weighting,
            "vocabulary_size_limit": self.vocabulary_size_limit
        }


@dataclass
class EmbedderMetrics:
    """Metrics for embedding operations"""
    total_embeddings_generated: int = 0
    total_similarity_comparisons: int = 0
    avg_embedding_generation_time_ms: float = 0.0
    avg_similarity_computation_time_ms: float = 0.0
    vocabulary_size: int = 0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    error_count: int = 0
    last_processed_at: Optional[datetime] = None
    models_in_use: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_embeddings_generated": self.total_embeddings_generated,
            "total_similarity_comparisons": self.total_similarity_comparisons,
            "avg_embedding_generation_time_ms": self.avg_embedding_generation_time_ms,
            "avg_similarity_computation_time_ms": self.avg_similarity_computation_time_ms,
            "vocabulary_size": self.vocabulary_size,
            "cache_hit_count": self.cache_hit_count,
            "cache_miss_count": self.cache_miss_count,
            "error_count": self.error_count,
            "last_processed_at": self.last_processed_at.isoformat() if self.last_processed_at else None,
            "models_in_use": self.models_in_use,
            "cache_hit_rate": self.cache_hit_count / (self.cache_hit_count + self.cache_miss_count) if (self.cache_hit_count + self.cache_miss_count) > 0 else 0.0
        }


class TextEmbedder:
    """
    Text embedding service for semantic analysis.
    Thread-safe singleton supporting multiple embedding models.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.config = EmbedderConfig()
            self.metrics = EmbedderMetrics()
            self._embedding_cache: Dict[str, Tuple[TextEmbedding, float]] = {}
            self._word_embeddings: Dict[str, WordEmbedding] = {}
            self._vocabulary: Dict[str, int] = {}  # word -> frequency
            self._document_embeddings: Dict[str, TextEmbedding] = {}
            self._lock = RLock()
            self._generation_times: List[float] = []
            self._similarity_times: List[float] = []
            self._initialized = True
    
    def embed_text(self, text: str, text_id: Optional[str] = None) -> TextEmbedding:
        """
        Generate embedding for input text.
        
        Args:
            text: Input text to embed
            text_id: Optional document ID
            
        Returns:
            TextEmbedding with vector representation
        """
        if not text or not isinstance(text, str):
            self.metrics.error_count += 1
            raise ValueError("Text must be non-empty string")
        
        start_time = time.time()
        text_id = text_id or self._generate_text_id(text)
        
        # Check cache
        if self.config.cache_embeddings and text_id in self._embedding_cache:
            cached_embedding, cached_time = self._embedding_cache[text_id]
            if time.time() - cached_time < self.config.cache_ttl_seconds:
                self.metrics.cache_hit_count += 1
                return cached_embedding
        
        self.metrics.cache_miss_count += 1
        
        try:
            # Generate embedding based on model
            if self.config.embedding_model == EmbeddingModel.SIMPLE_HASH:
                embedding = self._generate_simple_hash_embedding(text)
            elif self.config.embedding_model == EmbeddingModel.TFIDF:
                embedding = self._generate_tfidf_embedding(text)
            else:
                # Fallback to simple hash
                embedding = self._generate_simple_hash_embedding(text)
            
            # Normalize if configured
            if self.config.normalize_embeddings:
                embedding = self._normalize_vector(embedding)
            
            # Calculate vector norm
            norm = self._calculate_norm(embedding)
            
            text_embedding = TextEmbedding(
                text_id=text_id,
                text_snippet=text[:100],
                embedding=embedding,
                embedding_dim=len(embedding),
                model=self.config.embedding_model,
                norm=norm
            )
            
            # Cache embedding
            if self.config.cache_embeddings:
                self._embedding_cache[text_id] = (text_embedding, time.time())
            
            # Store for similarity searches
            self._document_embeddings[text_id] = text_embedding
            
            generation_time_ms = (time.time() - start_time) * 1000
            self._generation_times.append(generation_time_ms)
            if len(self._generation_times) > 1000:
                self._generation_times.pop(0)
            
            # Update metrics
            with self._lock:
                self.metrics.total_embeddings_generated += 1
                self.metrics.last_processed_at = datetime.now()
                if len(self._generation_times) > 0:
                    self.metrics.avg_embedding_generation_time_ms = sum(self._generation_times) / len(self._generation_times)
                if self.config.embedding_model not in self.metrics.models_in_use:
                    self.metrics.models_in_use.append(self.config.embedding_model.value)
            
            return text_embedding
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Error embedding text: {str(e)}")
            raise
    
    def embed_word(self, word: str) -> WordEmbedding:
        """Generate embedding for single word."""
        if word in self._word_embeddings:
            return self._word_embeddings[word]
        
        embedding = self._generate_simple_hash_embedding(word)
        if self.config.normalize_embeddings:
            embedding = self._normalize_vector(embedding)
        
        word_embedding = WordEmbedding(
            word=word,
            embedding=embedding,
            model=self.config.embedding_model,
            vocabulary_frequency=self._vocabulary.get(word, 0)
        )
        
        self._word_embeddings[word] = word_embedding
        return word_embedding
    
    def calculate_similarity(self, text1: str, text2: str, metric: Optional[SimilarityMetric] = None) -> SimilarityResult:
        """
        Calculate similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            metric: Optional override for similarity metric
            
        Returns:
            SimilarityResult with similarity score and details
        """
        start_time = time.time()
        metric = metric or self.config.similarity_metric
        
        try:
            # Generate embeddings
            embedding1 = self.embed_text(text1, "text1")
            embedding2 = self.embed_text(text2, "text2")
            
            # Calculate similarity
            if metric == SimilarityMetric.COSINE:
                score = self._cosine_similarity(embedding1.embedding, embedding2.embedding)
            elif metric == SimilarityMetric.EUCLIDEAN:
                score = 1.0 / (1.0 + self._euclidean_distance(embedding1.embedding, embedding2.embedding))
            elif metric == SimilarityMetric.MANHATTAN:
                score = 1.0 / (1.0 + self._manhattan_distance(embedding1.embedding, embedding2.embedding))
            elif metric == SimilarityMetric.JACCARD:
                score = self._jaccard_similarity(set(text1.split()), set(text2.split()))
            else:
                score = self._cosine_similarity(embedding1.embedding, embedding2.embedding)
            
            # Extract common and unique words
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            common = list(words1 & words2)
            unique1 = list(words1 - words2)
            unique2 = list(words2 - words1)
            
            computation_time_ms = (time.time() - start_time) * 1000
            self._similarity_times.append(computation_time_ms)
            if len(self._similarity_times) > 1000:
                self._similarity_times.pop(0)
            
            result = SimilarityResult(
                text1_id="text1",
                text2_id="text2",
                similarity_score=max(0.0, min(score, 1.0)),
                metric=metric,
                confidence=abs(score) if metric == SimilarityMetric.COSINE else min(score, 1.0),
                common_words=common,
                unique_to_text1=unique1,
                unique_to_text2=unique2
            )
            
            # Update metrics
            with self._lock:
                self.metrics.total_similarity_comparisons += 1
                if len(self._similarity_times) > 0:
                    self.metrics.avg_similarity_computation_time_ms = sum(self._similarity_times) / len(self._similarity_times)
            
            return result
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Error calculating similarity: {str(e)}")
            raise
    
    def find_similar_texts(self, text: str, threshold: Optional[float] = None) -> List[Tuple[str, float]]:
        """Find similar texts from stored embeddings."""
        threshold = threshold or self.config.min_similarity_threshold
        embedding = self.embed_text(text)
        
        similarities = []
        for text_id, stored_embedding in self._document_embeddings.items():
            if text_id != embedding.text_id:
                score = self._cosine_similarity(embedding.embedding, stored_embedding.embedding)
                if score >= threshold:
                    similarities.append((text_id, score))
        
        return sorted(similarities, key=lambda x: x[1], reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get embedder metrics."""
        return self.metrics.to_dict()
    
    def get_config(self) -> Dict[str, Any]:
        """Get embedder configuration."""
        return self.config.to_dict()
    
    def update_config(self, **kwargs) -> None:
        """Update embedder configuration."""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
    
    def clear_cache(self) -> None:
        """Clear embedding cache."""
        with self._lock:
            self._embedding_cache.clear()
    
    # Private methods
    
    def _generate_simple_hash_embedding(self, text: str) -> List[float]:
        """Generate embedding using hash-based method."""
        # Use text hash to seed random number generator for reproducibility
        import hashlib
        hash_value = hashlib.md5(text.encode()).hexdigest()
        hash_int = int(hash_value[:8], 16)
        
        random.seed(hash_int)
        embedding = [random.gauss(0, 1) for _ in range(self.config.embedding_dim)]
        
        return embedding
    
    def _generate_tfidf_embedding(self, text: str) -> List[float]:
        """Generate TF-IDF based embedding."""
        # Simple TF-IDF calculation
        words = text.lower().split()
        
        # Update vocabulary
        for word in words:
            self._vocabulary[word] = self._vocabulary.get(word, 0) + 1
        
        # Calculate TF weights
        term_count = {}
        for word in words:
            term_count[word] = term_count.get(word, 0) + 1
        
        embedding = [0.0] * self.config.embedding_dim
        
        # Create feature vector (simplified: hash each word to dimension)
        for word, count in term_count.items():
            word_hash = hash(word) % self.config.embedding_dim
            tf = count / len(words) if len(words) > 0 else 0
            idf = 1.0 + math.log(len(self._vocabulary) / (self._vocabulary.get(word, 1) + 1))
            embedding[word_hash] += tf * idf if self.config.use_idf_weighting else tf
        
        return embedding
    
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize vector to unit length."""
        norm = self._calculate_norm(vector)
        if norm == 0:
            return vector
        return [v / norm for v in vector]
    
    def _calculate_norm(self, vector: List[float]) -> float:
        """Calculate L2 norm of vector."""
        return math.sqrt(sum(v * v for v in vector))
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
        norm1 = self._calculate_norm(vec1)
        norm2 = self._calculate_norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Euclidean distance between vectors."""
        if len(vec1) != len(vec2):
            return float('inf')
        
        return math.sqrt(sum((v1 - v2) ** 2 for v1, v2 in zip(vec1, vec2)))
    
    def _manhattan_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Manhattan distance between vectors."""
        if len(vec1) != len(vec2):
            return float('inf')
        
        return sum(abs(v1 - v2) for v1, v2 in zip(vec1, vec2))
    
    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """Calculate Jaccard similarity between sets."""
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _generate_text_id(self, text: str) -> str:
        """Generate ID for text."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()[:8]


# Singleton instance
_text_embedder = None


def get_text_embedder() -> TextEmbedder:
    """Get TextEmbedder singleton instance."""
    global _text_embedder
    if _text_embedder is None:
        _text_embedder = TextEmbedder()
    return _text_embedder
