"""
Phase 55: Backward Compatibility Checker
Comprehensive compatibility analysis with breaking change detection,
schema comparison, and migration recommendations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
import json
import re


class ChangeType(Enum):
    """Type of change between versions."""
    ADDED_ENDPOINT = "added_endpoint"
    REMOVED_ENDPOINT = "removed_endpoint"
    DEPRECATED_ENDPOINT = "deprecated_endpoint"
    MODIFIED_ENDPOINT = "modified_endpoint"
    
    # Parameter changes
    PARAMETER_ADDED = "parameter_added"
    PARAMETER_REMOVED = "parameter_removed"
    PARAMETER_TYPE_CHANGED = "parameter_type_changed"
    PARAMETER_REQUIRED_CHANGED = "parameter_required_changed"
    
    # Response changes
    RESPONSE_FIELD_ADDED = "response_field_added"
    RESPONSE_FIELD_REMOVED = "response_field_removed"
    RESPONSE_FIELD_TYPE_CHANGED = "response_field_type_changed"
    
    # Status code changes
    STATUS_CODE_ADDED = "status_code_added"
    STATUS_CODE_REMOVED = "status_code_removed"


class ChangeSeverity(Enum):
    """Severity of a breaking change."""
    NONE = "none"  # Not breaking
    LOW = "low"  # Minor, doesn't affect most clients
    MEDIUM = "medium"  # Affects some clients
    HIGH = "high"  # Affects many clients
    CRITICAL = "critical"  # Breaking change for most clients


@dataclass
class SchemaChange:
    """Represents a change in schema."""
    change_type: ChangeType
    severity: ChangeSeverity
    field: str
    old_value: Any = None
    new_value: Any = None
    description: str = ""
    breaking: bool = False
    requires_migration: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'change_type': self.change_type.value,
            'severity': self.severity.value,
            'field': self.field,
            'old_value': str(self.old_value),
            'new_value': str(self.new_value),
            'description': self.description,
            'breaking': self.breaking,
            'requires_migration': self.requires_migration
        }


@dataclass
class EndpointCompatibility:
    """Compatibility information for an endpoint."""
    endpoint: str
    method: str
    old_version: str
    new_version: str
    compatibility_status: str  # compatible, breaking, modified
    breaking_changes: List[SchemaChange] = field(default_factory=list)
    non_breaking_changes: List[SchemaChange] = field(default_factory=list)
    migration_path: List[str] = field(default_factory=list)
    risk_level: str = "low"  # low, medium, high, critical

    def has_breaking_changes(self) -> bool:
        """Check if endpoint has breaking changes."""
        return len(self.breaking_changes) > 0

    def get_migration_effort(self) -> str:
        """Estimate migration effort."""
        if not self.breaking_changes:
            return "none"
        if len(self.breaking_changes) <= 2:
            return "low"
        elif len(self.breaking_changes) <= 5:
            return "medium"
        else:
            return "high"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'endpoint': self.endpoint,
            'method': self.method,
            'old_version': self.old_version,
            'new_version': self.new_version,
            'compatibility_status': self.compatibility_status,
            'has_breaking_changes': self.has_breaking_changes(),
            'breaking_changes_count': len(self.breaking_changes),
            'non_breaking_changes_count': len(self.non_breaking_changes),
            'migration_effort': self.get_migration_effort(),
            'risk_level': self.risk_level,
            'breaking_changes': [c.to_dict() for c in self.breaking_changes],
            'non_breaking_changes': [c.to_dict() for c in self.non_breaking_changes]
        }


@dataclass
class CompatibilityReport:
    """Comprehensive compatibility report between versions."""
    from_version: str
    to_version: str
    analysis_date: str
    overall_compatibility: str  # compatible, mostly_compatible, broken
    endpoints_analyzed: int = 0
    breaking_changes_found: int = 0
    removals: int = 0
    additions: int = 0
    modifications: int = 0
    endpoint_changes: List[EndpointCompatibility] = field(default_factory=list)
    migration_recommendations: List[str] = field(default_factory=list)
    estimated_migration_hours: int = 0

    def get_affected_endpoints(self) -> List[EndpointCompatibility]:
        """Get all affected (changed) endpoints."""
        return [e for e in self.endpoint_changes if e.compatibility_status != "compatible"]

    def get_breaking_endpoints(self) -> List[EndpointCompatibility]:
        """Get endpoints with breaking changes."""
        return [e for e in self.endpoint_changes if e.has_breaking_changes()]

    def get_risk_summary(self) -> Dict[str, int]:
        """Get summary of risk levels."""
        return {
            'low': len([e for e in self.endpoint_changes if e.risk_level == 'low']),
            'medium': len([e for e in self.endpoint_changes if e.risk_level == 'medium']),
            'high': len([e for e in self.endpoint_changes if e.risk_level == 'high']),
            'critical': len([e for e in self.endpoint_changes if e.risk_level == 'critical'])
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'from_version': self.from_version,
            'to_version': self.to_version,
            'analysis_date': self.analysis_date,
            'overall_compatibility': self.overall_compatibility,
            'summary': {
                'endpoints_analyzed': self.endpoints_analyzed,
                'breaking_changes': self.breaking_changes_found,
                'removed_endpoints': self.removals,
                'added_endpoints': self.additions,
                'modified_endpoints': self.modifications
            },
            'risk_distribution': self.get_risk_summary(),
            'affected_endpoints': len(self.get_affected_endpoints()),
            'breaking_endpoints': len(self.get_breaking_endpoints()),
            'migration_effort_hours': self.estimated_migration_hours,
            'recommendations': self.migration_recommendations
        }


class SchemaComparator:
    """Compares schemas between API versions."""

    @staticmethod
    def compare_parameters(
        old_params: Dict[str, Any],
        new_params: Dict[str, Any]
    ) -> Tuple[List[SchemaChange], List[SchemaChange]]:
        """Compare parameter schemas."""
        breaking = []
        non_breaking = []

        old_param_names = set(old_params.keys()) if old_params else set()
        new_param_names = set(new_params.keys()) if new_params else set()

        # Check for removed parameters
        for param in old_param_names - new_param_names:
            breaking.append(SchemaChange(
                change_type=ChangeType.PARAMETER_REMOVED,
                severity=ChangeSeverity.HIGH,
                field=param,
                description=f"Parameter '{param}' removed",
                breaking=True,
                requires_migration=True
            ))

        # Check for added parameters
        for param in new_param_names - old_param_names:
            old_schema = new_params.get(param, {})
            required = old_schema.get('required', False)
            
            if required:
                breaking.append(SchemaChange(
                    change_type=ChangeType.PARAMETER_ADDED,
                    severity=ChangeSeverity.MEDIUM,
                    field=param,
                    description=f"Required parameter '{param}' added",
                    breaking=True,
                    requires_migration=True
                ))
            else:
                non_breaking.append(SchemaChange(
                    change_type=ChangeType.PARAMETER_ADDED,
                    severity=ChangeSeverity.NONE,
                    field=param,
                    description=f"Optional parameter '{param}' added"
                ))

        # Check for modified parameters
        for param in old_param_names & new_param_names:
            old_schema = old_params.get(param, {})
            new_schema = new_params.get(param, {})

            # Type changes
            old_type = old_schema.get('type')
            new_type = new_schema.get('type')
            
            if old_type and new_type and old_type != new_type:
                breaking.append(SchemaChange(
                    change_type=ChangeType.PARAMETER_TYPE_CHANGED,
                    severity=ChangeSeverity.HIGH,
                    field=param,
                    old_value=old_type,
                    new_value=new_type,
                    description=f"Parameter '{param}' type changed from {old_type} to {new_type}",
                    breaking=True,
                    requires_migration=True
                ))

            # Required changes
            old_required = old_schema.get('required', False)
            new_required = new_schema.get('required', False)
            
            if not old_required and new_required:
                breaking.append(SchemaChange(
                    change_type=ChangeType.PARAMETER_REQUIRED_CHANGED,
                    severity=ChangeSeverity.MEDIUM,
                    field=param,
                    description=f"Parameter '{param}' is now required",
                    breaking=True,
                    requires_migration=True
                ))

        return breaking, non_breaking

    @staticmethod
    def compare_response_schemas(
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> Tuple[List[SchemaChange], List[SchemaChange]]:
        """Compare response schemas."""
        breaking = []
        non_breaking = []

        old_fields = set(old_schema.keys()) if old_schema else set()
        new_fields = set(new_schema.keys()) if new_schema else set()

        # Removed fields
        for field in old_fields - new_fields:
            breaking.append(SchemaChange(
                change_type=ChangeType.RESPONSE_FIELD_REMOVED,
                severity=ChangeSeverity.HIGH,
                field=field,
                description=f"Response field '{field}' removed",
                breaking=True,
                requires_migration=True
            ))

        # Added fields
        for field in new_fields - old_fields:
            non_breaking.append(SchemaChange(
                change_type=ChangeType.RESPONSE_FIELD_ADDED,
                severity=ChangeSeverity.NONE,
                field=field,
                description=f"Response field '{field}' added"
            ))

        # Modified fields
        for field in old_fields & new_fields:
            old_type = old_schema.get(field, {}).get('type') if isinstance(old_schema.get(field), dict) else str(type(old_schema.get(field)))
            new_type = new_schema.get(field, {}).get('type') if isinstance(new_schema.get(field), dict) else str(type(new_schema.get(field)))

            if old_type != new_type:
                breaking.append(SchemaChange(
                    change_type=ChangeType.RESPONSE_FIELD_TYPE_CHANGED,
                    severity=ChangeSeverity.HIGH,
                    field=field,
                    old_value=old_type,
                    new_value=new_type,
                    description=f"Response field '{field}' type changed",
                    breaking=True,
                    requires_migration=True
                ))

        return breaking, non_breaking

    @staticmethod
    def compare_status_codes(
        old_codes: Set[int],
        new_codes: Set[int]
    ) -> Tuple[List[SchemaChange], List[SchemaChange]]:
        """Compare expected status codes."""
        breaking = []
        non_breaking = []

        # Removed status codes
        for code in old_codes - new_codes:
            breaking.append(SchemaChange(
                change_type=ChangeType.STATUS_CODE_REMOVED,
                severity=ChangeSeverity.LOW,
                field=str(code),
                description=f"Status code {code} no longer returned",
                breaking=True
            ))

        # Added status codes
        for code in new_codes - old_codes:
            non_breaking.append(SchemaChange(
                change_type=ChangeType.STATUS_CODE_ADDED,
                severity=ChangeSeverity.NONE,
                field=str(code),
                description=f"New status code {code} may be returned"
            ))

        return breaking, non_breaking


class CompatibilityChecker:
    """Checks compatibility between API versions."""

    def __init__(self):
        """Initialize checker."""
        self.comparator = SchemaComparator()
        self.cache: Dict[str, CompatibilityReport] = {}

    def compare_endpoints(
        self,
        endpoint: str,
        method: str,
        old_version: str,
        new_version: str,
        old_request_schema: Optional[Dict] = None,
        new_request_schema: Optional[Dict] = None,
        old_response_schema: Optional[Dict] = None,
        new_response_schema: Optional[Dict] = None,
        old_status_codes: Optional[Set[int]] = None,
        new_status_codes: Optional[Set[int]] = None
    ) -> EndpointCompatibility:
        """Compare two endpoint versions."""
        breaking_changes = []
        non_breaking_changes = []

        # Compare request schemas
        if old_request_schema and new_request_schema:
            req_breaking, req_non_breaking = self.comparator.compare_parameters(
                old_request_schema, new_request_schema
            )
            breaking_changes.extend(req_breaking)
            non_breaking_changes.extend(req_non_breaking)

        # Compare response schemas
        if old_response_schema and new_response_schema:
            resp_breaking, resp_non_breaking = self.comparator.compare_response_schemas(
                old_response_schema, new_response_schema
            )
            breaking_changes.extend(resp_breaking)
            non_breaking_changes.extend(resp_non_breaking)

        # Compare status codes
        if old_status_codes and new_status_codes:
            code_breaking, code_non_breaking = self.comparator.compare_status_codes(
                old_status_codes, new_status_codes
            )
            breaking_changes.extend(code_breaking)
            non_breaking_changes.extend(code_non_breaking)

        # Determine overall compatibility
        if breaking_changes:
            compatibility_status = "breaking"
            risk_level = self._calculate_risk_level(breaking_changes)
        elif non_breaking_changes:
            compatibility_status = "modified"
            risk_level = "low"
        else:
            compatibility_status = "compatible"
            risk_level = "low"

        # Create migration path
        migration_path = self._create_migration_path(
            endpoint, breaking_changes, non_breaking_changes
        )

        return EndpointCompatibility(
            endpoint=endpoint,
            method=method,
            old_version=old_version,
            new_version=new_version,
            compatibility_status=compatibility_status,
            breaking_changes=breaking_changes,
            non_breaking_changes=non_breaking_changes,
            migration_path=migration_path,
            risk_level=risk_level
        )

    def _calculate_risk_level(self, breaking_changes: List[SchemaChange]) -> str:
        """Calculate risk level based on breaking changes."""
        if not breaking_changes:
            return "low"
        
        severity_scores = {
            ChangeSeverity.NONE: 0,
            ChangeSeverity.LOW: 1,
            ChangeSeverity.MEDIUM: 2,
            ChangeSeverity.HIGH: 3,
            ChangeSeverity.CRITICAL: 4
        }
        
        avg_score = sum(severity_scores.get(c.severity, 0) for c in breaking_changes) / len(breaking_changes)
        
        if avg_score >= 3:
            return "critical"
        elif avg_score >= 2:
            return "high"
        elif avg_score >= 1:
            return "medium"
        else:
            return "low"

    def _create_migration_path(
        self,
        endpoint: str,
        breaking: List[SchemaChange],
        non_breaking: List[SchemaChange]
    ) -> List[str]:
        """Create migration path for endpoint."""
        path = []
        
        if not breaking:
            return ["No migration needed - endpoint is backward compatible"]
        
        path.append("1. Review breaking changes below:")
        
        for i, change in enumerate(breaking, 1):
            path.append(f"   - {change.description}")
        
        path.append("2. Update your code to handle the new schema")
        path.append("3. Test with the new endpoint version")
        
        return path

    def create_report(
        self,
        from_version: str,
        to_version: str,
        endpoint_comparisons: List[EndpointCompatibility]
    ) -> CompatibilityReport:
        """Create compatibility report."""
        breaking_endpoints = [ec for ec in endpoint_comparisons if ec.has_breaking_changes()]
        total_breaking = sum(len(ec.breaking_changes) for ec in endpoint_comparisons)
        
        # Categorize changes
        removals = len([ec for ec in endpoint_comparisons if ec.compatibility_status == "removed"])
        additions = len([ec for ec in endpoint_comparisons if ec.compatibility_status == "added"])
        modifications_list = [ec for ec in endpoint_comparisons if ec.compatibility_status == "modified"]
        modifications = len(modifications_list)

        # Overall compatibility
        if breaking_endpoints:
            overall = "broken"
        elif modifications > 0:
            overall = "mostly_compatible"
        else:
            overall = "compatible"

        # Estimate migration hours
        hours = sum(ec.get_migration_effort() == "high" and 8 or 
                   ec.get_migration_effort() == "medium" and 4 or 
                   ec.get_migration_effort() == "low" and 2 or 0
                   for ec in breaking_endpoints)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall, breaking_endpoints, endpoint_comparisons
        )

        report = CompatibilityReport(
            from_version=from_version,
            to_version=to_version,
            analysis_date=__import__('datetime').datetime.now().isoformat(),
            overall_compatibility=overall,
            endpoints_analyzed=len(endpoint_comparisons),
            breaking_changes_found=len(breaking_endpoints),
            removals=removals,
            additions=additions,
            modifications=modifications,
            endpoint_changes=endpoint_comparisons,
            migration_recommendations=recommendations,
            estimated_migration_hours=hours
        )

        return report

    def _generate_recommendations(
        self,
        overall_compatibility: str,
        breaking_endpoints: List[EndpointCompatibility],
        all_endpoints: List[EndpointCompatibility]
    ) -> List[str]:
        """Generate migration recommendations."""
        recommendations = []

        if overall_compatibility == "compatible":
            recommendations.append("✓ No action required - Version is fully backward compatible")
        elif overall_compatibility == "mostly_compatible":
            recommendations.append("⚠ Review new fields and parameters in modified endpoints")
        else:
            recommendations.append("⚠ BREAKING CHANGES DETECTED - Migration required")
            recommendations.append(f"  - {len(breaking_endpoints)} endpoints have breaking changes")
            recommendations.append(f"  - Estimated migration effort: {self._estimate_total_effort(breaking_endpoints)}")
            
            critical_endpoints = [e for e in breaking_endpoints if e.risk_level == 'critical']
            if critical_endpoints:
                recommendations.append(f"  - {len(critical_endpoints)} endpoint(s) have CRITICAL risk level")

        return recommendations

    def _estimate_total_effort(self, endpoints: List[EndpointCompatibility]) -> str:
        """Estimate total migration effort."""
        high_count = len([e for e in endpoints if e.get_migration_effort() == "high"])
        medium_count = len([e for e in endpoints if e.get_migration_effort() == "medium"])
        
        if high_count >= 3:
            return "High (8+ hours)"
        elif high_count >= 1 or medium_count >= 3:
            return "Medium (4-8 hours)"
        else:
            return "Low (1-4 hours)"


# Singleton instance
_compatibility_checker: Optional[CompatibilityChecker] = None


def get_compatibility_checker() -> CompatibilityChecker:
    """Get the compatibility checker singleton."""
    global _compatibility_checker
    if _compatibility_checker is None:
        _compatibility_checker = CompatibilityChecker()
    return _compatibility_checker


def reset_compatibility_checker() -> None:
    """Reset the compatibility checker (for testing)."""
    global _compatibility_checker
    _compatibility_checker = None
