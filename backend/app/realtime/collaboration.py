"""
Real-time Collaboration WebSocket Service
===========================================

WebSocket handlers for real-time multi-agent collaboration,
team communication, and task updates.
"""

import logging
import json
import asyncio
from typing import Dict, Set, Optional, List
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, asdict

from app.agents.orchestrator import agent_orchestrator, CollaborationMode
from app.rag.retrieval import rag_service
from app.memory.agent_memory import agent_memory_manager

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    message_type: str  # agent_response, task_update, team_status, query, chat
    timestamp: str
    sender_id: str
    data: dict
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class TeamSession:
    """Active team collaboration session."""
    team_id: str
    connections: Set[str] = None  # WebSocket connection IDs
    active_task_id: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    agent_count: int = 0
    
    def __post_init__(self):
        if self.connections is None:
            self.connections = set()
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow().isoformat()


# ============================================================================
# Collaboration Manager
# ============================================================================

class CollaborationWebSocketManager:
    """Manages WebSocket connections for real-time collaboration."""
    
    def __init__(self):
        self.team_sessions: Dict[str, TeamSession] = {}
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        self.active_subscriptions: Dict[str, Set[str]] = {}  # subscription_id -> connection_ids
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
    # ========================================================================
    # Connection Management
    # ========================================================================
    
    async def connect_user(self, user_id: int, websocket: WebSocket):
        """
        Register user connection.
        
        Args:
            user_id: User identifier
            websocket: WebSocket connection
        """
        await websocket.accept()
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        
        self.user_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.user_connections[user_id])}")
    
    def disconnect_user(self, user_id: int, websocket: WebSocket):
        """
        Unregister user connection.
        
        Args:
            user_id: User identifier
            websocket: WebSocket connection
        """
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        logger.info(f"User {user_id} disconnected")
    
    # ========================================================================
    # Team Session Management
    # ========================================================================
    
    def create_team_session(self, team_id: str, agent_count: int = 0) -> TeamSession:
        """
        Create new team collaboration session.
        
        Args:
            team_id: Team identifier
            agent_count: Number of agents in team
        
        Returns:
            TeamSession instance
        """
        session = TeamSession(
            team_id=team_id,
            agent_count=agent_count,
        )
        self.team_sessions[team_id] = session
        logger.info(f"Created team session: {team_id}")
        return session
    
    def get_team_session(self, team_id: str) -> Optional[TeamSession]:
        """Get team session by ID."""
        return self.team_sessions.get(team_id)
    
    async def update_team_session(self, team_id: str, **kwargs):
        """Update team session."""
        if team_id in self.team_sessions:
            session = self.team_sessions[team_id]
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.updated_at = datetime.utcnow().isoformat()
    
    # ========================================================================
    # Message Broadcasting
    # ========================================================================
    
    async def broadcast_to_user(
        self,
        user_id: int,
        message: WebSocketMessage,
    ):
        """
        Broadcast message to all connections of a user.
        
        Args:
            user_id: User identifier
            message: Message to broadcast
        """
        if user_id not in self.user_connections:
            return
        
        disconnected = set()
        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_text(message.to_json())
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                disconnected.add(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            self.user_connections[user_id].discard(websocket)
    
    async def broadcast_to_team(
        self,
        team_id: str,
        message: WebSocketMessage,
    ):
        """
        Broadcast message to all connected team members.
        
        Args:
            team_id: Team identifier
            message: Message to broadcast
        """
        session = self.get_team_session(team_id)
        if not session:
            return
        
        # In practice, would maintain connections per team
        # For now, broadcast to all connected users
        timestamp = datetime.utcnow().isoformat()
        
        for user_connections in self.user_connections.values():
            disconnected = set()
            for websocket in user_connections:
                try:
                    await websocket.send_text(message.to_json())
                except Exception as e:
                    logger.error(f"Error broadcasting to team: {str(e)}")
                    disconnected.add(websocket)
            
            for websocket in disconnected:
                user_connections.discard(websocket)
    
    # ========================================================================
    # Subscription Management
    # ========================================================================
    
    def subscribe(self, subscription_id: str, connection_id: str):
        """Subscribe connection to updates."""
        if subscription_id not in self.active_subscriptions:
            self.active_subscriptions[subscription_id] = set()
        self.active_subscriptions[subscription_id].add(connection_id)
    
    def unsubscribe(self, subscription_id: str, connection_id: str):
        """Unsubscribe connection from updates."""
        if subscription_id in self.active_subscriptions:
            self.active_subscriptions[subscription_id].discard(connection_id)
            if not self.active_subscriptions[subscription_id]:
                del self.active_subscriptions[subscription_id]
    
    # ========================================================================
    # Message Processing
    # ========================================================================
    
    async def handle_agent_query(
        self,
        user_id: int,
        query: str,
        team_id: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> str:
        """
        Handle agent query and broadcast response.
        
        Args:
            user_id: User executing query
            query: Query text
            team_id: Optional team identifier
            context: Optional context
        
        Returns:
            Task ID
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        # Retrieve context with RAG
        rag_context = rag_service.retrieve_context(query, top_k=5)
        augmented_query = rag_service.augment_prompt(query)
        
        # Send query received message
        message = WebSocketMessage(
            message_type="query_received",
            timestamp=datetime.utcnow().isoformat(),
            sender_id="system",
            data={
                "task_id": task_id,
                "query": query,
                "retrieved_docs": len(rag_context.retrieved_docs),
            },
        )
        await self.broadcast_to_user(user_id, message)
        
        # Execute collaborative task if team provided
        if team_id:
            try:
                result = await agent_orchestrator.execute_collaborative_task(
                    task_id=task_id,
                    description=query,
                    user_id=user_id,
                    team_id=team_id,
                    context=context,
                )
                
                # Broadcast task result
                result_message = WebSocketMessage(
                    message_type="task_complete",
                    timestamp=datetime.utcnow().isoformat(),
                    sender_id="system",
                    data={
                        "task_id": task_id,
                        "result": result,
                        "duration_ms": 0,
                    },
                )
                await self.broadcast_to_team(team_id, result_message)
                
            except Exception as e:
                logger.error(f"Task execution failed: {str(e)}")
                error_message = WebSocketMessage(
                    message_type="error",
                    timestamp=datetime.utcnow().isoformat(),
                    sender_id="system",
                    data={
                        "task_id": task_id,
                        "error": str(e),
                    },
                )
                await self.broadcast_to_user(user_id, error_message)
        
        return task_id
    
    async def handle_team_message(
        self,
        team_id: str,
        user_id: int,
        message: str,
        message_type: str = "chat",
    ):
        """
        Handle team message and broadcast.
        
        Args:
            team_id: Team identifier
            user_id: User identifier
            message: Message text
            message_type: Type of message
        """
        # Store in team memory
        agent_memory_manager.store_memory(
            team_id=team_id,
            task_id=None,
            agent_id=f"user_{user_id}",
            content=message,
            message_type=message_type,
        )
        
        # Broadcast to team
        ws_message = WebSocketMessage(
            message_type=message_type,
            timestamp=datetime.utcnow().isoformat(),
            sender_id=str(user_id),
            data={
                "team_id": team_id,
                "message": message,
                "type": message_type,
            },
        )
        await self.broadcast_to_team(team_id, ws_message)
    
    # ========================================================================
    # Status and Statistics
    # ========================================================================
    
    async def get_team_status(self, team_id: str) -> dict:
        """
        Get current team status.
        
        Args:
            team_id: Team identifier
        
        Returns:
            Team status dictionary
        """
        session = self.get_team_session(team_id)
        if not session:
            return {"status": "not_found"}
        
        team = agent_orchestrator.get_team(team_id)
        
        return {
            "team_id": team_id,
            "status": "active",
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "active_task": session.active_task_id,
            "agent_count": len(team) if team else session.agent_count,
            "members": [
                {
                    "agent_id": m.agent_id,
                    "name": m.name,
                    "role": m.role.value,
                }
                for m in team.values()
            ] if team else [],
        }
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics."""
        total_users = len(self.user_connections)
        total_connections = sum(
            len(conns) for conns in self.user_connections.values()
        )
        
        return {
            "connected_users": total_users,
            "total_connections": total_connections,
            "active_teams": len(self.team_sessions),
            "active_subscriptions": len(self.active_subscriptions),
        }


# ============================================================================
# Global Instance
# ============================================================================

collaboration_manager = CollaborationWebSocketManager()


# ============================================================================
# WebSocket Event Handlers
# ============================================================================

async def handle_websocket_message(
    websocket: WebSocket,
    user_id: int,
    raw_message: str,
):
    """
    Process incoming WebSocket message.
    
    Args:
        websocket: WebSocket connection
        user_id: User identifier
        raw_message: Raw message string
    """
    try:
        data = json.loads(raw_message)
        message_type = data.get("type", "unknown")
        
        if message_type == "query":
            # Handle agent query
            query = data.get("query")
            team_id = data.get("team_id")
            context = data.get("context")
            
            await collaboration_manager.handle_agent_query(
                user_id=user_id,
                query=query,
                team_id=team_id,
                context=context,
            )
        
        elif message_type == "chat":
            # Handle team chat message
            team_id = data.get("team_id")
            message = data.get("message")
            
            await collaboration_manager.handle_team_message(
                team_id=team_id,
                user_id=user_id,
                message=message,
                message_type="chat",
            )
        
        elif message_type == "subscribe":
            # Subscribe to updates
            subscription_id = data.get("subscription_id")
            collaboration_manager.subscribe(subscription_id, str(user_id))
        
        elif message_type == "unsubscribe":
            # Unsubscribe from updates
            subscription_id = data.get("subscription_id")
            collaboration_manager.unsubscribe(subscription_id, str(user_id))
        
        elif message_type == "get_status":
            # Get team status
            team_id = data.get("team_id")
            status = await collaboration_manager.get_team_status(team_id)
            
            response = WebSocketMessage(
                message_type="status",
                timestamp=datetime.utcnow().isoformat(),
                sender_id="system",
                data=status,
            )
            await websocket.send_text(response.to_json())
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON message: {raw_message}")
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {str(e)}")
