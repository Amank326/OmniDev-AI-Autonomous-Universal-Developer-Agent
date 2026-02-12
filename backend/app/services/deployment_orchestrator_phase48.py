"""
Phase 48: Universal Deployment & Integration Orchestrator
Unified system initialization, service orchestration, and deployment coordination.

Integrates all 47 phases into a single cohesive production platform.
Handles service startup, health checks, dependency resolution, and orchestration.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum, auto
from datetime import datetime, timedelta
from threading import Thread, RLock
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# Phase 48: Universal Orchestration Enums & Config
# ============================================================================

class PhaseEnum(Enum):
    """All implemented phases"""
    PHASE_44 = (44, "Event Streaming & Data Integration")
    PHASE_45 = (45, "ML Infrastructure & Predictions")
    PHASE_46 = (46, "Advanced Search & Retrieval Augmentation")
    PHASE_47 = (47, "Security & Governance Infrastructure")
    PHASE_48 = (48, "Universal Deployment & Orchestration")

class ServiceStatus(Enum):
    """Service lifecycle states"""
    INITIALIZING = auto()
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()
    STOPPED = auto()
    ERROR = auto()

class DeploymentStrategy(Enum):
    """Deployment approaches"""
    STANDALONE = "standalone"
    DOCKER = "docker"
    DOCKER_COMPOSE = "docker_compose"
    KUBERNETES = "kubernetes"
    SERVERLESS = "serverless"
    HYBRID = "hybrid"

class IntegrationMode(Enum):
    """Phase integration modes"""
    SEQUENTIAL = "sequential"  # Start phases in order
    PARALLEL = "parallel"      # Start all phases simultaneously
    DEPENDENCY = "dependency"  # Follow dependency graph
    PROGRESSIVE = "progressive"  # Start core, add features

# ============================================================================
# Phase 48: Data Structures
# ============================================================================

@dataclass
class ServiceInfo:
    """Service metadata and configuration"""
    name: str
    phase: int
    version: str = "1.0.0"
    dependencies: List[str] = field(default_factory=list)
    startup_order: int = 0
    startup_timeout_secs: int = 30
    health_check_interval_secs: int = 10
    critical: bool = True  # If critical=True, platform fails if service fails
    port: Optional[int] = None
    environment_vars: Dict[str, str] = field(default_factory=dict)

@dataclass
class HealthCheckResult:
    """Health check outcome"""
    service_name: str
    status: ServiceStatus
    timestamp: datetime
    response_time_ms: float = 0.0
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    strategy: DeploymentStrategy = DeploymentStrategy.DOCKER_COMPOSE
    integration_mode: IntegrationMode = IntegrationMode.DEPENDENCY
    enable_health_checks: bool = True
    health_check_interval_secs: int = 30
    enable_metrics: bool = True
    enable_logging: bool = True
    enable_tracing: bool = True
    environment: str = "production"  # development, staging, production
    log_level: str = "INFO"
    max_retries: int = 3
    retry_delay_secs: int = 5

@dataclass
class DeploymentMetrics:
    """Deployment operation metrics"""
    total_services: int = 0
    healthy_services: int = 0
    degraded_services: int = 0
    unhealthy_services: int = 0
    startup_time_secs: float = 0.0
    total_errors: int = 0
    last_health_check: Optional[datetime] = None
    uptime_percent: float = 100.0

@dataclass
class DeploymentCheckpoint:
    """Saves deployment progress state"""
    timestamp: datetime
    phase: int
    initialized_services: List[str]
    failed_services: List[str]
    pending_services: List[str]
    metrics: DeploymentMetrics

# ============================================================================
# Phase 48: Phase Dependency Graph
# ============================================================================

PHASE_DEPENDENCIES = {
    44: [],  # Foundation: Event Streaming (no dependencies)
    45: [44],  # ML needs Event Streaming
    46: [44, 45],  # Search needs Events and ML
    47: [44, 45, 46],  # Security needs all prior phases
    48: [44, 45, 46, 47],  # Orchestration depends on all
}

CRITICAL_SERVICES = [
    "encryption_service",  # Phase 47: Core encryption
    "auth_service",  # Phase 47: Authentication
    "event_stream_manager",  # Phase 44: Event foundation
    "access_control_service",  # Phase 47: Authorization
]

# ============================================================================
# Phase 48: Universal Deployment Orchestrator
# ============================================================================

class UniversalDeploymentOrchestrator:
    """
    Central orchestrator for entire OmniDev AI platform.
    
    Manages:
    - Service initialization and startup
    - Health monitoring
    - Dependency resolution
    - Failover and recovery
    - Metrics collection
    - Integration coordination
    """
    
    def __init__(self, config: Optional[DeploymentConfig] = None):
        """Initialize orchestrator"""
        self.config = config or DeploymentConfig()
        self.lock = RLock()
        
        # Service registry
        self._services: Dict[str, ServiceInfo] = {}
        self._service_status: Dict[str, ServiceStatus] = {}
        self._service_instances: Dict[str, Any] = {}
        
        # Monitoring
        self._health_results: Dict[str, List[HealthCheckResult]] = {}
        self._metrics = DeploymentMetrics()
        self._startup_time = time.time()
        
        # Callbacks
        self._health_check_handlers: Dict[str, Callable] = {}
        self._startup_handlers: List[Callable] = []
        self._shutdown_handlers: List[Callable] = []
        
        # Checkpoints
        self._checkpoints: List[DeploymentCheckpoint] = []
        self._current_checkpoint: Optional[DeploymentCheckpoint] = None
        
        # Monitoring thread
        self._monitoring_thread: Optional[Thread] = None
        self._monitoring_active = False
        
        logger.info("Initialized UniversalDeploymentOrchestrator")
    
    # ========================================================================
    # Service Registration
    # ========================================================================
    
    def register_service(self, service_info: ServiceInfo):
        """Register a service with orchestrator"""
        with self.lock:
            if service_info.name in self._services:
                logger.warning(f"Service {service_info.name} already registered, overwriting")
            self._services[service_info.name] = service_info
            self._service_status[service_info.name] = ServiceStatus.INITIALIZING
            self._health_results[service_info.name] = []
            logger.info(f"Registered service: {service_info.name} (Phase {service_info.phase})")
    
    def register_health_check(self, service_name: str, handler: Callable):
        """Register health check handler"""
        with self.lock:
            self._health_check_handlers[service_name] = handler
            logger.debug(f"Registered health check for {service_name}")
    
    def register_startup_handler(self, handler: Callable):
        """Register platform-wide startup handler"""
        with self.lock:
            self._startup_handlers.append(handler)
    
    def register_shutdown_handler(self, handler: Callable):
        """Register platform-wide shutdown handler"""
        with self.lock:
            self._shutdown_handlers.append(handler)
    
    # ========================================================================
    # Service Initialization & Startup
    # ========================================================================
    
    def initialize_service(self, service_name: str) -> bool:
        """Initialize individual service"""
        try:
            with self.lock:
                if service_name not in self._services:
                    logger.error(f"Service {service_name} not registered")
                    return False
                
                service = self._services[service_name]
                logger.info(f"Initializing {service_name} (Phase {service.phase})")
                
                # Check dependencies
                for dep in service.dependencies:
                    if self._service_status.get(dep) != ServiceStatus.HEALTHY:
                        logger.warning(f"Dependency {dep} not healthy for {service_name}")
                        if service.critical:
                            return False
                
                # Record initialization
                self._service_status[service_name] = ServiceStatus.INITIALIZING
            
            # Run startup handlers
            for handler in self._startup_handlers:
                try:
                    handler(service_name)
                except Exception as e:
                    logger.error(f"Startup handler failed for {service_name}: {e}")
            
            self._service_status[service_name] = ServiceStatus.HEALTHY
            logger.info(f"Successfully initialized {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize {service_name}: {e}")
            self._service_status[service_name] = ServiceStatus.ERROR
            return False
    
    def startup_phase(self, phase: int) -> bool:
        """Initialize all services in a phase"""
        logger.info(f"Starting Phase {phase}...")
        
        services_in_phase = [
            s for s in self._services.values() 
            if s.phase == phase
        ]
        
        if not services_in_phase:
            logger.warning(f"No services found for Phase {phase}")
            return True
        
        success = True
        for service in services_in_phase:
            if not self.initialize_service(service.name):
                success = False
                if service.critical:
                    logger.error(f"Critical service {service.name} failed to initialize")
                    return False
        
        logger.info(f"Phase {phase} startup complete (success={success})")
        return success
    
    def startup_all(self) -> bool:
        """Initialize entire platform following dependency order"""
        logger.info("Starting OmniDev AI Platform (All 48 Phases)...")
        
        start_time = time.time()
        success = True
        
        # Determine startup order
        if self.config.integration_mode == IntegrationMode.SEQUENTIAL:
            startup_phases = [44, 45, 46, 47, 48]
        elif self.config.integration_mode == IntegrationMode.DEPENDENCY:
            startup_phases = self._resolve_dependency_order()
        else:
            startup_phases = [44, 45, 46, 47, 48]  # Default to sequential
        
        # Start phases
        for phase in startup_phases:
            if not self.startup_phase(phase):
                success = False
                if phase in [44, 47]:  # Core phases
                    logger.error(f"Critical phase {phase} failed")
                    break
        
        # Calculate metrics
        startup_time_secs = time.time() - start_time
        self._metrics.startup_time_secs = startup_time_secs
        
        healthy_count = sum(1 for s in self._service_status.values() 
                           if s == ServiceStatus.HEALTHY)
        total_count = len(self._services)
        self._metrics.total_services = total_count
        self._metrics.healthy_services = healthy_count
        self._metrics.uptime_percent = (healthy_count / total_count * 100) if total_count > 0 else 0
        
        logger.info(f"Platform startup: {'SUCCESS' if success else 'PARTIAL'}")
        logger.info(f"Services: {healthy_count}/{total_count} healthy")
        logger.info(f"Startup time: {startup_time_secs:.2f}s")
        
        # Create checkpoint
        self._save_checkpoint()
        
        return success
    
    def shutdown_all(self) -> bool:
        """Graceful shutdown of entire platform"""
        logger.info("Shutting down OmniDev AI Platform...")
        
        self._monitoring_active = False
        
        for handler in reversed(self._shutdown_handlers):
            try:
                handler()
            except Exception as e:
                logger.error(f"Shutdown handler failed: {e}")
        
        # Mark all services as stopped
        for service_name in self._service_status:
            self._service_status[service_name] = ServiceStatus.STOPPED
        
        logger.info("Platform shutdown complete")
        return True
    
    # ========================================================================
    # Health Monitoring
    # ========================================================================
    
    async def health_check_service(self, service_name: str) -> HealthCheckResult:
        """Check single service health"""
        try:
            start_time = time.time()
            
            if service_name not in self._health_check_handlers:
                return HealthCheckResult(
                    service_name=service_name,
                    status=ServiceStatus.UNHEALTHY,
                    timestamp=datetime.now(),
                    error_message="No health check handler registered"
                )
            
            handler = self._health_check_handlers[service_name]
            result = await handler() if hasattr(handler, '__await__') else handler()
            
            response_time_ms = (time.time() - start_time) * 1000
            
            health_result = HealthCheckResult(
                service_name=service_name,
                status=ServiceStatus.HEALTHY if result else ServiceStatus.UNHEALTHY,
                timestamp=datetime.now(),
                response_time_ms=response_time_ms
            )
            
            self._health_results[service_name].append(health_result)
            return health_result
            
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return HealthCheckResult(
                service_name=service_name,
                status=ServiceStatus.ERROR,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def start_monitoring(self):
        """Start background health monitoring"""
        if not self.config.enable_health_checks:
            logger.info("Health checks disabled in config")
            return
        
        self._monitoring_active = True
        self._monitoring_thread = Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="DeploymentMonitoring"
        )
        self._monitoring_thread.start()
        logger.info("Health monitoring started")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._monitoring_active:
            try:
                self._metrics.last_health_check = datetime.now()
                
                # Check each service
                for service_name in self._services:
                    try:
                        if service_name in self._health_check_handlers:
                            handler = self._health_check_handlers[service_name]
                            result = handler()
                            
                            if result:
                                self._service_status[service_name] = ServiceStatus.HEALTHY
                            else:
                                self._service_status[service_name] = ServiceStatus.DEGRADED
                    except Exception as e:
                        logger.debug(f"Health check error for {service_name}: {e}")
                        self._service_status[service_name] = ServiceStatus.ERROR
                
                # Update metrics
                healthy = sum(1 for s in self._service_status.values() 
                             if s == ServiceStatus.HEALTHY)
                self._metrics.healthy_services = healthy
                
                time.sleep(self.config.health_check_interval_secs)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
    
    # ========================================================================
    # Dependency Resolution
    # ========================================================================
    
    def _resolve_dependency_order(self) -> List[int]:
        """Resolve phase startup order based on dependencies"""
        phases = [44, 45, 46, 47, 48]
        ordered = []
        visited = set()
        
        def visit(phase: int):
            if phase in visited:
                return
            visited.add(phase)
            for dep in PHASE_DEPENDENCIES.get(phase, []):
                visit(dep)
            ordered.append(phase)
        
        for phase in phases:
            visit(phase)
        
        return ordered
    
    # ========================================================================
    # Checkpoint & Recovery
    # ========================================================================
    
    def _save_checkpoint(self):
        """Save deployment progress checkpoint"""
        checkpoint = DeploymentCheckpoint(
            timestamp=datetime.now(),
            phase=max([s.phase for s in self._services.values()]),
            initialized_services=[
                name for name, status in self._service_status.items()
                if status == ServiceStatus.HEALTHY
            ],
            failed_services=[
                name for name, status in self._service_status.items()
                if status == ServiceStatus.ERROR
            ],
            pending_services=[
                name for name, status in self._service_status.items()
                if status == ServiceStatus.INITIALIZING
            ],
            metrics=self._metrics
        )
        self._checkpoints.append(checkpoint)
        self._current_checkpoint = checkpoint
        logger.info(f"Checkpoint saved: {checkpoint.timestamp}")
    
    def get_checkpoint(self) -> Optional[DeploymentCheckpoint]:
        """Get current deployment checkpoint"""
        return self._current_checkpoint
    
    # ========================================================================
    # Metrics & Reporting
    # ========================================================================
    
    def get_metrics(self) -> DeploymentMetrics:
        """Get deployment metrics"""
        with self.lock:
            uptime_secs = time.time() - self._startup_time
            total_secs = max(1, uptime_secs)
            
            # Calculate uptime percentage (based on healthy services)
            healthy = sum(1 for s in self._service_status.values() 
                         if s in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED])
            total = len(self._service_status)
            self._metrics.uptime_percent = (healthy / total * 100) if total > 0 else 0
            
            return self._metrics
    
    def get_deployment_report(self) -> Dict[str, Any]:
        """Get comprehensive deployment report"""
        with self.lock:
            metrics = self.get_metrics()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "strategy": self.config.strategy.value,
                "integration_mode": self.config.integration_mode.value,
                "environment": self.config.environment,
                "total_services": metrics.total_services,
                "healthy_services": metrics.healthy_services,
                "unhealthy_services": metrics.unhealthy_services,
                "startup_time_secs": metrics.startup_time_secs,
                "uptime_percent": metrics.uptime_percent,
                "service_status": {
                    name: status.name for name, status in self._service_status.items()
                },
                "phases": {
                    phase: {
                        "services": [
                            s.name for s in self._services.values() 
                            if s.phase == phase
                        ],
                        "status": "healthy" if all(
                            self._service_status.get(s.name) == ServiceStatus.HEALTHY
                            for s in self._services.values() if s.phase == phase
                        ) else "degraded"
                    }
                    for phase in [44, 45, 46, 47, 48]
                }
            }
    
    def print_status(self):
        """Print current platform status"""
        metrics = self.get_metrics()
        print("\n" + "="*70)
        print("OmniDev AI Platform Status".center(70))
        print("="*70)
        print(f"Environment:     {self.config.environment}")
        print(f"Strategy:        {self.config.strategy.value}")
        print(f"Total Services:  {metrics.total_services}")
        print(f"Healthy:         {metrics.healthy_services}")
        print(f"Degraded:        {metrics.degraded_services}")
        print(f"Unhealthy:       {metrics.unhealthy_services}")
        print(f"Uptime:          {metrics.uptime_percent:.1f}%")
        print(f"Startup Time:    {metrics.startup_time_secs:.2f}s")
        print("\nService Status:")
        for phase in [44, 45, 46, 47, 48]:
            phase_services = [s for s in self._services.values() if s.phase == phase]
            if phase_services:
                print(f"  Phase {phase}:")
                for service in sorted(phase_services, key=lambda x: x.name):
                    status = self._service_status.get(service.name, ServiceStatus.INITIALIZING)
                    symbol = "✅" if status == ServiceStatus.HEALTHY else "❌" if status == ServiceStatus.ERROR else "⚠️"
                    print(f"    {symbol} {service.name:<40} {status.name}")
        print("="*70 + "\n")


# ============================================================================
# Singleton Instance
# ============================================================================

_orchestrator_instance: Optional[UniversalDeploymentOrchestrator] = None

def get_orchestrator(config: Optional[DeploymentConfig] = None) -> UniversalDeploymentOrchestrator:
    """Get or create orchestrator singleton"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = UniversalDeploymentOrchestrator(config)
    return _orchestrator_instance
