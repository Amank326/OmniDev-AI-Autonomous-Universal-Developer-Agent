# Phase 4: Advanced Features Implementation Guide

**Status**: ✅ COMPLETE  
**Date**: 2026-02-05  
**Version**: 1.0.0  

---

## Table of Contents

1. [Overview](#overview)
2. [Real-Time Features (WebSocket)](#real-time-features)
3. [Advanced API Features](#advanced-api-features)
4. [Rate Limiting](#rate-limiting)
5. [Testing Framework](#testing-framework)
6. [Structured Logging](#structured-logging)
7. [Deployment & Running](#deployment--running)
8. [Best Practices](#best-practices)

---

## Overview

Phase 4 adds production-ready advanced features to OmniDev AI:

| Feature | Description | Use Case |
|---------|-------------|----------|
| **WebSocket** | Real-time project/task updates | Live collaboration, progress tracking |
| **Advanced Filters** | Pagination, sorting, searching | Efficient data retrieval, UX improvements |
| **Rate Limiting** | Prevent abuse, ensure fair usage | Security, resource protection |
| **Testing Framework** | Unit and integration tests | Quality assurance, regression prevention |
| **Structured Logging** | JSON logs with context | Observability, debugging, monitoring |

---

## Real-Time Features

### WebSocket Overview

Real-time updates for projects and tasks using WebSocket protocol with token-based authentication.

**Features:**
- ✅ Multi-room subscription (project, task, user)
- ✅ Token-based authentication
- ✅ Automatic connection cleanup
- ✅ Broadcasting with filtering
- ✅ Connection statistics

### WebSocket Endpoints

#### 1. Project Updates: `/api/ws/projects/{project_id}`

Subscribe to real-time project updates.

**Authentication:**
```
WebSocket URI: ws://localhost:8000/api/ws/projects/123?token=<JWT_TOKEN>
```

**Incoming Message Types:**

```json
{
  "type": "ping"
}
```
Keep-alive ping (receive "pong" response).

```json
{
  "type": "status_update",
  "status": "active"
}
```
Update project status.

```json
{
  "type": "subscribe",
  "sub_rooms": ["task:456", "task:789"]
}
```
Subscribe to additional task rooms.

**Outgoing Message Types:**

```json
{
  "type": "connected",
  "room": "project:123",
  "user_id": 42,
  "message": "Connected to project 123 updates",
  "timestamp": "2026-02-05T10:30:00.000000"
}
```
Confirmation of connection.

```json
{
  "type": "task_created",
  "task_id": 789,
  "title": "Implement feature",
  "timestamp": "2026-02-05T10:31:00.000000"
}
```
New task created in project.

```json
{
  "type": "task_updated",
  "task_id": 789,
  "changes": {"status": "in_progress"},
  "timestamp": "2026-02-05T10:32:00.000000"
}
```
Task updated.

#### 2. Task Updates: `/api/ws/tasks/{task_id}`

Subscribe to real-time task updates (comments, progress, assignments).

**WebSocket URI:**
```
ws://localhost:8000/api/ws/tasks/789?token=<JWT_TOKEN>
```

**Incoming Message Types:**

```json
{
  "type": "progress",
  "progress": 75
}
```
Update task progress (0-100).

```json
{
  "type": "comment",
  "comment": "Started working on this"
}
```
Add comment to task.

```json
{
  "type": "assign",
  "assigned_to": 42
}
```
Assign task to user.

**Outgoing Message Types:**

```json
{
  "type": "progress_updated",
  "task_id": 789,
  "progress": 75,
  "updated_by": 99,
  "timestamp": "2026-02-05T10:33:00.000000"
}
```

```json
{
  "type": "comment_added",
  "task_id": 789,
  "author_id": 42,
  "text": "Started working on this",
  "timestamp": "2026-02-05T10:34:00.000000"
}
```

### WebSocket Client Example (JavaScript)

```javascript
// Connect to project updates
const projectId = 123;
const token = "your_jwt_token_here";
const ws = new WebSocket(
  `ws://localhost:8000/api/ws/projects/${projectId}?token=${token}`
);

// Handle connection
ws.onopen = (event) => {
  console.log("Connected to project updates");
  
  // Send ping to keep alive
  setInterval(() => {
    ws.send(JSON.stringify({ type: "ping" }));
  }, 30000); // Every 30 seconds
};

// Handle incoming messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === "task_created") {
    console.log(`New task: ${message.title}`);
    // Update UI with new task
  } else if (message.type === "task_updated") {
    console.log(`Task ${message.task_id} updated:`, message.changes);
    // Update UI with task changes
  }
};

// Handle errors
ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

// Handle disconnection
ws.onclose = () => {
  console.log("Disconnected from project updates");
  // Attempt to reconnect
};

// Send message to update task
ws.send(JSON.stringify({
  type: "progress",
  progress: 50
}));
```

### WebSocket Statistics Endpoint

**Endpoint:** `GET /api/ws/stats`

**Response:**
```json
{
  "total_connections": 42,
  "total_rooms": 5,
  "rooms": {
    "project:1": {
      "room": "project:1",
      "connections": 10,
      "users": [1, 2, 3, 4, 5],
      "user_count": 5,
      "active": true
    },
    "task:123": {
      "room": "task:123",
      "connections": 8,
      "users": [6, 7, 8],
      "user_count": 3,
      "active": true
    }
  },
  "timestamp": "2026-02-05T10:35:00.000000"
}
```

---

## Advanced API Features

### Filtering and Pagination

Consistent API for filtering, sorting, and paginating resources.

#### Query Parameters

**Pagination:**
```
GET /api/projects?skip=0&limit=20
```
- `skip`: Number of records to skip (default: 0)
- `limit`: Max records to return (default: 20, max: 100)

**Filtering:**
```
GET /api/projects?status=active&owner_id=42&search=web
```
- `status`: Filter by project status
- `owner_id`: Filter by project owner
- `search`: Text search in title/description

**Sorting:**
```
GET /api/projects?sort_by=created_at&sort_order=desc
```
- `sort_by`: Field to sort by (created_at, updated_at, title)
- `sort_order`: asc or desc

#### Example Requests

**Get active projects, sorted by creation date:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/projects?status=active&sort_by=created_at&sort_order=desc&limit=10"
```

**Search for project and get second page:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/projects?search=python&skip=20&limit=20"
```

**Get high-priority pending tasks:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/tasks?status=pending&priority=high&sort_by=created_at"
```

### Filter Models

#### ProjectFilter
```python
class ProjectFilter(BaseModel):
    status: Optional[str]        # "active", "completed", "archived"
    owner_id: Optional[int]      # User ID
    search: Optional[str]        # Text search
    sort_by: str                 # "created_at", "updated_at", "title"
    sort_order: SortOrder        # "asc" or "desc"
```

#### TaskFilter
```python
class TaskFilter(BaseModel):
    status: Optional[str]        # "pending", "in_progress", "completed"
    priority: Optional[str]      # "low", "medium", "high"
    assigned_to: Optional[int]   # User ID
    project_id: Optional[int]    # Project ID
    search: Optional[str]        # Text search
    sort_by: str                 # "created_at", "updated_at", "title"
    sort_order: SortOrder        # "asc" or "desc"
```

#### UserFilter
```python
class UserFilter(BaseModel):
    is_active: Optional[bool]    # Filter by active status
    is_admin: Optional[bool]     # Filter by admin status
    search: Optional[str]        # Text search in username/email
    sort_by: str                 # "created_at", "username"
    sort_order: SortOrder        # "asc" or "desc"
```

---

## Rate Limiting

### Rate Limit Configuration

Protection against abuse and resource exhaustion.

**Default Limits:**
- Global default: **100 requests / 15 minutes**
- Auth endpoints:
  - Register: **5 requests / 15 minutes** (strict)
  - Login: **10 requests / 15 minutes**
  - Refresh: **20 requests / 15 minutes**
- WebSocket: 5 connections per user, 60 messages/minute per connection

### Rate Limit Responses

**When limit exceeded (HTTP 429):**
```json
{
  "detail": "Too many requests. Please try again later.",
  "error_code": "rate_limit_exceeded",
  "retry_after": 60
}
```

**Headers:**
```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

### Rate Limit Key Functions

**Authentication endpoints:** IP address-based
```
10.0.0.1 can register 5 times in 15 minutes
```

**Authenticated endpoints:** User ID-based
```
User 42 can make 100 requests in 15 minutes regardless of IP
```

---

## Testing Framework

### Setup and Configuration

**Requirements:**
```
pytest>=7.0.0
pytest-cov>=4.0.0  # Code coverage
pytest-asyncio>=0.20.0  # For async tests
```

### Running Tests

**All tests:**
```bash
pytest tests/ -v
```

**Specific test file:**
```bash
pytest tests/test_auth.py -v
```

**Specific test class:**
```bash
pytest tests/test_auth.py::TestPasswordHashing -v
```

**Specific test:**
```bash
pytest tests/test_auth.py::TestPasswordHashing::test_hash_password_creates_different_hashes -v
```

**With coverage report:**
```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

**Run only integration tests:**
```bash
pytest tests/ -m integration -v
```

**Run only unit tests:**
```bash
pytest tests/ -m unit -v
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_auth.py             # Authentication tests (70+ tests)
└── test_api.py              # API endpoint tests (15+ tests)
```

### Test Fixtures

Available fixtures in `conftest.py`:

```python
# Database fixtures
@pytest.fixture
def db():  # Test database session
    
@pytest.fixture
def client():  # FastAPI test client
    
# User fixtures
@pytest.fixture
def test_user_data():  # Sample user data
    
@pytest.fixture
def authenticated_client():  # Authenticated client + token
    
# Resource fixtures
@pytest.fixture
def sample_project_data():  # Sample project data
    
@pytest.fixture
def sample_task_data():  # Sample task data
```

### Example Tests

**Unit Test - Password Hashing:**
```python
@pytest.mark.unit
def test_hash_password_creates_different_hashes():
    """Same password should create different hashes (due to salt)."""
    password = "TestPassword123!"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    assert hash1 != hash2  # Different due to random salt
    assert verify_password(password, hash1)
```

**Integration Test - User Registration:**
```python
@pytest.mark.integration
def test_register_user_success(client: TestClient, test_user_data: dict):
    """Test successful user registration."""
    response = client.post(
        "/api/auth/register",
        json=test_user_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == test_user_data["username"]
```

**Integration Test - Authenticated Endpoint:**
```python
@pytest.mark.integration
def test_get_current_user(authenticated_client: dict):
    """Test getting current user information."""
    response = authenticated_client["client"].get("/api/auth/me")
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
```

### Test Coverage Goals

| Component | Target Coverage |
|-----------|-----------------|
| Authentication | >90% |
| Database Models | >85% |
| Services | >80% |
| API Routes | >75% |
| Utilities | >90% |

---

## Structured Logging

### Overview

JSON-formatted logs with context information for better observability.

### Configuration

**Environment Variables:**
```bash
# Set log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Set format (json or text)
LOG_FORMAT=json

# Optional: Output to file
LOG_FILE=/var/log/omnidev/app.log
```

### Log Format

**JSON Format (Default):**
```json
{
  "timestamp": "2026-02-05T10:35:00.000000",
  "level": "INFO",
  "logger": "app.auth.routes",
  "message": "User registered successfully",
  "module": "routes",
  "function": "register",
  "line": 45,
  "user_id": 42,
  "operation": "user_registration",
  "email": "user@example.com"
}
```

**Text Format (Human-Readable):**
```
2026-02-05T10:35:00 | INFO     | app.auth.routes            | User registered successfully | user_id=42 | operation=user_registration | email=user@example.com
```

### Logging with Context

```python
import logging
from app.logging_config import ContextLogger, get_logger

# Get logger
logger = get_logger("omnidev_ai")

# Create context logger
ctx_logger = ContextLogger(logger)

# Set context for request
ctx_logger.set_context(
    user_id=42,
    request_id="req-12345",
    operation="create_project"
)

# All logs automatically include context
ctx_logger.info("Creating new project")
# Output: {..., "user_id": 42, "request_id": "req-12345", "operation": "create_project"}

# Add additional context to specific log
ctx_logger.info(
    "Project created",
    project_id=789,
    duration_ms=145,
    status="success"
)
```

### Usage in Application

**In routes:**
```python
import logging
from app.logging_config import get_logger

logger = get_logger("omnidev_ai")

@router.post("/api/projects")
async def create_project(data: ProjectCreate, db: Session):
    try:
        project = service.create_project(data)
        logger.info(
            "Project created",
            extra={
                "project_id": project.id,
                "title": project.title,
                "status": "success"
            }
        )
        return project
    except Exception as e:
        logger.error(
            "Project creation failed",
            extra={
                "error": str(e),
                "status": "error"
            }
        )
        raise
```

---

## Deployment & Running

### Start Development Server

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Run Tests Before Deployment

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Generate coverage report
pytest tests/ --cov=app --cov-report=html
```

### Docker Deployment

```bash
# Build image
docker build -f docker/Dockerfile -t omnidev-ai:latest .

# Run with docker-compose
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose logs -f app
```

### Environment Configuration

Create `.env` file in backend root:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/omnidev

# Authentication
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/app.log

# Rate Limiting
RATE_LIMIT_ENABLED=true
```

---

## Best Practices

### WebSocket

✅ **DO:**
- Always authenticate WebSocket connections with tokens
- Send keep-alive pings every 30 seconds
- Implement automatic reconnection on client side
- Use specific room names (project:123, task:456)
- Log all connections and disconnections

❌ **DON'T:**
- Send large JSON payloads (>10KB per message)
- Block WebSocket thread with synchronous I/O
- Store unencrypted sensitive data in messages
- Keep connections open indefinitely without monitoring

### Rate Limiting

✅ **DO:**
- Implement exponential backoff on rate limit errors
- Respect `Retry-After` header
- Log rate limit violations for security analysis
- Use user-based limits for authenticated endpoints

❌ **DON'T:**
- Retry immediately on rate limit (429) error
- Bypass rate limits with IP rotation
- Set limits too high for critical operations
- Ignore rate limit warnings

### Testing

✅ **DO:**
- Write unit tests for business logic
- Write integration tests for API endpoints
- Aim for >80% code coverage
- Use fixtures for setup/teardown
- Test error conditions and edge cases

❌ **DON'T:**
- Skip testing database interactions
- Mock everything (some integration needed)
- Test implementation details instead of behavior
- Leave failing tests in the codebase

### Logging

✅ **DO:**
- Use structured JSON logging for all logs
- Include request IDs for tracing
- Log authentication events (login, logout, failures)
- Log performance metrics (latency, status codes)
- Use appropriate log levels (DEBUG < INFO < WARNING < ERROR)

❌ **DON'T:**
- Log sensitive data (passwords, tokens, API keys)
- Use string concatenation for log messages
- Log at wrong level (DEBUG for errors, ERROR for warnings)
- Leave debug logs in production code

### Security

✅ **DO:**
- Always require authentication for WebSocket connections
- Validate and sanitize all user inputs
- Use HTTPS/WSS in production
- Implement CORS carefully
- Keep dependencies updated

❌ **DON'T:**
- Trust client-side validation alone
- Send sensitive data in logs
- Use default/weak secret keys
- Expose internal error details to clients
- Skip security testing

---

## Summary

**Phase 4 Implementation Checklist:**

- ✅ WebSocket real-time features
- ✅ Advanced API filtering & pagination
- ✅ Rate limiting protection
- ✅ Comprehensive testing framework
- ✅ Structured logging configuration
- ✅ Production-ready error handling
- ✅ Documentation and examples

**Files Created/Modified:**
- `/app/realtime/` - WebSocket implementation
- `/app/middleware/` - Rate limiting
- `/app/api/filters.py` - Advanced filters
- `/app/logging_config.py` - Structured logging
- `/tests/` - Comprehensive test suite
- `requirements.txt` - Updated dependencies
- `app/main.py` - Integrated new features

**Ready for Phase 5:** Frontend integration, DevOps pipeline, monitoring dashboards.
