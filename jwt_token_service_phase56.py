"""
Phase 56: Security & Authentication
JWT token generation/validation, OAuth2 support, API key management,
role-based access control (RBAC), and security audit logging.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import jwt
import secrets
import hashlib
from abc import ABC, abstractmethod


class TokenType(Enum):
    """Types of authentication tokens."""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    SESSION = "session"


class Permission(Enum):
    """Standard permissions in the system."""
    # Resource operations
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    
    # Admin operations
    ADMIN = "admin"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_PERMISSIONS = "manage_permissions"
    
    # Security operations
    VIEW_AUDIT = "view_audit"
    MANAGE_SECURITY = "manage_security"
    MANAGE_API_KEYS = "manage_api_keys"
    MANAGE_OAUTH = "manage_oauth"
    
    # Other
    IMPERSONATE = "impersonate"


class GrantType(Enum):
    """OAuth2 grant types."""
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    PASSWORD = "password"
    REFRESH_TOKEN = "refresh_token"
    IMPLICIT = "implicit"
    DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"


class TokenStatus(Enum):
    """Status of authentication token."""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"


@dataclass
class JWTClaims:
    """JWT token claims."""
    subject: str  # user ID
    issue_time: datetime
    expiration_time: datetime
    token_type: TokenType
    scopes: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    issuer: str = "api"
    audience: str = "api-users"
    jti: str = ""  # JWT ID for revocation tracking
    custom_claims: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert claims to dictionary."""
        return {
            'sub': self.subject,
            'iat': int(self.issue_time.timestamp()),
            'exp': int(self.expiration_time.timestamp()),
            'type': self.token_type.value,
            'scopes': self.scopes,
            'roles': self.roles,
            'permissions': self.permissions,
            'iss': self.issuer,
            'aud': self.audience,
            'jti': self.jti,
            **self.custom_claims
        }

    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now() >= self.expiration_time


@dataclass
class TokenPayload:
    """Token response payload."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    scope: str = ""
    id_token: Optional[str] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'access_token': self.access_token,
            'token_type': self.token_type,
            'expires_in': self.expires_in,
            'scope': self.scope
        }
        if self.refresh_token:
            result['refresh_token'] = self.refresh_token
        if self.id_token:
            result['id_token'] = self.id_token
        result.update(self.custom_params)
        return result


@dataclass
class APIKey:
    """API key for service-to-service authentication."""
    key_id: str
    key_secret: str  # hashed
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    scopes: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    enabled: bool = True
    usage_count: int = 0
    description: str = ""

    @staticmethod
    def hash_secret(secret: str) -> str:
        """Hash API key secret."""
        return hashlib.sha256(secret.encode()).hexdigest()

    def verify_secret(self, secret: str) -> bool:
        """Verify API key secret."""
        return self.key_secret == self.hash_secret(secret)

    def is_valid(self) -> bool:
        """Check if key is valid and not expired."""
        if not self.enabled:
            return False
        if self.expires_at and datetime.now() >= self.expires_at:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (public info only)."""
        return {
            'key_id': self.key_id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'enabled': self.enabled,
            'usage_count': self.usage_count,
            'description': self.description,
            'scopes': self.scopes
        }


@dataclass
class Session:
    """User session."""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True
    device_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now() >= self.expires_at

    def is_valid(self) -> bool:
        """Check if session is valid."""
        return self.is_active and not self.is_expired()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'is_active': self.is_active,
            'is_valid': self.is_valid(),
            'ip_address': self.ip_address,
            'device_id': self.device_id
        }


@dataclass
class AuditEvent:
    """Security audit event."""
    event_id: str
    timestamp: datetime
    user_id: Optional[str]
    action: str
    resource: str
    status: str  # success, failure
    ip_address: str
    user_agent: str
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    severity: str = "info"  # info, warning, error, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'action': self.action,
            'resource': self.resource,
            'status': self.status,
            'ip_address': self.ip_address,
            'severity': self.severity,
            'details': self.details,
            'error_message': self.error_message
        }


class JWTTokenService:
    """JWT token generation and validation."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """Initialize token service."""
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.revoked_tokens: Set[str] = set()
        self.token_blacklist: Dict[str, datetime] = {}

    def create_token(
        self,
        subject: str,
        token_type: TokenType,
        expires_in_minutes: int = 60,
        scopes: List[str] = None,
        roles: List[str] = None,
        permissions: List[str] = None,
        custom_claims: Dict[str, Any] = None
    ) -> str:
        """Create JWT token."""
        now = datetime.now()
        expiration = now + timedelta(minutes=expires_in_minutes)
        
        # Generate unique JWT ID
        jti = secrets.token_urlsafe(16)

        claims = JWTClaims(
            subject=subject,
            issue_time=now,
            expiration_time=expiration,
            token_type=token_type,
            scopes=scopes or [],
            roles=roles or [],
            permissions=permissions or [],
            jti=jti,
            custom_claims=custom_claims or {}
        )

        payload = claims.to_dict()
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Tuple[bool, Optional[JWTClaims], Optional[str]]:
        """Verify JWT token."""
        try:
            # Check if token is blacklisted
            if self._is_token_blacklisted(token):
                return False, None, "Token has been revoked"

            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Extract claims
            claims = JWTClaims(
                subject=payload.get('sub'),
                issue_time=datetime.fromtimestamp(payload.get('iat', 0)),
                expiration_time=datetime.fromtimestamp(payload.get('exp', 0)),
                token_type=TokenType(payload.get('type', 'access')),
                scopes=payload.get('scopes', []),
                roles=payload.get('roles', []),
                permissions=payload.get('permissions', []),
                issuer=payload.get('iss', 'api'),
                audience=payload.get('aud', 'api-users'),
                jti=payload.get('jti', ''),
                custom_claims={k: v for k, v in payload.items() 
                              if k not in ['sub', 'iat', 'exp', 'type', 'scopes', 
                                          'roles', 'permissions', 'iss', 'aud', 'jti']}
            )

            if claims.is_expired():
                return False, None, "Token has expired"

            return True, claims, None

        except jwt.InvalidTokenError as e:
            return False, None, str(e)
        except Exception as e:
            return False, None, f"Token validation error: {str(e)}"

    def revoke_token(self, token: str, jti: Optional[str] = None) -> bool:
        """Revoke a token."""
        if jti:
            self.revoked_tokens.add(jti)
        else:
            # Try to extract JTI from token
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm],
                                    options={"verify_signature": False})
                jti = payload.get('jti')
                if jti:
                    self.revoked_tokens.add(jti)
            except:
                pass
        
        self.token_blacklist[token] = datetime.now() + timedelta(hours=1)
        return True

    def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        if token in self.token_blacklist:
            if datetime.now() < self.token_blacklist[token]:
                return True
            else:
                del self.token_blacklist[token]
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm],
                               options={"verify_signature": False})
            jti = payload.get('jti')
            return jti in self.revoked_tokens
        except:
            return False

    def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Create new access token from refresh token."""
        valid, claims, error = self.verify_token(refresh_token)
        
        if not valid or claims.token_type != TokenType.REFRESH:
            return None

        # Create new access token with same claims
        return self.create_token(
            subject=claims.subject,
            token_type=TokenType.ACCESS,
            scopes=claims.scopes,
            roles=claims.roles,
            permissions=claims.permissions
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get token service statistics."""
        return {
            'revoked_tokens': len(self.revoked_tokens),
            'blacklisted_tokens': len(self.token_blacklist),
            'algorithm': self.algorithm
        }


class APIKeyManager:
    """Manages API keys for service authentication."""

    def __init__(self):
        """Initialize API key manager."""
        self.api_keys: Dict[str, APIKey] = {}
        self.key_index: Dict[str, str] = {}  # key_id -> user_id mapping

    def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: List[str] = None,
        permissions: List[str] = None,
        expires_in_days: Optional[int] = None,
        description: str = ""
    ) -> Tuple[str, APIKey]:
        """Create new API key."""
        # Generate key
        key_id = f"key_{secrets.token_urlsafe(16)}"
        key_secret = secrets.token_urlsafe(32)
        
        # Hash secret for storage
        key_secret_hashed = APIKey.hash_secret(key_secret)

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        api_key = APIKey(
            key_id=key_id,
            key_secret=key_secret_hashed,
            name=name,
            created_at=datetime.now(),
            expires_at=expires_at,
            scopes=scopes or [],
            permissions=permissions or [],
            description=description
        )

        self.api_keys[key_id] = api_key
        self.key_index[key_id] = user_id

        # Return unhashed secret (only shown once)
        return key_secret, api_key

    def verify_api_key(self, key_id: str, key_secret: str) -> Tuple[bool, Optional[str]]:
        """Verify API key."""
        api_key = self.api_keys.get(key_id)
        
        if not api_key:
            return False, None

        if not api_key.is_valid():
            return False, None

        if not api_key.verify_secret(key_secret):
            return False, None

        # Update usage
        api_key.last_used = datetime.now()
        api_key.usage_count += 1

        # Return associated user ID
        return True, self.key_index.get(key_id)

    def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """Get API key details."""
        return self.api_keys.get(key_id)

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key."""
        api_key = self.api_keys.get(key_id)
        if api_key:
            api_key.enabled = False
            return True
        return False

    def list_user_keys(self, user_id: str) -> List[APIKey]:
        """List all keys for a user."""
        return [
            self.api_keys[key_id]
            for key_id, u_id in self.key_index.items()
            if u_id == user_id
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get API key statistics."""
        active_keys = sum(1 for k in self.api_keys.values() if k.enabled)
        expired_keys = sum(1 for k in self.api_keys.values() 
                          if k.expires_at and datetime.now() >= k.expires_at)
        
        return {
            'total_keys': len(self.api_keys),
            'active_keys': active_keys,
            'revoked_keys': len(self.api_keys) - active_keys,
            'expired_keys': expired_keys,
            'total_users': len(set(self.key_index.values()))
        }


class SessionManager:
    """Manages user sessions."""

    def __init__(self, session_timeout_minutes: int = 30):
        """Initialize session manager."""
        self.sessions: Dict[str, Session] = {}
        self.user_sessions: Dict[str, List[str]] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)

    def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        device_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Create new session."""
        session_id = secrets.token_urlsafe(32)
        now = datetime.now()

        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            expires_at=now + self.session_timeout,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            metadata=metadata or {}
        )

        self.sessions[session_id] = session
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session."""
        session = self.sessions.get(session_id)
        if session and session.is_valid():
            session.last_activity = datetime.now()
            return session
        return None

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate session."""
        session = self.sessions.get(session_id)
        if session:
            session.is_active = False
            return True
        return False

    def invalidate_user_sessions(self, user_id: str) -> int:
        """Invalidate all sessions for user."""
        session_ids = self.user_sessions.get(user_id, [])
        count = 0
        for session_id in session_ids:
            if self.invalidate_session(session_id):
                count += 1
        return count

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions."""
        expired = [
            sid for sid, sess in self.sessions.items()
            if sess.is_expired()
        ]
        for sid in expired:
            del self.sessions[sid]
        return len(expired)

    def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for user."""
        session_ids = self.user_sessions.get(user_id, [])
        return [
            self.sessions[sid]
            for sid in session_ids
            if sid in self.sessions and self.sessions[sid].is_valid()
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        active = sum(1 for s in self.sessions.values() if s.is_valid())
        expired = sum(1 for s in self.sessions.values() if s.is_expired())
        
        return {
            'total_sessions': len(self.sessions),
            'active_sessions': active,
            'expired_sessions': expired,
            'unique_users': len(self.user_sessions)
        }


class AuditLogger:
    """Logs security audit events."""

    def __init__(self, max_events: int = 10000):
        """Initialize audit logger."""
        self.events: List[AuditEvent] = []
        self.max_events = max_events
        self.event_counts: Dict[str, int] = {}

    def log_event(
        self,
        user_id: Optional[str],
        action: str,
        resource: str,
        status: str,
        ip_address: str,
        user_agent: str,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        severity: str = "info"
    ) -> AuditEvent:
        """Log audit event."""
        event_id = f"audit_{secrets.token_urlsafe(12)}"
        
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            resource=resource,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            error_message=error_message,
            severity=severity
        )

        self.events.append(event)
        
        # Update event counts
        key = f"{action}:{resource}:{status}"
        self.event_counts[key] = self.event_counts.get(key, 0) + 1

        # Cleanup if max reached
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

        return event

    def get_events(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        hours: int = 24
    ) -> List[AuditEvent]:
        """Get audit events."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        events = [e for e in self.events if e.timestamp >= cutoff]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if action:
            events = [e for e in events if e.action == action]

        return events

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics."""
        total_events = len(self.events)
        success_events = sum(1 for e in self.events if e.status == "success")
        failure_events = sum(1 for e in self.events if e.status == "failure")
        
        critical_events = sum(1 for e in self.events if e.severity == "critical")
        
        return {
            'total_events': total_events,
            'success_events': success_events,
            'failure_events': failure_events,
            'critical_events': critical_events,
            'unique_users': len(set(e.user_id for e in self.events if e.user_id)),
            'event_breakdown': self.event_counts
        }


# Singleton instances
_jwt_service: Optional[JWTTokenService] = None
_api_key_manager: Optional[APIKeyManager] = None
_session_manager: Optional[SessionManager] = None
_audit_logger: Optional[AuditLogger] = None


def get_jwt_service(secret_key: str = "default-secret-key-change-in-production") -> JWTTokenService:
    """Get JWT token service singleton."""
    global _jwt_service
    if _jwt_service is None:
        _jwt_service = JWTTokenService(secret_key)
    return _jwt_service


def get_api_key_manager() -> APIKeyManager:
    """Get API key manager singleton."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


def get_session_manager() -> SessionManager:
    """Get session manager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def get_audit_logger() -> AuditLogger:
    """Get audit logger singleton."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def reset_jwt_service() -> None:
    """Reset JWT service (for testing)."""
    global _jwt_service
    _jwt_service = None


def reset_api_key_manager() -> None:
    """Reset API key manager (for testing)."""
    global _api_key_manager
    _api_key_manager = None


def reset_session_manager() -> None:
    """Reset session manager (for testing)."""
    global _session_manager
    _session_manager = None


def reset_audit_logger() -> None:
    """Reset audit logger (for testing)."""
    global _audit_logger
    _audit_logger = None
