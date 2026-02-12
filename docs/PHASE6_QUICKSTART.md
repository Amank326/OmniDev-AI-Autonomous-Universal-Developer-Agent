# Phase 6: Analytics & Revenue Dashboard - Quickstart

**Get started with analytics in 30 minutes!**

---

## ⚡ Quick Setup

### 1. Run Database Migration
```bash
# Apply Phase 6 analytics tables
cd backend
alembic upgrade head
```

This creates 9 new tables:
- `analytics_events` - Event tracking
- `revenue_metrics` - Daily revenue aggregations
- `subscription_metrics` - Subscription stats
- `customer_metrics` - Customer analytics
- `forecasted_metrics` - Revenue predictions
- `dashboard_widgets` - Dashboard configuration
- `analytics_reports` - Generated reports
- `analytics_alerts` - Business alerts

### 2. Verify Backend Routes
```bash
# Start backend (if not running)
cd backend
uvicorn app.main:app --reload

# Test analytics endpoint
curl -X GET http://localhost:8000/api/analytics/dashboard \
  -H "Authorization: Bearer $YOUR_TOKEN"
```

You should get a response with MRR, ARR, LTV, churn rate, etc.

### 3. View Analytics Dashboard
```bash
# Visit analytics page
http://localhost:3000/analytics
```

You'll see:
- Dashboard tab with 6 metric cards
- Subscriptions tab with subscription metrics
- Customers tab with cohort analysis
- Export tab for downloading data

---

## 🎯 Key Metrics Explained

### Monthly Recurring Revenue (MRR)
The predictable monthly revenue from active subscriptions.
```
MRR = Sum of all active subscription prices per month
Current MRR = $2,450 (42 active subscriptions)
```

### Annual Recurring Revenue (ARR)
The annualized MRR for yearly revenue targets.
```
ARR = MRR × 12 = $29,400
```

### Customer Lifetime Value (LTV)
Average revenue earned from each customer over their lifetime.
```
Avg LTV = Total revenue / Number of customers = $543.21
```

### Churn Rate
Percentage of subscriptions that canceled in the period.
```
30-day churn = (3 canceled / 58 active at start) × 100 = 5.12%
Alert: Churn > 10% triggers critical alert
```

### Customer Health Score
0-100 score indicating customer engagement and payment health.
```
100 = Recent payment, consistent
70-80 = Some payment delays
< 50 = High risk (no recent payment)
```

### Churn Risk
Probability (0-1.0) that a customer will cancel.
```
0.0-0.3 = Low risk
0.3-0.7 = Medium risk
0.7-1.0 = High risk
```

---

## 📊 Dashboard Walkthrough

### Dashboard Tab
**View at-a-glance business metrics:**

1. **Metric Cards** (top row)
   - MRR, ARR, Avg LTV, Churn Rate, Total Customers, Retention Rate
   - Each card shows key number + supporting metric

2. **Revenue Breakdown** (bottom left)
   - Bar chart showing New Revenue, Churned Revenue, Net Revenue
   - Helps identify if losing more than gaining

3. **MRR Forecast** (bottom right)
   - 30-day prediction using linear trend
   - Confidence decreases over time

### Subscriptions Tab
**Track subscription-specific metrics:**

1. **Key Metrics**
   - Active subscriptions count
   - New subscriptions this month
   - Cancellations this month

2. **Subscription Trend**
   - 7-day area chart showing subscription growth
   - Real-time trend analysis

3. **Upgrades vs Cancellations**
   - Bar chart comparing conversions
   - Helps identify pricing tier issues

4. **Tier Breakdown**
   - Pie chart showing distribution across tiers
   - Which tier is most popular

### Customers Tab
**Understand customer behavior and risks:**

1. **Cohort Retention**
   - Table showing retention curves by signup month
   - Month 0 = 100%, Month 1 = 92%, Month 2 = 85%, etc.
   - Identify if retention improving over time

2. **Customer Health Distribution**
   - Scatter chart showing health score distribution
   - Identify clusters of healthy vs at-risk customers

3. **LTV by Cohort**
   - Line chart of average LTV per signup month
   - Identify which cohorts are most valuable

4. **Churn Risk Distribution**
   - Breakdown of customers by risk level
   - Visual heat map: Green (low) → Red (high)

5. **High Risk Customers**
   - Table of customers with > 60% churn risk
   - Action required section with contact info
   - Days inactive showing how long since last engagement

### Export Tab
**Download data for external analysis:**

1. **CSV Export**
   - Compatible with Excel, Google Sheets
   - Headers: Metric, Value, Unit, Timestamp

2. **JSON Export**
   - For API integrations
   - Complete metric structure

3. **PDF Export**
   - Coming in Phase 7
   - Professional reports ready to share

---

## 🔌 API Quick Reference

### Get All Metrics (Recommended)
```bash
GET /api/analytics/dashboard
# Returns: MRR, ARR, LTV, churn rate, revenue metrics, customer metrics, forecast
```

### Get Specific Metrics
```bash
GET /api/analytics/mrr              # Monthly recurring revenue
GET /api/analytics/arr              # Annual recurring revenue
GET /api/analytics/ltv              # Lifetime value
GET /api/analytics/churn-rate       # Churn percentage
GET /api/analytics/revenue          # Revenue breakdown
GET /api/analytics/customers        # Customer metrics
GET /api/analytics/forecast         # Revenue forecast
GET /api/analytics/cohort/2026-01   # Cohort analysis
```

### Export Data
```bash
POST /api/analytics/export
# Body: {"format": "csv|json", "period_days": 30}
# Returns: File download or JSON data
```

### Refresh Metrics Manually
```bash
POST /api/analytics/refresh-metrics
# Updates all customer metrics and checks for alerts
```

---

## 💡 Usage Examples

### Example 1: Track Monthly Revenue
```bash
# Get current MRR
curl http://localhost:8000/api/analytics/mrr \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "value": 2450.00,
  "subscription_count": 42,
  "method": "active_subscriptions"
}

# Use in: Revenue reports, investor updates, financial planning
```

### Example 2: Monitor At-Risk Customers
```bash
# Get customer metrics
curl http://localhost:8000/api/analytics/customers \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "total_customers": 58,
  "retention_rate": 91.4,
  "churned_customers_30d": 3
}

# Action: If retention < 85%, contact at-risk customers
```

### Example 3: Analyze Cohorts
```bash
# Get cohort retention for Jan 2026 signups
curl http://localhost:8000/api/analytics/cohort/2026-01 \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "cohort_size": 12,
  "retention": {
    "month_0": 100.0,
    "month_1": 91.67,
    "month_2": 83.33
  }
}

# Use in: Identifying when/how customers churn
```

---

## 🎓 Common Questions

### Q: When is MRR calculated?
**A:** MRR is calculated in real-time by summing all active subscriptions. Updated whenever a subscription changes (new, upgrade, cancel).

### Q: How often is the forecast updated?
**A:** Forecast regenerates daily using 90 days of historical data. Confidence decreases over time (99% @ day 1 → 60% @ day 30).

### Q: Why is my churn rate high?
**A:** Churn = canceled subscriptions / active at period start.
- If 3 canceled out of 58 active = 5% churn
- Industry average for SaaS: 3-7% monthly
- 10%+ triggers critical alert

### Q: How is customer health calculated?
**A:** Health score = 100 - penalties for payment recency
- 100 = Payment within 7 days
- 85 = Payment within 7-30 days
- 70 = Payment within 30-60 days
- 20 = No payment in 90+ days

### Q: Can I customize the dashboard?
**A:** In Phase 7! Currently fixed layout, but you can:
- Switch between tabs
- Export data to analyze externally
- View different time periods (7d/30d/90d)

### Q: Are my analytics private?
**A:** Yes! Each customer only sees their own metrics. Authentication is required on all endpoints.

---

## 🧪 Test the Analytics

### Without Real Data
The dashboard works with generated sample data if no subscriptions exist yet.

### With Real Data
1. Create some test subscriptions in billing UI
2. Make some test payments
3. Visit analytics page - metrics will populate

### Expected Sample Values
```
- MRR: $2,450
- ARR: $29,400
- Avg LTV: $543
- Churn rate: 5%
- Total customers: 58
- Retention: 91%
```

---

## 📞 Troubleshooting

### Issue: Dashboard shows "No data available"
**Solution:** 
1. Verify JWT token is valid
2. Check database migration ran: `alembic history`
3. Verify subscription data exists in `subscriptions` table

### Issue: Charts not rendering
**Solution:**
1. Check browser console for errors
2. Verify recharts library installed: `npm list recharts`
3. Hard refresh page (Cmd/Ctrl + Shift + R)

### Issue: Metrics appear incorrect
**Solution:**
1. Manually trigger refresh: `POST /api/analytics/refresh-metrics`
2. Check `customer_metrics` table populated
3. Verify payment data in `payment_transactions`

### Issue: Export fails
**Solution:**
1. For CSV: Verify database query completes
2. For JSON: Check response format in Network tab
3. Verify storage permissions on server

---

## 🚀 What's Next

After Phase 6, you have:
- ✅ Complete revenue tracking
- ✅ Subscription analytics
- ✅ Customer insights
- ✅ Real-time dashboard

**Next Steps:**
1. **Phase 7:** Advanced analytics (ML churn prediction, email reports)
2. **Monitor metrics** daily - look for trends
3. **Set up alerts** for churn spikes or revenue drops
4. **Export reports** weekly for stakeholders
5. **Optimize pricing** based on tier distribution

---

## 📚 More Resources

- **Full Documentation:** See `PHASE6_ANALYTICS.md`
- **API Reference:** See `PHASE6_API_REFERENCE.md`
- **Testing Guide:** See `PHASE6_TESTING.md`
- **Phase 5 (Payments):** See `PHASE5_PAYMENT_INTEGRATION.md`

---

**Analytics Dashboard Ready!** 📊  
Check out http://localhost:3000/analytics to see your business metrics.
