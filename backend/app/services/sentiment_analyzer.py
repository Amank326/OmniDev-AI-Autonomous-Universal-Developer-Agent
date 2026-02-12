"""
Sentiment Analyzer Service
Provides sentiment analysis and opinion extraction from text including
polarity detection, emotion analysis, and threat context assessment.
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


class SentimentPolarity(Enum):
    """Sentiment polarity classification"""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class EmotionType(Enum):
    """Emotion classification"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    SURPRISE = "surprise"
    FEAR = "fear"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    NEUTRAL = "neutral"


class ThreatContext(Enum):
    """Threat-related context"""
    NEUTRAL = "neutral"
    SUSPICIOUS = "suspicious"
    THREATENING = "threatening"
    EMERGENCY = "emergency"
    URGENT = "urgent"


class SubjectivityLevel(Enum):
    """Subjectivity assessment"""
    OBJECTIVE = "objective"
    MOSTLY_OBJECTIVE = "mostly_objective"
    MIXED = "mixed"
    MOSTLY_SUBJECTIVE = "mostly_subjective"
    SUBJECTIVE = "subjective"


@dataclass
class SentimentScore:
    """Detailed sentiment score"""
    polarity: SentimentPolarity  # -1.0 to 1.0 mapped to polarity
    polarity_score: float  # -1.0 (very negative) to 1.0 (very positive)
    confidence: float  # 0.0 to 1.0
    subjectivity: SubjectivityLevel
    subjectivity_score: float  # 0.0 (objective) to 1.0 (subjective)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "polarity": self.polarity.value,
            "polarity_score": self.polarity_score,
            "confidence": self.confidence,
            "subjectivity": self.subjectivity.value,
            "subjectivity_score": self.subjectivity_score
        }


@dataclass
class EmotionScore:
    """Emotion detection scores"""
    primary_emotion: EmotionType
    emotion_scores: Dict[str, float]  # emotion -> confidence
    intensity: float  # 0.0 to 1.0
    secondary_emotions: List[Tuple[EmotionType, float]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_emotion": self.primary_emotion.value,
            "emotion_scores": self.emotion_scores,
            "intensity": self.intensity,
            "secondary_emotions": [(e.value, score) for e, score in self.secondary_emotions]
        }


@dataclass
class ThreatAnalysis:
    """Threat-related sentiment analysis"""
    threat_context: ThreatContext
    threat_score: float  # 0.0 to 1.0
    urgency_level: float  # 0.0 to 1.0
    risk_indicators: List[str]
    suspicious_patterns: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "threat_context": self.threat_context.value,
            "threat_score": self.threat_score,
            "urgency_level": self.urgency_level,
            "risk_indicators": self.risk_indicators,
            "suspicious_patterns": self.suspicious_patterns
        }


@dataclass
class SentimentAnalysisResult:
    """Complete sentiment analysis result"""
    text: str
    sentiment_score: SentimentScore
    emotion_score: Optional[EmotionScore]
    threat_analysis: Optional[ThreatAnalysis]
    positive_aspects: List[str]
    negative_aspects: List[str]
    neutral_aspects: List[str]
    overall_assessment: str
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentiment_score": self.sentiment_score.to_dict(),
            "emotion_score": self.emotion_score.to_dict() if self.emotion_score else None,
            "threat_analysis": self.threat_analysis.to_dict() if self.threat_analysis else None,
            "positive_aspects": self.positive_aspects,
            "negative_aspects": self.negative_aspects,
            "neutral_aspects": self.neutral_aspects,
            "overall_assessment": self.overall_assessment,
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class SentimentAnalyzerConfig:
    """Sentiment analyzer configuration"""
    analyze_emotion: bool = True
    analyze_threat_context: bool = True
    detect_sarcasm: bool = False
    detect_negation: bool = True
    extract_aspects: bool = True
    min_confidence: float = 0.3
    cache_results: bool = True
    cache_ttl_seconds: int = 3600
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analyze_emotion": self.analyze_emotion,
            "analyze_threat_context": self.analyze_threat_context,
            "detect_sarcasm": self.detect_sarcasm,
            "detect_negation": self.detect_negation,
            "extract_aspects": self.extract_aspects,
            "min_confidence": self.min_confidence,
            "cache_results": self.cache_results,
            "cache_ttl_seconds": self.cache_ttl_seconds
        }


@dataclass
class SentimentAnalyzerMetrics:
    """Metrics for sentiment analysis"""
    total_texts_analyzed: int = 0
    avg_polarity_score: float = 0.0
    avg_confidence: float = 0.0
    sentiment_distribution: Dict[str, int] = field(default_factory=dict)
    emotion_distribution: Dict[str, int] = field(default_factory=dict)
    avg_processing_time_ms: float = 0.0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    error_count: int = 0
    last_analyzed_at: Optional[datetime] = None
    most_detected_emotion: Optional[EmotionType] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_texts_analyzed": self.total_texts_analyzed,
            "avg_polarity_score": self.avg_polarity_score,
            "avg_confidence": self.avg_confidence,
            "sentiment_distribution": self.sentiment_distribution,
            "emotion_distribution": self.emotion_distribution,
            "avg_processing_time_ms": self.avg_processing_time_ms,
            "cache_hit_count": self.cache_hit_count,
            "cache_miss_count": self.cache_miss_count,
            "error_count": self.error_count,
            "last_analyzed_at": self.last_analyzed_at.isoformat() if self.last_analyzed_at else None,
            "most_detected_emotion": self.most_detected_emotion.value if self.most_detected_emotion else None,
            "cache_hit_rate": self.cache_hit_count / (self.cache_hit_count + self.cache_miss_count) if (self.cache_hit_count + self.cache_miss_count) > 0 else 0.0
        }


class SentimentAnalyzer:
    """
    Sentiment and emotion analyzer for text comprehension.
    Thread-safe singleton with support for polarity, emotion, and threat analysis.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # Positive words lexicon (simplified)
    POSITIVE_WORDS = {
        "good", "great", "excellent", "amazing", "wonderful", "fantastic",
        "awesome", "perfect", "beautiful", "love", "happy", "excellent",
        "best", "positive", "bright", "wonderful", "terrific", "outstanding",
        "secure", "safe", "protected", "resolved", "fixed", "solved",
        "working", "operational", "clear", "successful"
    }
    
    # Negative words lexicon (simplified)
    NEGATIVE_WORDS = {
        "bad", "terrible", "awful", "horrible", "dreadful", "disgusting",
        "hate", "sad", "angry", "worst", "negative", "dark", "ugly",
        "broken", "fail", "failure", "error", "problem", "issue",
        "vulnerability", "breach", "compromise", "danger", "risk",
        "threat", "attack", "malware", "exploit", "critical", "severe",
        "dangerous", "unsafe", "vulnerable", "compromised", "down", "offline"
    }
    
    # Trust/confidence words
    TRUST_WORDS = {
        "trust", "reliable", "authentic", "verified", "certified", "proven",
        "trusted", "secure", "safe", "reputable", "legitimate"
    }
    
    # Fear/urgency words
    FEAR_WORDS = {
        "panic", "urgent", "emergency", "crisis", "critical", "severe",
        "immediately", "now", "must", "danger", "threat", "warning",
        "alert", "alarm", "alarming", "horror", "terrible", "dreadful"
    }
    
    # Negation words
    NEGATION_WORDS = {
        "not", "no", "never", "neither", "nor", "nothing", "nowhere",
        "cannot", "can't", "couldn't", "wouldn't", "shouldn't", "don't", "doesn't",
        "didn't", "haven't", "hasn't", "hadn't", "isn't", "aren't", "aren't"
    }
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.config = SentimentAnalyzerConfig()
            self.metrics = SentimentAnalyzerMetrics()
            self._cache: Dict[str, Tuple[SentimentAnalysisResult, float]] = {}
            self._lock = RLock()
            self._processing_times: List[float] = []
            self._polarity_scores: List[float] = []
            self._confidence_scores: List[float] = []
            self._initialized = True
    
    def analyze_sentiment(self, text: str) -> SentimentAnalysisResult:
        """
        Analyze sentiment and emotions in text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            SentimentAnalysisResult with comprehensive sentiment analysis
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
            # Analyze sentiment polarity
            sentiment_score = self._analyze_polarity(text)
            
            # Analyze emotions
            emotion_score = self._analyze_emotions(text) if self.config.analyze_emotion else None
            
            # Analyze threat context
            threat_analysis = self._analyze_threat_context(text) if self.config.analyze_threat_context else None
            
            # Extract aspects
            positive_aspects, negative_aspects, neutral_aspects = self._extract_aspects(text)
            
            # Generate assessment
            overall_assessment = self._generate_assessment(
                sentiment_score, emotion_score, threat_analysis
            )
            
            processing_time_ms = (time.time() - start_time) * 1000
            self._processing_times.append(processing_time_ms)
            if len(self._processing_times) > 1000:
                self._processing_times.pop(0)
            
            result = SentimentAnalysisResult(
                text=text,
                sentiment_score=sentiment_score,
                emotion_score=emotion_score,
                threat_analysis=threat_analysis,
                positive_aspects=positive_aspects,
                negative_aspects=negative_aspects,
                neutral_aspects=neutral_aspects,
                overall_assessment=overall_assessment,
                processing_time_ms=processing_time_ms
            )
            
            # Cache result
            if self.config.cache_results:
                self._cache[cache_key] = (result, time.time())
            
            # Update metrics
            with self._lock:
                self.metrics.total_texts_analyzed += 1
                self.metrics.last_analyzed_at = datetime.now()
                
                self._polarity_scores.append(sentiment_score.polarity_score)
                self._confidence_scores.append(sentiment_score.confidence)
                
                if len(self._polarity_scores) > 0:
                    self.metrics.avg_polarity_score = sum(self._polarity_scores) / len(self._polarity_scores)
                if len(self._confidence_scores) > 0:
                    self.metrics.avg_confidence = sum(self._confidence_scores) / len(self._confidence_scores)
                if len(self._processing_times) > 0:
                    self.metrics.avg_processing_time_ms = sum(self._processing_times) / len(self._processing_times)
                
                # Track sentiment distribution
                polarity_key = sentiment_score.polarity.value
                self.metrics.sentiment_distribution[polarity_key] = (
                    self.metrics.sentiment_distribution.get(polarity_key, 0) + 1
                )
                
                # Track emotion distribution
                if emotion_score:
                    emotion_key = emotion_score.primary_emotion.value
                    self.metrics.emotion_distribution[emotion_key] = (
                        self.metrics.emotion_distribution.get(emotion_key, 0) + 1
                    )
                    # Update most detected emotion
                    if emotion_key:
                        max_emotion = max(self.metrics.emotion_distribution, 
                                        key=self.metrics.emotion_distribution.get)
                        self.metrics.most_detected_emotion = EmotionType(max_emotion)
            
            return result
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Error analyzing sentiment: {str(e)}")
            raise
    
    def get_polarity_score(self, text: str) -> Tuple[float, float]:
        """Get polarity score (-1 to 1) and confidence."""
        result = self.analyze_sentiment(text)
        return result.sentiment_score.polarity_score, result.sentiment_score.confidence
    
    def get_emotion(self, text: str) -> Optional[EmotionType]:
        """Get primary emotion detected in text."""
        result = self.analyze_sentiment(text)
        return result.emotion_score.primary_emotion if result.emotion_score else None
    
    def is_threatening(self, text: str) -> Tuple[bool, float]:
        """Check if text contains threatening sentiment."""
        result = self.analyze_sentiment(text)
        if result.threat_analysis:
            return result.threat_analysis.threat_context in [
                ThreatContext.THREATENING, ThreatContext.EMERGENCY
            ], result.threat_analysis.threat_score
        return False, 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get sentiment analysis metrics."""
        return self.metrics.to_dict()
    
    def get_config(self) -> Dict[str, Any]:
        """Get analyzer configuration."""
        return self.config.to_dict()
    
    def update_config(self, **kwargs) -> None:
        """Update analyzer configuration."""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
    
    def clear_cache(self) -> None:
        """Clear analysis cache."""
        with self._lock:
            self._cache.clear()
    
    # Private analysis methods
    
    def _analyze_polarity(self, text: str) -> SentimentScore:
        """Analyze sentiment polarity of text."""
        text_lower = text.lower()
        words = text_lower.split()
        
        positive_count = 0
        negative_count = 0
        
        # Account for negation
        previous_word = None
        for word in words:
            is_negation = word in self.NEGATION_WORDS if self.config.detect_negation else False
            
            if word in self.POSITIVE_WORDS:
                if is_negation or (previous_word and previous_word in self.NEGATION_WORDS):
                    negative_count += 1
                else:
                    positive_count += 1
            elif word in self.NEGATIVE_WORDS:
                if is_negation or (previous_word and previous_word in self.NEGATION_WORDS):
                    positive_count += 1
                else:
                    negative_count += 1
            
            previous_word = word
        
        total = positive_count + negative_count
        if total == 0:
            polarity_score = 0.0
            confidence = 0.0
        else:
            polarity_score = (positive_count - negative_count) / total
            confidence = total / (len(words) + 1)  # Normalize by text length
        
        # Map to polarity
        if polarity_score < -0.6:
            polarity = SentimentPolarity.VERY_NEGATIVE
        elif polarity_score < -0.2:
            polarity = SentimentPolarity.NEGATIVE
        elif polarity_score < 0.2:
            polarity = SentimentPolarity.NEUTRAL
        elif polarity_score < 0.6:
            polarity = SentimentPolarity.POSITIVE
        else:
            polarity = SentimentPolarity.VERY_POSITIVE
        
        # Detect subjectivity
        subjective_indicators = positive_count + negative_count
        subjectivity_score = min(subjective_indicators / (len(words) + 1), 1.0)
        
        if subjectivity_score < 0.2:
            subjectivity = SubjectivityLevel.OBJECTIVE
        elif subjectivity_score < 0.4:
            subjectivity = SubjectivityLevel.MOSTLY_OBJECTIVE
        elif subjectivity_score < 0.6:
            subjectivity = SubjectivityLevel.MIXED
        elif subjectivity_score < 0.8:
            subjectivity = SubjectivityLevel.MOSTLY_SUBJECTIVE
        else:
            subjectivity = SubjectivityLevel.SUBJECTIVE
        
        return SentimentScore(
            polarity=polarity,
            polarity_score=polarity_score,
            confidence=confidence,
            subjectivity=subjectivity,
            subjectivity_score=subjectivity_score
        )
    
    def _analyze_emotions(self, text: str) -> EmotionScore:
        """Analyze emotions in text."""
        text_lower = text.lower()
        words = set(text_lower.split())
        
        emotion_scores = {
            "joy": len(words & {"good", "great", "happy", "awesome", "wonderful"}),
            "sadness": len(words & {"sad", "unhappy", "depressed", "down", "lost"}),
            "anger": len(words & {"angry", "furious", "mad", "rage", "hate"}),
            "fear": len(words & {"afraid", "scared", "terrified", "dread", "panic"}),
            "trust": len(words & self.TRUST_WORDS),
            "surprise": len(words & {"shocked", "surprised", "amazed", "astonished"}),
            "disgust": len(words & {"disgusted", "repulsed", "revolted", "sickened"}),
            "anticipation": len(words & {"expect", "anticipate", "await", "ready"}),
        }
        
        # Normalize scores
        total = sum(emotion_scores.values())
        if total > 0:
            emotion_scores = {k: v / total for k, v in emotion_scores.items()}
        
        # Find primary emotion
        primary = max(emotion_scores, key=emotion_scores.get)
        primary_score = emotion_scores[primary]
        
        # Find secondary emotions
        secondary = sorted(
            [(k, v) for k, v in emotion_scores.items() if k != primary],
            key=lambda x: x[1],
            reverse=True
        )[:2]
        secondary_emotions = [(EmotionType(k), v) for k, v in secondary]
        
        intensity = max(emotion_scores.values()) if emotion_scores else 0.0
        
        return EmotionScore(
            primary_emotion=EmotionType(primary),
            emotion_scores=emotion_scores,
            intensity=intensity,
            secondary_emotions=secondary_emotions
        )
    
    def _analyze_threat_context(self, text: str) -> ThreatAnalysis:
        """Analyze threat-related context in text."""
        text_lower = text.lower()
        words = text_lower.split()
        
        threat_indicators = []
        urgency_indicators = []
        
        # Count threat and urgency indicators
        threat_count = sum(1 for w in words if any(threat in w for threat in self.NEGATIVE_WORDS))
        urgency_count = sum(1 for w in words if any(urgency in w for urgency in self.FEAR_WORDS))
        
        # Check for specific threat patterns
        if "attack" in text_lower or "breach" in text_lower:
            threat_indicators.append("explicit_attack_mention")
        if "urgent" in text_lower or "immediately" in text_lower:
            urgency_indicators.append("explicit_urgency")
        if "critical" in text_lower or "critical" in text_lower:
            threat_indicators.append("critical_severity")
        
        threat_score = min((threat_count + urgency_count) / (len(words) + 1), 1.0)
        urgency_level = min(urgency_count / (len(words) + 1), 1.0)
        
        # Classify threat context
        if threat_score > 0.6:
            threat_context = ThreatContext.THREATENING if urgency_level < 0.8 else ThreatContext.EMERGENCY
        elif threat_score > 0.3:
            threat_context = ThreatContext.SUSPICIOUS
        else:
            threat_context = ThreatContext.NEUTRAL
        
        return ThreatAnalysis(
            threat_context=threat_context,
            threat_score=threat_score,
            urgency_level=urgency_level,
            risk_indicators=threat_indicators,
            suspicious_patterns=urgency_indicators if urgency_level > 0.3 else []
        )
    
    def _extract_aspects(self, text: str) -> Tuple[List[str], List[str], List[str]]:
        """Extract positive, negative, and neutral aspects from text."""
        text_lower = text.lower()
        words = text_lower.split()
        
        positive = [w for w in words if w in self.POSITIVE_WORDS]
        negative = [w for w in words if w in self.NEGATIVE_WORDS]
        neutral = [w for w in words if w in self.TRUST_WORDS and w not in positive]
        
        return list(set(positive)), list(set(negative)), list(set(neutral))
    
    def _generate_assessment(
        self,
        sentiment: SentimentScore,
        emotion: Optional[EmotionScore],
        threat: Optional[ThreatAnalysis]
    ) -> str:
        """Generate overall sentiment assessment."""
        parts = []
        
        # Polarity assessment
        if sentiment.polarity == SentimentPolarity.VERY_POSITIVE:
            parts.append("Highly positive sentiment")
        elif sentiment.polarity == SentimentPolarity.POSITIVE:
            parts.append("Positive sentiment")
        elif sentiment.polarity == SentimentPolarity.NEUTRAL:
            parts.append("Neutral sentiment")
        elif sentiment.polarity == SentimentPolarity.NEGATIVE:
            parts.append("Negative sentiment")
        else:
            parts.append("Highly negative sentiment")
        
        # Emotion assessment
        if emotion and emotion.intensity > 0.5:
            parts.append(f"Strong {emotion.primary_emotion.value} emotion")
        
        # Threat assessment
        if threat and threat.threat_context != ThreatContext.NEUTRAL:
            parts.append(f"Contains {threat.threat_context.value} context")
        
        # Subjectivity assessment
        if sentiment.subjectivity in [SubjectivityLevel.SUBJECTIVE, SubjectivityLevel.MOSTLY_SUBJECTIVE]:
            parts.append("Highly subjective")
        
        return "; ".join(parts) if parts else "Neutral assessment"
    
    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()


# Singleton instance
_sentiment_analyzer = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get SentimentAnalyzer singleton instance."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer
