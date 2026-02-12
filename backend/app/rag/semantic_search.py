"""
Semantic Search Service
=======================

Query embedding and similarity matching for semantic retrieval.
Enables context-aware search and document ranking.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database.config import SessionLocal

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    logger.warning("sentence-transformers not installed, semantic search limited")

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    logger.warning("faiss-cpu not installed, using simple vector search")


class EmbeddingModel:
    """Manages embeddings using sentence transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding model.
        
        Args:
            model_name: Sentence transformer model name
        """
        self.model_name = model_name
        self.model = None
        
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.model = SentenceTransformer(model_name)
                logger.info(f"Loaded embedding model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {str(e)}")
    
    def encode(self, texts: List[str]) -> Optional[np.ndarray]:
        """
        Encode texts to embeddings.
        
        Args:
            texts: List of texts to encode
        
        Returns:
            Array of embeddings or None if model unavailable
        """
        if not self.model:
            logger.warning("Embedding model not available")
            return None
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode texts: {str(e)}")
            return None
    
    def encode_single(self, text: str) -> Optional[np.ndarray]:
        """Encode single text."""
        embeddings = self.encode([text])
        return embeddings[0] if embeddings is not None else None


class VectorStore:
    """Vector store for efficient similarity search."""
    
    def __init__(self, embedding_dim: int = 384, use_faiss: bool = True):
        """
        Initialize vector store.
        
        Args:
            embedding_dim: Dimension of embeddings
            use_faiss: Use FAISS for indexing (if available)
        """
        self.embedding_dim = embedding_dim
        self.use_faiss = use_faiss and HAS_FAISS
        self.documents: Dict[int, str] = {}  # doc_id -> text
        self.vectors: Dict[int, np.ndarray] = {}  # doc_id -> embedding
        self.metadata: Dict[int, Dict[str, Any]] = {}  # doc_id -> metadata
        self.next_doc_id = 0
        
        # Initialize FAISS index if available
        if self.use_faiss:
            try:
                self.faiss_index = faiss.IndexFlatL2(embedding_dim)
                self.faiss_doc_ids = []
            except Exception as e:
                logger.error(f"Failed to initialize FAISS: {str(e)}")
                self.use_faiss = False
    
    def add_document(
        self,
        text: str,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Add document to store.
        
        Args:
            text: Document text
            embedding: Document embedding
            metadata: Document metadata
        
        Returns:
            Document ID
        """
        doc_id = self.next_doc_id
        self.next_doc_id += 1
        
        self.documents[doc_id] = text
        self.vectors[doc_id] = embedding
        self.metadata[doc_id] = metadata or {}
        
        # Add to FAISS if available
        if self.use_faiss:
            self.faiss_index.add(np.array([embedding]))
            self.faiss_doc_ids.append(doc_id)
        
        return doc_id
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> List[Tuple[int, float, str]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding
            top_k: Number of results to return
        
        Returns:
            List of (doc_id, similarity, text) tuples
        """
        if not self.vectors:
            return []
        
        results = []
        
        if self.use_faiss and self.faiss_doc_ids:
            # Use FAISS search
            distances, indices = self.faiss_index.search(
                np.array([query_embedding]),
                min(top_k, len(self.faiss_doc_ids))
            )
            
            for idx, distance in zip(indices[0], distances[0]):
                doc_id = self.faiss_doc_ids[idx]
                # Convert L2 distance to similarity score
                similarity = 1.0 / (1.0 + distance)
                results.append((doc_id, similarity, self.documents[doc_id]))
        else:
            # Simple linear search with cosine similarity
            query_norm = np.linalg.norm(query_embedding)
            if query_norm == 0:
                return []
            
            for doc_id, vector in self.vectors.items():
                vector_norm = np.linalg.norm(vector)
                if vector_norm == 0:
                    similarity = 0
                else:
                    similarity = np.dot(query_embedding, vector) / (query_norm * vector_norm)
                results.append((doc_id, similarity, self.documents[doc_id]))
            
            # Sort by similarity and get top-k
            results.sort(key=lambda x: x[1], reverse=True)
            results = results[:top_k]
        
        return results


class SemanticSearchService:
    """
    Service for semantic search and similarity matching.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize semantic search service.
        
        Args:
            model_name: Sentence transformer model name
        """
        self.embedding_model = EmbeddingModel(model_name)
        self.vector_stores: Dict[str, VectorStore] = {}
        self.embedding_dim = 384  # Default for all-MiniLM-L6-v2
    
    def create_index(
        self,
        index_name: str,
        embedding_dim: Optional[int] = None,
    ) -> bool:
        """
        Create a new semantic index.
        
        Args:
            index_name: Name of index
            embedding_dim: Embedding dimension
        
        Returns:
            True if created successfully
        """
        try:
            if index_name in self.vector_stores:
                logger.warning(f"Index {index_name} already exists")
                return False
            
            dim = embedding_dim or self.embedding_dim
            self.vector_stores[index_name] = VectorStore(embedding_dim=dim)
            logger.info(f"Created index: {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {str(e)}")
            return False
    
    def index_document(
        self,
        index_name: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """
        Index a document.
        
        Args:
            index_name: Index name
            text: Document text
            metadata: Document metadata
        
        Returns:
            Document ID or None
        """
        try:
            if index_name not in self.vector_stores:
                logger.warning(f"Index {index_name} not found")
                return None
            
            if not self.embedding_model.model:
                logger.warning("Embedding model not available")
                return None
            
            # Generate embedding
            embedding = self.embedding_model.encode_single(text)
            if embedding is None:
                return None
            
            # Add to store
            store = self.vector_stores[index_name]
            doc_id = store.add_document(text, embedding, metadata)
            
            logger.debug(f"Indexed document {doc_id} in {index_name}")
            return doc_id
        
        except Exception as e:
            logger.error(f"Failed to index document: {str(e)}")
            return None
    
    def index_documents(
        self,
        index_name: str,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[int]:
        """
        Index multiple documents.
        
        Args:
            index_name: Index name
            texts: List of document texts
            metadatas: List of metadata dicts
        
        Returns:
            List of document IDs
        """
        try:
            if index_name not in self.vector_stores:
                logger.warning(f"Index {index_name} not found")
                return []
            
            if not self.embedding_model.model:
                logger.warning("Embedding model not available")
                return []
            
            # Generate embeddings for all texts
            embeddings = self.embedding_model.encode(texts)
            if embeddings is None:
                return []
            
            # Add all documents
            store = self.vector_stores[index_name]
            doc_ids = []
            
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                metadata = metadatas[i] if metadatas else None
                doc_id = store.add_document(text, embedding, metadata)
                doc_ids.append(doc_id)
            
            logger.info(f"Indexed {len(doc_ids)} documents in {index_name}")
            return doc_ids
        
        except Exception as e:
            logger.error(f"Failed to batch index documents: {str(e)}")
            return []
    
    def search(
        self,
        index_name: str,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search index for similar documents.
        
        Args:
            index_name: Index name
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of search results with text and metadata
        """
        try:
            if index_name not in self.vector_stores:
                logger.warning(f"Index {index_name} not found")
                return []
            
            if not self.embedding_model.model:
                logger.warning("Embedding model not available")
                return []
            
            # Encode query
            query_embedding = self.embedding_model.encode_single(query)
            if query_embedding is None:
                return []
            
            # Search
            store = self.vector_stores[index_name]
            results = store.search(query_embedding, top_k=top_k)
            
            # Format results
            formatted = []
            for doc_id, similarity, text in results:
                metadata = store.metadata.get(doc_id, {})
                formatted.append({
                    "doc_id": doc_id,
                    "similarity_score": float(similarity),
                    "text": text,
                    "metadata": metadata,
                })
            
            return formatted
        
        except Exception as e:
            logger.error(f"Failed to search index {index_name}: {str(e)}")
            return []
    
    def get_index_stats(self, index_name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for an index."""
        if index_name not in self.vector_stores:
            return None
        
        store = self.vector_stores[index_name]
        return {
            "index_name": index_name,
            "document_count": len(store.documents),
            "embedding_dim": store.embedding_dim,
            "using_faiss": store.use_faiss,
        }
    
    def list_indexes(self) -> List[str]:
        """List all available indexes."""
        return list(self.vector_stores.keys())


# Global service instance
semantic_search_service = SemanticSearchService()
