"""
Document Processor Service - Content Parsing and Chunking
Processes various document formats and prepares them for embedding.
"""

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Dict, List, Optional, Tuple, Any, Callable
import hashlib
import time
import re
from datetime import datetime


class ContentType(Enum):
    """Supported content types."""
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    CODE = "code"
    JSON = "json"
    DOCX = "docx"
    CSV = "csv"


class ChunkingStrategy(Enum):
    """Document chunking strategies."""
    FIXED_SIZE = "fixed_size"          # Fixed token/char count
    SLIDING_WINDOW = "sliding_window"  # Sliding window with overlap
    SEMANTIC = "semantic"              # Semantic boundary detection
    HIERARCHICAL = "hierarchical"      # Preserve document structure
    PARAGRAPH = "paragraph"            # Split by paragraphs
    SENTENCE = "sentence"              # Split by sentences


class TokenizationMethod(Enum):
    """Tokenization methods."""
    WHITESPACE = "whitespace"
    REGEX = "regex"
    NLTK = "nltk"
    SPACY = "spacy"
    TIKTOKEN = "tiktoken"


@dataclass
class DocumentChunk:
    """Single chunk from document."""
    chunk_id: str
    original_doc_id: str
    text: str
    chunk_number: int
    total_chunks: int
    start_char: int
    end_char: int
    start_token: int
    end_token: int
    tokens_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    chunk_type: str = "text"  # text, code, table, etc.


@dataclass
class ProcessingConfig:
    """Configuration for document processing."""
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.SLIDING_WINDOW
    chunk_size: int = 512  # tokens
    chunk_overlap: int = 50  # tokens
    min_chunk_size: int = 50
    max_chunk_size: int = 2000
    tokenization_method: TokenizationMethod = TokenizationMethod.REGEX
    preserve_headers: bool = True
    preserve_code_blocks: bool = True
    extract_metadata: bool = True
    clean_text: bool = True
    remove_urls: bool = False
    remove_emails: bool = False
    lowercase: bool = False


@dataclass
class ProcessingResult:
    """Result of document processing."""
    doc_id: str
    original_size: int
    chunks: List[DocumentChunk]
    metadata: Dict[str, Any]
    processing_time_ms: float
    success: bool
    error_message: Optional[str] = None


class DocumentProcessor:
    """Service for processing and chunking documents."""

    def __init__(self):
        """Initialize document processor."""
        self._lock = RLock()
        self._config = ProcessingConfig()
        self._processing_history: deque = deque(maxlen=10000)
        self._chunk_cache: Dict[str, List[DocumentChunk]] = {}
        
        # Format-specific processors
        self._processors: Dict[ContentType, Callable] = {
            ContentType.TEXT: self._process_text,
            ContentType.MARKDOWN: self._process_markdown,
            ContentType.HTML: self._process_html,
            ContentType.CODE: self._process_code,
            ContentType.JSON: self._process_json,
        }
        
        # Statistics
        self._stats = {
            'documents_processed': 0,
            'total_chunks_created': 0,
            'avg_chunks_per_doc': 0.0,
            'avg_processing_time_ms': 0.0,
            'errors': 0,
        }
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            'processing_started': [],
            'chunk_created': [],
            'processing_completed': [],
        }

    def process_document(
        self,
        doc_id: str,
        content: str,
        content_type: ContentType = ContentType.TEXT,
        config: Optional[ProcessingConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ProcessingResult]:
        """Process document and create chunks."""
        with self._lock:
            start_time = time.time()
            config = config or self._config

            self._trigger_callback('processing_started', doc_id=doc_id)

            try:
                # Select processor
                processor = self._processors.get(content_type, self._process_text)

                # Process content
                processed_content = processor(content, config)

                # Chunk content
                chunks = self._chunk_content(
                    doc_id=doc_id,
                    content=processed_content,
                    config=config,
                )

                processing_time = (time.time() - start_time) * 1000

                result = ProcessingResult(
                    doc_id=doc_id,
                    original_size=len(content),
                    chunks=chunks,
                    metadata=metadata or {},
                    processing_time_ms=processing_time,
                    success=True,
                )

                # Update statistics
                self._stats['documents_processed'] += 1
                self._stats['total_chunks_created'] += len(chunks)
                self._stats['avg_chunks_per_doc'] = (
                    self._stats['total_chunks_created'] /
                    self._stats['documents_processed']
                )

                self._processing_history.append({
                    'doc_id': doc_id,
                    'chunks_count': len(chunks),
                    'timestamp': time.time(),
                })

                self._trigger_callback(
                    'processing_completed',
                    doc_id=doc_id,
                    chunks_count=len(chunks),
                    time_ms=processing_time,
                )

                return result

            except Exception as e:
                self._stats['errors'] += 1
                return ProcessingResult(
                    doc_id=doc_id,
                    original_size=len(content),
                    chunks=[],
                    metadata=metadata or {},
                    processing_time_ms=(time.time() - start_time) * 1000,
                    success=False,
                    error_message=str(e),
                )

    def batch_process_documents(
        self,
        documents: List[Tuple[str, str, ContentType]],  # (doc_id, content, type)
        config: Optional[ProcessingConfig] = None,
    ) -> List[ProcessingResult]:
        """Process multiple documents."""
        with self._lock:
            results = []
            for doc_id, content, content_type in documents:
                result = self.process_document(
                    doc_id=doc_id,
                    content=content,
                    content_type=content_type,
                    config=config,
                )
                if result:
                    results.append(result)

            return results

    def rechunk_document(
        self,
        chunks: List[DocumentChunk],
        new_config: ProcessingConfig,
    ) -> List[DocumentChunk]:
        """Rechunk already-processed document."""
        with self._lock:
            if not chunks:
                return []

            # Reconstruct original content
            original_content = "".join(chunk.text for chunk in chunks)

            # Get original doc_id from first chunk
            doc_id = chunks[0].original_doc_id

            # Rechunk with new config
            new_chunks = self._chunk_content(
                doc_id=doc_id,
                content=original_content,
                config=new_config,
            )

            return new_chunks

    def extract_tables(self, content: str) -> List[Dict[str, Any]]:
        """Extract tables from content."""
        with self._lock:
            # Simple table extraction (CSV format detection)
            tables = []
            current_table = []

            for line in content.split('\n'):
                if '|' in line:
                    # Potential table row
                    cells = [cell.strip() for cell in line.split('|')]
                    current_table.append(cells)
                else:
                    if current_table:
                        tables.append({
                            'rows': current_table,
                            'columns': len(current_table[0]) if current_table else 0,
                        })
                        current_table = []

            if current_table:
                tables.append({
                    'rows': current_table,
                    'columns': len(current_table[0]) if current_table else 0,
                })

            return tables

    def extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """Extract code blocks from content."""
        with self._lock:
            code_blocks = []

            # Markdown code blocks (```...```)
            pattern = r'```(\w+)?\n(.*?)\n```'
            matches = re.finditer(pattern, content, re.DOTALL)

            for match in matches:
                language = match.group(1) or "text"
                code = match.group(2)
                code_blocks.append({
                    'language': language,
                    'code': code,
                })

            return code_blocks

    def extract_headers(self, content: str) -> Dict[int, List[str]]:
        """Extract header hierarchy from content."""
        with self._lock:
            headers: Dict[int, List[str]] = defaultdict(list)

            # Markdown headers
            pattern = r'^(#+)\s+(.*)$'
            for line in content.split('\n'):
                match = re.match(pattern, line)
                if match:
                    level = len(match.group(1))
                    text = match.group(2)
                    headers[level].append(text)

            return dict(headers)

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        with self._lock:
            return {
                'documents_processed': self._stats['documents_processed'],
                'total_chunks_created': self._stats['total_chunks_created'],
                'avg_chunks_per_doc': self._stats['avg_chunks_per_doc'],
                'avg_processing_time_ms': self._stats['avg_processing_time_ms'],
                'errors': self._stats['errors'],
            }

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for event."""
        with self._lock:
            if event in self._callbacks:
                self._callbacks[event].append(callback)

    def _chunk_content(
        self,
        doc_id: str,
        content: str,
        config: ProcessingConfig,
    ) -> List[DocumentChunk]:
        """Create chunks from content."""
        chunks = []

        if config.chunking_strategy == ChunkingStrategy.FIXED_SIZE:
            chunks = self._chunk_fixed_size(doc_id, content, config)
        elif config.chunking_strategy == ChunkingStrategy.SLIDING_WINDOW:
            chunks = self._chunk_sliding_window(doc_id, content, config)
        elif config.chunking_strategy == ChunkingStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraph(doc_id, content, config)
        elif config.chunking_strategy == ChunkingStrategy.SENTENCE:
            chunks = self._chunk_by_sentence(doc_id, content, config)
        elif config.chunking_strategy == ChunkingStrategy.HIERARCHICAL:
            chunks = self._chunk_hierarchical(doc_id, content, config)
        else:
            chunks = self._chunk_fixed_size(doc_id, content, config)

        # Number chunks
        for i, chunk in enumerate(chunks):
            chunk.chunk_number = i + 1
            chunk.total_chunks = len(chunks)

        return chunks

    def _chunk_fixed_size(
        self,
        doc_id: str,
        content: str,
        config: ProcessingConfig,
    ) -> List[DocumentChunk]:
        """Chunk with fixed size."""
        chunks = []
        tokens = content.split()
        chunk_size = config.chunk_size

        for i in range(0, len(tokens), chunk_size):
            chunk_tokens = tokens[i:i + chunk_size]

            if len(chunk_tokens) < config.min_chunk_size:
                continue

            text = " ".join(chunk_tokens)

            chunk = DocumentChunk(
                chunk_id=hashlib.sha256(
                    f"{doc_id}_{i}".encode()
                ).hexdigest()[:16],
                original_doc_id=doc_id,
                text=text,
                chunk_number=0,
                total_chunks=0,
                start_char=content.find(text),
                end_char=content.find(text) + len(text),
                start_token=i,
                end_token=i + len(chunk_tokens),
                tokens_count=len(chunk_tokens),
            )

            chunks.append(chunk)
            self._trigger_callback('chunk_created', chunk_id=chunk.chunk_id)

        return chunks

    def _chunk_sliding_window(
        self,
        doc_id: str,
        content: str,
        config: ProcessingConfig,
    ) -> List[DocumentChunk]:
        """Chunk with sliding window."""
        chunks = []
        tokens = content.split()
        chunk_size = config.chunk_size
        overlap = config.chunk_overlap
        stride = chunk_size - overlap

        i = 0
        while i < len(tokens):
            chunk_tokens = tokens[i:i + chunk_size]

            if len(chunk_tokens) < config.min_chunk_size:
                break

            text = " ".join(chunk_tokens)

            chunk = DocumentChunk(
                chunk_id=hashlib.sha256(
                    f"{doc_id}_{i}".encode()
                ).hexdigest()[:16],
                original_doc_id=doc_id,
                text=text,
                chunk_number=0,
                total_chunks=0,
                start_char=content.find(text),
                end_char=content.find(text) + len(text),
                start_token=i,
                end_token=i + len(chunk_tokens),
                tokens_count=len(chunk_tokens),
            )

            chunks.append(chunk)
            self._trigger_callback('chunk_created', chunk_id=chunk.chunk_id)

            i += stride

        return chunks

    def _chunk_by_paragraph(
        self,
        doc_id: str,
        content: str,
        config: ProcessingConfig,
    ) -> List[DocumentChunk]:
        """Chunk by paragraphs."""
        chunks = []
        paragraphs = content.split('\n\n')

        for i, para in enumerate(paragraphs):
            if len(para.strip()) < config.min_chunk_size:
                continue

            chunk = DocumentChunk(
                chunk_id=hashlib.sha256(
                    f"{doc_id}_{i}".encode()
                ).hexdigest()[:16],
                original_doc_id=doc_id,
                text=para,
                chunk_number=0,
                total_chunks=0,
                start_char=content.find(para),
                end_char=content.find(para) + len(para),
                start_token=i,
                end_token=i + 1,
                tokens_count=len(para.split()),
            )

            chunks.append(chunk)
            self._trigger_callback('chunk_created', chunk_id=chunk.chunk_id)

        return chunks

    def _chunk_by_sentence(
        self,
        doc_id: str,
        content: str,
        config: ProcessingConfig,
    ) -> List[DocumentChunk]:
        """Chunk by sentences."""
        chunks = []
        sentences = re.split(r'[.!?]+', content)

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < config.min_chunk_size:
                continue

            chunk = DocumentChunk(
                chunk_id=hashlib.sha256(
                    f"{doc_id}_{i}".encode()
                ).hexdigest()[:16],
                original_doc_id=doc_id,
                text=sentence,
                chunk_number=0,
                total_chunks=0,
                start_char=content.find(sentence),
                end_char=content.find(sentence) + len(sentence),
                start_token=i,
                end_token=i + 1,
                tokens_count=len(sentence.split()),
            )

            chunks.append(chunk)
            self._trigger_callback('chunk_created', chunk_id=chunk.chunk_id)

        return chunks

    def _chunk_hierarchical(
        self,
        doc_id: str,
        content: str,
        config: ProcessingConfig,
    ) -> List[DocumentChunk]:
        """Chunk preserving hierarchical structure."""
        # Use fixed size as default for hierarchical
        return self._chunk_fixed_size(doc_id, content, config)

    def _process_text(self, content: str, config: ProcessingConfig) -> str:
        """Process plain text."""
        text = content

        if config.clean_text:
            text = self._clean_text(text)

        if config.lowercase:
            text = text.lower()

        return text

    def _process_markdown(self, content: str, config: ProcessingConfig) -> str:
        """Process markdown."""
        # Remove markdown formatting
        text = content
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)  # Remove headers
        text = re.sub(r'[*_]{1,2}(.*?)[*_]{1,2}', r'\1', text)  # Remove bold/italic
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Remove links

        return self._process_text(text, config)

    def _process_html(self, content: str, config: ProcessingConfig) -> str:
        """Process HTML."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', content)
        text = re.sub(r'&[a-z]+;', '', text)  # Remove HTML entities

        return self._process_text(text, config)

    def _process_code(self, content: str, config: ProcessingConfig) -> str:
        """Process code."""
        # Keep code as-is, just clean up
        return content

    def _process_json(self, content: str, config: ProcessingConfig) -> str:
        """Process JSON."""
        try:
            import json as json_module
            data = json_module.loads(content)
            # Flatten JSON to text
            text = json_module.dumps(data, indent=2)
            return self._process_text(text, config)
        except Exception:
            return self._process_text(content, config)

    def _clean_text(self, text: str) -> str:
        """Clean text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        return text.strip()

    def _trigger_callback(self, event: str, **kwargs) -> None:
        """Trigger callbacks for event."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(**kwargs)
                except Exception:
                    pass


from collections import defaultdict
