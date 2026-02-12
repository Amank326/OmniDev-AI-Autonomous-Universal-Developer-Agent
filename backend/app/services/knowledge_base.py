"""
Knowledge Base Manager - Document & Collection Management
Manages knowledge bases, documents, and metadata for RAG systems.
"""

from collections import deque, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Dict, List, Optional, Set, Any, Callable
import hashlib
import time
from datetime import datetime


class KBStatus(Enum):
    """Knowledge base status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    MAINTENANCE = "maintenance"


class DocumentStatus(Enum):
    """Document status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    DELETED = "deleted"


class AccessLevel(Enum):
    """Access control levels."""
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"
    RESTRICTED = "restricted"


@dataclass
class DocumentMetadata:
    """Metadata for a document."""
    doc_id: str
    title: str
    description: str
    author: str
    source: str
    content_type: str  # text, pdf, html, markdown, code, etc.
    language: str = "en"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    category: str = ""
    access_level: AccessLevel = AccessLevel.PRIVATE
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Document in knowledge base."""
    doc_id: str
    content: str
    metadata: DocumentMetadata
    status: DocumentStatus = DocumentStatus.DRAFT
    embeddings_computed: bool = False
    indexed: bool = False
    views: int = 0
    likes: int = 0
    dislikes: int = 0


@dataclass
class KBConfig:
    """Configuration for knowledge base."""
    name: str
    description: str
    owner: str
    access_level: AccessLevel = AccessLevel.PRIVATE
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    max_documents: int = 1000000
    auto_index: bool = True
    enable_versioning: bool = True
    retention_days: Optional[int] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentVersion:
    """Document version history."""
    version_id: str
    doc_id: str
    content: str
    changed_by: str
    change_description: str
    created_at: float = field(default_factory=time.time)
    parent_version_id: Optional[str] = None


@dataclass
class KBStatistics:
    """Statistics for knowledge base."""
    total_documents: int = 0
    indexed_documents: int = 0
    published_documents: int = 0
    total_content_size_mb: float = 0.0
    total_views: int = 0
    avg_rating: float = 0.0
    last_updated: Optional[float] = None


class KnowledgeBase:
    """Service for managing knowledge bases."""

    def __init__(self):
        """Initialize knowledge base manager."""
        self._lock = RLock()
        self._kbs: Dict[str, KBConfig] = {}
        self._documents: Dict[str, Dict[str, Document]] = defaultdict(dict)  # kb_name -> doc_id -> doc
        self._versions: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))  # doc_id -> versions
        self._statistics: Dict[str, KBStatistics] = defaultdict(KBStatistics)
        
        # Metadata indices
        self._doc_by_tag: Dict[str, Set[str]] = defaultdict(set)  # tag -> doc_ids
        self._doc_by_category: Dict[str, Set[str]] = defaultdict(set)  # category -> doc_ids
        self._doc_by_author: Dict[str, Set[str]] = defaultdict(set)  # author -> doc_ids
        self._doc_by_source: Dict[str, Set[str]] = defaultdict(set)  # source -> doc_ids
        
        # Access control
        self._permissions: Dict[str, Dict[str, AccessLevel]] = {}  # user -> kb -> level
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            'kb_created': [],
            'document_added': [],
            'document_updated': [],
            'document_deleted': [],
            'document_published': [],
            'kb_indexed': [],
        }
        
        # Statistics
        self._stats = {
            'total_kbs': 0,
            'total_documents': 0,
            'total_views': 0,
        }

    def create_knowledge_base(self, kb_config: KBConfig) -> bool:
        """Create new knowledge base."""
        with self._lock:
            if kb_config.name in self._kbs:
                return False

            self._kbs[kb_config.name] = kb_config
            self._statistics[kb_config.name] = KBStatistics()
            self._stats['total_kbs'] += 1

            self._trigger_callback('kb_created', kb_name=kb_config.name)
            return True

    def delete_knowledge_base(self, kb_name: str, force: bool = False) -> bool:
        """Delete knowledge base."""
        with self._lock:
            if kb_name not in self._kbs:
                return False

            if not force and len(self._documents[kb_name]) > 0:
                return False

            del self._kbs[kb_name]
            if kb_name in self._documents:
                del self._documents[kb_name]
            if kb_name in self._statistics:
                del self._statistics[kb_name]

            return True

    def add_document(
        self,
        kb_name: str,
        content: str,
        metadata: DocumentMetadata,
    ) -> Optional[str]:
        """Add document to knowledge base."""
        with self._lock:
            if kb_name not in self._kbs:
                return None

            # Check limit
            if len(self._documents[kb_name]) >= self._kbs[kb_name].max_documents:
                return None

            doc = Document(
                doc_id=metadata.doc_id,
                content=content,
                metadata=metadata,
            )

            self._documents[kb_name][metadata.doc_id] = doc

            # Index metadata
            self._index_document_metadata(kb_name, metadata)

            # Update statistics
            self._statistics[kb_name].total_documents += 1
            self._statistics[kb_name].total_content_size_mb += len(content) / (1024 * 1024)
            self._statistics[kb_name].last_updated = time.time()
            self._stats['total_documents'] += 1

            # Create initial version if versioning enabled
            if self._kbs[kb_name].enable_versioning:
                self._create_version(
                    doc_id=metadata.doc_id,
                    content=content,
                    changed_by=metadata.author,
                    change_description="Initial version",
                )

            self._trigger_callback(
                'document_added',
                kb_name=kb_name,
                doc_id=metadata.doc_id,
            )

            return metadata.doc_id

    def update_document(
        self,
        kb_name: str,
        doc_id: str,
        new_content: str,
        updated_by: str,
        change_description: str = "",
    ) -> bool:
        """Update document content."""
        with self._lock:
            if kb_name not in self._documents or doc_id not in self._documents[kb_name]:
                return False

            doc = self._documents[kb_name][doc_id]
            old_content = doc.content
            
            doc.content = new_content
            doc.metadata.updated_at = time.time()
            doc.embeddings_computed = False  # Flag for recomputation
            doc.indexed = False

            # Create version
            if self._kbs[kb_name].enable_versioning:
                self._create_version(
                    doc_id=doc_id,
                    content=new_content,
                    changed_by=updated_by,
                    change_description=change_description,
                )

            self._statistics[kb_name].last_updated = time.time()

            self._trigger_callback(
                'document_updated',
                kb_name=kb_name,
                doc_id=doc_id,
                updated_by=updated_by,
            )

            return True

    def get_document(self, kb_name: str, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        with self._lock:
            if kb_name not in self._documents:
                return None

            doc = self._documents[kb_name].get(doc_id)
            if doc:
                doc.views += 1
                self._statistics[kb_name].total_views += 1
                self._stats['total_views'] += 1

            return doc

    def delete_document(self, kb_name: str, doc_id: str) -> bool:
        """Delete document from knowledge base."""
        with self._lock:
            if kb_name not in self._documents or doc_id not in self._documents[kb_name]:
                return False

            doc = self._documents[kb_name][doc_id]
            
            # Remove from metadata indices
            for tag in doc.metadata.tags:
                self._doc_by_tag[tag].discard(doc_id)

            self._doc_by_category[doc.metadata.category].discard(doc_id)
            self._doc_by_author[doc.metadata.author].discard(doc_id)
            self._doc_by_source[doc.metadata.source].discard(doc_id)

            del self._documents[kb_name][doc_id]
            
            # Update statistics
            self._statistics[kb_name].total_documents -= 1
            self._statistics[kb_name].total_content_size_mb -= len(doc.content) / (1024 * 1024)
            self._stats['total_documents'] -= 1

            self._trigger_callback(
                'document_deleted',
                kb_name=kb_name,
                doc_id=doc_id,
            )

            return True

    def publish_document(self, kb_name: str, doc_id: str) -> bool:
        """Publish document."""
        with self._lock:
            if kb_name not in self._documents or doc_id not in self._documents[kb_name]:
                return False

            doc = self._documents[kb_name][doc_id]
            doc.status = DocumentStatus.PUBLISHED

            self._statistics[kb_name].published_documents += 1

            self._trigger_callback(
                'document_published',
                kb_name=kb_name,
                doc_id=doc_id,
            )

            return True

    def archive_document(self, kb_name: str, doc_id: str) -> bool:
        """Archive document."""
        with self._lock:
            if kb_name not in self._documents or doc_id not in self._documents[kb_name]:
                return False

            doc = self._documents[kb_name][doc_id]
            doc.status = DocumentStatus.ARCHIVED

            return True

    def find_documents(
        self,
        kb_name: str,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        author: Optional[str] = None,
        status: Optional[DocumentStatus] = None,
    ) -> List[Document]:
        """Find documents by criteria."""
        with self._lock:
            if kb_name not in self._documents:
                return []

            docs = list(self._documents[kb_name].values())

            # Filter by status
            if status:
                docs = [d for d in docs if d.status == status]

            # Filter by tags
            if tags:
                docs = [d for d in docs if any(t in d.metadata.tags for t in tags)]

            # Filter by category
            if category:
                docs = [d for d in docs if d.metadata.category == category]

            # Filter by author
            if author:
                docs = [d for d in docs if d.metadata.author == author]

            # Filter by content (mock search)
            if query:
                query_lower = query.lower()
                docs = [
                    d for d in docs
                    if query_lower in d.content.lower() or query_lower in d.metadata.title.lower()
                ]

            return docs

    def get_document_versions(self, doc_id: str) -> List[DocumentVersion]:
        """Get version history for document."""
        with self._lock:
            return list(self._versions.get(doc_id, []))

    def restore_document_version(
        self,
        kb_name: str,
        doc_id: str,
        version_id: str,
        restored_by: str,
    ) -> bool:
        """Restore document to previous version."""
        with self._lock:
            if kb_name not in self._documents or doc_id not in self._documents[kb_name]:
                return False

            versions = self._versions[doc_id]
            version = next((v for v in versions if v.version_id == version_id), None)

            if not version:
                return False

            # Update document with old content
            doc = self._documents[kb_name][doc_id]
            old_content = doc.content
            doc.content = version.content
            doc.metadata.updated_at = time.time()

            # Create new version for restoration
            self._create_version(
                doc_id=doc_id,
                content=version.content,
                changed_by=restored_by,
                change_description=f"Restored to version {version_id}",
            )

            return True

    def rate_document(
        self,
        kb_name: str,
        doc_id: str,
        rating: float,  # -1 to 1
    ) -> bool:
        """Rate document (like/dislike)."""
        with self._lock:
            if kb_name not in self._documents or doc_id not in self._documents[kb_name]:
                return False

            doc = self._documents[kb_name][doc_id]

            if rating > 0:
                doc.likes += 1
            elif rating < 0:
                doc.dislikes += 1

            # Update average rating
            total_ratings = doc.likes + doc.dislikes
            if total_ratings > 0:
                avg_rating = doc.likes / total_ratings
                self._statistics[kb_name].avg_rating = avg_rating

            return True

    def get_kb_statistics(self, kb_name: str) -> Optional[Dict[str, Any]]:
        """Get knowledge base statistics."""
        with self._lock:
            if kb_name not in self._statistics:
                return None

            stats = self._statistics[kb_name]
            return {
                'name': kb_name,
                'total_documents': stats.total_documents,
                'indexed_documents': stats.indexed_documents,
                'published_documents': stats.published_documents,
                'total_content_size_mb': stats.total_content_size_mb,
                'total_views': stats.total_views,
                'avg_rating': stats.avg_rating,
                'last_updated': stats.last_updated,
            }

    def get_all_knowledge_bases(self) -> List[KBConfig]:
        """Get all knowledge bases."""
        with self._lock:
            return list(self._kbs.values())

    def grant_access(
        self,
        user_id: str,
        kb_name: str,
        access_level: AccessLevel,
    ) -> bool:
        """Grant access to knowledge base for user."""
        with self._lock:
            if kb_name not in self._kbs:
                return False

            if user_id not in self._permissions:
                self._permissions[user_id] = {}

            self._permissions[user_id][kb_name] = access_level
            return True

    def has_access(self, user_id: str, kb_name: str) -> bool:
        """Check if user has access to knowledge base."""
        with self._lock:
            if kb_name not in self._kbs:
                return False

            kb_config = self._kbs[kb_name]

            if kb_config.access_level == AccessLevel.PUBLIC:
                return True

            return (
                user_id in self._permissions and
                kb_name in self._permissions[user_id]
            )

    def register_callback(self, event: str, callback: Callable) -> None:
        """Register callback for event."""
        with self._lock:
            if event in self._callbacks:
                self._callbacks[event].append(callback)

    def _index_document_metadata(self, kb_name: str, metadata: DocumentMetadata) -> None:
        """Index document metadata."""
        doc_id = metadata.doc_id

        for tag in metadata.tags:
            self._doc_by_tag[tag].add(doc_id)

        self._doc_by_category[metadata.category].add(doc_id)
        self._doc_by_author[metadata.author].add(doc_id)
        self._doc_by_source[metadata.source].add(doc_id)

    def _create_version(
        self,
        doc_id: str,
        content: str,
        changed_by: str,
        change_description: str,
    ) -> None:
        """Create new document version."""
        version_id = hashlib.sha256(
            f"{doc_id}_{time.time()}".encode()
        ).hexdigest()[:16]

        versions = self._versions[doc_id]
        parent_version = versions[-1] if versions else None

        version = DocumentVersion(
            version_id=version_id,
            doc_id=doc_id,
            content=content,
            changed_by=changed_by,
            change_description=change_description,
            parent_version_id=parent_version.version_id if parent_version else None,
        )

        versions.append(version)

    def _trigger_callback(self, event: str, **kwargs) -> None:
        """Trigger callbacks for event."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(**kwargs)
                except Exception:
                    pass
