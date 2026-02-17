# API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### Authentication

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "Full Name"
}
```

Response (201):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "role": "user",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Response (200):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Users

#### List Users
```http
GET /users?skip=0&limit=100
Authorization: Bearer <token>
```

#### Get User
```http
GET /users/{user_id}
Authorization: Bearer <token>
```

#### Update User
```http
PUT /users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "New Name",
  "email": "newemail@example.com"
}
```

### AI Agents

#### Create Agent
```http
POST /agents
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Code Analyzer",
  "agent_type": "code_analyzer",
  "description": "Analyzes code quality",
  "configuration": {
    "language": "python",
    "rules": ["pep8", "complexity"]
  },
  "capabilities": ["static_analysis", "complexity_check"]
}
```

#### List Agents
```http
GET /agents?skip=0&limit=100
Authorization: Bearer <token>
```

#### Get Agent
```http
GET /agents/{agent_id}
Authorization: Bearer <token>
```

#### Create Agent Task
```http
POST /agents/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "agent_id": 1,
  "task_name": "Analyze Code",
  "input_data": {
    "code": "def hello(): print('world')",
    "language": "python"
  }
}
```

#### Get Task
```http
GET /agents/tasks/{task_id}
Authorization: Bearer <token>
```

### Notifications

#### Create Notification
```http
POST /notifications
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Welcome",
  "message": "Welcome to OmniDev AI",
  "channel": "email",
  "data": null
}
```

#### Get My Notifications
```http
GET /notifications/?skip=0&limit=100&unread_only=false
Authorization: Bearer <token>
```

#### Mark as Read
```http
PUT /notifications/{notification_id}/read
Authorization: Bearer <token>
```

### Subscriptions

#### Create Subscription
```http
POST /subscriptions
Authorization: Bearer <token>
Content-Type: application/json

{
  "plan": "pro",
  "stripe_subscription_id": "sub_xxxxx",
  "stripe_customer_id": "cus_xxxxx"
}
```

#### Get My Subscriptions
```http
GET /subscriptions/
Authorization: Bearer <token>
```

#### Get Subscription
```http
GET /subscriptions/{subscription_id}
Authorization: Bearer <token>
```

#### Cancel Subscription
```http
DELETE /subscriptions/{subscription_id}
Authorization: Bearer <token>
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse:
- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

## Pagination

List endpoints support pagination with query parameters:
- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum number of items to return (default: 100, max: 100)

## Interactive Documentation

Visit these URLs for interactive API documentation:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc
