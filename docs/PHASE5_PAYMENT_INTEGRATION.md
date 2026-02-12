# Phase 5: Payment Integration & Stripe Implementation

## Overview

Phase 5 implements complete payment processing and subscription management using Stripe. This enables monetization through multiple pricing tiers, recurring billing, and comprehensive invoice management.

## Architecture

### Backend Components

#### 1. Database Models (`/backend/app/models/payment_models.py`)

**StripeCustomer Model**
- Links app users to Stripe customer accounts
- Stores customer metadata and sync timestamp
- Relationships: subscriptions, invoices, payment_methods

**PricingPlan Model**
- 4-tier subscription model: FREE, STARTER, PROFESSIONAL, ENTERPRISE
- Monthly and annual pricing with trial period configuration
- Feature list and usage limits per tier
- Stripe product/price ID mapping for syncing

**Subscription Model**
- Tracks user subscriptions with Stripe sync
- Status: trialing, active, past_due, canceled, unpaid, ended
- Billing cycle tracking (monthly/annual)
- Trial end and cancellation scheduling

**Invoice Model**
- Billing records synchronized from Stripe
- Status: draft, open, paid, void, uncollectible
- Amount tracking (subtotal, tax, total)
- PDF URL for self-service downloads

**PaymentMethod Model**
- Saved credit cards and payment instruments
- Default payment method tracking
- Card details (brand, last 4, expiration)

**PaymentTransaction Model**
- Complete transaction history
- Status: pending, succeeded, failed, refunded, canceled
- One-time and recurring payment tracking

**UsageRecord Model**
- Metered billing for API usage
- Tracks consumption per metric (API calls, storage, etc.)
- Period-based billing calculations

**Coupon Model**
- Discount codes with percentage or fixed amount
- Redemption limits and validity periods
- Automatic sync with Stripe

### 2. Stripe Service Layer (`/backend/app/services/stripe_service.py`)

Comprehensive wrapper for Stripe API operations:

**Customer Management**
- `create_customer()` - Create Stripe customers
- `get_customer()` - Retrieve customer details
- `update_customer()` - Update customer metadata

**Checkout & Payments**
- `create_checkout_session()` - Initialize checkout flow
- `get_checkout_session()` - Verify checkout completion
- `create_payment_intent()` - One-time payments
- `get_payment_intent()` - Check payment status

**Subscriptions**
- `create_subscription()` - Set up recurring billing
- `get_subscription()` - Check subscription status
- `update_subscription()` - Change plans/pricing
- `cancel_subscription()` - Cancel at period end or immediately
- `list_subscriptions()` - Query active subscriptions

**Invoices**
- `get_invoices()` - Retrieve user invoices
- `get_invoice()` - Get specific invoice
- `finalize_invoice()` - Finalize draft invoices
- `pay_invoice()` - Manually trigger payment

**Products & Pricing**
- `create_product()` - Create Stripe products
- `create_price()` - Add pricing to products
- `list_products()` - Query products

**Utilities**
- `construct_webhook_event()` - Verify webhook signatures
- Comprehensive error handling and logging

### 3. API Routes (`/backend/app/api/payment_routes.py`)

RESTful endpoints for payment operations:

```
GET    /api/payments/pricing              - List all pricing plans
POST   /api/payments/checkout             - Create checkout session
GET    /api/payments/subscription         - Get current subscription
POST   /api/payments/subscription/cancel  - Cancel subscription
GET    /api/payments/invoices             - List user invoices (paginated)
GET    /api/payments/invoices/{id}        - Get invoice details
POST   /api/payments/billing-portal       - Open self-service portal
POST   /api/payments/payment-methods      - Add payment method
GET    /api/payments/payment-methods      - List saved cards
DELETE /api/payments/payment-methods/{id} - Remove payment method
```

All endpoints require JWT authentication via `get_current_user` dependency.

### 4. Webhook Handler (`/backend/app/api/webhooks.py`)

Stripe webhook event processing with 14 event handlers:

**Customer Events**
- `customer.created` - Log new customers
- `customer.updated` - Sync customer changes
- `customer.deleted` - Mark inactive

**Checkout Events**
- `checkout.session.completed` - Record successful checkout

**Payment Events**
- `payment_intent.succeeded` - Record successful payment
- `payment_intent.payment_failed` - Log failed payments

**Subscription Events**
- `customer.subscription.created` - Create subscription record
- `customer.subscription.updated` - Update subscription status
- `customer.subscription.deleted` - Mark ended

**Invoice Events**
- `invoice.created` - Create invoice record
- `invoice.paid` - Update payment status
- `invoice.payment_failed` - Track failed payments

**Payment Method Events**
- `payment_method.attached` - Save card details
- `payment_method.detached` - Mark inactive

### 5. Frontend Components

#### StripeCheckout.tsx
- **PricingCards** - Display all plans with features and pricing
- **StripeCheckout** - Embedded checkout form
- Monthly/annual pricing toggle
- Responsive grid layout

#### BillingPortal.tsx (380 LOC)
- Current subscription display with status
- Subscription cancellation
- Invoice history with PDF downloads
- Payment method management
- Stripe self-service portal integration

#### PaymentMethods.tsx (240 LOC)
- List saved payment methods
- Set default payment method
- Delete payment methods
- Add new payment method button

#### SubscriptionManager.tsx (320 LOC)
- Plan comparison view
- Monthly/annual pricing selection
- Upgrade/downgrade with plan selection
- Feature and limit display
- Automatic checkout integration

#### billing.tsx (280 LOC)
- Main billing page
- Tab navigation (overview, plans, payment methods)
- Account status overview
- Member since and email display
- Support contact information

## Pricing Tiers

### FREE
- Price: $0/month
- Features: Basic API access, community support
- Limits: 100 API calls/day, 1GB storage

### STARTER
- Price: $9/month ($99/year - save 8%)
- Features: Standard API access, email support
- Limits: 10,000 API calls/day, 50GB storage

### PROFESSIONAL
- Price: $49/month ($490/year - save 16%)
- Features: Priority API access, priority support, advanced features
- Limits: 100,000 API calls/day, 1TB storage

### ENTERPRISE
- Price: Custom
- Features: Dedicated support, custom integrations, SLA guarantee
- Limits: Unlimited API calls, unlimited storage

## Setup & Configuration

### 1. Environment Variables

Create `.env.production` and `.env.development`:

```env
# Stripe Keys
STRIPE_SECRET_KEY=sk_live_... (production) or sk_test_... (development)
STRIPE_PUBLIC_KEY=pk_live_... (production) or pk_test_... (development)
STRIPE_WEBHOOK_SECRET=whsec_...

# Application URLs
FRONTEND_URL=https://omnidev.ai (production) or http://localhost:3000 (development)
BACKEND_URL=https://api.omnidev.ai (production) or http://localhost:8000 (development)

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/omnidev_db
```

### 2. Database Migration

Run the migration to create payment tables:

```bash
# Inside backend container
cd /app
alembic upgrade head
```

This creates 8 new tables:
- stripe_customers
- pricing_plans
- subscriptions
- invoices
- payment_methods
- payment_transactions
- usage_records
- coupons

### 3. Initialize Pricing Plans

Create pricing plan records in the database:

```python
# In a management script or Django shell
from app.models.payment_models import PricingPlan
from sqlalchemy.orm import Session

plans = [
    PricingPlan(
        name="Free",
        tier="free",
        price_monthly=None,
        price_annual=None,
        features=["Basic API access", "Community support"],
        limits={"api_calls_per_day": 100, "storage_gb": 1},
        trial_days=None,
    ),
    PricingPlan(
        name="Starter",
        tier="starter",
        price_monthly=900,  # $9.00 in cents
        price_annual=9900,  # $99.00 in cents
        features=["Standard API access", "Email support", "Advanced analytics"],
        limits={"api_calls_per_day": 10000, "storage_gb": 50},
        trial_days=14,
    ),
    # ... more plans
]

for plan in plans:
    db.add(plan)
db.commit()
```

### 4. Install Stripe CLI (Optional - for testing)

```bash
# Download from https://stripe.com/docs/stripe-cli
stripe login
stripe listen --forward-to localhost:8000/webhooks/stripe
```

## Integration Steps

### Frontend Integration

1. **Install Stripe packages:**
```bash
npm install @stripe/js @stripe/react-stripe-js
```

2. **Create Stripe context provider:**
```tsx
// app/providers.tsx
import { loadStripe } from '@stripe/js';
import { Elements } from '@stripe/react-stripe-js';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLIC_KEY!);

export function StripeProvider({ children }) {
  return (
    <Elements stripe={stripePromise}>
      {children}
    </Elements>
  );
}
```

3. **Add billing page route:**
```tsx
// app/billing/page.tsx
import BillingPage from '@/pages/billing';
export default BillingPage;
```

### Backend Integration

1. **Install Stripe SDK:**
```bash
pip install stripe>=8.0.0
```

2. **Routes already registered** in `/backend/app/main.py`:
```python
from app.api.payment_routes import router as payment_router
from app.api.webhooks import router as webhook_router

app.include_router(payment_router)
app.include_router(webhook_router)
```

3. **Configure webhook signing secret:**
The webhook handler automatically validates Stripe signatures using the `STRIPE_WEBHOOK_SECRET` from environment.

## Testing

### Development Testing

1. **Use Stripe test mode:**
   - Use test API keys from Stripe Dashboard
   - Test card: `4242 4242 4242 4242` (expires any future date, any CVC)

2. **Test webhook events locally:**
```bash
stripe listen --forward-to localhost:8000/webhooks/stripe
stripe trigger payment_intent.succeeded
```

3. **Test subscription flow:**
   - Create checkout session
   - Complete payment with test card
   - Verify subscription created in Stripe Dashboard
   - Verify webhook events received and processed

### Unit Tests

```python
# Test payment service
def test_create_customer():
    result = StripeService.create_customer(
        user_id="user123",
        email="test@example.com"
    )
    assert result['success']
    assert 'stripe_customer_id' in result

def test_create_subscription():
    result = StripeService.create_subscription(
        customer_id="cus_xxx",
        price_id="price_xxx"
    )
    assert result['success']
    assert result['status'] in ['trialing', 'active']
```

## Monitoring & Observability

### Logging

All operations logged to `/backend/logs/payment.log`:

```
[2025-02-06 14:30:00] INFO: Created Stripe customer cus_xxx for user user123
[2025-02-06 14:31:00] INFO: Webhook event received: customer.subscription.created
[2025-02-06 14:32:00] ERROR: Payment failed for invoice inv_xxx - Declined
```

### Metrics

Monitor in Prometheus/Grafana:
- `payment_checkout_sessions_total` - Total checkout sessions created
- `payment_subscriptions_active` - Current active subscriptions
- `payment_revenue_usd` - Monthly recurring revenue
- `payment_failures_total` - Failed payment attempts

### Stripe Dashboard

Access [Stripe Dashboard](https://dashboard.stripe.com/) to:
- Monitor transaction volume and revenue
- Review customer activity
- Manage disputes and refunds
- Configure email notifications
- View webhook delivery logs

## Security Best Practices

1. **API Keys:** Store in environment variables, never commit to git
2. **Webhook Verification:** Always verify Stripe signature before processing
3. **PCI Compliance:** Never handle raw card data; use Stripe tokenization
4. **Rate Limiting:** Apply rate limits to payment endpoints (already done via slowapi)
5. **Audit Logging:** Log all payment operations for compliance

## Troubleshooting

### Common Issues

**Issue:** "Invalid API key"
- Solution: Verify `STRIPE_SECRET_KEY` in environment
- Check key format: `sk_test_...` or `sk_live_...`

**Issue:** "Webhook signature verification failed"
- Solution: Verify `STRIPE_WEBHOOK_SECRET` matches Stripe Dashboard
- Ensure webhook endpoint URL is registered in Stripe

**Issue:** "Subscription not created after checkout"
- Solution: Check webhook logs in Stripe Dashboard
- Verify database migration ran successfully
- Check `payment_webhooks.log` for processing errors

**Issue:** "Payment method not appearing in list"
- Solution: Verify `payment_methods.attached` webhook is triggered
- Check `stripe_payment_method_id` in database

### Debug Mode

Enable debug logging:

```python
# In app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps (Phase 6)

1. **Analytics Dashboard** - Visualize subscription and revenue metrics
2. **Usage Metering** - Implement per-API-call billing
3. **Advanced Promotions** - Promo codes, referral bonuses
4. **Invoice Customization** - Branding and custom fields
5. **Multi-currency** - Support payments in multiple currencies

## References

- [Stripe API Documentation](https://stripe.com/docs/api)
- [Stripe Python SDK](https://github.com/stripe/stripe-python)
- [Stripe Testing Guide](https://stripe.com/docs/testing)
- [Stripe Best Practices](https://stripe.com/docs/keys-management)
