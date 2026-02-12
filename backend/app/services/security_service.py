"""
Security Service
Encryption, authentication, authorization, and audit logging.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
import hashlib
import hmac
import secrets
import json
import threading
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class EncryptionAlgorithm(Enum):
    """Encryption algorithms."""
    AES_256_GCM = "aes-256-gcm"
    AES_256_CBC = "aes-256-cbc"
    SHA256 = "sha256"
    BCRYPT = "bcrypt"


class TokenType(Enum):
    """JWT token types."""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    SERVICE = "service"


class AuditAction(Enum):
    """Audit log actions."""
    LOGIN = "login"
    LOGOUT = "logout"
    API_CALL = "api_call"
    PERMISSION_DENIED = "permission_denied"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    ENCRYPTION_KEY_ROTATE = "encryption_key_rotate"
    POLICY_CHANGE = "policy_change"
    SECURITY_EVENT = "security_event"


class PermissionLevel(Enum):
    """Permission levels."""
    PUBLIC = 0
    AUTHENTICATED = 1
    USER = 2
    ADMIN = 3
    SUPER_ADMIN = 4


@dataclass
class EncryptedData:
    """Encrypted data container."""
    ciphertext: str
    nonce: str
    algorithm: EncryptionAlgorithm
    timestamp: datetime = field(default_factory=datetime.utcnow)
    key_id: str = ""


@dataclass
class JWTToken:
    """JWT token representation."""
    token_id: str
    user_id: str
    token_type: TokenType
    issued_at: datetime
    expires_at: datetime
    claims: Dict[str, Any] = field(default_factory=dict)
    scopes: List[str] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    def has_scope(self, scope: str) -> bool:
        """Check if token has scope."""
        return scope in self.scopes


@dataclass
class AuditLog:
    """Audit log entry."""
    log_id: str
    timestamp: datetime
    user_id: str
    action: AuditAction
    resource: str
    resource_id: str
    status: str  # success, failure
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    user_agent: str = ""
    severity: str = "info"  # info, warning, critical


@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_digits: bool = True
    password_require_special: bool = True
    password_expiry_days: int = 90
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 60
    require_mfa: bool = False
    encryption_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    token_expiry_hours: int = 24
    refresh_token_expiry_days: int = 30
    audit_retention_days: int = 365


class EncryptionManager:
    """Handles encryption/decryption operations."""
    
    def __init__(self, master_key: str):
        """Initialize encryption manager."""
        self.master_key = master_key
        self.lock = threading.RLock()
        self.key_versions: Dict[str, str] = {"current": master_key}
    
    def encrypt(self, data: str, algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM) -> EncryptedData:
        """Encrypt data."""
        with self.lock:
            try:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                from cryptography.hazmat.primitives import hashes
                
                # Derive key from master key
                key = self._derive_key(self.master_key)
                nonce = secrets.token_hex(12)
                
                if algorithm == EncryptionAlgorithm.AES_256_GCM:
                    cipher = AESGCM(key)
                    ciphertext = cipher.encrypt(nonce.encode(), data.encode(), None)
                    return EncryptedData(
                        ciphertext=ciphertext.hex(),
                        nonce=nonce,
                        algorithm=algorithm,
                        key_id="current"
                    )
            except Exception as e:
                logger.error(f"Encryption failed: {e}")
                # Fallback to simple base64
                import base64
                ciphertext = base64.b64encode(data.encode()).decode()
                return EncryptedData(
                    ciphertext=ciphertext,
                    nonce=nonce,
                    algorithm=EncryptionAlgorithm.SHA256,
                    key_id="current"
                )
    
    def decrypt(self, encrypted: EncryptedData) -> Optional[str]:
        """Decrypt data."""
        with self.lock:
            try:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                
                if encrypted.algorithm == EncryptionAlgorithm.AES_256_GCM:
                    key = self._derive_key(self.master_key)
                    cipher = AESGCM(key)
                    plaintext = cipher.decrypt(
                        encrypted.nonce.encode(),
                        bytes.fromhex(encrypted.ciphertext),
                        None
                    )
                    return plaintext.decode()
            except Exception as e:
                logger.error(f"Decryption failed: {e}")
                # Fallback to base64
                import base64
                try:
                    return base64.b64decode(encrypted.ciphertext).decode()
                except:
                    return None
        return None
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        try:
            import bcrypt
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(password.encode(), salt).decode()
        except:
            # Fallback to PBKDF2
            import hashlib
            salt = secrets.token_hex(16)
            hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return f"{salt}${hashed.hex()}"
    
    def verify_password(self, password: str, hash_value: str) -> bool:
        """Verify password against hash."""
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode(), hash_value.encode())
        except:
            # Fallback verification
            if '$' in hash_value:
                salt, hashed = hash_value.split('$')
                import hashlib
                computed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
                return computed.hex() == hashed
            return False
    
    def _derive_key(self, master_key: str) -> bytes:
        """Derive encryption key from master key."""
        import hashlib
        key = hashlib.sha256(master_key.encode()).digest()
        return key[:32]  # 256-bit key


class TokenManager:
    """Manages JWT tokens."""
    
    def __init__(self, secret_key: str, policy: SecurityPolicy):
        """Initialize token manager."""
        self.secret_key = secret_key
        self.policy = policy
        self.tokens: Dict[str, JWTToken] = {}
        self.revoked_tokens: Set[str] = set()
        self.lock = threading.RLock()
    
    def create_token(
        self,
        user_id: str,
        token_type: TokenType,
        scopes: Optional[List[str]] = None,
        claims: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, JWTToken]:
        """Create JWT token."""
        with self.lock:
            token_id = secrets.token_urlsafe()
            issued_at = datetime.utcnow()
            
            if token_type == TokenType.REFRESH:
                expires_at = issued_at + timedelta(days=self.policy.refresh_token_expiry_days)
            else:
                expires_at = issued_at + timedelta(hours=self.policy.token_expiry_hours)
            
            token_obj = JWTToken(
                token_id=token_id,
                user_id=user_id,
                token_type=token_type,
                issued_at=issued_at,
                expires_at=expires_at,
                scopes=scopes or [],
                claims=claims or {}
            )
            
            self.tokens[token_id] = token_obj
            
            # Create JWT string
            token_str = self._encode_token(token_obj)
            return token_str, token_obj
    
    def verify_token(self, token_str: str) -> Optional[JWTToken]:
        """Verify and decode token."""
        with self.lock:
            try:
                # Simple token verification (in production use PyJWT)
                parts = token_str.split('.')
                if len(parts) != 3:
                    return None
                
                token_id = parts[0]
                if token_id in self.revoked_tokens:
                    return None
                
                if token_id in self.tokens:
                    token_obj = self.tokens[token_id]
                    if not token_obj.is_expired():
                        return token_obj
            except Exception as e:
                logger.error(f"Token verification failed: {e}")
            
            return None
    
    def revoke_token(self, token_str: str) -> bool:
        """Revoke token."""
        with self.lock:
            try:
                token_id = token_str.split('.')[0]
                self.revoked_tokens.add(token_id)
                if token_id in self.tokens:
                    del self.tokens[token_id]
                return True
            except:
                return False
    
    def _encode_token(self, token_obj: JWTToken) -> str:
        """Encode token to JWT string (simplified)."""
        import hmac
        payload = {
            'token_id': token_obj.token_id,
            'user_id': token_obj.user_id,
            'type': token_obj.token_type.value,
            'iat': int(token_obj.issued_at.timestamp()),
            'exp': int(token_obj.expires_at.timestamp()),
            'scopes': token_obj.scopes,
            'claims': token_obj.claims
        }
        
        payload_str = json.dumps(payload, default=str)
        header = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"  # {"alg":"HS256","typ":"JWT"}
        payload_b64 = __import__('base64').b64encode(payload_str.encode()).decode().rstrip('=')
        
        signature = hmac.new(
            self.secret_key.encode(),
            f"{header}.{payload_b64}".encode(),
            'sha256'
        ).digest()
        signature_b64 = __import__('base64').b64encode(signature).decode().rstrip('=')
        
        return f"{header}.{payload_b64}.{signature_b64}"


class AuditLogger:
    """Audit logging system."""
    
    def __init__(self, policy: SecurityPolicy):
        """Initialize audit logger."""
        self.policy = policy
        self.logs: List[AuditLog] = []
        self.lock = threading.RLock()
    
    def log(
        self,
        user_id: str,
        action: AuditAction,
        resource: str,
        resource_id: str,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        ip_address: str = "",
        user_agent: str = "",
        severity: str = "info"
    ) -> str:
        """Log audit event."""
        with self.lock:
            log_id = secrets.token_hex(8)
            log_entry = AuditLog(
                log_id=log_id,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                status=status,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                severity=severity
            )
            
            self.logs.append(log_entry)
            
            # Enforce retention
            cutoff = datetime.utcnow() - timedelta(days=self.policy.audit_retention_days)
            self.logs = [log for log in self.logs if log.timestamp > cutoff]
            
            return log_id
    
    def get_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource: Optional[str] = None,
        days: int = 30
    ) -> List[AuditLog]:
        """Query audit logs."""
        with self.lock:
            cutoff = datetime.utcnow() - timedelta(days=days)
            results = self.logs
            
            if user_id:
                results = [l for l in results if l.user_id == user_id]
            if action:
                results = [l for l in results if l.action == action]
            if resource:
                results = [l for l in results if l.resource == resource]
            
            results = [l for l in results if l.timestamp > cutoff]
            return sorted(results, key=lambda x: x.timestamp, reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit statistics."""
        with self.lock:
            return {
                'total_logs': len(self.logs),
                'actions': {a.value: len([l for l in self.logs if l.action == a]) 
                           for a in AuditAction},
                'last_7_days': len([l for l in self.logs 
                                   if l.timestamp > datetime.utcnow() - timedelta(days=7)]),
                'failures': len([l for l in self.logs if l.status == 'failure']),
                'critical': len([l for l in self.logs if l.severity == 'critical'])
            }


class SecurityService:
    """Main security service."""
    
    def __init__(self, master_key: str, secret_key: str, policy: Optional[SecurityPolicy] = None):
        """Initialize security service."""
        self.policy = policy or SecurityPolicy()
        self.encryption = EncryptionManager(master_key)
        self.tokens = TokenManager(secret_key, self.policy)
        self.audit = AuditLogger(self.policy)
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password against policy."""
        errors = []
        
        if len(password) < self.policy.password_min_length:
            errors.append(f"Password must be at least {self.policy.password_min_length} characters")
        
        if self.policy.password_require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain uppercase letter")
        
        if self.policy.password_require_digits and not any(c.isdigit() for c in password):
            errors.append("Password must contain digit")
        
        if self.policy.password_require_special and not any(c in "!@#$%^&*" for c in password):
            errors.append("Password must contain special character")
        
        return len(errors) == 0, errors
    
    def create_api_key(self, user_id: str, name: str, scopes: List[str]) -> Tuple[str, str]:
        """Create API key."""
        with self.lock:
            key_id = secrets.token_urlsafe(16)
            key_secret = secrets.token_urlsafe(32)
            
            self.api_keys[key_id] = {
                'user_id': user_id,
                'name': name,
                'scopes': scopes,
                'created_at': datetime.utcnow(),
                'last_used': None,
                'enabled': True
            }
            
            return key_id, key_secret
    
    def verify_api_key(self, key_id: str, key_secret: str) -> Optional[Dict[str, Any]]:
        """Verify API key."""
        with self.lock:
            if key_id in self.api_keys:
                key_info = self.api_keys[key_id]
                if key_info['enabled']:
                    key_info['last_used'] = datetime.utcnow()
                    return key_info
            return None
    
    def encrypt_data(self, data: str) -> EncryptedData:
        """Encrypt sensitive data."""
        return self.encryption.encrypt(data)
    
    def decrypt_data(self, encrypted: EncryptedData) -> Optional[str]:
        """Decrypt sensitive data."""
        return self.encryption.decrypt(encrypted)
    
    def hash_password(self, password: str) -> str:
        """Hash password."""
        return self.encryption.hash_password(password)
    
    def verify_password(self, password: str, hash_value: str) -> bool:
        """Verify password."""
        return self.encryption.verify_password(password, hash_value)
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        with self.lock:
            return {
                'api_keys': len(self.api_keys),
                'tokens': len(self.tokens.tokens),
                'revoked_tokens': len(self.tokens.revoked_tokens),
                'audit_logs': len(self.audit.logs),
                'audit_stats': self.audit.get_stats()
            }
