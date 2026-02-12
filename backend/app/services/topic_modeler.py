"""
Topic Modeler Service
Implements topic modeling and document clustering for discovering latent themes,
categorizing documents, and identifying dominant topics.
Integrates with NLP engine for text preprocessing.
"""

import threading
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any, Set
from datetime import datetime
from threading import RLock
from collections import Counter
import math

logger = logging.getLogger(__name__)


class ClusteringAlgorithm(Enum):
    """Topic modeling and clustering algorithms"""
    LDA = "lda"  # Latent Dirichlet Allocation
    LSA = "lsa"  # Latent Semantic Analysis
    KMEANS = "kmeans"  # K-Means clustering
    DBSCAN = "dbscan"  # Density-based clustering
    HIERARCHICAL = "hierarchical"  # Hierarchical clustering


class TopicCategory(Enum):
    """High-level topic categories"""
    TECHNICAL = "technical"
    BUSINESS = "business"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    USER_BEHAVIOR = "user_behavior"
    INCIDENT = "incident"
    POLICY = "policy"
    COMPLIANCE = "compliance"
    GENERAL = "general"


@dataclass
class Topic:
    """Discovered topic with keywords and distribution"""
    topic_id: int
    name: str
    keywords: List[Tuple[str, float]]  # (keyword, weight) pairs
    category: TopicCategory
    coherence_score: float  # 0-1, higher = more coherent
    frequency: int  # How often this topic appears
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "name": self.name,
            "keywords": keywords,
            "category": self.category.value,
            "coherence_score": self.coherence_score,
            "frequency": self.frequency
        }


@dataclass
class DocumentTopicDistribution:
    """Distribution of topics in a document"""
    document_id: str
    text_snippet: str
    primary_topic: Topic
    topic_distribution: Dict[int, float]  # topic_id -> probability
    main_topic_strength: float  # 0-1, strength of primary topic
    secondary_topics: List[Tuple[Topic, float]]  # (topic, probability) pairs
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "primary_topic": self.primary_topic.to_dict(),
            "main_topic_strength": self.main_topic_strength,
            "secondary_topics": [(t.to_dict(), p) for t, p in self.secondary_topics],
            "confidence": self.confidence
        }


@dataclass
class ClusteringResult:
    """Result of document clustering"""
    documents: List[str]
    num_clusters: int
    clusters: List[List[int]]  # List of document indices per cluster
    cluster_topics: List[Topic]
    silhouette_score: float  # -1 to 1, higher = better
    inertia: float  # Sum of squared distances to closest cluster
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_clusters": self.num_clusters,
            "num_documents": len(self.documents),
            "silhouette_score": self.silhouette_score,
            "inertia": self.inertia,
            "cluster_topics": [t.to_dict() for t in self.cluster_topics],
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class TopicModelingConfig:
    """Topic modeling configuration"""
    algorithm: ClusteringAlgorithm = ClusteringAlgorithm.LDA
    num_topics: int = 5
    num_keywords_per_topic: int = 10
    min_document_frequency: int = 1
    max_document_percentage: float = 0.9
    coherence_threshold: float = 0.5
    cache_results: bool = True
    cache_ttl_seconds: int = 3600
    enable_stemming: bool = True
    min_token_length: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm.value,
            "num_topics": self.num_topics,
            "num_keywords_per_topic": self.num_keywords_per_topic,
            "min_document_frequency": self.min_document_frequency,
            "max_document_percentage": self.max_document_percentage,
            "coherence_threshold": self.coherence_threshold,
            "cache_results": self.cache_results,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "enable_stemming": self.enable_stemming,
            "min_token_length": self.min_token_length
        }


@dataclass
class TopicModelerMetrics:
    """Metrics for topic modeling"""
    total_documents_processed: int = 0
    total_topics_discovered: int = 0
    avg_coherence_score: float = 0.0
    avg_silhouette_score: float = 0.0
    avg_processing_time_ms: float = 0.0
    clustering_runs: int = 0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    error_count: int = 0
    last_processed_at: Optional[datetime] = None
    most_common_topic_category: Optional[TopicCategory] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_documents_processed": self.total_documents_processed,
            "total_topics_discovered": self.total_topics_discovered,
            "avg_coherence_score": self.avg_coherence_score,
            "avg_silhouette_score": self.avg_silhouette_score,
            "avg_processing_time_ms": self.avg_processing_time_ms,
            "clustering_runs": self.clustering_runs,
            "cache_hit_count": self.cache_hit_count,
            "cache_miss_count": self.cache_miss_count,
            "error_count": self.error_count,
            "last_processed_at": self.last_processed_at.isoformat() if self.last_processed_at else None,
            "most_common_topic_category": self.most_common_topic_category.value if self.most_common_topic_category else None,
            "cache_hit_rate": self.cache_hit_count / (self.cache_hit_count + self.cache_miss_count) if (self.cache_hit_count + self.cache_miss_count) > 0 else 0.0
        }


class TopicModeler:
    """
    Topic modeling and document clustering service.
    Thread-safe singleton supporting multiple algorithms for discovering latent topics.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # Common stopwords
    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "is", "are", "am", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did",
        "that", "this", "these", "those", "which", "who", "what", "where",
        "when", "why", "how"
    }
    
    # Topic categories keywords
    TOPIC_KEYWORDS = {
        TopicCategory.SECURITY: {"security", "breach", "attack", "threat", "vulnerability", "exploit", "malware"},
        TopicCategory.TECHNICAL: {"system", "code", "software", "technical", "api", "database", "server", "network"},
        TopicCategory.BUSINESS: {"business", "revenue", "sales", "market", "customer", "product", "profit"},
        TopicCategory.INFRASTRUCTURE: {"infrastructure", "cloud", "compute", "storage", "deployment", "scaling"},
        TopicCategory.USER_BEHAVIOR: {"user", "behavior", "activity", "access", "login", "session", "request"},
        TopicCategory.INCIDENT: {"incident", "issue", "problem", "error", "failure", "down", "outage"},
        TopicCategory.POLICY: {"policy", "rule", "regulation", "compliance", "governance", "control"},
        TopicCategory.COMPLIANCE: {"compliance", "regulation", "audit", "requirement", "standard", "law"}
    }
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.config = TopicModelingConfig()
            self.metrics = TopicModelerMetrics()
            self._cache: Dict[str, Tuple[ClusteringResult, float]] = {}
            self._topics: Dict[int, Topic] = {}
            self._topic_counter = 0
            self._lock = RLock()
            self._processing_times: List[float] = []
            self._coherence_scores: List[float] = []
            self._silhouette_scores: List[float] = []
            self._initialized = True
    
    def discover_topics(self, documents: List[str]) -> ClusteringResult:
        """
        Discover topics in collection of documents.
        
        Args:
            documents: List of documents to analyze
            
        Returns:
            ClusteringResult with discovered topics and document assignments
        """
        if not documents or not all(isinstance(d, str) for d in documents):
            self.metrics.error_count += 1
            raise ValueError("Documents must be non-empty list of strings")
        
        start_time = time.time()
        
        # Create cache key from first and last doc for efficiency
        cache_key = self._generate_cache_key(documents)
        if self.config.cache_results and cache_key in self._cache:
            cached_result, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self.config.cache_ttl_seconds:
                self.metrics.cache_hit_count += 1
                return cached_result
        
        self.metrics.cache_miss_count += 1
        
        try:
            # Preprocess documents
            tokenized_docs = [self._preprocess_document(doc) for doc in documents]
            
            # Build vocabulary
            vocab = self._build_vocabulary(tokenized_docs)
            
            # Create document-term matrix (simplified)
            doc_term_matrix = self._create_doc_term_matrix(tokenized_docs, vocab)
            
            # Discover topics based on algorithm
            if self.config.algorithm == ClusteringAlgorithm.LDA:
                topics, assignments = self._lda_modeling(tokenized_docs, vocab)
            elif self.config.algorithm == ClusteringAlgorithm.KMEANS:
                topics, assignments = self._kmeans_clustering(doc_term_matrix, tokenized_docs, vocab)
            else:
                topics, assignments = self._simple_topic_extraction(tokenized_docs, vocab)
            
            # Calculate quality metrics
            silhouette_score = self._calculate_silhouette_score(doc_term_matrix, assignments)
            inertia = self._calculate_inertia(doc_term_matrix, assignments, topics)
            
            # Create clusters from assignments
            clusters = self._create_clusters(assignments)
            
            processing_time_ms = (time.time() - start_time) * 1000
            self._processing_times.append(processing_time_ms)
            if len(self._processing_times) > 1000:
                self._processing_times.pop(0)
            
            # Track coherence scores
            avg_coherence = sum(t.coherence_score for t in topics) / len(topics) if topics else 0.0
            self._coherence_scores.append(avg_coherence)
            if len(self._coherence_scores) > 1000:
                self._coherence_scores.pop(0)
            
            self._silhouette_scores.append(silhouette_score)
            if len(self._silhouette_scores) > 1000:
                self._silhouette_scores.pop(0)
            
            result = ClusteringResult(
                documents=documents,
                num_clusters=len(topics),
                clusters=clusters,
                cluster_topics=topics,
                silhouette_score=silhouette_score,
                inertia=inertia,
                processing_time_ms=processing_time_ms
            )
            
            # Cache result
            if self.config.cache_results:
                self._cache[cache_key] = (result, time.time())
            
            # Update metrics
            with self._lock:
                self.metrics.total_documents_processed += len(documents)
                self.metrics.total_topics_discovered += len(topics)
                self.metrics.clustering_runs += 1
                self.metrics.last_processed_at = datetime.now()
                
                if len(self._processing_times) > 0:
                    self.metrics.avg_processing_time_ms = sum(self._processing_times) / len(self._processing_times)
                if len(self._coherence_scores) > 0:
                    self.metrics.avg_coherence_score = sum(self._coherence_scores) / len(self._coherence_scores)
                if len(self._silhouette_scores) > 0:
                    self.metrics.avg_silhouette_score = sum(self._silhouette_scores) / len(self._silhouette_scores)
                
                # Track most common category
                categories = [t.category for t in topics]
                if categories:
                    category_counts = Counter(categories)
                    most_common = category_counts.most_common(1)[0][0]
                    self.metrics.most_common_topic_category = most_common
            
            return result
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Error discovering topics: {str(e)}")
            raise
    
    def get_document_topics(self, text: str) -> DocumentTopicDistribution:
        """Get topic distribution for a single document."""
        tokenized = self._preprocess_document(text)
        
        # Simple topic assignment based on keyword matching
        topic_scores = {}
        for topic_id, topic in self._topics.items():
            score = sum(1 for keyword, weight in topic.keywords if keyword in tokenized) * weight
            topic_scores[topic_id] = score
        
        if not topic_scores:
            # Default topic if no matches
            primary_topic = list(self._topics.values())[0] if self._topics else self._create_default_topic()
            topic_distribution = {0: 1.0}
            main_topic_strength = 1.0
        else:
            total_score = sum(topic_scores.values())
            topic_distribution = {k: v / total_score for k, v in topic_scores.items()}
            primary_topic_id = max(topic_scores, key=topic_scores.get)
            primary_topic = self._topics[primary_topic_id]
            main_topic_strength = topic_scores[primary_topic_id] / total_score
        
        secondary_topics = sorted(
            [(self._topics[k], v) for k, v in topic_distribution.items() if k != primary_topic.topic_id],
            key=lambda x: x[1],
            reverse=True
        )[:2]
        
        return DocumentTopicDistribution(
            document_id=self._generate_cache_key(text)[:8],
            text_snippet=text[:100],
            primary_topic=primary_topic,
            topic_distribution=topic_distribution,
            main_topic_strength=main_topic_strength,
            secondary_topics=secondary_topics,
            confidence=min(main_topic_strength, 0.99) if main_topic_strength > 0 else 0.5
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get topic modeling metrics."""
        return self.metrics.to_dict()
    
    def get_config(self) -> Dict[str, Any]:
        """Get modeler configuration."""
        return self.config.to_dict()
    
    def update_config(self, **kwargs) -> None:
        """Update modeler configuration."""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
    
    def clear_cache(self) -> None:
        """Clear modeling cache."""
        with self._lock:
            self._cache.clear()
    
    # Private methods
    
    def _preprocess_document(self, doc: str) -> List[str]:
        """Preprocess and tokenize document."""
        # Simple preprocessing
        text = doc.lower()
        tokens = text.split()
        
        # Filter stopwords and short tokens
        tokens = [
            t for t in tokens
            if t not in self.STOPWORDS and len(t) >= self.config.min_token_length
        ]
        
        return tokens
    
    def _build_vocabulary(self, tokenized_docs: List[List[str]]) -> Dict[str, int]:
        """Build vocabulary from documents."""
        word_freq = Counter()
        for doc in tokenized_docs:
            word_freq.update(doc)
        
        # Filter by document frequency
        min_df = self.config.min_document_frequency
        max_df_count = max(len(tokenized_docs) * self.config.max_document_percentage, 1)
        
        vocab = {
            word: idx for idx, (word, freq) in enumerate(
                (w, f) for w, f in word_freq.items()
                if min_df <= f <= max_df_count
            )
        }
        
        return vocab
    
    def _create_doc_term_matrix(self, tokenized_docs: List[List[str]], vocab: Dict[str, int]) -> List[Dict[int, int]]:
        """Create document-term matrix (as list of sparse vectors)."""
        matrix = []
        for doc in tokenized_docs:
            doc_vec = {}
            for word in doc:
                if word in vocab:
                    word_id = vocab[word]
                    doc_vec[word_id] = doc_vec.get(word_id, 0) + 1
            matrix.append(doc_vec)
        return matrix
    
    def _lda_modeling(self, tokenized_docs: List[List[str]], vocab: Dict[str, int]) -> Tuple[List[Topic], List[int]]:
        """Simple LDA-like topic modeling."""
        topics = []
        
        for _ in range(self.config.num_topics):
            # Simple topic: most frequent words per document cluster
            keywords = {}
            for doc in tokenized_docs:
                for word in doc[:5]:  # Top 5 words per doc
                    keywords[word] = keywords.get(word, 0) + 1
            
            top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:self.config.num_keywords_per_topic]
            
            topic = self._create_topic(
                name=f"Topic_{len(topics)}",
                keywords=[(w, f / sum(kw[1] for kw in top_keywords)) for w, f in top_keywords]
            )
            topics.append(topic)
        
        # Simple assignment: round-robin
        assignments = [i % len(topics) for i in range(len(tokenized_docs))]
        
        return topics, assignments
    
    def _kmeans_clustering(self, doc_term_matrix: List[Dict[int, int]], tokenized_docs: List[List[str]], vocab: Dict[str, int]) -> Tuple[List[Topic], List[int]]:
        """Simple K-means-like clustering."""
        k = min(self.config.num_topics, len(tokenized_docs))
        assignments = [i % k for i in range(len(tokenized_docs))]
        
        # Extract keywords for each cluster
        topics = []
        for cluster_id in range(k):
            cluster_docs = [tokenized_docs[i] for i, a in enumerate(assignments) if a == cluster_id]
            keywords = Counter()
            for doc in cluster_docs:
                keywords.update(doc)
            
            top_keywords = keywords.most_common(self.config.num_keywords_per_topic)
            
            topic = self._create_topic(
                name=f"Topic_{cluster_id}",
                keywords=[(w, f / len(cluster_docs)) if len(cluster_docs) > 0 else (w, f) for w, f in top_keywords]
            )
            topics.append(topic)
        
        return topics, assignments
    
    def _simple_topic_extraction(self, tokenized_docs: List[List[str]], vocab: Dict[str, int]) -> Tuple[List[Topic], List[int]]:
        """Simple topic extraction using frequency analysis."""
        all_words = Counter()
        for doc in tokenized_docs:
            all_words.update(doc)
        
        top_words = all_words.most_common(self.config.num_topics * self.config.num_keywords_per_topic)
        
        topics = []
        for topic_id in range(min(self.config.num_topics, len(tokenized_docs))):
            start_idx = topic_id * self.config.num_keywords_per_topic
            end_idx = start_idx + self.config.num_keywords_per_topic
            keywords = top_words[start_idx:end_idx]
            
            topic = self._create_topic(
                name=f"Topic_{topic_id}",
                keywords=keywords
            )
            topics.append(topic)
        
        assignments = [i % len(topics) for i in range(len(tokenized_docs))]
        
        return topics, assignments
    
    def _create_topic(self, name: str, keywords: List[Tuple[str, float]]) -> Topic:
        """Create a Topic object with category classification."""
        topic_id = self._topic_counter
        self._topic_counter += 1
        
        # Determine category based on keywords
        category = self._classify_topic_category(keywords)
        
        # Calculate coherence (simple: based on keyword weights)
        coherence = sum(w for _, w in keywords) / len(keywords) if keywords else 0.0
        
        topic = Topic(
            topic_id=topic_id,
            name=name,
            keywords=keywords,
            category=category,
            coherence_score=min(coherence, 1.0),
            frequency=1
        )
        
        self._topics[topic_id] = topic
        return topic
    
    def _create_default_topic(self) -> Topic:
        """Create a default/fallback topic."""
        return self._create_topic(
            name="General",
            keywords=[("general", 0.5)]
        )
    
    def _classify_topic_category(self, keywords: List[Tuple[str, float]]) -> TopicCategory:
        """Classify topic into category based on keywords."""
        keyword_words = set(w for w, _ in keywords)
        
        scores = {}
        for category, cat_keywords in self.TOPIC_KEYWORDS.items():
            score = len(keyword_words & cat_keywords)
            scores[category] = score
        
        best_category = max(scores, key=scores.get) if scores else TopicCategory.GENERAL
        return best_category
    
    def _calculate_silhouette_score(self, doc_term_matrix: List[Dict[int, int]], assignments: List[int]) -> float:
        """Calculate silhouette coefficient (simplified)."""
        if not assignments or len(set(assignments)) <= 1:
            return 0.0
        
        # Simple silhouette calculation
        cluster_count = len(set(assignments))
        total_score = 0.0
        
        for doc_id, cluster_id in enumerate(assignments):
            same_cluster = sum(1 for i, c in enumerate(assignments) if c == cluster_id and i != doc_id)
            diff_cluster = len(assignments) - same_cluster - 1
            
            if same_cluster > 0 and diff_cluster > 0:
                score = (diff_cluster - same_cluster) / max(same_cluster, diff_cluster)
                total_score += score
        
        return total_score / len(assignments) if assignments else 0.0
    
    def _calculate_inertia(self, doc_term_matrix: List[Dict[int, int]], assignments: List[int], topics: List[Topic]) -> float:
        """Calculate inertia (sum of squared distances)."""
        inertia = 0.0
        
        for doc_id, cluster_id in enumerate(assignments):
            if cluster_id < len(topics):
                # Simple distance based on matching keywords
                doc_keywords = set(doc_term_matrix[doc_id].keys()) if doc_id < len(doc_term_matrix) else set()
                topic_keywords = set(w for w, _ in topics[cluster_id].keywords)
                distance = 1.0 - (len(doc_keywords & topic_keywords) / max(len(doc_keywords), len(topic_keywords), 1))
                inertia += distance ** 2
        
        return inertia
    
    def _create_clusters(self, assignments: List[int]) -> List[List[int]]:
        """Create cluster lists from assignments."""
        clusters = {}
        for doc_id, cluster_id in enumerate(assignments):
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(doc_id)
        
        return list(clusters.values())
    
    def _generate_cache_key(self, documents: List[str]) -> str:
        """Generate cache key from documents."""
        import hashlib
        combined = "".join(documents[:3])  # Use first few docs
        return hashlib.md5(combined.encode()).hexdigest()


# Singleton instance
_topic_modeler = None


def get_topic_modeler() -> TopicModeler:
    """Get TopicModeler singleton instance."""
    global _topic_modeler
    if _topic_modeler is None:
        _topic_modeler = TopicModeler()
    return _topic_modeler
