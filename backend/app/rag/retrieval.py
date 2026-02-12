"""
RAG (Retrieval-Augmented Generation) Service
==============================================

Context-aware response generation with retrieved documents.
Integrates semantic search with agent prompts for enhanced accuracy.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.rag.knowledge_base import knowledge_base_manager, DocumentSource
from app.rag.semantic_search import semantic_search_service

logger = logging.getLogger(__name__)


class RAGContext:
    """Context retrieved from knowledge base."""
    
    def __init__(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        context_text: str,
    ):
        """Initialize RAG context."""
        self.query = query
        self.retrieved_docs = retrieved_docs
        self.context_text = context_text
        self.timestamp = datetime.utcnow()
        self.metadata = {
            "doc_count": len(retrieved_docs),
            "timestamp": self.timestamp.isoformat(),
        }


class PromptTemplate:
    """Template for constructing prompts with context."""
    
    def __init__(self, template: str):
        """Initialize with template string."""
        self.template = template
    
    def format(
        self,
        query: str,
        context: str,
        **kwargs,
    ) -> str:
        """
        Format template with query and context.
        
        Args:
            query: User query
            context: Retrieved context
            **kwargs: Additional template variables
        
        Returns:
            Formatted prompt
        """
        return self.template.format(
            query=query,
            context=context,
            **kwargs,
        )


class RAGService:
    """
    Service for Retrieval-Augmented Generation.
    """
    
    # Default prompt templates
    CONTEXT_PROMPT = """Use the following context to answer the question. If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {query}

Answer:"""

    CODEBASE_PROMPT = """You are a code assistant. Use the following code context to answer the question.

Code Context:
{context}

Question: {query}

Helpful Code Solution:"""

    DOCUMENTATION_PROMPT = """You are a documentation assistant. Use the following documentation to answer the question.

Documentation:
{context}

Question: {query}

Answer based on the documentation:"""
    
    def __init__(self):
        """Initialize RAG service."""
        self.templates: Dict[str, PromptTemplate] = {
            "default": PromptTemplate(self.CONTEXT_PROMPT),
            "code": PromptTemplate(self.CODEBASE_PROMPT),
            "documentation": PromptTemplate(self.DOCUMENTATION_PROMPT),
        }
        self.retrieval_history: List[Dict[str, Any]] = []
    
    # ========================================================================
    # Knowledge Base Integration
    # ========================================================================
    
    def add_document(
        self,
        title: str,
        content: str,
        source: DocumentSource = DocumentSource.FILE,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_chunk: bool = True,
        auto_index: bool = True,
    ) -> int:
        """
        Add document to knowledge base.
        
        Args:
            title: Document title
            content: Document content
            source: Document source type
            source_url: Source URL
            metadata: Additional metadata
            auto_chunk: Automatically chunk document
            auto_index: Automatically index chunks
        
        Returns:
            Document ID
        """
        try:
            doc_id = knowledge_base_manager.add_document(
                title=title,
                content=content,
                source=source,
                source_url=source_url,
                metadata=metadata,
            )
            
            if auto_chunk:
                knowledge_base_manager.chunk_document(doc_id)
            
            if auto_index:
                knowledge_base_manager.index_document(doc_id)
            
            logger.info(f"Added and processed document {doc_id}: {title}")
            return doc_id
        
        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            return -1
    
    def add_code_file(
        self,
        title: str,
        code_content: str,
        file_path: str,
        auto_chunk: bool = True,
        auto_index: bool = True,
    ) -> int:
        """Add code file to knowledge base."""
        return self.add_document(
            title=title,
            content=code_content,
            source=DocumentSource.CODE,
            source_url=file_path,
            metadata={"file_path": file_path},
            auto_chunk=auto_chunk,
            auto_index=auto_index,
        )
    
    def add_documentation(
        self,
        title: str,
        doc_content: str,
        doc_url: Optional[str] = None,
        auto_chunk: bool = True,
        auto_index: bool = True,
    ) -> int:
        """Add documentation to knowledge base."""
        return self.add_document(
            title=title,
            content=doc_content,
            source=DocumentSource.DOCUMENTATION,
            source_url=doc_url,
            auto_chunk=auto_chunk,
            auto_index=auto_index,
        )
    
    # ========================================================================
    # Context Retrieval
    # ========================================================================
    
    def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        include_metadata: bool = True,
    ) -> RAGContext:
        """
        Retrieve context for a query.
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            include_metadata: Include document metadata
        
        Returns:
            RAG context with retrieved documents
        """
        try:
            # Retrieve relevant documents
            retrieved_docs = knowledge_base_manager.retrieve(query, top_k=top_k)
            
            # Format as context string
            context_text = knowledge_base_manager.retrieve_with_context(
                query,
                top_k=top_k,
            )
            
            # Create RAG context
            context = RAGContext(
                query=query,
                retrieved_docs=retrieved_docs,
                context_text=context_text,
            )
            
            # Log retrieval
            self.retrieval_history.append({
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "doc_count": len(retrieved_docs),
                "context": context_text[:200],  # Log first 200 chars
            })
            
            logger.debug(f"Retrieved {len(retrieved_docs)} documents for query: {query}")
            return context
        
        except Exception as e:
            logger.error(f"Failed to retrieve context: {str(e)}")
            return RAGContext(
                query=query,
                retrieved_docs=[],
                context_text="",
            )
    
    def retrieve_by_source(
        self,
        query: str,
        source: DocumentSource,
        top_k: int = 5,
    ) -> RAGContext:
        """
        Retrieve context from specific source.
        
        Args:
            query: Search query
            source: Document source type
            top_k: Number of results
        
        Returns:
            RAG context with filtered documents
        """
        try:
            # Retrieve all results
            all_results = knowledge_base_manager.retrieve(query, top_k=top_k * 2)
            
            # Filter by source
            filtered = [
                r for r in all_results
                if r['metadata'].get('source') == source.value
            ][:top_k]
            
            # Format context
            context_parts = [
                f"[{r['metadata'].get('title', 'Unknown')}]\n{r['text']}"
                for r in filtered
            ]
            context_text = "\n\n---\n\n".join(context_parts)
            
            return RAGContext(
                query=query,
                retrieved_docs=filtered,
                context_text=context_text,
            )
        
        except Exception as e:
            logger.error(f"Failed to retrieve by source: {str(e)}")
            return RAGContext(query=query, retrieved_docs=[], context_text="")
    
    # ========================================================================
    # Prompt Engineering
    # ========================================================================
    
    def augment_prompt(
        self,
        query: str,
        template_name: str = "default",
        context: Optional[RAGContext] = None,
        **kwargs,
    ) -> str:
        """
        Augment query with retrieved context.
        
        Args:
            query: Original query
            template_name: Prompt template to use
            context: Pre-retrieved context (optional)
            **kwargs: Additional template variables
        
        Returns:
            Augmented prompt with context
        """
        try:
            # Retrieve context if not provided
            if context is None:
                context = self.retrieve_context(query)
            
            # Get template
            template = self.templates.get(template_name)
            if not template:
                logger.warning(f"Template {template_name} not found, using default")
                template = self.templates["default"]
            
            # Format prompt
            augmented_prompt = template.format(
                query=query,
                context=context.context_text,
                **kwargs,
            )
            
            return augmented_prompt
        
        except Exception as e:
            logger.error(f"Failed to augment prompt: {str(e)}")
            return query
    
    def augment_prompt_with_source(
        self,
        query: str,
        source: DocumentSource,
        template_name: str = "default",
        **kwargs,
    ) -> str:
        """Augment prompt with context from specific source."""
        context = self.retrieve_by_source(query, source)
        return self.augment_prompt(query, template_name, context, **kwargs)
    
    def register_template(
        self,
        name: str,
        template_string: str,
    ) -> bool:
        """
        Register a custom prompt template.
        
        Args:
            name: Template name
            template_string: Template with {query} and {context} placeholders
        
        Returns:
            True if registered successfully
        """
        try:
            self.templates[name] = PromptTemplate(template_string)
            logger.info(f"Registered template: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register template: {str(e)}")
            return False
    
    # ========================================================================
    # Advanced Features
    # ========================================================================
    
    def get_related_documents(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Get semantically related documents.
        
        Args:
            query: Search query
            top_k: Number of results
            similarity_threshold: Minimum similarity score
        
        Returns:
            List of related documents
        """
        try:
            results = knowledge_base_manager.retrieve(query, top_k=top_k * 2)
            
            # Filter by similarity threshold
            filtered = [
                r for r in results
                if r['similarity_score'] >= similarity_threshold
            ][:top_k]
            
            return filtered
        
        except Exception as e:
            logger.error(f"Failed to get related documents: {str(e)}")
            return []
    
    def get_context_chain(
        self,
        query: str,
        depth: int = 2,
    ) -> str:
        """
        Build context chain by following document relationships.
        
        Args:
            query: Initial query
            depth: Depth of retrieval chain
        
        Returns:
            Chained context string
        """
        try:
            context_chain = []
            current_query = query
            
            for i in range(depth):
                context = self.retrieve_context(current_query, top_k=3)
                if context.context_text:
                    context_chain.append(f"Step {i+1}: {context.context_text}")
                    # Use first retrieved doc as next query
                    if context.retrieved_docs:
                        current_query = context.retrieved_docs[0]['text'][:100]
                else:
                    break
            
            return "\n\n---\n\n".join(context_chain)
        
        except Exception as e:
            logger.error(f"Failed to build context chain: {str(e)}")
            return ""
    
    # ========================================================================
    # Knowledge Base Statistics
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        try:
            kb_stats = knowledge_base_manager.get_knowledge_base_stats()
            return {
                "knowledge_base": kb_stats,
                "templates": list(self.templates.keys()),
                "retrieval_history_size": len(self.retrieval_history),
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {}


# Global RAG service instance
rag_service = RAGService()
