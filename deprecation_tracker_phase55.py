"""
Phase 55: Deprecation Tracker
Monitors deprecated endpoints, tracks usage, generates warnings,
and provides sunset monitoring capabilities.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import json


@dataclass
class DeprecationWarning:
    """Warning about deprecated endpoint usage."""
    endpoint: str
    client_id: Optional[str]
    timestamp: datetime
    warning_level: str  # warning, critical
    message: str
    removal_date: Optional[datetime] = None
    days_until_removal: Optional[int] = None
    replacement_endpoint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'endpoint': self.endpoint,
            'client_id': self.client_id,
            'timestamp': self.timestamp.isoformat(),
            'warning_level': self.warning_level,
            'message': self.message,
            'removal_date': self.removal_date.isoformat() if self.removal_date else None,
            'days_until_removal': self.days_until_removal,
            'replacement_endpoint': self.replacement_endpoint
        }


@dataclass
class EndpointUsageMetrics:
    """Usage metrics for an endpoint."""
    endpoint: str
    total_requests: int = 0
    unique_clients: int = 0
    first_request_time: Optional[datetime] = None
    last_request_time: Optional[datetime] = None
    average_response_time: float = 0.0
    error_rate: float = 0.0
    client_list: Set[str] = field(default_factory=set)
    hourly_requests: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'endpoint': self.endpoint,
            'total_requests': self.total_requests,
            'unique_clients': self.unique_clients,
            'first_request_time': self.first_request_time.isoformat() if self.first_request_time else None,
            'last_request_time': self.last_request_time.isoformat() if self.last_request_time else None,
            'average_response_time_ms': round(self.average_response_time, 2),
            'error_rate': round(self.error_rate, 2),
            'hourly_distribution': dict(sorted(self.hourly_requests.items()))
        }


@dataclass
class DeprecationNotice:
    """Notice about a deprecated endpoint."""
    endpoint: str
    deprecated_date: datetime
    removal_date: datetime
    replacement_endpoint: Optional[str]
    reason: str
    migration_guide_url: Optional[str] = None
    support_email: Optional[str] = None
    auto_migration_available: bool = False
    deprecation_level: str = "standard"  # standard, aggressive, final

    @property
    def days_until_removal(self) -> int:
        """Get days until removal."""
        delta = self.removal_date - datetime.now()
        return max(0, delta.days)

    @property
    def days_since_deprecation(self) -> int:
        """Get days since deprecation."""
        delta = datetime.now() - self.deprecated_date
        return max(0, delta.days)

    @property
    def is_in_sunset_period(self) -> bool:
        """Check if in final 7-day sunset period."""
        return self.days_until_removal <= 7

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'endpoint': self.endpoint,
            'deprecated_date': self.deprecated_date.isoformat(),
            'removal_date': self.removal_date.isoformat(),
            'days_since_deprecation': self.days_since_deprecation,
            'days_until_removal': self.days_until_removal,
            'is_in_sunset_period': self.is_in_sunset_period,
            'replacement_endpoint': self.replacement_endpoint,
            'reason': self.reason,
            'migration_guide_url': self.migration_guide_url,
            'support_email': self.support_email,
            'auto_migration_available': self.auto_migration_available,
            'deprecation_level': self.deprecation_level
        }


class DeprecationTracker:
    """Tracks deprecated endpoints and their usage."""

    def __init__(self):
        """Initialize deprecation tracker."""
        self.deprecation_notices: Dict[str, DeprecationNotice] = {}
        self.endpoint_usage: Dict[str, EndpointUsageMetrics] = {}
        self.warnings: List[DeprecationWarning] = []
        self.removal_queue: List[str] = []
        self.client_notifications: Dict[str, List[DeprecationWarning]] = defaultdict(list)
        self.usage_by_client: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def register_deprecation(
        self,
        endpoint: str,
        removal_date: datetime,
        replacement_endpoint: Optional[str] = None,
        reason: str = "Endpoint deprecated",
        migration_guide_url: Optional[str] = None,
        support_email: Optional[str] = None,
        auto_migration: bool = False,
        deprecation_level: str = "standard"
    ) -> 'DeprecationTracker':
        """Register a deprecated endpoint."""
        notice = DeprecationNotice(
            endpoint=endpoint,
            deprecated_date=datetime.now(),
            removal_date=removal_date,
            replacement_endpoint=replacement_endpoint,
            reason=reason,
            migration_guide_url=migration_guide_url,
            support_email=support_email,
            auto_migration_available=auto_migration,
            deprecation_level=deprecation_level
        )
        self.deprecation_notices[endpoint] = notice
        
        # Initialize usage metrics
        if endpoint not in self.endpoint_usage:
            self.endpoint_usage[endpoint] = EndpointUsageMetrics(endpoint=endpoint)
        
        return self

    def record_usage(
        self,
        endpoint: str,
        client_id: Optional[str] = None,
        response_time_ms: float = 0.0,
        status_code: int = 200,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record usage of an endpoint."""
        if timestamp is None:
            timestamp = datetime.now()

        # Initialize metrics if endpoint not tracked
        if endpoint not in self.endpoint_usage:
            self.endpoint_usage[endpoint] = EndpointUsageMetrics(endpoint=endpoint)

        metrics = self.endpoint_usage[endpoint]
        metrics.total_requests += 1
        
        if client_id:
            metrics.client_list.add(client_id)
            metrics.unique_clients = len(metrics.client_list)
            self.usage_by_client[client_id][endpoint] += 1

        # Update time tracking
        if metrics.first_request_time is None:
            metrics.first_request_time = timestamp
        metrics.last_request_time = timestamp

        # Update average response time
        if metrics.total_requests == 1:
            metrics.average_response_time = response_time_ms
        else:
            metrics.average_response_time = (
                (metrics.average_response_time * (metrics.total_requests - 1) + response_time_ms)
                / metrics.total_requests
            )

        # Track error rate
        if status_code >= 400:
            metrics.error_rate = (metrics.error_rate * (metrics.total_requests - 1) + 1) / metrics.total_requests
        else:
            metrics.error_rate = metrics.error_rate * (metrics.total_requests - 1) / metrics.total_requests

        # Track hourly distribution
        hour_key = timestamp.strftime("%Y-%m-%d %H:00:00")
        metrics.hourly_requests[hour_key] = metrics.hourly_requests.get(hour_key, 0) + 1

        # Generate warning if endpoint is deprecated
        if endpoint in self.deprecation_notices:
            self._generate_warning(endpoint, client_id, timestamp)

    def _generate_warning(
        self,
        endpoint: str,
        client_id: Optional[str],
        timestamp: datetime
    ) -> None:
        """Generate warning for deprecated endpoint usage."""
        notice = self.deprecation_notices[endpoint]
        
        # Determine warning level
        if notice.is_in_sunset_period:
            warning_level = "critical"
        else:
            warning_level = "warning"

        warning = DeprecationWarning(
            endpoint=endpoint,
            client_id=client_id,
            timestamp=timestamp,
            warning_level=warning_level,
            message=f"Using deprecated endpoint {endpoint}. {notice.reason}",
            removal_date=notice.removal_date,
            days_until_removal=notice.days_until_removal,
            replacement_endpoint=notice.replacement_endpoint
        )
        
        self.warnings.append(warning)
        
        if client_id:
            self.client_notifications[client_id].append(warning)

    def get_deprecation_notice(self, endpoint: str) -> Optional[DeprecationNotice]:
        """Get deprecation notice for endpoint."""
        return self.deprecation_notices.get(endpoint)

    def get_usage_metrics(self, endpoint: str) -> Optional[EndpointUsageMetrics]:
        """Get usage metrics for endpoint."""
        return self.endpoint_usage.get(endpoint)

    def get_all_deprecated_endpoints(self) -> List[DeprecationNotice]:
        """Get all deprecated endpoints."""
        return list(self.deprecation_notices.values())

    def get_deprecated_endpoints_in_sunset(self) -> List[DeprecationNotice]:
        """Get endpoints in their final sunset period."""
        return [n for n in self.deprecation_notices.values() if n.is_in_sunset_period]

    def get_warnings_for_client(self, client_id: str) -> List[DeprecationWarning]:
        """Get all warnings for a specific client."""
        return self.client_notifications.get(client_id, [])

    def get_recent_warnings(self, hours: int = 24) -> List[DeprecationWarning]:
        """Get warnings from the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [w for w in self.warnings if w.timestamp >= cutoff]

    def get_warnings_by_level(self, level: str = "critical") -> List[DeprecationWarning]:
        """Get warnings by level."""
        return [w for w in self.warnings if w.warning_level == level]

    def get_high_usage_deprecated_endpoints(self, threshold: int = 100) -> List[Dict[str, Any]]:
        """Get deprecated endpoints with high usage."""
        high_usage = []
        for endpoint, notice in self.deprecation_notices.items():
            metrics = self.endpoint_usage.get(endpoint)
            if metrics and metrics.total_requests >= threshold:
                high_usage.append({
                    'endpoint': endpoint,
                    'requests': metrics.total_requests,
                    'unique_clients': metrics.unique_clients,
                    'days_until_removal': notice.days_until_removal,
                    'replacement': notice.replacement_endpoint
                })
        return sorted(high_usage, key=lambda x: x['requests'], reverse=True)

    def get_client_migration_impact(self, client_id: str) -> Dict[str, Any]:
        """Get migration impact for a client."""
        client_usage = self.usage_by_client.get(client_id, {})
        affected_endpoints = []
        
        for endpoint, request_count in client_usage.items():
            if endpoint in self.deprecation_notices:
                notice = self.deprecation_notices[endpoint]
                affected_endpoints.append({
                    'endpoint': endpoint,
                    'requests': request_count,
                    'replacement': notice.replacement_endpoint,
                    'removal_date': notice.removal_date.isoformat(),
                    'days_until_removal': notice.days_until_removal
                })
        
        return {
            'client_id': client_id,
            'affected_endpoints': affected_endpoints,
            'total_deprecated_requests': sum(r['requests'] for r in affected_endpoints),
            'migration_complexity': self._calculate_migration_complexity(affected_endpoints)
        }

    def _calculate_migration_complexity(self, endpoints: List[Dict[str, Any]]) -> str:
        """Calculate migration complexity based on affected endpoints."""
        if not endpoints:
            return "none"
        
        total_requests = sum(e['requests'] for e in endpoints)
        num_endpoints = len(endpoints)
        
        if total_requests < 100 and num_endpoints <= 2:
            return "low"
        elif total_requests < 500 and num_endpoints <= 5:
            return "medium"
        else:
            return "high"

    def get_deprecation_timeline(self) -> List[Dict[str, Any]]:
        """Get timeline of deprecations."""
        timeline = []
        for notice in sorted(
            self.deprecation_notices.values(),
            key=lambda n: n.removal_date
        ):
            timeline.append({
                'endpoint': notice.endpoint,
                'deprecated_date': notice.deprecated_date.isoformat(),
                'removal_date': notice.removal_date.isoformat(),
                'status': 'sunset' if notice.is_in_sunset_period else 'active',
                'days_until_removal': notice.days_until_removal,
                'replacement': notice.replacement_endpoint
            })
        return timeline

    def get_statistics(self) -> Dict[str, Any]:
        """Get deprecation statistics."""
        all_notices = list(self.deprecation_notices.values())
        sunset_notices = self.get_deprecated_endpoints_in_sunset()
        critical_warnings = self.get_warnings_by_level("critical")
        
        total_usage = sum(m.total_requests for m in self.endpoint_usage.values())
        deprecated_usage = sum(
            m.total_requests for endpoint, m in self.endpoint_usage.items()
            if endpoint in self.deprecation_notices
        )

        return {
            'total_deprecated_endpoints': len(all_notices),
            'endpoints_in_sunset': len(sunset_notices),
            'total_warnings': len(self.warnings),
            'critical_warnings': len(critical_warnings),
            'deprecated_requests_percentage': round(
                (deprecated_usage / total_usage * 100) if total_usage > 0 else 0, 2
            ),
            'affected_clients': len(self.client_notifications),
            'average_warning_per_client': round(
                len(self.warnings) / len(self.client_notifications) if self.client_notifications else 0, 2
            ) if self.client_notifications else 0
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'deprecated_endpoints': [n.to_dict() for n in self.deprecation_notices.values()],
            'endpoints_in_sunset': [n.to_dict() for n in self.get_deprecated_endpoints_in_sunset()],
            'recent_warnings': [w.to_dict() for w in self.get_recent_warnings()],
            'high_usage_deprecated': self.get_high_usage_deprecated_endpoints(),
            'timeline': self.get_deprecation_timeline(),
            'statistics': self.get_statistics()
        }


# Singleton instance
_deprecation_tracker: Optional[DeprecationTracker] = None


def get_deprecation_tracker() -> DeprecationTracker:
    """Get the deprecation tracker singleton."""
    global _deprecation_tracker
    if _deprecation_tracker is None:
        _deprecation_tracker = DeprecationTracker()
    return _deprecation_tracker


def reset_deprecation_tracker() -> None:
    """Reset the deprecation tracker (for testing)."""
    global _deprecation_tracker
    _deprecation_tracker = None
