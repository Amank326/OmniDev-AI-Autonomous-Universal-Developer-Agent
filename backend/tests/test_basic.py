"""Basic tests for OmniDev AI Platform."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Test health endpoint."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "omnidev-ai"


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Test root endpoint."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "status" in data


@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient, test_user_data):
    """Test user registration endpoint exists and rejects bad input."""
    # Empty body should return 422 (validation error)
    response = await async_client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_agents_requires_auth(async_client: AsyncClient):
    """Test that agents endpoint requires authentication."""
    response = await async_client.get("/api/v1/agents/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_openapi_docs(async_client: AsyncClient):
    """Test that API documentation is accessible."""
    response = await async_client.get("/api/v1/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_openapi_json(async_client: AsyncClient):
    """Test that OpenAPI JSON is accessible."""
    response = await async_client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data


@pytest.mark.asyncio
async def test_notifications_requires_auth(async_client: AsyncClient):
    """Test that notifications endpoint requires authentication."""
    response = await async_client.get("/api/v1/notifications/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_subscriptions_requires_auth(async_client: AsyncClient):
    """Test that subscriptions endpoint requires authentication."""
    response = await async_client.get("/api/v1/subscriptions/")
    assert response.status_code == 401
