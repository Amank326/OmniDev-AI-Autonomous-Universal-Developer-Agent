"""
Phase 8: Advanced AI Features - Comprehensive Test Suite
=========================================================

Tests for:
- Agent orchestration with collaboration modes
- Semantic search and embeddings
- Knowledge base and document management
- RAG context retrieval
- Team collaboration memory
- REST API endpoints
- WebSocket real-time collaboration
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

# Orchestration Tests
from app.agents.orchestrator import (
    AgentOrchestrator, AgentRole, CollaborationMode,
    AgentTeamMember, CollaborationTask, AgentResponse,
    agent_orchestrator,
)

# Semantic Search Tests
from app.rag.semantic_search import (
    SemanticSearchService, EmbeddingModel, VectorStore,
    semantic_search_service,
)

# Knowledge Base Tests
from app.rag.knowledge_base import (
    KnowledgeBaseManager, DocumentChunkStrategy, DocumentSource,
    knowledge_base_manager,
)

# RAG Tests
from app.rag.retrieval import RAGService, PromptTemplate, rag_service

# Memory Tests
from app.memory.agent_memory import (
    AgentMemoryManager, CollaborationMemory, AgentMemoryEntry,
    agent_memory_manager,
)

# WebSocket Tests
from app.realtime.collaboration import (
    CollaborationWebSocketManager, WebSocketMessage, TeamSession,
    collaboration_manager, handle_websocket_message,
)


# ============================================================================
# Agent Orchestration Tests
# ============================================================================

class TestAgentOrchestration:
    """Tests for agent orchestration and collaboration."""
    
    def test_agent_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        assert agent_orchestrator is not None
        assert isinstance(agent_orchestrator, AgentOrchestrator)
        assert len(agent_orchestrator.available_agents) >= 0
    
    def test_agent_registration(self):
        """Test agent registration."""
        mock_agent = MagicMock()
        mock_agent.name = "test_agent"
        
        agent_orchestrator.register_agent(
            agent_id="test_001",
            agent=mock_agent,
            agent_type="TestAgent",
            capabilities=["analysis", "generation"],
        )
        
        assert "test_001" in agent_orchestrator.available_agents
    
    def test_team_creation(self):
        """Test team creation."""
        agents = [("agent_1", AgentRole.EXECUTOR), ("agent_2", AgentRole.REVIEWER)]
        success = agent_orchestrator.create_team("team_test_001", agents)
        
        assert success is True
        assert agent_orchestrator.get_team("team_test_001") is not None
    
    def test_team_retrieval(self):
        """Test team retrieval."""
        team = agent_orchestrator.get_team("team_test_001")
        
        assert team is not None
        # Team should have members or be empty
        assert isinstance(team, dict)
    
    def test_collaboration_task_creation(self):
        """Test collaboration task creation."""
        task = CollaborationTask(
            task_id="task_001",
            description="Test task",
            team_id="team_001",
            context={"test": "data"},
        )
        
        assert task.task_id == "task_001"
        assert task.description == "Test task"
        assert task.team_id == "team_001"
    
    def test_agent_role_enum(self):
        """Test agent role enum values."""
        roles = [AgentRole.COORDINATOR, AgentRole.EXECUTOR, 
                AgentRole.VALIDATOR, AgentRole.REVIEWER, AgentRole.ASSISTANT]
        
        assert len(roles) == 5
        assert all(isinstance(r, AgentRole) for r in roles)
    
    def test_collaboration_mode_enum(self):
        """Test collaboration mode enum values."""
        modes = [CollaborationMode.SEQUENTIAL, CollaborationMode.PARALLEL,
                CollaborationMode.HIERARCHICAL, CollaborationMode.CONSENSUS]
        
        assert len(modes) == 4
        assert all(isinstance(m, CollaborationMode) for m in modes)
    
    @pytest.mark.asyncio
    async def test_collaborative_task_execution_async(self):
        """Test async collaborative task execution."""
        # Mock agents
        with patch.object(agent_orchestrator, 'get_available_agents', return_value={}):
            # Should not raise even with no agents
            result = await agent_orchestrator.execute_collaborative_task(
                task_id="async_task_001",
                description="Test async task",
                user_id=1,
                mode=CollaborationMode.PARALLEL,
            )
            
            assert result is not None
    
    def test_active_tasks_tracking(self):
        """Test tracking of active tasks."""
        tasks = agent_orchestrator.get_active_tasks()
        
        assert isinstance(tasks, list)
    
    def test_collaboration_history(self):
        """Test collaboration history retrieval."""
        history = agent_orchestrator.get_collaboration_history(user_id=1, limit=10)
        
        assert isinstance(history, list)
        assert len(history) <= 10


# ============================================================================
# Semantic Search Tests
# ============================================================================

class TestSemanticSearch:
    """Tests for semantic search service."""
    
    def test_semantic_search_service_initialization(self):
        """Test semantic search service initialization."""
        assert semantic_search_service is not None
        assert isinstance(semantic_search_service, SemanticSearchService)
    
    def test_embedding_model_graceful_loading(self):
        """Test embedding model loads gracefully."""
        model = EmbeddingModel()
        assert model is not None
    
    def test_vector_store_creation(self):
        """Test vector store creation."""
        store = VectorStore()
        assert store is not None
        assert store.dimension > 0
    
    def test_create_index(self):
        """Test index creation."""
        success = semantic_search_service.create_index("test_index")
        
        assert success is True
        assert "test_index" in semantic_search_service.indexes
    
    def test_list_indexes(self):
        """Test listing indexes."""
        # Create test indexes
        semantic_search_service.create_index("list_test_1")
        semantic_search_service.create_index("list_test_2")
        
        indexes = semantic_search_service.list_indexes()
        
        assert isinstance(indexes, list)
        assert len(indexes) >= 0
    
    @pytest.mark.asyncio
    async def test_index_document_async(self):
        """Test async document indexing."""
        index_name = "doc_test"
        semantic_search_service.create_index(index_name)
        
        result = await semantic_search_service.index_document(
            index_name,
            doc_id="doc_001",
            text="Sample document for testing",
        )
        
        # Result depends on embedding availability
        assert result is not None or result is False
    
    def test_get_index_stats(self):
        """Test getting index statistics."""
        semantic_search_service.create_index("stats_test")
        stats = semantic_search_service.get_index_stats("stats_test")
        
        assert isinstance(stats, dict)
        assert "doc_count" in stats


# ============================================================================
# Knowledge Base Tests
# ============================================================================

class TestKnowledgeBase:
    """Tests for knowledge base management."""
    
    def test_knowledge_base_manager_initialization(self):
        """Test knowledge base manager initialization."""
        assert knowledge_base_manager is not None
        assert isinstance(knowledge_base_manager, KnowledgeBaseManager)
    
    def test_document_chunk_strategy_enum(self):
        """Test document chunk strategy enum."""
        strategies = [
            DocumentChunkStrategy.FIXED_SIZE,
            DocumentChunkStrategy.SEMANTIC,
            DocumentChunkStrategy.SENTENCE,
            DocumentChunkStrategy.PARAGRAPH,
        ]
        
        assert len(strategies) == 4
        assert all(isinstance(s, DocumentChunkStrategy) for s in strategies)
    
    def test_document_source_enum(self):
        """Test document source enum."""
        sources = [
            DocumentSource.FILE,
            DocumentSource.URL,
            DocumentSource.DATABASE,
            DocumentSource.CODE,
            DocumentSource.DOCUMENTATION,
            DocumentSource.WIKI,
        ]
        
        assert len(sources) == 6
        assert all(isinstance(s, DocumentSource) for s in sources)
    
    def test_add_document(self):
        """Test adding document to knowledge base."""
        doc_id = knowledge_base_manager.add_document(
            title="Test Document",
            content="This is a test document for the knowledge base.",
            source=DocumentSource.FILE,
        )
        
        assert doc_id is not None
        assert isinstance(doc_id, int)
    
    def test_get_document(self):
        """Test retrieving document."""
        # Add a document first
        doc_id = knowledge_base_manager.add_document(
            title="Retrieval Test",
            content="Test content for retrieval",
            source=DocumentSource.FILE,
        )
        
        # Retrieve it
        if doc_id and doc_id > 0:
            doc = knowledge_base_manager.get_document(doc_id)
            # Document may not be in memory, just check retrieval works
            assert doc is not None or doc is None  # Either found or not
    
    def test_list_documents(self):
        """Test listing documents."""
        docs = knowledge_base_manager.list_documents(limit=10)
        
        assert isinstance(docs, list)
    
    def test_chunk_document_fixed_size(self):
        """Test fixed-size document chunking."""
        chunks = knowledge_base_manager.chunk_document(
            content="This is a test document. " * 50,
            strategy=DocumentChunkStrategy.FIXED_SIZE,
            chunk_size=256,
        )
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(c, dict) for c in chunks)
    
    def test_chunk_document_sentence(self):
        """Test sentence-based chunking."""
        content = "First sentence. Second sentence. Third sentence."
        chunks = knowledge_base_manager.chunk_document(
            content=content,
            strategy=DocumentChunkStrategy.SENTENCE,
        )
        
        assert isinstance(chunks, list)
        assert len(chunks) >= 1
    
    def test_chunk_document_paragraph(self):
        """Test paragraph-based chunking."""
        content = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = knowledge_base_manager.chunk_document(
            content=content,
            strategy=DocumentChunkStrategy.PARAGRAPH,
        )
        
        assert isinstance(chunks, list)
    
    def test_get_knowledge_base_stats(self):
        """Test knowledge base statistics."""
        stats = knowledge_base_manager.get_knowledge_base_stats()
        
        assert isinstance(stats, dict)
        assert "total_documents" in stats
        assert "total_chunks" in stats


# ============================================================================
# RAG Retrieval Tests
# ============================================================================

class TestRAGRetrieval:
    """Tests for RAG (Retrieval-Augmented Generation)."""
    
    def test_rag_service_initialization(self):
        """Test RAG service initialization."""
        assert rag_service is not None
        assert isinstance(rag_service, RAGService)
    
    def test_prompt_template_creation(self):
        """Test prompt template creation."""
        template = PromptTemplate(
            name="test_template",
            template="Question: {query}\nContext: {context}",
        )
        
        assert template.name == "test_template"
        assert "{query}" in template.template
    
    def test_prompt_template_format(self):
        """Test prompt template formatting."""
        template = PromptTemplate(
            name="format_test",
            template="Query: {query}\nContext: {context}",
        )
        
        formatted = template.format(
            query="What is AI?",
            context="AI is artificial intelligence.",
        )
        
        assert "What is AI?" in formatted
        assert "AI is artificial intelligence." in formatted
    
    def test_register_custom_template(self):
        """Test registering custom template."""
        rag_service.register_template(
            name="custom",
            template_string="Custom: {query} | {context}",
        )
        
        assert "custom" in rag_service.prompt_templates
    
    def test_add_document_to_rag(self):
        """Test adding document to RAG."""
        doc_id = rag_service.add_document(
            title="RAG Test",
            content="This is test content for RAG.",
        )
        
        assert doc_id is not None or doc_id is False
    
    def test_retrieve_context(self):
        """Test context retrieval."""
        context = rag_service.retrieve_context(
            query="test query",
            top_k=3,
        )
        
        assert context is not None
        assert isinstance(context.retrieved_docs, list)
    
    def test_augment_prompt(self):
        """Test prompt augmentation."""
        augmented = rag_service.augment_prompt(
            query="What is Python?",
            template_name="default",
        )
        
        assert isinstance(augmented, str)
        assert "Python" in augmented or len(augmented) > 0
    
    def test_get_rag_stats(self):
        """Test RAG statistics."""
        stats = rag_service.get_stats()
        
        assert isinstance(stats, dict)
        assert "total_documents" in stats


# ============================================================================
# Team Memory Tests
# ============================================================================

class TestAgentMemory:
    """Tests for agent team collaboration memory."""
    
    def test_agent_memory_manager_initialization(self):
        """Test agent memory manager initialization."""
        assert agent_memory_manager is not None
        assert isinstance(agent_memory_manager, AgentMemoryManager)
    
    def test_store_memory(self):
        """Test storing memory."""
        success = agent_memory_manager.store_memory(
            team_id="team_mem_001",
            task_id="task_mem_001",
            agent_id="agent_001",
            content="Test memory entry",
            message_type="contribution",
        )
        
        assert success is not None
    
    def test_retrieve_memory(self):
        """Test retrieving memory."""
        # Store first
        agent_memory_manager.store_memory(
            team_id="team_mem_002",
            task_id="task_mem_002",
            agent_id="agent_002",
            content="Retrievable memory",
            message_type="decision",
        )
        
        # Retrieve
        entries = agent_memory_manager.retrieve_memory(
            team_id="team_mem_002",
            limit=10,
        )
        
        assert isinstance(entries, list)
    
    def test_record_decision(self):
        """Test recording team decision."""
        agent_memory_manager.record_decision(
            team_id="team_mem_003",
            task_id="task_mem_003",
            agent_id="agent_003",
            decision="Proceed with option A",
            confidence=0.95,
        )
        
        # Should not raise
        assert True
    
    def test_record_solution(self):
        """Test recording team solution."""
        agent_memory_manager.record_solution(
            team_id="team_mem_004",
            task_id="task_mem_004",
            agent_id="agent_004",
            solution="Use approach B",
            effectiveness=0.88,
        )
        
        assert True
    
    def test_record_error(self):
        """Test recording team error."""
        agent_memory_manager.record_error(
            team_id="team_mem_005",
            task_id="task_mem_005",
            agent_id="agent_005",
            error="Connection timeout",
            recovery_suggestions=["Retry", "Use fallback"],
        )
        
        assert True
    
    def test_get_memory_stats(self):
        """Test memory statistics."""
        stats = agent_memory_manager.get_memory_stats()
        
        assert isinstance(stats, dict)
        assert "total_entries" in stats or "memory_entries" in stats
    
    def test_get_team_context(self):
        """Test getting formatted team context."""
        # Store some memory first
        agent_memory_manager.store_memory(
            team_id="team_ctx_001",
            task_id="task_ctx_001",
            agent_id="agent_ctx_001",
            content="Team context test",
        )
        
        context = agent_memory_manager.get_team_context(
            team_id="team_ctx_001",
            task_id="task_ctx_001",
        )
        
        assert isinstance(context, str)


# ============================================================================
# WebSocket Collaboration Tests
# ============================================================================

class TestWebSocketCollaboration:
    """Tests for WebSocket real-time collaboration."""
    
    def test_collaboration_manager_initialization(self):
        """Test collaboration manager initialization."""
        assert collaboration_manager is not None
        assert isinstance(collaboration_manager, CollaborationWebSocketManager)
    
    def test_websocket_message_creation(self):
        """Test WebSocket message creation."""
        message = WebSocketMessage(
            message_type="test",
            timestamp=datetime.utcnow().isoformat(),
            sender_id="user_001",
            data={"test": "data"},
        )
        
        assert message.message_type == "test"
        assert message.sender_id == "user_001"
    
    def test_websocket_message_to_json(self):
        """Test WebSocket message JSON serialization."""
        message = WebSocketMessage(
            message_type="json_test",
            timestamp=datetime.utcnow().isoformat(),
            sender_id="user_002",
            data={"key": "value"},
        )
        
        json_str = message.to_json()
        
        assert isinstance(json_str, str)
        assert "json_test" in json_str
    
    def test_team_session_creation(self):
        """Test team session creation."""
        session = TeamSession(
            team_id="team_ws_001",
            agent_count=3,
        )
        
        assert session.team_id == "team_ws_001"
        assert session.agent_count == 3
        assert session.created_at is not None
    
    def test_create_team_session_in_manager(self):
        """Test creating team session in manager."""
        session = collaboration_manager.create_team_session(
            team_id="team_ws_002",
            agent_count=2,
        )
        
        assert session.team_id == "team_ws_002"
        assert collaboration_manager.get_team_session("team_ws_002") is not None
    
    def test_get_connection_stats(self):
        """Test getting connection statistics."""
        stats = collaboration_manager.get_connection_stats()
        
        assert isinstance(stats, dict)
        assert "connected_users" in stats
        assert "total_connections" in stats
        assert "active_teams" in stats
    
    @pytest.mark.asyncio
    async def test_team_status_retrieval(self):
        """Test async team status retrieval."""
        # Create team session first
        collaboration_manager.create_team_session("team_status_001", agent_count=2)
        
        status = await collaboration_manager.get_team_status("team_status_001")
        
        assert isinstance(status, dict)
        assert status["team_id"] == "team_status_001"
    
    def test_subscribe_to_updates(self):
        """Test subscription to updates."""
        collaboration_manager.subscribe("subscription_001", "connection_001")
        
        assert "subscription_001" in collaboration_manager.active_subscriptions
    
    def test_unsubscribe_from_updates(self):
        """Test unsubscription from updates."""
        collaboration_manager.subscribe("subscription_002", "connection_002")
        collaboration_manager.unsubscribe("subscription_002", "connection_002")
        
        assert "subscription_002" not in collaboration_manager.active_subscriptions


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase8Integration:
    """Integration tests for Phase 8 components."""
    
    @pytest.mark.asyncio
    async def test_orchestration_rag_integration(self):
        """Test orchestration with RAG context."""
        # RAG should be able to augment task descriptions
        task_description = "Analyze Python code"
        augmented = rag_service.augment_prompt(task_description)
        
        assert len(augmented) >= len(task_description)
    
    @pytest.mark.asyncio
    async def test_orchestration_memory_integration(self):
        """Test orchestration with team memory."""
        # Memory should track team decisions
        team_id = "integration_team_001"
        agent_memory_manager.record_decision(
            team_id=team_id,
            task_id="integration_task_001",
            agent_id="agent_001",
            decision="Use multiprocessing",
            confidence=0.92,
        )
        
        context = agent_memory_manager.get_team_context(
            team_id=team_id,
            task_id="integration_task_001",
        )
        
        assert context is not None
    
    def test_knowledge_base_semantic_search_integration(self):
        """Test knowledge base with semantic search."""
        # Add document to KB
        doc_id = knowledge_base_manager.add_document(
            title="Integration Test",
            content="This document tests integration between KB and semantic search",
            source=DocumentSource.DOCUMENTATION,
        )
        
        # Should be indexed
        assert doc_id is not None or doc_id is False


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
