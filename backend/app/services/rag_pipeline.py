"""
RAG Pipeline Service - Retrieval-Augmented Generation
Orchestrates retrieval and generation for context-aware LLM responses.
"""

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Dict, List, Optional, Tuple, Any, Callable
import hashlib
import time
import json
from datetime import datetime


class LLMModel(Enum):
    """Supported LLM models."""
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_35_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    MISTRAL_LARGE = "mistral-large"
    MISTRAL_MEDIUM = "mistral-medium"
    LLAMA_2_70B = "llama-2-70b"
    LLAMA_2_13B = "llama-2-13b"
    PALM_2 = "palm-2"
    COHERE_COMMAND = "command"


class RetrievalStrategy(Enum):
    """Strategies for retrieving context."""
    SEMANTIC = "semantic"          # Vector similarity search
    BM25 = "bm25"                  # BM25 keyword matching
    HYBRID = "hybrid"              # Combined semantic + BM25
    RERANKING = "reranking"        # Use reranker to score candidates
    MULTI_HOP = "multi_hop"        # Multi-hop reasoning over documents
    ADAPTIVE = "adaptive"          # Adapt strategy based on query


class PromptStrategy(Enum):
    """Strategies for prompt engineering."""
    SIMPLE = "simple"              # Direct question + context
    CHAIN_OF_THOUGHT = "chain_of_thought"  # Step-by-step reasoning
    TREE_OF_THOUGHT = "tree_of_thought"  # Multiple reasoning paths
    HYDE = "hyde"                  # Hypothetical document embeddings
    FLARE = "flare"                # Few-shot prompting
    IN_CONTEXT_LEARNING = "in_context_learning"  # In-context examples


@dataclass
class RetrievedContext:
    """Retrieved context document."""
    doc_id: str
    text: str
    title: Optional[str]
    score: float
    source: str
    relevance: float
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGInput:
    """Input to RAG pipeline."""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    knowledge_base_name: str = "default"
    retrieval_strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    prompt_strategy: PromptStrategy = PromptStrategy.SIMPLE
    llm_model: LLMModel = LLMModel.GPT_35_TURBO
    top_k: int = 5
    max_context_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 0.9
    max_output_tokens: int = 500
    include_sources: bool = True
    stream_response: bool = False
    metadata_filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGOutput:
    """Output from RAG pipeline."""
    query: str
    response: str
    retrieved_documents: List[RetrievedContext]
    reasoning_steps: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    sources: List[str] = field(default_factory=list)
    stop_reason: str = "stop"
    prompt_used: str = ""
    tokens_used: Dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0
    model_used: LLMModel = LLMModel.GPT_35_TURBO


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline."""
    default_llm: LLMModel = LLMModel.GPT_35_TURBO
    default_retrieval_strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    default_prompt_strategy: PromptStrategy = PromptStrategy.SIMPLE
    default_top_k: int = 5
    default_max_context_tokens: int = 2000
    enable_reranking: bool = True
    reranker_model: Optional[str] = None
    enable_query_expansion: bool = True
    enable_answer_generation: bool = True
    enable_source_attribution: bool = True
    cache_results: bool = True
    cache_ttl_seconds: int = 3600
    collect_feedback: bool = True


@dataclass
class RAGMetrics:
    """Metrics for RAG operations."""
    total_queries: int = 0
    avg_latency_ms: float = 0.0
    retrieval_success_rate: float = 0.0
    generation_success_rate: float = 0.0
    avg_retrieval_time_ms: float = 0.0
    avg_generation_time_ms: float = 0.0
    total_tokens_used: int = 0
    avg_source_count: int = 0


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline."""

    def __init__(self, config: RAGConfig = None):
        """Initialize RAG pipeline."""
        self._lock = RLock()
        self._config = config or RAGConfig()
        
        # Pipeline stages
        self._query_processors: List[Callable] = []
        self._retrievers: Dict[RetrievalStrategy, Callable] = {}
        self._rerankers: List[Callable] = []
        self._generators: Dict[str, Callable] = {}
        
        # Cache
        self._response_cache: Dict[str, RAGOutput] = {}
        self._cache_max = 10000
        
        # Metrics
        self._metrics = RAGMetrics()
        self._latencies: deque = deque(maxlen=1000)
        
        # Session tracking
        self._sessions: Dict[str, List[RAGInput]] = {}
        self._session_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Feedback
        self._feedback: deque = deque(maxlen=10000)
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            'retrieval_started': [],
            'retrieval_completed': [],
            'generation_started': [],
            'generation_completed': [],
            'pipeline_completed': [],
            'feedback_received': [],
        }

    def execute(self, rag_input: RAGInput) -> Optional[RAGOutput]:
        """Execute RAG pipeline."""
        with self._lock:
            start_time = time.time()

            # Check cache
            cache_key = self._compute_cache_key(rag_input)
            if self._config.cache_results and cache_key in self._response_cache:
                return self._response_cache[cache_key]

            # Step 1: Process query
            processed_query = self._process_query(rag_input.query)
            self._trigger_callback('retrieval_started', query=processed_query)

            # Step 2: Retrieve context
            retrieved_docs = self._retrieve_context(
                query=processed_query,
                strategy=rag_input.retrieval_strategy,
                top_k=rag_input.top_k,
                kb_name=rag_input.knowledge_base_name,
                filters=rag_input.metadata_filters,
            )

            if not retrieved_docs:
                # Fallback: Return empty response
                output = RAGOutput(
                    query=rag_input.query,
                    response="I apologize, but I could not find relevant information to answer your question.",
                    retrieved_documents=[],
                    confidence_score=0.0,
                    model_used=rag_input.llm_model,
                )
                return self._finalize_output(output, start_time, rag_input)

            self._trigger_callback('retrieval_completed', docs_count=len(retrieved_docs))

            # Step 3: Rerank if enabled
            if self._config.enable_reranking:
                retrieved_docs = self._rerank_documents(
                    query=processed_query,
                    documents=retrieved_docs,
                )

            # Step 4: Build context
            context = self._build_context(
                documents=retrieved_docs,
                max_tokens=rag_input.max_context_tokens,
            )

            # Step 5: Generate response
            self._trigger_callback('generation_started')
            
            response = self._generate_response(
                query=rag_input.query,
                context=context,
                llm_model=rag_input.llm_model,
                prompt_strategy=rag_input.prompt_strategy,
                temperature=rag_input.temperature,
                top_p=rag_input.top_p,
                max_tokens=rag_input.max_output_tokens,
            )

            self._trigger_callback('generation_completed')

            # Step 6: Build output
            output = RAGOutput(
                query=rag_input.query,
                response=response['text'],
                retrieved_documents=retrieved_docs,
                reasoning_steps=response.get('reasoning_steps', []),
                confidence_score=self._compute_confidence(retrieved_docs, response),
                sources=[doc.source for doc in retrieved_docs] if rag_input.include_sources else [],
                prompt_used=response.get('prompt', ''),
                tokens_used=response.get('tokens', {}),
                model_used=rag_input.llm_model,
            )

            output = self._finalize_output(output, start_time, rag_input)

            # Cache result
            if self._config.cache_results:
                if len(self._response_cache) >= self._cache_max:
                    first_key = next(iter(self._response_cache))
                    del self._response_cache[first_key]
                self._response_cache[cache_key] = output

            # Track session
            if rag_input.session_id:
                if rag_input.session_id not in self._sessions:
                    self._sessions[rag_input.session_id] = []
                self._sessions[rag_input.session_id].append(rag_input)

            self._trigger_callback(
                'pipeline_completed',
                query=rag_input.query,
                latency_ms=output.latency_ms,
            )

            return output

    def provide_feedback(
        self,
        output_id: str,
        rating: int,  # 1-5
        feedback_text: Optional[str] = None,
        is_relevant: Optional[bool] = None,
    ) -> bool:
        """Provide feedback on RAG output."""
        with self._lock:
            feedback_entry = {
                'output_id': output_id,
                'rating': rating,
                'feedback_text': feedback_text,
                'is_relevant': is_relevant,
                'timestamp': time.time(),
            }

            self._feedback.append(feedback_entry)

            self._trigger_callback(
                'feedback_received',
                rating=rating,
                is_relevant=is_relevant,
            )

            return True

    def register_retriever(
        self,
        strategy: RetrievalStrategy,
        retriever_fn: Callable,
    ) -> None:
        """Register custom retriever function."""
        with self._lock:
            self._retrievers[strategy] = retriever_fn

    def register_generator(
        self,
        model_name: str,
        generator_fn: Callable,
    ) -> None:
        """Register custom generator function."""
        with self._lock:
            self._generators[model_name] = generator_fn

    def register_query_processor(self, processor_fn: Callable) -> None:
        """Register query preprocessing function."""
        with self._lock:
            self._query_processors.append(processor_fn)

    def get_session_history(self, session_id: str) -> List[RAGInput]:
        """Get conversation history for session."""
        with self._lock:
            return self._sessions.get(session_id, [])

    def get_metrics(self) -> Dict[str, Any]:
        """Get RAG pipeline metrics."""
        with self._lock:
            avg_latency = (
                sum(self._latencies) / len(self._latencies)
                if self._latencies
                else 0.0
            )

            return {
                'total_queries': self._metrics.total_queries,
                'avg_latency_ms': avg_latency,
                'retrieval_success_rate': self._metrics.retrieval_success_rate,
                'generation_success_rate': self._metrics.generation_success_rate,
                'avg_retrieval_time_ms': self._metrics.avg_retrieval_time_ms,
                'avg_generation_time_ms': self._metrics.avg_generation_time_ms,
                'total_tokens_used': self._metrics.total_tokens_used,
                'cache_size': len(self._response_cache),
                'feedback_count': len(self._feedback),
                'avg_feedback_rating': self._compute_avg_feedback_rating(),
            }

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for event."""
        with self._lock:
            if event in self._callbacks:
                self._callbacks[event].append(callback)

    def _process_query(self, query: str) -> str:
        """Process and potentially expand query."""
        processed = query

        # Apply registered processors
        for processor in self._query_processors:
            try:
                processed = processor(processed)
            except Exception:
                pass

        # Query expansion (mock)
        if self._config.enable_query_expansion:
            processed = self._expand_query(processed)

        return processed

    def _expand_query(self, query: str) -> str:
        """Expand query with related terms."""
        # Mock query expansion
        return query

    def _retrieve_context(
        self,
        query: str,
        strategy: RetrievalStrategy,
        top_k: int,
        kb_name: str,
        filters: Dict[str, Any],
    ) -> List[RetrievedContext]:
        """Retrieve relevant context."""
        # Mock retrieval
        docs = []
        for i in range(top_k):
            docs.append(RetrievedContext(
                doc_id=f"doc_{i}",
                text=f"This is mock context document {i} related to your query.",
                title=f"Document {i}",
                score=1.0 - (i * 0.1),  # Decreasing scores
                source=f"kb:{kb_name}/doc_{i}",
                relevance=1.0 - (i * 0.1),
                token_count=100,
            ))

        return docs

    def _rerank_documents(
        self,
        query: str,
        documents: List[RetrievedContext],
    ) -> List[RetrievedContext]:
        """Rerank documents using cross-encoder."""
        # Mock reranking (keep order for demo)
        return documents

    def _build_context(
        self,
        documents: List[RetrievedContext],
        max_tokens: int,
    ) -> str:
        """Build context string from documents."""
        context_parts = []
        token_count = 0

        for doc in documents:
            if token_count + doc.token_count > max_tokens:
                break

            context_parts.append(f"[{doc.title}]\n{doc.text}")
            token_count += doc.token_count

        return "\n\n".join(context_parts)

    def _generate_response(
        self,
        query: str,
        context: str,
        llm_model: LLMModel,
        prompt_strategy: PromptStrategy,
        temperature: float,
        top_p: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """Generate response using LLM."""
        # Build prompt
        prompt = self._build_prompt(query, context, prompt_strategy)

        # Mock generation
        response_text = f"Based on the provided context, I can answer your question about '{query}'."

        return {
            'text': response_text,
            'prompt': prompt,
            'tokens': {
                'prompt': len(prompt.split()),
                'completion': len(response_text.split()),
                'total': len(prompt.split()) + len(response_text.split()),
            },
            'reasoning_steps': [],
        }

    def _build_prompt(
        self,
        query: str,
        context: str,
        prompt_strategy: PromptStrategy,
    ) -> str:
        """Build prompt based on strategy."""
        if prompt_strategy == PromptStrategy.SIMPLE:
            return f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        elif prompt_strategy == PromptStrategy.CHAIN_OF_THOUGHT:
            return f"Context:\n{context}\n\nQuestion: {query}\n\nLet me think through this step by step:"
        elif prompt_strategy == PromptStrategy.IN_CONTEXT_LEARNING:
            return f"Context:\n{context}\n\nQuestion: {query}\n\nBased on similar examples, the answer is:"
        else:
            return f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"

    def _compute_confidence(
        self,
        documents: List[RetrievedContext],
        response: Dict[str, Any],
    ) -> float:
        """Compute confidence score for response."""
        if not documents:
            return 0.0

        avg_doc_score = sum(doc.score for doc in documents) / len(documents)
        return avg_doc_score

    def _finalize_output(
        self,
        output: RAGOutput,
        start_time: float,
        rag_input: RAGInput,
    ) -> RAGOutput:
        """Finalize output and update metrics."""
        output.latency_ms = (time.time() - start_time) * 1000

        # Update metrics
        self._latencies.append(output.latency_ms)
        self._metrics.total_queries += 1
        self._metrics.avg_latency_ms = sum(self._latencies) / len(self._latencies)
        self._metrics.avg_source_count = len(output.sources)

        return output

    def _compute_cache_key(self, rag_input: RAGInput) -> str:
        """Compute cache key for RAG input."""
        key_str = f"{rag_input.query}_{rag_input.knowledge_base_name}_{rag_input.retrieval_strategy.value}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _compute_avg_feedback_rating(self) -> float:
        """Compute average feedback rating."""
        if not self._feedback:
            return 0.0

        ratings = [f['rating'] for f in self._feedback if 'rating' in f]
        return sum(ratings) / len(ratings) if ratings else 0.0

    def _trigger_callback(self, event: str, **kwargs) -> None:
        """Trigger callbacks for event."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(**kwargs)
                except Exception:
                    pass
