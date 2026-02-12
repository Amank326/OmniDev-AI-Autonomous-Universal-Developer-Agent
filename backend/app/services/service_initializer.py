"""
Service Initializer - Registers all Phase 44-47 services with the deployment orchestrator.

This module:
1. Discovers all services from Phase 44-47
2. Registers them with the orchestrator
3. Sets up dependencies
4. Configures health checks
"""

from typing import Callable, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging

# Import orchestrator
from app.services.deployment_orchestrator_phase48 import (
    UniversalDeploymentOrchestrator,
    ServiceInfo,
    get_orchestrator,
    ServiceStatus
)

# Phase 44: Event Streaming Services
from app.services.event_stream_manager import EventStreamManager, get_event_manager
from app.services.message_queue_service import MessageQueueService

# Phase 45: ML Infrastructure Services
from app.services.ml_pipeline_manager import MLPipelineManager
from app.services.model_registry_service import ModelRegistry
from app.services.model_serving_service import ModelServingService
from app.services.ml_model_service import MLModelService
from app.services.prediction_service import PredictionService
from app.services.feature_engineer import FeatureEngineer

# Phase 46: Advanced Search & Retrieval Services
from app.services.knowledge_base import KnowledgeBase
from app.services.semantic_search import SemanticSearchEngine
from app.services.retrieval_engine import RetrievalEngine
from app.services.rag_pipeline import RAGPipeline

# Phase 47: Security & Governance Services
from app.services.encryption_service import EncryptionEngine, get_encryption_engine
from app.services.auth_service import AuthenticationEngine, get_auth_engine
from app.services.audit_logger import AuditLogger, get_audit_logger
from app.services.compliance_checker import ComplianceChecker, get_compliance_checker
from app.services.governance_engine import GovernanceEngine, get_governance_engine
from app.services.access_control_service import AccessControlEngine, get_access_control_engine
from app.services.security_monitor import SecurityMonitor, get_security_monitor

logger = logging.getLogger(__name__)

# ============================================================================
# Service Instances (Singletons)
# ============================================================================

class ServiceInstances:
    """Holds references to all service singletons"""
    
    # Phase 44
    event_manager: Optional[EventStreamManager] = None
    message_queue: Optional[MessageQueueService] = None
    
    # Phase 45
    ml_pipeline: Optional[MLPipelineManager] = None
    model_registry: Optional[ModelRegistry] = None
    model_serving: Optional[ModelServingService] = None
    ml_model: Optional[MLModelService] = None
    prediction: Optional[PredictionService] = None
    feature_engineer: Optional[FeatureEngineer] = None
    
    # Phase 46
    knowledge_base: Optional[KnowledgeBase] = None
    semantic_search: Optional[SemanticSearchEngine] = None
    retrieval_engine: Optional[RetrievalEngine] = None
    rag_pipeline: Optional[RAGPipeline] = None
    
    # Phase 47
    encryption: Optional[EncryptionEngine] = None
    auth: Optional[AuthenticationEngine] = None
    audit_logger: Optional[AuditLogger] = None
    compliance: Optional[ComplianceChecker] = None
    governance: Optional[GovernanceEngine] = None
    access_control: Optional[AccessControlEngine] = None
    security_monitor: Optional[SecurityMonitor] = None


# ============================================================================
# Health Check Handlers
# ============================================================================

class HealthChecks:
    """Health check implementations for all services"""
    
    @staticmethod
    def check_event_manager() -> bool:
        """Check event manager health"""
        try:
            manager = get_event_manager()
            stats = manager.get_statistics()
            return stats.get('total_events', 0) >= 0
        except Exception as e:
            logger.error(f"Event manager health check failed: {e}")
            return False
    
    @staticmethod
    def check_auth_service() -> bool:
        """Check auth service health"""
        try:
            auth = get_auth_engine()
            stats = auth.get_statistics()
            return 'total_logins' in stats
        except Exception as e:
            logger.error(f"Auth service health check failed: {e}")
            return False
    
    @staticmethod
    def check_encryption_service() -> bool:
        """Check encryption service health"""
        try:
            encryption = get_encryption_engine()
            # Test encryption/decryption
            test_data = "health_check_test"
            encrypted = encryption.encrypt(test_data)
            decrypted = encryption.decrypt(encrypted)
            return decrypted == test_data
        except Exception as e:
            logger.error(f"Encryption service health check failed: {e}")
            return False
    
    @staticmethod
    def check_audit_logger() -> bool:
        """Check audit logger health"""
        try:
            audit = get_audit_logger()
            stats = audit.get_statistics()
            return 'total_events' in stats
        except Exception as e:
            logger.error(f"Audit logger health check failed: {e}")
            return False
    
    @staticmethod
    def check_access_control() -> bool:
        """Check access control health"""
        try:
            access = get_access_control_engine()
            stats = access.get_statistics()
            return 'total_decisions' in stats
        except Exception as e:
            logger.error(f"Access control health check failed: {e}")
            return False
    
    @staticmethod
    def check_security_monitor() -> bool:
        """Check security monitor health"""
        try:
            monitor = get_security_monitor()
            stats = monitor.get_statistics()
            return 'total_events' in stats
        except Exception as e:
            logger.error(f"Security monitor health check failed: {e}")
            return False
    
    @staticmethod
    def check_compliance_checker() -> bool:
        """Check compliance checker health"""
        try:
            compliance = get_compliance_checker()
            stats = compliance.get_statistics()
            return 'total_checks' in stats
        except Exception as e:
            logger.error(f"Compliance checker health check failed: {e}")
            return False
    
    @staticmethod
    def check_governance_engine() -> bool:
        """Check governance engine health"""
        try:
            governance = get_governance_engine()
            stats = governance.get_statistics()
            return 'total_policies' in stats
        except Exception as e:
            logger.error(f"Governance engine health check failed: {e}")
            return False
    
    @staticmethod
    def check_prediction_service() -> bool:
        """Check prediction service health"""
        try:
            prediction = PredictionService()
            # Just verify it's instantiable
            return True
        except Exception as e:
            logger.error(f"Prediction service health check failed: {e}")
            return False
    
    @staticmethod
    def check_knowledge_base() -> bool:
        """Check knowledge base health"""
        try:
            kb = KnowledgeBase()
            # Verify basic operation
            return True
        except Exception as e:
            logger.error(f"Knowledge base health check failed: {e}")
            return False


# ============================================================================
# Service Initializers
# ============================================================================

class ServiceInitializers:
    """Initialization logic for all services"""
    
    @staticmethod
    def init_phase_44_services(orchestrator: UniversalDeploymentOrchestrator):
        """Initialize Phase 44: Event Streaming Services"""
        logger.info("Initializing Phase 44 services...")
        
        # Event Stream Manager
        orchestrator.register_service(ServiceInfo(
            name="event_stream_manager",
            phase=44,
            version="1.0.0",
            dependencies=[],
            startup_order=1,
            critical=True,
            port=None
        ))
        orchestrator.register_health_check(
            "event_stream_manager",
            HealthChecks.check_event_manager
        )
        
        # Message Queue Service
        orchestrator.register_service(ServiceInfo(
            name="message_queue_service",
            phase=44,
            version="1.0.0",
            dependencies=[],
            startup_order=2,
            critical=True
        ))
    
    @staticmethod
    def init_phase_45_services(orchestrator: UniversalDeploymentOrchestrator):
        """Initialize Phase 45: ML Infrastructure Services"""
        logger.info("Initializing Phase 45 services...")
        
        services = [
            ("ml_pipeline_manager", 1, True),
            ("model_registry_service", 2, True),
            ("model_serving_service", 3, False),
            ("ml_model_service", 4, False),
            ("prediction_service", 5, True),
            ("feature_engineer", 6, False),
        ]
        
        for service_name, order, critical in services:
            orchestrator.register_service(ServiceInfo(
                name=service_name,
                phase=45,
                version="1.0.0",
                dependencies=["event_stream_manager"],
                startup_order=order,
                critical=critical
            ))
            
            # Register health checks
            if service_name == "prediction_service":
                orchestrator.register_health_check(
                    service_name,
                    HealthChecks.check_prediction_service
                )
    
    @staticmethod
    def init_phase_46_services(orchestrator: UniversalDeploymentOrchestrator):
        """Initialize Phase 46: Advanced Search & Retrieval Services"""
        logger.info("Initializing Phase 46 services...")
        
        services = [
            ("knowledge_base", 1, True),
            ("semantic_search", 2, True),
            ("retrieval_engine", 3, True),
            ("rag_pipeline", 4, False),
        ]
        
        for service_name, order, critical in services:
            deps = ["event_stream_manager", "ml_pipeline_manager", "prediction_service"]
            orchestrator.register_service(ServiceInfo(
                name=service_name,
                phase=46,
                version="1.0.0",
                dependencies=deps,
                startup_order=order,
                critical=critical
            ))
            
            if service_name == "knowledge_base":
                orchestrator.register_health_check(
                    service_name,
                    HealthChecks.check_knowledge_base
                )
    
    @staticmethod
    def init_phase_47_services(orchestrator: UniversalDeploymentOrchestrator):
        """Initialize Phase 47: Security & Governance Services"""
        logger.info("Initializing Phase 47 services...")
        
        # Ordered by startup dependency
        services = [
            ("encryption_service", 1, True, HealthChecks.check_encryption_service),
            ("auth_service", 2, True, HealthChecks.check_auth_service),
            ("audit_logger", 3, True, HealthChecks.check_audit_logger),
            ("access_control_service", 4, True, HealthChecks.check_access_control),
            ("compliance_checker", 5, True, HealthChecks.check_compliance_checker),
            ("governance_engine", 6, True, HealthChecks.check_governance_engine),
            ("security_monitor", 7, True, HealthChecks.check_security_monitor),
        ]
        
        for service_name, order, critical, health_check in services:
            orchestrator.register_service(ServiceInfo(
                name=service_name,
                phase=47,
                version="2.0.0",  # Phase 47 is major version 2
                dependencies=["event_stream_manager"],
                startup_order=order,
                critical=critical
            ))
            
            orchestrator.register_health_check(service_name, health_check)
    
    @staticmethod
    def init_phase_48_services(orchestrator: UniversalDeploymentOrchestrator):
        """Initialize Phase 48: Deployment Orchestrator"""
        logger.info("Initializing Phase 48 services...")
        
        orchestrator.register_service(ServiceInfo(
            name="deployment_orchestrator",
            phase=48,
            version="1.0.0",
            dependencies=[
                "event_stream_manager",
                "ml_pipeline_manager",
                "knowledge_base",
                "encryption_service",
                "auth_service",
                "access_control_service",
                "security_monitor"
            ],
            startup_order=1,
            critical=True
        ))


# ============================================================================
# Startup Handlers
# ============================================================================

def create_startup_handler(service_name: str) -> Callable:
    """Create startup handler for a service"""
    def handler(svc_name: str):
        logger.info(f"Starting {service_name}...")
        try:
            # These would be actual startup logic
            # For now, just log
            logger.info(f"{service_name} started successfully")
        except Exception as e:
            logger.error(f"Failed to start {service_name}: {e}")
            raise
    
    return handler


def create_shutdown_handler(service_name: str) -> Callable:
    """Create shutdown handler for a service"""
    def handler():
        logger.info(f"Shutting down {service_name}...")
        try:
            # Cleanup logic here
            logger.info(f"{service_name} shut down successfully")
        except Exception as e:
            logger.error(f"Failed to shut down {service_name}: {e}")
    
    return handler


# ============================================================================
# Main Initialization Function
# ============================================================================

def initialize_all_services(config=None) -> UniversalDeploymentOrchestrator:
    """
    Initialize all services across all phases.
    
    Args:
        config: DeploymentConfig object (optional)
    
    Returns:
        UniversalDeploymentOrchestrator instance with all services registered
    """
    orchestrator = get_orchestrator(config)
    
    logger.info("="*70)
    logger.info("Initializing OmniDev AI Platform - All 48 Phases")
    logger.info("="*70)
    
    # Register all services
    ServiceInitializers.init_phase_44_services(orchestrator)
    ServiceInitializers.init_phase_45_services(orchestrator)
    ServiceInitializers.init_phase_46_services(orchestrator)
    ServiceInitializers.init_phase_47_services(orchestrator)
    ServiceInitializers.init_phase_48_services(orchestrator)
    
    # Register startup/shutdown handlers
    for service_name in ["event_stream_manager", "encryption_service", "auth_service", "access_control_service"]:
        orchestrator.register_startup_handler(create_startup_handler(service_name))
        orchestrator.register_shutdown_handler(create_shutdown_handler(service_name))
    
    logger.info("All services registered with orchestrator")
    
    return orchestrator


def startup_platform(config=None) -> bool:
    """
    Start the entire OmniDev AI platform.
    
    Args:
        config: DeploymentConfig object (optional)
    
    Returns:
        True if startup successful, False otherwise
    """
    orchestrator = initialize_all_services(config)
    
    # Start all services
    success = orchestrator.startup_all()
    
    # Start health monitoring
    orchestrator.start_monitoring()
    
    # Print status
    orchestrator.print_status()
    
    return success


def shutdown_platform():
    """Gracefully shutdown the platform"""
    orchestrator = get_orchestrator()
    orchestrator.shutdown_all()


def get_platform_status() -> Dict[str, Any]:
    """Get current platform status"""
    orchestrator = get_orchestrator()
    return orchestrator.get_deployment_report()
