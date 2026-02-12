# Phase 8 API Reference

Complete API documentation for cohort analysis and custom metrics endpoints.

**Base URL:** `http://localhost:8000/api`

**Authentication:** All endpoints require JWT Bearer token in `Authorization` header

---

## Cohort Analysis API

### POST /cohorts/create

Create a new customer cohort for analysis.

**Parameters:**
- `cohort_name` (query, required): Name of cohort (e.g., "January 2025")
- `cohort_type` (query, required): Grouping type
  - `signup_month`: Group by signup month
  - `signup_quarter`: Group by signup quarter
  - `signup_year`: Group by signup year
  - `first_purchase_month`: Group by first purchase
  - `first_feature_month`: Group by first feature usage
  - `product_tier`: Group by subscription tier
  - `geographic`: Group by region
  - `custom`: User-defined grouping
- `customer_ids` (query, repeated, required): Array of customer IDs to include

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/cohorts/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -G \
  -d "cohort_name=January 2025 Signups" \
  -d "cohort_type=signup_month" \
  -d "customer_ids=1&customer_ids=2&customer_ids=3"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "cohort_name": "January 2025 Signups",
  "cohort_type": "signup_month",
  "size": 3,
  "active_count": 2,
  "retention_rate": 66.7,
  "avg_engagement_score": 75.5,
  "churn_rate": 33.3,
  "created_at": "2025-01-20T10:30:00Z"
}
```

---

### GET /cohorts/retention/{cohort_id}

Get retention curve data for a cohort at key time intervals.

**Path Parameters:**
- `cohort_id` (required): Cohort ID

**Response (200 OK):**
```json
{
  "cohort_id": 1,
  "cohort_name": "January 2025 Signups",
  "points": [
    {
      "period_label": "Day 0",
      "days_since_cohort": 0,
      "retained_count": 3,
      "retention_percentage": 100.0,
      "api_calls_in_period": 150,
      "revenue_in_period": 3000.0
    },
    {
      "period_label": "Week 1",
      "days_since_cohort": 7,
      "retained_count": 3,
      "retention_percentage": 100.0,
      "api_calls_in_period": 420,
      "revenue_in_period": 1500.0
    },
    {
      "period_label": "Month 1",
      "days_since_cohort": 30,
      "retained_count": 2,
      "retention_percentage": 66.7,
      "api_calls_in_period": 240,
      "revenue_in_period": 800.0
    },
    {
      "period_label": "Month 3",
      "days_since_cohort": 90,
      "retained_count": 2,
      "retention_percentage": 66.7,
      "api_calls_in_period": 180,
      "revenue_in_period": 500.0
    },
    {
      "period_label": "Month 6",
      "days_since_cohort": 180,
      "retained_count": 2,
      "retention_percentage": 66.7,
      "api_calls_in_period": 100,
      "revenue_in_period": 300.0
    },
    {
      "period_label": "Month 12",
      "days_since_cohort": 365,
      "retained_count": 2,
      "retention_percentage": 66.7,
      "api_calls_in_period": 50,
      "revenue_in_period": 200.0
    }
  ]
}
```

---

### GET /cohorts/compare

Compare retention curves across multiple cohorts.

**Query Parameters:**
- `cohort_ids` (required, repeated): Array of cohort IDs to compare

**Example Request:**
```bash
curl http://localhost:8000/api/cohorts/compare?cohort_ids=1&cohort_ids=2 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (200 OK):**
```json
[
  {
    "cohort_id": 1,
    "cohort_name": "January 2025",
    "points": [...]
  },
  {
    "cohort_id": 2,
    "cohort_name": "February 2025",
    "points": [...]
  }
]
```

---

### GET /cohorts/ltv/{customer_id}

Get lifetime value projection for a customer.

**Path Parameters:**
- `customer_id` (required): Customer ID

**Response (200 OK):**
```json
{
  "customer_id": 123,
  "historical_ltv": 5000.0,
  "projected_ltv": 8500.0,
  "ltv_tier": "High",
  "retention_probability_12mo": 0.85,
  "ltv_if_retained_12mo": 9000.0,
  "ltv_if_upsell": 11050.0,
  "churn_risk_score": 0.3,
  "calculated_at": "2025-01-20T10:30:00Z"
}
```

**Response Meanings:**
- `historical_ltv`: Actual revenue generated to date
- `projected_ltv`: ML-based forecast of total lifetime value
- `ltv_tier`: Segmentation (High/Medium/Low)
- `ltv_if_retained_12mo`: Revenue if customer stays 12 more months
- `ltv_if_upsell`: Revenue if customer successfully upgrades
- `retention_probability_12mo`: Probability customer stays 12 months (0-1.0)
- `churn_risk_score`: Risk of churn in next 30 days (0-1.0)

---

### POST /cohorts/ltv/recalculate

Batch recalculate LTV for all customers (heavy operation).

**Response (200 OK):**
```json
{
  "updated": 450,
  "total": 500
}
```

---

### GET /cohorts/journey/{customer_id}

Map customer through AARRR funnel stages.

**Path Parameters:**
- `customer_id` (required): Customer ID

**Response (200 OK):**
```json
{
  "customer_id": 123,
  "current_stage": "retention",
  "days_in_stage": 45,
  "engagement_trajectory": "growing",
  "momentum_score": 0.6,
  "at_risk": false,
  "features_adopted": 4,
  "time_to_activation_days": 3
}
```

**Stage Definitions:**
- `awareness`: New customer, exploring product
- `consideration`: Evaluating features
- `activation`: Using core features
- `retention`: Regular, active user
- `revenue`: Paying customer
- `advocacy`: Promoting to others
- `churn`: Inactive or cancelled

---

### GET /cohorts/journey-by-stage/{stage}

Get all customers at a specific journey stage.

**Path Parameters:**
- `stage` (required): One of: awareness, consideration, activation, retention, revenue, advocacy, churn

**Query Parameters:**
- `limit` (optional, default=50): Max results to return
- `offset` (optional, default=0): Pagination offset

**Example Request:**
```bash
curl "http://localhost:8000/api/cohorts/journey-by-stage/retention?limit=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (200 OK):**
```json
{
  "stage": "retention",
  "count": 247,
  "customers": [123, 124, 125, ...]
}
```

---

### GET /cohorts/churn-flow/{customer_id}

Analyze churn trajectory and early warning signals.

**Path Parameters:**
- `customer_id` (required): Customer ID

**Response (200 OK):**
```json
{
  "customer_id": 123,
  "churn_probability": 0.45,
  "risk_level": "medium",
  "signals_detected": 2,
  "activity_decline": true,
  "feature_usage_drop": false,
  "engagement_score_drop": true,
  "intervention_offered": false,
  "churned": false
}
```

**Signal Interpretation:**
- `activity_decline`: Activity drop >30% in recent period
- `feature_usage_drop`: Engagement score dropped below 40
- `engagement_score_drop`: Negative trend in engagement
- `api_call_decrease`: <5 API calls in last 7 days
- `support_tickets_increase`: Increase in support requests

---

### GET /cohorts/at-risk-customers

Get customers at high churn risk for intervention.

**Query Parameters:**
- `limit` (optional, default=50): Max results
- `offset` (optional, default=0): Pagination offset

**Response (200 OK):**
```json
{
  "count": 12,
  "customers": [
    {
      "customer_id": 456,
      "churn_probability": 0.92,
      "signals_detected": 4,
      "risk_level": "critical"
    },
    {
      "customer_id": 457,
      "churn_probability": 0.78,
      "signals_detected": 3,
      "risk_level": "high"
    }
  ]
}
```

---

### POST /cohorts/feature-adoption/{customer_id}/{feature_name}

Track feature adoption.

**Path Parameters:**
- `customer_id` (required): Customer ID
- `feature_name` (required): Feature name (e.g., "api_webhooks")

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/cohorts/feature-adoption/123/api_webhooks \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (200 OK):**
```json
{
  "customer_id": 123,
  "feature": "api_webhooks",
  "usage_count": 1,
  "usage_frequency": "once",
  "early_adopter": true
}
```

---

### GET /cohorts/feature-adoption/{customer_id}

Get all features adopted by customer.

**Path Parameters:**
- `customer_id` (required): Customer ID

**Response (200 OK):**
```json
[
  {
    "customer_id": 123,
    "feature_name": "api_webhooks",
    "days_to_adopt": 2,
    "usage_count": 47,
    "usage_frequency": "daily",
    "early_adopter": true,
    "impact_on_retention": 0.85
  },
  {
    "customer_id": 123,
    "feature_name": "custom_dashboards",
    "days_to_adopt": 15,
    "usage_count": 5,
    "usage_frequency": "weekly",
    "early_adopter": false,
    "impact_on_retention": 0.65
  }
]
```

---

### POST /cohorts/interventions

Create retention intervention for at-risk customer.

**Query Parameters:**
- `customer_id` (required): Customer ID
- `intervention_type` (required): One of: discount, upgrade, training, support, business_review
- `intervention_name` (required): Name (e.g., "20% discount")
- `description` (optional): Detailed description

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/cohorts/interventions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -G \
  -d "customer_id=456" \
  -d "intervention_type=discount" \
  -d "intervention_name=20% discount - 3 months"
```

**Response (200 OK):**
```json
{
  "id": 42,
  "customer_id": 456,
  "intervention_type": "discount",
  "intervention_name": "20% discount - 3 months",
  "status": "suggested",
  "accepted": false,
  "success": false,
  "revenue_impact": 0.0,
  "created_at": "2025-01-20T10:30:00Z"
}
```

---

### POST /cohorts/interventions/{intervention_id}/accept

Mark intervention as accepted by customer.

**Path Parameters:**
- `intervention_id` (required): Intervention ID

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Intervention accepted"
}
```

---

### GET /cohorts/interventions/{intervention_id}/effectiveness

Evaluate intervention effectiveness and ROI.

**Path Parameters:**
- `intervention_id` (required): Intervention ID

**Response (200 OK):**
```json
{
  "churn_prevented": true,
  "revenue_impact": 3000.0,
  "roi": 2.5,
  "success": true
}
```

---

## Custom Metrics API

### POST /api/metrics

Create custom metric definition.

**Request Body:**
```json
{
  "name": "API Success Rate",
  "metric_type": "custom_formula",
  "description": "Percentage of successful API calls",
  "formula": "successful_calls / total_calls * 100",
  "threshold_warning": 95,
  "threshold_critical": 90
}
```

**Metric Types:**
- `count`: COUNT(*) from table
- `sum`: SUM(field) from table
- `average`: AVG(field) from table
- `percentage`: % calculation
- `ratio`: Ratio of two values
- `custom_formula`: User-defined formula

**Formula Syntax:**
- Operators: +, -, *, /, %, ()
- Field references: {field_name}
- Example: `(api_calls + webhooks) / total_requests * 100`

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "API Success Rate",
  "metric_type": "custom_formula",
  "formula": "successful_calls / total_calls * 100",
  "current_value": 0.0,
  "threshold_warning": 95,
  "threshold_critical": 90,
  "is_public": false,
  "created_by": "user@example.com"
}
```

---

### GET /api/metrics

List all accessible metrics.

**Query Parameters:**
- `include_public` (optional, default=true): Include public metrics from other users

**Response (200 OK):**
```json
{
  "count": 5,
  "metrics": [
    {
      "id": 1,
      "name": "API Success Rate",
      "metric_type": "custom_formula",
      "current_value": 98.5,
      "trend_direction": "down"
    }
  ]
}
```

---

### GET /api/metrics/{metric_id}

Get metric definition and current value.

**Path Parameters:**
- `metric_id` (required): Metric ID

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "API Success Rate",
  "metric_type": "custom_formula",
  "formula": "successful_calls / total_calls * 100",
  "current_value": 98.5,
  "previous_value": 97.3,
  "change_percentage": 1.2,
  "trend_direction": "up",
  "threshold_warning": 95,
  "threshold_critical": 90
}
```

---

### POST /api/metrics/{metric_id}/calculate

Calculate metric value with provided data.

**Path Parameters:**
- `metric_id` (required): Metric ID

**Request Body (for custom_formula):**
```json
{
  "successful_calls": 985,
  "total_calls": 1000
}
```

**Response (200 OK):**
```json
{
  "metric_id": 1,
  "name": "API Success Rate",
  "current_value": 98.5,
  "previous_value": 97.3,
  "change": 1.2,
  "change_percentage": 1.2,
  "trend_direction": "up",
  "status": "healthy",
  "calculated_at": "2025-01-20T10:30:00Z"
}
```

**Status Values:**
- `healthy`: Within normal range
- `warning`: At/above warning threshold
- `critical`: At/above critical threshold

---

### GET /api/metrics/{metric_id}/history

Get metric value history for trending.

**Path Parameters:**
- `metric_id` (required): Metric ID

**Query Parameters:**
- `days` (optional, default=30): Days of history to return

**Response (200 OK):**
```json
{
  "metric_id": 1,
  "name": "API Success Rate",
  "days": 30,
  "points": [
    {
      "date": "2025-01-20T10:30:00Z",
      "value": 98.5,
      "change": 1.2,
      "percent_change": 1.2
    },
    {
      "date": "2025-01-19T10:30:00Z",
      "value": 97.3,
      "change": -0.5,
      "percent_change": -0.5
    }
  ]
}
```

---

### PATCH /api/metrics/{metric_id}

Update metric settings.

**Path Parameters:**
- `metric_id` (required): Metric ID

**Query Parameters:**
- `threshold_warning` (optional): New warning threshold
- `threshold_critical` (optional): New critical threshold
- `is_public` (optional): Make metric public/private

**Example Request:**
```bash
curl -X PATCH http://localhost:8000/api/metrics/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -G \
  -d "threshold_warning=92" \
  -d "threshold_critical=85"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "API Success Rate",
  "threshold_warning": 92,
  "threshold_critical": 85,
  "is_public": false
}
```

---

### DELETE /api/metrics/{metric_id}

Delete metric and its history.

**Path Parameters:**
- `metric_id` (required): Metric ID

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Metric deleted"
}
```

---

### POST /api/metrics/formula/validate

Validate formula syntax before creating metric.

**Query Parameters:**
- `formula` (required): Formula to validate

**Example Request:**
```bash
curl "http://localhost:8000/api/metrics/formula/validate?formula=(successful_calls%2Ftotal_calls)*100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (200 OK):**
```json
{
  "valid": true,
  "formula": "(successful_calls / total_calls) * 100",
  "fields": ["successful_calls", "total_calls"],
  "message": "Formula is valid"
}
```

**Response (Invalid Formula):**
```json
{
  "valid": false,
  "error": "Unbalanced parentheses"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid metric type: invalid_type"
}
```

### 404 Not Found
```json
{
  "detail": "Metric not found"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Database error: [detailed message]"
}
```

---

## Rate Limiting

- Unauthenticated requests: 10 requests/minute
- Authenticated requests: 100 requests/minute
- Batch operations: 5 requests/minute

---

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict (duplicate) |
| 429 | Rate Limited |
| 500 | Server Error |

---

## Pagination

For endpoints that return lists, use `limit` and `offset` query parameters:

```bash
curl "http://localhost:8000/api/cohorts/at-risk-customers?limit=50&offset=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Sorting & Filtering

Common query parameters:
- `sort_by`: Field name to sort by
- `sort_direction`: asc or desc
- `filter`: Field=value filter

Example:
```bash
curl "http://localhost:8000/api/cohorts?sort_by=retention_rate&sort_direction=desc" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
