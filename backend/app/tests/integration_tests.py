"""
Integration Test Suite
Comprehensive testing for Phase 40 integration across all platform phases
"""

import pytest
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict

from backend.app.services.integration_config import (
    ServiceRegistry, ServiceConfiguration, ServiceDependency,
    ServiceHealthStatus, ServiceHealth, ServicePhase, IntegrationMode,
    IntegrationValidator, ServiceLocator, register_phase_service,
    get_service_registry, get_integration_validator, IntegrationMetrics
)

logger = logging.getLogger(__name__)


class TestServiceDependency:
    """Test service dependency validation"""

    def test_compatible_version_exact_match(self):
        """Test exact version match compatibility"""
        dep = ServiceDependency(
            service_name="auth_service",
            min_version="1.0.0",
            max_version="2.0.0"
        )
        assert dep.is_compatible("1.0.0") is True
        assert dep.is_compatible("1.5.0") is True
        assert dep.is_compatible("2.0.0") is True

    def test_incompatible_version_out_of_range(self):
        """Test version out of acceptable range"""
        dep = ServiceDependency(
            service_name="auth_service",
            min_version="1.0.0",
            max_version="2.0.0"
        )
        assert dep.is_compatible("0.9.9") is False
        assert dep.is_compatible("2.0.1") is False

    def test_version_comparison_logic(self):
        """Test semantic version comparison"""
        dep = ServiceDependency(
            service_name="test",
            min_version="1.2.3",
            max_version="1.5.0"
        )
        assert dep.is_compatible("1.2.3") is True
        assert dep.is_compatible("1.3.0") is True
        assert dep.is_compatible("1.2.2") is False
        assert dep.is_compatible("1.5.1") is False


class TestServiceRegistry:
    """Test service registry functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.registry = ServiceRegistry()

    def test_register_service(self):
        """Test service registration"""
        config = ServiceConfiguration(
            name="test_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0",
            enabled=True
        )
        result = self.registry.register_service(config)
        assert result is True
        assert "test_service" in self.registry.services
        assert self.registry.metrics.total_services == 1

    def test_register_service_with_instance(self):
        """Test service registration with instance"""
        config = ServiceConfiguration(
            name="auth_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0"
        )
        instance = Mock()
        self.registry.register_service(config, instance)
        assert self.registry.get_service("auth_service") is instance

    def test_get_service_not_found(self):
        """Test retrieving non-existent service"""
        result = self.registry.get_service("nonexistent")
        assert result is None

    def test_service_with_dependencies(self):
        """Test registering service with dependencies"""
        dep = ServiceDependency(
            service_name="auth_service",
            required=True,
            min_version="1.0.0"
        )
        config = ServiceConfiguration(
            name="api_service",
            phase=ServicePhase.ADVANCED_FEATURES,
            version="2.0.0",
            dependencies=[dep]
        )
        self.registry.register_service(config)
        assert "api_service" in self.registry.dependency_graph
        assert "auth_service" in self.registry.dependency_graph["api_service"]

    def test_validate_dependencies_satisfied(self):
        """Test dependency validation when all satisfied"""
        # Register dependency first
        auth_config = ServiceConfiguration(
            name="auth_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.5.0"
        )
        self.registry.register_service(auth_config)
        
        # Register dependent service
        dep = ServiceDependency(
            service_name="auth_service",
            required=True,
            min_version="1.0.0",
            max_version="2.0.0"
        )
        api_config = ServiceConfiguration(
            name="api_service",
            phase=ServicePhase.ADVANCED_FEATURES,
            version="1.0.0",
            dependencies=[dep]
        )
        self.registry.register_service(api_config)
        
        valid, errors = self.registry.validate_dependencies("api_service")
        assert valid is True
        assert errors == []

    def test_validate_dependencies_missing_required(self):
        """Test validation when required dependency is missing"""
        dep = ServiceDependency(
            service_name="missing_service",
            required=True
        )
        config = ServiceConfiguration(
            name="dependent_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0",
            dependencies=[dep]
        )
        self.registry.register_service(config)
        
        valid, errors = self.registry.validate_dependencies("dependent_service")
        assert valid is False
        assert len(errors) > 0

    def test_validate_dependencies_version_mismatch(self):
        """Test validation when dependency version is incompatible"""
        # Register with version 1.0.0
        auth_config = ServiceConfiguration(
            name="auth_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0"
        )
        self.registry.register_service(auth_config)
        
        # Require version 2.0.0 or higher
        dep = ServiceDependency(
            service_name="auth_service",
            required=True,
            min_version="2.0.0"
        )
        api_config = ServiceConfiguration(
            name="api_service",
            phase=ServicePhase.ADVANCED_FEATURES,
            version="1.0.0",
            dependencies=[dep]
        )
        self.registry.register_service(api_config)
        
        valid, errors = self.registry.validate_dependencies("api_service")
        assert valid is False

    def test_update_service_health(self):
        """Test updating service health status"""
        config = ServiceConfiguration(
            name="test_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0"
        )
        self.registry.register_service(config)
        
        result = self.registry.update_service_health(
            "test_service",
            ServiceHealth.HEALTHY,
            latency_ms=45.5,
            error_rate=0.02
        )
        assert result is True
        health = self.registry.health_status["test_service"]
        assert health.status == ServiceHealth.HEALTHY
        assert health.endpoint_latency_ms == 45.5
        assert health.error_rate == 0.02

    def test_get_services_by_phase(self):
        """Test retrieving services by phase"""
        config1 = ServiceConfiguration(
            name="core_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0"
        )
        config2 = ServiceConfiguration(
            name="advanced_service",
            phase=ServicePhase.ADVANCED_FEATURES,
            version="1.0.0"
        )
        self.registry.register_service(config1)
        self.registry.register_service(config2)
        
        core_services = self.registry.get_services_by_phase(ServicePhase.CORE_FOUNDATION)
        assert len(core_services) == 1
        assert core_services[0].name == "core_service"

    def test_enable_disable_service(self):
        """Test enabling and disabling services"""
        config = ServiceConfiguration(
            name="test_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0",
            enabled=True
        )
        self.registry.register_service(config)
        
        # Disable service
        result = self.registry.disable_service("test_service")
        assert result is True
        assert self.registry.services["test_service"].enabled is False
        assert self.registry.health_status["test_service"].status == ServiceHealth.OFFLINE
        
        # Re-enable service
        result = self.registry.enable_service("test_service")
        assert result is True
        assert self.registry.services["test_service"].enabled is True

    def test_health_callback_triggered(self):
        """Test that health callbacks are triggered on status change"""
        config = ServiceConfiguration(
            name="test_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0"
        )
        self.registry.register_service(config)
        
        callback_mock = Mock()
        self.registry.register_health_callback(callback_mock)
        
        self.registry.update_service_health(
            "test_service",
            ServiceHealth.CRITICAL
        )
        
        callback_mock.assert_called_once_with("test_service", ServiceHealth.CRITICAL)

    def test_metrics_calculation(self):
        """Test metrics calculation"""
        configs = [
            ServiceConfiguration(
                name="service1",
                phase=ServicePhase.CORE_FOUNDATION,
                version="1.0.0"
            ),
            ServiceConfiguration(
                name="service2",
                phase=ServicePhase.ADVANCED_FEATURES,
                version="1.0.0"
            ),
        ]
        for config in configs:
            self.registry.register_service(config)
        
        self.registry.update_service_health("service1", ServiceHealth.HEALTHY)
        self.registry.update_service_health("service2", ServiceHealth.WARNING)
        
        metrics = self.registry.get_metrics()
        assert metrics.total_services == 2
        assert metrics.healthy_services == 1
        assert metrics.services_with_warnings == 1


class TestIntegrationValidator:
    """Test integration validation functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.registry = ServiceRegistry()
        self.validator = IntegrationValidator(self.registry, IntegrationMode.STRICT)

    def test_validate_all_services_success(self):
        """Test successful validation of all services"""
        config = ServiceConfiguration(
            name="test_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0"
        )
        self.registry.register_service(config)
        
        valid, results = self.validator.validate_all_services()
        assert valid is True
        assert "test_service" in results

    def test_validate_startup_order(self):
        """Test startup order generation"""
        # Create dependency chain: C -> B -> A
        config_a = ServiceConfiguration(
            name="service_a",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0"
        )
        
        dep_b = ServiceDependency(service_name="service_a", required=True)
        config_b = ServiceConfiguration(
            name="service_b",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0",
            dependencies=[dep_b]
        )
        
        dep_c = ServiceDependency(service_name="service_b", required=True)
        config_c = ServiceConfiguration(
            name="service_c",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0",
            dependencies=[dep_c]
        )
        
        self.registry.register_service(config_a)
        self.registry.register_service(config_b)
        self.registry.register_service(config_c)
        
        order = self.validator.validate_startup_order()
        assert order.index("service_a") < order.index("service_b")
        assert order.index("service_b") < order.index("service_c")

    def test_check_version_compatibility(self):
        """Test version compatibility checking"""
        config_a = ServiceConfiguration(
            name="service_a",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0"
        )
        
        dep = ServiceDependency(
            service_name="service_a",
            required=True,
            min_version="2.0.0"
        )
        config_b = ServiceConfiguration(
            name="service_b",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0",
            dependencies=[dep]
        )
        
        self.registry.register_service(config_a)
        self.registry.register_service(config_b)
        
        issues = self.validator.check_version_compatibility()
        assert "service_b" in issues

    def test_get_validation_report(self):
        """Test comprehensive validation report"""
        config = ServiceConfiguration(
            name="test_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0"
        )
        self.registry.register_service(config)
        
        report = self.validator.get_validation_report()
        assert "validation_results" in report
        assert "startup_order" in report
        assert "version_issues" in report
        assert "health_report" in report
        assert "metrics" in report


class TestServiceLocator:
    """Test service locator pattern"""

    def test_singleton_initialization(self):
        """Test that service locator is singleton"""
        registry1 = ServiceLocator.get_registry()
        registry2 = ServiceLocator.get_registry()
        assert registry1 is registry2

    def test_register_and_get_service(self):
        """Test registering and retrieving services"""
        config = ServiceConfiguration(
            name="test_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0"
        )
        instance = Mock()
        ServiceLocator.register_service(config, instance)
        
        retrieved = ServiceLocator.get_service("test_service")
        assert retrieved is instance

    def test_register_phase_service_convenience(self):
        """Test convenience function for phase service registration"""
        result = register_phase_service(
            name="auth_service",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0",
            enabled=True
        )
        assert result is True

    def test_get_validator(self):
        """Test getting validator from locator"""
        validator = ServiceLocator.get_validator()
        assert validator is not None
        assert isinstance(validator, IntegrationValidator)


class TestIntegrationMetrics:
    """Test integration metrics tracking"""

    def test_metrics_initialization(self):
        """Test metrics initialization"""
        metrics = IntegrationMetrics()
        assert metrics.total_services == 0
        assert metrics.healthy_services == 0
        assert metrics.average_latency_ms == 0.0

    def test_metrics_recalculation(self):
        """Test metrics recalculation with multiple services"""
        registry = ServiceRegistry()
        
        for i in range(3):
            config = ServiceConfiguration(
                name=f"service_{i}",
                phase=ServicePhase.CORE_FOUNDATION,
                version="1.0.0"
            )
            registry.register_service(config)
            
            if i == 0:
                registry.update_service_health(f"service_{i}", ServiceHealth.HOLY)
            elif i == 1:
                registry.update_service_health(f"service_{i}", ServiceHealth.WARNING)
            else:
                registry.update_service_health(f"service_{i}", ServiceHealth.HEALTHY)
        
        metrics = registry.get_metrics()
        assert metrics.total_services == 3


class TestPhaseIntegration:
    """Test integration across phases"""

    def test_all_phase_services_registered(self):
        """Test that services from all phases can be registered"""
        registry = ServiceRegistry()
        
        for phase in ServicePhase:
            config = ServiceConfiguration(
                name=f"service_{phase.value}",
                phase=phase,
                version="1.0.0"
            )
            registry.register_service(config)
        
        assert len(registry.services) == len(ServicePhase)

    def test_cross_phase_dependencies(self):
        """Test dependencies across phases"""
        registry = ServiceRegistry()
        validator = IntegrationValidator(registry)
        
        # Core foundation service
        config_a = ServiceConfiguration(
            name="core_auth",
            phase=ServicePhase.CORE_FOUNDATION,
            version="1.0.0"
        )
        registry.register_service(config_a)
        
        # Monitoring service depends on core
        dep = ServiceDependency(service_name="core_auth", required=True)
        config_b = ServiceConfiguration(
            name="monitoring_service",
            phase=ServicePhase.MONITORING_ANALYTICS,
            version="1.0.0",
            dependencies=[dep]
        )
        registry.register_service(config_b)
        
        valid, _ = validator.validate_all_services()
        assert valid is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
