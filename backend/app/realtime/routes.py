"""
WebSocket Routes for Real-time Updates

Provides WebSocket endpoints for real-time project and task updates.

Routes:
    /ws/projects/{project_id} - Subscribe to project updates
    /ws/tasks/{task_id} - Subscribe to task updates
    /ws/user/{user_id} - Subscribe to user-specific updates

Features:
    - Token-based authentication via URL parameter
    - Multiple room subscriptions
    - Graceful disconnection handling
    - Message type routing
    - Broadcast capabilities
"""

import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from app.realtime.connection_manager import manager
from app.auth.utils import get_user_from_token
from app.database.services import UserService
from app.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/ws",
    tags=["websocket"]
)


async def authenticate_websocket_token(token: str) -> Optional[int]:
    """
    Authenticate a WebSocket connection using JWT token.
    
    Args:
        token: JWT token from query parameter
    
    Returns:
        User ID if authenticated, None otherwise
    """
    try:
        user_id = get_user_from_token(token)
        if user_id:
            # Verify user exists and is active
            db = SessionLocal()
            try:
                user_service = UserService(db)
                user = user_service.get_user_by_id(user_id)
                if user and user.is_active:
                    return user_id
            finally:
                db.close()
    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}")
    
    return None


@router.websocket("/projects/{project_id}")
async def websocket_project_endpoint(
    websocket: WebSocket,
    project_id: int,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time project updates.
    
    Clients can subscribe to project-specific updates (tasks, status changes, etc.).
    
    Query Parameters:
        token (str): JWT authentication token
    
    Message Types (Received):
        - {"type": "ping"} - Keep-alive ping
        - {"type": "status_update", "status": "active"} - Project status updates
        - {"type": "subscribe", "sub_rooms": ["task:123", "task:456"]} - Subscribe to additional rooms
    
    Message Types (Sent):
        - {"type": "task_created", "task_id": int, "title": str} - Task created in project
        - {"type": "task_updated", "task_id": int, "changes": dict} - Task updated
        - {"type": "task_completed", "task_id": int, "timestamp": str} - Task completed
        - {"type": "project_updated", "changes": dict} - Project updated
    
    Example (Client):
        const ws = new WebSocket(`ws://localhost:8000/api/ws/projects/123?token=eyJ...`);
        
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            console.log('Received:', message);
        };
        
        ws.send(JSON.stringify({type: 'ping'}));
    """
    user_id = await authenticate_websocket_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(f"WebSocket authentication failed for project:{project_id}")
        return
    
    room = f"project:{project_id}"
    await manager.connect(websocket, room=room, user_id=user_id)
    
    try:
        logger.info(f"User {user_id} connected to project {project_id} updates")
        
        # Send welcome message
        await manager.send_to_connection(
            websocket,
            {
                "type": "connected",
                "room": room,
                "user_id": user_id,
                "message": f"Connected to project {project_id} updates"
            }
        )
        
        while True:
            data = await websocket.receive_json()
            
            message_type = data.get("type", "unknown")
            
            if message_type == "ping":
                # Keep-alive response
                await manager.send_to_connection(websocket, {"type": "pong"})
            
            elif message_type == "subscribe":
                # Subscribe to additional rooms
                sub_rooms = data.get("sub_rooms", [])
                for sub_room in sub_rooms:
                    if isinstance(sub_room, str):
                        logger.debug(f"User {user_id} subscribing to {sub_room}")
            
            elif message_type == "status_update":
                # Broadcast project status update
                new_status = data.get("status")
                await manager.broadcast_to_room(
                    room,
                    {
                        "type": "project_status_changed",
                        "project_id": project_id,
                        "new_status": new_status,
                        "changed_by": user_id
                    },
                    exclude_user=user_id
                )
            
            else:
                logger.debug(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        logger.info(f"User {user_id} disconnected from project {project_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for project {project_id}: {str(e)}")
        manager.disconnect(websocket, room)


@router.websocket("/tasks/{task_id}")
async def websocket_task_endpoint(
    websocket: WebSocket,
    task_id: int,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time task updates.
    
    Clients can subscribe to task-specific updates (comments, status, progress).
    
    Query Parameters:
        token (str): JWT authentication token
    
    Message Types (Received):
        - {"type": "ping"} - Keep-alive ping
        - {"type": "comment", "comment": "str"} - Add comment to task
        - {"type": "progress", "progress": int} - Update task progress (0-100)
        - {"type": "assign", "assigned_to": int} - Assign task to user
    
    Message Types (Sent):
        - {"type": "comment_added", "comment_id": int, "author_id": int, "text": str}
        - {"type": "progress_updated", "task_id": int, "progress": int}
        - {"type": "task_assigned", "task_id": int, "assigned_to": int}
        - {"type": "task_completed", "task_id": int, "completed_at": str}
    """
    user_id = await authenticate_websocket_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    room = f"task:{task_id}"
    await manager.connect(websocket, room=room, user_id=user_id)
    
    try:
        logger.info(f"User {user_id} connected to task {task_id} updates")
        
        await manager.send_to_connection(
            websocket,
            {
                "type": "connected",
                "room": room,
                "task_id": task_id,
                "message": f"Connected to task {task_id} updates"
            }
        )
        
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "unknown")
            
            if message_type == "ping":
                await manager.send_to_connection(websocket, {"type": "pong"})
            
            elif message_type == "progress":
                progress = data.get("progress", 0)
                await manager.broadcast_to_room(
                    room,
                    {
                        "type": "progress_updated",
                        "task_id": task_id,
                        "progress": progress,
                        "updated_by": user_id
                    },
                    exclude_user=user_id
                )
            
            elif message_type == "comment":
                comment_text = data.get("comment")
                await manager.broadcast_to_room(
                    room,
                    {
                        "type": "comment_added",
                        "task_id": task_id,
                        "author_id": user_id,
                        "text": comment_text
                    }
                )
            
            elif message_type == "assign":
                assigned_to = data.get("assigned_to")
                await manager.broadcast_to_room(
                    room,
                    {
                        "type": "task_assigned",
                        "task_id": task_id,
                        "assigned_to": assigned_to,
                        "assigned_by": user_id
                    }
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
        logger.info(f"User {user_id} disconnected from task {task_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {str(e)}")
        manager.disconnect(websocket, room)


@router.get("/stats")
async def get_websocket_stats():
    """
    Get real-time WebSocket connection statistics.
    
    Returns:
        Dict with total connections, active rooms, and detailed room statistics
    
    Example Response:
        {
            "total_connections": 42,
            "total_rooms": 5,
            "rooms": {
                "project:1": {
                    "connections": 10,
                    "users": [1, 2, 3, 4, 5],
                    "user_count": 5
                }
            }
        }
    """
    return manager.get_all_stats()


@router.post("/broadcast/global")
async def broadcast_message_global(message: dict):
    """
    Broadcast a message to all connected WebSocket clients.
    
    Warning: Admin endpoint - requires proper authentication in production
    
    Request Body:
        {
            "type": "system_notification",
            "content": "str",
            "severity": "info|warning|error" (optional)
        }
    
    Returns:
        Number of messages sent
    """
    sent_count = await manager.broadcast_global(message)
    return {
        "success": True,
        "message": "Broadcast sent",
        "sent_count": sent_count
    }
