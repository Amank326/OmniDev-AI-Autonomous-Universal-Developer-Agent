"""
Phase 48: Service Registry & Initialization
================================================
Central registry for all services from Phases 44-47
Provides unified initialization, lifecycle management, and dependency injection
"""

import threading
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service lifecycle status"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


class ServiceTier(Enum):
    """Service importance tiers"""
    CRITICAL = "critical"  # System cannot operate without
    HIGH = "high"          # Core functionality
    MEDIUM = "medium"      # Important features
    LOW = "low"            # Optional features


@dataclass
class ServiceMetrics:
    """Service performance metrics"""
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_health_check: Optional[datetime] = None
    health_check_count: int = 0
    error_count: int = 0
    initialization_time_ms: float = 0.0
    last_error: Optional[str] = None
    dependencies_ready: int = 0
    total_dependencies: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_check_count": self.health_check_count,
            "error_count": self.error_count,
            "initialization_time_ms": self.initialization_time_ms,
            "last_error": self.last_error,
            "dependencies_ready": f"{self.dependencies_ready}/{self.total_dependencies}"
        }


@dataclass
class ServiceInfo:
    """Service registration information"""
    service_id: str
    service_name: str
    tier: ServiceTier
    phase: int
    status: ServiceStatus = ServiceStatus.UNINITIALIZED
    description: str = ""
    version: str = "1.0.0"
    dependencies: list = field(default_factory=list)
    metrics: ServiceMetrics = field(default_factory=ServiceMetrics)
    initialization_fn: Optional[Callable] = None
    shutdown_fn: Optional[Callable] = None
    health_check_fn: Optional[Callable] = None
    service_instance: Optional[Any] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class ServiceRegistry:
    """
    Central registry for all platform services.
    Manages initialization, lifecycle, health checks, and dependency resolution.
    """

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.services: Dict[str, ServiceInfo] = {}
        self._lock = threading.RLock()
        self._startup_lock = threading.Lock()
        self._metrics = {
            "total_services": 0,
            "initialized_services": 0,
            "failed_services": 0,
            "startup_time_ms": 0.0
        }
        self._initialized = True
        logger.info("ServiceRegistry initialized")

    def register_service(
        self,
        service_id: str,
        service_name: str,
        phase: int,
        tier: ServiceTier,
        description: str = "",
        version: str = "1.0.0",
        dependencies: list = None,
        initialization_fn: Optional[Callable] = None,
        shutdown_fn: Optional[Callable] = None,
        health_check_fn: Optional[Callable] = None
    ) -> ServiceInfo:
        """Register a new service"""
        with self._lock:
            if service_id in self.services:
                logger.warning(f"Service {service_id} already registered")
                return self.services[service_id]

            service = ServiceInfo(
                service_id=service_id,
                service_name=service_name,
                tier=tier,
                phase=phase,
                description=description,
                version=version,
                dependencies=dependencies or [],
                initialization_fn=initialization_fn,
                shutdown_fn=shutdown_fn,
                health_check_fn=health_check_fn
            )

            self.services[service_id] = service
            self._metrics["total_services"] = len(self.services)
            logger.info(f"Registered service: {service_name} (Phase {phase}, Tier: {tier.value})")
            return service

    def initialize_service(self, service_id: str, dependencies_resolved: dict = None) -> bool:
        """Initialize a single service"""
        with self._lock:
            if service_id not in self.services:
                logger.error(f"Service {service_id} not found in registry")
                return False

            service = self.services[service_id]
            if service.status == ServiceStatus.READY:
                logger.debug(f"Service {service_id} already initialized")
                return True

            service.status = ServiceStatus.INITIALIZING
            start_time = datetime.utcnow()

            try:
                # Check dependencies
                if service.dependencies:
                    unresolved = [d for d in service.dependencies if d not in self.services or self.services[d].status != ServiceStatus.READY]
                    if unresolved:
                        logger.warning(f"Service {service_id} has unresolved dependencies: {unresolved}")
                        service.status = ServiceStatus.DEGRADED
                        service.metrics.last_error = f"Unresolved dependencies: {unresolved}"
                        return False

                    service.metrics.dependencies_ready = len(service.dependencies)
                    service.metrics.total_dependencies = len(service.dependencies)

                # Initialize service
                if service.initialization_fn:
                    service.service_instance = service.initialization_fn(dependencies_resolved or {})
                else:
                    service.service_instance = {}

                service.status = ServiceStatus.READY
                service.metrics.initialization_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                self._metrics["initialized_services"] += 1
                logger.info(f"Service {service_id} initialized successfully ({service.metrics.initialization_time_ms:.2f}ms)")
                return True

            except Exception as e:
                logger.error(f"Failed to initialize service {service_id}: {str(e)}")
                service.status = ServiceStatus.UNHEALTHY
                service.metrics.error_count += 1
                service.metrics.last_error = str(e)
                self._metrics["failed_services"] += 1
                return False

    def initialize_all(self, phases: list = None) -> Dict[str, bool]:
        """Initialize all services or services from specific phases"""
        with self._startup_lock:
            logger.info("Initializing all services...")
            start_time = datetime.utcnow()
            results = {}

            # Get services to initialize
            services_to_init = self.services
            if phases:
                services_to_init = {s_id: s for s_id, s in self.services.items() if s.phase in phases}

            # Sort by dependencies (topological sort)
            sorted_services = self._topological_sort(services_to_init)

            dependencies_resolved = {}
            for service_id in sorted_services:
                service = self.services[service_id]
                success = self.initialize_service(service_id, dependencies_resolved)
                results[service_id] = success

                if success:
                    dependencies_resolved[service_id] = service.service_instance

            self._metrics["startup_time_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"Service initialization completed in {self._metrics['startup_time_ms']:.2f}ms")
            logger.info(f"Results: {self._metrics['initialized_services']}/{self._metrics['total_services']} services ready")

            return results

    def health_check_service(self, service_id: str) -> bool:
        """Perform health check on a service"""
        with self._lock:
            if service_id not in self.services:
                return False

            service = self.services[service_id]

            # Update last health check
            service.metrics.last_health_check = datetime.utcnow()
            service.metrics.health_check_count += 1

            try:
                if service.health_check_fn:
                    is_healthy = service.health_check_fn(service.service_instance)
                else:
                    is_healthy = service.status == ServiceStatus.READY

                if is_healthy and service.status == ServiceStatus.UNHEALTHY:
                    service.status = ServiceStatus.READY
                    logger.info(f"Service {service_id} recovered")
                elif not is_healthy:
                    service.status = ServiceStatus.DEGRADED
                    service.metrics.error_count += 1

                return is_healthy

            except Exception as e:
                service.status = ServiceStatus.UNHEALTHY
                service.metrics.error_count += 1
                service.metrics.last_error = str(e)
                logger.error(f"Health check failed for {service_id}: {str(e)}")
                return False

    def health_check_all(self) -> Dict[str, bool]:
        """Perform health checks on all services"""
        logger.info("Running comprehensive health checks...")
        results = {}

        for service_id in self.services:
            results[service_id] = self.health_check_service(service_id)

        healthy_count = sum(1 for v in results.values() if v)
        logger.info(f"Health check complete: {healthy_count}/{len(results)} services healthy")
        return results

    def shutdown_service(self, service_id: str) -> bool:
        """Shutdown a single service"""
        with self._lock:
            if service_id not in self.services:
                return False

            service = self.services[service_id]
            service.status = ServiceStatus.SHUTTING_DOWN

            try:
                if service.shutdown_fn:
                    service.shutdown_fn(service.service_instance)

                service.status = ServiceStatus.STOPPED
                logger.info(f"Service {service_id} shutdown successfully")
                return True

            except Exception as e:
                logger.error(f"Error shutting down service {service_id}: {str(e)}")
                return False

    def shutdown_all(self) -> Dict[str, bool]:
        """Shutdown all services in reverse dependency order"""
        logger.info("Shutting down all services...")
        results = {}

        # Shutdown in reverse order of initialization
        sorted_services = list(reversed(self._topological_sort(self.services)))
        for service_id in sorted_services:
            results[service_id] = self.shutdown_service(service_id)

        return results

    def get_service_instance(self, service_id: str) -> Optional[Any]:
        """Get service instance"""
        with self._lock:
            if service_id in self.services:
                return self.services[service_id].service_instance
            return None

    def get_service_info(self, service_id: str) -> Optional[ServiceInfo]:
        """Get service info"""
        with self._lock:
            return self.services.get(service_id)

    def get_all_services(self) -> Dict[str, ServiceInfo]:
        """Get all registered services"""
        with self._lock:
            return dict(self.services)

    def get_services_by_tier(self, tier: ServiceTier) -> Dict[str, ServiceInfo]:
        """Get services by tier"""
        with self._lock:
            return {s_id: s for s_id, s in self.services.items() if s.tier == tier}

    def get_services_by_phase(self, phase: int) -> Dict[str, ServiceInfo]:
        """Get services from a specific phase"""
        with self._lock:
            return {s_id: s for s_id, s in self.services.items() if s.phase == phase}

    def get_registry_status(self) -> Dict[str, Any]:
        """Get overall registry status"""
        with self._lock:
            status_count = {}
            for service in self.services.values():
                status = service.status.value
                status_count[status] = status_count.get(status, 0) + 1

            return {
                "total_services": self._metrics["total_services"],
                "initialized_services": self._metrics["initialized_services"],
                "failed_services": self._metrics["failed_services"],
                "startup_time_ms": self._metrics["startup_time_ms"],
                "status_breakdown": status_count,
                "services_by_phase": self._get_phase_breakdown(),
                "services_by_tier": self._get_tier_breakdown()
            }

    def export_metrics(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export all service metrics"""
        with self._lock:
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "registry_status": self.get_registry_status(),
                "services": {
                    s_id: {
                        "name": s.service_name,
                        "status": s.status.value,
                        "tier": s.tier.value,
                        "phase": s.phase,
                        "version": s.version,
                        "metrics": s.metrics.to_dict()
                    }
                    for s_id, s in self.services.items()
                }
            }

            if output_path:
                try:
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w') as f:
                        json.dump(metrics, f, indent=2)
                    logger.info(f"Metrics exported to {output_path}")
                except Exception as e:
                    logger.error(f"Failed to export metrics: {str(e)}")

            return metrics

    def _topological_sort(self, services: Dict[str, ServiceInfo]) -> list:
        """Topological sort of services by dependencies"""
        visited = set()
        stack = []

        def visit(service_id):
            if service_id in visited:
                return
            visited.add(service_id)

            service = services.get(service_id)
            if service:
                for dep_id in service.dependencies:
                    if dep_id in services:
                        visit(dep_id)

            stack.append(service_id)

        for service_id in services:
            visit(service_id)

        return stack

    def _get_phase_breakdown(self) -> Dict[int, int]:
        """Get service count by phase"""
        breakdown = {}
        for service in self.services.values():
            phase = service.phase
            breakdown[phase] = breakdown.get(phase, 0) + 1
        return breakdown

    def _get_tier_breakdown(self) -> Dict[str, int]:
        """Get service count by tier"""
        breakdown = {}
        for service in self.services.values():
            tier = service.tier.value
            breakdown[tier] = breakdown.get(tier, 0) + 1
        return breakdown
