# Environment Configuration for Phase 5 - Payment Integration

## Development Environment (.env.development)

```env
# ============================================
# DATABASE
# ============================================
DATABASE_URL=postgresql://omnidev:omnidev@localhost:5432/omnidev_db
DATABASE_ECHO=false
DATABASE_POOL_SIZE=10

# ============================================
# STRIPE (TESTING)
# ============================================
# Get these from: https://dashboard.stripe.com/test/apikeys
STRIPE_SECRET_KEY=sk_test_YOUR_SECRET_KEY_HERE
STRIPE_PUBLIC_KEY=pk_test_YOUR_PUBLIC_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_test_YOUR_WEBHOOK_SECRET_HERE

# ============================================
# APPLICATION URLs
# ============================================
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# ============================================
# PAYMENT CONFIGURATION
# ============================================
PAYMENT_SUCCESS_URL=http://localhost:3000/billing?success=true
PAYMENT_CANCEL_URL=http://localhost:3000/billing?canceled=true
STRIPE_API_VERSION=2024-06-20

# ============================================
# SECURITY
# ============================================
SECRET_KEY=your-secret-key-for-development
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ============================================
# EMAIL (for receipts and notifications)
# ============================================
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SENDER_EMAIL=noreply@omnidev.ai

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=DEBUG
```

## Production Environment (.env.production)

```env
# ============================================
# DATABASE
# ============================================
DATABASE_URL=postgresql://prod_user:SECURE_PASSWORD@prod-db.internal:5432/omnidev_db
DATABASE_ECHO=false
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# ============================================
# STRIPE (LIVE)
# ============================================
# Get these from: https://dashboard.stripe.com/apikeys
# IMPORTANT: Use LIVE keys only in production
STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_SECRET_KEY
STRIPE_PUBLIC_KEY=pk_live_YOUR_LIVE_PUBLIC_KEY
STRIPE_WEBHOOK_SECRET=whsec_live_YOUR_LIVE_WEBHOOK_SECRET

# ============================================
# APPLICATION URLs
# ============================================
BACKEND_URL=https://api.omnidev.ai
FRONTEND_URL=https://omnidev.ai

# ============================================
# PAYMENT CONFIGURATION
# ============================================
PAYMENT_SUCCESS_URL=https://omnidev.ai/billing?success=true
PAYMENT_CANCEL_URL=https://omnidev.ai/billing?canceled=true
STRIPE_API_VERSION=2024-06-20

# ============================================
# SECURITY
# ============================================
SECRET_KEY=GENERATE_STRONG_RANDOM_KEY_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=https://omnidev.ai,https://www.omnidev.ai

# ============================================
# EMAIL (for receipts and notifications)
# ============================================
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.YOUR_SENDGRID_API_KEY
SENDER_EMAIL=billing@omnidev.ai

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=INFO
LOG_FILE=/var/log/omnidev/payment.log

# ============================================
# MONITORING
# ============================================
SENTRY_DSN=https://YOUR_SENTRY_KEY@sentry.io/YOUR_PROJECT_ID
```

## Docker Compose Override (.env for docker-compose)

```env
# ============================================
# POSTGRES
# ============================================
POSTGRES_USER=omnidev
POSTGRES_PASSWORD=omnidev
POSTGRES_DB=omnidev_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# ============================================
# STRIPE
# ============================================
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLIC_KEY=pk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_test_xxxxx

# ============================================
# BACKEND SERVICE
# ============================================
BACKEND_PORT=8000
WORKERS=4
LOG_LEVEL=debug
```

## Frontend Environment (.env.local)

```env
# ============================================
# STRIPE PUBLIC KEY (Safe to expose)
# ============================================
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_YOUR_PUBLIC_KEY_HERE

# ============================================
# API CONFIGURATION
# ============================================
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=OmniDev AI

# ============================================
# ENVIRONMENT
# ============================================
NODE_ENV=development
```

## Frontend Environment (Production - .env.production)

```env
# ============================================
# STRIPE PUBLIC KEY (Safe to expose)
# ============================================
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_live_YOUR_LIVE_PUBLIC_KEY

# ============================================
# API CONFIGURATION
# ============================================
NEXT_PUBLIC_API_URL=https://api.omnidev.ai
NEXT_PUBLIC_APP_NAME=OmniDev AI

# ============================================
# ENVIRONMENT
# ============================================
NODE_ENV=production
```

## Setup Instructions

### 1. Backend Development Setup

```bash
# Copy template
cp .env.development.template .env.development

# Edit with your Stripe test keys
nano .env.development

# Verify by running:
python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.development'); print('STRIPE_SECRET_KEY:', os.getenv('STRIPE_SECRET_KEY')[:20] + '...')"
```

### 2. Backend Production Setup

```bash
# Copy template
cp .env.production.template .env.production

# Edit with your Stripe LIVE keys
nano .env.production

# Use environment variables in deployment:
# export $(cat .env.production | xargs)
```

### 3. Frontend Development Setup

```bash
# Copy template in frontend directory
cp .env.local.template .env.local

# Edit with your Stripe public key
nano .env.local

# Verify by starting dev server:
npm run dev
```

### 4. Docker Compose Setup

```bash
# Copy to root directory
cp .env.docker.template .env

# Update with your configuration
nano .env

# Run services:
docker-compose up -d
```

## Important Security Notes

⚠️ **NEVER commit `.env` files to Git**

Add to `.gitignore`:
```
.env
.env.local
.env.production
.env.development
.env.*.local
```

✅ **Safe to commit:**
- `.env.template` - Template with placeholder values
- `.env.example` - Example configuration

## Getting Stripe Keys

### Development (Test Mode)

1. Go to https://dashboard.stripe.com/test/apikeys
2. Click "Reveal test key"
3. Copy `Secret key` (starts with `sk_test_`)
4. Copy `Publishable key` (starts with `pk_test_`)
5. Create webhook: https://dashboard.stripe.com/test/webhooks
6. Add endpoint: `http://localhost:8000/webhooks/stripe` or use Stripe CLI

### Production (Live Mode)

1. Activate live mode: https://dashboard.stripe.com/settings/apikeys
2. Go to https://dashboard.stripe.com/apikeys
3. Copy `Secret key` (starts with `sk_live_`)
4. Copy `Publishable key` (starts with `pk_live_`)
5. Create webhook: https://dashboard.stripe.com/webhooks
6. Add endpoint: `https://api.omnidev.ai/webhooks/stripe`
7. Copy `Signing secret` (starts with `whsec_`)

## Webhook Configuration

### Development with Stripe CLI

```bash
# Install Stripe CLI
curl https://files.stripe.com/stripe-cli/install.sh -o install.sh
bash install.sh

# Authenticate
stripe login

# Forward webhook events
stripe listen --forward-to localhost:8000/webhooks/stripe

# Your webhook signing secret will be displayed:
# > Ready! Your webhook signing secret is: whsec_test_xxxxx
```

### Production

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Enter URL: `https://api.omnidev.ai/webhooks/stripe`
4. Select events to listen for (all by default)
5. Copy signing secret to `.env.production`

## Verification

### Backend

```bash
# Verify database connection
python -c "from app.database import SessionLocal; db = SessionLocal(); print('✅ DB connected')"

# Verify Stripe API key
python -c "import stripe; stripe.api_key = 'sk_test_...'; print(stripe.Account.retrieve())"

# Verify payment models
python -c "from app.models.payment_models import *; print('✅ Models imported')"
```

### Frontend

```bash
# Verify Stripe public key is loaded
npm run dev
# Check browser console: window.NEXT_PUBLIC_STRIPE_PUBLIC_KEY should be defined
```

## Troubleshooting

**Issue:** "Invalid API key"
- Solution: Verify key format and that test/live keys are in correct environment

**Issue:** "Webhook signature verification failed"
- Solution: Ensure webhook secret is correct and formatted as `whsec_...`

**Issue:** ".env not loaded"
- Solution: For Python, use `python-dotenv`: `from dotenv import load_dotenv; load_dotenv()`
- For Node.js, keys starting with `NEXT_PUBLIC_` are automatically available

## Next Steps

1. Configure environment variables for your environment
2. Run database migration: `alembic upgrade head`
3. Initialize pricing plans
4. Test with Stripe test cards
5. Deploy to production with live keys
