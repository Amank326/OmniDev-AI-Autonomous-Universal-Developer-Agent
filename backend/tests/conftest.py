"""
Test Configuration and Fixtures

Pytest configuration with shared fixtures for testing:
- Database fixtures with test data seeding
- FastAPI test client
- Authentication fixtures
- Mock objects for external services

Usage:
    pytest tests/ -v
    pytest tests/test_auth.py -v
    pytest tests/ --cov=app --cov-report=html
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from typing import Generator

from app.main import app
from app.database import Base
from app.database.config import get_db
from app.auth.utils import hash_password


# Test database configuration
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine for entire test session."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(test_db_engine) -> Session:
    """Get test database session."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator:
    """Get FastAPI test client with test database."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }


@pytest.fixture
def test_admin_data() -> dict:
    """Sample admin user data for testing."""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "full_name": "Admin User"
    }


@pytest.fixture
def authenticated_client(client: TestClient, test_user_data: dict) -> dict:
    """
    Provide authenticated test client and token.
    
    Returns:
        Dict with:
        - client: Authenticated FastAPI test client
        - token: Access token
        - user_id: User ID
    """
    # Create user via registration endpoint
    response = client.post(
        "/api/auth/register",
        json=test_user_data
    )
    assert response.status_code == 201
    
    # Login to get token
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
    )
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    token = token_data["access_token"]
    
    # Create authenticated client
    client.headers = {"Authorization": f"Bearer {token}"}
    
    return {
        "client": client,
        "token": token,
        "user_id": token_data.get("user_id"),
        "refresh_token": token_data.get("refresh_token")
    }


@pytest.fixture
def sample_project_data() -> dict:
    """Sample project data for testing."""
    return {
        "title": "Test Project",
        "description": "A test project for automated testing",
        "status": "active"
    }


@pytest.fixture
def sample_task_data() -> dict:
    """Sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "A test task for automated testing",
        "priority": "medium",
        "status": "pending"
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Logging configuration for tests
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        if "unit" not in item.keywords:
            if item.fspath.basename == "test_auth.py":
                item.add_marker(pytest.mark.unit)
            elif item.fspath.basename == "test_models.py":
                item.add_marker(pytest.mark.unit)
            elif item.fspath.basename == "test_api.py":
                item.add_marker(pytest.mark.integration)
