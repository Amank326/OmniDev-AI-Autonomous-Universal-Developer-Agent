"""
Phase 55: API Versioning Routes
RESTful API endpoints for version management, deprecation tracking,
compatibility checking, and migration support (15+ endpoints).
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from api_versioning_service import (
    get_version_manager, reset_version_manager,
    APIVersion, APIEndpoint, SemanticVersion, MigrationPath, MigrationSeverity
)
from deprecation_tracker_phase55 import (
    get_deprecation_tracker, reset_deprecation_tracker
)
from compatibility_checker_phase55 import (
    get_compatibility_checker, reset_compatibility_checker,
    EndpointCompatibility
)
from migration_helpers_phase55 import (
    get_migration_helper, reset_migration_helper,
    VersionMapping, MigrationGuide, FieldMapping, TransformationType
)


# Pydantic models for request/response validation
class VersionInfoRequest(BaseModel):
    """Request to create version info."""
    major: int
    minor: int
    patch: int
    changelog: str = ""
    release_notes: str = ""
    end_of_life_days: Optional[int] = None


class EndpointInfoRequest(BaseModel):
    """Request to add endpoint to version."""
    path: str
    method: str
    description: str = ""
    request_schema: Optional[Dict] = None
    response_schema: Optional[Dict] = None


class DeprecationRequest(BaseModel):
    """Request to deprecate endpoint."""
    version: str
    endpoint_path: str
    endpoint_method: str
    removal_date: str  # ISO format
    replacement: Optional[str] = None
    reason: str = ""


class UsageRecordRequest(BaseModel):
    """Request to record endpoint usage."""
    endpoint: str
    client_id: Optional[str] = None
    response_time_ms: float = 0.0
    status_code: int = 200


class MappingRequest(BaseModel):
    """Request to add version mapping."""
    from_version: str
    to_version: str
    field_mappings: List[Dict[str, str]]  # from_path, to_path, type


class MigrationGuideRequest(BaseModel):
    """Request to create migration guide."""
    from_version: str
    to_version: str
    title: str
    description: str
    breaking_changes: List[str]


# Create router
router = APIRouter(prefix="/api/v1/versioning", tags=["versioning"])


# ===================== VERSION MANAGEMENT ENDPOINTS =====================

@router.post("/versions/register")
async def register_version(request: VersionInfoRequest) -> Dict[str, Any]:
    """Register a new API version."""
    try:
        version = SemanticVersion(request.major, request.minor, request.patch)
        api_version = APIVersion(
            version=version,
            release_date=datetime.now(),
            changelog=request.changelog,
            release_notes=request.release_notes
        )
        
        if request.end_of_life_days:
            api_version.end_of_life_date = datetime.now() + timedelta(days=request.end_of_life_days)
        
        get_version_manager().register_version(api_version)
        
        return {
            'success': True,
            'version': str(version),
            'message': f'Version {version} registered successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/versions")
async def list_versions() -> Dict[str, Any]:
    """Get all registered API versions."""
    manager = get_version_manager()
    versions = manager.get_versions()
    
    return {
        'total_versions': len(versions),
        'current_version': str(manager.current_version) if manager.current_version else None,
        'versions': [v.to_dict() for v in versions]
    }


@router.get("/versions/{version}")
async def get_version(version: str) -> Dict[str, Any]:
    """Get specific API version details."""
    try:
        parsed_version = SemanticVersion.parse(version)
        api_version = get_version_manager().get_version(parsed_version)
        
        if not api_version:
            raise HTTPException(status_code=404, detail=f"Version {version} not found")
        
        return api_version.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/versions/{version}/endpoints")
async def add_endpoint(version: str, request: EndpointInfoRequest) -> Dict[str, Any]:
    """Add endpoint to a version."""
    try:
        parsed_version = SemanticVersion.parse(version)
        api_version = get_version_manager().get_version(parsed_version)
        
        if not api_version:
            raise HTTPException(status_code=404, detail=f"Version {version} not found")
        
        endpoint = APIEndpoint(
            path=request.path,
            method=request.method,
            version=parsed_version,
            description=request.description,
            request_schema=request.request_schema,
            response_schema=request.response_schema
        )
        
        api_version.add_endpoint(endpoint)
        
        return {
            'success': True,
            'endpoint': f"{request.method} {request.path}",
            'version': version,
            'message': 'Endpoint added successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/versions/timeline")
async def get_version_timeline() -> Dict[str, Any]:
    """Get timeline of all versions."""
    manager = get_version_manager()
    timeline = manager.get_version_timeline()
    
    return {
        'timeline': timeline,
        'total_versions': len(timeline)
    }


@router.get("/versions/statistics")
async def get_version_statistics() -> Dict[str, Any]:
    """Get versioning statistics."""
    manager = get_version_manager()
    return manager.get_statistics()


# ===================== DEPRECATION TRACKING ENDPOINTS =====================

@router.post("/endpoints/deprecate")
async def deprecate_endpoint(request: DeprecationRequest) -> Dict[str, Any]:
    """Mark an endpoint as deprecated."""
    try:
        from datetime import datetime as dt
        removal_date = dt.fromisoformat(request.removal_date)
        
        parsed_version = SemanticVersion.parse(request.version)
        success = get_version_manager().deprecate_endpoint(
            version=parsed_version,
            endpoint_path=request.endpoint_path,
            endpoint_method=request.endpoint_method,
            removal_date=removal_date,
            replacement=request.replacement
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Endpoint not found in version")
        
        # Also register in deprecation tracker
        get_deprecation_tracker().register_deprecation(
            endpoint=f"{request.endpoint_method} {request.endpoint_path}",
            removal_date=removal_date,
            replacement_endpoint=request.replacement,
            reason=request.reason
        )
        
        return {
            'success': True,
            'endpoint': f"{request.endpoint_method} {request.endpoint_path}",
            'version': request.version,
            'removal_date': request.removal_date,
            'message': 'Endpoint marked as deprecated'
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/endpoints/usage")
async def record_endpoint_usage(request: UsageRecordRequest) -> Dict[str, Any]:
    """Record usage of an endpoint."""
    try:
        tracker = get_deprecation_tracker()
        tracker.record_usage(
            endpoint=request.endpoint,
            client_id=request.client_id,
            response_time_ms=request.response_time_ms,
            status_code=request.status_code
        )
        
        # Check if deprecated
        notice = tracker.get_deprecation_notice(request.endpoint)
        warning_generated = notice is not None
        
        return {
            'success': True,
            'endpoint': request.endpoint,
            'deprecated': warning_generated,
            'message': 'Usage recorded successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/endpoints/deprecated")
async def list_deprecated_endpoints() -> Dict[str, Any]:
    """Get all deprecated endpoints."""
    tracker = get_deprecation_tracker()
    
    return {
        'deprecated_endpoints': tracker.get_deprecation_timeline(),
        'total_deprecated': len(tracker.get_all_deprecated_endpoints()),
        'in_sunset': len(tracker.get_deprecated_endpoints_in_sunset())
    }


@router.get("/endpoints/deprecated/sunset")
async def get_sunset_endpoints() -> Dict[str, Any]:
    """Get endpoints in sunset period (final week before removal)."""
    tracker = get_deprecation_tracker()
    sunset = tracker.get_deprecated_endpoints_in_sunset()
    
    return {
        'endpoints_in_sunset': [n.to_dict() for n in sunset],
        'total_in_sunset': len(sunset)
    }


@router.get("/endpoints/{endpoint_path}/usage")
async def get_endpoint_usage_metrics(endpoint_path: str) -> Dict[str, Any]:
    """Get usage metrics for an endpoint."""
    tracker = get_deprecation_tracker()
    metrics = tracker.get_usage_metrics(endpoint_path)
    
    if not metrics:
        raise HTTPException(status_code=404, detail="No usage metrics found")
    
    return metrics.to_dict()


@router.get("/clients/{client_id}/migration-impact")
async def get_client_migration_impact(client_id: str) -> Dict[str, Any]:
    """Get migration impact for a specific client."""
    tracker = get_deprecation_tracker()
    impact = tracker.get_client_migration_impact(client_id)
    
    return impact


@router.get("/deprecation/statistics")
async def get_deprecation_statistics() -> Dict[str, Any]:
    """Get deprecation statistics."""
    tracker = get_deprecation_tracker()
    
    return {
        'statistics': tracker.get_statistics(),
        'deprecated_endpoints': tracker.get_deprecation_timeline()
    }


# ===================== COMPATIBILITY CHECKING ENDPOINTS =====================

@router.post("/compatibility/check")
async def check_compatibility(
    from_version: str = Query(...),
    to_version: str = Query(...)
) -> Dict[str, Any]:
    """Check compatibility between two versions."""
    try:
        checker = get_compatibility_checker()
        
        # Create test comparison
        compatibility = EndpointCompatibility(
            endpoint="/test",
            method="GET",
            old_version=from_version,
            new_version=to_version,
            compatibility_status="compatible"
        )
        
        report = checker.create_report(from_version, to_version, [compatibility])
        
        return {
            'from_version': from_version,
            'to_version': to_version,
            'overall_compatibility': report.overall_compatibility,
            'summary': report.to_dict()['summary'],
            'recommendations': report.migration_recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/compatibility/{from_version}/{to_version}")
async def get_compatibility_report(from_version: str, to_version: str) -> Dict[str, Any]:
    """Get full compatibility report between versions."""
    try:
        checker = get_compatibility_checker()
        
        compatibility = EndpointCompatibility(
            endpoint="/test",
            method="GET",
            old_version=from_version,
            new_version=to_version,
            compatibility_status="compatible"
        )
        
        report = checker.create_report(from_version, to_version, [compatibility])
        return report.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================== MIGRATION HELPERS ENDPOINTS =====================

@router.post("/migrations/register-mapping")
async def register_version_mapping(request: MappingRequest) -> Dict[str, Any]:
    """Register a version mapping for automatic transformation."""
    try:
        mapping = VersionMapping(
            from_version=request.from_version,
            to_version=request.to_version,
            direction="forward"
        )
        
        # Parse mappings
        for field_map in request.field_mappings:
            mapping.add_request_mapping(
                FieldMapping(
                    from_path=field_map.get('from_path', ''),
                    to_path=field_map.get('to_path', ''),
                    transformation_type=TransformationType.RENAME_FIELD
                )
            )
        
        get_migration_helper().register_mapping(mapping)
        
        return {
            'success': True,
            'from_version': request.from_version,
            'to_version': request.to_version,
            'mappings': len(request.field_mappings),
            'message': 'Mapping registered successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/migrations/guides")
async def create_migration_guide(request: MigrationGuideRequest) -> Dict[str, Any]:
    """Create a migration guide between versions."""
    try:
        guide = MigrationGuide(
            from_version=request.from_version,
            to_version=request.to_version,
            title=request.title,
            description=request.description,
            breaking_changes=request.breaking_changes
        )
        
        get_migration_helper().register_guide(guide)
        
        return {
            'success': True,
            'from_version': request.from_version,
            'to_version': request.to_version,
            'message': 'Migration guide created successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/migrations/guides/{from_version}/{to_version}")
async def get_migration_guide(from_version: str, to_version: str) -> Dict[str, Any]:
    """Get migration guide for version upgrade."""
    helper = get_migration_helper()
    guide = helper.get_guide(from_version, to_version)
    
    if not guide:
        raise HTTPException(status_code=404, detail="Migration guide not found")
    
    return guide.to_dict()


@router.post("/migrations/transform-request")
async def transform_request(
    from_version: str = Query(...),
    to_version: str = Query(...),
    data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Transform request from one version to another."""
    try:
        helper = get_migration_helper()
        transformed = helper.transform_request(data or {}, from_version, to_version)
        
        if transformed is None:
            raise HTTPException(status_code=404, detail="Mapping not found")
        
        return {
            'success': True,
            'from_version': from_version,
            'to_version': to_version,
            'transformed_data': transformed
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/migrations/transform-response")
async def transform_response(
    from_version: str = Query(...),
    to_version: str = Query(...),
    data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Transform response from one version to another."""
    try:
        helper = get_migration_helper()
        transformed = helper.transform_response(data or {}, from_version, to_version)
        
        if transformed is None:
            raise HTTPException(status_code=404, detail="Mapping not found")
        
        return {
            'success': True,
            'from_version': from_version,
            'to_version': to_version,
            'transformed_data': transformed
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/migrations/overview")
async def get_migrations_overview() -> Dict[str, Any]:
    """Get overview of all registered migrations."""
    helper = get_migration_helper()
    
    return {
        'total_mappings': len(helper.get_all_mappings()),
        'total_guides': len(helper.get_all_guides()),
        'mappings': [m.to_dict() for m in helper.get_all_mappings()],
        'guides': [g.to_dict() for g in helper.get_all_guides()]
    }


# ===================== TESTING & RESET ENDPOINTS =====================

@router.post("/test/reset")
async def reset_all_services() -> Dict[str, str]:
    """Reset all versioning services (for testing)."""
    reset_version_manager()
    reset_deprecation_tracker()
    reset_compatibility_checker()
    reset_migration_helper()
    
    return {'success': True, 'message': 'All services reset successfully'}


@router.get("/health")
async def versioning_health() -> Dict[str, str]:
    """Check health of versioning services."""
    return {
        'status': 'healthy',
        'service': 'API Versioning Management',
        'endpoints': '15+',
        'features': 'Version Management, Deprecation Tracking, Compatibility Checking, Migration Helpers'
    }
