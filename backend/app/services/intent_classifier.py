"""
Intent Classifier Service
Classifies text into predefined intents for command processing,
request understanding, and intent-based routing.
Integrates with NLP engine and entity recognition.
"""

import threading
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
from threading import RLock

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Predefined intent types"""
    # Security-related intents
    REPORT_SECURITY_ISSUE = "report_security_issue"
    CHECK_COMPLIANCE = "check_compliance"
    PERFORM_AUDIT = "perform_audit"
    UPDATE_POLICY = "update_policy"
    INVESTIGATE_THREAT = "investigate_threat"
    RESPOND_TO_INCIDENT = "respond_to_incident"
    
    # Data-related intents
    QUERY_DATABASE = "query_database"
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"
    DELETE_DATA = "delete_data"
    SEARCH_DATA = "search_data"
    
    # System intents
    SYSTEM_STATUS = "system_status"
    PERFORM_BACKUP = "perform_backup"
    PERFORM_RESTORE = "perform_restore"
    MANAGE_USERS = "manage_users"
    CONFIGURE_SYSTEM = "configure_system"
    
    # Analysis intents
    ANALYZE_SENTIMENT = "analyze_sentiment"
    EXTRACT_ENTITIES = "extract_entities"
    FIND_SIMILAR = "find_similar"
    CLASSIFY_DOCUMENT = "classify_document"
    
    # Information retrieval
    GET_INFORMATION = "get_information"
    PROVIDE_RECOMMENDATION = "provide_recommendation"
    EXPLAIN_CONCEPT = "explain_concept"
    ANSWER_QUESTION = "answer_question"
    
    # Unknown intent
    UNKNOWN = "unknown"
    CHITCHAT = "chitchat"


class ConfidenceLevel(Enum):
    """Confidence levels for intent classification"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class Intent:
    """Classified intent for input text"""
    intent_type: IntentType
    confidence: float  # 0.0 to 1.0
    confidence_level: ConfidenceLevel
    matched_patterns: List[str]
    required_entities: List[str]
    optional_entities: List[str]
    action_parameters: Dict[str, Any] = field(default_factory=dict)
    alternatives: List[Tuple[IntentType, float]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_type": self.intent_type.value,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "matched_patterns": self.matched_patterns,
            "required_entities": self.required_entities,
            "optional_entities": self.optional_entities,
            "action_parameters": self.action_parameters,
            "alternatives": [(i.value, c) for i, c in self.alternatives]
        }


@dataclass
class IntentClassificationResult:
    """Complete intent classification result"""
    text: str
    primary_intent: Intent
    all_intents: List[Intent]
    intent_confidence: float
    requires_clarification: bool
    clarification_questions: List[str]
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_intent": self.primary_intent.to_dict(),
            "all_intents": [i.to_dict() for i in self.all_intents],
            "intent_confidence": self.intent_confidence,
            "requires_clarification": self.requires_clarification,
            "clarification_questions": self.clarification_questions,
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class IntentClassifierConfig:
    """Intent classifier configuration"""
    enable_intent_suggestions: bool = True
    confidence_threshold: float = 0.5
    max_alternatives: int = 3
    allow_multi_intent: bool = False
    cache_results: bool = True
    cache_ttl_seconds: int = 3600
    auto_detect_entities: bool = True
    require_entity_validation: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enable_intent_suggestions": self.enable_intent_suggestions,
            "confidence_threshold": self.confidence_threshold,
            "max_alternatives": self.max_alternatives,
            "allow_multi_intent": self.allow_multi_intent,
            "cache_results": self.cache_results,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "auto_detect_entities": self.auto_detect_entities,
            "require_entity_validation": self.require_entity_validation
        }


@dataclass
class IntentClassifierMetrics:
    """Metrics for intent classification"""
    total_texts_classified: int = 0
    intent_distribution: Dict[str, int] = field(default_factory=dict)
    avg_confidence: float = 0.0
    avg_processing_time_ms: float = 0.0
    clarification_requests: int = 0
    unknown_intent_count: int = 0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    error_count: int = 0
    last_classified_at: Optional[datetime] = None
    most_common_intent: Optional[IntentType] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_texts_classified": self.total_texts_classified,
            "intent_distribution": self.intent_distribution,
            "avg_confidence": self.avg_confidence,
            "avg_processing_time_ms": self.avg_processing_time_ms,
            "clarification_requests": self.clarification_requests,
            "unknown_intent_count": self.unknown_intent_count,
            "cache_hit_count": self.cache_hit_count,
            "cache_miss_count": self.cache_miss_count,
            "error_count": self.error_count,
            "last_classified_at": self.last_classified_at.isoformat() if self.last_classified_at else None,
            "most_common_intent": self.most_common_intent.value if self.most_common_intent else None,
            "cache_hit_rate": self.cache_hit_count / (self.cache_hit_count + self.cache_miss_count) if (self.cache_hit_count + self.cache_miss_count) > 0 else 0.0
        }


class IntentClassifier:
    """
    Intent classification service for understanding user commands and requests.
    Thread-safe singleton supporting multiple intent types.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # Intent patterns and keywords
    INTENT_PATTERNS = {
        IntentType.REPORT_SECURITY_ISSUE: {
            "keywords": ["report", "vulnerability", "security", "issue", "breach", "threat"],
            "phrases": ["report security", "found issue", "security problem"],
            "required_entities": ["issue_description"],
            "optional_entities": ["severity", "affected_resource"]
        },
        IntentType.CHECK_COMPLIANCE: {
            "keywords": ["compliance", "check", "audit", "verify", "validate"],
            "phrases": ["check compliance", "run audit", "verify compliance"],
            "required_entities": ["compliance_framework"],
            "optional_entities": ["resources", "date_range"]
        },
        IntentType.QUERY_DATABASE: {
            "keywords": ["query", "select", "search", "database", "data", "retrieve"],
            "phrases": ["query database", "search records", "get data"],
            "required_entities": ["query", "table"],
            "optional_entities": ["filters", "ordering"]
        },
        IntentType.SEARCH_DATA: {
            "keywords": ["search", "find", "look for", "discover", "locate"],
            "phrases": ["search for", "find data", "locate records"],
            "required_entities": ["search_term"],
            "optional_entities": ["scope", "filters"]
        },
        IntentType.ANALYZE_SENTIMENT: {
            "keywords": ["analyze", "sentiment", "opinion", "emotion", "mood"],
            "phrases": ["analyze sentiment", "check opinion", "detect emotion"],
            "required_entities": ["text"],
            "optional_entities": []
        },
        IntentType.EXTRACT_ENTITIES: {
            "keywords": ["extract", "entities", "identify", "recognize", "find", "keywords"],
            "phrases": ["extract entities", "identify keywords", "recognize entities"],
            "required_entities": ["text"],
            "optional_entities": ["entity_types"]
        },
        IntentType.INVESTIGATE_THREAT: {
            "keywords": ["investigate", "threat", "incident", "attack", "breach"],
            "phrases": ["investigate attack", "check threat", "analyze incident"],
            "required_entities": ["threat_id", "incident_id"],
            "optional_entities": ["timeline", "scope"]
        },
        IntentType.SYSTEM_STATUS: {
            "keywords": ["status", "health", "check", "how are", "operational"],
            "phrases": ["system status", "health check", "how is system"],
            "required_entities": [],
            "optional_entities": ["component"]
        },
        IntentType.GET_INFORMATION: {
            "keywords": ["tell me", "explain", "what is", "how does", "information"],
            "phrases": ["tell me about", "explain how", "what is"],
            "required_entities": ["topic"],
            "optional_entities": []
        },
        IntentType.ANSWER_QUESTION: {
            "keywords": ["question", "ask", "why", "why not", "what", "how", "when", "where"],
            "phrases": ["answer the question", "can you answer"],
            "required_entities": ["question"],
            "optional_entities": []
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
            self.config = IntentClassifierConfig()
            self.metrics = IntentClassifierMetrics()
            self._cache: Dict[str, Tuple[IntentClassificationResult, float]] = {}
            self._lock = RLock()
            self._processing_times: List[float] = []
            self._confidence_scores: List[float] = []
            self._initialized = True
    
    def classify_intent(self, text: str) -> IntentClassificationResult:
        """
        Classify intent for input text.
        
        Args:
            text: Input text to classify
            
        Returns:
            IntentClassificationResult with classified intent(s)
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
            # Score all intents
            intent_scores = self._score_intents(text)
            
            # Sort by confidence
            sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1][0], reverse=True)
            
            # Create Intent objects
            all_intents = []
            for intent_type, (confidence, patterns) in sorted_intents[:self.config.max_alternatives + 1]:
                if confidence >= self.config.confidence_threshold:
                    intent = self._create_intent(intent_type, confidence, patterns)
                    all_intents.append(intent)
            
            # Select primary intent
            if not all_intents:
                primary_intent = self._create_intent(IntentType.UNKNOWN, 0.0, [])
                all_intents = [primary_intent]
            else:
                primary_intent = all_intents[0]
            
            # Check if clarification is needed
            requires_clarification = primary_intent.confidence < 0.7
            clarification_questions = self._generate_clarification_questions(primary_intent, text)
            
            processing_time_ms = (time.time() - start_time) * 1000
            self._processing_times.append(processing_time_ms)
            if len(self._processing_times) > 1000:
                self._processing_times.pop(0)
            
            self._confidence_scores.append(primary_intent.confidence)
            if len(self._confidence_scores) > 1000:
                self._confidence_scores.pop(0)
            
            result = IntentClassificationResult(
                text=text,
                primary_intent=primary_intent,
                all_intents=all_intents,
                intent_confidence=primary_intent.confidence,
                requires_clarification=requires_clarification,
                clarification_questions=clarification_questions,
                processing_time_ms=processing_time_ms
            )
            
            # Cache result
            if self.config.cache_results:
                self._cache[cache_key] = (result, time.time())
            
            # Update metrics
            with self._lock:
                self.metrics.total_texts_classified += 1
                self.metrics.last_classified_at = datetime.now()
                
                intent_key = primary_intent.intent_type.value
                self.metrics.intent_distribution[intent_key] = (
                    self.metrics.intent_distribution.get(intent_key, 0) + 1
                )
                
                if primary_intent.intent_type == IntentType.UNKNOWN:
                    self.metrics.unknown_intent_count += 1
                
                if requires_clarification:
                    self.metrics.clarification_requests += 1
                
                if len(self._confidence_scores) > 0:
                    self.metrics.avg_confidence = sum(self._confidence_scores) / len(self._confidence_scores)
                if len(self._processing_times) > 0:
                    self.metrics.avg_processing_time_ms = sum(self._processing_times) / len(self._processing_times)
                
                # Track most common intent
                if self.metrics.intent_distribution:
                    most_common_key = max(self.metrics.intent_distribution, 
                                         key=self.metrics.intent_distribution.get)
                    self.metrics.most_common_intent = IntentType(most_common_key)
            
            return result
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Error classifying intent: {str(e)}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get intent classification metrics."""
        return self.metrics.to_dict()
    
    def get_config(self) -> Dict[str, Any]:
        """Get classifier configuration."""
        return self.config.to_dict()
    
    def update_config(self, **kwargs) -> None:
        """Update classifier configuration."""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
    
    def clear_cache(self) -> None:
        """Clear classification cache."""
        with self._lock:
            self._cache.clear()
    
    # Private methods
    
    def _score_intents(self, text: str) -> Dict[IntentType, Tuple[float, List[str]]]:
        """Score all possible intents for text."""
        text_lower = text.lower()
        scores = {}
        
        for intent_type, pattern_data in self.INTENT_PATTERNS.items():
            score = 0.0
            matched_patterns = []
            
            # Check keywords
            keywords = pattern_data.get("keywords", [])
            keyword_matches = sum(1 for kw in keywords if kw in text_lower)
            if keyword_matches > 0:
                score += (keyword_matches / len(keywords)) * 0.5 if keywords else 0
                for kw in keywords:
                    if kw in text_lower:
                        matched_patterns.append(f"keyword:{kw}")
            
            # Check phrases
            phrases = pattern_data.get("phrases", [])
            phrase_matches = sum(1 for phrase in phrases if phrase in text_lower)
            if phrase_matches > 0:
                score += (phrase_matches / len(phrases)) * 0.5 if phrases else 0
                for phrase in phrases:
                    if phrase in text_lower:
                        matched_patterns.append(f"phrase:{phrase}")
            
            scores[intent_type] = (min(score, 1.0), matched_patterns)
        
        # Unknown intent if no matches
        if all(score == 0.0 for _, (score, _) in scores.items()):
            scores[IntentType.UNKNOWN] = (0.5, ["no_match"])
            scores[IntentType.CHITCHAT] = (0.3, [])
        
        return scores
    
    def _create_intent(self, intent_type: IntentType, confidence: float, patterns: List[str]) -> Intent:
        """Create Intent object."""
        pattern_data = self.INTENT_PATTERNS.get(intent_type, {
            "required_entities": [],
            "optional_entities": []
        })
        
        # Map confidence to level
        if confidence >= 0.9:
            confidence_level = ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.7:
            confidence_level = ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            confidence_level = ConfidenceLevel.MEDIUM
        elif confidence >= 0.3:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.VERY_LOW
        
        return Intent(
            intent_type=intent_type,
            confidence=confidence,
            confidence_level=confidence_level,
            matched_patterns=patterns,
            required_entities=pattern_data.get("required_entities", []),
            optional_entities=pattern_data.get("optional_entities", [])
        )
    
    def _generate_clarification_questions(self, intent: Intent, text: str) -> List[str]:
        """Generate clarification questions if needed."""
        questions = []
        
        if intent.intent_type == IntentType.UNKNOWN:
            questions.append("Could you please rephrase your request?")
            questions.append("Are you asking about security, data, or system management?")
        
        if intent.required_entities:
            missing = intent.required_entities
            if intent.intent_type == IntentType.QUERY_DATABASE:
                questions.append(f"Which table or data would you like to query?")
            elif intent.intent_type == IntentType.REPORT_SECURITY_ISSUE:
                questions.append(f"Can you provide more details about the issue?")
        
        return questions[:2]  # Return top 2 clarification questions
    
    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()


# Singleton instance
_intent_classifier = None


def get_intent_classifier() -> IntentClassifier:
    """Get IntentClassifier singleton instance."""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
