"""
Integration Configuration Service
Manages cross-phase configuration, service registration, dependency injection, and version compatibility
Phase 40: Final Integration & Platform Stabilization
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from threading import RLock
from datetime import datetime
import json

# Configure logging
logger = logging.getLogger(__name__)


class ServicePhase(Enum):
    """Service phase enum for version tracking"""
    CORE_FOUNDATION = "phase_1_5"  # Phases 1-5: Core foundation
    ADVANCED_FEATURES = "phase_6_15"  # Phases 6-15: Advanced features
    DATA_INTEGRATION = "phase_16_25"  # Phases 16-25: Data integration
    MONITORING_ANALYTICS = "phase_26_35"  # Phases 26-35: Monitoring
    INTEGRATION_SECURITY = "phase_36_40"  # Phases 36-40: Integration


class ServiceHealth(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


class IntegrationMode(Enum):
    """Integration mode for service loading"""
    STRICT = "strict"  # All dependencies must be available
    LENIENT = "lenient"  # Graceful degradation allowed
    FALLBACK = "fallback"  # Use fallback implementations


@dataclass
class ServiceDependency:
    """Represents a service dependency"""
    service_name: str
    required: bool = True
    min_version: str = "1.0.0"
    max_version: str = "999.999.999"
    fallback_available: bool = False

    def is_compatible(self, version: str) -> bool:
        """Check if version is within acceptable range"""
        return self._compare_versions(self.min_version, version) <= 0 and \
               self._compare_versions(version, self.max_version) <= 0

    @staticmethod
    def _compare_versions(v1: str, v2: str) -> int:
        """Compare semantic versions (-1: v1 < v2, 0: equal, 1: v1 > v2)"""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            if p1 > p2:
                return 1
        return 0


@dataclass
class ServiceConfiguration:
    """Service configuration and metadata"""
    name: str
    phase: ServicePhase
    version: str
    enabled: bool = True
    dependencies: List[ServiceDependency] = field(default_factory=list)
    health_check_interval_seconds: int = 60
    startup_timeout_seconds: int = 30
    shutdown_timeout_seconds: int = 10
    config_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceHealthStatus:
    """Service health status report"""
    service_name: str
    status: ServiceHealth
    last_check: datetime = field(default_factory=datetime.utcnow)
    endpoint_latency_ms: Optional[float] = None
    error_rate: float = 0.0
    warning_message: Optional[str] = None
    critical_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationMetrics:
    """Integration metrics and statistics"""
    total_services: int = 0
    healthy_services: int = 0
    services_with_warnings: int = 0
    critical_services: int = 0
    offline_services: int = 0
    average_latency_ms: float = 0.0
    error_rate: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    dependency_violations: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)


class ServiceRegistry:
    """Registry for all platform services across phases"""

    def __init__(self):
        self.services: Dict[str, ServiceConfiguration] = {}
        self.health_status: Dict[str, ServiceHealthStatus] = {}
        self.service_instances: Dict[str, Any] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        self.metrics = IntegrationMetrics()
        self.lock = RLock()
        self.health_callbacks: List[Callable] = []

    def register_service(self, config: ServiceConfiguration, instance: Optional[Any] = None) -> bool:
        """Register a service in the registry"""
        with self.lock:
            if config.name in self.services:
                logger.warning(f"Service {config.name} already registered, overwriting")
            
            self.services[config.name] = config
            if instance:
                self.service_instances[config.name] = instance
            
            # Build dependency graph
            self.dependency_graph[config.name] = [dep.service_name for dep in config.dependencies]
            
            # Initialize health status
            self.health_status[config.name] = ServiceHealthStatus(
                service_name=config.name,
                status=ServiceHealth.HEALTHY if config.enabled else ServiceHealth.OFFLINE
            )
            
            logger.info(f"Service {config.name} (phase {config.phase.value}) registered")
            self.metrics.total_services += 1
            return True

    def get_service(self, service_name: str) -> Optional[Any]:
        """Retrieve a service instance"""
        with self.lock:
            return self.service_instances.get(service_name)

    def get_service_config(self, service_name: str) -> Optional[ServiceConfiguration]:
        """Retrieve service configuration"""
        with self.lock:
            return self.services.get(service_name)

    def validate_dependencies(self, service_name: str) -> tuple[bool, List[str]]:
        """Validate all dependencies for a service"""
        with self.lock:
            config = self.services.get(service_name)
            if not config:
                return False, [f"Service {service_name} not found"]
            
            errors = []
            for dep in config.dependencies:
                dep_config = self.services.get(dep.service_name)
                
                if not dep_config:
                    if dep.required:
                        errors.append(f"Required dependency {dep.service_name} not found")
                    continue
                
                if not dep.is_compatible(dep_config.version):
                    error = f"Dependency {dep.service_name} version {dep_config.version} " \
                           f"not in range [{dep.min_version}, {dep.max_version}]"
                    if dep.required:
                        errors.append(error)
                    else:
                        logger.warning(error)
                
                if not dep_config.enabled and dep.required:
                    errors.append(f"Required dependency {dep.service_name} is disabled")
            
            return len(errors) == 0, errors

    def update_service_health(self, service_name: str, status: ServiceHealth,
                            latency_ms: Optional[float] = None,
                            error_rate: float = 0.0,
                            warning_msg: Optional[str] = None,
                            critical_msg: Optional[str] = None,
                            metrics: Optional[Dict] = None) -> bool:
        """Update service health status"""
        with self.lock:
            if service_name not in self.health_status:
                return False
            
            health = self.health_status[service_name]
            health.status = status
            health.last_check = datetime.utcnow()
            health.endpoint_latency_ms = latency_ms
            health.error_rate = error_rate
            health.warning_message = warning_msg
            health.critical_message = critical_msg
            if metrics:
                health.metrics.update(metrics)
            
            # Update metrics
            self._recalculate_metrics()
            
            # Trigger callbacks
            for callback in self.health_callbacks:
                try:
                    callback(service_name, status)
                except Exception as e:
                    logger.error(f"Health callback error for {service_name}: {e}")
            
            return True

    def get_health_report(self) -> Dict[str, ServiceHealthStatus]:
        """Get complete health report for all services"""
        with self.lock:
            return dict(self.health_status)

    def get_metrics(self) -> IntegrationMetrics:
        """Get integration metrics"""
        with self.lock:
            return self.metrics

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get dependency graph (service -> dependencies)"""
        with self.lock:
            return dict(self.dependency_graph)

    def get_services_by_phase(self, phase: ServicePhase) -> List[ServiceConfiguration]:
        """Get all services from a specific phase"""
        with self.lock:
            return [config for config in self.services.values() if config.phase == phase]

    def enable_service(self, service_name: str) -> bool:
        """Enable a service"""
        with self.lock:
            if service_name not in self.services:
                return False
            self.services[service_name].enabled = True
            self.health_status[service_name].status = ServiceHealth.HEALTHY
            logger.info(f"Service {service_name} enabled")
            return True

    def disable_service(self, service_name: str) -> bool:
        """Disable a service"""
        with self.lock:
            if service_name not in self.services:
                return False
            self.services[service_name].enabled = False
            self.health_status[service_name].status = ServiceHealth.OFFLINE
            logger.info(f"Service {service_name} disabled")
            return True

    def register_health_callback(self, callback: Callable[[str, ServiceHealth], None]) -> None:
        """Register a callback for health status changes"""
        with self.lock:
            self.health_callbacks.append(callback)

    def _recalculate_metrics(self) -> None:
        """Recalculate integration metrics"""
        self.metrics.total_services = len(self.services)
        self.metrics.healthy_services = sum(1 for h in self.health_status.values() 
                                           if h.status == ServiceHealth.HEALTHY)
        self.metrics.services_with_warnings = sum(1 for h in self.health_status.values() 
                                                 if h.status == ServiceHealth.WARNING)
        self.metrics.critical_services = sum(1 for h in self.health_status.values() 
                                            if h.status == ServiceHealth.CRITICAL)
        self.metrics.offline_services = sum(1 for h in self.health_status.values() 
                                           if h.status == ServiceHealth.OFFLINE)
        
        latencies = [h.endpoint_latency_ms for h in self.health_status.values() 
                    if h.endpoint_latency_ms is not None]
        if latencies:
            self.metrics.average_latency_ms = sum(latencies) / len(latencies)
        
        error_rates = [h.error_rate for h in self.health_status.values()]
        if error_rates:
            self.metrics.error_rate = sum(error_rates) / len(error_rates)
        
        self.metrics.last_updated = datetime.utcnow()


class IntegrationValidator:
    """Validates platform integration and configuration"""

    def __init__(self, registry: ServiceRegistry, mode: IntegrationMode = IntegrationMode.STRICT):
        self.registry = registry
        self.mode = mode
        self.validation_results: Dict[str, tuple[bool, List[str]]] = {}

    def validate_all_services(self) -> tuple[bool, Dict[str, List[str]]]:
        """Validate all services and their dependencies"""
        results = {}
        all_valid = True
        
        for service_name in self.registry.services:
            valid, errors = self.registry.validate_dependencies(service_name)
            results[service_name] = errors
            
            if not valid:
                all_valid = False
                if self.mode == IntegrationMode.STRICT:
                    logger.error(f"Service {service_name} validation failed: {errors}")
                else:
                    logger.warning(f"Service {service_name} validation failed: {errors}")
        
        self.validation_results = {name: (len(errors) == 0, errors) for name, errors in results.items()}
        return all_valid, results

    def validate_startup_order(self) -> List[str]:
        """Generate startup order based on dependency graph"""
        graph = self.registry.get_dependency_graph()
        visited = set()
        order = []
        
        def visit(service: str, visiting: set) -> bool:
            if service in visiting:
                logger.warning(f"Circular dependency detected involving {service}")
                return False
            if service in visited:
                return True
            
            visiting.add(service)
            for dep in graph.get(service, []):
                if not visit(dep, visiting):
                    return False
            visiting.remove(service)
            visited.add(service)
            order.append(service)
            return True
        
        for service in graph:
            if service not in visited:
                visit(service, set())
        
        return order

    def check_version_compatibility(self) -> Dict[str, List[str]]:
        """Check version compatibility across all services"""
        issues = {}
        
        for service_name, config in self.registry.services.items():
            service_issues = []
            for dep in config.dependencies:
                dep_config = self.registry.get_service_config(dep.service_name)
                if dep_config and not dep.is_compatible(dep_config.version):
                    service_issues.append(
                        f"Incompatible {dep.service_name}: {dep_config.version} "
                        f"not in [{dep.min_version}, {dep.max_version}]"
                    )
            if service_issues:
                issues[service_name] = service_issues
        
        return issues

    def get_validation_report(self) -> Dict[str, Any]:
        """Get comprehensive validation report"""
        return {
            "validation_results": self.validation_results,
            "startup_order": self.validate_startup_order(),
            "version_issues": self.check_version_compatibility(),
            "health_report": self.registry.get_health_report(),
            "metrics": self.registry.get_metrics(),
            "timestamp": datetime.utcnow().isoformat()
        }


class ServiceLocator:
    """Service locator pattern for dependency injection"""

    _registry: Optional[ServiceRegistry] = None
    _validator: Optional[IntegrationValidator] = None

    @classmethod
    def initialize(cls, mode: IntegrationMode = IntegrationMode.STRICT) -> ServiceRegistry:
        """Initialize the service locator"""
        if cls._registry is None:
            cls._registry = ServiceRegistry()
            cls._validator = IntegrationValidator(cls._registry, mode)
            logger.info(f"Service locator initialized with mode {mode.value}")
        return cls._registry

    @classmethod
    def get_registry(cls) -> ServiceRegistry:
        """Get the service registry"""
        if cls._registry is None:
            cls.initialize()
        return cls._registry

    @classmethod
    def get_validator(cls) -> IntegrationValidator:
        """Get the integration validator"""
        if cls._validator is None:
            cls.initialize()
        return cls._validator

    @classmethod
    def get_service(cls, service_name: str) -> Optional[Any]:
        """Get a service by name"""
        return cls.get_registry().get_service(service_name)

    @classmethod
    def register_service(cls, config: ServiceConfiguration, instance: Optional[Any] = None) -> bool:
        """Register a service"""
        return cls.get_registry().register_service(config, instance)


# Global service locator singleton
def get_service_registry() -> ServiceRegistry:
    """Get or create the service registry"""
    return ServiceLocator.get_registry()


def get_integration_validator(mode: IntegrationMode = IntegrationMode.STRICT) -> IntegrationValidator:
    """Get or create the integration validator"""
    return ServiceLocator.get_validator()


def register_phase_service(name: str, phase: ServicePhase, version: str,
                          dependencies: Optional[List[ServiceDependency]] = None,
                          instance: Optional[Any] = None,
                          enabled: bool = True,
                          config_params: Optional[Dict] = None) -> bool:
    """Convenience function to register a phase service"""
    config = ServiceConfiguration(
        name=name,
        phase=phase,
        version=version,
        enabled=enabled,
        dependencies=dependencies or [],
        config_params=config_params or {}
    )
    return ServiceLocator.register_service(config, instance)
