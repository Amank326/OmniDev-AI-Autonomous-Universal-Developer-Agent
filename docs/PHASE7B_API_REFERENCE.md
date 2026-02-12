# Phase 7B API Reference & Quick Start Guide

## Quick Start (5 Minutes)

### 1. Database Migration

```bash
# Execute Alembic migration to create new tables
alembic upgrade head

# Verify tables created:
# - user_activities
# - engagement_metrics
# - project_metrics
# - system_metrics
# - audit_logs
# - anomaly_detections
# - churn_predictions
# - customer_segments
# - predictive_alerts
# - recommendations
```

### 2. Import Components (Frontend)

```typescript
// pages/advanced-analytics.tsx
import {
  ActivityFeed,
  EngagementChart,
  AnomalyAlerts,
  ChurnPredictions,
  ProjectAnalytics,
  RevenueForecasting
} from '@/components/AdvancedAnalyticsComponents';

export default function AdvancedAnalyticsPage() {
  const customerId = useAuth().user.customer_id;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
      <ActivityFeed />
      <EngagementChart customerId={customerId} />
      <AnomalyAlerts />
      <ChurnPredictions customerId={customerId} />
      <ProjectAnalytics customerId={customerId} />
      <RevenueForecasting customerId={customerId} />
    </div>
  );
}
```

### 3. Register API Routes (Backend)

```python
# app/main.py
from app.api import activity_routes, metrics_websocket_routes

app.include_router(activity_routes.router)
app.include_router(metrics_websocket_routes.router)
```

### 4. Connect WebSocket (Frontend)

```typescript
// hooks/useRealtimeMetrics.ts
export function useRealtimeMetrics() {
  const token = localStorage.getItem('access_token');
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/live-metrics/${token}`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMetrics(prev => ({ ...prev, ...message }));
    };

    return () => ws.close();
  }, [token]);

  return metrics;
}
```

### 5. Start Logging Activities

```python
# In your request handlers
from app.services.advanced_analytics_service import AdvancedAnalyticsService

# Log activity
AdvancedAnalyticsService.log_user_activity(
    db=db,
    customer_id=user.customer_id,
    activity_type="feature_used",
    description="Used advanced analytics dashboard",
    endpoint="/analytics",
    ip_address=request.client.host
)
```

**That's it! You now have:**
- ✅ Activity tracking for 20 activity types
- ✅ Engagement scoring (0-100)
- ✅ Real-time WebSocket streaming
- ✅ 17 API endpoints operational
- ✅ Dashboard components rendering
- ✅ Churn predictions calculating
- ✅ Anomalies being detected

---

## Complete API Reference

### Activity Logs

#### GET `/api/activity/logs`
Retrieve activity logs with filtering and pagination

**Query Parameters:**
```
customer_id: int (required)
limit: int (default: 100, max: 1000)
offset: int (default: 0)
days: int (default: 30) - look back period
```

**Response (200):**
```json
[
  {
    "id": 1,
    "customer_id": 123,
    "activity_type": "api_call",
    "description": "API request completed",
    "endpoint": "/api/data/query",
    "created_at": "2026-02-06T10:30:00Z"
  }
]
```

#### POST `/api/activity/logs/log-event`
Log a custom activity event

**Query Parameters:**
```
activity_type: str (required) - from ActivityType enum
description: str (optional)
endpoint: str (optional)
```

**Response (201):**
```json
{
  "status": "logged",
  "activity_id": 1
}
```

#### GET `/api/activity/logs/summary`
Get activity statistics summary

**Query Parameters:**
```
customer_id: int (required)
days: int (default: 30)
```

**Response (200):**
```json
{
  "total_activities": 145,
  "activity_types": 8,
  "last_activity": "2026-02-06T14:22:00Z",
  "days_period": 30
}
```

---

### Engagement Metrics

#### GET `/api/activity/engagement/{customer_id}`
Get engagement score and component breakdown

**Path Parameters:**
```
customer_id: int (required)
```

**Query Parameters:**
```
period_days: int (default: 30)
```

**Response (200):**
```json
{
  "engagement_score": 75.5,
  "login_frequency_score": 18.0,
  "feature_usage_score": 16.5,
  "api_usage_score": 20.0,
  "retention_score": 20.0,
  "logins_30d": 28,
  "active_days_30d": 26,
  "feature_count_used": 8,
  "last_activity_at": "2026-02-06T14:22:00Z",
  "engagement_trend": "increasing"
}
```

**Score Interpretation:**
- 85-100: Excellent engagement
- 65-84: Good engagement
- 45-64: Fair engagement
- 25-44: Poor engagement
- 0-24: Critical engagement

#### POST `/api/activity/engagement/recalculate`
Manually trigger engagement score recalculation

**Query Parameters:**
```
customer_id: int (required)
```

**Response (200):**
```json
{
  "engagement_score": 75.5,
  "updated_at": "2026-02-06T14:30:00Z"
}
```

#### GET `/api/activity/engagement/trends/{customer_id}`
Analyze engagement trends over time

**Path Parameters:**
```
customer_id: int (required)
```

**Query Parameters:**
```
period_days: int (default: 90)
```

**Response (200):**
```json
{
  "trend": "increasing",
  "slope": 0.85,
  "weeks": {
    "5": 12,
    "6": 14,
    "7": 18,
    "8": 22
  },
  "total_activities": 66
}
```

---

### Churn Prediction

#### GET `/api/activity/churn/{customer_id}`
Get churn prediction for a customer

**Path Parameters:**
```
customer_id: int (required)
```

**Response (200):**
```json
{
  "customer_id": 123,
  "churn_probability": 0.45,
  "churn_risk_level": "high",
  "engagement_score": 62.0,
  "days_since_last_activity": 12,
  "subscription_tenure_days": 180,
  "payment_issues_count": 0,
  "intervention_recommended": true,
  "suggested_intervention": "Schedule business review call with customer"
}
```

**Risk Levels:**
- `critical`: 75-100% probability
- `high`: 50-74% probability
- `medium`: 30-49% probability
- `low`: 0-29% probability

#### POST `/api/activity/churn/predict-all`
Predict churn for all customers

**Response (200):**
```json
{
  "total_predictions": 456,
  "high_risk_count": 23,
  "results": [
    {
      "customer_id": 123,
      "churn_probability": 0.85,
      "risk_level": "critical",
      "intervention": "Immediate outreach required"
    }
  ]
}
```

---

### Anomaly Detection

#### GET `/api/activity/anomalies`
Get detected anomalies

**Query Parameters:**
```
customer_id: int (optional) - filter by customer
severity: str (optional) - "critical", "high", "medium", "low"
limit: int (default: 50)
```

**Response (200):**
```json
[
  {
    "id": 1,
    "anomaly_type": "revenue_drop",
    "severity": "high",
    "metric_name": "mrr",
    "expected_value": 50000,
    "actual_value": 42000,
    "deviation_percent": -16.0,
    "description": "MRR dropped 16% from expected level",
    "detected_at": "2026-02-06T13:45:00Z"
  }
]
```

#### POST `/api/activity/anomalies/detect`
Trigger anomaly detection immediately

**Response (200):**
```json
{
  "anomalies_detected": 2,
  "results": [...]
}
```

---

### Audit Logs

#### GET `/api/activity/audit-logs`
Retrieve audit trail for compliance

**Query Parameters:**
```
customer_id: int (required)
resource_type: str (optional) - filter by type
limit: int (default: 100)
offset: int (default: 0)
```

**Response (200):**
```json
[
  {
    "id": 1,
    "action": "update",
    "resource_type": "subscription",
    "resource_id": "sub_123",
    "changes_summary": "Upgraded from basic to pro plan",
    "actor_type": "user",
    "created_at": "2026-02-06T10:15:00Z"
  }
]
```

#### POST `/api/activity/audit-logs/create`
Create an audit log entry

**Query Parameters:**
```
action: str (required) - "create", "read", "update", "delete", etc.
resource_type: str (required) - "subscription", "customer", "payment", etc.
resource_id: str (required) - ID of the resource
changes_summary: str (optional)
```

**Response (201):**
```json
{
  "status": "created",
  "log_id": 1
}
```

---

### Recommendations

#### GET `/api/activity/recommendations/{customer_id}`
Get AI-powered recommendations

**Path Parameters:**
```
customer_id: int (required)
```

**Response (200):**
```json
[
  {
    "id": 1,
    "recommendation_type": "upsell",
    "recommendation_title": "Upgrade to Professional Plan",
    "recommendation_score": 85,
    "expected_value": 49.0,
    "sent": false,
    "clicked": false,
    "converted": false
  }
]
```

---

### Customer Segments

#### GET `/api/activity/segments/{customer_id}`
Get customer segment classification

**Path Parameters:**
```
customer_id: int (required)
```

**Response (200):**
```json
{
  "customer_id": 123,
  "segment_name": "High-Value Engaged",
  "value_segment": "enterprise",
  "engagement_segment": "highly-engaged",
  "segment_score": 0.92,
  "characteristics": {
    "profile": "Top-tier customer with strong engagement"
  }
}
```

---

### Predictive Alerts

#### GET `/api/activity/alerts`
Get predictive alerts

**Query Parameters:**
```
priority: str (optional) - "critical", "high", "medium", "low"
resolved: bool (default: false)
limit: int (default: 50)
```

**Response (200):**
```json
[
  {
    "id": 1,
    "alert_type": "churn_risk",
    "alert_title": "High Churn Risk Detected",
    "priority": "critical",
    "urgency": "immediate",
    "recommended_action": "Schedule customer success call",
    "acknowledged": false,
    "resolved": false
  }
]
```

#### POST `/api/activity/alerts/{alert_id}/acknowledge`
Mark alert as acknowledged

**Path Parameters:**
```
alert_id: int (required)
```

**Response (200):**
```json
{
  "status": "acknowledged"
}
```

---

### Project Metrics

#### GET `/api/activity/projects/{customer_id}`
Get per-project metrics

**Path Parameters:**
```
customer_id: int (required)
```

**Response (200):**
```json
[
  {
    "id": 1,
    "project_name": "Analytics API",
    "api_calls": 45234,
    "active_endpoints": 12,
    "error_rate": 0.5,
    "avg_response_time_ms": 245.6,
    "uptime_percentage": 99.95,
    "last_api_call_at": "2026-02-06T14:28:00Z"
  }
]
```

---

## WebSocket APIs

### Connection URLs

```
ws://localhost:8000/ws/live-metrics/{token}
ws://localhost:8000/ws/live-activity/{token}
ws://localhost:8000/ws/live-alerts/{token}
ws://localhost:8000/ws/live-engagement/{token}
```

### Message Format

All WebSocket messages use JSON format:

```json
{
  "type": "message_type",
  "timestamp": "2026-02-06T14:30:00Z",
  "data": {}
}
```

### Example: Listen to Revenue Updates

```javascript
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`ws://localhost:8000/ws/live-metrics/${token}`);

ws.onopen = () => {
  console.log('Connected to metrics stream');
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.type === 'revenue_update') {
    console.log(`MRR: $${msg.mrr}, ARR: $${msg.arr}`);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Send ping to keep connection alive
setInterval(() => {
  ws.send(JSON.stringify({ action: 'ping' }));
}, 30000);
```

---

## Response Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Server Error |

---

## Rate Limiting

- **Default**: 100 requests/minute per customer
- **Headers**:
  - `X-RateLimit-Limit: 100`
  - `X-RateLimit-Remaining: 75`
  - `X-RateLimit-Reset: 1707235800`

---

## Authentication

All API endpoints require JWT bearer token:

```bash
curl -X GET "http://localhost:8000/api/activity/logs" \
  -H "Authorization: Bearer {your_jwt_token}"
```

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message",
  "error_code": "RESOURCE_NOT_FOUND",
  "timestamp": "2026-02-06T14:30:00Z"
}
```

### Example Error Responses

**404 Not Found:**
```json
{
  "detail": "Customer 999 not found",
  "error_code": "CUSTOMER_NOT_FOUND"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid or expired token",
  "error_code": "INVALID_TOKEN"
}
```

**429 Too Many Requests:**
```json
{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

---

## Integration Examples

### Python (requests)
```python
import requests
import json

token = "your_jwt_token"
headers = {"Authorization": f"Bearer {token}"}

# Get engagement metrics
response = requests.get(
    "http://localhost:8000/api/activity/engagement/123",
    headers=headers
)
engagement = response.json()
print(f"Engagement Score: {engagement['engagement_score']}")

# Get churn prediction
response = requests.get(
    "http://localhost:8000/api/activity/churn/123",
    headers=headers
)
churn = response.json()
print(f"Churn Risk: {churn['churn_risk_level']}")
```

### JavaScript (fetch)
```javascript
const token = localStorage.getItem('access_token');
const headers = { 'Authorization': `Bearer ${token}` };

// Get engagement metrics
const engagement = await fetch(
  'http://localhost:8000/api/activity/engagement/123',
  { headers }
).then(r => r.json());

// Stream real-time alerts
const ws = new WebSocket(`ws://localhost:8000/ws/live-alerts/${token}`);
ws.onmessage = msg => console.log(JSON.parse(msg.data));
```

### cURL
```bash
TOKEN="your_jwt_token"

# Get all high-risk churn predictions
curl "http://localhost:8000/api/activity/churn/predict-all" \
  -H "Authorization: Bearer $TOKEN"

# Create audit log
curl -X POST "http://localhost:8000/api/activity/audit-logs/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "update",
    "resource_type": "subscription",
    "resource_id": "sub_123",
    "changes_summary": "Plan upgraded to pro"
  }'
```

---

## Pagination

Endpoints that return lists support pagination:

```
GET /api/activity/logs?limit=50&offset=0
GET /api/activity/audit-logs?limit=100&offset=50
```

**Response Headers:**
```
X-Total-Count: 456
X-Page-Size: 50
X-Page-Offset: 0
```

---

## Filtering

Most list endpoints support filtering:

```
GET /api/activity/anomalies?severity=high&customer_id=123
GET /api/activity/alerts?priority=critical&resolved=false
```

---

## Sorting

Supported sort parameters:

```
GET /api/activity/logs?sort=-created_at
GET /api/activity/churn/predict-all?sort=-churn_probability
```

---

Generated: 2026-02-06
Last Updated: 2026-02-06
API Version: 1.0.0
