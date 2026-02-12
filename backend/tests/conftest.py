"""Test configuration and fixtures."""

import pytest


@pytest.fixture
def test_user_data():
    """Fixture for test user data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }


@pytest.fixture
def test_agent_data():
    """Fixture for test agent data."""
    return {
        "name": "Test Agent",
        "agent_type": "code_analyzer",
        "description": "Test agent for unit tests",
        "configuration": {"language": "python"},
        "capabilities": ["analysis", "testing"]
    }
