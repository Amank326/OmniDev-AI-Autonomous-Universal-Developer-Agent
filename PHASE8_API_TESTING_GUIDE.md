# Phase 8 API Testing Guide

**Purpose:** Manual testing of all 22 Phase 8 API endpoints  
**Prerequisites:** 
- Backend running on `http://localhost:8000`
- Valid JWT token in environment variable `TOKEN`
- PostgreSQL database with Phase 8 migration applied

---

## Setup: Get JWT Token

```bash
# Login to get token (adjust credentials)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Response:
# {
#   "access_token": "eyJhbGc...",
#   "token_type": "bearer"
# }

# Export token for use in tests
export TOKEN="eyJhbGc..."
```

---

## Test Suite: Cohort Management Endpoints

### 1. Create Cohort
```bash
curl -X POST http://localhost:8000/api/cohorts/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cohort_name": "January 2024 Signups",
    "cohort_type": "signup_month",
    "customer_ids": [1, 2, 3, 4, 5]
  }'

# Expected Response (201 Created):
# {
#   "cohort_id": 1,
#   "cohort_name": "January 2024 Signups",
#   "cohort_type": "signup_month",
#   "size": 5,
#   "active_count": 5,
#   "retention_rate": 100.0,
#   "avg_engagement_score": 45.3,
#   "avg_api_calls": 234.5,
#   "avg_revenue_per_user": 125.0,
#   "churn_rate": 0.0
# }
```

### 2. Get Retention Curve
```bash
curl -X GET http://localhost:8000/api/cohorts/retention/1 \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# [
#   {
#     "period_label": "Day 0",
#     "days_since_cohort": 0,
#     "retention_percentage": 100.0,
#     "retained_count": 5,
#     "api_calls_in_period": 1200,
#     "revenue_in_period": 625.0
#   },
#   {
#     "period_label": "Week 1",
#     "days_since_cohort": 7,
#     "retention_percentage": 95.0,
#     "retained_count": 5,
#     "api_calls_in_period": 1100,
#     "revenue_in_period": 600.0
#   },
#   {
#     "period_label": "Month 1",
#     "days_since_cohort": 30,
#     "retention_percentage": 85.0,
#     "retained_count": 4,
#     "api_calls_in_period": 950,
#     "revenue_in_period": 500.0
#   },
#   ...
# ]
```

### 3. Compare Cohorts
```bash
curl -X GET "http://localhost:8000/api/cohorts/compare?cohort_ids=1&cohort_ids=2" \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# [
#   {
#     "cohort_id": 1,
#     "cohort_name": "January 2024 Signups",
#     "retention_curves": [ ... ]
#   },
#   {
#     "cohort_id": 2,
#     "cohort_name": "February 2024 Signups",
#     "retention_curves": [ ... ]
#   }
# ]
```

### 4. Get Lifetime Value
```bash
curl -X GET http://localhost:8000/api/cohorts/ltv/1 \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# {
#   "customer_id": 1,
#   "historical_ltv": 1250.0,
#   "projected_ltv": 2100.0,
#   "ltv_tier": "High",
#   "ltv_percentile": 85.0,
#   "ltv_if_retained_12mo": 2500.0,
#   "ltv_if_churn_today": 1250.0,
#   "ltv_if_upsell": 2730.0,
#   "retention_probability_12mo": 0.85,
#   "churn_risk_score": 0.15
# }
```

### 5. Batch Recalculate LTV
```bash
curl -X POST http://localhost:8000/api/cohorts/ltv/recalculate \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# {
#   "updated": 5,
#   "total": 5,
#   "message": "LTV recalculation completed"
# }
```

---

## Test Suite: Customer Journey & Churn

### 6. Get Customer Journey
```bash
curl -X GET http://localhost:8000/api/cohorts/journey/1 \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# {
#   "customer_id": 1,
#   "current_stage": "retention",
#   "stage_entry_date": "2024-01-15T10:00:00",
#   "days_in_stage": 22,
#   "features_adopted": 5,
#   "engagement_trajectory": "growing",
#   "momentum_score": 0.75,
#   "at_risk": false,
#   "risk_factors": []
# }
```

### 7. Get Journey by Stage
```bash
curl -X GET "http://localhost:8000/api/cohorts/journey-by-stage/retention?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# {
#   "stage": "retention",
#   "count": 45,
#   "customers": [
#     {"id": 1, "days_in_stage": 22, "momentum_score": 0.75},
#     {"id": 2, "days_in_stage": 18, "momentum_score": 0.45},
#     ...
#   ],
#   "pagination": {"limit": 10, "offset": 0}
# }
```

### 8. Get Churn Flow Analysis
```bash
curl -X GET http://localhost:8000/api/cohorts/churn-flow/1 \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# {
#   "customer_id": 1,
#   "churn_probability": 0.15,
#   "risk_level": "low",
#   "days_to_churn_predicted": 45,
#   "signals_detected": 1,
#   "signal_names": ["activity_decline"],
#   "activity_decline": true,
#   "feature_usage_drop": false,
#   "api_call_decrease": false,
#   "engagement_score_drop": false,
#   "support_tickets_increase": false
# }
```

### 9. Get At-Risk Customers
```bash
curl -X GET "http://localhost:8000/api/cohorts/at-risk-customers?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# {
#   "count": 12,
#   "customers": [
#     {
#       "customer_id": 5,
#       "churn_probability": 0.72,
#       "risk_level": "critical",
#       "signals_detected": 5,
#       "signal_names": ["activity_decline", "feature_usage_drop", ...]
#     },
#     {
#       "customer_id": 8,
#       "churn_probability": 0.55,
#       "risk_level": "high",
#       "signals_detected": 3,
#       "signal_names": ["api_call_decrease", ...]
#     }
#   ],
#   "pagination": {"limit": 10, "offset": 0}
# }
```

---

## Test Suite: Feature Adoption

### 10. Track Feature Adoption
```bash
curl -X POST http://localhost:8000/api/cohorts/feature-adoption/1/export \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (201 Created):
# {
#   "customer_id": 1,
#   "feature_name": "export",
#   "usage_count": 12,
#   "usage_frequency": "weekly",
#   "early_adopter": true,
#   "days_to_adopt": 3,
#   "impact_on_retention": 0.25,
#   "correlated_with_upgrade": true
# }
```

### 11. Get Feature Adoption List
```bash
curl -X GET http://localhost:8000/api/cohorts/feature-adoption/1 \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# [
#   {
#     "feature_name": "export",
#     "usage_count": 12,
#     "usage_frequency": "weekly",
#     "early_adopter": true,
#     "impact_on_retention": 0.25
#   },
#   {
#     "feature_name": "collaboration",
#     "usage_count": 45,
#     "usage_frequency": "daily",
#     "early_adopter": false,
#     "impact_on_retention": 0.15
#   }
# ]
```

---

## Test Suite: Retention Interventions

### 12. Create Intervention
```bash
curl -X POST http://localhost:8000/api/cohorts/interventions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 5,
    "intervention_type": "discount",
    "intervention_name": "20% Off Annual Plan"
  }'

# Expected Response (201 Created):
# {
#   "id": 1,
#   "customer_id": 5,
#   "intervention_type": "discount",
#   "intervention_name": "20% Off Annual Plan",
#   "status": "suggested",
#   "created_at": "2024-02-06T10:30:00"
# }
```

### 13. Accept Intervention
```bash
curl -X POST http://localhost:8000/api/cohorts/interventions/1/accept \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# {
#   "success": true,
#   "message": "Intervention 1 accepted by customer 5"
# }
```

### 14. Check Intervention Effectiveness
```bash
curl -X GET http://localhost:8000/api/cohorts/interventions/1/effectiveness \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# {
#   "intervention_id": 1,
#   "churn_prevented": true,
#   "revenue_impact": 250.0,
#   "roi": 2.5,
#   "success": true
# }
```

---

## Test Suite: Custom Metrics

### 15. Create Custom Metric
```bash
curl -X POST http://localhost:8000/api/metrics \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Successful API Calls Rate",
    "description": "Percentage of successful API calls",
    "metric_type": "percentage",
    "formula": "(successful_calls / total_calls) * 100",
    "source_table": "api_logs",
    "source_fields": ["successful_calls", "total_calls"],
    "time_period": "daily",
    "aggregation": "avg",
    "threshold_warning": 80.0,
    "threshold_critical": 70.0
  }'

# Expected Response (201 Created):
# {
#   "id": 1,
#   "customer_id": 1,
#   "name": "Successful API Calls Rate",
#   "metric_type": "percentage",
#   "current_value": 98.5,
#   "trend_direction": "up",
#   "is_public": false
# }
```

### 16. List Custom Metrics
```bash
curl -X GET http://localhost:8000/api/metrics \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# [
#   {
#     "id": 1,
#     "name": "Successful API Calls Rate",
#     "metric_type": "percentage",
#     "current_value": 98.5,
#     "trend_direction": "up",
#     "created_at": "2024-02-06T10:00:00"
#   }
# ]
```

### 17. Get Metric Details
```bash
curl -X GET http://localhost:8000/api/metrics/1 \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# {
#   "id": 1,
#   "customer_id": 1,
#   "name": "Successful API Calls Rate",
#   "description": "Percentage of successful API calls",
#   "metric_type": "percentage",
#   "formula": "(successful_calls / total_calls) * 100",
#   "current_value": 98.5,
#   "previous_value": 97.2,
#   "change_percentage": 1.3,
#   "trend_direction": "up",
#   "threshold_warning": 80.0,
#   "threshold_critical": 70.0
# }
```

### 18. Calculate Metric Value
```bash
curl -X POST http://localhost:8000/api/metrics/1/calculate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "successful_calls": 985,
    "total_calls": 1000
  }'

# Expected Response (200 OK):
# {
#   "metric_id": 1,
#   "value": 98.5,
#   "status": "healthy",
#   "message": "Value: 98.5 (Threshold: 80.0 warning, 70.0 critical)"
# }
```

### 19. Get Metric History
```bash
curl -X GET "http://localhost:8000/api/metrics/1/history?days=30" \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# [
#   {
#     "recorded_at": "2024-02-06T10:00:00",
#     "value": 98.5,
#     "change_from_previous": 1.3,
#     "percent_change": 1.3
#   },
#   {
#     "recorded_at": "2024-02-05T10:00:00",
#     "value": 97.2,
#     "change_from_previous": -0.8,
#     "percent_change": -0.8
#   }
# ]
```

### 20. Update Metric Settings
```bash
curl -X PATCH http://localhost:8000/api/metrics/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold_warning": 85.0,
    "threshold_critical": 75.0,
    "is_public": true
  }'

# Expected Response (200 OK):
# {
#   "id": 1,
#   "name": "Successful API Calls Rate",
#   "threshold_warning": 85.0,
#   "threshold_critical": 75.0,
#   "is_public": true
# }
```

### 21. Delete Metric
```bash
curl -X DELETE http://localhost:8000/api/metrics/1 \
  -H "Authorization: Bearer $TOKEN"

# Expected Response (200 OK):
# {
#   "success": true,
#   "message": "Metric 1 deleted successfully"
# }
```

### 22. Validate Formula
```bash
curl -X POST http://localhost:8000/api/metrics/formula/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "formula": "(a + b) / c * 100"
  }'

# Expected Response (200 OK):
# {
#   "valid": true,
#   "formula": "(a + b) / c * 100",
#   "fields": ["a", "b", "c"],
#   "message": "Formula is valid"
# }
```

---

## Test Results Tracking

Create a test results log:

```bash
# Run all tests and save results
TEST_DATE=$(date +%Y-%m-%d_%H-%M-%S)
TEST_LOG="phase8_test_results_$TEST_DATE.txt"

echo "=== Phase 8 API Test Results ===" > $TEST_LOG
echo "Date: $(date)" >> $TEST_LOG
echo "" >> $TEST_LOG

# Test each endpoint and append result
for endpoint in {1..22}; do
  echo "Testing endpoint $endpoint..." >> $TEST_LOG
  # Run curl command and log response
  # curl ... >> $TEST_LOG 2>&1
done

echo "" >> $TEST_LOG
echo "=== Test Complete ===" >> $TEST_LOG

# Display results
cat $TEST_LOG
```

---

## Expected Status Codes

| Endpoint | Success | Auth Error | Validation Error |
|----------|---------|-----------|------------------|
| POST /cohorts/create | 201 | 401 | 422 |
| GET /cohorts/retention/{id} | 200 | 401 | 404 |
| GET /cohorts/compare | 200 | 401 | 422 |
| GET /cohorts/ltv/{id} | 200 | 401 | 404 |
| POST /cohorts/ltv/recalculate | 200 | 401 | 500 |
| GET /cohorts/journey/{id} | 200 | 401 | 404 |
| GET /cohorts/journey-by-stage/{stage} | 200 | 401 | 422 |
| GET /cohorts/churn-flow/{id} | 200 | 401 | 404 |
| GET /cohorts/at-risk-customers | 200 | 401 | 422 |
| POST /cohorts/feature-adoption/{cid}/{fname} | 201 | 401 | 404 |
| GET /cohorts/feature-adoption/{id} | 200 | 401 | 404 |
| POST /cohorts/interventions | 201 | 401 | 422 |
| POST /cohorts/interventions/{id}/accept | 200 | 401 | 404 |
| GET /cohorts/interventions/{id}/effectiveness | 200 | 401 | 404 |
| POST /metrics | 201 | 401 | 422 |
| GET /metrics | 200 | 401 | - |
| GET /metrics/{id} | 200 | 401 | 404 |
| POST /metrics/{id}/calculate | 200 | 401 | 422 |
| GET /metrics/{id}/history | 200 | 401 | 404 |
| PATCH /metrics/{id} | 200 | 401 | 422 |
| DELETE /metrics/{id} | 200 | 401 | 404 |
| POST /metrics/formula/validate | 200 | 401 | 422 |

---

## Common Errors & Solutions

### 401 Unauthorized
```
Solution: Check TOKEN environment variable is set
$ export TOKEN="your_jwt_token_here"
```

### 404 Not Found
```
Solution: Check endpoint path and resource ID
Common: Wrong path formatting, missing prefix (/api/cohorts/, /api/metrics/)
```

### 422 Unprocessable Entity
```
Solution: Validate request body matches schema
Check: JSON syntax, required fields, field types, enum values
```

### 500 Internal Server Error
```
Solution: Check server logs and database connection
Common: Database not initialized, missing migration, bad formula
```

---

**Last Updated:** 2026-02-06  
**Ready to Test:** YES ✅
