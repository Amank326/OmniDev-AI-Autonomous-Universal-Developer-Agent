"""
Retrieval Engine - Advanced Document Retrieval
Coordinates semantic search, vector search, and ranking for document retrieval.
"""

from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Dict, List, Optional, Tuple, Set, Any, Callable
import hashlib
import time
import numpy as np
from datetime import datetime


class RetrievalMode(Enum):
    """Retrieval modes."""
    SEMANTIC = "semantic"       # Vector similarity
    KEYWORD = "keyword"         # Full-text search
    HYBRID = "hybrid"           # Semantic + keyword
    DENSE = "dense"             # Dense retrieval
    SPARSE = "sparse"           # Sparse retrieval (BM25)
    ADAPTIVE = "adaptive"       # Choose based on query


class QueryExpansionStrategy(Enum):
    """Query expansion strategies."""
    NONE = "none"
    SYNONYM = "synonym"         # Add synonyms
    RELATED_TERMS = "related_terms"  # Add related concepts
    QUERY_REWRITING = "query_rewriting"  # Rewrite query
    SUQ = "sub_query"           # Generate sub-queries
    PRF = "prf"                 # Pseudo-relevance feedback


class RerankerType(Enum):
    """Reranking model types."""
    CROSS_ENCODER = "cross_encoder"
    LISTWISE_LM = "listwise_lm"
    POINTWISE_LM = "pointwise_lm"
    LTR = "ltr"                # Learning to rank
    MLP = "mlp"                # Neural network


@dataclass
class RetrievalQuery:
    """Query for retrieval."""
    query_text: str
    query_id: str = field(default_factory=lambda: hashlib.md5(str(time.time()).encode()).hexdigest()[:16])
    retrieval_mode: RetrievalMode = RetrievalMode.HYBRID
    top_k: int = 10
    expansion_strategy: QueryExpansionStrategy = QueryExpansionStrategy.NONE
    filter_criteria: Dict[str, Any] = field(default_factory=dict)
    boost_recent: bool = False
    diversity_penalty: float = 0.0
    personalization_user_id: Optional[str] = None
    reranker_type: Optional[RerankerType] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class RetrievedDocument:
    """Retrieved document with ranking information."""
    doc_id: str
    text: str
    title: Optional[str]
    score: float
    retrieval_score: float
    rerank_score: float
    combined_score: float
    rank: int
    relevance: float
    match_type: str  # semantic, keyword, both
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval operations."""
    total_queries: int = 0
    avg_retrieval_time_ms: float = 0.0
    avg_results_count: int = 0
    ndcg_score: float = 0.0
    mrr_score: float = 0.0
    precision_at_10: float = 0.0
    recall_at_10: float = 0.0


class RetrievalEngine:
    """Advanced retrieval engine for document search."""

    def __init__(self):
        """Initialize retrieval engine."""
        self._lock = RLock()
        
        # Indices
        self._vector_index: Dict[str, np.ndarray] = {}
        self._inverted_index: Dict[str, Set[str]] = defaultdict(set)  # term -> doc_ids
        self._document_store: Dict[str, Dict[str, Any]] = {}
        
        # Query expansion
        self._expansion_cache: Dict[str, List[str]] = {}
        self._query_suggestions: Dict[str, List[str]] = {}
        
        # Reranking
        self._reranker_scores: Dict[str, Dict[str, float]] = {}
        
        # Cache
        self._retrieval_cache: Dict[str, List[RetrievedDocument]] = {}
        self._cache_max = 5000
        
        # Statistics and metrics
        self._metrics = RetrievalMetrics()
        self._retrieval_times: deque = deque(maxlen=1000)
        self._user_preferences: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Click-through data for learning
        self._ctr_data: deque = deque(maxlen=10000)
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            'retrieval_started': [],
            'query_expanded': [],
            'documents_reranked': [],
            'retrieval_completed': [],
            'cache_hit': [],
        }

    def retrieve(self, query: RetrievalQuery) -> List[RetrievedDocument]:
        """Retrieve documents matching query."""
        with self._lock:
            start_time = time.time()

            # Check cache
            cache_key = self._compute_cache_key(query)
            if cache_key in self._retrieval_cache:
                self._trigger_callback('cache_hit', query_id=query.query_id)
                return self._retrieval_cache[cache_key]

            self._trigger_callback('retrieval_started', query=query.query_text)

            # Expand query if enabled
            expanded_queries = [query.query_text]
            if query.expansion_strategy != QueryExpansionStrategy.NONE:
                expanded_queries = self._expand_query(
                    query.query_text,
                    query.expansion_strategy,
                )
                self._trigger_callback(
                    'query_expanded',
                    original=query.query_text,
                    expanded=expanded_queries,
                )

            # Retrieve using specified mode
            results = []
            if query.retrieval_mode == RetrievalMode.SEMANTIC:
                results = self._retrieve_semantic(expanded_queries, query)
            elif query.retrieval_mode == RetrievalMode.KEYWORD:
                results = self._retrieve_keyword(expanded_queries, query)
            elif query.retrieval_mode == RetrievalMode.HYBRID:
                results = self._retrieve_hybrid(expanded_queries, query)
            elif query.retrieval_mode == RetrievalMode.ADAPTIVE:
                results = self._retrieve_adaptive(expanded_queries, query)

            # Apply diversity penalty
            if query.diversity_penalty > 0:
                results = self._apply_diversity_penalty(results, query.diversity_penalty)

            # Rerank if specified
            if query.reranker_type:
                results = self._rerank_documents(
                    query.query_text,
                    results,
                    query.reranker_type,
                )
                self._trigger_callback(
                    'documents_reranked',
                    reranker_type=query.reranker_type.value,
                )

            # Limit results
            results = results[:query.top_k]

            # Add ranks
            for i, result in enumerate(results):
                result.rank = i + 1

            # Cache result
            if len(self._retrieval_cache) >= self._cache_max:
                first_key = next(iter(self._retrieval_cache))
                del self._retrieval_cache[first_key]
            self._retrieval_cache[cache_key] = results

            # Update metrics
            retrieval_time = (time.time() - start_time) * 1000
            self._retrieval_times.append(retrieval_time)
            self._metrics.total_queries += 1
            self._metrics.avg_retrieval_time_ms = np.mean(list(self._retrieval_times))
            self._metrics.avg_results_count = int(np.mean([len(r) for r in self._retrieval_cache.values()]))

            self._trigger_callback(
                'retrieval_completed',
                query_id=query.query_id,
                results_count=len(results),
                time_ms=retrieval_time,
            )

            return results

    def index_document(
        self,
        doc_id: str,
        text: str,
        title: Optional[str],
        vector: Optional[List[float]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Index document for retrieval."""
        with self._lock:
            if doc_id in self._document_store:
                return False

            # Store document
            self._document_store[doc_id] = {
                'text': text,
                'title': title,
                'vector': vector,
                'metadata': metadata or {},
                'indexed_at': time.time(),
            }

            # Index vector
            if vector:
                self._vector_index[doc_id] = np.array(vector, dtype=np.float32)

            # Index keywords
            terms = self._extract_terms(text)
            for term in terms:
                self._inverted_index[term].add(doc_id)

            return True

    def record_interaction(
        self,
        query_id: str,
        doc_id: str,
        interaction_type: str,  # click, view, skip, etc.
        position: int,
    ) -> None:
        """Record user interaction with retrieved document."""
        with self._lock:
            self._ctr_data.append({
                'query_id': query_id,
                'doc_id': doc_id,
                'type': interaction_type,
                'position': position,
                'timestamp': time.time(),
            })

    def get_feedback_for_query(self, query_id: str) -> Dict[str, Any]:
        """Get feedback data for a query."""
        with self._lock:
            interactions = [d for d in self._ctr_data if d['query_id'] == query_id]
            
            click_count = sum(1 for d in interactions if d['type'] == 'click')
            view_count = len(interactions)
            ctr = click_count / view_count if view_count > 0 else 0.0

            return {
                'query_id': query_id,
                'interactions': interactions,
                'click_count': click_count,
                'view_count': view_count,
                'ctr': ctr,
            }

    def set_user_preference(
        self,
        user_id: str,
        preference_name: str,
        value: Any,
    ) -> None:
        """Set user preference for retrieval."""
        with self._lock:
            self._user_preferences[user_id][preference_name] = value

    def get_user_preference(
        self,
        user_id: str,
        preference_name: str,
        default: Any = None,
    ) -> Any:
        """Get user preference."""
        with self._lock:
            return self._user_preferences.get(user_id, {}).get(preference_name, default)

    def batch_retrieve(
        self,
        queries: List[RetrievalQuery],
    ) -> Dict[str, List[RetrievedDocument]]:
        """Batch retrieve for multiple queries."""
        with self._lock:
            results = {}
            for query in queries:
                results[query.query_id] = self.retrieve(query)

            return results

    def get_similar_documents(
        self,
        doc_id: str,
        top_k: int = 5,
    ) -> List[RetrievedDocument]:
        """Get documents similar to a given document."""
        with self._lock:
            if doc_id not in self._document_store:
                return []

            if doc_id not in self._vector_index:
                return []

            query_vector = self._vector_index[doc_id]
            similarities = []

            for other_id, other_vector in self._vector_index.items():
                if other_id == doc_id:
                    continue

                # Cosine similarity
                similarity = np.dot(query_vector, other_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(other_vector) + 1e-8
                )

                doc_data = self._document_store[other_id]
                result = RetrievedDocument(
                    doc_id=other_id,
                    text=doc_data['text'][:200],
                    title=doc_data.get('title'),
                    score=float(similarity),
                    retrieval_score=float(similarity),
                    rerank_score=0.0,
                    combined_score=float(similarity),
                    rank=0,
                    relevance=float(similarity),
                    match_type='semantic',
                    metadata=doc_data.get('metadata', {}),
                )
                similarities.append(result)

            similarities.sort(key=lambda x: x.score, reverse=True)
            return similarities[:top_k]

    def get_metrics(self) -> Dict[str, Any]:
        """Get retrieval metrics."""
        with self._lock:
            return {
                'total_queries': self._metrics.total_queries,
                'avg_retrieval_time_ms': self._metrics.avg_retrieval_time_ms,
                'avg_results_count': self._metrics.avg_results_count,
                'cache_size': len(self._retrieval_cache),
                'indexed_documents': len(self._document_store),
                'ndcg_score': self._metrics.ndcg_score,
                'mrr_score': self._metrics.mrr_score,
            }

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for event."""
        with self._lock:
            if event in self._callbacks:
                self._callbacks[event].append(callback)

    def _retrieve_semantic(
        self,
        queries: List[str],
        query_obj: RetrievalQuery,
    ) -> List[RetrievedDocument]:
        """Semantic retrieval using vectors."""
        # Mock semantic retrieval
        results = []
        for i, doc_id in enumerate(list(self._document_store.keys())[:10]):
            doc_data = self._document_store[doc_id]
            result = RetrievedDocument(
                doc_id=doc_id,
                text=doc_data['text'][:200],
                title=doc_data.get('title'),
                score=0.9 - (i * 0.05),
                retrieval_score=0.9 - (i * 0.05),
                rerank_score=0.0,
                combined_score=0.9 - (i * 0.05),
                rank=0,
                relevance=0.9 - (i * 0.05),
                match_type='semantic',
                metadata=doc_data.get('metadata', {}),
            )
            results.append(result)

        return results

    def _retrieve_keyword(
        self,
        queries: List[str],
        query_obj: RetrievalQuery,
    ) -> List[RetrievedDocument]:
        """Keyword retrieval using inverted index."""
        results_dict: Dict[str, float] = defaultdict(float)

        for query in queries:
            terms = self._extract_terms(query)
            for term in terms:
                for doc_id in self._inverted_index.get(term, set()):
                    results_dict[doc_id] += 1.0

        # Convert to results
        results = []
        for doc_id, score in sorted(results_dict.items(), key=lambda x: x[1], reverse=True):
            if doc_id in self._document_store:
                doc_data = self._document_store[doc_id]
                result = RetrievedDocument(
                    doc_id=doc_id,
                    text=doc_data['text'][:200],
                    title=doc_data.get('title'),
                    score=score,
                    retrieval_score=score,
                    rerank_score=0.0,
                    combined_score=score,
                    rank=0,
                    relevance=score,
                    match_type='keyword',
                    metadata=doc_data.get('metadata', {}),
                )
                results.append(result)

        return results

    def _retrieve_hybrid(
        self,
        queries: List[str],
        query_obj: RetrievalQuery,
    ) -> List[RetrievedDocument]:
        """Hybrid retrieval combining semantic and keyword."""
        semantic = self._retrieve_semantic(queries, query_obj)
        keyword = self._retrieve_keyword(queries, query_obj)

        # Combine and deduplicate
        combined: Dict[str, RetrievedDocument] = {}
        for result in semantic:
            combined[result.doc_id] = result

        for result in keyword:
            if result.doc_id in combined:
                existing = combined[result.doc_id]
                # Average scores
                existing.combined_score = (
                    0.6 * existing.retrieval_score + 0.4 * result.retrieval_score
                )
                existing.match_type = 'both'
            else:
                result.combined_score = result.retrieval_score
                combined[result.doc_id] = result

        # Sort by combined score
        results = sorted(
            combined.values(),
            key=lambda x: x.combined_score,
            reverse=True,
        )

        return results

    def _retrieve_adaptive(
        self,
        queries: List[str],
        query_obj: RetrievalQuery,
    ) -> List[RetrievedDocument]:
        """Adaptive retrieval choosing best strategy."""
        # Heuristic: use semantic if vectors available, else keyword
        if self._vector_index:
            return self._retrieve_semantic(queries, query_obj)
        else:
            return self._retrieve_keyword(queries, query_obj)

    def _rerank_documents(
        self,
        query: str,
        documents: List[RetrievedDocument],
        reranker_type: RerankerType,
    ) -> List[RetrievedDocument]:
        """Rerank documents using specified reranker."""
        # Mock reranking (apply slight adjustments)
        for i, doc in enumerate(documents):
            if reranker_type == RerankerType.CROSS_ENCODER:
                # Mock cross-encoder score
                doc.rerank_score = doc.retrieval_score * (1.0 - i * 0.05)
            else:
                doc.rerank_score = doc.retrieval_score

            doc.combined_score = 0.7 * doc.retrieval_score + 0.3 * doc.rerank_score

        # Re-sort by combined score
        documents.sort(key=lambda x: x.combined_score, reverse=True)
        return documents

    def _apply_diversity_penalty(
        self,
        documents: List[RetrievedDocument],
        penalty: float,
    ) -> List[RetrievedDocument]:
        """Apply diversity penalty to reduce redundancy."""
        # Mock diversity application
        for i, doc in enumerate(documents):
            doc.combined_score *= (1.0 - penalty * (i / max(len(documents), 1)))

        documents.sort(key=lambda x: x.combined_score, reverse=True)
        return documents

    def _expand_query(
        self,
        query: str,
        strategy: QueryExpansionStrategy,
    ) -> List[str]:
        """Expand query with additional terms."""
        expanded = [query]

        if strategy == QueryExpansionStrategy.SYNONYM:
            # Mock synonym expansion
            expanded.append(query)  # Would add synonyms
        elif strategy == QueryExpansionStrategy.RELATED_TERMS:
            # Mock related terms
            expanded.append(query)
        elif strategy == QueryExpansionStrategy.SUQ:
            # Generate sub-queries
            expanded.append(query)

        return expanded

    def _extract_terms(self, text: str) -> List[str]:
        """Extract terms from text."""
        # Simple tokenization
        return text.lower().split()

    def _compute_cache_key(self, query: RetrievalQuery) -> str:
        """Compute cache key for query."""
        key_str = f"{query.query_text}_{query.retrieval_mode.value}_{query.top_k}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _trigger_callback(self, event: str, **kwargs) -> None:
        """Trigger callbacks for event."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(**kwargs)
                except Exception:
                    pass
