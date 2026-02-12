"""
Relationship Extractor Service
Extracts and identifies relationships between entities in text.
Builds entity relationship graphs for knowledge representation.
Integrates with entity recognition and NLP engine.
"""

import threading
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any, Set
from datetime import datetime
from threading import RLock

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of relationships between entities"""
    # Actor relationships
    IS_A = "is_a"  # Inheritance/categorization
    PART_OF = "part_of"  # Containment
    INSTANCE_OF = "instance_of"  # Specific instance
    
    # Security relationships
    EXPLOITS = "exploits"  # Vulnerability exploited by threat
    TARGETS = "targets"  # Attack targets entity
    AFFECTS = "affects"  # Impact relationship
    CAUSED_BY = "caused_by"  # Causal relationship
    LEADS_TO = "leads_to"  # Consequence
    
    # Organizational relationships
    BELONGS_TO = "belongs_to"  # Membership
    MANAGES = "manages"  # Management
    REPORTS_TO = "reports_to"  # Hierarchy
    COLLABORATES_WITH = "collaborates_with"  # Partnership
    
    # Data relationships
    CONTAINS = "contains"  # Containment
    REFERENCES = "references"  # Reference
    DEPENDS_ON = "depends_on"  # Dependency
    RELATED_TO = "related_to"  # General relation
    
    # Temporal relationships
    OCCURS_BEFORE = "occurs_before"  # Temporal ordering
    OCCURS_AFTER = "occurs_after"  # Temporal ordering
    OCCURS_DURING = "occurs_during"  # Temporal containment
    
    # Other relationships
    SIMILAR_TO = "similar_to"  # Similarity
    OPPOSITE_OF = "opposite_of"  # Opposition
    ATTRIBUTE_OF = "attribute_of"  # Property
    LOCATED_IN = "located_in"  # Location


class RelationshipConfidence(Enum):
    """Confidence levels for relationships"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class Relationship:
    """Relationship between two entities"""
    source_entity: str
    source_type: str
    target_entity: str
    target_type: str
    relationship_type: RelationshipType
    confidence: float
    confidence_level: RelationshipConfidence
    evidence: List[str]  # Supporting text/context
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_entity": self.source_entity,
            "source_type": self.source_type,
            "target_entity": self.target_entity,
            "target_type": self.target_type,
            "relationship_type": self.relationship_type.value,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "evidence": self.evidence[:3],  # Top 3 pieces of evidence
            "attributes": self.attributes
        }


@dataclass
class RelationshipExtractionResult:
    """Result of relationship extraction"""
    text: str
    relationships: List[Relationship]
    relationship_count: int
    unique_entities_found: int
    entity_pair_count: int
    graph_density: float  # Measures connectivity
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "relationships": [r.to_dict() for r in self.relationships],
            "relationship_count": self.relationship_count,
            "unique_entities_found": self.unique_entities_found,
            "entity_pair_count": self.entity_pair_count,
            "graph_density": self.graph_density,
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class EntityRelationshipGraph:
    """Graph representation of entity relationships"""
    entities: Set[str]
    relationships: List[Relationship]
    adjacency_list: Dict[str, List[str]]  # Entity -> connected entities
    node_count: int
    edge_count: int
    clustering_coefficient: float  # Measure of graph clustering
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "clustering_coefficient": self.clustering_coefficient,
            "relationships": [r.to_dict() for r in self.relationships[:10]]  # Top relationships
        }


@dataclass
class RelationshipExtractorConfig:
    """Relationship extractor configuration"""
    min_confidence: float = 0.5
    max_relationships: int = 100
    enable_bidirectional: bool = True
    cache_results: bool = True
    cache_ttl_seconds: int = 3600
    extract_attribute_relations: bool = True
    build_graph: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_confidence": self.min_confidence,
            "max_relationships": self.max_relationships,
            "enable_bidirectional": self.enable_bidirectional,
            "cache_results": self.cache_results,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "extract_attribute_relations": self.extract_attribute_relations,
            "build_graph": self.build_graph
        }


@dataclass
class RelationshipExtractorMetrics:
    """Metrics for relationship extraction"""
    total_texts_processed: int = 0
    total_relationships_extracted: int = 0
    relationship_type_distribution: Dict[str, int] = field(default_factory=dict)
    avg_relationships_per_text: float = 0.0
    avg_confidence: float = 0.0
    avg_processing_time_ms: float = 0.0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    error_count: int = 0
    last_processed_at: Optional[datetime] = None
    most_common_relationship_type: Optional[RelationshipType] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_texts_processed": self.total_texts_processed,
            "total_relationships_extracted": self.total_relationships_extracted,
            "relationship_type_distribution": self.relationship_type_distribution,
            "avg_relationships_per_text": self.avg_relationships_per_text,
            "avg_confidence": self.avg_confidence,
            "avg_processing_time_ms": self.avg_processing_time_ms,
            "cache_hit_count": self.cache_hit_count,
            "cache_miss_count": self.cache_miss_count,
            "error_count": self.error_count,
            "last_processed_at": self.last_processed_at.isoformat() if self.last_processed_at else None,
            "most_common_relationship_type": self.most_common_relationship_type.value if self.most_common_relationship_type else None,
            "cache_hit_rate": self.cache_hit_count / (self.cache_hit_count + self.cache_miss_count) if (self.cache_hit_count + self.cache_miss_count) > 0 else 0.0
        }


class RelationshipExtractor:
    """
    Relationship extraction service for discovering entity relationships.
    Thread-safe singleton supporting multiple relationship types.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # Relationship patterns and keywords
    RELATIONSHIP_PATTERNS = {
        RelationshipType.EXPLOITS: {
            "keywords": ["exploit", "exploited by", "exploits", "takes advantage"],
            "pattern_templates": ["{entity1} exploits {entity2}", "{entity1} is exploited by {entity2}"]
        },
        RelationshipType.TARGETS: {
            "keywords": ["targets", "target", "attacks", "aimed at", "affects"],
            "pattern_templates": ["{entity1} targets {entity2}", "{entity1} attacks {entity2}"]
        },
        RelationshipType.AFFECTS: {
            "keywords": ["affects", "affected by", "impacts", "impacts", "influences"],
            "pattern_templates": ["{entity1} affects {entity2}"]
        },
        RelationshipType.CAUSED_BY: {
            "keywords": ["caused by", "caused", "due to", "because of", "result of"],
            "pattern_templates": ["{entity1} caused by {entity2}", "{entity1} is due to {entity2}"]
        },
        RelationshipType.LEADS_TO: {
            "keywords": ["leads to", "results in", "causes", "results in", "produces"],
            "pattern_templates": ["{entity1} leads to {entity2}"]
        },
        RelationshipType.CONTAINS: {
            "keywords": ["contains", "includes", "composed of", "made of", "has"],
            "pattern_templates": ["{entity1} contains {entity2}", "{entity1} includes {entity2}"]
        },
        RelationshipType.PART_OF: {
            "keywords": ["part of", "member of", "component of", "element of"],
            "pattern_templates": ["{entity1} part of {entity2}"]
        },
        RelationshipType.BELONGS_TO: {
            "keywords": ["belongs to", "is member of", "works for", "employed by"],
            "pattern_templates": ["{entity1} belongs to {entity2}"]
        },
        RelationshipType.DEPENDS_ON: {
            "keywords": ["depends on", "depends upon", "requires", "needs", "relies on"],
            "pattern_templates": ["{entity1} depends on {entity2}"]
        },
        RelationshipType.RELATED_TO: {
            "keywords": ["related to", "related with", "associated with", "connected to"],
            "pattern_templates": ["{entity1} related to {entity2}"]
        }
    }
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.config = RelationshipExtractorConfig()
            self.metrics = RelationshipExtractorMetrics()
            self._cache: Dict[str, Tuple[RelationshipExtractionResult, float]] = {}
            self._lock = RLock()
            self._processing_times: List[float] = []
            self._confidence_scores: List[float] = []
            self._relationship_counts: List[int] = []
            self._initialized = True
    
    def extract_relationships(self, text: str, entities: Optional[List[Tuple[str, str]]] = None) -> RelationshipExtractionResult:
        """
        Extract relationships between entities in text.
        
        Args:
            text: Input text to analyze
            entities: Optional list of (entity, entity_type) tuples
            
        Returns:
            RelationshipExtractionResult with extracted relationships
        """
        if not text or not isinstance(text, str):
            self.metrics.error_count += 1
            raise ValueError("Text must be non-empty string")
        
        start_time = time.time()
        
        # Check cache
        cache_key = self._generate_cache_key(text)
        if self.config.cache_results and cache_key in self._cache:
            cached_result, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self.config.cache_ttl_seconds:
                self.metrics.cache_hit_count += 1
                return cached_result
        
        self.metrics.cache_miss_count += 1
        
        try:
            # Extract candidate entities if not provided
            if not entities:
                entities = self._extract_entities(text)
            
            # Find relationships between entities
            relationships = self._find_relationships(text, entities)
            
            # Filter by confidence
            relationships = [r for r in relationships if r.confidence >= self.config.min_confidence]
            
            # Sort by confidence
            relationships.sort(key=lambda r: r.confidence, reverse=True)
            
            # Limit relationships
            relationships = relationships[:self.config.max_relationships]
            
            # Calculate metrics
            unique_entities = set()
            for entity, _ in entities:
                unique_entities.add(entity)
            for rel in relationships:
                unique_entities.add(rel.source_entity)
                unique_entities.add(rel.target_entity)
            
            entity_pairs = len(entities)
            graph_density = (len(relationships) / (entity_pairs * (entity_pairs - 1))) if entity_pairs > 1 else 0.0
            
            processing_time_ms = (time.time() - start_time) * 1000
            self._processing_times.append(processing_time_ms)
            if len(self._processing_times) > 1000:
                self._processing_times.pop(0)
            
            self._relationship_counts.append(len(relationships))
            if len(self._relationship_counts) > 1000:
                self._relationship_counts.pop(0)
            
            result = RelationshipExtractionResult(
                text=text,
                relationships=relationships,
                relationship_count=len(relationships),
                unique_entities_found=len(unique_entities),
                entity_pair_count=entity_pairs,
                graph_density=min(graph_density, 1.0),
                processing_time_ms=processing_time_ms
            )
            
            # Cache result
            if self.config.cache_results:
                self._cache[cache_key] = (result, time.time())
            
            # Update metrics
            with self._lock:
                self.metrics.total_texts_processed += 1
                self.metrics.total_relationships_extracted += len(relationships)
                self.metrics.last_processed_at = datetime.now()
                
                for rel in relationships:
                    rel_type_key = rel.relationship_type.value
                    self.metrics.relationship_type_distribution[rel_type_key] = (
                        self.metrics.relationship_type_distribution.get(rel_type_key, 0) + 1
                    )
                
                if len(self._relationship_counts) > 0:
                    self.metrics.avg_relationships_per_text = sum(self._relationship_counts) / len(self._relationship_counts)
                
                if relationships:
                    avg_conf = sum(r.confidence for r in relationships) / len(relationships)
                    self._confidence_scores.append(avg_conf)
                    if len(self._confidence_scores) > 1000:
                        self._confidence_scores.pop(0)
                    if len(self._confidence_scores) > 0:
                        self.metrics.avg_confidence = sum(self._confidence_scores) / len(self._confidence_scores)
                
                if len(self._processing_times) > 0:
                    self.metrics.avg_processing_time_ms = sum(self._processing_times) / len(self._processing_times)
                
                # Track most common relationship type
                if self.metrics.relationship_type_distribution:
                    most_common_key = max(self.metrics.relationship_type_distribution, 
                                         key=self.metrics.relationship_type_distribution.get)
                    self.metrics.most_common_relationship_type = RelationshipType(most_common_key)
            
            return result
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Error extracting relationships: {str(e)}")
            raise
    
    def build_relationship_graph(self, text: str, entities: Optional[List[Tuple[str, str]]] = None) -> EntityRelationshipGraph:
        """Build graph representation of entity relationships."""
        extraction_result = self.extract_relationships(text, entities)
        relationships = extraction_result.relationships
        
        # Build adjacency list
        adjacency_list = {}
        entity_set = set()
        
        for rel in relationships:
            entity_set.add(rel.source_entity)
            entity_set.add(rel.target_entity)
            
            if rel.source_entity not in adjacency_list:
                adjacency_list[rel.source_entity] = []
            adjacency_list[rel.source_entity].append(rel.target_entity)
            
            if self.config.enable_bidirectional:
                if rel.target_entity not in adjacency_list:
                    adjacency_list[rel.target_entity] = []
                adjacency_list[rel.target_entity].append(rel.source_entity)
        
        # Calculate clustering coefficient (simplified)
        clustering_coeff = self._calculate_clustering_coefficient(adjacency_list)
        
        return EntityRelationshipGraph(
            entities=entity_set,
            relationships=relationships,
            adjacency_list=adjacency_list,
            node_count=len(entity_set),
            edge_count=len(relationships),
            clustering_coefficient=clustering_coeff
        )
    
    def get_related_entities(self, entity: str, relationship_type: Optional[RelationshipType] = None) -> List[Tuple[str, float]]:
        """Find entities related to given entity."""
        # This would query stored relationships - simplified implementation
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get extraction metrics."""
        return self.metrics.to_dict()
    
    def get_config(self) -> Dict[str, Any]:
        """Get extractor configuration."""
        return self.config.to_dict()
    
    def update_config(self, **kwargs) -> None:
        """Update extractor configuration."""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
    
    def clear_cache(self) -> None:
        """Clear extraction cache."""
        with self._lock:
            self._cache.clear()
    
    # Private methods
    
    def _extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """Extract candidate entities from text (simplified)."""
        # Simple extraction: capitalized phrases
        import re
        entities = []
        
        # Find capitalized phrases
        matches = re.finditer(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for match in matches:
            entity = match.group(0)
            entities.append((entity, "ENTITY"))
        
        return entities
    
    def _find_relationships(self, text: str, entities: List[Tuple[str, str]]) -> List[Relationship]:
        """Find relationships between entities in text."""
        relationships = []
        text_lower = text.lower()
        entity_texts = {e[0].lower(): (e[0], e[1]) for e in entities}
        
        # Check each pair of entities for relationships
        entity_list = list(entities)
        for i, (entity1, type1) in enumerate(entity_list):
            for entity2, type2 in entity_list[i+1:]:
                if entity1 == entity2:
                    continue
                
                # Look for relationship patterns
                for rel_type, pattern_data in self.RELATIONSHIP_PATTERNS.items():
                    rel = self._detect_relationship(
                        text_lower, entity1, entity2, type1, type2, rel_type, pattern_data
                    )
                    if rel:
                        relationships.append(rel)
        
        return relationships
    
    def _detect_relationship(self, text_lower: str, entity1: str, entity2: str, type1: str, type2: str,
                            rel_type: RelationshipType, pattern_data: Dict) -> Optional[Relationship]:
        """Detect if relationship exists between entities."""
        entity1_lower = entity1.lower()
        entity2_lower = entity2.lower()
        
        # Check if entities appear together
        if entity1_lower not in text_lower or entity2_lower not in text_lower:
            return None
        
        # Find entities in text
        entity1_pos = text_lower.find(entity1_lower)
        entity2_pos = text_lower.find(entity2_lower)
        
        if entity1_pos == -1 or entity2_pos == -1:
            return None
        
        # Check proximity
        distance = abs(entity1_pos - entity2_pos)
        if distance > 200:  # Max distance between entities
            return None
        
        # Check for relationship keywords
        keywords = pattern_data.get("keywords", [])
        text_between = text_lower[min(entity1_pos, entity2_pos):max(entity1_pos, entity2_pos) + max(len(entity1_lower), len(entity2_lower))]
        
        keyword_matches = [kw for kw in keywords if kw in text_between]
        if not keyword_matches:
            return None
        
        # Map confidence based on keyword match
        confidence = min(0.5 + (len(keyword_matches) * 0.2), 0.95)
        
        # Determine confidence level
        if confidence >= 0.9:
            conf_level = RelationshipConfidence.VERY_HIGH
        elif confidence >= 0.75:
            conf_level = RelationshipConfidence.HIGH
        elif confidence >= 0.6:
            conf_level = RelationshipConfidence.MEDIUM
        else:
            conf_level = RelationshipConfidence.LOW
        
        return Relationship(
            source_entity=entity1,
            source_type=type1,
            target_entity=entity2,
            target_type=type2,
            relationship_type=rel_type,
            confidence=confidence,
            confidence_level=conf_level,
            evidence=keyword_matches
        )
    
    def _calculate_clustering_coefficient(self, adjacency_list: Dict[str, List[str]]) -> float:
        """Calculate clustering coefficient for graph."""
        if len(adjacency_list) < 3:
            return 0.0
        
        clustering_coeff = 0.0
        for node in adjacency_list:
            neighbors = adjacency_list[node]
            if len(neighbors) < 2:
                continue
            
            # Count edges between neighbors
            edges_between = 0
            for i, neighbor1 in enumerate(neighbors):
                for neighbor2 in neighbors[i+1:]:
                    if neighbor2 in adjacency_list.get(neighbor1, []):
                        edges_between += 1
            
            max_edges = len(neighbors) * (len(neighbors) - 1) / 2
            if max_edges > 0:
                clustering_coeff += edges_between / max_edges
        
        return clustering_coeff / len(adjacency_list) if adjacency_list else 0.0
    
    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()


# Singleton instance
_relationship_extractor = None


def get_relationship_extractor() -> RelationshipExtractor:
    """Get RelationshipExtractor singleton instance."""
    global _relationship_extractor
    if _relationship_extractor is None:
        _relationship_extractor = RelationshipExtractor()
    return _relationship_extractor
