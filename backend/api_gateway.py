"""API Gateway - Quick Start Guide

This file provides a simple way to test the OmniDev AI platform APIs.

## Prerequisites
1. Install httpx: pip install httpx
2. Ensure the backend is running on http://localhost:8000

## Usage
```python
python api_gateway.py
```
"""

import asyncio
import httpx
import json

API_BASE_URL = "http://localhost:8000/api/v1"


async def test_health():
    """Test health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        print(f"Health Check: {response.json()}")


async def register_user(email: str, username: str, password: str):
    """Register a new user."""
    async with httpx.AsyncClient() as client:
        data = {
            "email": email,
            "username": username,
            "password": password,
            "full_name": "Test User"
        }
        response = await client.post(f"{API_BASE_URL}/auth/register", json=data)
        print(f"Register User: {response.status_code}")
        if response.status_code == 201:
            print(json.dumps(response.json(), indent=2))
        return response


async def login_user(email: str, password: str):
    """Login user and get tokens."""
    async with httpx.AsyncClient() as client:
        data = {
            "email": email,
            "password": password
        }
        response = await client.post(f"{API_BASE_URL}/auth/login", json=data)
        print(f"Login User: {response.status_code}")
        if response.status_code == 200:
            tokens = response.json()
            print(json.dumps(tokens, indent=2))
            return tokens.get("access_token")
        return None


async def create_agent(token: str):
    """Create an AI agent."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "name": "My Code Analyzer",
            "agent_type": "code_analyzer",
            "description": "Analyzes code quality",
            "configuration": {"language": "python"},
            "capabilities": ["static_analysis", "complexity_check"]
        }
        response = await client.post(
            f"{API_BASE_URL}/agents",
            json=data,
            headers=headers
        )
        print(f"Create Agent: {response.status_code}")
        if response.status_code == 201:
            print(json.dumps(response.json(), indent=2))
        return response


async def list_agents(token: str):
    """List all agents."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"{API_BASE_URL}/agents", headers=headers)
        print(f"List Agents: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        return response


async def main():
    """Main function to run tests."""
    print("=" * 50)
    print("OmniDev AI Platform - API Test Suite")
    print("=" * 50)
    
    # Test health
    print("\n1. Testing Health Endpoint...")
    await test_health()
    
    # Register user
    print("\n2. Registering New User...")
    test_email = "test@example.com"
    test_username = "testuser"
    test_password = "testpassword123"
    
    register_response = await register_user(test_email, test_username, test_password)
    
    # Login user
    print("\n3. Logging In...")
    access_token = await login_user(test_email, test_password)
    
    if access_token:
        # Create agent
        print("\n4. Creating AI Agent...")
        await create_agent(access_token)
        
        # List agents
        print("\n5. Listing Agents...")
        await list_agents(access_token)
    
    print("\n" + "=" * 50)
    print("Test Suite Completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
