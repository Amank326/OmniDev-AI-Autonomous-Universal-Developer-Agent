"""
Orchestration API Routes for OmniDev AI
REST API endpoints for agent orchestration, task management, and dependency resolution
"""

from flask import Blueprint, request, jsonify
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from app.services.task_queue_service import (
    TaskQueueService, TaskStatus, TaskPriority, TaskType, TaskDependency
)
from app.services.agent_coordinator_service import (
    AgentCoordinatorService, AgentStatus, AgentCapability, CollaborationType
)
from app.services.dependency_resolver_service import (
    DependencyResolverService, DependencyType
)

# Initialize blueprint
orchestration_bp = Blueprint("orchestration", __name__, url_prefix="/api/v1/orchestration")

# Initialize services (should be injected from main app)
task_queue_service = TaskQueueService()
agent_coordinator_service = AgentCoordinatorService()
dependency_resolver_service = DependencyResolverService()


# ==================== TASK MANAGEMENT ENDPOINTS ====================

@orchestration_bp.route("/tasks", methods=["GET"])
def get_tasks():
    """
    Get all tasks with optional filtering
    Query params: status, agent_id, workspace_id, priority, limit, offset
    """
    try:
        status_filter = request.args.get("status")
        agent_id = request.args.get("agent_id")
        workspace_id = request.args.get("workspace_id", "default")
        priority = request.args.get("priority")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        tasks = task_queue_service.get_all_tasks()

        # Apply filters
        if status_filter:
            tasks = [t for t in tasks if t.status.value == status_filter]
        if agent_id:
            tasks = [t for t in tasks if t.assigned_agent == agent_id]
        if workspace_id:
            tasks = [t for t in tasks if t.workspace_id == workspace_id]
        if priority:
            tasks = [t for t in tasks if t.priority.value == priority]

        # Pagination
        total = len(tasks)
        tasks = tasks[offset:offset + limit]

        return jsonify({
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "type": t.task_type.value,
                    "status": t.status.value,
                    "priority": t.priority.value,
                    "assigned_agent": t.assigned_agent,
                    "created_at": t.created_at.isoformat(),
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "estimated_duration": t.estimated_duration_seconds,
                }
                for t in tasks
            ]
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/tasks", methods=["POST"])
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()

        task = task_queue_service.create_task(
            name=data.get("name"),
            description=data.get("description", ""),
            task_type=TaskType(data.get("task_type", "analysis")),
            assigned_agent=data.get("assigned_agent"),
            payload=data.get("payload", {}),
            priority=TaskPriority(data.get("priority", 1)),
            estimated_duration=data.get("estimated_duration", 300),
            timeout=data.get("timeout", 3600),
            tags=data.get("tags", []),
            created_by=data.get("created_by", ""),
            workspace_id=data.get("workspace_id", "default"),
        )

        # Add dependencies if specified
        dependencies = data.get("dependencies", [])
        for dep in dependencies:
            dep_obj = TaskDependency(
                task_id=dep["task_id"],
                required_status=TaskStatus(dep.get("required_status", "completed")),
                must_succeed=dep.get("must_succeed", True),
            )
            task.dependencies.append(dep_obj)

        return jsonify({
            "success": True,
            "message": "Task created",
            "data": {
                "id": task.id,
                "name": task.name,
                "status": task.status.value,
                "assigned_agent": task.assigned_agent,
            }
        }), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/tasks/<task_id>", methods=["GET"])
def get_task(task_id):
    """Get task details"""
    try:
        task = task_queue_service.get_task(task_id)
        if not task:
            return jsonify({"success": False, "error": "Task not found"}), 404

        return jsonify({
            "success": True,
            "data": {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "type": task.task_type.value,
                "status": task.status.value,
                "priority": task.priority.value,
                "assigned_agent": task.assigned_agent,
                "payload": task.payload,
                "result": task.result,
                "error": task.error,
                "dependencies": [
                    {
                        "task_id": d.task_id,
                        "required_status": d.required_status.value,
                        "must_succeed": d.must_succeed,
                    }
                    for d in task.dependencies
                ],
                "subtasks": task.subtasks,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "metrics": {
                    "execution_time": task.metrics.execution_time_seconds,
                    "retry_count": task.metrics.retry_count,
                }
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/tasks/<task_id>/status", methods=["PUT"])
def update_task_status(task_id):
    """Update task status"""
    try:
        data = request.get_json()
        status = TaskStatus(data.get("status"))
        result = data.get("result")
        error = data.get("error")

        success = task_queue_service.update_task_status(
            task_id=task_id,
            status=status,
            result=result,
            error=error,
        )

        if not success:
            return jsonify({"success": False, "error": "Task not found"}), 404

        # If task completed, unblock dependent tasks
        if status == TaskStatus.COMPLETED:
            unblocked = task_queue_service._unblock_dependent_tasks(task_id)

        return jsonify({
            "success": True,
            "message": f"Task status updated to {status.value}",
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/tasks/<task_id>/schedule", methods=["POST"])
def schedule_task(task_id):
    """Schedule task for future execution"""
    try:
        data = request.get_json()
        scheduled_time = datetime.fromisoformat(data.get("scheduled_time"))

        success = task_queue_service.schedule_task(task_id, scheduled_time)

        if not success:
            return jsonify({"success": False, "error": "Task not found"}), 404

        return jsonify({
            "success": True,
            "message": "Task scheduled",
            "data": {
                "task_id": task_id,
                "scheduled_at": scheduled_time.isoformat(),
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/tasks/<task_id>/pause", methods=["POST"])
def pause_task(task_id):
    """Pause a running task"""
    try:
        success = task_queue_service.pause_task(task_id)
        if not success:
            return jsonify({"success": False, "error": "Task not found or not running"}), 404

        return jsonify({
            "success": True,
            "message": "Task paused",
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/tasks/<task_id>/resume", methods=["POST"])
def resume_task(task_id):
    """Resume a paused task"""
    try:
        success = task_queue_service.resume_task(task_id)
        if not success:
            return jsonify({"success": False, "error": "Task not found or not paused"}), 404

        return jsonify({
            "success": True,
            "message": "Task resumed",
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/tasks/<task_id>/cancel", methods=["POST"])
def cancel_task(task_id):
    """Cancel a task"""
    try:
        success = task_queue_service.cancel_task(task_id)
        if not success:
            return jsonify({"success": False, "error": "Task not found"}), 404

        return jsonify({
            "success": True,
            "message": "Task cancelled",
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/tasks/<task_id>/retry", methods=["POST"])
def retry_task(task_id):
    """Retry a failed task"""
    try:
        success = task_queue_service.retry_task(task_id)
        if not success:
            return jsonify({"success": False, "error": "Task not found or retry limit exceeded"}), 404

        return jsonify({
            "success": True,
            "message": "Task queued for retry",
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==================== AGENT QUEUE ENDPOINTS ====================

@orchestration_bp.route("/agents/<agent_id>/queue", methods=["GET"])
def get_agent_queue(agent_id):
    """Get task queue for agent"""
    try:
        queue = task_queue_service.get_agent_queue(agent_id)

        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "queue_size": len(queue),
            "data": [
                {
                    "id": t.id,
                    "name": t.name,
                    "status": t.status.value,
                    "priority": t.priority.value,
                    "created_at": t.created_at.isoformat(),
                }
                for t in queue
            ]
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/agents/<agent_id>/next-task", methods=["POST"])
def get_next_task(agent_id):
    """Get next task for agent to execute"""
    try:
        task = task_queue_service.pop_next_task(agent_id)
        if not task:
            return jsonify({"success": False, "message": "No tasks available"}), 200

        # Update task status
        task_queue_service.update_task_status(task.id, TaskStatus.RUNNING)

        return jsonify({
            "success": True,
            "data": {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "type": task.task_type.value,
                "payload": task.payload,
                "timeout": task.timeout_seconds,
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/queue/stats", methods=["GET"])
def get_queue_stats():
    """Get overall queue statistics"""
    try:
        stats = task_queue_service.get_queue_stats()

        return jsonify({
            "success": True,
            "data": stats
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==================== AGENT MANAGEMENT ENDPOINTS ====================

@orchestration_bp.route("/agents", methods=["GET"])
def get_agents():
    """Get all agents with status"""
    try:
        stats = agent_coordinator_service.get_all_agents_stats()

        return jsonify({
            "success": True,
            "total_agents": len(stats),
            "data": stats
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/agents", methods=["POST"])
def register_agent():
    """Register a new agent"""
    try:
        data = request.get_json()

        agent = agent_coordinator_service.register_agent(
            name=data.get("name"),
            agent_type=data.get("agent_type"),
            capabilities=[AgentCapability(c) for c in data.get("capabilities", [])],
            max_concurrent_tasks=data.get("max_concurrent_tasks", 3),
            available_memory_mb=data.get("available_memory_mb", 2048),
            api_endpoint=data.get("api_endpoint", ""),
            metadata=data.get("metadata", {}),
        )

        return jsonify({
            "success": True,
            "message": "Agent registered",
            "data": {
                "id": agent.id,
                "name": agent.name,
                "agent_type": agent.agent_type,
            }
        }), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/agents/<agent_id>", methods=["GET"])
def get_agent(agent_id):
    """Get agent details"""
    try:
        stats = agent_coordinator_service.get_agent_stats(agent_id)
        if not stats:
            return jsonify({"success": False, "error": "Agent not found"}), 404

        return jsonify({
            "success": True,
            "data": stats
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/agents/<agent_id>/status", methods=["PUT"])
def update_agent_status(agent_id):
    """Update agent status"""
    try:
        data = request.get_json()
        status = AgentStatus(data.get("status"))

        success = agent_coordinator_service.update_agent_status(agent_id, status)
        if not success:
            return jsonify({"success": False, "error": "Agent not found"}), 404

        return jsonify({
            "success": True,
            "message": f"Agent status updated to {status.value}",
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/agents/<agent_id>/assign-task/<task_id>", methods=["POST"])
def assign_task_to_agent(agent_id, task_id):
    """Assign task to agent"""
    try:
        data = request.get_json()
        memory_required = data.get("memory_mb", 512)

        success = agent_coordinator_service.assign_task_to_agent(
            agent_id, task_id, memory_required
        )

        if not success:
            return jsonify({"success": False, "error": "Assignment failed"}), 400

        return jsonify({
            "success": True,
            "message": "Task assigned",
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/agents/<agent_id>/complete-task/<task_id>", methods=["POST"])
def complete_agent_task(agent_id, task_id):
    """Mark task as completed for agent"""
    try:
        data = request.get_json()
        memory_freed = data.get("memory_freed_mb", 512)
        success = data.get("success", True)

        success = agent_coordinator_service.complete_agent_task(
            agent_id, task_id, memory_freed, success
        )

        if not success:
            return jsonify({"success": False, "error": "Task not found"}), 404

        return jsonify({
            "success": True,
            "message": "Task completed",
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/system/health", methods=["GET"])
def get_system_health():
    """Get overall system health"""
    try:
        health = agent_coordinator_service.get_system_health()

        return jsonify({
            "success": True,
            "data": health
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==================== COLLABORATION ENDPOINTS ====================

@orchestration_bp.route("/collaborations", methods=["POST"])
def create_collaboration():
    """Create multi-agent collaboration"""
    try:
        data = request.get_json()

        collab = agent_coordinator_service.create_collaboration(
            name=data.get("name"),
            description=data.get("description", ""),
            agent_ids=data.get("agent_ids", []),
            task_id=data.get("task_id", ""),
            collaboration_type=CollaborationType(data.get("collaboration_type", "sequential")),
            metadata=data.get("metadata", {}),
        )

        if not collab:
            return jsonify({"success": False, "error": "Invalid agents"}), 400

        return jsonify({
            "success": True,
            "message": "Collaboration created",
            "data": {
                "id": collab.id,
                "name": collab.name,
                "agent_ids": collab.agent_ids,
                "status": collab.status,
            }
        }), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/collaborations/<collab_id>", methods=["GET"])
def get_collaboration(collab_id):
    """Get collaboration details"""
    try:
        collab = agent_coordinator_service.get_collaboration(collab_id)
        if not collab:
            return jsonify({"success": False, "error": "Collaboration not found"}), 404

        return jsonify({
            "success": True,
            "data": {
                "id": collab.id,
                "name": collab.name,
                "description": collab.description,
                "agent_ids": collab.agent_ids,
                "status": collab.status,
                "collaboration_type": collab.collaboration_type.value,
                "created_at": collab.created_at.isoformat(),
                "completed_at": collab.completed_at.isoformat() if collab.completed_at else None,
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/collaborations/<collab_id>/complete", methods=["POST"])
def complete_collaboration(collab_id):
    """Complete collaboration"""
    try:
        data = request.get_json()
        result = data.get("result", {})

        success = agent_coordinator_service.complete_collaboration(collab_id, result)
        if not success:
            return jsonify({"success": False, "error": "Collaboration not found"}), 404

        return jsonify({
            "success": True,
            "message": "Collaboration completed",
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==================== DEPENDENCY RESOLUTION ENDPOINTS ====================

@orchestration_bp.route("/dependencies/add", methods=["POST"])
def add_dependency():
    """Add task dependency"""
    try:
        data = request.get_json()
        workspace_id = data.get("workspace_id", "default")
        task_id = data.get("task_id")
        depends_on_task_id = data.get("depends_on_task_id")

        success = dependency_resolver_service.add_dependency(
            workspace_id=workspace_id,
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
            dependency_type=DependencyType(data.get("dependency_type", "must_complete")),
            weight=float(data.get("weight", 1.0)),
        )

        if not success:
            return jsonify({"success": False, "error": "Failed to add dependency (may create cycle)"}), 400

        return jsonify({
            "success": True,
            "message": "Dependency added",
        }), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/dependencies/<workspace_id>/execution-order", methods=["GET"])
def get_execution_order(workspace_id):
    """Get optimal task execution order"""
    try:
        order = dependency_resolver_service.get_execution_order(workspace_id)

        return jsonify({
            "success": True,
            "execution_order": order,
            "total_tasks": len(order),
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/dependencies/<workspace_id>/cycles", methods=["GET"])
def find_cycles(workspace_id):
    """Find dependency cycles"""
    try:
        cycles = dependency_resolver_service.find_all_cycles(workspace_id)

        return jsonify({
            "success": True,
            "has_cycles": len(cycles) > 0,
            "cycle_count": len(cycles),
            "cycles": cycles,
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/dependencies/<workspace_id>/parallel-groups", methods=["GET"])
def get_parallel_groups(workspace_id):
    """Get groups of tasks that can execute in parallel"""
    try:
        groups = dependency_resolver_service.get_parallelizable_groups(workspace_id)

        return jsonify({
            "success": True,
            "group_count": len(groups),
            "groups": groups,
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/dependencies/<workspace_id>/critical-path", methods=["GET"])
def get_critical_path(workspace_id):
    """Get critical path through dependencies"""
    try:
        path, duration = dependency_resolver_service.get_critical_path(workspace_id)

        return jsonify({
            "success": True,
            "critical_path": path,
            "estimated_duration_seconds": duration,
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/dependencies/<workspace_id>/task/<task_id>/impact", methods=["GET"])
def get_impact_analysis(workspace_id, task_id):
    """Get impact analysis for task changes"""
    try:
        impact = dependency_resolver_service.get_impact_analysis(workspace_id, task_id)

        return jsonify({
            "success": True,
            "data": impact
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@orchestration_bp.route("/dependencies/<workspace_id>/plan", methods=["GET"])
def get_execution_plan(workspace_id):
    """Get optimized execution plan"""
    try:
        plan = dependency_resolver_service.optimize_execution_plan(workspace_id)

        return jsonify({
            "success": True,
            "data": plan
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ==================== UTILITY ENDPOINTS ====================

@orchestration_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "orchestration",
        "timestamp": datetime.utcnow().isoformat(),
    }), 200


@orchestration_bp.route("/stats", methods=["GET"])
def get_stats():
    """Get all statistics"""
    try:
        queue_stats = task_queue_service.get_queue_stats()
        system_health = agent_coordinator_service.get_system_health()

        return jsonify({
            "success": True,
            "queue": queue_stats,
            "system": system_health,
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
