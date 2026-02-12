"""Vector Memory System - Learning and context storage"""

from typing import Optional, Any, List
import logging

logger = logging.getLogger(__name__)

class VectorMemory:
    """Vector database for AI memory and learning"""
    
    def __init__(self):
        """Initialize vector memory"""
        self.memory_store = {}
        self.embeddings_cache = {}
        logger.info("Vector Memory initialized")
    
    async def store(self, key: str, value: Any) -> bool:
        """
        Store information in vector memory
        
        Args:
            key: Memory key
            value: Data to store
        
        Returns:
            Success status
        """
        try:
            self.memory_store[key] = {
                "value": value,
                "embedding": self._generate_embedding(str(value))
            }
            logger.info(f"Stored in memory: {key}")
            return True
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return False
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve information from vector memory
        
        Args:
            key: Memory key
        
        Returns:
            Stored value or None
        """
        if key in self.memory_store:
            return self.memory_store[key]["value"]
        return None
    
    async def search(self, query: str, limit: int = 5) -> List[dict]:
        """
        Semantic search in memory
        
        Args:
            query: Search query
            limit: Number of results
        
        Returns:
            List of relevant memories
        """
        results = []
        query_embedding = self._generate_embedding(query)
        
        for key, data in self.memory_store.items():
            similarity = self._calculate_similarity(
                query_embedding,
                data["embedding"]
            )
            results.append({
                "key": key,
                "value": data["value"],
                "similarity": similarity
            })
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate simple embedding for text"""
        # Simple hash-based embedding (production use real embeddings)
        return [float(ord(c)) / 256.0 for c in text[:512]]
    
    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        if not vec1 or not vec2:
            return 0.0
        
        # Pad shorter vector
        max_len = max(len(vec1), len(vec2))
        v1 = vec1 + [0] * (max_len - len(vec1))
        v2 = vec2 + [0] * (max_len - len(vec2))
        
        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(v1, v2))
        mag1 = sum(x**2 for x in v1) ** 0.5
        mag2 = sum(x**2 for x in v2) ** 0.5
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    async def clear(self):
        """Clear all memory"""
        self.memory_store.clear()
        logger.info("Memory cleared")
    
    async def get_stats(self) -> dict:
        """Get memory statistics"""
        return {
            "total_entries": len(self.memory_store),
            "keys": list(self.memory_store.keys()),
            "memory_size": len(str(self.memory_store))
        }
