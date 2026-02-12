"""
Phase 56: Security & Authentication Verification Tests
Comprehensive test suite for JWT tokens, OAuth2, API keys,
sessions, RBAC, and audit logging (15 test cases).
"""

import sys
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import services
from jwt_token_service_phase56 import (
    get_jwt_service, reset_jwt_service, TokenType, TokenStatus,
    get_api_key_manager, reset_api_key_manager,
    get_session_manager, reset_session_manager,
    get_audit_logger, reset_audit_logger
)
from oauth2_provider_phase56 import (
    get_oauth2_provider, reset_oauth2_provider,
    OAuth2ClientType, OAuth2ResponseType, GrantType
)
from rbac_engine_phase56 import (
    get_rbac_engine, reset_rbac_engine,
    ResourceType, PolicyEffect, AccessDecision, PolicyRule
)


class TestJWTTokenService:
    """Test JWT token creation, verification, and revocation."""
    
    def setup_method(self):
        """Setup before each test."""
        reset_jwt_service()
    
    def test_token_creation_and_verification(self):
        """Test creating and verifying tokens."""
        service = get_jwt_service()
        
        # Create token
        token = service.create_token(
            subject="test_user",
            token_type=TokenType.ACCESS,
            scopes=["read", "write"]
        )
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token
        valid, claims, error = service.verify_token(token)
        assert valid is True
        assert claims.subject == "test_user"
        assert "read" in claims.scopes
        assert error is None
    
    def test_token_refresh(self):
        """Test refresh token flow."""
        service = get_jwt_service()
        
        # Create refresh token
        refresh_token = service.create_token(
            subject="test_user",
            token_type=TokenType.REFRESH,
            expires_in_minutes=7 * 24 * 60
        )
        
        # Refresh to get new access token
        new_token = service.refresh_token(refresh_token)
        assert new_token is not None
        
        # Verify new token
        valid, claims, _ = service.verify_token(new_token)
        assert valid is True
        assert claims.subject == "test_user"
    
    def test_token_revocation(self):
        """Test token revocation and blacklisting."""
        service = get_jwt_service()
        
        # Create token
        token = service.create_token(
            subject="test_user",
            token_type=TokenType.ACCESS
        )
        
        # Revoke token
        service.revoke_token(token)
        
        # Verify token is blacklisted
        valid, _, _ = service.verify_token(token)
        assert valid is False


class TestAPIKeyManager:
    """Test API key creation, verification, and revocation."""
    
    def setup_method(self):
        """Setup before each test."""
        reset_api_key_manager()
    
    def test_api_key_creation_and_verification(self):
        """Test creating and verifying API keys."""
        manager = get_api_key_manager()
        user_id = "test_user"
        
        # Create API key
        secret, api_key = manager.create_api_key(
            user_id=user_id,
            name="test_key",
            scopes=["read", "write"]
        )
        
        assert secret is not None
        assert api_key.key_id is not None
        assert api_key.name == "test_key"
        
        # Verify API key
        valid, returned_user_id = manager.verify_api_key(secret)
        assert valid is True
        assert returned_user_id == user_id
    
    def test_api_key_revocation(self):
        """Test API key revocation."""
        manager = get_api_key_manager()
        
        # Create key
        secret, api_key = manager.create_api_key(
            user_id="test_user",
            name="test_key"
        )
        
        # Revoke key
        success = manager.revoke_api_key(api_key.key_id)
        assert success is True
        
        # Verify revoked key is invalid
        valid, _ = manager.verify_api_key(secret)
        assert valid is False
    
    def test_api_key_listing(self):
        """Test listing user's API keys."""
        manager = get_api_key_manager()
        user_id = "test_user"
        
        # Create multiple keys
        manager.create_api_key(user_id=user_id, name="key1")
        manager.create_api_key(user_id=user_id, name="key2")
        
        # List keys
        keys = manager.list_user_keys(user_id)
        assert len(keys) == 2
        assert keys[0].name in ["key1", "key2"]


class TestSessionManager:
    """Test session creation, validation, and expiration."""
    
    def setup_method(self):
        """Setup before each test."""
        reset_session_manager()
    
    def test_session_creation_and_retrieval(self):
        """Test creating and retrieving sessions."""
        manager = get_session_manager()
        user_id = "test_user"
        
        # Create session
        session = manager.create_session(
            user_id=user_id,
            ip_address="192.168.1.1",
            user_agent="test_agent"
        )
        
        assert session is not None
        assert session.user_id == user_id
        assert session.is_active is True
        
        # Retrieve session
        retrieved = manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.user_id == user_id
    
    def test_session_invalidation(self):
        """Test session invalidation."""
        manager = get_session_manager()
        
        # Create and invalidate
        session = manager.create_session(user_id="test_user")
        manager.invalidate_session(session.session_id)
        
        # Verify session is inactive
        retrieved = manager.get_session(session.session_id)
        assert retrieved is None or retrieved.is_active is False
    
    def test_user_sessions_cleanup(self):
        """Test cleaning up expired sessions."""
        manager = get_session_manager()
        
        # Create sessions
        session = manager.create_session(
            user_id="test_user",
            timeout_minutes=0  # Expire immediately
        )
        
        # Cleanup
        count = manager.cleanup_expired_sessions()
        assert count > 0


class TestOAuth2Provider:
    """Test OAuth2 client registration and authorization flows."""
    
    def setup_method(self):
        """Setup before each test."""
        reset_oauth2_provider()
    
    def test_client_registration(self):
        """Test OAuth2 client registration."""
        provider = get_oauth2_provider()
        
        # Register client
        client_id, client_secret = provider.register_client(
            client_name="test_app",
            client_type=OAuth2ClientType.CONFIDENTIAL,
            redirect_uris=["https://app.example.com/callback"],
            allowed_scopes=["read", "write"],
            allowed_grant_types=[GrantType.AUTH_CODE]
        )
        
        assert client_id is not None
        assert client_secret is not None
        
        # Verify client
        assert provider.validate_client(client_id, client_secret) is True
    
    def test_authorization_code_flow(self):
        """Test OAuth2 authorization code flow."""
        provider = get_oauth2_provider()
        
        # Register client
        client_id, client_secret = provider.register_client(
            client_name="test_app",
            client_type=OAuth2ClientType.CONFIDENTIAL,
            redirect_uris=["https://app.example.com/callback"],
            allowed_scopes=["read"],
            allowed_grant_types=[GrantType.AUTH_CODE]
        )
        
        # Create authorization code
        code = provider.create_authorization_code(
            client_id=client_id,
            user_id="test_user",
            scopes=["read"],
            redirect_uri="https://app.example.com/callback"
        )
        
        assert code is not None
        
        # Exchange code for token info
        token_info = provider.exchange_authorization_code(
            client_id=client_id,
            code=code,
            redirect_uri="https://app.example.com/callback"
        )
        
        assert token_info is not None
        assert token_info['user_id'] == "test_user"
    
    def test_pkce_support(self):
        """Test PKCE (Proof Key for Public Clients) support."""
        provider = get_oauth2_provider()
        
        # Register public client
        client_id, _ = provider.register_client(
            client_name="mobile_app",
            client_type=OAuth2ClientType.PUBLIC,
            redirect_uris=["com.example.app://callback"],
            allowed_scopes=["read"],
            allowed_grant_types=[GrantType.AUTH_CODE],
            require_pkce=True
        )
        
        # Generate PKCE challenge
        verifier = "test_verifier_string_that_is_long_enough"
        challenge = provider.generate_code_challenge(verifier, "S256")
        
        assert challenge is not None
        
        # Create auth code with PKCE
        code = provider.create_authorization_code(
            client_id=client_id,
            user_id="test_user",
            scopes=["read"],
            redirect_uri="com.example.app://callback",
            code_challenge=challenge,
            code_challenge_method="S256"
        )
        
        assert code is not None


class TestRBACEngine:
    """Test Role-Based Access Control system."""
    
    def setup_method(self):
        """Setup before each test."""
        reset_rbac_engine()
    
    def test_role_creation_and_assignment(self):
        """Test creating roles and assigning to subjects."""
        engine = get_rbac_engine()
        
        # Register subject
        subject = engine.register_subject(
            subject_id="user1",
            subject_type="user"
        )
        
        assert subject is not None
        
        # Get default user role
        user_role = engine.get_role("user")
        assert user_role is not None
        
        # Assign role
        success = engine.assign_role_to_subject("user1", "user")
        assert success is True
        
        # Verify role assignment
        updated_subject = engine.get_subject("user1")
        assert "user" in updated_subject.roles
    
    def test_permission_management(self):
        """Test registering and managing permissions."""
        engine = get_rbac_engine()
        
        # Register permission
        perm = engine.register_permission(
            permission_id="read_documents",
            name="Read Documents",
            resource_type=ResourceType.DOCUMENT,
            action="read"
        )
        
        assert perm is not None
        assert perm.permission_id == "read_documents"
        
        # Grant permission to role
        success = engine.grant_permission_to_role("user", "read_documents")
        assert success is True
    
    def test_access_evaluation(self):
        """Test evaluating access requests."""
        engine = get_rbac_engine()
        
        # Register subject with admin role
        engine.register_subject("admin_user", "user")
        engine.assign_role_to_subject("admin_user", "admin")
        
        # Evaluate access (admin should be allowed everything)
        allowed, reason = engine.evaluate_access(
            subject_id="admin_user",
            action="delete",
            resource="any_resource",
            resource_type=ResourceType.DOCUMENT
        )
        
        assert allowed is True
    
    def test_policy_based_rules(self):
        """Test policy-based access control."""
        engine = get_rbac_engine()
        
        # Register subject
        engine.register_subject("user1", "user")
        engine.assign_role_to_subject("user1", "user")
        
        # Add policy rule
        rule = PolicyRule(
            rule_id="allow_user_read",
            effect=PolicyEffect.ALLOW,
            subjects=["user1"],
            actions=["read"],
            resources=["document_*"],
            conditions={},
            priority=100
        )
        
        engine.add_policy(rule)
        
        # Test access
        allowed, _ = engine.evaluate_access(
            subject_id="user1",
            action="read",
            resource="document_123",
            resource_type=ResourceType.DOCUMENT
        )
        
        assert allowed is True


class TestAuditLogging:
    """Test audit logging and event tracking."""
    
    def setup_method(self):
        """Setup before each test."""
        reset_audit_logger()
    
    def test_audit_event_logging(self):
        """Test logging audit events."""
        logger = get_audit_logger()
        
        # Log event
        logger.log_event(
            user_id="test_user",
            action="login",
            resource="user",
            status="success",
            ip_address="192.168.1.1"
        )
        
        # Retrieve events
        events = logger.get_events(user_id="test_user", action="login")
        assert len(events) > 0
        assert events[0].action == "login"
    
    def test_audit_statistics(self):
        """Test audit statistics."""
        logger = get_audit_logger()
        
        # Log multiple events
        logger.log_event("user1", "login", "user", "success")
        logger.log_event("user1", "login", "user", "success")
        logger.log_event("user2", "logout", "user", "failure")
        
        # Get statistics
        stats = logger.get_statistics()
        assert stats['total_events'] >= 3
        assert stats['success_events'] >= 2


class TestIntegrationScenarios:
    """Test integrated authentication and authorization flows."""
    
    def setup_method(self):
        """Setup before each test."""
        reset_jwt_service()
        reset_oauth2_provider()
        reset_rbac_engine()
        reset_audit_logger()
    
    def test_login_to_authorization_flow(self):
        """Test complete flow from login through authorization."""
        jwt_service = get_jwt_service()
        rbac_engine = get_rbac_engine()
        logger = get_audit_logger()
        
        # Step 1: Create user token
        token = jwt_service.create_token(
            subject="test_user",
            token_type=TokenType.ACCESS,
            scopes=["read", "write"]
        )
        
        # Step 2: Verify token
        valid, claims, _ = jwt_service.verify_token(token)
        assert valid is True
        
        # Step 3: Register user in RBAC
        rbac_engine.register_subject("test_user", "user")
        rbac_engine.assign_role_to_subject("test_user", "user")
        
        # Step 4: Check authorization
        allowed, _ = rbac_engine.evaluate_access(
            subject_id="test_user",
            action="read",
            resource="document_123",
            resource_type=ResourceType.DOCUMENT
        )
        
        # Step 5: Log access attempt
        logger.log_event(
            user_id="test_user",
            action="access_resource",
            resource="document_123",
            status="success" if allowed else "failure"
        )
        
        assert valid is True
        assert allowed is True
        
        # Verify audit trail
        events = logger.get_events(user_id="test_user")
        assert len(events) > 0
    
    def test_api_key_with_rbac(self):
        """Test API key authentication integrated with RBAC."""
        api_key_mgr = get_api_key_manager()
        rbac_engine = get_rbac_engine()
        
        # Create API key
        secret, api_key = api_key_mgr.create_api_key(
            user_id="api_user",
            name="service_key",
            scopes=["read"]
        )
        
        # Register user in RBAC
        rbac_engine.register_subject("api_user", "service")
        rbac_engine.assign_role_to_subject("api_user", "user")
        
        # Authenticate with API key
        valid, user_id = api_key_mgr.verify_api_key(secret)
        assert valid is True
        assert user_id == "api_user"
        
        # Check authorization
        allowed, _ = rbac_engine.evaluate_access(
            subject_id=user_id,
            action="read",
            resource="data",
            resource_type=ResourceType.DATASET
        )
        
        assert allowed is True


# ===================== TEST EXECUTION =====================

def run_all_tests():
    """Run all tests and report results."""
    test_classes = [
        TestJWTTokenService,
        TestAPIKeyManager,
        TestSessionManager,
        TestOAuth2Provider,
        TestRBACEngine,
        TestAuditLogging,
        TestIntegrationScenarios
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        
        for method in methods:
            total_tests += 1
            try:
                instance.setup_method()
                getattr(instance, method)()
                passed_tests += 1
                print(f"✓ {test_class.__name__}.{method}")
            except Exception as e:
                failed_tests.append((test_class.__name__, method, str(e)))
                print(f"✗ {test_class.__name__}.{method}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"Test Summary: {passed_tests}/{total_tests} passed")
    print(f"{'='*60}")
    
    if failed_tests:
        print("\nFailed Tests:")
        for class_name, method, error in failed_tests:
            print(f"  - {class_name}.{method}")
            print(f"    Error: {error}")
        return False
    else:
        print("\n🎉 All tests passed!")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
