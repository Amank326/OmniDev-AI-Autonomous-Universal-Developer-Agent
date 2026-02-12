"""
Multi-Agent Collaboration Routes
=================================

REST API endpoints for agent orchestration, RAG, and team collaboration.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from app.agents.orchestrator import (
    agent_orchestrator, CollaborationMode, AgentRole
)
from app.rag.retrieval import rag_service
from app.rag.knowledge_base import DocumentSource
from app.memory.agent_memory import agent_memory_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/collaboration", tags=["collaboration"])


# ============================================================================
# Request/Response Models
# ============================================================================

class DocumentUpload(BaseModel):
    """Model for uploading documents to knowledge base."""
    title: str
    content: str
    source: str = "file"
    source_url: Optional[str] = None


class QueryRequest(BaseModel):
    """Model for knowledge base queries."""
    query: str
    top_k: int = 5
    include_metadata: bool = True


class AugmentedQueryRequest(BaseModel):
    """Model for augmented query with RAG."""
    query: str
    template: str = "default"
    top_k: int = 5


class CollaborativeTaskRequest(BaseModel):
    """Model for collaborative task execution."""
    description: str
    mode: str = "parallel"  # sequential, parallel, hierarchical, consensus
    team_id: Optional[str] = None
    project_id: Optional[int] = None
    context: Optional[dict] = None


class AgentTeamRequest(BaseModel):
    """Model for creating agent team."""
    team_id: str
    agents: List[dict]  # [{agent_id: str, role: str}, ...]


# ============================================================================
# Agent Management Endpoints
# ============================================================================

@router.get("/agents")
async def get_available_agents():
    """
    Get list of available agents.
    
    Returns:
        List of available agents with capabilities
    """
    try:
        agents = agent_orchestrator.get_available_agents()
        return {
            "status": "success",
            "agents": agents,
            "count": len(agents),
        }
    except Exception as e:
        logger.error(f"Failed to get agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/best")
async def get_best_agent(
    task: str = Query(..., description="Task description"),
    capabilities: Optional[str] = Query(None, description="Comma-separated required capabilities"),
):
    """
    Find best agent for a task.
    
    Query Parameters:
        task: Task description
        capabilities: Required capabilities (comma-separated)
    
    Returns:
        Best agent for the task
    """
    try:
        required_caps = capabilities.split(",") if capabilities else []
        agent_id = agent_orchestrator.get_best_agent_for_task(task, required_caps)
        
        if not agent_id:
            raise HTTPException(status_code=404, detail="No suitable agent found")
        
        agent = agent_orchestrator.available_agents.get(agent_id)
        return {
            "status": "success",
            "agent_id": agent_id,
            "agent_type": type(agent).__name__,
            "name": getattr(agent, "name", agent_id),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get best agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Team Management Endpoints
# ============================================================================

@router.post("/teams")
async def create_team(request: AgentTeamRequest):
    """
    Create an agent team.
    
    Request Body:
        team_id: Unique team identifier
        agents: List of {agent_id, role} objects
    
    Returns:
        Team creation status
    """
    try:
        agents = [(a["agent_id"], AgentRole(a["role"])) for a in request.agents]
        success = agent_orchestrator.create_team(request.team_id, agents)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create team")
        
        return {
            "status": "success",
            "team_id": request.team_id,
            "agents": len(agents),
        }
    except Exception as e:
        logger.error(f"Failed to create team: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}")
async def get_team(team_id: str):
    """
    Get team information.
    
    Path Parameters:
        team_id: Team identifier
    
    Returns:
        Team details with members
    """
    try:
        team = agent_orchestrator.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return {
            "status": "success",
            "team_id": team_id,
            "members": [
                {
                    "agent_id": m.agent_id,
                    "agent_type": m.agent_type,
                    "name": m.name,
                    "role": m.role.value,
                }
                for m in team.values()
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Collaborative Task Execution Endpoints
# ============================================================================

@router.post("/tasks/execute")
async def execute_collaborative_task(
    request: CollaborativeTaskRequest,
    user_id: int = Query(...),
):
    """
    Execute a collaborative task using multiple agents.
    
    Query Parameters:
        user_id: User executing task
    
    Request Body:
        description: Task description
        mode: Collaboration mode (sequential, parallel, hierarchical, consensus)
        team_id: Optional team identifier
        project_id: Optional project identifier
        context: Optional task context
    
    Returns:
        Task execution result with all agent responses
    """
    try:
        import uuid
        task_id = str(uuid.uuid4())
        
        mode = CollaborationMode(request.mode)
        
        result = await agent_orchestrator.execute_collaborative_task(
            task_id=task_id,
            description=request.description,
            user_id=user_id,
            mode=mode,
            team_id=request.team_id,
            project_id=request.project_id,
            context=request.context,
        )
        
        return {
            "status": "success",
            "task_id": task_id,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Failed to execute task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/history")
async def get_collaboration_history(
    user_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get collaboration task history.
    
    Query Parameters:
        user_id: Filter by user (optional)
        limit: Maximum results (1-1000)
    
    Returns:
        List of collaborative tasks
    """
    try:
        history = agent_orchestrator.get_collaboration_history(user_id, limit)
        
        return {
            "status": "success",
            "tasks": history,
            "count": len(history),
        }
    except Exception as e:
        logger.error(f"Failed to get history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Knowledge Base and RAG Endpoints
# ============================================================================

@router.post("/knowledge/documents")
async def add_knowledge_document(request: DocumentUpload):
    """
    Add document to knowledge base.
    
    Request Body:
        title: Document title
        content: Document content
        source: Document source (file, url, code, documentation, wiki)
        source_url: Optional source URL
    
    Returns:
        Document ID
    """
    try:
        source = DocumentSource(request.source)
        doc_id = rag_service.add_document(
            title=request.title,
            content=request.content,
            source=source,
            source_url=request.source_url,
        )
        
        if doc_id < 0:
            raise HTTPException(status_code=400, detail="Failed to add document")
        
        return {
            "status": "success",
            "document_id": doc_id,
            "title": request.title,
        }
    except Exception as e:
        logger.error(f"Failed to add document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/search")
async def search_knowledge_base(request: QueryRequest):
    """
    Search knowledge base.
    
    Request Body:
        query: Search query
        top_k: Number of results (1-100)
        include_metadata: Include document metadata
    
    Returns:
        List of matching documents
    """
    try:
        context = rag_service.retrieve_context(
            query=request.query,
            top_k=min(request.top_k, 100),
        )
        
        return {
            "status": "success",
            "query": request.query,
            "results": context.retrieved_docs,
            "count": len(context.retrieved_docs),
            "context_preview": context.context_text[:500],
        }
    except Exception as e:
        logger.error(f"Failed to search knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/augment-query")
async def augment_query_with_rag(request: AugmentedQueryRequest):
    """
    Augment query with retrieved context (RAG).
    
    Request Body:
        query: Original query
        template: Prompt template (default, code, documentation)
        top_k: Number of documents to retrieve
    
    Returns:
        Augmented prompt with context
    """
    try:
        augmented = rag_service.augment_prompt(
            query=request.query,
            template_name=request.template,
        )
        
        return {
            "status": "success",
            "query": request.query,
            "template": request.template,
            "augmented_prompt": augmented,
        }
    except Exception as e:
        logger.error(f"Failed to augment query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/stats")
async def get_knowledge_base_stats():
    """
    Get knowledge base statistics.
    
    Returns:
        Knowledge base metrics
    """
    try:
        stats = rag_service.get_stats()
        
        return {
            "status": "success",
            "stats": stats,
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Collaboration Memory Endpoints
# ============================================================================

@router.post("/memory/store")
async def store_team_memory(
    team_id: str = Query(...),
    task_id: str = Query(...),
    agent_id: str = Query(...),
    content: str = Query(...),
    message_type: str = Query("contribution"),
):
    """
    Store team collaboration memory.
    
    Query Parameters:
        team_id: Team identifier
        task_id: Task identifier
        agent_id: Agent identifier
        content: Memory content
        message_type: Type (contribution, decision, solution, error)
    
    Returns:
        Storage status
    """
    try:
        success = agent_memory_manager.store_memory(
            team_id=team_id,
            task_id=task_id,
            agent_id=agent_id,
            content=content,
            message_type=message_type,
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to store memory")
        
        return {
            "status": "success",
            "team_id": team_id,
            "task_id": task_id,
        }
    except Exception as e:
        logger.error(f"Failed to store memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/retrieve")
async def retrieve_team_memory(
    team_id: str = Query(...),
    task_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    message_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Retrieve team collaboration memory.
    
    Query Parameters:
        team_id: Team identifier
        task_id: Task identifier (optional)
        agent_id: Agent identifier (optional)
        message_type: Message type (optional)
        limit: Maximum results
    
    Returns:
        List of memory entries
    """
    try:
        entries = agent_memory_manager.retrieve_memory(
            team_id=team_id,
            task_id=task_id,
            agent_id=agent_id,
            message_type=message_type,
            limit=limit,
        )
        
        return {
            "status": "success",
            "team_id": team_id,
            "entries": entries,
            "count": len(entries),
        }
    except Exception as e:
        logger.error(f"Failed to retrieve memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/context")
async def get_team_context(
    team_id: str = Query(...),
    task_id: str = Query(...),
    include_reasoning: bool = Query(False),
):
    """
    Get formatted team context string.
    
    Query Parameters:
        team_id: Team identifier
        task_id: Task identifier
        include_reasoning: Include reasoning in context
    
    Returns:
        Team context string
    """
    try:
        context = agent_memory_manager.get_team_context(
            team_id=team_id,
            task_id=task_id,
            include_reasoning=include_reasoning,
        )
        
        return {
            "status": "success",
            "team_id": team_id,
            "task_id": task_id,
            "context": context,
            "length": len(context),
        }
    except Exception as e:
        logger.error(f"Failed to get context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/stats")
async def get_collaboration_stats():
    """
    Get collaboration system statistics.
    
    Returns:
        System metrics and stats
    """
    try:
        active_tasks = agent_orchestrator.get_active_tasks()
        memory_stats = agent_memory_manager.get_memory_stats()
        kb_stats = rag_service.get_stats()
        
        return {
            "status": "success",
            "active_tasks": len(active_tasks),
            "agents_available": len(agent_orchestrator.available_agents),
            "teams": len(agent_orchestrator.agent_teams),
            "memory_stats": memory_stats,
            "knowledge_base": kb_stats,
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
