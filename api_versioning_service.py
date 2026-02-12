"""
Phase 55: API Versioning Management
Comprehensive version management system for APIs with deprecation tracking,
migration helpers, and backward compatibility checking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
from datetime import datetime, timedelta
import re
from abc import ABC, abstractmethod


class VersionFormat(Enum):
    """Supported version formats."""
    SEMANTIC = "semantic"  # 1.2.3
    MAJOR_MINOR = "major_minor"  # 1.2
    MAJOR = "major"  # 1


class DeprecationStatus(Enum):
    """Status of deprecated endpoints."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"  # In final days before removal
    REMOVED = "removed"


class MigrationSeverity(Enum):
    """Severity of breaking changes requiring migration."""
    LOW = "low"  # Minor changes, simple update
    MEDIUM = "medium"  # Moderate changes, requires attention
    HIGH = "high"  # Breaking changes, migration required
    CRITICAL = "critical"  # Major breaking changes, substantial refactoring


class CompatibilityLevel(Enum):
    """Level of backward compatibility."""
    FULLY_COMPATIBLE = "fully_compatible"  # No breaking changes
    MOSTLY_COMPATIBLE = "mostly_compatible"  # Minor incompatibilities
    PARTIALLY_COMPATIBLE = "partially_compatible"  # Some major incompatibilities
    INCOMPATIBLE = "incompatible"  # Major breaking changes


@dataclass
class SemanticVersion:
    """Semantic version representation (major.minor.patch)."""
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        """Return version string."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: 'SemanticVersion') -> bool:
        """Compare versions."""
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: 'SemanticVersion') -> bool:
        """Compare versions."""
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

    def __gt__(self, other: 'SemanticVersion') -> bool:
        """Compare versions."""
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other: 'SemanticVersion') -> bool:
        """Compare versions."""
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)

    def __eq__(self, other: 'SemanticVersion') -> bool:
        """Compare versions."""
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __hash__(self) -> int:
        """Hash version."""
        return hash((self.major, self.minor, self.patch))

    @staticmethod
    def parse(version_str: str) -> 'SemanticVersion':
        """Parse version string like '1.2.3'."""
        match = re.match(r'v?(\d+)\.(\d+)\.(\d+)', version_str)
        if not match:
            raise ValueError(f"Invalid semantic version: {version_str}")
        return SemanticVersion(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    def is_major_change(self, other: 'SemanticVersion') -> bool:
        """Check if this is a major version change from other."""
        return self.major > other.major

    def is_minor_change(self, other: 'SemanticVersion') -> bool:
        """Check if this is a minor version change from other."""
        return self.major == other.major and self.minor > other.minor

    def is_patch_change(self, other: 'SemanticVersion') -> bool:
        """Check if this is a patch version change from other."""
        return self.major == other.major and self.minor == other.minor and self.patch > other.patch


@dataclass
class EndpointChange:
    """Represents a change to an endpoint."""
    endpoint: str
    change_type: str  # added, removed, modified, deprecated
    severity: MigrationSeverity
    description: str
    deprecation_date: Optional[datetime] = None
    removal_date: Optional[datetime] = None
    replacement_endpoint: Optional[str] = None
    migration_guide_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'endpoint': self.endpoint,
            'change_type': self.change_type,
            'severity': self.severity.value,
            'description': self.description,
            'deprecation_date': self.deprecation_date.isoformat() if self.deprecation_date else None,
            'removal_date': self.removal_date.isoformat() if self.removal_date else None,
            'replacement_endpoint': self.replacement_endpoint,
            'migration_guide_url': self.migration_guide_url
        }


@dataclass
class APIEndpoint:
    """Represents an API endpoint."""
    path: str
    method: str
    version: SemanticVersion
    description: str = ""
    deprecated: bool = False
    deprecation_date: Optional[datetime] = None
    removal_date: Optional[datetime] = None
    replacement: Optional[str] = None
    breaking_changes: List[str] = field(default_factory=list)
    new_parameters: List[str] = field(default_factory=list)
    removed_parameters: List[str] = field(default_factory=list)
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None

    def get_deprecation_status(self) -> DeprecationStatus:
        """Get current deprecation status."""
        if not self.deprecated:
            return DeprecationStatus.ACTIVE
        
        now = datetime.now()
        if self.removal_date and now >= self.removal_date:
            return DeprecationStatus.REMOVED
        elif self.removal_date and (self.removal_date - now) <= timedelta(days=7):
            return DeprecationStatus.SUNSET
        else:
            return DeprecationStatus.DEPRECATED

    def days_until_removal(self) -> Optional[int]:
        """Get days until endpoint removal."""
        if not self.removal_date:
            return None
        delta = self.removal_date - datetime.now()
        return max(0, delta.days)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'path': self.path,
            'method': self.method,
            'version': str(self.version),
            'description': self.description,
            'deprecated': self.deprecated,
            'deprecation_status': self.get_deprecation_status().value,
            'deprecation_date': self.deprecation_date.isoformat() if self.deprecation_date else None,
            'removal_date': self.removal_date.isoformat() if self.removal_date else None,
            'replacement': self.replacement,
            'days_until_removal': self.days_until_removal(),
            'breaking_changes': self.breaking_changes,
            'new_parameters': self.new_parameters,
            'removed_parameters': self.removed_parameters
        }


@dataclass
class APIVersion:
    """Represents a complete API version."""
    version: SemanticVersion
    release_date: datetime
    endpoints: List[APIEndpoint] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    new_features: List[str] = field(default_factory=list)
    deprecated_endpoints: List[str] = field(default_factory=list)
    changelog: str = ""
    release_notes: str = ""
    migration_guide: str = ""
    end_of_life_date: Optional[datetime] = None

    def add_endpoint(self, endpoint: APIEndpoint) -> 'APIVersion':
        """Add an endpoint to this version."""
        self.endpoints.append(endpoint)
        return self

    def get_deprecated_endpoints(self) -> List[APIEndpoint]:
        """Get all deprecated endpoints in this version."""
        return [e for e in self.endpoints if e.deprecated]

    def get_breaking_changes_summary(self) -> Dict[str, List[str]]:
        """Get summary of breaking changes."""
        changes = {
            'endpoints_removed': [],
            'endpoints_deprecated': [],
            'parameters_removed': [],
            'schema_changes': []
        }
        for endpoint in self.endpoints:
            if endpoint.breaking_changes:
                changes['parameters_removed'].extend(endpoint.breaking_changes)
            if endpoint.removed_parameters:
                changes['parameters_removed'].extend(endpoint.removed_parameters)
            if endpoint.deprecated:
                changes['endpoints_deprecated'].append(f"{endpoint.method} {endpoint.path}")
        return changes

    def is_end_of_life(self) -> bool:
        """Check if this version is end of life."""
        if not self.end_of_life_date:
            return False
        return datetime.now() >= self.end_of_life_date

    def days_until_eol(self) -> Optional[int]:
        """Get days until end of life."""
        if not self.end_of_life_date:
            return None
        delta = self.end_of_life_date - datetime.now()
        return max(0, delta.days)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'version': str(self.version),
            'release_date': self.release_date.isoformat(),
            'end_of_life_date': self.end_of_life_date.isoformat() if self.end_of_life_date else None,
            'days_until_eol': self.days_until_eol(),
            'is_eol': self.is_end_of_life(),
            'total_endpoints': len(self.endpoints),
            'deprecated_endpoints': len(self.get_deprecated_endpoints()),
            'breaking_changes': self.breaking_changes,
            'new_features': self.new_features,
            'changelog': self.changelog[:500] if self.changelog else ""
        }


@dataclass
class MigrationPath:
    """Represents a migration path between versions."""
    from_version: SemanticVersion
    to_version: SemanticVersion
    severity: MigrationSeverity
    message: str
    steps: List[Dict[str, str]] = field(default_factory=list)
    timeline_days: int = 7
    affected_endpoints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'from_version': str(self.from_version),
            'to_version': str(self.to_version),
            'severity': self.severity.value,
            'message': self.message,
            'steps': self.steps,
            'timeline_days': self.timeline_days,
            'affected_endpoints': self.affected_endpoints
        }


@dataclass
class CompatibilityReport:
    """Report on compatibility between versions."""
    from_version: SemanticVersion
    to_version: SemanticVersion
    compatibility_level: CompatibilityLevel
    breaking_changes: List[str] = field(default_factory=list)
    deprecated_features: List[str] = field(default_factory=list)
    new_features: List[str] = field(default_factory=list)
    migration_effort: str = ""  # low, medium, high, critical
    estimated_hours: int = 0
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'from_version': str(self.from_version),
            'to_version': str(self.to_version),
            'compatibility_level': self.compatibility_level.value,
            'breaking_changes_count': len(self.breaking_changes),
            'breaking_changes': self.breaking_changes,
            'deprecated_features': self.deprecated_features,
            'new_features': self.new_features,
            'migration_effort': self.migration_effort,
            'estimated_hours': self.estimated_hours,
            'recommendations': self.recommendations
        }


class BackwardCompatibilityChecker:
    """Checks backward compatibility between API versions."""

    @staticmethod
    def check_compatibility(old_version: APIVersion, new_version: APIVersion) -> CompatibilityReport:
        """Check backward compatibility between versions."""
        breaking_changes = []
        deprecated_features = []
        new_features = []
        recommendations = []

        # Check for removed endpoints
        old_paths = {(e.path, e.method) for e in old_version.endpoints}
        new_paths = {(e.path, e.method) for e in new_version.endpoints}
        
        removed_endpoints = old_paths - new_paths
        if removed_endpoints:
            for path, method in removed_endpoints:
                breaking_changes.append(f"Endpoint removed: {method} {path}")
            recommendations.append("Ensure clients are updated before endpoint removal")

        # Check for deprecated endpoints
        for endpoint in new_version.endpoints:
            if endpoint.deprecated:
                deprecated_features.append(f"{endpoint.method} {endpoint.path}")
                if endpoint.removal_date:
                    days = (endpoint.removal_date - datetime.now()).days
                    recommendations.append(f"Update {endpoint.path} usage - removal in {days} days")

        # Check for parameter changes
        for new_endpoint in new_version.endpoints:
            old_endpoint = next(
                (e for e in old_version.endpoints 
                 if e.path == new_endpoint.path and e.method == new_endpoint.method),
                None
            )
            if old_endpoint:
                # Check removed parameters
                if new_endpoint.removed_parameters:
                    for param in new_endpoint.removed_parameters:
                        breaking_changes.append(f"Parameter removed: {param} from {new_endpoint.path}")

        # Check for new features
        for endpoint in new_version.endpoints:
            if endpoint.path not in [e.path for e in old_version.endpoints]:
                new_features.append(f"{endpoint.method} {endpoint.path}")

        # Determine compatibility level
        if len(breaking_changes) == 0:
            compatibility = CompatibilityLevel.FULLY_COMPATIBLE
            migration_effort = "none"
            estimated_hours = 0
        elif len(breaking_changes) <= 2:
            compatibility = CompatibilityLevel.MOSTLY_COMPATIBLE
            migration_effort = "low"
            estimated_hours = 2
        elif len(breaking_changes) <= 5:
            compatibility = CompatibilityLevel.PARTIALLY_COMPATIBLE
            migration_effort = "medium"
            estimated_hours = 8
        else:
            compatibility = CompatibilityLevel.INCOMPATIBLE
            migration_effort = "high"
            estimated_hours = 24

        return CompatibilityReport(
            from_version=old_version.version,
            to_version=new_version.version,
            compatibility_level=compatibility,
            breaking_changes=breaking_changes,
            deprecated_features=deprecated_features,
            new_features=new_features,
            migration_effort=migration_effort,
            estimated_hours=estimated_hours,
            recommendations=recommendations
        )


class VersionManager:
    """Manages API versions and versioning."""

    def __init__(self):
        """Initialize version manager."""
        self.versions: Dict[str, APIVersion] = {}
        self.migration_paths: List[MigrationPath] = []
        self.current_version: Optional[SemanticVersion] = None
        self.supported_versions: List[SemanticVersion] = []
        self.deprecation_log: List[Dict[str, Any]] = []

    def register_version(self, version: APIVersion) -> 'VersionManager':
        """Register a new API version."""
        version_str = str(version.version)
        self.versions[version_str] = version
        self.supported_versions.append(version.version)
        self.supported_versions.sort(reverse=True)
        
        if self.current_version is None or version.version > self.current_version:
            self.current_version = version.version
        
        return self

    def get_version(self, version: SemanticVersion) -> Optional[APIVersion]:
        """Get a specific version."""
        return self.versions.get(str(version))

    def get_versions(self) -> List[APIVersion]:
        """Get all registered versions."""
        return list(self.versions.values())

    def deprecate_endpoint(
        self,
        version: SemanticVersion,
        endpoint_path: str,
        endpoint_method: str,
        removal_date: datetime,
        replacement: Optional[str] = None
    ) -> bool:
        """Mark an endpoint as deprecated in a version."""
        api_version = self.get_version(version)
        if not api_version:
            return False

        for endpoint in api_version.endpoints:
            if endpoint.path == endpoint_path and endpoint.method == endpoint_method:
                endpoint.deprecated = True
                endpoint.deprecation_date = datetime.now()
                endpoint.removal_date = removal_date
                endpoint.replacement = replacement
                
                # Log deprecation
                self.deprecation_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'version': str(version),
                    'endpoint': f"{endpoint_method} {endpoint_path}",
                    'removal_date': removal_date.isoformat(),
                    'replacement': replacement
                })
                
                if endpoint_path not in api_version.deprecated_endpoints:
                    api_version.deprecated_endpoints.append(endpoint_path)
                
                return True
        
        return False

    def check_compatibility(
        self,
        from_version: SemanticVersion,
        to_version: SemanticVersion
    ) -> Optional[CompatibilityReport]:
        """Check compatibility between two versions."""
        old_api = self.get_version(from_version)
        new_api = self.get_version(to_version)
        
        if not old_api or not new_api:
            return None
        
        return BackwardCompatibilityChecker.check_compatibility(old_api, new_api)

    def get_migration_path(
        self,
        from_version: SemanticVersion,
        to_version: SemanticVersion
    ) -> Optional[MigrationPath]:
        """Get migration path between versions."""
        return next(
            (mp for mp in self.migration_paths
             if mp.from_version == from_version and mp.to_version == to_version),
            None
        )

    def add_migration_path(self, path: MigrationPath) -> 'VersionManager':
        """Add a migration path."""
        self.migration_paths.append(path)
        return self

    def get_active_versions(self) -> List[APIVersion]:
        """Get all non-EOL versions."""
        return [v for v in self.versions.values() if not v.is_end_of_life()]

    def get_eol_versions(self) -> List[APIVersion]:
        """Get all EOL versions."""
        return [v for v in self.versions.values() if v.is_end_of_life()]

    def get_deprecated_endpoints_across_versions(self) -> List[Dict[str, Any]]:
        """Get all deprecated endpoints across all versions."""
        deprecated = []
        for version in self.versions.values():
            for endpoint in version.get_deprecated_endpoints():
                deprecated.append({
                    'version': str(version.version),
                    'endpoint': f"{endpoint.method} {endpoint.path}",
                    'deprecation_status': endpoint.get_deprecation_status().value,
                    'days_until_removal': endpoint.days_until_removal(),
                    'replacement': endpoint.replacement
                })
        return deprecated

    def get_version_timeline(self) -> List[Dict[str, Any]]:
        """Get timeline of all versions."""
        timeline = []
        for version in sorted(self.versions.values(), key=lambda v: v.version):
            timeline.append({
                'version': str(version.version),
                'release_date': version.release_date.isoformat(),
                'total_endpoints': len(version.endpoints),
                'status': 'EOL' if version.is_end_of_life() else 'Active',
                'eol_date': version.end_of_life_date.isoformat() if version.end_of_life_date else None
            })
        return timeline

    def get_statistics(self) -> Dict[str, Any]:
        """Get versioning statistics."""
        all_versions = list(self.versions.values())
        active_versions = self.get_active_versions()
        eol_versions = self.get_eol_versions()
        deprecated_endpoints = self.get_deprecated_endpoints_across_versions()

        return {
            'total_versions': len(all_versions),
            'active_versions': len(active_versions),
            'eol_versions': len(eol_versions),
            'current_version': str(self.current_version) if self.current_version else None,
            'total_endpoints': sum(len(v.endpoints) for v in all_versions),
            'deprecated_endpoints_count': len(deprecated_endpoints),
            'migration_paths': len(self.migration_paths),
            'deprecation_events': len(self.deprecation_log)
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'current_version': str(self.current_version) if self.current_version else None,
            'versions': {k: v.to_dict() for k, v in self.versions.items()},
            'statistics': self.get_statistics(),
            'timeline': self.get_version_timeline(),
            'deprecated_endpoints': self.get_deprecated_endpoints_across_versions()
        }


# Singleton instance
_version_manager: Optional[VersionManager] = None


def get_version_manager() -> VersionManager:
    """Get the version manager singleton."""
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager()
    return _version_manager


def reset_version_manager() -> None:
    """Reset the version manager (for testing)."""
    global _version_manager
    _version_manager = None
