"""
NLP Engine Service
Provides core natural language processing capabilities including tokenization,
preprocessing, normalization, language detection, and model management.
Integrates with entity recognition, sentiment analysis, and semantic understanding.
"""

import re
import threading
import time
import json
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
from threading import RLock
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE = "zh"
    JAPANESE = "ja"
    ARABIC = "ar"
    RUSSIAN = "ru"
    PORTUGUESE = "pt"
    ITALIAN = "it"


class TokenType(Enum):
    """Token classifications"""
    WORD = "word"
    NUMBER = "number"
    PUNCTUATION = "punctuation"
    WHITESPACE = "whitespace"
    SPECIAL = "special"
    URL = "url"
    EMAIL = "email"
    MENTION = "mention"
    HASHTAG = "hashtag"
    EMOJI = "emoji"


class TextNormalizationStrategy(Enum):
    """Text normalization strategies"""
    LOWERCASE = "lowercase"
    PRESERVE_CASE = "preserve_case"
    TITLECASE = "titlecase"
    UPPERCASE = "uppercase"


class NLPTask(Enum):
    """NLP task types"""
    TOKENIZATION = "tokenization"
    NORMALIZATION = "normalization"
    LEMMATIZATION = "lemmatization"
    POS_TAGGING = "pos_tagging"
    DEPENDENCY_PARSING = "dependency_parsing"
    LANGUAGE_DETECTION = "language_detection"
    STOPWORD_FILTERING = "stopword_filtering"


@dataclass
class Token:
    """Individual token with metadata"""
    text: str
    token_type: TokenType
    position: int
    length: int
    is_stopword: bool = False
    lemma: str = ""
    pos_tag: str = ""
    lowercase: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "token_type": self.token_type.value,
            "position": self.position,
            "length": self.length,
            "is_stopword": self.is_stopword,
            "lemma": self.lemma,
            "pos_tag": self.pos_tag,
            "lowercase": self.lowercase
        }


@dataclass
class TextAnalysis:
    """Result of text analysis"""
    text: str
    language: Language
    tokens: List[Token]
    sentences: List[str]
    word_count: int
    unique_words: int
    avg_word_length: float
    text_length: int
    complexity_score: float  # 0-1 indicating text complexity
    vocabulary_richness: float  # 0-1 ratio of unique to total words
    readability_score: float  # 0-100 Flesch-Kincaid level equivalent
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language.value,
            "tokens": [t.to_dict() for t in self.tokens],
            "sentences": self.sentences,
            "word_count": self.word_count,
            "unique_words": self.unique_words,
            "avg_word_length": self.avg_word_length,
            "text_length": self.text_length,
            "complexity_score": self.complexity_score,
            "vocabulary_richness": self.vocabulary_richness,
            "readability_score": self.readability_score,
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class NLPConfig:
    """NLP Engine configuration"""
    normalize_text: bool = True
    normalization_strategy: TextNormalizationStrategy = TextNormalizationStrategy.LOWERCASE
    remove_stopwords: bool = False
    remove_punctuation: bool = False
    min_token_length: int = 1
    max_token_length: int = 100
    detect_language: bool = True
    enable_lemmatization: bool = False
    enable_pos_tagging: bool = False
    cache_analyses: bool = True
    cache_ttl_seconds: int = 3600
    batch_mode: bool = False
    batch_size: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "normalize_text": self.normalize_text,
            "normalization_strategy": self.normalization_strategy.value,
            "remove_stopwords": self.remove_stopwords,
            "remove_punctuation": self.remove_punctuation,
            "min_token_length": self.min_token_length,
            "max_token_length": self.max_token_length,
            "detect_language": self.detect_language,
            "enable_lemmatization": self.enable_lemmatization,
            "enable_pos_tagging": self.enable_pos_tagging,
            "cache_analyses": self.cache_analyses,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "batch_mode": self.batch_mode,
            "batch_size": self.batch_size
        }


@dataclass
class NLPMetrics:
    """Metrics for NLP operations"""
    total_texts_processed: int = 0
    total_tokens_extracted: int = 0
    total_sentences_detected: int = 0
    avg_processing_time_ms: float = 0.0
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    error_count: int = 0
    last_processed_at: Optional[datetime] = None
    most_common_language: Optional[Language] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_texts_processed": self.total_texts_processed,
            "total_tokens_extracted": self.total_tokens_extracted,
            "total_sentences_detected": self.total_sentences_detected,
            "avg_processing_time_ms": self.avg_processing_time_ms,
            "cache_hit_count": self.cache_hit_count,
            "cache_miss_count": self.cache_miss_count,
            "error_count": self.error_count,
            "last_processed_at": self.last_processed_at.isoformat() if self.last_processed_at else None,
            "most_common_language": self.most_common_language.value if self.most_common_language else None,
            "cache_hit_rate": self.cache_hit_count / (self.cache_hit_count + self.cache_miss_count) if (self.cache_hit_count + self.cache_miss_count) > 0 else 0.0
        }


class NLPEngine:
    """
    Core NLP Engine providing text processing, tokenization, analysis.
    Thread-safe singleton service.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    # Stopwords for multiple languages
    STOPWORDS = {
        Language.ENGLISH: {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
                          "is", "are", "am", "was", "were", "be", "been", "being",
                          "have", "has", "had", "do", "does", "did", "would", "could", "should",
                          "that", "this", "these", "those", "which", "who", "whom", "what", "where",
                          "when", "why", "how", "all", "each", "every", "both", "few", "more", "most",
                          "other", "some", "any", "such", "so", "than", "as", "with", "from", "of", "by"},
        Language.SPANISH: {"el", "la", "de", "que", "y", "a", "en", "un", "ser", "se", "no", "haber",
                          "por", "con", "su", "para", "es", "esta", "estamos", "estoy", "sera", "somos",
                          "sois", "estais", "estan", "como", "en", "para", "atras", "bajo", "cabe"},
        Language.FRENCH: {"le", "de", "un", "et", "a", "être", "en", "que", "se", "pas", "je", "tu",
                         "il", "nous", "vous", "ils", "elles", "on", "on", "par", "pour", "dans"}
    }
    
    # Simple URL pattern
    URL_PATTERN = re.compile(
        r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
    )
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    MENTION_PATTERN = re.compile(r'@\w+')
    HASHTAG_PATTERN = re.compile(r'#\w+')
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.config = NLPConfig()
            self.metrics = NLPMetrics()
            self._cache: Dict[str, Tuple[TextAnalysis, float]] = {}
            self._lock = RLock()
            self._language_cache: Dict[str, Language] = {}
            self._processing_times: List[float] = []
            
            # Start background cleanup thread
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_expired_cache, daemon=True
            )
            self._cleanup_thread.start()
            
            self._initialized = True
    
    def analyze_text(self, text: str, language: Optional[Language] = None) -> TextAnalysis:
        """
        Comprehensive text analysis including tokenization, normalization, statistics.
        
        Args:
            text: Input text to analyze
            language: Optional language hint
            
        Returns:
            TextAnalysis with tokens, sentences, metrics
        """
        if not text or not isinstance(text, str):
            self.metrics.error_count += 1
            raise ValueError("Text must be non-empty string")
        
        start_time = time.time()
        
        # Check cache
        cache_key = self._generate_cache_key(text)
        if self.config.cache_analyses and cache_key in self._cache:
            cached_result, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self.config.cache_ttl_seconds:
                self.metrics.cache_hit_count += 1
                return cached_result
        
        self.metrics.cache_miss_count += 1
        
        try:
            # Detect language
            if language is None and self.config.detect_language:
                language = self.detect_language(text)
            else:
                language = language or Language.ENGLISH
            
            # Split sentences
            sentences = self._split_sentences(text)
            
            # Tokenize
            tokens = self._tokenize(text, language)
            
            # Filter and process tokens
            if self.config.remove_stopwords:
                tokens = [t for t in tokens if not self._is_stopword(t.text, language)]
            
            if self.config.remove_punctuation:
                tokens = [t for t in tokens if t.token_type != TokenType.PUNCTUATION]
            
            # Filter by length
            tokens = [t for t in tokens if self.config.min_token_length <= len(t.text) <= self.config.max_token_length]
            
            # Normalize tokens
            if self.config.normalize_text:
                for token in tokens:
                    token.lowercase = self._normalize_text(token.text, self.config.normalization_strategy)
            
            # Calculate statistics
            word_tokens = [t for t in tokens if t.token_type == TokenType.WORD]
            word_count = len(word_tokens)
            unique_words = len(set(t.lowercase for t in word_tokens)) if self.config.normalize_text else len(set(t.text for t in word_tokens))
            avg_word_length = sum(len(t.text) for t in word_tokens) / word_count if word_count > 0 else 0
            vocabulary_richness = unique_words / word_count if word_count > 0 else 0
            
            # Calculate complexity (based on various factors)
            complexity_score = self._calculate_complexity(tokens, sentences, text)
            readability_score = self._calculate_readability(text, sentences, word_tokens)
            
            processing_time_ms = (time.time() - start_time) * 1000
            self._processing_times.append(processing_time_ms)
            if len(self._processing_times) > 1000:
                self._processing_times.pop(0)
            
            analysis = TextAnalysis(
                text=text,
                language=language,
                tokens=tokens,
                sentences=sentences,
                word_count=word_count,
                unique_words=unique_words,
                avg_word_length=avg_word_length,
                text_length=len(text),
                complexity_score=complexity_score,
                vocabulary_richness=vocabulary_richness,
                readability_score=readability_score,
                processing_time_ms=processing_time_ms
            )
            
            # Cache result
            if self.config.cache_analyses:
                self._cache[cache_key] = (analysis, time.time())
            
            # Update metrics
            with self._lock:
                self.metrics.total_texts_processed += 1
                self.metrics.total_tokens_extracted += len(tokens)
                self.metrics.total_sentences_detected += len(sentences)
                self.metrics.last_processed_at = datetime.now()
                if len(self._processing_times) > 0:
                    self.metrics.avg_processing_time_ms = sum(self._processing_times) / len(self._processing_times)
                
                # Track most common language
                language_count = self._language_cache.get(language.value, 0)
                self._language_cache[language.value] = language_count + 1
                if language_count > 0:
                    max_lang = max(self._language_cache.values())
                    self.metrics.most_common_language = Language(
                        [k for k, v in self._language_cache.items() if v == max_lang][0]
                    )
            
            return analysis
            
        except Exception as e:
            self.metrics.error_count += 1
            logger.error(f"Error analyzing text: {str(e)}")
            raise
    
    def detect_language(self, text: str) -> Language:
        """
        Detect language of input text using simple heuristics and character sets.
        
        Args:
            text: Input text
            
        Returns:
            Detected Language
        """
        if not text:
            return Language.ENGLISH
        
        # Check for specific scripts
        cyrillic_count = len(re.findall(r'[а-яА-ЯёЁ]', text))
        greek_count = len(re.findall(r'[α-ωΑ-Ω]', text))
        chinese_count = len(re.findall(r'[\u4e00-\u9fff]', text))
        japanese_count = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
        arabic_count = len(re.findall(r'[\u0600-\u06ff]', text))
        
        total = len(text)
        
        if cyrillic_count > total * 0.3:
            return Language.RUSSIAN
        elif arabic_count > total * 0.3:
            return Language.ARABIC
        elif chinese_count > total * 0.3:
            return Language.CHINESE
        elif japanese_count > total * 0.3:
            return Language.JAPANESE
        
        # Default to English
        return Language.ENGLISH
    
    def extract_tokens(self, text: str) -> List[Token]:
        """Extract tokens from text."""
        analysis = self.analyze_text(text)
        return analysis.tokens
    
    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        return self._split_sentences(text)
    
    def normalize_text(self, text: str, strategy: TextNormalizationStrategy = TextNormalizationStrategy.LOWERCASE) -> str:
        """
        Normalize text with specified strategy.
        
        Args:
            text: Input text
            strategy: Normalization strategy
            
        Returns:
            Normalized text
        """
        return self._normalize_text(text, strategy)
    
    def tokenize(self, text: str, language: Optional[Language] = None) -> List[Token]:
        """
        Tokenize text into individual tokens.
        
        Args:
            text: Input text
            language: Optional language hint
            
        Returns:
            List of tokens
        """
        if language is None:
            language = self.detect_language(text)
        return self._tokenize(text, language)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get NLP engine metrics and statistics."""
        return self.metrics.to_dict()
    
    def get_config(self) -> Dict[str, Any]:
        """Get NLP configuration."""
        return self.config.to_dict()
    
    def update_config(self, **kwargs) -> None:
        """Update NLP configuration."""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
    
    def clear_cache(self) -> None:
        """Clear analysis cache."""
        with self._lock:
            self._cache.clear()
    
    # Private helper methods
    
    def _tokenize(self, text: str, language: Language) -> List[Token]:
        """Tokenize text into Token objects."""
        tokens = []
        position = 0
        
        # Pattern to match different token types
        patterns = [
            (self.URL_PATTERN, TokenType.URL),
            (self.EMAIL_PATTERN, TokenType.EMAIL),
            (self.MENTION_PATTERN, TokenType.MENTION),
            (self.HASHTAG_PATTERN, TokenType.HASHTAG),
            (re.compile(r'\d+\.?\d*'), TokenType.NUMBER),
            (re.compile(r'[^\w\s]'), TokenType.PUNCTUATION),
            (re.compile(r'\s+'), TokenType.WHITESPACE),
            (re.compile(r'\w+'), TokenType.WORD),
        ]
        
        i = 0
        while i < len(text):
            matched = False
            for pattern, token_type in patterns:
                match = pattern.match(text, i)
                if match:
                    token_text = match.group(0)
                    token = Token(
                        text=token_text,
                        token_type=token_type,
                        position=i,
                        length=len(token_text),
                        is_stopword=self._is_stopword(token_text, language) if token_type == TokenType.WORD else False,
                        lowercase=token_text.lower() if token_type == TokenType.WORD else ""
                    )
                    tokens.append(token)
                    i = match.end()
                    matched = True
                    break
            
            if not matched:
                i += 1
        
        return tokens
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting on . ! ? with handling for abbreviations
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _normalize_text(self, text: str, strategy: TextNormalizationStrategy) -> str:
        """Normalize text with given strategy."""
        if strategy == TextNormalizationStrategy.LOWERCASE:
            return text.lower()
        elif strategy == TextNormalizationStrategy.UPPERCASE:
            return text.upper()
        elif strategy == TextNormalizationStrategy.TITLECASE:
            return text.title()
        else:
            return text
    
    def _is_stopword(self, token: str, language: Language) -> bool:
        """Check if token is a stopword."""
        stopwords = self.STOPWORDS.get(language, set())
        return token.lower() in stopwords
    
    def _calculate_complexity(self, tokens: List[Token], sentences: List[str], text: str) -> float:
        """Calculate text complexity score (0-1)."""
        if not tokens or not sentences:
            return 0.0
        
        avg_token_length = sum(len(t.text) for t in tokens) / len(tokens) if tokens else 0
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Normalize to 0-1
        length_complexity = min(avg_token_length / 10, 1.0)  # Long words = more complex
        sentence_complexity = min(avg_sentence_length / 30, 1.0)  # Long sentences = more complex
        
        return (length_complexity + sentence_complexity) / 2
    
    def _calculate_readability(self, text: str, sentences: List[str], word_tokens: List[Token]) -> float:
        """
        Calculate readability score (0-100).
        Flesch-Kincaid Grade Level equivalent.
        """
        if not word_tokens or not sentences:
            return 0.0
        
        word_count = len(word_tokens)
        sentence_count = len(sentences)
        
        # Count syllables (simplified)
        syllable_count = sum(self._count_syllables(t.text) for t in word_tokens)
        
        if sentence_count == 0:
            return 0.0
        
        # Flesch-Kincaid Grade Level
        grade_level = (
            0.39 * (word_count / sentence_count) +
            11.8 * (syllable_count / word_count) - 15.59
        )
        
        # Convert to 0-100 scale (0-12 grade level)
        readability = max(0, min(100, (100 - (grade_level * 8.33))))
        return readability
    
    def _count_syllables(self, word: str) -> int:
        """
        Estimate syllable count in word (simplified algorithm).
        """
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith('e'):
            syllable_count -= 1
        
        # Adjust for le ending
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            syllable_count += 1
        
        return max(1, syllable_count)
    
    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _cleanup_expired_cache(self) -> None:
        """Background task to clean expired cache entries."""
        while True:
            try:
                time.sleep(300)  # Every 5 minutes
                current_time = time.time()
                expired_keys = [
                    k for k, (_, cached_time) in self._cache.items()
                    if current_time - cached_time > self.config.cache_ttl_seconds
                ]
                if expired_keys:
                    with self._lock:
                        for key in expired_keys:
                            del self._cache[key]
            except Exception as e:
                logger.error(f"Error in cache cleanup: {str(e)}")


# Singleton instance
_nlp_engine = None


def get_nlp_engine() -> NLPEngine:
    """Get NLP Engine singleton instance."""
    global _nlp_engine
    if _nlp_engine is None:
        _nlp_engine = NLPEngine()
    return _nlp_engine
