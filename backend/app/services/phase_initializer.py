"""
Phase 48: Service Initialization Configuration
=========================================================
Centralized configuration and initialization for all Phase 44-47 services
Bootstraps the entire security, governance, and monitoring infrastructure
"""

import logging
from typing import Dict, Any, Optional
from app.services.service_registry import ServiceRegistry, ServiceTier
from app.services.health_monitor import HealthMonitor

logger = logging.getLogger(__name__)


class PhaseServiceInitializer:
    """
    Initializes all services from Phases 44-47 in correct order
    Manages dependencies, health checks, and lifecycle
    """

    def __init__(self):
        self.registry = ServiceRegistry()
        self.health_monitor = HealthMonitor(check_interval_seconds=30)
        self.initialized = False

    def initialize_all_phases(self) -> Dict[str, bool]:
        """Initialize all services from Phases 44-47"""
        logger.info("=" * 80)
        logger.info("OMNIDEV AI - Phase 44-47 Service Initialization")
        logger.info("=" * 80)

        # Register all Phase 44 services (Event & Data Infrastructure)
        self._register_phase_44_services()

        # Register all Phase 45 services (ML & Predictions)
        self._register_phase_45_services()

        # Register all Phase 46 services (Advanced Search & Retrieval)
        self._register_phase_46_services()

        # Register all Phase 47 services (Security & Governance)
        self._register_phase_47_services()

        # Initialize all services
        logger.info("\nInitializing services...")
        results = self.registry.initialize_all()

        # Start health monitoring
        logger.info("\nStarting health monitoring...")
        self.health_monitor.start_monitoring()

        # Print initialization summary
        self._print_initialization_summary(results)

        self.initialized = True
        return results

    def _register_phase_44_services(self) -> None:
        """Register Phase 44: Event & Data Infrastructure"""
        logger.info("\nRegistering Phase 44 services (Event & Data Infrastructure)...")

        # Event Stream Manager
        self.registry.register_service(
            service_id="event_stream_manager",
            service_name="Event Stream Manager",
            phase=44,
            tier=ServiceTier.CRITICAL,
            description="Real-time event streaming and distribution",
            dependencies=[]
        )

        # Data Pipeline Manager
        self.registry.register_service(
            service_id="data_pipeline_manager",
            service_name="Data Pipeline Manager",
            phase=44,
            tier=ServiceTier.CRITICAL,
            description="Data ingestion, transformation, and orchestration",
            dependencies=[]
        )

        # Time Series Engine
        self.registry.register_service(
            service_id="time_series_engine",
            service_name="Time Series Engine",
            phase=44,
            tier=ServiceTier.HIGH,
            description="Time series data storage and analysis",
            dependencies=["data_pipeline_manager"]
        )

        # Distributed Cache
        self.registry.register_service(
            service_id="distributed_cache",
            service_name="Distributed Cache",
            phase=44,
            tier=ServiceTier.HIGH,
            description="Distributed caching for performance optimization",
            dependencies=[]
        )

        # Message Queue System
        self.registry.register_service(
            service_id="message_queue",
            service_name="Message Queue System",
            phase=44,
            tier=ServiceTier.CRITICAL,
            description="Asynchronous message processing",
            dependencies=[]
        )

        # Data Warehouse
        self.registry.register_service(
            service_id="data_warehouse",
            service_name="Data Warehouse",
            phase=44,
            tier=ServiceTier.HIGH,
            description="Centralized data storage and analytics",
            dependencies=["data_pipeline_manager"]
        )

        # Stream Processing
        self.registry.register_service(
            service_id="stream_processor",
            service_name="Stream Processing Engine",
            phase=44,
            tier=ServiceTier.HIGH,
            description="Real-time stream processing and analytics",
            dependencies=["event_stream_manager", "message_queue"]
        )

        # Data Governance
        self.registry.register_service(
            service_id="data_governance",
            service_name="Data Governance Service",
            phase=44,
            tier=ServiceTier.MEDIUM,
            description="Data quality, lineage, and compliance",
            dependencies=["data_pipeline_manager", "data_warehouse"]
        )

        logger.info("✓ Phase 44 services registered (8 services)")

    def _register_phase_45_services(self) -> None:
        """Register Phase 45: ML & Predictions"""
        logger.info("\nRegistering Phase 45 services (ML & Predictions)...")

        # ML Pipeline Orchestrator
        self.registry.register_service(
            service_id="ml_pipeline_orchestrator",
            service_name="ML Pipeline Orchestrator",
            phase=45,
            tier=ServiceTier.CRITICAL,
            description="Machine learning pipeline management",
            dependencies=["data_pipeline_manager"]
        )

        # Model Training Engine
        self.registry.register_service(
            service_id="model_training_engine",
            service_name="Model Training Engine",
            phase=45,
            tier=ServiceTier.HIGH,
            description="Training and optimization of ML models",
            dependencies=["ml_pipeline_orchestrator", "data_warehouse"]
        )

        # Feature Engineering
        self.registry.register_service(
            service_id="feature_engineering",
            service_name="Feature Engineering Service",
            phase=45,
            tier=ServiceTier.HIGH,
            description="Feature creation and selection",
            dependencies=["data_warehouse"]
        )

        # Model Inference Engine
        self.registry.register_service(
            service_id="model_inference_engine",
            service_name="Model Inference Engine",
            phase=45,
            tier=ServiceTier.CRITICAL,
            description="Real-time model inference and predictions",
            dependencies=["ml_pipeline_orchestrator"]
        )

        # Model Registry & Versioning
        self.registry.register_service(
            service_id="model_registry",
            service_name="Model Registry",
            phase=45,
            tier=ServiceTier.HIGH,
            description="Model storage, versioning, and deployment",
            dependencies=[]
        )

        # Prediction Service
        self.registry.register_service(
            service_id="prediction_service",
            service_name="Prediction Service",
            phase=45,
            tier=ServiceTier.HIGH,
            description="High-level prediction API",
            dependencies=["model_inference_engine", "model_registry"]
        )

        # ML Monitoring & Evaluation
        self.registry.register_service(
            service_id="ml_monitoring",
            service_name="ML Monitoring Service",
            phase=45,
            tier=ServiceTier.MEDIUM,
            description="Model performance monitoring and drift detection",
            dependencies=["model_inference_engine"]
        )

        # Experiment Tracking
        self.registry.register_service(
            service_id="experiment_tracking",
            service_name="Experiment Tracking Service",
            phase=45,
            tier=ServiceTier.MEDIUM,
            description="ML experiment tracking and comparison",
            dependencies=["model_training_engine"]
        )

        logger.info("✓ Phase 45 services registered (8 services)")

    def _register_phase_46_services(self) -> None:
        """Register Phase 46: Advanced Search & Retrieval"""
        logger.info("\nRegistering Phase 46 services (Advanced Search & Retrieval)...")

        # Full-Text Search
        self.registry.register_service(
            service_id="full_text_search",
            service_name="Full-Text Search Engine",
            phase=46,
            tier=ServiceTier.HIGH,
            description="Advanced full-text search capabilities",
            dependencies=["data_warehouse"]
        )

        # Vector Search Engine
        self.registry.register_service(
            service_id="vector_search",
            service_name="Vector Search Engine",
            phase=46,
            tier=ServiceTier.HIGH,
            description="Semantic search using embeddings",
            dependencies=["distributed_cache"]
        )

        # Knowledge Base
        self.registry.register_service(
            service_id="knowledge_base",
            service_name="Knowledge Base",
            phase=46,
            tier=ServiceTier.HIGH,
            description="Centralized knowledge repository",
            dependencies=["data_warehouse", "vector_search"]
        )

        # RAG System
        self.registry.register_service(
            service_id="rag_system",
            service_name="RAG System",
            phase=46,
            tier=ServiceTier.HIGH,
            description="Retrieval-Augmented Generation",
            dependencies=["knowledge_base", "model_inference_engine"]
        )

        # Document Ingestion
        self.registry.register_service(
            service_id="document_ingestion",
            service_name="Document Ingestion Service",
            phase=46,
            tier=ServiceTier.MEDIUM,
            description="Document parsing and indexing",
            dependencies=["knowledge_base"]
        )

        # Semantic Understanding
        self.registry.register_service(
            service_id="semantic_analyzer",
            service_name="Semantic Analyzer",
            phase=46,
            tier=ServiceTier.MEDIUM,
            description="Understanding semantic relationships",
            dependencies=["model_inference_engine"]
        )

        # Search Analytics
        self.registry.register_service(
            service_id="search_analytics",
            service_name="Search Analytics Service",
            phase=46,
            tier=ServiceTier.MEDIUM,
            description="Search performance and user insights",
            dependencies=["full_text_search", "vector_search"]
        )

        # Query Optimizer
        self.registry.register_service(
            service_id="query_optimizer",
            service_name="Query Optimizer",
            phase=46,
            tier=ServiceTier.MEDIUM,
            description="Query optimization and rewriting",
            dependencies=["full_text_search"]
        )

        logger.info("✓ Phase 46 services registered (8 services)")

    def _register_phase_47_services(self) -> None:
        """Register Phase 47: Security & Governance"""
        logger.info("\nRegistering Phase 47 services (Security & Governance)...")

        # Encryption Service
        self.registry.register_service(
            service_id="encryption_service",
            service_name="Encryption Service",
            phase=47,
            tier=ServiceTier.CRITICAL,
            description="Data encryption, key management, and signing",
            dependencies=[]
        )

        # Authentication Service
        self.registry.register_service(
            service_id="auth_service",
            service_name="Authentication Service",
            phase=47,
            tier=ServiceTier.CRITICAL,
            description="User authentication, JWT, OAuth2, MFA",
            dependencies=["encryption_service"]
        )

        # Audit Logger
        self.registry.register_service(
            service_id="audit_logger",
            service_name="Audit Logger",
            phase=47,
            tier=ServiceTier.CRITICAL,
            description="Immutable audit trail logging",
            dependencies=[]
        )

        # Compliance Checker
        self.registry.register_service(
            service_id="compliance_checker",
            service_name="Compliance Checker",
            phase=47,
            tier=ServiceTier.HIGH,
            description="Compliance verification for multiple frameworks",
            dependencies=["encryption_service", "auth_service", "audit_logger"]
        )

        # Governance Engine
        self.registry.register_service(
            service_id="governance_engine",
            service_name="Governance Engine",
            phase=47,
            tier=ServiceTier.HIGH,
            description="Policy management and governance workflows",
            dependencies=["audit_logger"]
        )

        # Access Control Service
        self.registry.register_service(
            service_id="access_control_service",
            service_name="Access Control Service",
            phase=47,
            tier=ServiceTier.CRITICAL,
            description="RBAC/ABAC authorization and access decisions",
            dependencies=["audit_logger", "encryption_service"]
        )

        # Security Monitor
        self.registry.register_service(
            service_id="security_monitor",
            service_name="Security Monitor",
            phase=47,
            tier=ServiceTier.HIGH,
            description="Threat detection, incident response",
            dependencies=["audit_logger"]
        )

        # Service Registry (Phase 48)
        self.registry.register_service(
            service_id="service_registry",
            service_name="Service Registry",
            phase=48,
            tier=ServiceTier.CRITICAL,
            description="Central registry for all services",
            dependencies=[]
        )

        logger.info("✓ Phase 47 services registered (7 services)")

    def _print_initialization_summary(self, results: Dict[str, bool]) -> None:
        """Print initialization summary"""
        successful = sum(1 for v in results.values() if v)
        failed = len(results) - successful

        logger.info("\n" + "=" * 80)
        logger.info("Service Initialization Summary")
        logger.info("=" * 80)

        # By phase
        phases = {}
        for service_id, service_info in self.registry.get_all_services().items():
            phase = service_info.phase
            if phase not in phases:
                phases[phase] = {"total": 0, "successful": 0}
            phases[phase]["total"] += 1
            if results.get(service_id, False):
                phases[phase]["successful"] += 1

        for phase in sorted(phases.keys()):
            phase_data = phases[phase]
            status = "✓" if phase_data["successful"] == phase_data["total"] else "✗"
            logger.info(f"{status} Phase {phase}: {phase_data['successful']}/{phase_data['total']} services initialized")

        logger.info("\n" + "-" * 80)
        logger.info(f"Total: {successful}/{len(results)} services initialized successfully")

        if failed > 0:
            logger.warning(f"Failed services: {failed}")
            for service_id, success in results.items():
                if not success:
                    service_info = self.registry.get_service_info(service_id)
                    logger.warning(f"  - {service_id}: {service_info.metrics.last_error}")

        logger.info("=" * 80 + "\n")

    def get_registry(self) -> ServiceRegistry:
        """Get the service registry"""
        return self.registry

    def get_health_monitor(self) -> HealthMonitor:
        """Get the health monitor"""
        return self.health_monitor

    def get_initialization_status(self) -> Dict[str, Any]:
        """Get current initialization status"""
        return {
            "initialized": self.initialized,
            "registry_status": self.registry.get_registry_status(),
            "health_status": self.health_monitor.get_overall_status()
        }


# Singleton instance
_initializer = None


def get_initializer() -> PhaseServiceInitializer:
    """Get or create the phase service initializer"""
    global _initializer
    if _initializer is None:
        _initializer = PhaseServiceInitializer()
    return _initializer


def initialize_all_services() -> Dict[str, bool]:
    """Initialize all services"""
    initializer = get_initializer()
    return initializer.initialize_all_phases()
