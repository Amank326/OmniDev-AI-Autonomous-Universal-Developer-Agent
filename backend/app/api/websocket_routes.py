"""
WebSocket Routes for Real-Time Features
Handles live updates, notifications, and collaboration
"""

import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.database.models import User
from app.websockets.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/project/{project_id}")
async def websocket_project_endpoint(
    websocket: WebSocket,
    project_id: str,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time project updates
    
    Connects to project-specific room for:
    - Task updates
    - Agent execution status
    - Team collaboration
    - Live notifications
    """
    # Verify user and project access
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=1008, reason="Unauthorized")
            return

        # TODO: Verify user has access to project
        # from app.database.models import Project
        # project = db.query(Project).filter(
        #     Project.id == project_id,
        #     Project.owner_id == user_id
        # ).first()
        # if not project:
        #     await websocket.close(code=1008, reason="Project not found")
        #     return

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        await websocket.close(code=1008, reason="Unauthorized")
        return

    # Create connection ID
    connection_id = str(uuid.uuid4())
    room_id = f"project:{project_id}"

    try:
        await manager.connect(websocket, room_id, user_id, connection_id)

        # Send welcome message with connection info
        await manager.send_to_connection(
            room_id,
            connection_id,
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "room_id": room_id,
                "user_id": user_id,
                "message": f"Connected to project {project_id}",
                "message_history": manager.get_message_history(room_id, limit=20),
            },
        )

        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_json()

            # Handle different message types
            if data.get("type") == "message":
                await manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "message",
                        "user_id": user_id,
                        "content": data.get("content", ""),
                        "room_id": room_id,
                    },
                )

            elif data.get("type") == "task_update":
                await manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "task_update",
                        "task_id": data.get("task_id"),
                        "status": data.get("status"),
                        "updated_by": user_id,
                        "room_id": room_id,
                    },
                )

            elif data.get("type") == "agent_status":
                await manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "agent_status",
                        "agent_id": data.get("agent_id"),
                        "status": data.get("status"),
                        "progress": data.get("progress", 0),
                        "updated_by": user_id,
                        "room_id": room_id,
                    },
                )

            elif data.get("type") == "ping":
                await manager.send_to_connection(
                    room_id,
                    connection_id,
                    {"type": "pong", "timestamp": data.get("timestamp")},
                )

            else:
                logger.warning(f"Unknown message type: {data.get('type')}")

    except WebSocketDisconnect:
        manager.disconnect(room_id, connection_id)
        
        # Broadcast user left message
        await manager.broadcast_to_room(
            room_id,
            {
                "type": "user_left",
                "user_id": user_id,
                "room_id": room_id,
                "active_count": manager.get_room_user_count(room_id),
            },
        )

    except Exception as e:
        logger.error(f"WebSocket error in project {project_id}: {e}")
        manager.disconnect(room_id, connection_id)


@router.websocket("/agent/{agent_id}")
async def websocket_agent_endpoint(
    websocket: WebSocket,
    agent_id: str,
    user_id: str = Query(...),
):
    """
    WebSocket endpoint for real-time agent execution updates
    
    Streams:
    - Agent execution progress
    - Status changes
    - Output logs
    - Completion notifications
    """
    connection_id = str(uuid.uuid4())
    room_id = f"agent:{agent_id}"

    try:
        await manager.connect(websocket, room_id, user_id, connection_id)

        # Send connection established message
        await manager.send_to_connection(
            room_id,
            connection_id,
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "agent_id": agent_id,
                "message": f"Connected to agent {agent_id}",
            },
        )

        while True:
            data = await websocket.receive_json()

            if data.get("type") == "execution_update":
                await manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "execution_update",
                        "agent_id": agent_id,
                        "execution_id": data.get("execution_id"),
                        "status": data.get("status"),
                        "progress": data.get("progress"),
                        "output": data.get("output"),
                        "updated_by": user_id,
                    },
                )

            elif data.get("type") == "execution_complete":
                await manager.broadcast_to_room(
                    room_id,
                    {
                        "type": "execution_complete",
                        "agent_id": agent_id,
                        "execution_id": data.get("execution_id"),
                        "result": data.get("result"),
                        "duration_ms": data.get("duration_ms"),
                        "updated_by": user_id,
                    },
                )

            elif data.get("type") == "ping":
                await manager.send_to_connection(
                    room_id,
                    connection_id,
                    {"type": "pong"},
                )

    except WebSocketDisconnect:
        manager.disconnect(room_id, connection_id)
    except Exception as e:
        logger.error(f"WebSocket error in agent {agent_id}: {e}")
        manager.disconnect(room_id, connection_id)


@router.websocket("/notifications")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    user_id: str = Query(...),
):
    """
    WebSocket endpoint for user-specific notifications
    
    Sends:
    - Task notifications
    - Agent completion alerts
    - Team invitations
    - System announcements
    """
    connection_id = str(uuid.uuid4())
    room_id = f"notifications:{user_id}"

    try:
        await manager.connect(websocket, room_id, user_id, connection_id)

        # Send initial message
        await manager.send_to_connection(
            room_id,
            connection_id,
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "user_id": user_id,
                "message": "Connected to notifications",
            },
        )

        while True:
            data = await websocket.receive_json()

            if data.get("type") == "mark_read":
                # Handle mark as read
                await manager.send_to_connection(
                    room_id,
                    connection_id,
                    {
                        "type": "notification_read",
                        "notification_id": data.get("notification_id"),
                    },
                )

            elif data.get("type") == "ping":
                await manager.send_to_connection(
                    room_id,
                    connection_id,
                    {"type": "pong"},
                )

    except WebSocketDisconnect:
        manager.disconnect(room_id, connection_id)
    except Exception as e:
        logger.error(f"WebSocket error in notifications for user {user_id}: {e}")
        manager.disconnect(room_id, connection_id)


@router.get("/stats")
async def get_websocket_stats():
    """
    Get real-time WebSocket connection statistics
    
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
    return manager.get_stats()


@router.post("/broadcast/global")
async def broadcast_message_global(message: dict):
    """
    Broadcast a message to all connected WebSocket clients
    
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
    stats = manager.get_stats()
    total_connections = stats["total_connections"]

    # Broadcast to all rooms
    await manager.broadcast_to_all_rooms(message)

    return {
        "status": "success",
        "message_sent": True,
        "connections_notified": total_connections,
        "rooms": len(stats["rooms"]),
    }
