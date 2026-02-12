# Phase 5 Quick Start - Payment Integration

## 5-Minute Setup

### 1. Get Stripe API Keys

1. Create [Stripe account](https://stripe.com)
2. Go to Dashboard → Developers → API Keys
3. Copy **Secret Key** and **Publishable Key**
4. Create webhook endpoint at `https://your-domain.com/webhooks/stripe`
5. Copy **Signing Secret**

### 2. Update Environment Variables

**Backend (`.env.production` or `.env.development`):**
```env
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLIC_KEY=pk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

**Frontend (`.env.local`):**
```env
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_xxxxx
```

### 3. Run Database Migration

```bash
# Enter backend container
docker exec -it omnidev-backend bash

# Run migration
cd /app
alembic upgrade head
```

Verify tables created:
```bash
# Inside container
python
>>> from app.models.payment_models import *
>>> from app.database import SessionLocal
>>> db = SessionLocal()
>>> from sqlalchemy import inspect
>>> inspector = inspect(db.get_bind())
>>> tables = inspector.get_table_names()
>>> print([t for t in tables if 'stripe' in t or 'pricing' in t or 'subscription' in t])
```

Expected tables:
- stripe_customers
- pricing_plans
- subscriptions
- invoices
- payment_methods
- payment_transactions
- usage_records
- coupons

### 4. Initialize Pricing Plans

Create a script at `/backend/app/init_pricing.py`:

```python
from app.database import SessionLocal
from app.models.payment_models import PricingPlan
from datetime import datetime
import uuid

db = SessionLocal()

plans_data = [
    {
        "name": "Free",
        "tier": "free",
        "description": "Perfect for getting started",
        "price_monthly": None,
        "price_annual": None,
        "features": ["Basic API access", "Community support", "5 projects"],
        "limits": {"api_calls_per_day": 100, "storage_gb": 1, "team_members": 1},
        "trial_days": None,
    },
    {
        "name": "Starter",
        "tier": "starter",
        "description": "For individual developers",
        "price_monthly": 900,  # $9.00 in cents
        "price_annual": 9900,  # $99.00 in cents ($8.25/month)
        "features": ["Standard API access", "Email support", "50 projects", "Basic analytics"],
        "limits": {"api_calls_per_day": 10000, "storage_gb": 50, "team_members": 2},
        "trial_days": 14,
    },
    {
        "name": "Professional",
        "tier": "professional",
        "description": "For teams and advanced usage",
        "price_monthly": 4900,  # $49.00 in cents
        "price_annual": 49000,  # $490.00 in cents ($40.83/month)
        "features": ["Priority API access", "Priority support", "Unlimited projects", "Advanced analytics", "Team collaboration"],
        "limits": {"api_calls_per_day": 100000, "storage_gb": 1000, "team_members": 10},
        "trial_days": 30,
    },
    {
        "name": "Enterprise",
        "tier": "enterprise",
        "description": "Custom for your needs",
        "price_monthly": None,
        "price_annual": None,
        "features": ["Dedicated support", "Custom integrations", "SLA guarantee", "Advanced security"],
        "limits": {"api_calls_per_day": "unlimited", "storage_gb": "unlimited", "team_members": "unlimited"},
        "trial_days": None,
    },
]

now = datetime.utcnow()

for plan_data in plans_data:
    plan = PricingPlan(
        id=str(uuid.uuid4()),
        **plan_data,
        created_at=now,
        updated_at=now,
    )
    db.add(plan)

db.commit()
print(f"✅ Created {len(plans_data)} pricing plans")
db.close()
```

Run it:
```bash
cd /backend && python -c "from app.init_pricing import *"
```

### 5. Test Endpoints

**List pricing plans:**
```bash
curl http://localhost:8000/api/payments/pricing
```

Expected response:
```json
{
  "plans": [
    {
      "id": "uuid",
      "name": "Free",
      "tier": "free",
      "price_monthly": null,
      "features": [...],
      ...
    }
  ]
}
```

**Get current subscription:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/payments/subscription
```

### 6. Test Frontend

1. Navigate to `/billing` page
2. Click on pricing plan
3. Complete payment with test card: `4242 4242 4242 4242`
4. Verify subscription created in Stripe Dashboard

## Testing Checklist

- [ ] Stripe API keys configured
- [ ] Database migration completed
- [ ] Pricing plans initialized
- [ ] Payment endpoints responding
- [ ] Billing page displays correctly
- [ ] Test card checkout succeeds
- [ ] Subscription appears in Stripe Dashboard
- [ ] Invoice generated and available
- [ ] Webhook events logged

## Common Commands

```bash
# View payment logs
docker logs omnidev-backend | grep payment

# Check database
docker exec -it omnidev-postgres psql -U omnidev -d omnidev_db \
  -c "SELECT COUNT(*) FROM stripe_customers;"

# Restart Stripe webhook listener (if using Stripe CLI)
stripe listen --forward-to localhost:8000/webhooks/stripe
```

## Test Stripe Cards

| Card | Purpose |
|------|---------|
| 4242 4242 4242 4242 | Success |
| 4000 0000 0000 0002 | Decline |
| 4000 0000 0000 3220 | 3D Secure Authentication |
| 5555 5555 5555 4444 | Mastercard |
| 3782 822463 10005 | American Express |

## Next Steps

- [ ] Deploy to production
- [ ] Set up Stripe live keys
- [ ] Configure production webhook endpoint
- [ ] Set up email notifications
- [ ] Monitor revenue metrics
- [ ] Create support documentation for customers

## Support

- **Stripe Docs:** https://stripe.com/docs
- **Issues:** Check `/backend/logs/payment.log`
- **Webhook Issues:** View Stripe Dashboard → Developers → Webhooks → Delivery

---

**Phase 5 Status:** ✅ Payment Infrastructure Complete | 🔄 Frontend Components Integrated | ⏳ Production Ready

Total implementation time: ~2 hours
Total LOC added: 3,500+
