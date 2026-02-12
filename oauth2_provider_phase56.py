"""
Phase 56: OAuth2 Provider
Complete OAuth2 implementation with multiple grant types,
authorization code flow, client management, and scope handling.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import secrets
import hashlib


class OAuth2ClientType(Enum):
    """OAuth2 client types."""
    CONFIDENTIAL = "confidential"  # Web apps, backend servers
    PUBLIC = "public"  # SPAs, mobile apps, desktop apps


class OAuth2ResponseType(Enum):
    """OAuth2 response types."""
    CODE = "code"  # Authorization code flow
    TOKEN = "token"  # Implicit flow
    ID_TOKEN = "id_token"  # OpenID Connect


@dataclass
class OAuth2Client:
    """OAuth2 registered client application."""
    client_id: str
    client_secret: Optional[str]  # None for public clients
    client_name: str
    client_type: OAuth2ClientType
    redirect_uris: List[str] = field(default_factory=list)
    allowed_scopes: List[str] = field(default_factory=list)
    allowed_grant_types: List[str] = field(default_factory=list)
    response_types: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    is_active: bool = True
    require_pkce: bool = False
    token_endpoint_auth_method: str = "client_secret_basic"
    description: str = ""
    owner_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def hash_secret(secret: str) -> str:
        """Hash client secret."""
        return hashlib.sha256(secret.encode()).hexdigest()

    def verify_secret(self, secret: str) -> bool:
        """Verify client secret."""
        if self.client_secret is None:
            return False
        return self.client_secret == self.hash_secret(secret)

    def validate_redirect_uri(self, uri: str) -> bool:
        """Validate redirect URI is registered."""
        return uri in self.redirect_uris

    def validate_scope(self, scopes: List[str]) -> bool:
        """Validate requested scopes are allowed."""
        return all(scope in self.allowed_scopes for scope in scopes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (public info only)."""
        return {
            'client_id': self.client_id,
            'client_name': self.client_name,
            'client_type': self.client_type.value,
            'redirect_uris': self.redirect_uris,
            'allowed_scopes': self.allowed_scopes,
            'allowed_grant_types': self.allowed_grant_types,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'description': self.description
        }


@dataclass
class AuthorizationCode:
    """Authorization code for code flow."""
    code: str
    client_id: str
    user_id: str
    scopes: List[str]
    redirect_uri: str
    created_at: datetime
    expires_at: datetime
    is_used: bool = False
    used_at: Optional[datetime] = None
    code_challenge: Optional[str] = None  # For PKCE
    code_challenge_method: Optional[str] = None

    def is_valid(self) -> bool:
        """Check if code is valid."""
        if self.is_used or datetime.now() >= self.expires_at:
            return False
        return True


@dataclass
class OAuth2Consent:
    """User consent to share scopes with client."""
    consent_id: str
    user_id: str
    client_id: str
    granted_scopes: List[str]
    granted_at: datetime
    expires_at: Optional[datetime] = None
    remember_consent: bool = True

    def is_valid(self) -> bool:
        """Check if consent is still valid."""
        if self.expires_at and datetime.now() >= self.expires_at:
            return False
        return True


@dataclass
class TokenGrant:
    """Record of token grant."""
    grant_id: str
    client_id: str
    user_id: str
    token_type: str
    scopes: List[str]
    issued_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str

    def is_active(self) -> bool:
        """Check if grant is still active."""
        return datetime.now() < self.expires_at


class OAuth2Provider:
    """OAuth2 authorization server implementation."""

    def __init__(self):
        """Initialize OAuth2 provider."""
        self.clients: Dict[str, OAuth2Client] = {}
        self.authorization_codes: Dict[str, AuthorizationCode] = {}
        self.consents: Dict[str, OAuth2Consent] = {}
        self.token_grants: Dict[str, TokenGrant] = {}
        self.revoked_tokens: Set[str] = set()
        self.device_codes: Dict[str, Dict[str, Any]] = {}

    # ===================== CLIENT MANAGEMENT =====================

    def register_client(
        self,
        client_name: str,
        client_type: OAuth2ClientType,
        redirect_uris: List[str],
        allowed_scopes: List[str],
        allowed_grant_types: List[str],
        response_types: List[str] = None,
        require_pkce: bool = False,
        description: str = "",
        owner_id: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """Register new OAuth2 client."""
        client_id = f"client_{secrets.token_urlsafe(16)}"
        client_secret = None
        client_secret_hashed = None

        # Generate client secret for confidential clients
        if client_type == OAuth2ClientType.CONFIDENTIAL:
            client_secret = secrets.token_urlsafe(32)
            client_secret_hashed = OAuth2Client.hash_secret(client_secret)

        client = OAuth2Client(
            client_id=client_id,
            client_secret=client_secret_hashed,
            client_name=client_name,
            client_type=client_type,
            redirect_uris=redirect_uris,
            allowed_scopes=allowed_scopes,
            allowed_grant_types=allowed_grant_types,
            response_types=response_types or ["code"],
            require_pkce=require_pkce,
            description=description,
            owner_id=owner_id
        )

        self.clients[client_id] = client
        return client_id, client_secret

    def get_client(self, client_id: str) -> Optional[OAuth2Client]:
        """Get OAuth2 client."""
        return self.clients.get(client_id)

    def validate_client(
        self,
        client_id: str,
        client_secret: Optional[str] = None
    ) -> bool:
        """Validate client credentials."""
        client = self.get_client(client_id)
        
        if not client or not client.is_active:
            return False

        # Public clients don't need secret
        if client.client_type == OAuth2ClientType.PUBLIC:
            return True

        # Confidential clients must provide valid secret
        if client.client_type == OAuth2ClientType.CONFIDENTIAL:
            return client_secret is not None and client.verify_secret(client_secret)

        return False

    # ===================== AUTHORIZATION CODE FLOW =====================

    def create_authorization_code(
        self,
        client_id: str,
        user_id: str,
        scopes: List[str],
        redirect_uri: str,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None
    ) -> Optional[str]:
        """Create authorization code."""
        client = self.get_client(client_id)
        
        if not client:
            return None

        # Validate redirect URI
        if not client.validate_redirect_uri(redirect_uri):
            return None

        # Validate scopes
        if not client.validate_scope(scopes):
            return None

        code = secrets.token_urlsafe(32)
        
        auth_code = AuthorizationCode(
            code=code,
            client_id=client_id,
            user_id=user_id,
            scopes=scopes,
            redirect_uri=redirect_uri,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=10),
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )

        self.authorization_codes[code] = auth_code
        return code

    def exchange_authorization_code(
        self,
        client_id: str,
        code: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for tokens."""
        auth_code = self.authorization_codes.get(code)
        
        if not auth_code:
            return None

        # Validate code
        if not auth_code.is_valid():
            return None

        if auth_code.client_id != client_id:
            return None

        if auth_code.redirect_uri != redirect_uri:
            return None

        # Validate PKCE if required
        if auth_code.code_challenge:
            if not code_verifier:
                return None
            
            if not self._verify_pkce(code_verifier, auth_code.code_challenge, 
                                     auth_code.code_challenge_method):
                return None

        # Mark code as used
        auth_code.is_used = True
        auth_code.used_at = datetime.now()

        # Return token info (actual tokens created by JWT service)
        return {
            'user_id': auth_code.user_id,
            'scopes': auth_code.scopes,
            'client_id': client_id
        }

    # ===================== PKCE SUPPORT =====================

    @staticmethod
    def _verify_pkce(
        code_verifier: str,
        code_challenge: str,
        method: Optional[str] = None
    ) -> bool:
        """Verify PKCE code verifier."""
        if method == "S256":
            import base64
            challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode().rstrip('=')
            return challenge == code_challenge
        elif method == "plain":
            return code_verifier == code_challenge
        else:
            return False

    @staticmethod
    def generate_code_challenge(code_verifier: str, method: str = "S256") -> str:
        """Generate code challenge from verifier."""
        if method == "S256":
            import base64
            return base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode().rstrip('=')
        elif method == "plain":
            return code_verifier
        else:
            raise ValueError(f"Unsupported PKCE method: {method}")

    # ===================== CONSENT MANAGEMENT =====================

    def get_or_create_consent(
        self,
        user_id: str,
        client_id: str,
        requested_scopes: List[str]
    ) -> Optional[OAuth2Consent]:
        """Get existing consent or request new one."""
        # Look for existing valid consent
        for consent in self.consents.values():
            if (consent.user_id == user_id and 
                consent.client_id == client_id and 
                consent.is_valid()):
                # Check if all requested scopes are granted
                if all(scope in consent.granted_scopes for scope in requested_scopes):
                    return consent

        # Create new consent request
        consent_id = f"consent_{secrets.token_urlsafe(16)}"
        consent = OAuth2Consent(
            consent_id=consent_id,
            user_id=user_id,
            client_id=client_id,
            granted_scopes=requested_scopes,
            granted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365)
        )

        self.consents[consent_id] = consent
        return consent

    def grant_consent(
        self,
        user_id: str,
        client_id: str,
        granted_scopes: List[str],
        remember: bool = True
    ) -> str:
        """Record user consent to share scopes with client."""
        consent_id = f"consent_{secrets.token_urlsafe(16)}"
        
        consent = OAuth2Consent(
            consent_id=consent_id,
            user_id=user_id,
            client_id=client_id,
            granted_scopes=granted_scopes,
            granted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=365 if remember else 1),
            remember_consent=remember
        )

        self.consents[consent_id] = consent
        return consent_id

    def revoke_consent(self, consent_id: str) -> bool:
        """Revoke consent."""
        if consent_id in self.consents:
            del self.consents[consent_id]
            return True
        return False

    # ===================== DEVICE FLOW =====================

    def start_device_flow(
        self,
        client_id: str,
        scopes: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Start device authorization flow."""
        client = self.get_client(client_id)
        
        if not client:
            return None

        device_code = secrets.token_urlsafe(24)
        user_code = f"{secrets.token_hex(2)}-{secrets.token_hex(2)}".upper()

        self.device_codes[device_code] = {
            'client_id': client_id,
            'user_code': user_code,
            'scopes': scopes,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=15),
            'approved': False,
            'user_id': None
        }

        return {
            'device_code': device_code,
            'user_code': user_code,
            'verification_uri': f"https://auth.example.com/device",
            'expires_in': 900,
            'interval': 5
        }

    def approve_device_code(
        self,
        device_code: str,
        user_id: str
    ) -> bool:
        """Approve device code."""
        if device_code not in self.device_codes:
            return False

        device_info = self.device_codes[device_code]
        
        if datetime.now() >= device_info['expires_at']:
            return False

        device_info['approved'] = True
        device_info['user_id'] = user_id

        return True

    # ===================== TOKEN REVOCATION =====================

    def revoke_token(self, token: str, token_type_hint: Optional[str] = None) -> bool:
        """Revoke token."""
        self.revoked_tokens.add(token)
        return True

    def is_token_revoked(self, token: str) -> bool:
        """Check if token is revoked."""
        return token in self.revoked_tokens

    # ===================== STATISTICS =====================

    def get_statistics(self) -> Dict[str, Any]:
        """Get OAuth2 provider statistics."""
        active_clients = sum(1 for c in self.clients.values() if c.is_active)
        confidential_clients = sum(1 for c in self.clients.values() 
                                  if c.client_type == OAuth2ClientType.CONFIDENTIAL)
        public_clients = sum(1 for c in self.clients.values() 
                            if c.client_type == OAuth2ClientType.PUBLIC)
        
        valid_codes = sum(1 for c in self.authorization_codes.values() if c.is_valid())
        used_codes = sum(1 for c in self.authorization_codes.values() if c.is_used)
        
        active_consents = sum(1 for c in self.consents.values() if c.is_valid())
        active_grants = sum(1 for g in self.token_grants.values() if g.is_active())

        return {
            'total_clients': len(self.clients),
            'active_clients': active_clients,
            'confidential_clients': confidential_clients,
            'public_clients': public_clients,
            'authorization_codes': {
                'valid': valid_codes,
                'used': used_codes,
                'total': len(self.authorization_codes)
            },
            'consents': {
                'active': active_consents,
                'total': len(self.consents)
            },
            'token_grants': {
                'active': active_grants,
                'total': len(self.token_grants)
            },
            'revoked_tokens': len(self.revoked_tokens)
        }


# Singleton instance
_oauth2_provider: Optional[OAuth2Provider] = None


def get_oauth2_provider() -> OAuth2Provider:
    """Get OAuth2 provider singleton."""
    global _oauth2_provider
    if _oauth2_provider is None:
        _oauth2_provider = OAuth2Provider()
    return _oauth2_provider


def reset_oauth2_provider() -> None:
    """Reset OAuth2 provider (for testing)."""
    global _oauth2_provider
    _oauth2_provider = None
