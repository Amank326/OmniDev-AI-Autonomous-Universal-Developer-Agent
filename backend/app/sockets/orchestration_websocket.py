"""
Orchestration WebSocket Handler for OmniDev AI
Real-time updates for agent orchestration and task management
"""

from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from datetime import datetime
from app.services.task_queue_service import TaskQueueService, TaskStatus
from app.services.agent_coordinator_service import AgentCoordinatorService, AgentStatus
from app.services.dependency_resolver_service import DependencyResolverService

# Services (should be injected)
task_queue_service = TaskQueueService()
agent_coordinator_service = AgentCoordinatorService()
dependency_resolver_service = DependencyResolverService()

# Connected clients tracking
connected_clients = {}  # user_id -> client_info


def init_orchestration_websocket(socketio: SocketIO):
    """Initialize WebSocket handlers"""

    # ==================== CONNECTION EVENTS ====================

    @socketio.on("connect", namespace="/orchestration")
    def handle_connect():
        """Handle WebSocket connection"""
        user_id = request.args.get("user_id", "anonymous")
        
        connected_clients[user_id] = {
            "sid": request.sid,
            "connected_at": datetime.utcnow(),
            "subscribed_queues": [],
        }

        emit("connection_established", {
            "status": "connected",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

    @socketio.on("disconnect", namespace="/orchestration")
    def handle_disconnect():
        """Handle WebSocket disconnection"""
        user_id = None
        for uid, client in connected_clients.items():
            if client["sid"] == request.sid:
                user_id = uid
                del connected_clients[uid]
                break

        if user_id:
            emit("user_disconnected", {"user_id": user_id}, broadcast=True)

    # ==================== TASK EVENTS ====================

    @socketio.on("task_created", namespace="/orchestration")
    def on_task_created(data):
        """Broadcast task creation"""
        task_id = data.get("task_id")
        workspace_id = data.get("workspace_id", "default")

        emit("task_event", {
            "event": "task_created",
            "task_id": task_id,
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat(),
        }, broadcast=True, to=f"workspace:{workspace_id}")

    @socketio.on("task_status_changed", namespace="/orchestration")
    def on_task_status_changed(data):
        """Broadcast task status change"""
        task_id = data.get("task_id")
        old_status = data.get("old_status")
        new_status = data.get("new_status")
        workspace_id = data.get("workspace_id", "default")

        task = task_queue_service.get_task(task_id)
        if task:
            emit("task_event", {
                "event": "task_status_changed",
                "task_id": task_id,
                "old_status": old_status,
                "new_status": new_status,
                "timestamp": datetime.utcnow().isoformat(),
                "task_info": {
                    "name": task.name,
                    "assigned_agent": task.assigned_agent,
                    "progress": data.get("progress", 0),
                }
            }, broadcast=True, to=f"workspace:{workspace_id}")

    @socketio.on("subscribe_to_task", namespace="/orchestration")
    def on_subscribe_to_task(data):
        """Subscribe to task updates"""
        task_id = data.get("task_id")
        user_id = data.get("user_id")

        room = f"task:{task_id}"
        join_room(room)

        emit("subscription_confirmed", {
            "type": "task",
            "task_id": task_id,
        })

    @socketio.on("unsubscribe_from_task", namespace="/orchestration")
    def on_unsubscribe_from_task(data):
        """Unsubscribe from task updates"""
        task_id = data.get("task_id")

        room = f"task:{task_id}"
        leave_room(room)

        emit("unsubscribed", {
            "type": "task",
            "task_id": task_id,
        })

    # ==================== QUEUE EVENTS ====================

    @socketio.on("subscribe_to_queue", namespace="/orchestration")
    def on_subscribe_to_queue(data):
        """Subscribe to agent queue updates"""
        agent_id = data.get("agent_id")
        user_id = data.get("user_id")

        room = f"queue:{agent_id}"
        join_room(room)

        # Send current queue state
        queue = task_queue_service.get_agent_queue(agent_id)
        emit("queue_state", {
            "agent_id": agent_id,
            "queue_size": len(queue),
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status.value,
                    "priority": t.priority.value,
                }
                for t in queue
            ]
        })

        emit("subscription_confirmed", {
            "type": "queue",
            "agent_id": agent_id,
        })

    @socketio.on("unsubscribe_from_queue", namespace="/orchestration")
    def on_unsubscribe_from_queue(data):
        """Unsubscribe from queue updates"""
        agent_id = data.get("agent_id")

        room = f"queue:{agent_id}"
        leave_room(room)

        emit("unsubscribed", {
            "type": "queue",
            "agent_id": agent_id,
        })

    @socketio.on("queue_updated", namespace="/orchestration")
    def on_queue_updated(data):
        """Broadcast queue update"""
        agent_id = data.get("agent_id")

        queue = task_queue_service.get_agent_queue(agent_id)
        emit("queue_event", {
            "agent_id": agent_id,
            "queue_size": len(queue),
            "event": data.get("event"),
            "timestamp": datetime.utcnow().isoformat(),
        }, broadcast=True, to=f"queue:{agent_id}")

    # ==================== AGENT EVENTS ====================

    @socketio.on("agent_status_changed", namespace="/orchestration")
    def on_agent_status_changed(data):
        """Broadcast agent status change"""
        agent_id = data.get("agent_id")
        old_status = data.get("old_status")
        new_status = data.get("new_status")

        emit("agent_event", {
            "event": "status_changed",
            "agent_id": agent_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.utcnow().isoformat(),
        }, broadcast=True, to=f"agent:{agent_id}")

    @socketio.on("get_agent_status", namespace="/orchestration")
    def on_get_agent_status(data):
        """Get current agent status"""
        agent_id = data.get("agent_id")

        stats = agent_coordinator_service.get_agent_stats(agent_id)
        if stats:
            emit("agent_status", {
                "agent_id": agent_id,
                "status": stats["status"],
                "load_percent": stats["load_percent"],
                "current_tasks": stats["current_tasks"],
                "memory_available_mb": stats["memory_available_mb"],
            })
        else:
            emit("error", {"message": "Agent not found"})

    @socketio.on("subscribe_to_agent", namespace="/orchestration")
    def on_subscribe_to_agent(data):
        """Subscribe to agent updates"""
        agent_id = data.get("agent_id")

        room = f"agent:{agent_id}"
        join_room(room)

        # Send current state
        stats = agent_coordinator_service.get_agent_stats(agent_id)
        if stats:
            emit("agent_state", {
                "agent_id": agent_id,
                "status": stats["status"],
                "load_percent": stats["load_percent"],
                "current_tasks": stats["current_tasks"],
            })

        emit("subscription_confirmed", {
            "type": "agent",
            "agent_id": agent_id,
        })

    @socketio.on("unsubscribe_from_agent", namespace="/orchestration")
    def on_unsubscribe_from_agent(data):
        """Unsubscribe from agent updates"""
        agent_id = data.get("agent_id")

        room = f"agent:{agent_id}"
        leave_room(room)

        emit("unsubscribed", {
            "type": "agent",
            "agent_id": agent_id,
        })

    # ==================== WORKSPACE EVENTS ====================

    @socketio.on("join_workspace", namespace="/orchestration")
    def on_join_workspace(data):
        """Join workspace room for broadcasts"""
        workspace_id = data.get("workspace_id", "default")
        user_id = data.get("user_id")

        room = f"workspace:{workspace_id}"
        join_room(room)

        emit("workspace_joined", {
            "workspace_id": workspace_id,
            "user_id": user_id,
        }, broadcast=True, to=room)

    @socketio.on("leave_workspace", namespace="/orchestration")
    def on_leave_workspace(data):
        """Leave workspace room"""
        workspace_id = data.get("workspace_id", "default")

        room = f"workspace:{workspace_id}"
        leave_room(room)

        emit("workspace_left", {
            "workspace_id": workspace_id,
        }, broadcast=True, to=room)

    # ==================== COLLABORATION EVENTS ====================

    @socketio.on("collaboration_created", namespace="/orchestration")
    def on_collaboration_created(data):
        """Broadcast collaboration creation"""
        collab_id = data.get("collab_id")
        workspace_id = data.get("workspace_id", "default")

        emit("collaboration_event", {
            "event": "created",
            "collab_id": collab_id,
            "timestamp": datetime.utcnow().isoformat(),
        }, broadcast=True, to=f"workspace:{workspace_id}")

    @socketio.on("collaboration_status_changed", namespace="/orchestration")
    def on_collaboration_status_changed(data):
        """Broadcast collaboration status change"""
        collab_id = data.get("collab_id")
        old_status = data.get("old_status")
        new_status = data.get("new_status")
        workspace_id = data.get("workspace_id", "default")

        emit("collaboration_event", {
            "event": "status_changed",
            "collab_id": collab_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.utcnow().isoformat(),
        }, broadcast=True, to=f"workspace:{workspace_id}")

    @socketio.on("subscribe_to_collaboration", namespace="/orchestration")
    def on_subscribe_to_collaboration(data):
        """Subscribe to collaboration updates"""
        collab_id = data.get("collab_id")

        room = f"collab:{collab_id}"
        join_room(room)

        collab = agent_coordinator_service.get_collaboration(collab_id)
        if collab:
            emit("collaboration_state", {
                "collab_id": collab_id,
                "status": collab.status,
                "agent_count": len(collab.agent_ids),
            })

        emit("subscription_confirmed", {
            "type": "collaboration",
            "collab_id": collab_id,
        })

    # ==================== MONITORING EVENTS ====================

    @socketio.on("heartbeat", namespace="/orchestration")
    def handle_heartbeat():
        """Respond to heartbeat for connection health"""
        emit("heartbeat_ack", {
            "timestamp": datetime.utcnow().isoformat(),
        })

    @socketio.on("request_system_stats", namespace="/orchestration")
    def on_request_system_stats(data):
        """Get current system statistics"""
        workspace_id = data.get("workspace_id", "default")

        queue_stats = task_queue_service.get_queue_stats()
        system_health = agent_coordinator_service.get_system_health()

        emit("system_stats", {
            "workspace_id": workspace_id,
            "queue": queue_stats,
            "system": system_health,
            "timestamp": datetime.utcnow().isoformat(),
        })

    @socketio.on("get_connections", namespace="/orchestration")
    def on_get_connections(data):
        """Get active connections for workspace"""
        workspace_id = data.get("workspace_id", "default")

        emit("connections", {
            "workspace_id": workspace_id,
            "total_connected": len(connected_clients),
            "connections": [
                {
                    "user_id": uid,
                    "connected_at": client["connected_at"].isoformat(),
                }
                for uid, client in connected_clients.items()
            ],
        })

    @socketio.on("list_subscriptions", namespace="/orchestration")
    def on_list_subscriptions(data):
        """List all active subscriptions"""
        user_id = data.get("user_id")

        # Note: This is a simplified implementation
        # In production, track subscriptions per user
        emit("subscriptions_list", {
            "user_id": user_id,
            "subscriptions": [],
        })

    # ==================== DEPENDENCY EVENTS ====================

    @socketio.on("request_execution_plan", namespace="/orchestration")
    def on_request_execution_plan(data):
        """Request optimized execution plan"""
        workspace_id = data.get("workspace_id", "default")

        plan = dependency_resolver_service.optimize_execution_plan(workspace_id)

        emit("execution_plan", {
            "workspace_id": workspace_id,
            "plan": plan,
            "timestamp": datetime.utcnow().isoformat(),
        })

    @socketio.on("request_critical_path", namespace="/orchestration")
    def on_request_critical_path(data):
        """Request critical path analysis"""
        workspace_id = data.get("workspace_id", "default")

        path, duration = dependency_resolver_service.get_critical_path(workspace_id)

        emit("critical_path", {
            "workspace_id": workspace_id,
            "path": path,
            "duration_seconds": duration,
        })

    # ==================== DIAGNOSTICS ====================

    @socketio.on("get_diagnostics", namespace="/orchestration")
    def on_get_diagnostics(data):
        """Get system diagnostics"""
        workspace_id = data.get("workspace_id", "default")

        queue_stats = task_queue_service.get_queue_stats()
        system_health = agent_coordinator_service.get_system_health()
        is_valid, issues = dependency_resolver_service.validate_graph(workspace_id)

        emit("diagnostics", {
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow().isoformat(),
            "queue_stats": queue_stats,
            "system_health": system_health,
            "graph_valid": is_valid,
            "graph_issues": issues,
            "message": f"System health: {system_health.get('avg_success_rate')}% success rate",
        })

    @socketio.on("test_event", namespace="/orchestration")
    def on_test_event(data):
        """Test WebSocket connectivity"""
        emit("test_response", {
            "message": "WebSocket connection successful",
            "echo": data.get("message", ""),
            "timestamp": datetime.utcnow().isoformat(),
        })
