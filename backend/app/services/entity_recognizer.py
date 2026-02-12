"""
Entity Recognizer Service
Implements Named Entity Recognition (NER) for extracting and classifying entities
from text including persons, organizations, locations, threats, security artifacts.
Integrates with NLP engine and semantic understanding.
"""

import re
import threading
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any, Set
from datetime import datetime
from threading import RLock

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Entity classification types"""
    # Person entities
    PERSON = "person"
    TITLE = "title"
    
    # Organization entities
    ORGANIZATION = "organization"
    TEAM = "team"
    DEPARTMENT = "department"
    
    # Location entities
    LOCATION = "location"
    ADDRESS = "address"
    COUNTRY = "country"
    CITY = "city"
    
    # Technical entities
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    URL = "url"
    EMAIL = "email"
    HOSTNAME = "hostname"
    FILE_PATH = "file_path"
    
    # Security entities
    VULNERABILITY = "vulnerability"
    CVE = "cve"
    MALWARE = "malware"
    ATTACK_TYPE = "attack_type"
    THREAT_ACTOR = "threat_actor"
    INCIDENT = "incident"
    
    # Temporal entities
    DATE = "date"
    TIME = "time"
    DURATION = "duration"
    
    # Other
    PRODUCT = "product"
    VERSION = "version"
    HASH = "hash"
    PORT = "port"
    PROTOCOL = "protocol"
    MONEY = "money"
    PERCENTAGE = "percentage"


class EntityConfidence(Enum):
    """Confidence levels for entity recognition"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class Entity:
    """Recognized entity with metadata"""
    text: str
    entity_type: EntityType
    start_position: int
    end_position: int
    confidence: EntityConfidence
    context: str
    disambiguation_candidates: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "entity_type": self.entity_type.value,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "confidence": self.confidence.value,
            "context": self.context,
            "disambiguation_candidates": self.disambiguation_candidates,
            "attributes": self.attributes
        }


@dataclass
class EntityRecognitionResult:
    """Result of entity recognition"""
    text: str
    entities: List[Entity]
    entity_count: int
    unique_entity_types: int
    entity_density: float  # Entities per 100 characters
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "entity_count": self.entity_count,
            "unique_entity_types": self.unique_entity_types,
            "entity_density": self.entity_density,
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class EntityRecognizerConfig:
    """Entity recognizer configuration"""
    enable_person_recognition: bool = True
    enable_organization_recognition: bool = True
    enable_location_recognition: bool = True
    enable_technical_recognition: bool = True
    enable_security_recognition: bool = True
    enable_temporal_recognition: bool = True
    confidence_threshold: EntityConfidence = EntityConfidence.MEDIUM
    max_context_length: int = 100
    enable_disambiguation: bool = True
    cache_results: bool = True
    cache_ttl_seconds: int = 3600
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_person_recognition": self.enable_person_recognition,
            "enable_organization_recognition": self.enable_organization_recognition,
            "enable_location_recognition": self.enable_location_recognition,
            "enable_technical_recognition": self.enable_technical_recognition,
            "enable_security_recognition": self.enable_security_recognition,
            "enable_temporal_recognition": self.enable_temporal_recognition,
            "confidence_threshold": self.confidence_threshold.value,
            "max_context_length": self.max_context_length,
            "enable_disambiguation": self.enable_disambiguation,
            "cache_results": self.cache_results,
            "cache_ttl_seconds": self.cache_ttl_seconds
        }


@dataclass
class EntityRecognizerMetrics:
    """Metrics for entity recognition"""
    total_texts_processed: int = 0
    total_entities_recognized: int = 0
    entities_by_type: Dict[str, int] = field(default_factory=dict)
    avg_processing_time_ms: float = 0.0
    avg_entities_per_text: float = 0.0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    error_count: int = 0
    last_processed_at: Optional[datetime] = None
    most_common_entity_type: Optional[EntityType] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_texts_processed": self.total_texts_processed,
            "total_entities_recognized": self.total_entities_recognized,
            "entities_by_type": self.entities_by_type,
            "avg_processing_time_ms": self.avg_processing_time_ms,
            "avg_entities_per_text": self.avg_entities_per_text,
            "cache_hit_count": self.cache_hit_count,
            "cache_miss_count": self.cache_miss_count,
            "error_count": self.error_count,
            "last_processed_at": self.last_processed_at.isoformat() if self.last_processed_at else None,
            "most_common_entity_type": self.most_common_entity_type.value if self.most_common_entity_type else None,
            "cache_hit_rate": self.cache_hit_count / (self.cache_hit_count + self.cache_miss_count) if (self.cache_hit_count + self.cache_miss_count) > 0 else 0.0
        }


class EntityRecognizer:
    """
    Named Entity Recognizer extracting and classifying entities from text.
    Thread-safe singleton service supporting multiple entity types.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # Regex patterns for entity detection
    IP_V4_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    IP_V6_PATTERN = re.compile(r'(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    URL_PATTERN = re.compile(
        r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
    )
    DOMAIN_PATTERN = re.compile(r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b')
    CVE_PATTERN = re.compile(r'CVE-\d{4}-\d{4,}')
    PORT_PATTERN = re.compile(r':(\d{1,5})(?:\s|$|/)')
    HASH_PATTERN = re.compile(r'\b(?:[a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64})\b')
    FILE_PATH_PATTERN = re.compile(r'(?:[/\\][\w.-]+)+')
    
    # Known security terms
    ATTACK_TYPES = {
        "brute force", "sql injection", "xss", "csrf", "ddos", "doxing",
        "phishing", "ransomware", "privilege escalation", "data exfiltration",
        "man-in-the-middle", "zero-day", "buffer overflow", "injection",
        "social engineering", "insider threat"
    }
    
    THREAT_ACTORS = {
        "apt", "apt1", "apt28", "apt29", "turla", "lazarus", "mirai",
        "emotet", "wannacry", "notpetya", "stuxnet", "flame"
    }
    
    KNOWN_VULNS = {
        "heartbleed", "shellshock", "spectre", "meltdown", "krack",
        "log4j", "zerologging"
    }
    
    # Known organizations
    KNOWN_ORGS = {
        "microsoft", "apple", "google", "amazon", "facebook", "meta",
        "ibm", "oracle", "cisco", "vmware", "splunk", "crowdstrike"
    }
    
    # Known locations
    KNOWN_LOCATIONS = {
        "usa", "uk", "germany", "france", "china", "russia", "japan",
        "india", "australia", "canada", "mexico", "brazil", "new york",
        "london", "paris", "tokyo", "beijing", "moscow"
    }
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.config = EntityRecognizerConfig()
            self.metrics = EntityRecognizerMetrics()
            self._cache: Dict[str, Tuple[EntityRecognitionResult, float]] = {}
            self._lock = RLock()
            self._processing_times: List[float] = []
            self._initialized = True
    
    def recognize_entities(self, text: str) -> EntityRecognitionResult:
        """
        Recognize and classify entities in text.
        
        Args:
            text: Input text to process
            
        Returns:
            EntityRecognitionResult with extracted entities
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
            entities = []
            
            # Run enabled entity recognizers
            if self.config.enable_technical_recognition:
                entities.extend(self._recognize_ip_addresses(text))
                entities.extend(self._recognize_urls(text))
                entities.extend(self._recognize_emails(text))
                entities.extend(self._recognize_domains(text))
                entities.extend(self._recognize_file_paths(text))
                entities.extend(self._recognize_hashes(text))
                entities.extend(self._recognize_ports(text))
            
            if self.config.enable_security_recognition:
                entities.extend(self._recognize_cves(text))
                entities.extend(self._recognize_attack_types(text))
                entities.extend(self._recognize_threat_actors(text))
                entities.extend(self._recognize_vulnerabilities(text))
            
            if self.config.enable_person_recognition:
                entities.extend(self._recognize_persons(text))
            
            if self.config.enable_organization_recognition:
                entities.extend(self._recognize_organizations(text))
            
            if self.config.enable_location_recognition:
                entities.extend(self._recognize_locations(text))
            
            if self.config.enable_temporal_recognition:
                entities.extend(self._recognize_dates_times(text))
            
            # Filter by confidence threshold
            entities = [e for e in entities if e.confidence.value >= self.config.confidence_threshold.value]
            
            # Sort by position
            entities.sort(key=lambda e: e.start_position)
            
            # Calculate metrics
            unique_types = len(set(e.entity_type for e in entities))
            entity_density = (len(entities) / len(text)) * 100 if text else 0
            processing_time_ms = (time.time() - start_time) * 1000
            self._processing_times.append(processing_time_ms)
            if len(self._processing_times) > 1000:
                self._processing_times.pop(0)
            
            result = EntityRecognitionResult(
                text=text,
                entities=entities,
                entity_count=len(entities),
                unique_entity_types=unique_types,
                entity_density=entity_density,
                processing_time_ms=processing_time_ms
            )
            
            # Cache result
            if self.config.cache_results:
                self._cache[cache_key] = (result, time.time())
            
            # Update metrics
            with self._lock:
                self.metrics.total_texts_processed += 1
                self.metrics.total_entities_recognized += len(entities)
                self.metrics.last_processed_at = datetime.now()
                if len(self._processing_times) > 0:
                    self.metrics.avg_processing_time_ms = sum(self._processing_times) / len(self._processing_times)
                if self.metrics.total_texts_processed > 0:
                    self.metrics.avg_entities_per_text = self.metrics.total_entities_recognized / self.metrics.total_texts_processed
                
                # Track by entity type
                for entity in entities:
                    entity_type_key = entity.entity_type.value
                    self.metrics.entities_by_type[entity_type_key] = self.metrics.entities_by_type.get(entity_type_key, 0) + 1
                
                # Update most common type
                if self.metrics.entities_by_type:
                    max_type = max(self.metrics.entities_by_type, key=self.metrics.entities_by_type.get)
                    self.metrics.most_common_entity_type = EntityType(max_type)
            
            return result
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Error recognizing entities: {str(e)}")
            raise
    
    def get_entities_by_type(self, text: str, entity_type: EntityType) -> List[Entity]:
        """Get entities of specific type from text."""
        result = self.recognize_entities(text)
        return [e for e in result.entities if e.entity_type == entity_type]
    
    def extract_security_entities(self, text: str) -> List[Entity]:
        """Extract all security-related entities from text."""
        result = self.recognize_entities(text)
        security_types = {
            EntityType.IP_ADDRESS, EntityType.DOMAIN, EntityType.CVE,
            EntityType.MALWARE, EntityType.ATTACK_TYPE, EntityType.THREAT_ACTOR,
            EntityType.VULNERABILITY
        }
        return [e for e in result.entities if e.entity_type in security_types]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get entity recognition metrics."""
        return self.metrics.to_dict()
    
    def get_config(self) -> Dict[str, Any]:
        """Get recognizer configuration."""
        return self.config.to_dict()
    
    def update_config(self, **kwargs) -> None:
        """Update recognizer configuration."""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
    
    def clear_cache(self) -> None:
        """Clear recognition cache."""
        with self._lock:
            self._cache.clear()
    
    # Private recognition methods
    
    def _recognize_ip_addresses(self, text: str) -> List[Entity]:
        """Recognize IP addresses in text."""
        entities = []
        for match in self.IP_V4_PATTERN.finditer(text):
            entities.append(Entity(
                text=match.group(0),
                entity_type=EntityType.IP_ADDRESS,
                start_position=match.start(),
                end_position=match.end(),
                confidence=EntityConfidence.VERY_HIGH,
                context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
            ))
        return entities
    
    def _recognize_urls(self, text: str) -> List[Entity]:
        """Recognize URLs in text."""
        entities = []
        for match in self.URL_PATTERN.finditer(text):
            entities.append(Entity(
                text=match.group(0),
                entity_type=EntityType.URL,
                start_position=match.start(),
                end_position=match.end(),
                confidence=EntityConfidence.VERY_HIGH,
                context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
            ))
        return entities
    
    def _recognize_emails(self, text: str) -> List[Entity]:
        """Recognize email addresses in text."""
        entities = []
        for match in self.EMAIL_PATTERN.finditer(text):
            entities.append(Entity(
                text=match.group(0),
                entity_type=EntityType.EMAIL,
                start_position=match.start(),
                end_position=match.end(),
                confidence=EntityConfidence.VERY_HIGH,
                context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
            ))
        return entities
    
    def _recognize_domains(self, text: str) -> List[Entity]:
        """Recognize domain names in text."""
        entities = []
        for match in self.DOMAIN_PATTERN.finditer(text):
            # Skip if already matched as part of URL or email
            domain_text = match.group(0)
            if not any(match.start() >= e.start_position and match.end() <= e.end_position 
                      for e in entities if e.entity_type in [EntityType.URL, EntityType.EMAIL]):
                entities.append(Entity(
                    text=domain_text,
                    entity_type=EntityType.DOMAIN,
                    start_position=match.start(),
                    end_position=match.end(),
                    confidence=EntityConfidence.HIGH,
                    context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
                ))
        return entities
    
    def _recognize_cves(self, text: str) -> List[Entity]:
        """Recognize CVE identifiers in text."""
        entities = []
        for match in self.CVE_PATTERN.finditer(text):
            entities.append(Entity(
                text=match.group(0),
                entity_type=EntityType.CVE,
                start_position=match.start(),
                end_position=match.end(),
                confidence=EntityConfidence.VERY_HIGH,
                context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
            ))
        return entities
    
    def _recognize_attack_types(self, text: str) -> List[Entity]:
        """Recognize attack types in text."""
        entities = []
        text_lower = text.lower()
        for attack in self.ATTACK_TYPES:
            for match in re.finditer(r'\b' + re.escape(attack) + r'\b', text_lower):
                original_text = text[match.start():match.end()]
                entities.append(Entity(
                    text=original_text,
                    entity_type=EntityType.ATTACK_TYPE,
                    start_position=match.start(),
                    end_position=match.end(),
                    confidence=EntityConfidence.HIGH,
                    context=text[max(0, match.start()-20):min(len(text), match.end()+20)],
                    attributes={"attack": attack}
                ))
        return entities
    
    def _recognize_threat_actors(self, text: str) -> List[Entity]:
        """Recognize threat actors in text."""
        entities = []
        text_lower = text.lower()
        for actor in self.THREAT_ACTORS:
            for match in re.finditer(r'\b' + re.escape(actor) + r'\b', text_lower):
                original_text = text[match.start():match.end()]
                entities.append(Entity(
                    text=original_text,
                    entity_type=EntityType.THREAT_ACTOR,
                    start_position=match.start(),
                    end_position=match.end(),
                    confidence=EntityConfidence.MEDIUM,
                    context=text[max(0, match.start()-20):min(len(text), match.end()+20)],
                    attributes={"actor": actor}
                ))
        return entities
    
    def _recognize_vulnerabilities(self, text: str) -> List[Entity]:
        """Recognize known vulnerabilities in text."""
        entities = []
        text_lower = text.lower()
        for vuln in self.KNOWN_VULNS:
            for match in re.finditer(r'\b' + re.escape(vuln) + r'\b', text_lower):
                original_text = text[match.start():match.end()]
                entities.append(Entity(
                    text=original_text,
                    entity_type=EntityType.VULNERABILITY,
                    start_position=match.start(),
                    end_position=match.end(),
                    confidence=EntityConfidence.HIGH,
                    context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
                ))
        return entities
    
    def _recognize_file_paths(self, text: str) -> List[Entity]:
        """Recognize file paths in text."""
        entities = []
        for match in self.FILE_PATH_PATTERN.finditer(text):
            entities.append(Entity(
                text=match.group(0),
                entity_type=EntityType.FILE_PATH,
                start_position=match.start(),
                end_position=match.end(),
                confidence=EntityConfidence.MEDIUM,
                context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
            ))
        return entities
    
    def _recognize_hashes(self, text: str) -> List[Entity]:
        """Recognize file hashes in text."""
        entities = []
        for match in self.HASH_PATTERN.finditer(text):
            hash_value = match.group(0)
            hash_type = "md5" if len(hash_value) == 32 else "sha1" if len(hash_value) == 40 else "sha256"
            entities.append(Entity(
                text=hash_value,
                entity_type=EntityType.HASH,
                start_position=match.start(),
                end_position=match.end(),
                confidence=EntityConfidence.HIGH,
                context=text[max(0, match.start()-20):min(len(text), match.end()+20)],
                attributes={"hash_type": hash_type}
            ))
        return entities
    
    def _recognize_ports(self, text: str) -> List[Entity]:
        """Recognize network ports in text."""
        entities = []
        for match in self.PORT_PATTERN.finditer(text):
            port_num = int(match.group(1))
            if 1 <= port_num <= 65535:
                entities.append(Entity(
                    text=match.group(1),
                    entity_type=EntityType.PORT,
                    start_position=match.start(1),
                    end_position=match.end(1),
                    confidence=EntityConfidence.HIGH,
                    context=text[max(0, match.start()-20):min(len(text), match.end()+20)],
                    attributes={"port_number": port_num}
                ))
        return entities
    
    def _recognize_persons(self, text: str) -> List[Entity]:
        """Recognize person names in text (simplified)."""
        entities = []
        # Simple capitalized word detection
        for match in re.finditer(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b', text):
            entities.append(Entity(
                text=match.group(0),
                entity_type=EntityType.PERSON,
                start_position=match.start(),
                end_position=match.end(),
                confidence=EntityConfidence.MEDIUM,
                context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
            ))
        return entities
    
    def _recognize_organizations(self, text: str) -> List[Entity]:
        """Recognize organization names in text."""
        entities = []
        text_lower = text.lower()
        for org in self.KNOWN_ORGS:
            for match in re.finditer(r'\b' + re.escape(org) + r'\b', text_lower):
                original_text = text[match.start():match.end()]
                entities.append(Entity(
                    text=original_text,
                    entity_type=EntityType.ORGANIZATION,
                    start_position=match.start(),
                    end_position=match.end(),
                    confidence=EntityConfidence.HIGH,
                    context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
                ))
        return entities
    
    def _recognize_locations(self, text: str) -> List[Entity]:
        """Recognize locations in text."""
        entities = []
        text_lower = text.lower()
        for location in self.KNOWN_LOCATIONS:
            for match in re.finditer(r'\b' + re.escape(location) + r'\b', text_lower):
                original_text = text[match.start():match.end()]
                entities.append(Entity(
                    text=original_text,
                    entity_type=EntityType.LOCATION,
                    start_position=match.start(),
                    end_position=match.end(),
                    confidence=EntityConfidence.MEDIUM,
                    context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
                ))
        return entities
    
    def _recognize_dates_times(self, text: str) -> List[Entity]:
        """Recognize dates and times in text."""
        entities = []
        # Simple date patterns (MM/DD/YYYY, DD-MM-YYYY)
        date_pattern = re.compile(r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b')
        for match in date_pattern.finditer(text):
            entities.append(Entity(
                text=match.group(0),
                entity_type=EntityType.DATE,
                start_position=match.start(),
                end_position=match.end(),
                confidence=EntityConfidence.HIGH,
                context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
            ))
        
        # Simple time patterns (HH:MM:SS, HH:MM)
        time_pattern = re.compile(r'\b(?:\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?)\b')
        for match in time_pattern.finditer(text):
            entities.append(Entity(
                text=match.group(0),
                entity_type=EntityType.TIME,
                start_position=match.start(),
                end_position=match.end(),
                confidence=EntityConfidence.MEDIUM,
                context=text[max(0, match.start()-20):min(len(text), match.end()+20)]
            ))
        
        return entities
    
    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()


# Singleton instance
_entity_recognizer = None


def get_entity_recognizer() -> EntityRecognizer:
    """Get EntityRecognizer singleton instance."""
    global _entity_recognizer
    if _entity_recognizer is None:
        _entity_recognizer = EntityRecognizer()
    return _entity_recognizer
