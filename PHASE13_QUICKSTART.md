# Phase 13: Advanced Monitoring & Observability - QUICKSTART

## Installation & Setup

### Prerequisites
- Python 3.13.7 with FastAPI installed
- Node.js 18+ with React 18
- Backend running on port 8000
- Frontend running on port 3000

### Backend Setup

1. **Start the Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Verify Phase 13 Services:**
```bash
curl -H "x-tenant-id: test-tenant" http://localhost:8000/api/v1/monitoring/health
```

Expected Response:
```json
{
  "status": "healthy",
  "services": {
    "tracing": true,
    "metrics": true,
    "sla": true,
    "anomalies": true,
    "alerts": true,
    "costs": true
  }
}
```

### Frontend Setup

1. **Install Dependencies:**
```bash
cd frontend
npm install
```

2. **Start Frontend:**
```bash
npm start
```

3. **Access Dashboard:**
Open `http://localhost:3000` and navigate to Monitoring section

---

## API Examples

### Distributed Tracing

**Get Recent Traces:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/traces?limit=20
```

**Get Trace Details:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/traces/trace_abc123def456
```

**Get Service Dependencies:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/service-dependencies
```

**Get Critical Path (Slowest Spans):**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/traces/trace_abc123def456/critical-path
```

### Metrics

**Get All Metrics:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/metrics
```

**Get Specific Metric Time Series:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/metrics/http_request_duration_ms?limit=100
```

**Get P95 Latency:**
```bash
curl -H "x-tenant-id: tenant-123" \
  "http://localhost:8000/api/v1/monitoring/metrics/http_request_duration_ms/percentile?percentile=95&hours=1"
```

**Get Rolling Average:**
```bash
curl -H "x-tenant-id: tenant-123" \
  "http://localhost:8000/api/v1/monitoring/metrics/http_request_duration_ms/rolling-average?window_minutes=5"
```

**Export Metrics (Prometheus Format):**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/metrics/export/prometheus
```

### SLA/SLO Tracking

**Get SLA Compliance:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/sla/sla_xyz789abc/compliance?hours=24
```

**Get Error Budget:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/sla/sla_xyz789abc/budget?hours=24
```

**Get SLA Report:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/sla/sla_xyz789abc/report?hours=24
```

### Anomaly Detection

**Get Anomalies:**
```bash
curl -H "x-tenant-id: tenant-123" \
  "http://localhost:8000/api/v1/monitoring/anomalies?hours=24&limit=10"
```

**Explain Anomaly:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/anomalies/anom_123456789/explain
```

**Predict Next Anomaly:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/anomalies/http_request_duration_ms/predict
```

**Get Metric Trend:**
```bash
curl -H "x-tenant-id: tenant-123" \
  "http://localhost:8000/api/v1/monitoring/anomalies/http_request_duration_ms/trend?hours=1"
```

### Alerts

**Get Active Alerts:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/alerts
```

**Acknowledge Alert:**
```bash
curl -X POST \
  -H "x-tenant-id: tenant-123" \
  -H "x-user-id: user-456" \
  http://localhost:8000/api/v1/monitoring/alerts/alert_abc123def/acknowledge
```

**Resolve Alert:**
```bash
curl -X POST \
  -H "x-tenant-id: tenant-123" \
  -H "x-user-id: user-456" \
  http://localhost:8000/api/v1/monitoring/alerts/alert_abc123def/resolve
```

**Get Alert History:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/alerts/history?limit=50
```

### Cost Analysis

**Get Cost Breakdown:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/costs/breakdown?group_by=category
```

**Get Monthly Costs:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/costs/monthly?months=12
```

**Forecast Future Costs:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/costs/forecast?months=3
```

**Get Optimization Recommendations:**
```bash
curl -H "x-tenant-id: tenant-123" \
  http://localhost:8000/api/v1/monitoring/costs/optimizations
```

**Optimize for Budget:**
```bash
curl -X POST \
  -H "x-tenant-id: tenant-123" \
  -H "Content-Type: application/json" \
  -d '{"budget": 5000}' \
  http://localhost:8000/api/v1/monitoring/costs/optimize-for-budget
```

---

## React UI Navigation

### ObservabilityDashboard
**Access:** Dashboard → Monitoring → Observability

**Tabs:**
- **Overview:** Real-time summary with recent traces and alerts
- **Metrics:** Select metric and view time-series graph
- **SLA/SLO:** Compliance status and error budget
- **Anomalies:** Recent detected anomalies with severity
- **Alerts:** Active alerts with acknowledge button
- **Costs:** Cost breakdown and monthly trends

**Actions:**
- Refresh data: Click "Refresh" button
- Acknowledge alert: Click "Acknowledge" button on alert card
- View trace details: Click trace ID in Recent Traces

### TraceViewer
**Access:** Monitoring → Trace Viewer OR click trace ID from Overview

**Tabs:**
- **Waterfall Timeline:** Visual timeline with offset bars
- **Span Details:** Click span to view tags, metrics, logs
- **Service Dependencies:** Tree view of service calls
- **Critical Path:** Longest chain of spans

**Actions:**
- Export trace: Click "Export" button to download JSON
- Refresh: Click "Refresh" to reload trace
- Select span: Click span ID in waterfall view

### CostAnalysis
**Access:** Dashboard → Monitoring → Cost Analysis

**Views:**
- **Cost Breakdown:** Pie chart of costs by category
- **Monthly Trend:** 12-month line graph
- **Forecast:** 3-month bar chart projection
- **Recommendations:** Optimization opportunities

**Actions:**
- Optimize for budget: Click "Optimize for Budget" button
- Export data: Each chart has export option

---

## Common Tasks

### Monitor API Performance
1. Go to ObservabilityDashboard
2. Navigate to "Metrics" tab
3. Select `http_request_duration_ms`
4. View graph and percentiles
5. Create alert for p99 > 500ms

### Investigate Slow Request
1. Find trace in ObservabilityDashboard → Overview
2. Click trace ID to open TraceViewer
3. View Waterfall Timeline
4. Click slowest span for details
5. Check tags and logs
6. Compare with service dependency graph

### Set Up Cost Budget
1. Go to CostAnalysis
2. Review current monthly cost
3. Click "Optimize for Budget"
4. Enter target budget amount
5. Review recommendations
6. Implement suggested optimizations

### Track Availability SLA
1. Go to ObservabilityDashboard → SLA/SLO
2. View current compliance rate
3. Monitor error budget remaining
4. Set alert for budget threshold
5. Review report for compliance history

### Detect Performance Regressions
1. Monitor metrics trends weekly
2. Create alert for metric > baseline
3. ObservabilityDashboard shows alerts
4. Use TraceViewer to identify root cause
5. Compare with recent deployments

---

## Configuration & Customization

### Adjust Sensitivity Levels
**Anomaly Detection (anomaly_detector_ml.py):**
```python
detector.sensitivity_level = 2.5  # Default: 2.5 sigma
# Lower = more sensitive (more false positives)
# Higher = less sensitive (may miss real anomalies)
```

### Change Metric Retention
**Metrics Aggregator (metrics_aggregator.py):**
```python
aggregator.metric_retention_days = 90  # Default: 90 days
# Adjust for longer/shorter history
```

### Configure Trace Retention
**Distributed Tracer (distributed_tracer.py):**
```python
tracer.trace_retention_hours = 24  # Default: 24 hours
# Adjust for longer/shorter trace history
```

### Add Custom Notification Channel
In **alert_manager.py**, extend `AlertManager._send_to_channel()`:
```python
elif channel == NotificationChannel.CUSTOM:
    self._send_custom(alert)
```

### Adjust SLA Policies
In **sla_slo_manager.py**, modify `SLAPolicy.policies`:
```python
"PROFESSIONAL": {
    "availability": 99.5,
    "response_time_p99": 200,
    # ... adjust thresholds
}
```

---

## Troubleshooting

### Services Not Available
**Problem:** Health check returns "services: false"

**Solution:**
1. Verify backend started successfully
2. Check for import errors in logs
3. Ensure all service files exist in app/services/
4. Verify middleware registered in main.py

### No Traces Recorded
**Problem:** GET /traces returns empty list

**Solution:**
1. Make requests to backend to generate traces
2. Verify monitoring_middleware is added
3. Check x-tenant-id header in requests
4. Ensure MonitoringMiddleware before route handlers

### Metrics Not Showing
**Problem:** Metrics list empty

**Solution:**
1. Make HTTP requests to trigger metric recording
2. Verify MonitoringMiddleware logging metrics
3. Check default metric recording in middleware
4. Ensure metrics_aggregator instance created

### Anomaly Not Detected
**Problem:** No anomalies despite unusual values

**Solution:**
1. Need 100+ baseline samples to train
2. Check sensitivity_level (default: 2.5 sigma)
3. Verify metric values being recorded
4. Look at anomaly_score for value (should be > 0.5)

### Alerts Not Firing
**Problem:** No alerts created despite conditions met

**Solution:**
1. Verify alert rules created via API or code
2. Check condition syntax (e.g., "gt:100")
3. Ensure deduplication window hasn't suppressed it
4. Check metrics being recorded for rule condition
5. Verify notification channels configured

---

## Performance Tips

1. **Limit Trace Queries:** Use offset/limit to avoid large datasets
2. **Percentile Caching:** Calculate common percentiles (p50, p95, p99) infrequently
3. **Aggregation Interval:** Use appropriate aggregation (1m vs 1h) based on needs
4. **Alert Deduplication:** Adjust window to avoid spam
5. **Cost Calculation:** Run forecasting during off-peak hours
6. **Dashboard Refresh:** Use 30-60 second intervals instead of continuous

---

**Phase 13 is now ready for production use!** 🚀
