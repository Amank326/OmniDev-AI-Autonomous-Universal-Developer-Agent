"""
Knowledge Base Manager
======================

Document storage, chunking, and indexing for RAG systems.
Manages context documents for retrieval-augmented generation.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON

from app.database.config import SessionLocal, Base
from app.rag.semantic_search import semantic_search_service

logger = logging.getLogger(__name__)


class DocumentChunkStrategy(str, Enum):
    """Strategies for chunking documents."""
    FIXED_SIZE = "fixed_size"  # Fixed chunk size
    SEMANTIC = "semantic"  # Semantic-based chunking
    SENTENCE = "sentence"  # Sentence-based chunking
    PARAGRAPH = "paragraph"  # Paragraph-based chunking


class DocumentSource(str, Enum):
    """Document source types."""
    FILE = "file"
    URL = "url"
    DATABASE = "database"
    CODE = "code"
    DOCUMENTATION = "documentation"
    WIKI = "wiki"


class Document(Base):
    """Database model for documents in knowledge base."""
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    content = Column(Text)
    source = Column(String(50))
    source_url = Column(String(512), nullable=True)
    chunk_strategy = Column(String(50), default="fixed_size")
    indexed = Column(Integer, default=0)  # Number of chunks indexed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON, default={})


class DocumentChunk:
    """Represents a chunk of a document."""
    
    def __init__(
        self,
        doc_id: int,
        chunk_index: int,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize document chunk."""
        self.doc_id = doc_id
        self.chunk_index = chunk_index
        self.text = text
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()


class KnowledgeBaseManager:
    """
    Manages knowledge base documents and retrieval.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize knowledge base manager."""
        self.db = db or SessionLocal()
        self.chunks: Dict[int, List[DocumentChunk]] = {}  # doc_id -> chunks
        self.index_name = "knowledge_base"
        
        # Ensure index exists
        if not semantic_search_service.vector_stores.get(self.index_name):
            semantic_search_service.create_index(self.index_name)
    
    # ========================================================================
    # Document Management
    # ========================================================================
    
    def add_document(
        self,
        title: str,
        content: str,
        source: DocumentSource = DocumentSource.FILE,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Add document to knowledge base.
        
        Args:
            title: Document title
            content: Document content
            source: Document source type
            source_url: Source URL (if applicable)
            metadata: Additional metadata
        
        Returns:
            Document ID
        """
        try:
            # Create document record
            doc = Document(
                title=title,
                content=content,
                source=source.value,
                source_url=source_url,
                metadata=metadata or {},
            )
            self.db.add(doc)
            self.db.commit()
            self.db.refresh(doc)
            
            logger.info(f"Added document {doc.id}: {title}")
            return doc.id
        
        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            self.db.rollback()
            return -1
    
    def get_document(self, doc_id: int) -> Optional[Document]:
        """Get document by ID."""
        try:
            return self.db.query(Document).filter_by(id=doc_id).first()
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {str(e)}")
            return None
    
    def list_documents(self) -> List[Document]:
        """List all documents."""
        try:
            return self.db.query(Document).all()
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            return []
    
    def delete_document(self, doc_id: int) -> bool:
        """Delete document."""
        try:
            doc = self.db.query(Document).filter_by(id=doc_id).first()
            if doc:
                self.db.delete(doc)
                self.db.commit()
                logger.info(f"Deleted document {doc_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {str(e)}")
            self.db.rollback()
            return False
    
    # ========================================================================
    # Document Chunking
    # ========================================================================
    
    def chunk_document(
        self,
        doc_id: int,
        strategy: DocumentChunkStrategy = DocumentChunkStrategy.FIXED_SIZE,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> List[DocumentChunk]:
        """
        Chunk a document into smaller pieces.
        
        Args:
            doc_id: Document ID
            strategy: Chunking strategy
            chunk_size: Size of chunks (for fixed_size)
            overlap: Character overlap between chunks
        
        Returns:
            List of document chunks
        """
        try:
            doc = self.get_document(doc_id)
            if not doc:
                logger.error(f"Document {doc_id} not found")
                return []
            
            chunks = []
            
            if strategy == DocumentChunkStrategy.FIXED_SIZE:
                chunks = self._chunk_fixed_size(doc.content, chunk_size, overlap)
            elif strategy == DocumentChunkStrategy.SEMANTIC:
                chunks = self._chunk_semantic(doc.content)
            elif strategy == DocumentChunkStrategy.SENTENCE:
                chunks = self._chunk_sentence(doc.content)
            elif strategy == DocumentChunkStrategy.PARAGRAPH:
                chunks = self._chunk_paragraph(doc.content)
            
            # Create chunk objects
            document_chunks = [
                DocumentChunk(
                    doc_id=doc_id,
                    chunk_index=i,
                    text=chunk,
                    metadata={
                        "title": doc.title,
                        "source": doc.source,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    }
                )
                for i, chunk in enumerate(chunks)
            ]
            
            # Store chunks
            self.chunks[doc_id] = document_chunks
            
            # Update document
            doc.chunk_strategy = strategy.value
            doc.indexed = len(document_chunks)
            self.db.commit()
            
            logger.info(f"Chunked document {doc_id} into {len(document_chunks)} chunks")
            return document_chunks
        
        except Exception as e:
            logger.error(f"Failed to chunk document {doc_id}: {str(e)}")
            return []
    
    def _chunk_fixed_size(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> List[str]:
        """Chunk by fixed size with overlap."""
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i : i + chunk_size])
        return chunks
    
    def _chunk_sentence(self, text: str) -> List[str]:
        """Chunk by sentences."""
        # Simple sentence splitting on periods, newlines
        sentences = re.split(r'[.!?\n]+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) > 500:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _chunk_paragraph(self, text: str) -> List[str]:
        """Chunk by paragraphs."""
        # Split on double newlines
        paragraphs = re.split(r'\n\n+', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _chunk_semantic(self, text: str) -> List[str]:
        """Chunk by semantic boundaries (simple implementation)."""
        # For now, use paragraph chunking as semantic base
        return self._chunk_paragraph(text)
    
    # ========================================================================
    # Indexing
    # ========================================================================
    
    def index_document(self, doc_id: int) -> bool:
        """
        Index a document's chunks into semantic search.
        
        Args:
            doc_id: Document ID
        
        Returns:
            True if successfully indexed
        """
        try:
            # Get or create chunks
            if doc_id not in self.chunks:
                chunks = self.chunk_document(doc_id)
                if not chunks:
                    return False
            else:
                chunks = self.chunks[doc_id]
            
            # Index chunks
            texts = [c.text for c in chunks]
            metadatas = [c.metadata for c in chunks]
            
            doc_ids = semantic_search_service.index_documents(
                self.index_name,
                texts,
                metadatas,
            )
            
            if doc_ids:
                logger.info(f"Indexed document {doc_id} with {len(doc_ids)} chunks")
                return True
            return False
        
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {str(e)}")
            return False
    
    def index_all_documents(self) -> int:
        """Index all documents."""
        try:
            documents = self.list_documents()
            indexed_count = 0
            
            for doc in documents:
                if self.index_document(doc.id):
                    indexed_count += 1
            
            logger.info(f"Indexed {indexed_count} documents")
            return indexed_count
        
        except Exception as e:
            logger.error(f"Failed to index all documents: {str(e)}")
            return 0
    
    # ========================================================================
    # Retrieval
    # ========================================================================
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of relevant documents with content and metadata
        """
        try:
            # Search semantic index
            results = semantic_search_service.search(
                self.index_name,
                query,
                top_k=top_k,
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {str(e)}")
            return []
    
    def retrieve_with_context(
        self,
        query: str,
        top_k: int = 5,
        context_window: int = 100,
    ) -> str:
        """
        Retrieve documents and format as context string.
        
        Args:
            query: Search query
            top_k: Number of results
            context_window: Characters before/after to include
        
        Returns:
            Formatted context string
        """
        try:
            results = self.retrieve(query, top_k=top_k)
            
            context_parts = []
            for result in results:
                # Extract source document title
                title = result['metadata'].get('title', 'Unknown')
                text = result['text']
                score = result['similarity_score']
                
                context_parts.append(
                    f"[From: {title} (relevance: {score:.2f})]\n{text}"
                )
            
            return "\n\n---\n\n".join(context_parts)
        
        except Exception as e:
            logger.error(f"Failed to retrieve context: {str(e)}")
            return ""
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        try:
            documents = self.list_documents()
            total_documents = len(documents)
            total_chunks = sum(len(self.chunks.get(d.id, [])) for d in documents)
            
            return {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "average_chunks_per_doc": total_chunks / total_documents if total_documents > 0 else 0,
                "index_stats": semantic_search_service.get_index_stats(self.index_name),
            }
        
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {}
    
    def close(self):
        """Close and cleanup."""
        if self.db:
            self.db.close()
            logger.info("Closed KnowledgeBaseManager")


# Global instance
knowledge_base_manager = KnowledgeBaseManager()
