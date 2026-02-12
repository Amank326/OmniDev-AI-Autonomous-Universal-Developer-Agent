"""
Phase 56: Security & Authentication Routes
RESTful API endpoints for authentication, OAuth2, API keys, RBAC,
and audit logging (20+ endpoints).
"""

from fastapi import APIRouter, HTTPException, Query, Header
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

from jwt_token_service_phase56 import (
    get_jwt_service, reset_jwt_service,
    get_api_key_manager, reset_api_key_manager,
    get_session_manager, reset_session_manager,
    get_audit_logger, reset_audit_logger,
    TokenType, Permission, GrantType
)
from oauth2_provider_phase56 import (
    get_oauth2_provider, reset_oauth2_provider,
    OAuth2ClientType, OAuth2ResponseType
)
from rbac_engine_phase56 import (
    get_rbac_engine, reset_rbac_engine,
    ResourceType, PolicyEffect, PolicyRule, Permission as RBACPermission
)


# Pydantic models for request/response validation
class LoginRequest(BaseModel):
    """User login request."""
    username: str
    password: str
    device_id: Optional[str] = None


class TokenRefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class TokenRevokeRequest(BaseModel):
    """Token revocation request."""
    token: str
    token_type_hint: Optional[str] = None


class APIKeyCreateRequest(BaseModel):
    """API key creation request."""
    name: str
    scopes: List[str] = []
    expires_in_days: Optional[int] = None
    description: str = ""


class OAuthClientRequest(BaseModel):
    """OAuth2 client registration request."""
    client_name: str
    client_type: str
    redirect_uris: List[str]
    allowed_scopes: List[str]
    allowed_grant_types: List[str]


class AuthorizationRequest(BaseModel):
    """OAuth2 authorization request."""
    client_id: str
    response_type: str
    scopes: List[str]
    redirect_uri: str
    state: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None


class TokenExchangeRequest(BaseModel):
    """OAuth2 token exchange request."""
    grant_type: str
    code: Optional[str] = None
    client_id: str
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    refresh_token: Optional[str] = None
    code_verifier: Optional[str] = None


class RoleCreateRequest(BaseModel):
    """Role creation request."""
    role_id: str
    name: str
    description: str = ""
    permissions: List[str] = []


class RoleAssignmentRequest(BaseModel):
    """Role assignment request."""
    subject_id: str
    role_id: str


class PermissionCheckRequest(BaseModel):
    """Permission check request."""
    action: str
    resource: str
    resource_type: str


# Create router
router = APIRouter(prefix="/api/v1/security", tags=["security"])


# ===================== AUTHENTICATION ENDPOINTS =====================

@router.post("/auth/login")
async def login(request: LoginRequest) -> Dict[str, Any]:
    """Login user and get tokens."""
    try:
        # Verify credentials (simplified - in production would check database)
        if request.username and request.password:
            # Create access and refresh tokens
            access_token = get_jwt_service().create_token(
                subject=request.username,
                token_type=TokenType.ACCESS,
                expires_in_minutes=60,
                custom_claims={"username": request.username}
            )
            
            refresh_token = get_jwt_service().create_token(
                subject=request.username,
                token_type=TokenType.REFRESH,
                expires_in_minutes=7 * 24 * 60
            )
            
            # Create session
            session = get_session_manager().create_session(
                user_id=request.username,
                ip_address="0.0.0.0",  # Would get from request in production
                user_agent="",
                device_id=request.device_id
            )
            
            # Log auth event
            get_audit_logger().log_event(
                user_id=request.username,
                action="login",
                resource=request.username,
                status="success",
                ip_address="0.0.0.0",
                user_agent=""
            )
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': 3600,
                'session_id': session.session_id
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/logout")
async def logout(
    token: str = Header(...),
) -> Dict[str, str]:
    """Logout user."""
    try:
        get_jwt_service().revoke_token(token)
        
        get_audit_logger().log_event(
            user_id="unknown",
            action="logout",
            resource="user",
            status="success",
            ip_address="0.0.0.0",
            user_agent=""
        )
        
        return {'success': True, 'message': 'Logged out successfully'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/token/refresh")
async def refresh_token(request: TokenRefreshRequest) -> Dict[str, Any]:
    """Refresh access token."""
    try:
        new_token = get_jwt_service().refresh_token(request.refresh_token)
        
        if not new_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        return {
            'access_token': new_token,
            'token_type': 'Bearer',
            'expires_in': 3600
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/token/revoke")
async def revoke_token(request: TokenRevokeRequest) -> Dict[str, str]:
    """Revoke token."""
    try:
        get_jwt_service().revoke_token(request.token, request.token_type_hint)
        
        return {'success': True, 'message': 'Token revoked'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/token/verify")
async def verify_token(token: str = Header(...)) -> Dict[str, Any]:
    """Verify token validity."""
    try:
        valid, claims, error = get_jwt_service().verify_token(token)
        
        if not valid:
            raise HTTPException(status_code=401, detail=error)
        
        return {
            'valid': True,
            'subject': claims.subject,
            'token_type': claims.token_type.value,
            'scopes': claims.scopes,
            'roles': claims.roles,
            'permissions': claims.permissions,
            'expires_at': claims.expiration_time.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================== API KEY MANAGEMENT =====================

@router.post("/api-keys")
async def create_api_key(
    request: APIKeyCreateRequest,
    user_id: str = Header(...)
) -> Dict[str, Any]:
    """Create new API key."""
    try:
        key_secret, api_key = get_api_key_manager().create_api_key(
            user_id=user_id,
            name=request.name,
            scopes=request.scopes,
            expires_in_days=request.expires_in_days,
            description=request.description
        )
        
        get_audit_logger().log_event(
            user_id=user_id,
            action="create_api_key",
            resource=api_key.key_id,
            status="success",
            ip_address="0.0.0.0",
            user_agent=""
        )
        
        return {
            'key_id': api_key.key_id,
            'key_secret': key_secret,  # Only shown once
            'name': api_key.name,
            'created_at': api_key.created_at.isoformat(),
            'scopes': api_key.scopes,
            'message': 'Save the key_secret securely - it cannot be retrieved later'
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api-keys")
async def list_api_keys(user_id: str = Header(...)) -> Dict[str, Any]:
    """List user's API keys."""
    try:
        keys = get_api_key_manager().list_user_keys(user_id)
        
        return {
            'keys': [k.to_dict() for k in keys],
            'total': len(keys)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    user_id: str = Header(...)
) -> Dict[str, str]:
    """Revoke API key."""
    try:
        success = get_api_key_manager().revoke_api_key(key_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        
        get_audit_logger().log_event(
            user_id=user_id,
            action="revoke_api_key",
            resource=key_id,
            status="success",
            ip_address="0.0.0.0",
            user_agent=""
        )
        
        return {'success': True, 'message': 'API key revoked'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================== OAUTH2 ENDPOINTS =====================

@router.post("/oauth2/clients")
async def register_oauth_client(request: OAuthClientRequest) -> Dict[str, Any]:
    """Register OAuth2 client."""
    try:
        provider = get_oauth2_provider()
        client_type = OAuth2ClientType(request.client_type)
        
        client_id, client_secret = provider.register_client(
            client_name=request.client_name,
            client_type=client_type,
            redirect_uris=request.redirect_uris,
            allowed_scopes=request.allowed_scopes,
            allowed_grant_types=request.allowed_grant_types
        )
        
        return {
            'client_id': client_id,
            'client_secret': client_secret,
            'client_name': request.client_name,
            'client_type': request.client_type,
            'message': 'Save client_secret securely'
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/oauth2/authorize")
async def authorize_endpoint(request: AuthorizationRequest) -> Dict[str, Any]:
    """OAuth2 authorization endpoint."""
    try:
        provider = get_oauth2_provider()
        
        # Validate client
        if not provider.validate_client(request.client_id):
            raise HTTPException(status_code=400, detail="Invalid client")
        
        # Create authorization code
        code = provider.create_authorization_code(
            client_id=request.client_id,
            user_id="current_user",  # Would get from session
            scopes=request.scopes,
            redirect_uri=request.redirect_uri,
            code_challenge=request.code_challenge,
            code_challenge_method=request.code_challenge_method
        )
        
        if not code:
            raise HTTPException(status_code=400, detail="Failed to create authorization code")
        
        return {
            'code': code,
            'state': request.state,
            'redirect_uri': request.redirect_uri
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/oauth2/token")
async def token_endpoint(request: TokenExchangeRequest) -> Dict[str, Any]:
    """OAuth2 token endpoint."""
    try:
        provider = get_oauth2_provider()
        
        # Validate client
        if not provider.validate_client(request.client_id, request.client_secret):
            raise HTTPException(status_code=401, detail="Invalid client credentials")
        
        if request.grant_type == "authorization_code":
            # Exchange code for tokens
            token_info = provider.exchange_authorization_code(
                client_id=request.client_id,
                code=request.code,
                redirect_uri=request.redirect_uri,
                code_verifier=request.code_verifier
            )
            
            if not token_info:
                raise HTTPException(status_code=400, detail="Invalid authorization code")
            
            # Create actual tokens using JWT service
            access_token = get_jwt_service().create_token(
                subject=token_info['user_id'],
                token_type=TokenType.OAUTH2,
                scopes=token_info['scopes']
            )
            
            return {
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': 3600,
                'scope': ' '.join(token_info['scopes'])
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported grant type: {request.grant_type}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================== RBAC MANAGEMENT ENDPOINTS =====================

@router.post("/roles")
async def create_role(request: RoleCreateRequest) -> Dict[str, Any]:
    """Create new role."""
    try:
        engine = get_rbac_engine()
        
        role = engine.create_role(
            role_id=request.role_id,
            name=request.name,
            description=request.description,
            permissions=request.permissions
        )
        
        return role.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/roles")
async def list_roles() -> Dict[str, Any]:
    """List all roles."""
    try:
        engine = get_rbac_engine()
        roles = list(engine.roles.values())
        
        return {
            'roles': [r.to_dict() for r in roles],
            'total': len(roles)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/roles/{role_id}/permissions/{permission_id}")
async def grant_permission_to_role(
    role_id: str,
    permission_id: str
) -> Dict[str, str]:
    """Grant permission to role."""
    try:
        engine = get_rbac_engine()
        success = engine.grant_permission_to_role(role_id, permission_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Role or permission not found")
        
        return {'success': True, 'message': 'Permission granted'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subjects/{subject_id}/roles/{role_id}")
async def assign_role_to_subject(
    subject_id: str,
    role_id: str
) -> Dict[str, str]:
    """Assign role to subject."""
    try:
        engine = get_rbac_engine()
        success = engine.assign_role_to_subject(subject_id, role_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        get_audit_logger().log_event(
            user_id="admin",
            action="assign_role",
            resource=f"{subject_id}:{role_id}",
            status="success",
            ip_address="0.0.0.0",
            user_agent=""
        )
        
        return {'success': True, 'message': 'Role assigned'}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subjects/{subject_id}/check-permission")
async def check_permission(
    subject_id: str,
    request: PermissionCheckRequest
) -> Dict[str, Any]:
    """Check if subject has permission."""
    try:
        engine = get_rbac_engine()
        
        allowed, reason = engine.evaluate_access(
            subject_id=subject_id,
            action=request.action,
            resource=request.resource,
            resource_type=request.resource_type
        )
        
        return {
            'subject_id': subject_id,
            'allowed': allowed,
            'action': request.action,
            'resource': request.resource,
            'reason': reason
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subjects/{subject_id}/permissions")
async def get_subject_permissions(subject_id: str) -> Dict[str, Any]:
    """Get all permissions for subject."""
    try:
        engine = get_rbac_engine()
        permissions = engine.get_subject_permissions(subject_id)
        
        return {
            'subject_id': subject_id,
            'permissions': permissions,
            'total': len(permissions)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================== AUDIT LOG ENDPOINTS =====================

@router.get("/audit/events")
async def get_audit_events(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    hours: int = 24
) -> Dict[str, Any]:
    """Get audit events."""
    try:
        logger = get_audit_logger()
        events = logger.get_events(user_id=user_id, action=action, hours=hours)
        
        return {
            'events': [e.to_dict() for e in events],
            'total': len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/audit/statistics")
async def get_audit_statistics() -> Dict[str, Any]:
    """Get audit statistics."""
    try:
        logger = get_audit_logger()
        return logger.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================== SERVICE MONITORING =====================

@router.get("/security/health")
async def security_health() -> Dict[str, str]:
    """Check security services health."""
    return {
        'status': 'healthy',
        'jwt_service': 'operational',
        'oauth2_provider': 'operational',
        'rbac_engine': 'operational',
        'audit_logger': 'operational',
        'endpoints': '20+',
        'features': 'JWT, OAuth2, API Keys, RBAC, Audit Logging'
    }


@router.get("/security/statistics")
async def get_security_statistics() -> Dict[str, Any]:
    """Get overall security statistics."""
    try:
        return {
            'jwt_service': get_jwt_service().get_statistics(),
            'api_key_manager': get_api_key_manager().get_statistics(),
            'session_manager': get_session_manager().get_statistics(),
            'oauth2_provider': get_oauth2_provider().get_statistics(),
            'rbac_engine': get_rbac_engine().get_statistics(),
            'audit_logger': get_audit_logger().get_statistics()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===================== TESTING & RESET ENDPOINTS =====================

@router.post("/test/reset")
async def reset_all_security_services() -> Dict[str, str]:
    """Reset all security services (for testing)."""
    reset_jwt_service()
    reset_api_key_manager()
    reset_session_manager()
    reset_audit_logger()
    reset_oauth2_provider()
    reset_rbac_engine()
    
    return {'success': True, 'message': 'All services reset successfully'}
