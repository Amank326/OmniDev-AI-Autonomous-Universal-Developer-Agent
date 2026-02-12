"""
Phase 12: Enterprise Routes
REST API endpoints for enterprise features
"""

from fastapi import APIRouter, HTTPException, status, Header, Body
from typing import Optional, List, Dict, Any
from datetime import datetime
from .enterprise_service import EnterpriseService
from ..services.subscription_models import SubscriptionTier

router = APIRouter(prefix="/api/v1/enterprise", tags=["enterprise"])
enterprise_service = EnterpriseService()


# ============================================================================
# Helper Functions
# ============================================================================

def _verify_tenant_access(user_id: str, tenant_id: str, required_permission: Optional[str] = None) -> bool:
    """Verify user has access to tenant"""
    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )

    if required_permission:
        has_perm = enterprise_service.check_permission(user_id, required_permission, tenant_id)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {required_permission}"
            )

    return True


# ============================================================================
# Tenant Management Endpoints (5)
# ============================================================================

@router.post("/tenants")
async def create_tenant(
    tenant_name: str = Body(...),
    plan: str = Body("free"),
    data_residency: str = Body("US"),
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, Any]:
    """
    Create a new tenant
    Required permission: tenant:create
    """
    _verify_tenant_access(x_user_id, x_tenant_id)

    # Create tenant with subscription
    tenant, subscription = enterprise_service.create_tenant_with_subscription(
        tenant_name=tenant_name,
        owner_id=x_user_id,
        plan=SubscriptionTier(plan),
        data_residency=data_residency
    )

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create tenant"
        )

    return {
        "status": "success",
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "status": tenant.status.value,
            "created_at": tenant.created_at.isoformat(),
            "owner_id": tenant.owner_id,
        },
        "subscription": subscription.to_dict(),
    }


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, Any]:
    """
    Get tenant details
    Required permission: tenant:read
    """
    _verify_tenant_access(x_user_id, x_tenant_id, "tenant:read")

    tenant = enterprise_service.tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return {
        "id": tenant.id,
        "name": tenant.name,
        "status": tenant.status.value,
        "created_at": tenant.created_at.isoformat(),
        "owner_id": tenant.owner_id,
        "members": tenant.members,
        "data_residency": tenant.data_residency,
        "member_count": len(tenant.members),
    }


@router.put("/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    updates: Dict[str, Any] = Body(...),
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, Any]:
    """
    Update tenant details
    Required permission: tenant:update
    """
    _verify_tenant_access(x_user_id, x_tenant_id, "tenant:update")

    tenant = enterprise_service.tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Update allowed fields
    allowed_fields = {"name", "data_residency"}
    for field in updates:
        if field in allowed_fields:
            setattr(tenant, field, updates[field])

    # Log change
    enterprise_service.log_resource_change(
        action="update",
        resource_type="tenant",
        resource_id=tenant_id,
        user_id=x_user_id,
        tenant_id=tenant_id,
        old_value={"name": tenant.name},
        new_value=updates
    )

    return {
        "status": "success",
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "data_residency": tenant.data_residency,
        }
    }


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    reason: str = Body(""),
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, str]:
    """
    Delete tenant
    Required permission: tenant:delete
    """
    _verify_tenant_access(x_user_id, x_tenant_id, "tenant:delete")

    if enterprise_service.delete_tenant(tenant_id, x_user_id, reason):
        return {"status": "success", "message": "Tenant deleted"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete tenant"
        )


@router.get("/tenants")
async def list_tenants(
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, List]:
    """
    List all tenants for user
    """
    _verify_tenant_access(x_user_id, x_tenant_id)

    # In real implementation, filter by user's accessible tenants
    tenants = []
    for tenant in enterprise_service.tenant_manager.tenants.values():
        if x_user_id in tenant.members or tenant.owner_id == x_user_id:
            tenants.append({
                "id": tenant.id,
                "name": tenant.name,
                "status": tenant.status.value,
                "created_at": tenant.created_at.isoformat(),
                "member_count": len(tenant.members),
            })

    return {"tenants": tenants, "count": len(tenants)}


# ============================================================================
# RBAC Management Endpoints (6)
# ============================================================================

@router.post("/rbac/roles/{user_id}")
async def assign_role(
    user_id: str,
    role: str = Body(...),
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, str]:
    """
    Assign role to user
    Required permission: rbac:manage
    """
    _verify_tenant_access(x_user_id, x_tenant_id, "rbac:manage")

    if enterprise_service.assign_user_role(user_id, role, x_tenant_id, x_user_id):
        return {"status": "success", "message": f"Role {role} assigned to {user_id}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign role"
        )


@router.delete("/rbac/roles/{user_id}")
async def revoke_role(
    user_id: str,
    role: str = Body(...),
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, str]:
    """
    Revoke role from user
    Required permission: rbac:manage
    """
    _verify_tenant_access(x_user_id, x_tenant_id, "rbac:manage")

    if enterprise_service.revoke_user_role(user_id, role, x_tenant_id, x_user_id):
        return {"status": "success", "message": f"Role {role} revoked from {user_id}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to revoke role"
        )


@router.get("/rbac/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: str,
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, Any]:
    """
    Get user's permissions
    Required permission: rbac:view
    """
    _verify_tenant_access(x_user_id, x_tenant_id, "rbac:view")

    permissions = enterprise_service.get_user_permissions(user_id, x_tenant_id)
    roles = enterprise_service.rbac_service.get_user_roles(user_id, x_tenant_id)

    return {
        "user_id": user_id,
        "tenant_id": x_tenant_id,
        "roles": roles,
        "permissions": list(permissions),
        "permission_count": len(permissions),
    }


@router.get("/rbac/users/{user_id}/roles")
async def get_user_roles(
    user_id: str,
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, Any]:
    """
    Get user's roles
    """
    _verify_tenant_access(x_user_id, x_tenant_id)

    roles = enterprise_service.rbac_service.get_user_roles(user_id, x_tenant_id)

    return {
        "user_id": user_id,
        "tenant_id": x_tenant_id,
        "roles": roles,
        "role_count": len(roles),
    }


@router.post("/rbac/permissions/check")
async def check_permission(
    user_id: str = Body(...),
    permission: str = Body(...),
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, Any]:
    """
    Check if user has specific permission
    """
    _verify_tenant_access(x_user_id, x_tenant_id)

    has_perm = enterprise_service.check_permission(user_id, permission, x_tenant_id)

    return {
        "user_id": user_id,
        "permission": permission,
        "has_permission": has_perm,
    }


@router.get("/rbac/roles")
async def list_all_roles(
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, List]:
    """
    List all available roles
    Required permission: rbac:view
    """
    _verify_tenant_access(x_user_id, x_tenant_id, "rbac:view")

    roles = enterprise_service.rbac_service.get_all_roles()

    return {
        "roles": roles,
        "role_count": len(roles),
    }


# ============================================================================
# Audit Logging Endpoints (2)
# ============================================================================

@router.get("/audit/logs")
async def get_audit_logs(
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, Any]:
    """
    Get audit logs for tenant
    Required permission: audit:view
    """
    _verify_tenant_access(x_user_id, x_tenant_id, "audit:view")

    filters = {}
    if event_type:
        filters["event_type"] = event_type
    if user_id:
        filters["user_id"] = user_id

    logs = enterprise_service.get_audit_log(x_tenant_id, filters=filters, limit=limit)

    return {
        "logs": logs,
        "count": len(logs),
        "filters": filters,
    }


@router.post("/audit/export")
async def export_audit_logs(
    format: str = Body("json"),
    event_type: Optional[str] = Body(None),
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, Any]:
    """
    Export audit logs
    Required permission: audit:export
    """
    _verify_tenant_access(x_user_id, x_tenant_id, "audit:export")

    filters = {"event_type": event_type} if event_type else None

    content = enterprise_service.export_audit_log(x_tenant_id, format=format, filters=filters)

    # Log the export
    enterprise_service.log_user_action(
        event_type="audit.export",
        user_id=x_user_id,
        tenant_id=x_tenant_id,
        description=f"Exported audit logs (format={format})",
    )

    return {
        "status": "success",
        "format": format,
        "content_preview": content[:500] if content else None,
        "export_date": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Subscription Endpoints (2)
# ============================================================================

@router.get("/subscriptions/{tenant_id}")
async def get_subscription(
    tenant_id: str,
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, Any]:
    """
    Get subscription for tenant
    Required permission: billing:view
    """
    _verify_tenant_access(x_user_id, x_tenant_id, "billing:view")

    subscription = enterprise_service.get_subscription(tenant_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    quota_check = enterprise_service.check_quota(tenant_id)

    return {
        "subscription": subscription.to_dict(),
        "quota_check": quota_check,
    }


@router.post("/subscriptions/{tenant_id}/upgrade")
async def upgrade_subscription(
    tenant_id: str,
    new_tier: str = Body(...),
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, str]:
    """
    Upgrade subscription tier
    Required permission: billing:manage
    """
    _verify_tenant_access(x_user_id, x_tenant_id, "billing:manage")

    if enterprise_service.upgrade_subscription(tenant_id, SubscriptionTier(new_tier), x_user_id):
        return {
            "status": "success",
            "message": f"Subscription upgraded to {new_tier}",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upgrade subscription"
        )


# ============================================================================
# Enterprise Health & Status (2)
# ============================================================================

@router.get("/status/{tenant_id}")
async def get_enterprise_status(
    tenant_id: str,
    x_user_id: str = Header(...),
    x_tenant_id: str = Header(...)
) -> Dict[str, Any]:
    """
    Get comprehensive enterprise status
    """
    _verify_tenant_access(x_user_id, x_tenant_id)

    return enterprise_service.get_enterprise_status(tenant_id)


@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """
    Get system health across all tenants
    """
    return enterprise_service.get_system_health()
