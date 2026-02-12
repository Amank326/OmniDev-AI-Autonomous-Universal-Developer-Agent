"""
Deployment Orchestrator Service
Manages deployment lifecycle, rollouts, and health checks
Phase 41: CI/CD Pipeline & Automated Deployment
"""

import logging
import asyncio
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from threading import RLock
import subprocess
import time

logger = logging.getLogger(__name__)


class DeploymentStrategy(Enum):
    """Deployment strategies"""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    SHADOW = "shadow"


class DeploymentEnvironment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(Enum):
    """Deployment status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    PAUSED = "paused"


class HealthCheckStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceInstance:
    """Represents a deployed service instance"""
    instance_id: str
    service_name: str
    version: str
    environment: DeploymentEnvironment
    status: HealthCheckStatus = HealthCheckStatus.UNKNOWN
    endpoint: Optional[str] = None
    startup_time: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    health_check_count: int = 0
    failed_checks: int = 0


@dataclass
class DeploymentConfig:
    """Configuration for a deployment"""
    name: str
    service_name: str
    version: str
    environment: DeploymentEnvironment
    strategy: DeploymentStrategy = DeploymentStrategy.BLUE_GREEN
    replicas: int = 3
    max_surge: int = 1
    max_unavailable: int = 0
    health_check_interval_seconds: int = 30
    health_check_timeout_seconds: int = 10
    health_check_max_retries: int = 3
    min_healthy_instances: int = 2
    rollback_on_failure: bool = True
    smoke_test_enabled: bool = True


@dataclass
class DeploymentRecord:
    """Record of a deployment operation"""
    deployment_id: str
    config: DeploymentConfig
    status: DeploymentStatus = DeploymentStatus.PENDING
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    deployed_instances: List[ServiceInstance] = field(default_factory=list)
    previous_version: Optional[str] = None
    error_message: Optional[str] = None
    rollback_performed: bool = False
    deployment_duration_seconds: float = 0.0
    metadata: Dict = field(default_factory=dict)


class HealthChecker:
    """Performs health checks on service instances"""

    def __init__(self, timeout_seconds: int = 10, max_retries: int = 3):
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.lock = RLock()

    def check_service_health(self, endpoint: str) -> HealthCheckStatus:
        """Check service health via HTTP"""
        try:
            # Try to reach health endpoint
            cmd = ["curl", "-f", "-s", "-m", str(self.timeout_seconds), f"{endpoint}/api/v1/health"]
            
            for attempt in range(self.max_retries):
                result = subprocess.run(cmd, capture_output=True, timeout=self.timeout_seconds + 5)
                
                if result.returncode == 0:
                    try:
                        data = json.loads(result.stdout.decode())
                        if data.get('status') == 'healthy':
                            return HealthCheckStatus.HEALTHY
                        else:
                            return HealthCheckStatus.DEGRADED
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid health check response from {endpoint}")
                        return HealthCheckStatus.UNKNOWN
                
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
            
            return HealthCheckStatus.UNHEALTHY
        
        except subprocess.TimeoutExpired:
            logger.warning(f"Health check timeout for {endpoint}")
            return HealthCheckStatus.UNHEALTHY
        except Exception as e:
            logger.error(f"Health check error for {endpoint}: {e}")
            return HealthCheckStatus.UNKNOWN

    def check_dependencies(self, service_name: str) -> Dict[str, bool]:
        """Check service dependencies"""
        try:
            cmd = ["curl", "-s", f"http://localhost:5000/api/v1/integration/services/{service_name}"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {dep: True for dep in data.get('dependencies', [])}
            
            return {}
        except Exception as e:
            logger.error(f"Dependency check error: {e}")
            return {}


class DeploymentOrchestrator:
    """Orchestrates deployments across environments"""

    def __init__(self):
        self.deployments: List[DeploymentRecord] = []
        self.instances: Dict[str, ServiceInstance] = {}
        self.health_checker = HealthChecker()
        self.lock = RLock()
        self.callbacks: List[Callable] = []
        self.active_deployments: Dict[str, DeploymentRecord] = {}

    def plan_deployment(self, config: DeploymentConfig) -> DeploymentRecord:
        """Plan a deployment"""
        import uuid
        deployment_id = f"deploy_{uuid.uuid4().hex[:12]}"
        
        record = DeploymentRecord(
            deployment_id=deployment_id,
            config=config
        )
        
        with self.lock:
            self.deployments.append(record)
            self.active_deployments[deployment_id] = record
        
        logger.info(f"Deployment {deployment_id} planned for {config.service_name} v{config.version}")
        return record

    def execute_deployment(self, deployment_id: str) -> bool:
        """Execute a deployment"""
        with self.lock:
            record = self.active_deployments.get(deployment_id)
            if not record:
                logger.error(f"Deployment {deployment_id} not found")
                return False
        
        logger.info(f"Executing deployment {deployment_id}")
        record.status = DeploymentStatus.IN_PROGRESS
        
        try:
            # Pre-deployment checks
            if not self._pre_deployment_checks(record):
                record.status = DeploymentStatus.FAILED
                return False
            
            # Deploy based on strategy
            if record.config.strategy == DeploymentStrategy.BLUE_GREEN:
                success = self._deploy_blue_green(record)
            elif record.config.strategy == DeploymentStrategy.CANARY:
                success = self._deploy_canary(record)
            elif record.config.strategy == DeploymentStrategy.ROLLING:
                success = self._deploy_rolling(record)
            else:
                success = self._deploy_shadow(record)
            
            if success:
                # Post-deployment validation
                if self._validate_deployment(record):
                    record.status = DeploymentStatus.COMPLETED
                    record.completed_at = datetime.utcnow()
                    logger.info(f"Deployment {deployment_id} completed successfully")
                    self._trigger_callbacks(record)
                    return True
            
            # Rollback on failure
            if record.config.rollback_on_failure:
                logger.warning(f"Deployment failed, rolling back {deployment_id}")
                self.rollback_deployment(deployment_id)
            
            record.status = DeploymentStatus.FAILED
            return False
        
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            record.status = DeploymentStatus.FAILED
            record.error_message = str(e)
            
            if record.config.rollback_on_failure:
                self.rollback_deployment(deployment_id)
            
            return False

    def rollback_deployment(self, deployment_id: str) -> bool:
        """Rollback a deployment"""
        with self.lock:
            record = self.active_deployments.get(deployment_id)
            if not record or not record.previous_version:
                logger.error(f"Cannot rollback {deployment_id}")
                return False
        
        try:
            logger.info(f"Rolling back deployment {deployment_id} to {record.previous_version}")
            
            # Rollback to previous version using kubectl
            cmd = [
                "kubectl", "rollout", "undo",
                f"deployment/{record.config.service_name}",
                "-n", record.config.environment.value
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            
            if result.returncode == 0:
                # Verify rollback
                time.sleep(10)
                if self._validate_deployment(record):
                    record.status = DeploymentStatus.ROLLED_BACK
                    record.rollback_performed = True
                    logger.info(f"Rollback completed for {deployment_id}")
                    return True
            
            logger.error(f"Rollback failed: {result.stderr.decode()}")
            return False
        
        except Exception as e:
            logger.error(f"Rollback error: {e}")
            return False

    def _pre_deployment_checks(self, record: DeploymentRecord) -> bool:
        """Perform pre-deployment checks"""
        logger.info(f"Running pre-deployment checks for {record.config.service_name}")
        
        # Verify image exists
        image_check = subprocess.run(
            ["docker", "inspect", f"{record.config.service_name}:{record.config.version}"],
            capture_output=True
        )
        
        if image_check.returncode != 0:
            logger.error(f"Docker image not found: {record.config.service_name}:{record.config.version}")
            return False
        
        # Check cluster connectivity
        cluster_check = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True
        )
        
        if cluster_check.returncode != 0:
            logger.error("Kubernetes cluster not accessible")
            return False
        
        return True

    def _deploy_blue_green(self, record: DeploymentRecord) -> bool:
        """Deploy using blue-green strategy"""
        logger.info(f"Deploying {record.config.service_name} with blue-green strategy")
        
        try:
            # Create green deployment
            cmd = [
                "kubectl", "set", "image",
                f"deployment/{record.config.service_name}-green",
                f"{record.config.service_name}=registry.example.com/{record.config.service_name}:{record.config.version}",
                "-n", record.config.environment.value,
                "--record"
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=600)
            if result.returncode != 0:
                return False
            
            # Wait for green to be ready
            time.sleep(30)
            
            # Switch traffic to green
            cmd = [
                "kubectl", "patch", "service", record.config.service_name,
                "-p", '{"spec":{"selector":{"version":"green"}}}',
                "-n", record.config.environment.value
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            return result.returncode == 0
        
        except Exception as e:
            logger.error(f"Blue-green deployment error: {e}")
            return False

    def _deploy_canary(self, record: DeploymentRecord) -> bool:
        """Deploy using canary strategy"""
        logger.info(f"Deploying {record.config.service_name} with canary strategy")
        
        try:
            # Deploy 1 replica of new version
            cmd = [
                "kubectl", "set", "image",
                f"deployment/{record.config.service_name}-canary",
                f"{record.config.service_name}=registry.example.com/{record.config.service_name}:{record.config.version}",
                "-n", record.config.environment.value,
                "--record"
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=600)
            if result.returncode != 0:
                return False
            
            # Monitor canary for errors
            time.sleep(60)
            
            # If successful, scale up rest of replicas
            cmd = [
                "kubectl", "set", "image",
                f"deployment/{record.config.service_name}",
                f"{record.config.service_name}=registry.example.com/{record.config.service_name}:{record.config.version}",
                "-n", record.config.environment.value,
                "--record"
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=600)
            return result.returncode == 0
        
        except Exception as e:
            logger.error(f"Canary deployment error: {e}")
            return False

    def _deploy_rolling(self, record: DeploymentRecord) -> bool:
        """Deploy using rolling strategy"""
        logger.info(f"Deploying {record.config.service_name} with rolling strategy")
        
        try:
            cmd = [
                "kubectl", "set", "image",
                f"deployment/{record.config.service_name}",
                f"{record.config.service_name}=registry.example.com/{record.config.service_name}:{record.config.version}",
                "-n", record.config.environment.value,
                "--record"
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=600)
            if result.returncode != 0:
                return False
            
            # Wait for rollout to complete
            cmd = ["kubectl", "rollout", "status", f"deployment/{record.config.service_name}",
                   "-n", record.config.environment.value]
            
            result = subprocess.run(cmd, capture_output=True, timeout=600)
            return result.returncode == 0
        
        except Exception as e:
            logger.error(f"Rolling deployment error: {e}")
            return False

    def _deploy_shadow(self, record: DeploymentRecord) -> bool:
        """Deploy shadow version (no traffic)"""
        logger.info(f"Deploying {record.config.service_name} as shadow deployment")
        
        try:
            cmd = [
                "kubectl", "create", "deployment",
                f"{record.config.service_name}-shadow",
                f"--image=registry.example.com/{record.config.service_name}:{record.config.version}",
                "-n", record.config.environment.value
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            return result.returncode == 0
        
        except Exception as e:
            logger.error(f"Shadow deployment error: {e}")
            return False

    def _validate_deployment(self, record: DeploymentRecord) -> bool:
        """Validate deployment health"""
        logger.info(f"Validating deployment {record.deployment_id}")
        
        try:
            # Get service endpoints
            cmd = ["kubectl", "get", "endpoints", record.config.service_name,
                   "-n", record.config.environment.value, "-o", "json"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return False
            
            endpoints = json.loads(result.stdout)
            healthy_count = 0
            
            for subset in endpoints.get('subsets', []):
                for addr in subset.get('addresses', []):
                    ip = addr.get('ip')
                    if ip:
                        # Check health
                        status = self.health_checker.check_service_health(f"http://{ip}:5000")
                        if status in [HealthCheckStatus.HEALTHY, HealthCheckStatus.DEGRADED]:
                            healthy_count += 1
            
            return healthy_count >= record.config.min_healthy_instances
        
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    def register_callback(self, callback: Callable[[DeploymentRecord], None]) -> None:
        """Register deployment callback"""
        with self.lock:
            self.callbacks.append(callback)

    def get_deployment_history(self, limit: int = 50) -> List[DeploymentRecord]:
        """Get deployment history"""
        with self.lock:
            return sorted(
                self.deployments,
                key=lambda d: d.started_at,
                reverse=True
            )[:limit]

    def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentRecord]:
        """Get deployment status"""
        with self.lock:
            return self.active_deployments.get(deployment_id)

    def _trigger_callbacks(self, record: DeploymentRecord) -> None:
        """Trigger registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(record)
            except Exception as e:
                logger.error(f"Callback error: {e}")


# Global orchestrator instance
_orchestrator: Optional[DeploymentOrchestrator] = None


def get_deployment_orchestrator() -> DeploymentOrchestrator:
    """Get or create deployment orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = DeploymentOrchestrator()
    return _orchestrator
