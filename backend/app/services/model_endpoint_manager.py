"""
Model Endpoint Manager
Manages model serving endpoints, including configuration, routing, traffic management,
and deployment strategies (canary, blue-green).
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from threading import RLock

logger = logging.getLogger(__name__)


# ===================== ENUMS =====================

class EndpointStatus(Enum):
    """Endpoint operational status"""
    INITIALIZING = "initializing"
    READY = "ready"
    SERVING = "serving"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    TERMINATING = "terminating"
    TERMINATED = "terminated"


class DeploymentStrategy(Enum):
    """Model deployment strategy"""
    BLUE_GREEN = "blue_green"  # Immediate 100% switch
    CANARY = "canary"  # Gradual rollout by percentage
    ROLLING = "rolling"  # Rolling update
    SHADOW = "shadow"  # Shadow traffic (no actual requests)
    A_B = "a_b"  # A/B test deployment


class TrafficAllocationStrategy(Enum):
    """How to allocate traffic between versions"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    RANDOM = "random"
    HASH_BASED = "hash_based"  # Hash on input features
    LATENCY_AWARE = "latency_aware"


class AuthenticationMethod(Enum):
    """Authentication methods for endpoints"""
    NONE = "none"
    API_KEY = "api_key"
    JWT = "jwt"
    OAUTH2 = "oauth2"
    MUTUAL_TLS = "mutual_tls"


class EndpointVisibility(Enum):
    """Endpoint access scope"""
    PRIVATE = "private"  # Internal only
    WORKSPACE = "workspace"  # Within workspace
    PUBLIC = "public"  # Public internet


# ===================== DATACLASSES =====================

@dataclass
class ModelRoute:
    """Route to specific model version"""
    model_id: str
    model_version: int
    traffic_percentage: float  # 0-100
    min_replicas: int = 1
    max_replicas: int = 5
    target_latency_ms: int = 50
    max_concurrent_requests: int = 100


@dataclass
class CanaryDeployment:
    """Canary deployment configuration"""
    deployment_id: str
    endpoint_id: str
    previous_route: ModelRoute
    new_route: ModelRoute
    initial_traffic_percentage: float  # Starting percentage for new model
    target_traffic_percentage: float  # Final percentage
    traffic_increment: float  # % to increase per step
    step_duration_seconds: int  # Time between increments
    analysis_metric: str = "error_rate"  # Track this metric
    success_threshold: float = 0.98  # Success criteria (0-1)
    rollback_threshold: float = 0.05  # Error rate that triggers rollback
    status: str = "pending"
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    rolled_back_at: Optional[float] = None


@dataclass
class EndpointConfig:
    """Model endpoint configuration"""
    endpoint_id: str
    workspace_id: str
    endpoint_name: str
    description: str = ""
    models: List[ModelRoute] = field(default_factory=list)
    traffic_strategy: TrafficAllocationStrategy = TrafficAllocationStrategy.ROUND_ROBIN
    deployment_strategy: DeploymentStrategy = DeploymentStrategy.BLUE_GREEN
    request_timeout_ms: int = 30000
    max_batch_size: int = 32
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    authentication: AuthenticationMethod = AuthenticationMethod.API_KEY
    visibility: EndpointVisibility = EndpointVisibility.PRIVATE
    min_replicas: int = 1
    max_replicas: int = 5
    cpu_limit_millicores: int = 1000
    memory_limit_mb: int = 1024
    enable_monitoring: bool = True
    enable_rate_limiting: bool = True
    rate_limit_rps: Optional[int] = None  # Requests per second
    rate_limit_burst: int = 10
    enable_request_logging: bool = True
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    updated_at: Optional[float] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


@dataclass
class EndpointMetrics:
    """Endpoint performance metrics"""
    endpoint_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    mean_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    throughput_rps: float = 0.0
    error_rate: float = 0.0
    active_connections: int = 0
    queued_requests: int = 0
    cache_hit_rate: float = 0.0
    avg_model_latency_ms: float = 0.0  # Inference latency only
    routing_time_ms: float = 0.0
    model_version_stats: Dict[int, Dict[str, float]] = field(default_factory=dict)


@dataclass
class EndpointInstance:
    """Individual endpoint instance"""
    instance_id: str
    endpoint_id: str
    status: EndpointStatus = EndpointStatus.INITIALIZING
    last_heartbeat: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    requests_processed: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    model_versions_loaded: List[int] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())


@dataclass
class APIKey:
    """API key for endpoint authentication"""
    key_id: str
    endpoint_id: str
    key_hash: str  # SHA-256 hash
    display_key: str  # Last 4 chars only
    permissions: List[str] = field(default_factory=list)  # read, write, admin
    rate_limit_override: Optional[int] = None
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    created_by: Optional[str] = None
    rotated_at: Optional[float] = None
    expires_at: Optional[float] = None
    is_active: bool = True


@dataclass
class RequestTrace:
    """Request tracing information"""
    request_id: str
    endpoint_id: str
    model_id: str
    model_version: int
    request_size_bytes: int
    response_size_bytes: int
    total_latency_ms: float
    routing_latency_ms: float
    model_latency_ms: float
    status_code: int
    error_message: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())


@dataclass
class EndpointHealth:
    """Endpoint health status"""
    endpoint_id: str
    overall_status: EndpointStatus
    instance_health: Dict[str, EndpointStatus]  # instance_id -> status
    recent_error_rate: float
    recent_latency_p99_ms: float
    model_availability: Dict[int, float]  # model_version -> availability%
    last_check_at: float
    checks_passed: int = 0
    checks_failed: int = 0
    unhealthy_instances: List[str] = field(default_factory=list)


# ===================== MODEL ENDPOINT MANAGER =====================

class ModelEndpointManager:
    """
    Manages model serving endpoints with traffic routing, deployment strategies,
    health checks, and canary deployments.
    """
    
    def __init__(self):
        # Endpoint management
        self.endpoints: Dict[str, EndpointConfig] = {}  # endpoint_id -> config
        self.endpoint_instances: Dict[str, List[EndpointInstance]] = {}  # endpoint_id -> instances
        self.endpoint_metrics: Dict[str, EndpointMetrics] = {}  # endpoint_id -> metrics
        
        # Deployment management
        self.deployments: Dict[str, CanaryDeployment] = {}  # deployment_id -> deployment
        self.active_deployments: Dict[str, str] = {}  # endpoint_id -> deployment_id
        
        # Authentication
        self.api_keys: Dict[str, APIKey] = {}  # key_id -> key
        self.endpoint_keys: Dict[str, List[str]] = {}  # endpoint_id -> key_ids
        
        # Monitoring
        self.request_traces: Dict[str, deque] = {}  # endpoint_id -> traces (last 10K)
        self.endpoint_health: Dict[str, EndpointHealth] = {}  # endpoint_id -> health
        
        # Thread safety
        self.lock = RLock()
        
        # Callbacks
        self.callbacks: Dict[str, List[Callable]] = {
            'endpoint_created': [],
            'endpoint_updated': [],
            'endpoint_deleted': [],
            'deployment_started': [],
            'deployment_completed': [],
            'deployment_rolled_back': [],
            'health_check_failed': [],
            'traffic_shifted': []
        }
    
    def create_endpoint(self, config: EndpointConfig) -> str:
        """Create new model serving endpoint"""
        endpoint_id = config.endpoint_id or f"endpoint_{uuid.uuid4().hex[:8]}"
        config.endpoint_id = endpoint_id
        
        with self.lock:
            if endpoint_id in self.endpoints:
                raise ValueError(f"Endpoint {endpoint_id} already exists")
            
            self.endpoints[endpoint_id] = config
            self.endpoint_instances[endpoint_id] = []
            self.endpoint_metrics[endpoint_id] = EndpointMetrics(endpoint_id=endpoint_id)
            self.endpoint_health[endpoint_id] = EndpointHealth(
                endpoint_id=endpoint_id,
                overall_status=EndpointStatus.INITIALIZING,
                instance_health={},
                recent_error_rate=0.0,
                recent_latency_p99_ms=0.0,
                model_availability={v.model_version: 100.0 for v in config.models},
                last_check_at=datetime.utcnow().timestamp()
            )
            self.request_traces[endpoint_id] = deque(maxlen=10000)
            self.endpoint_keys[endpoint_id] = []
            
            logger.info(f"Created endpoint {endpoint_id}")
            self._trigger_callback('endpoint_created', {
                'endpoint_id': endpoint_id,
                'name': config.endpoint_name
            })
            
            return endpoint_id
    
    def get_endpoint(self, endpoint_id: str) -> Optional[EndpointConfig]:
        """Get endpoint configuration"""
        with self.lock:
            return self.endpoints.get(endpoint_id)
    
    def list_endpoints(self, workspace_id: str) -> List[EndpointConfig]:
        """List all endpoints in workspace"""
        with self.lock:
            return [ep for ep in self.endpoints.values() if ep.workspace_id == workspace_id]
    
    def update_endpoint(self, endpoint_id: str, updates: Dict[str, Any]) -> bool:
        """Update endpoint configuration"""
        with self.lock:
            if endpoint_id not in self.endpoints:
                return False
            
            endpoint = self.endpoints[endpoint_id]
            
            # Update allowed fields
            allowed_fields = {'description', 'tags', 'metadata', 'min_replicas', 'max_replicas',
                            'request_timeout_ms', 'enable_monitoring', 'enable_rate_limiting',
                            'rate_limit_rps', 'traffic_strategy'}
            
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(endpoint, field, value)
            
            endpoint.updated_at = datetime.utcnow().timestamp()
            
            self._trigger_callback('endpoint_updated', {
                'endpoint_id': endpoint_id,
                'updates': updates
            })
            
            return True
    
    def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete endpoint"""
        with self.lock:
            if endpoint_id not in self.endpoints:
                return False
            
            # Clean up instances
            for instance in self.endpoint_instances.get(endpoint_id, []):
                instance.status = EndpointStatus.TERMINATED
            
            del self.endpoints[endpoint_id]
            del self.endpoint_instances[endpoint_id]
            del self.endpoint_metrics[endpoint_id]
            del self.endpoint_health[endpoint_id]
            
            logger.info(f"Deleted endpoint {endpoint_id}")
            self._trigger_callback('endpoint_deleted', {'endpoint_id': endpoint_id})
            
            return True
    
    def start_canary_deployment(self, endpoint_id: str, new_model_route: ModelRoute,
                               deployment_config: Dict[str, Any]) -> Optional[str]:
        """Start canary deployment to new model version"""
        with self.lock:
            endpoint = self.endpoints.get(endpoint_id)
            if not endpoint or not endpoint.models:
                return None
            
            current_route = endpoint.models[0]  # Assume primary route
            
            deployment = CanaryDeployment(
                deployment_id=f"deploy_{uuid.uuid4().hex[:8]}",
                endpoint_id=endpoint_id,
                previous_route=current_route,
                new_route=new_model_route,
                initial_traffic_percentage=deployment_config.get('initial_traffic_percentage', 5),
                target_traffic_percentage=deployment_config.get('target_traffic_percentage', 100),
                traffic_increment=deployment_config.get('traffic_increment', 10),
                step_duration_seconds=deployment_config.get('step_duration_seconds', 300),
                analysis_metric=deployment_config.get('analysis_metric', 'error_rate'),
                success_threshold=deployment_config.get('success_threshold', 0.98),
                rollback_threshold=deployment_config.get('rollback_threshold', 0.05)
            )
            
            self.deployments[deployment.deployment_id] = deployment
            self.active_deployments[endpoint_id] = deployment.deployment_id
            
            # Update traffic immediately
            current_route.traffic_percentage = 100 - deployment.initial_traffic_percentage
            new_model_route.traffic_percentage = deployment.initial_traffic_percentage
            
            deployment.status = "active"
            deployment.started_at = datetime.utcnow().timestamp()
            
            logger.info(f"Started canary deployment {deployment.deployment_id} on {endpoint_id}")
            self._trigger_callback('deployment_started', {
                'deployment_id': deployment.deployment_id,
                'endpoint_id': endpoint_id
            })
            
            return deployment.deployment_id
    
    def complete_canary_deployment(self, deployment_id: str) -> bool:
        """Complete canary deployment and promote new version"""
        with self.lock:
            if deployment_id not in self.deployments:
                return False
            
            deployment = self.deployments[deployment_id]
            deployment.status = "completed"
            deployment.completed_at = datetime.utcnow().timestamp()
            
            endpoint = self.endpoints.get(deployment.endpoint_id)
            if endpoint:
                # Swap routes: new becomes primary
                endpoint.models = [deployment.new_route]
            
            logger.info(f"Completed deployment {deployment_id}")
            self._trigger_callback('deployment_completed', {
                'deployment_id': deployment_id,
                'endpoint_id': deployment.endpoint_id
            })
            
            return True
    
    def rollback_canary_deployment(self, deployment_id: str) -> bool:
        """Rollback canary deployment"""
        with self.lock:
            if deployment_id not in self.deployments:
                return False
            
            deployment = self.deployments[deployment_id]
            deployment.status = "rolled_back"
            deployment.rolled_back_at = datetime.utcnow().timestamp()
            
            endpoint = self.endpoints.get(deployment.endpoint_id)
            if endpoint:
                # Restore to previous version
                endpoint.models = [deployment.previous_route]
            
            logger.info(f"Rolled back deployment {deployment_id}")
            self._trigger_callback('deployment_rolled_back', {
                'deployment_id': deployment_id,
                'endpoint_id': deployment.endpoint_id
            })
            
            return True
    
    def create_api_key(self, endpoint_id: str, permissions: List[str],
                      created_by: Optional[str] = None) -> Tuple[str, str]:
        """Create API key for endpoint authentication"""
        from hashlib import sha256
        
        if endpoint_id not in self.endpoints:
            raise ValueError(f"Endpoint {endpoint_id} not found")
        
        # Generate key
        key = f"sk_{uuid.uuid4().hex}"
        key_hash = sha256(key.encode()).hexdigest()
        key_id = f"key_{uuid.uuid4().hex[:8]}"
        
        api_key = APIKey(
            key_id=key_id,
            endpoint_id=endpoint_id,
            key_hash=key_hash,
            display_key=key[-4:],
            permissions=permissions,
            created_by=created_by
        )
        
        with self.lock:
            self.api_keys[key_id] = api_key
            self.endpoint_keys[endpoint_id].append(key_id)
        
        logger.info(f"Created API key {key_id} for endpoint {endpoint_id}")
        return key_id, key  # Return actual key only once
    
    def validate_api_key(self, endpoint_id: str, api_key: str) -> Tuple[bool, Optional[APIKey]]:
        """Validate API key for endpoint"""
        from hashlib import sha256
        
        key_hash = sha256(api_key.encode()).hexdigest()
        
        with self.lock:
            for key_id in self.endpoint_keys.get(endpoint_id, []):
                api_key_obj = self.api_keys.get(key_id)
                if api_key_obj and api_key_obj.key_hash == key_hash and api_key_obj.is_active:
                    return True, api_key_obj
        
        return False, None
    
    def record_request(self, trace: RequestTrace) -> None:
        """Record request trace for monitoring"""
        with self.lock:
            if trace.endpoint_id in self.request_traces:
                self.request_traces[trace.endpoint_id].append(trace)
    
    def get_endpoint_metrics(self, endpoint_id: str) -> Optional[EndpointMetrics]:
        """Get endpoint metrics"""
        with self.lock:
            return self.endpoint_metrics.get(endpoint_id)
    
    def update_endpoint_metrics(self, endpoint_id: str, latency_ms: float, success: bool,
                               model_version: int, request_size: int, response_size: int) -> None:
        """Update endpoint metrics"""
        with self.lock:
            if endpoint_id not in self.endpoint_metrics:
                return
            
            metrics = self.endpoint_metrics[endpoint_id]
            metrics.total_requests += 1
            
            if success:
                metrics.successful_requests += 1
                metrics.avg_model_latency_ms = (
                    (metrics.avg_model_latency_ms * (metrics.total_requests - 1) + latency_ms) /
                    metrics.total_requests
                )
            else:
                metrics.failed_requests += 1
            
            metrics.error_rate = metrics.failed_requests / max(metrics.total_requests, 1)
            
            # Update model version stats
            if model_version not in metrics.model_version_stats:
                metrics.model_version_stats[model_version] = {
                    'requests': 0,
                    'errors': 0,
                    'avg_latency_ms': 0.0
                }
            
            model_stats = metrics.model_version_stats[model_version]
            model_stats['requests'] += 1
            if not success:
                model_stats['errors'] += 1
    
    def get_endpoint_health(self, endpoint_id: str) -> Optional[EndpointHealth]:
        """Get endpoint health status"""
        with self.lock:
            return self.endpoint_health.get(endpoint_id)
    
    def check_endpoint_health(self, endpoint_id: str) -> Optional[EndpointHealth]:
        """Perform health check on endpoint"""
        with self.lock:
            if endpoint_id not in self.endpoint_health:
                return None
            
            health = self.endpoint_health[endpoint_id]
            instances = self.endpoint_instances.get(endpoint_id, [])
            
            # Check instances
            unhealthy_count = 0
            for instance in instances:
                heartbeat_age = datetime.utcnow().timestamp() - instance.last_heartbeat
                if heartbeat_age > 30:  # 30 second timeout
                    instance.status = EndpointStatus.UNHEALTHY
                    unhealthy_count += 1
                
                health.instance_health[instance.instance_id] = instance.status
            
            # Determine overall health
            if unhealthy_count == 0:
                health.overall_status = EndpointStatus.READY
            elif unhealthy_count < len(instances) / 2:
                health.overall_status = EndpointStatus.DEGRADED
            else:
                health.overall_status = EndpointStatus.UNHEALTHY
            
            health.unhealthy_instances = [
                inst.instance_id for inst in instances
                if inst.status == EndpointStatus.UNHEALTHY
            ]
            
            health.last_check_at = datetime.utcnow().timestamp()
            
            if health.overall_status != EndpointStatus.READY:
                self._trigger_callback('health_check_failed', {
                    'endpoint_id': endpoint_id,
                    'status': health.overall_status.value
                })
            
            return health
    
    def add_endpoint_instance(self, endpoint_id: str, instance_id: Optional[str] = None) -> str:
        """Add instance to endpoint"""
        with self.lock:
            if endpoint_id not in self.endpoint_instances:
                raise ValueError(f"Endpoint {endpoint_id} not found")
            
            instance_id = instance_id or f"instance_{uuid.uuid4().hex[:8]}"
            
            instance = EndpointInstance(
                instance_id=instance_id,
                endpoint_id=endpoint_id
            )
            
            self.endpoint_instances[endpoint_id].append(instance)
            
            logger.info(f"Added instance {instance_id} to endpoint {endpoint_id}")
            return instance_id
    
    def update_instance_status(self, endpoint_id: str, instance_id: str,
                              status: EndpointStatus) -> bool:
        """Update instance status"""
        with self.lock:
            instances = self.endpoint_instances.get(endpoint_id, [])
            for instance in instances:
                if instance.instance_id == instance_id:
                    instance.status = status
                    instance.last_heartbeat = datetime.utcnow().timestamp()
                    return True
            
            return False
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        with self.lock:
            total_endpoints = len(self.endpoints)
            total_instances = sum(len(instances) for instances in self.endpoint_instances.values())
            active_deployments = len([d for d in self.deployments.values() if d.status == "active"])
            
            return {
                'total_endpoints': total_endpoints,
                'total_instances': total_instances,
                'active_deployments': active_deployments,
                'total_api_keys': len(self.api_keys),
                'timestamp': datetime.utcnow().timestamp()
            }
    
    def _trigger_callback(self, event_type: str, data: Dict[str, Any]) -> None:
        """Trigger registered callbacks"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register callback for event"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        
        self.callbacks[event_type].append(callback)
