"""
Worker Management Routes
=======================

API endpoints for monitoring and managing Celery workers and tasks.

Endpoints:
- GET /api/workers/health - System health status
- GET /api/workers/stats - Worker statistics
- GET /api/tasks - List active, scheduled, and reserved tasks
- GET /api/tasks/{task_id} - Get specific task status
- POST /api/tasks/{task_id}/retry - Retry a failed task
- POST /api/tasks/{task_id}/revoke - Revoke a task
- GET /api/queues - Get queue statistics
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from app.tasks.monitoring import monitoring_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["workers"])


@router.get("/workers/health")
async def get_health_status() -> Dict[str, Any]:
    """
    Get overall health status of Celery system.
    
    Returns:
        Health information including workers count, active tasks, and status
    """
    try:
        health = monitoring_service.get_health_status()
        return health
    except Exception as e:
        logger.error(f"Failed to get health status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get health status")


@router.get("/workers/stats")
async def get_worker_stats() -> Dict[str, Any]:
    """
    Get detailed worker statistics.
    
    Returns:
        Dictionary with worker statistics including pool size, processed tasks, etc.
    """
    try:
        stats = monitoring_service.get_worker_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get worker stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get worker stats")


@router.get("/tasks")
async def list_tasks(
    task_type: Optional[str] = Query(None, description="Filter by task type: active, scheduled, reserved, all")
) -> Dict[str, Any]:
    """
    List tasks by category.
    
    Args:
        task_type: Type of tasks to list (active, scheduled, reserved, all)
    
    Returns:
        Dictionary containing tasks grouped by worker
    """
    try:
        if task_type == "active" or task_type is None:
            active = monitoring_service.get_active_tasks()
            return {"type": "active", "tasks": active}
        
        elif task_type == "scheduled":
            scheduled = monitoring_service.get_scheduled_tasks()
            return {"type": "scheduled", "tasks": scheduled}
        
        elif task_type == "reserved":
            reserved = monitoring_service.get_reserved_tasks()
            return {"type": "reserved", "tasks": reserved}
        
        elif task_type == "all":
            active = monitoring_service.get_active_tasks()
            scheduled = monitoring_service.get_scheduled_tasks()
            reserved = monitoring_service.get_reserved_tasks()
            return {
                "type": "all",
                "active": active,
                "scheduled": scheduled,
                "reserved": reserved,
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid task_type. Use: active, scheduled, reserved, all"
            )
    
    except Exception as e:
        logger.error(f"Failed to list tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list tasks")


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get status of a specific task.
    
    Args:
        task_id: Celery task ID
    
    Returns:
        Task status, result, and metadata
    """
    try:
        status = monitoring_service.get_task_status(task_id)
        return status
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get task status")


@router.get("/tasks/{task_id}/info")
async def get_task_info(task_id: str) -> Dict[str, Any]:
    """
    Get comprehensive information about a task.
    
    Args:
        task_id: Celery task ID
    
    Returns:
        Comprehensive task information
    """
    try:
        info = monitoring_service.get_task_info(task_id)
        return info
    except Exception as e:
        logger.error(f"Failed to get task info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get task info")


@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str) -> Dict[str, Any]:
    """
    Retry a failed task.
    
    Args:
        task_id: Celery task ID
    
    Returns:
        Result of retry operation
    """
    try:
        result = monitoring_service.retry_task(task_id)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retry task")


@router.post("/tasks/{task_id}/revoke")
async def revoke_task(task_id: str, terminate: bool = Query(False)) -> Dict[str, Any]:
    """
    Revoke a task (prevent execution or stop if running).
    
    Args:
        task_id: Celery task ID
        terminate: Whether to terminate running task
    
    Returns:
        Result of revoke operation
    """
    try:
        result = monitoring_service.revoke_task(task_id, terminate=terminate)
        return result
    except Exception as e:
        logger.error(f"Failed to revoke task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to revoke task")


@router.get("/queues")
async def get_queue_stats() -> Dict[str, Any]:
    """
    Get queue statistics.
    
    Returns:
        Queue names and approximate task counts
    """
    try:
        stats = monitoring_service.get_queue_stats()
        return {"queues": stats}
    except Exception as e:
        logger.error(f"Failed to get queue stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get queue stats")


@router.post("/tasks/purge")
async def purge_queue(queue_name: str = Query("default")) -> Dict[str, Any]:
    """
    Purge all tasks from a queue (DANGEROUS - use with caution).
    
    Args:
        queue_name: Name of the queue to purge
    
    Returns:
        Result of purge operation
    
    Note:
        This is a destructive operation. Use only in development/testing.
    """
    try:
        result = monitoring_service.purge_queue(queue_name)
        return result
    except Exception as e:
        logger.error(f"Failed to purge queue: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to purge queue")


@router.get("/failed-tasks")
async def get_failed_tasks(limit: int = Query(100, ge=1, le=1000)) -> Dict[str, Any]:
    """
    Get failed tasks (dead letter queue).
    
    Args:
        limit: Maximum number of failed tasks to return
    
    Returns:
        List of failed tasks
    """
    try:
        tasks = monitoring_service.get_failed_tasks(limit)
        return {"failed_tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.error(f"Failed to get failed tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get failed tasks")
