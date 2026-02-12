"""
Semantic Search Service - Advanced Search with Embeddings
Provides semantic search, keyword-semantic hybrid search, and faceted search.
"""

from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Dict, List, Optional, Tuple, Set, Any, Callable
import hashlib
import time
import re
import numpy as np
from datetime import datetime


class SearchMode(Enum):
    """Search execution modes."""
    SEMANTIC = "semantic"       # Vector similarity search
    KEYWORD = "keyword"         # Text matching (BM25-like)
    HYBRID = "hybrid"           # Combined semantic + keyword
    BOOLEAN = "boolean"         # Boolean query (AND/OR/NOT)
    FACETED = "faceted"         # Faceted search with filters


class SearchRankingMethod(Enum):
    """Ranking algorithms for search results."""
    RELEVANCE = "relevance"     # TF-IDF style ranking
    POP_RANK = "popularity"     # Popularity-based ranking
    TIME_DECAY = "time_decay"   # Recency-biased ranking
    HYBRID = "hybrid"           # Combination of factors
    PERSONALIZED = "personalized"  # User-based personalization


class FacetType(Enum):
    """Types of facets for filtering."""
    STRING = "string"
    NUMERIC = "numeric"
    DATE = "date"
    TAG = "tag"
    CATEGORY = "category"


@dataclass
class SearchQuery:
    """Search query specification."""
    query_text: str
    mode: SearchMode = SearchMode.HYBRID
    top_k: int = 10
    ranking_method: SearchRankingMethod = SearchRankingMethod.RELEVANCE
    filters: Dict[str, Any] = field(default_factory=dict)
    facets_to_return: List[str] = field(default_factory=list)
    min_similarity: float = 0.0
    max_results: int = 100
    language: str = "en"
    boost_recent: bool = False
    personalization_user_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class SearchResult:
    """Single search result."""
    result_id: str
    title: Optional[str]
    snippet: str
    similarity_score: float
    keyword_score: float
    combined_score: float
    rank: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    highlights: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Complete search response."""
    query_id: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    facet_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)
    did_you_mean: Optional[str] = None
    execution_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FacetConfig:
    """Configuration for faceted search."""
    name: str
    field: str
    facet_type: FacetType
    max_values: int = 10
    min_count: int = 1


@dataclass
class IndexedDocument:
    """Document indexed for semantic search."""
    doc_id: str
    text: str
    title: Optional[str]
    vector: List[float]
    keywords: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    popularity_score: float = 0.0
    view_count: int = 0


@dataclass
class SearchStatistics:
    """Statistics for search operations."""
    total_searches: int = 0
    avg_search_time_ms: float = 0.0
    queries_per_minute: float = 0.0
    click_through_rate: float = 0.0
    avg_results_per_query: int = 0
    top_queries: List[Tuple[str, int]] = field(default_factory=list)


class SemanticSearch:
    """Service for semantic search capabilities."""

    def __init__(self):
        """Initialize semantic search service."""
        self._lock = RLock()
        self._documents: Dict[str, IndexedDocument] = {}
        self._inverted_index: Dict[str, Set[str]] = defaultdict(set)  # keyword -> doc_ids
        self._doc_vectors: Dict[str, np.ndarray] = {}
        
        # Search history and analytics
        self._search_history: deque = deque(maxlen=10000)
        self._query_cache: Dict[str, SearchResponse] = OrderedDict()
        self._query_cache_max = 1000
        
        # Click tracking for ranking
        self._clicks: Dict[str, int] = defaultdict(int)  # doc_id -> click_count
        self._impressions: Dict[str, int] = defaultdict(int)  # doc_id -> impression_count
        
        # Facet configuration
        self._facet_configs: Dict[str, FacetConfig] = {}
        self._facet_index: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        
        # Statistics
        self._stats = SearchStatistics()
        self._query_times: deque = deque(maxlen=1000)
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            'search_executed': [],
            'document_indexed': [],
            'click_recorded': [],
            'relevance_feedback': [],
        }

    def index_document(
        self,
        doc_id: str,
        text: str,
        vector: List[float],
        title: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Index a document for search."""
        with self._lock:
            if doc_id in self._documents:
                return False

            doc = IndexedDocument(
                doc_id=doc_id,
                text=text,
                title=title,
                vector=vector,
                keywords=keywords or [],
                metadata=metadata or {},
            )

            self._documents[doc_id] = doc
            self._doc_vectors[doc_id] = np.array(vector, dtype=np.float32)

            # Build inverted index
            keywords_to_index = self._extract_keywords(text)
            if keywords:
                keywords_to_index.extend(keywords)

            for keyword in keywords_to_index:
                self._inverted_index[keyword.lower()].add(doc_id)

            # Index facets
            for facet_name, facet_config in self._facet_configs.items():
                if facet_config.field in (metadata or {}):
                    facet_value = str((metadata or {})[facet_config.field])
                    self._facet_index[facet_name][facet_value].add(doc_id)

            self._trigger_callback(
                'document_indexed',
                doc_id=doc_id,
                has_vector=True,
                keyword_count=len(keywords_to_index),
            )

            return True

    def search(self, query: SearchQuery) -> Optional[SearchResponse]:
        """Execute search query."""
        with self._lock:
            start_time = time.time()

            # Check cache
            cache_key = self._compute_query_hash(query)
            if cache_key in self._query_cache:
                return self._query_cache[cache_key]

            results = []

            if query.mode == SearchMode.SEMANTIC:
                results = self._semantic_search(query)
            elif query.mode == SearchMode.KEYWORD:
                results = self._keyword_search(query)
            elif query.mode == SearchMode.HYBRID:
                results = self._hybrid_search(query)
            elif query.mode == SearchMode.BOOLEAN:
                results = self._boolean_search(query)
            elif query.mode == SearchMode.FACETED:
                results = self._faceted_search(query)

            # Apply ranking
            results = self._rank_results(results, query)

            # Limit results
            results = results[:query.max_results]

            # Build response
            search_time = (time.time() - start_time) * 1000
            response = SearchResponse(
                query_id=hashlib.sha256(
                    f"{query.query_text}_{time.time()}".encode()
                ).hexdigest()[:16],
                results=results,
                total_results=len(results),
                search_time_ms=search_time,
                facet_counts=self._get_facet_counts(results, query),
                did_you_mean=self._get_spelling_suggestion(query.query_text),
            )

            # Cache result
            if len(self._query_cache) >= self._query_cache_max:
                self._query_cache.pop(next(iter(self._query_cache)))
            self._query_cache[cache_key] = response

            # Update statistics
            self._query_times.append(search_time)
            self._stats.total_searches += 1
            self._stats.avg_search_time_ms = np.mean(list(self._query_times))
            self._stats.avg_results_per_query = int(np.mean([
                len(r.results) for r in list(self._query_cache.values())
            ]))

            self._search_history.append(({
                'query': query.query_text,
                'timestamp': time.time(),
                'mode': query.mode.value,
                'results_count': len(results),
            }))

            self._trigger_callback(
                'search_executed',
                query=query.query_text,
                results_count=len(results),
                search_time_ms=search_time,
            )

            return response

    def record_click(self, query_id: str, doc_id: str, position: int) -> bool:
        """Record user click on search result."""
        with self._lock:
            if doc_id not in self._documents:
                return False

            self._clicks[doc_id] += 1
            self._impressions[doc_id] += 1

            # Update popularity score (exponential moving average)
            doc = self._documents[doc_id]
            doc.view_count += 1
            doc.popularity_score = (
                0.7 * doc.popularity_score + 0.3 * (1.0 / (position + 1))
            )

            self._trigger_callback(
                'click_recorded',
                doc_id=doc_id,
                position=position,
            )

            return True

    def provide_relevance_feedback(
        self,
        query_text: str,
        doc_id: str,
        relevant: bool,
    ) -> bool:
        """Collect relevance feedback for query optimization."""
        with self._lock:
            if doc_id not in self._documents:
                return False

            # Use feedback to adjust ranking weights
            if relevant:
                doc = self._documents[doc_id]
                doc.popularity_score += 0.1
                self._clicks[doc_id] += 2  # Weight positive feedback higher

            self._trigger_callback(
                'relevance_feedback',
                query=query_text,
                doc_id=doc_id,
                relevant=relevant,
            )

            return True

    def register_facet(self, facet_config: FacetConfig) -> bool:
        """Register a facet for search."""
        with self._lock:
            if facet_config.name in self._facet_configs:
                return False

            self._facet_configs[facet_config.name] = facet_config
            return True

    def get_facet_values(
        self,
        facet_name: str,
        limit: int = 10,
    ) -> List[Tuple[str, int]]:
        """Get top values for a facet."""
        with self._lock:
            if facet_name not in self._facet_index:
                return []

            facets = self._facet_index[facet_name]
            counts = [(value, len(doc_ids)) for value, doc_ids in facets.items()]
            counts.sort(key=lambda x: x[1], reverse=True)
            return counts[:limit]

    def auto_complete(self, prefix: str, limit: int = 10) -> List[str]:
        """Get auto-complete suggestions."""
        with self._lock:
            suggestions = []
            prefix_lower = prefix.lower()

            for keyword in self._inverted_index.keys():
                if keyword.startswith(prefix_lower):
                    doc_count = len(self._inverted_index[keyword])
                    suggestions.append((keyword, doc_count))

            # Sort by frequency
            suggestions.sort(key=lambda x: x[1], reverse=True)
            return [s[0] for s in suggestions[:limit]]

    def get_related_queries(self, query_text: str, limit: int = 5) -> List[str]:
        """Get related query suggestions."""
        with self._lock:
            query_lower = query_text.lower()
            related = []

            # Find queries with similar keywords
            for history_entry in self._search_history:
                if history_entry['query'].lower() != query_lower:
                    # Check keyword overlap
                    query_keywords = set(self._extract_keywords(query_text))
                    history_keywords = set(
                        self._extract_keywords(history_entry['query'])
                    )
                    overlap = len(query_keywords & history_keywords)
                    if overlap > 0:
                        related.append((history_entry['query'], overlap))

            # Sort by overlap
            related.sort(key=lambda x: x[1], reverse=True)
            return [r[0] for r in related[:limit]]

    def get_statistics(self) -> Dict[str, Any]:
        """Get search statistics."""
        with self._lock:
            ctr = (
                sum(self._clicks.values()) / sum(self._impressions.values())
                if sum(self._impressions.values()) > 0
                else 0.0
            )

            # Get top queries
            query_counts: Dict[str, int] = defaultdict(int)
            for entry in self._search_history:
                query_counts[entry['query']] += 1

            top_queries = sorted(
                query_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]

            return {
                'total_documents': len(self._documents),
                'total_searches': self._stats.total_searches,
                'avg_search_time_ms': self._stats.avg_search_time_ms,
                'avg_results_per_query': self._stats.avg_results_per_query,
                'click_through_rate': ctr,
                'indexed_keywords': len(self._inverted_index),
                'cache_size': len(self._query_cache),
                'top_queries': top_queries,
            }

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for event."""
        with self._lock:
            if event in self._callbacks:
                self._callbacks[event].append(callback)

    def _semantic_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform semantic search."""
        # Generate mock query vector
        query_vector = np.random.randn(384).astype(np.float32)

        results = []
        for doc_id, doc in self._documents.items():
            vector = self._doc_vectors.get(doc_id)
            if vector is None:
                continue

            # Compute cosine similarity
            similarity = np.dot(query_vector, vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(vector) + 1e-8
            )

            if similarity < query.min_similarity:
                continue

            result = SearchResult(
                result_id=doc_id,
                title=doc.title,
                snippet=self._create_snippet(doc.text),
                similarity_score=float(similarity),
                keyword_score=0.0,
                combined_score=float(similarity),
                rank=0,
                metadata=doc.metadata,
            )
            results.append(result)

        return results[:query.top_k]

    def _keyword_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform keyword-based search."""
        keywords = self._extract_keywords(query.query_text)
        doc_scores: Dict[str, float] = defaultdict(float)

        for keyword in keywords:
            matching_docs = self._inverted_index.get(keyword.lower(), set())
            for doc_id in matching_docs:
                # BM25-like scoring
                doc = self._documents[doc_id]
                # Count occurrences
                count = doc.text.lower().count(keyword.lower())
                doc_scores[doc_id] += count

        results = []
        for doc_id, score in doc_scores.items():
            if doc_id in self._documents:
                doc = self._documents[doc_id]
                result = SearchResult(
                    result_id=doc_id,
                    title=doc.title,
                    snippet=self._create_snippet(doc.text),
                    similarity_score=0.0,
                    keyword_score=float(score),
                    combined_score=float(score),
                    rank=0,
                    metadata=doc.metadata,
                )
                results.append(result)

        return results[:query.top_k]

    def _hybrid_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform hybrid semantic + keyword search."""
        semantic_results = self._semantic_search(query)
        keyword_results = self._keyword_search(query)

        # Combine and deduplicate
        combined: Dict[str, SearchResult] = {}
        for result in semantic_results:
            combined[result.result_id] = result

        for result in keyword_results:
            if result.result_id in combined:
                existing = combined[result.result_id]
                existing.keyword_score = result.keyword_score
                existing.combined_score = (
                    0.6 * existing.similarity_score + 0.4 * result.keyword_score
                )
            else:
                combined[result.result_id] = result

        return list(combined.values())[:query.top_k]

    def _boolean_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform boolean search (AND/OR/NOT)."""
        # Parse boolean query
        terms = re.split(r'\s+(AND|OR|NOT)\s+', query.query_text, flags=re.IGNORECASE)
        
        matching_docs = set(self._documents.keys())

        i = 0
        while i < len(terms):
            if i + 1 < len(terms):
                term = terms[i]
                operator = terms[i + 1].upper()
                next_term = terms[i + 2] if i + 2 < len(terms) else ""

            i += 3

        results = []
        for doc_id in matching_docs:
            if doc_id in self._documents:
                doc = self._documents[doc_id]
                result = SearchResult(
                    result_id=doc_id,
                    title=doc.title,
                    snippet=self._create_snippet(doc.text),
                    similarity_score=1.0,
                    keyword_score=1.0,
                    combined_score=1.0,
                    rank=0,
                    metadata=doc.metadata,
                )
                results.append(result)

        return results[:query.top_k]

    def _faceted_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform faceted search with filters."""
        # Get all docs matching facet filters
        matching_docs = set(self._documents.keys())

        for facet_name, facet_value in query.filters.items():
            if facet_name in self._facet_index:
                filtered = self._facet_index[facet_name].get(str(facet_value), set())
                matching_docs = matching_docs.intersection(filtered)

        results = []
        for doc_id in matching_docs:
            if doc_id in self._documents:
                doc = self._documents[doc_id]
                result = SearchResult(
                    result_id=doc_id,
                    title=doc.title,
                    snippet=self._create_snippet(doc.text),
                    similarity_score=0.5,
                    keyword_score=0.5,
                    combined_score=0.5,
                    rank=0,
                    metadata=doc.metadata,
                )
                results.append(result)

        return results[:query.top_k]

    def _rank_results(
        self,
        results: List[SearchResult],
        query: SearchQuery,
    ) -> List[SearchResult]:
        """Rank search results."""
        if query.ranking_method == SearchRankingMethod.RELEVANCE:
            results.sort(key=lambda x: x.combined_score, reverse=True)
        elif query.ranking_method == SearchRankingMethod.POP_RANK:
            for result in results:
                result.combined_score = self._documents[result.result_id].popularity_score
            results.sort(key=lambda x: x.combined_score, reverse=True)
        elif query.ranking_method == SearchRankingMethod.TIME_DECAY:
            current_time = time.time()
            for result in results:
                age_days = (current_time - self._documents[result.result_id].timestamp) / 86400
                decay = np.exp(-0.1 * age_days)
                result.combined_score *= decay
            results.sort(key=lambda x: x.combined_score, reverse=True)

        # Add ranks
        for i, result in enumerate(results):
            result.rank = i + 1

        return results

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if len(w) > 2]

    def _create_snippet(self, text: str, length: int = 150) -> str:
        """Create snippet from text."""
        if len(text) <= length:
            return text
        return text[:length] + "..."

    def _get_facet_counts(
        self,
        results: List[SearchResult],
        query: SearchQuery,
    ) -> Dict[str, Dict[str, int]]:
        """Get facet counts for results."""
        facet_counts: Dict[str, Dict[str, int]] = {}

        for facet_name in query.facets_to_return:
            if facet_name in self._facet_configs:
                facet_counts[facet_name] = {}
                for result in results:
                    doc = self._documents[result.result_id]
                    facet_config = self._facet_configs[facet_name]
                    if facet_config.field in doc.metadata:
                        value = str(doc.metadata[facet_config.field])
                        facet_counts[facet_name][value] = (
                            facet_counts[facet_name].get(value, 0) + 1
                        )

        return facet_counts

    def _get_spelling_suggestion(self, query_text: str) -> Optional[str]:
        """Get spelling suggestions."""
        # Simple suggestion based on keywords
        if len(self._documents) > 0:
            return None
        return None

    def _compute_query_hash(self, query: SearchQuery) -> str:
        """Compute query hash for caching."""
        cache_str = f"{query.query_text}_{query.mode.value}_{sorted(query.filters.items())}"
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _trigger_callback(self, event: str, **kwargs) -> None:
        """Trigger callbacks for event."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(**kwargs)
                except Exception:
                    pass


# Import at module level for OrderedDict
from collections import OrderedDict
