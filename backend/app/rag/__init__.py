"""
RAG Module
==========

Retrieval-Augmented Generation (RAG) for context-aware AI responses.
"""

from app.rag.semantic_search import (
    SemanticSearchService,
    semantic_search_service,
    EmbeddingModel,
    VectorStore,
)
from app.rag.knowledge_base import (
    KnowledgeBaseManager,
    knowledge_base_manager,
    Document,
    DocumentChunk,
    DocumentSource,
    DocumentChunkStrategy,
)
from app.rag.retrieval import (
    RAGService,
    rag_service,
    RAGContext,
    PromptTemplate,
)

__all__ = [
    # Semantic Search
    "SemanticSearchService",
    "semantic_search_service",
    "EmbeddingModel",
    "VectorStore",
    # Knowledge Base
    "KnowledgeBaseManager",
    "knowledge_base_manager",
    "Document",
    "DocumentChunk",
    "DocumentSource",
    "DocumentChunkStrategy",
    # RAG Retrieval
    "RAGService",
    "rag_service",
    "RAGContext",
    "PromptTemplate",
]
