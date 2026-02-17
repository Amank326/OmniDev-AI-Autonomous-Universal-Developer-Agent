"""RAG pipeline for document retrieval and generation."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Document:
    """Represents a document chunk for RAG."""

    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ):
        self.content = content
        self.metadata = metadata or {}
        self.embedding = embedding

    def __repr__(self) -> str:
        return f"Document(content={self.content[:50]}..., metadata={self.metadata})"


class VectorStore:
    """In-memory vector store for document embeddings.

    Replace with a proper vector database (e.g., Pinecone, Weaviate,
    pgvector) in production.
    """

    def __init__(self):
        self._documents: List[Document] = []

    async def add_documents(self, documents: List[Document]) -> int:
        """Add documents to the store."""
        self._documents.extend(documents)
        logger.info(f"Added {len(documents)} documents to vector store")
        return len(self._documents)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search for similar documents.

        This is a naive keyword search. Replace with proper
        vector similarity search in production.
        """
        query_lower = query.lower()
        scored: List[tuple] = []

        for doc in self._documents:
            if filters:
                skip = False
                for key, value in filters.items():
                    if doc.metadata.get(key) != value:
                        skip = True
                        break
                if skip:
                    continue

            # Simple keyword overlap scoring
            words = set(query_lower.split())
            doc_words = set(doc.content.lower().split())
            overlap = len(words & doc_words)
            if overlap > 0:
                scored.append((overlap, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    async def clear(self) -> None:
        """Clear all documents."""
        self._documents.clear()

    @property
    def count(self) -> int:
        return len(self._documents)


class TextSplitter:
    """Split text into chunks for embedding."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks: List[str] = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap

        return chunks


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline.

    Usage:
        pipeline = RAGPipeline()
        await pipeline.ingest("Some long document text...", metadata={"source": "readme"})
        results = await pipeline.query("How do I install?")
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self.vector_store = VectorStore()
        self.splitter = TextSplitter(chunk_size, chunk_overlap)

    async def ingest(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Ingest a document by splitting and storing chunks."""
        chunks = self.splitter.split(text)
        documents = [
            Document(content=chunk, metadata={**(metadata or {}), "chunk_index": i})
            for i, chunk in enumerate(chunks)
        ]
        return await self.vector_store.add_documents(documents)

    async def query(
        self,
        question: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query the pipeline and return relevant context."""
        results = await self.vector_store.search(question, top_k=top_k, filters=filters)
        return [
            {"content": doc.content, "metadata": doc.metadata}
            for doc in results
        ]

    async def clear(self) -> None:
        """Clear all stored documents."""
        await self.vector_store.clear()

    @property
    def document_count(self) -> int:
        return self.vector_store.count
