"""
Observability Configuration Service
Centralized configuration for metrics, logging, tracing, and alerting
Phase 42: Observability & Monitoring Infrastructure
"""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import threading


class ConfigEnvironment(Enum):
    """Configuration environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class MetricsConfig:
    """Metrics configuration"""
    enabled: bool = True
    retention_hours: int = 24
    sample_interval_seconds: int = 60
    export_interval_seconds: int = 300
    prometheus_port: int = 9090
    enable_system_metrics: bool = True
    enable_app_metrics: bool = True
    max_time_series: int = 10000
    cleanup_interval_seconds: int = 3600

    def to_dict(self):
        return asdict(self)


@dataclass
class LoggingConfig:
    """Logging configuration"""
    enabled: bool = True
    log_level: str = "INFO"
    backends: List[str] = field(default_factory=lambda: ["memory", "file"])
    memory_max_entries: int = 10000
    file_log_dir: str = "logs"
    file_max_size_mb: int = 100
    elasticsearch_endpoint: str = ""
    elasticsearch_enabled: bool = False
    loki_endpoint: str = ""
    loki_enabled: bool = False
    cloudwatch_enabled: bool = False
    cloudwatch_log_group: str = "omnidev-ai"
    enable_trace_correlation: bool = True
    enable_structured_logging: bool = True
    json_export: bool = True

    def to_dict(self):
        return asdict(self)


@dataclass
class TracingConfig:
    """Distributed tracing configuration"""
    enabled: bool = True
    service_name: str = "omnidev-ai"
    retention_hours: int = 24
    sample_rate: float = 0.1
    export_interval_seconds: int = 300
    max_traces_in_memory: int = 10000
    enable_w3c_propagation: bool = True
    jaeger_endpoint: str = ""
    jaeger_enabled: bool = False
    zipkin_endpoint: str = ""
    zipkin_enabled: bool = False
    enable_slow_trace_detection: bool = True
    slow_trace_threshold_ms: int = 1000
    capture_request_body: bool = False
    capture_response_body: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class AlertingConfig:
    """Alerting configuration"""
    enabled: bool = True
    default_severity: str = "medium"
    cooldown_seconds: int = 300
    notification_channels: List[str] = field(default_factory=lambda: ["log"])
    email_enabled: bool = False
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    email_from_address: str = ""
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    pagerduty_enabled: bool = False
    pagerduty_integration_key: str = ""
    webhook_enabled: bool = False
    webhook_url: str = ""
    sms_enabled: bool = False
    sms_provider: str = "twilio"
    max_alerts_in_memory: int = 1000
    enable_alert_grouping: bool = True
    group_by_rule: bool = True
    alert_retention_hours: int = 24

    def to_dict(self):
        return asdict(self)


@dataclass
class APMConfig:
    """APM integration configuration"""
    enabled: bool = True
    providers: List[str] = field(default_factory=list)
    datadog_enabled: bool = False
    datadog_api_key: str = ""
    datadog_app_key: str = ""
    datadog_api_endpoint: str = "https://api.datadoghq.com"
    new_relic_enabled: bool = False
    new_relic_api_key: str = ""
    new_relic_api_endpoint: str = "https://api.newrelic.com"
    dynatrace_enabled: bool = False
    dynatrace_api_token: str = ""
    dynatrace_environment_id: str = ""
    dynatrace_api_endpoint: str = ""
    elastic_apm_enabled: bool = False
    elastic_apm_server_url: str = ""
    elastic_apm_api_key: str = ""
    jaeger_enabled: bool = False
    jaeger_endpoint: str = "http://localhost:14268"
    zipkin_enabled: bool = False
    zipkin_endpoint: str = "http://localhost:9411"
    batch_size: int = 100
    flush_interval_seconds: int = 60
    request_timeout_seconds: int = 10

    def to_dict(self):
        return asdict(self)


@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    enabled: bool = True
    port: int = 3000
    host: str = "localhost"
    refresh_interval_seconds: int = 30
    chart_history_hours: int = 24
    max_log_entries: int = 5000
    max_trace_entries: int = 1000
    max_alert_entries: int = 500
    enable_real_time_updates: bool = True
    enable_export: bool = True
    export_formats: List[str] = field(default_factory=lambda: ["json", "csv", "prometheus"])

    def to_dict(self):
        return asdict(self)


class ObservabilityConfig:
    """Central observability configuration manager"""

    def __init__(self, environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION):
        self.environment = environment
        self.metrics_config = MetricsConfig()
        self.logging_config = LoggingConfig()
        self.tracing_config = TracingConfig()
        self.alerting_config = AlertingConfig()
        self.apm_config = APMConfig()
        self.dashboard_config = DashboardConfig()
        self.custom_config: Dict[str, Any] = {}
        self.last_reload = datetime.now()
        self.lock = threading.RLock()

    def load_from_file(self, config_file: str) -> bool:
        """Load configuration from JSON file"""
        try:
            with self.lock:
                if not os.path.exists(config_file):
                    return False

                with open(config_file, 'r') as f:
                    config_dict = json.load(f)

                # Load metrics config
                if 'metrics' in config_dict:
                    metrics_dict = config_dict['metrics']
                    self.metrics_config = MetricsConfig(**metrics_dict)

                # Load logging config
                if 'logging' in config_dict:
                    logging_dict = config_dict['logging']
                    self.logging_config = LoggingConfig(**logging_dict)

                # Load tracing config
                if 'tracing' in config_dict:
                    tracing_dict = config_dict['tracing']
                    self.tracing_config = TracingConfig(**tracing_dict)

                # Load alerting config
                if 'alerting' in config_dict:
                    alerting_dict = config_dict['alerting']
                    self.alerting_config = AlertingConfig(**alerting_dict)

                # Load APM config
                if 'apm' in config_dict:
                    apm_dict = config_dict['apm']
                    self.apm_config = APMConfig(**apm_dict)

                # Load dashboard config
                if 'dashboard' in config_dict:
                    dashboard_dict = config_dict['dashboard']
                    self.dashboard_config = DashboardConfig(**dashboard_dict)

                # Load custom config
                self.custom_config = config_dict.get('custom', {})

                self.last_reload = datetime.now()
                return True
        except Exception as e:
            print(f"Error loading config file: {e}")
            return False

    def load_from_env(self) -> bool:
        """Load configuration from environment variables"""
        try:
            with self.lock:
                # Metrics
                if os.getenv('METRICS_ENABLED'):
                    self.metrics_config.enabled = os.getenv('METRICS_ENABLED').lower() == 'true'
                if os.getenv('METRICS_RETENTION_HOURS'):
                    self.metrics_config.retention_hours = int(os.getenv('METRICS_RETENTION_HOURS'))

                # Logging
                if os.getenv('LOG_LEVEL'):
                    self.logging_config.log_level = os.getenv('LOG_LEVEL')
                if os.getenv('LOG_BACKENDS'):
                    self.logging_config.backends = os.getenv('LOG_BACKENDS').split(',')

                # Tracing
                if os.getenv('TRACING_ENABLED'):
                    self.tracing_config.enabled = os.getenv('TRACING_ENABLED').lower() == 'true'
                if os.getenv('TRACING_SERVICE_NAME'):
                    self.tracing_config.service_name = os.getenv('TRACING_SERVICE_NAME')

                # Alerting
                if os.getenv('ALERTING_ENABLED'):
                    self.alerting_config.enabled = os.getenv('ALERTING_ENABLED').lower() == 'true'
                if os.getenv('ALERT_CHANNELS'):
                    self.alerting_config.notification_channels = os.getenv('ALERT_CHANNELS').split(',')

                # APM
                if os.getenv('APM_ENABLED'):
                    self.apm_config.enabled = os.getenv('APM_ENABLED').lower() == 'true'
                if os.getenv('APM_PROVIDERS'):
                    self.apm_config.providers = os.getenv('APM_PROVIDERS').split(',')

                self.last_reload = datetime.now()
                return True
        except Exception as e:
            print(f"Error loading from environment: {e}")
            return False

    def save_to_file(self, config_file: str) -> bool:
        """Save configuration to JSON file"""
        try:
            with self.lock:
                config_dict = {
                    "environment": self.environment.value,
                    "timestamp": datetime.now().isoformat(),
                    "metrics": self.metrics_config.to_dict(),
                    "logging": self.logging_config.to_dict(),
                    "tracing": self.tracing_config.to_dict(),
                    "alerting": self.alerting_config.to_dict(),
                    "apm": self.apm_config.to_dict(),
                    "dashboard": self.dashboard_config.to_dict(),
                    "custom": self.custom_config,
                }

                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                with open(config_file, 'w') as f:
                    json.dump(config_dict, f, indent=2)

                return True
        except Exception as e:
            print(f"Error saving config file: {e}")
            return False

    def apply_environment_defaults(self) -> None:
        """Apply defaults based on environment"""
        with self.lock:
            if self.environment == ConfigEnvironment.PRODUCTION:
                self.metrics_config.retention_hours = 24
                self.logging_config.log_level = "WARNING"
                self.tracing_config.sample_rate = 0.01
                self.alerting_config.cooldown_seconds = 300
            elif self.environment == ConfigEnvironment.STAGING:
                self.metrics_config.retention_hours = 12
                self.logging_config.log_level = "INFO"
                self.tracing_config.sample_rate = 0.1
                self.alerting_config.cooldown_seconds = 180
            elif self.environment == ConfigEnvironment.DEVELOPMENT:
                self.metrics_config.retention_hours = 6
                self.logging_config.log_level = "DEBUG"
                self.tracing_config.sample_rate = 1.0
                self.alerting_config.cooldown_seconds = 60

    def validate_config(self) -> tuple[bool, List[str]]:
        """Validate configuration consistency"""
        errors = []

        if self.metrics_config.retention_hours < 1:
            errors.append("Metrics retention must be at least 1 hour")

        if self.logging_config.file_max_size_mb < 1:
            errors.append("Log file max size must be at least 1 MB")

        if self.tracing_config.sample_rate < 0 or self.tracing_config.sample_rate > 1:
            errors.append("Tracing sample rate must be between 0 and 1")

        if self.alerting_config.cooldown_seconds < 0:
            errors.append("Alert cooldown cannot be negative")

        if self.apm_config.batch_size < 1:
            errors.append("APM batch size must be at least 1")

        if self.dashboard_config.port < 1 or self.dashboard_config.port > 65535:
            errors.append("Dashboard port must be between 1 and 65535")

        return len(errors) == 0, errors

    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        with self.lock:
            return {
                "environment": self.environment.value,
                "last_reload": self.last_reload.isoformat(),
                "metrics_enabled": self.metrics_config.enabled,
                "logging_enabled": self.logging_config.enabled,
                "tracing_enabled": self.tracing_config.enabled,
                "alerting_enabled": self.alerting_config.enabled,
                "apm_enabled": self.apm_config.enabled,
                "dashboard_enabled": self.dashboard_config.enabled,
                "apm_providers": self.apm_config.providers,
                "log_backends": self.logging_config.backends,
                "alert_channels": self.alerting_config.notification_channels,
            }

    def update_metrics_config(self, **kwargs) -> bool:
        """Update metrics configuration"""
        try:
            with self.lock:
                for key, value in kwargs.items():
                    if hasattr(self.metrics_config, key):
                        setattr(self.metrics_config, key, value)
                return True
        except Exception as e:
            print(f"Error updating metrics config: {e}")
            return False

    def update_logging_config(self, **kwargs) -> bool:
        """Update logging configuration"""
        try:
            with self.lock:
                for key, value in kwargs.items():
                    if hasattr(self.logging_config, key):
                        setattr(self.logging_config, key, value)
                return True
        except Exception as e:
            print(f"Error updating logging config: {e}")
            return False

    def update_tracing_config(self, **kwargs) -> bool:
        """Update tracing configuration"""
        try:
            with self.lock:
                for key, value in kwargs.items():
                    if hasattr(self.tracing_config, key):
                        setattr(self.tracing_config, key, value)
                return True
        except Exception as e:
            print(f"Error updating tracing config: {e}")
            return False

    def update_alerting_config(self, **kwargs) -> bool:
        """Update alerting configuration"""
        try:
            with self.lock:
                for key, value in kwargs.items():
                    if hasattr(self.alerting_config, key):
                        setattr(self.alerting_config, key, value)
                return True
        except Exception as e:
            print(f"Error updating alerting config: {e}")
            return False

    def update_apm_config(self, **kwargs) -> bool:
        """Update APM configuration"""
        try:
            with self.lock:
                for key, value in kwargs.items():
                    if hasattr(self.apm_config, key):
                        setattr(self.apm_config, key, value)
                return True
        except Exception as e:
            print(f"Error updating APM config: {e}")
            return False

    def update_dashboard_config(self, **kwargs) -> bool:
        """Update dashboard configuration"""
        try:
            with self.lock:
                for key, value in kwargs.items():
                    if hasattr(self.dashboard_config, key):
                        setattr(self.dashboard_config, key, value)
                return True
        except Exception as e:
            print(f"Error updating dashboard config: {e}")
            return False


# Global singleton
_observability_config = None


def get_observability_config(environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION) -> ObservabilityConfig:
    """Get or create observability config singleton"""
    global _observability_config
    if _observability_config is None:
        _observability_config = ObservabilityConfig(environment)
    return _observability_config


def initialize_config(config_file: Optional[str] = None, environment: Optional[str] = None) -> ObservabilityConfig:
    """Initialize observability configuration"""
    env = ConfigEnvironment.PRODUCTION
    if environment:
        try:
            env = ConfigEnvironment[environment.upper()]
        except KeyError:
            pass

    config = get_observability_config(env)
    config.apply_environment_defaults()

    if config_file:
        config.load_from_file(config_file)

    config.load_from_env()

    return config
