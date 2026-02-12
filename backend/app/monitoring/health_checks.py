"""
Monitoring, Health Checks, and Metrics Configuration
=====================================================

Add this to app/monitoring/health_checks.py
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from redis import Redis
import psutil

from app.database.config import SessionLocal
from app.rag.knowledge_base import knowledge_base_manager
from app.agents.orchestrator import agent_orchestrator
from app.memory.agent_memory import agent_memory_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])

# Global health metrics
health_metrics = {
    "startup_time": datetime.utcnow(),
    "last_health_check": None,
    "request_count": 0,
    "error_count": 0,
}


class HealthChecker:
    """Health check service for system components."""
    
    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            db = SessionLocal()
            start = time.time()
            
            # Execute simple query
            result = db.execute(text("SELECT 1")).fetchone()
            
            duration_ms = (time.time() - start) * 1000
            db.close()
            
            return {
                "status": "healthy",
                "response_time_ms": round(duration_ms, 2),
                "connected": result is not None,
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    @staticmethod
    def check_redis() -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            redis = Redis(host='localhost', port=6379, db=0)
            start = time.time()
            
            redis.ping()
            
            duration_ms = (time.time() - start) * 1000
            
            info = redis.info()
            
            return {
                "status": "healthy",
                "response_time_ms": round(duration_ms, 2),
                "used_memory_mb": round(info.get('used_memory', 0) / 1024 / 1024, 2),
                "connected_clients": info.get('connected_clients', 0),
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    @staticmethod
    def check_knowledge_base() -> Dict[str, Any]:
        """Check knowledge base status."""
        try:
            stats = knowledge_base_manager.get_knowledge_base_stats()
            
            return {
                "status": "healthy",
                "total_documents": stats.get("total_documents", 0),
                "total_chunks": stats.get("total_chunks", 0),
                "indexed_documents": stats.get("indexed_documents", 0),
            }
        except Exception as e:
            logger.error(f"Knowledge base health check failed: {str(e)}")
            return {
                "status": "degraded",
                "error": str(e),
            }
    
    @staticmethod
    def check_agents() -> Dict[str, Any]:
        """Check agent orchestrator status."""
        try:
            agent_count = len(agent_orchestrator.available_agents)
            team_count = len(agent_orchestrator.agent_teams)
            active_tasks = len(agent_orchestrator.get_active_tasks())
            
            return {
                "status": "healthy",
                "agents_available": agent_count,
                "teams_active": team_count,
                "tasks_active": active_tasks,
            }
        except Exception as e:
            logger.error(f"Agent health check failed: {str(e)}")
            return {
                "status": "degraded",
                "error": str(e),
            }
    
    @staticmethod
    def check_system_resources() -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy" if cpu_percent < 80 else "degraded",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "memory_available_mb": round(memory.available / 1024 / 1024, 2),
            }
        except Exception as e:
            logger.error(f"System resource check failed: {str(e)}")
            return {
                "status": "unknown",
                "error": str(e),
            }
    
    @staticmethod
    def check_memory_system() -> Dict[str, Any]:
        """Check team memory system."""
        try:
            stats = agent_memory_manager.get_memory_stats()
            
            return {
                "status": "healthy",
                "total_entries": stats.get("total_entries", 0),
                "cached_entries": stats.get("cached_entries", 0),
                "avg_retrieval_time_ms": stats.get("avg_retrieval_time_ms", 0),
            }
        except Exception as e:
            logger.error(f"Memory system check failed: {str(e)}")
            return {
                "status": "degraded",
                "error": str(e),
            }


@router.get("/")
async def health_check() -> JSONResponse:
    """
    Basic health check endpoint.
    
    Returns:
        Health status
    """
    health_metrics["request_count"] += 1
    health_metrics["last_health_check"] = datetime.utcnow()
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - health_metrics["startup_time"]).total_seconds(),
        }
    )


@router.get("/detailed")
async def detailed_health_check() -> JSONResponse:
    """
    Detailed health check with all components.
    
    Returns:
        Detailed health status of all components
    """
    health_metrics["request_count"] += 1
    
    # Check all components
    checks = {
        "database": HealthChecker.check_database(),
        "redis": HealthChecker.check_redis(),
        "knowledge_base": HealthChecker.check_knowledge_base(),
        "agents": HealthChecker.check_agents(),
        "system_resources": HealthChecker.check_system_resources(),
        "memory_system": HealthChecker.check_memory_system(),
    }
    
    # Determine overall status
    statuses = [check.get("status", "unknown") for check in checks.values()]
    if "unhealthy" in statuses:
        overall_status = "unhealthy"
        status_code = 503
    elif "degraded" in statuses:
        overall_status = "degraded"
        status_code = 200
    else:
        overall_status = "healthy"
        status_code = 200
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - health_metrics["startup_time"]).total_seconds(),
            "checks": checks,
            "metrics": {
                "request_count": health_metrics["request_count"],
                "error_count": health_metrics["error_count"],
            },
        }
    )


@router.get("/readiness")
async def readiness_probe() -> JSONResponse:
    """
    Kubernetes readiness probe.
    
    Returns:
        Ready status
    """
    # Check critical dependencies
    db_check = HealthChecker.check_database()
    redis_check = HealthChecker.check_redis()
    
    if db_check["status"] == "healthy" and redis_check["status"] == "healthy":
        return JSONResponse(
            status_code=200,
            content={"status": "ready"}
        )
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready"}
        )


@router.get("/liveness")
async def liveness_probe() -> JSONResponse:
    """
    Kubernetes liveness probe.
    
    Returns:
        Alive status
    """
    # Simple check that service is running
    return JSONResponse(
        status_code=200,
        content={"status": "alive"}
    )


@router.get("/startup")
async def startup_probe() -> JSONResponse:
    """
    Kubernetes startup probe.
    
    Returns:
        Startup status
    """
    uptime = (datetime.utcnow() - health_metrics["startup_time"]).total_seconds()
    
    if uptime > 30:  # Allow 30 seconds for startup
        return JSONResponse(
            status_code=200,
            content={"status": "started"}
        )
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "starting", "uptime_seconds": uptime}
        )


@router.get("/metrics/basic")
async def basic_metrics() -> Dict[str, Any]:
    """Get basic system metrics."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - health_metrics["startup_time"]).total_seconds(),
        "request_count": health_metrics["request_count"],
        "error_count": health_metrics["error_count"],
        "error_rate": health_metrics["error_count"] / max(health_metrics["request_count"], 1),
    }
