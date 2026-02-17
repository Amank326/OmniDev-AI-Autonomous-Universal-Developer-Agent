# ============================================================
# OmniDev AI — DEPLOYMENT GUIDE
# ============================================================
# This project supports 4 deployment platforms:
# 1. Vercel (Frontend) + Railway (Backend)
# 2. Docker Compose (VPS / Self-hosted)
# 3. Azure Container Apps
# 4. Render
# ============================================================

## Prerequisites (All Platforms)

- Git repository pushed to GitHub
- Domain name (optional, recommended for production)
- Stripe API keys (for payment features)
- SMTP credentials (for email notifications)

---

## Option 1: Vercel + Railway (Recommended for Quick Start)

### Frontend → Vercel

1. **Connect to Vercel:**
   ```bash
   cd frontend
   npx vercel
   ```

2. **Set environment variables in Vercel dashboard:**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   NEXT_PUBLIC_WS_URL=wss://your-backend.railway.app/ws
   NEXT_PUBLIC_APP_NAME=OmniDev AI
   ```

3. **Deploy:**
   ```bash
   npx vercel --prod
   ```

### Backend → Railway

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Create project with services:**
   ```bash
   cd backend
   railway init
   railway add --plugin postgresql
   railway add --plugin redis
   ```

3. **Set environment variables:**
   ```bash
   railway variables set SECRET_KEY=$(openssl rand -hex 32)
   railway variables set ENVIRONMENT=production
   railway variables set CORS_ORIGINS=https://your-app.vercel.app
   ```
   > DATABASE_URL and REDIS_URL are auto-injected by Railway plugins.

4. **Deploy:**
   ```bash
   railway up
   ```

5. **Update Vercel env** with the Railway backend URL:
   ```
   NEXT_PUBLIC_API_URL=https://omnidev-backend.up.railway.app
   ```

---

## Option 2: Docker Compose (VPS / Self-Hosted)

### Requirements
- VPS with Docker & Docker Compose installed (Ubuntu 22.04+ recommended)
- Minimum 2GB RAM, 2 vCPUs

### Setup

1. **Clone and configure:**
   ```bash
   git clone https://github.com/Amank326/OmniDev-AI-Autonomous-Universal-Developer-Agent.git
   cd OmniDev-AI-Autonomous-Universal-Developer-Agent
   cp backend/.env.production .env
   ```

2. **Edit `.env` — fill in required values:**
   ```bash
   nano .env
   ```
   Required:
   - `POSTGRES_PASSWORD` — strong database password
   - `SECRET_KEY` — generated with `openssl rand -hex 32`
   - `REDIS_PASSWORD` — Redis auth password
   - `API_URL` — your domain (e.g., `https://api.yourdomain.com`)
   - `CORS_ORIGINS` — frontend domain

3. **Deploy:**
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

4. **Run database migrations:**
   ```bash
   docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```

5. **Setup SSL (recommended):**
   ```bash
   # Install certbot
   sudo apt install certbot
   sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com

   # Copy certs
   mkdir -p ssl
   cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
   cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/

   # Uncomment SSL volumes in docker-compose.prod.yml
   # Uncomment SSL server block in nginx.conf
   docker compose -f docker-compose.prod.yml restart nginx
   ```

6. **Monitor:**
   ```bash
   docker compose -f docker-compose.prod.yml logs -f
   docker compose -f docker-compose.prod.yml ps
   ```

### Useful Commands
```bash
# Stop all services
docker compose -f docker-compose.prod.yml down

# Restart a specific service
docker compose -f docker-compose.prod.yml restart backend

# View logs
docker compose -f docker-compose.prod.yml logs -f backend

# Scale workers
docker compose -f docker-compose.prod.yml up -d --scale celery-worker=3

# Backup database
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U omnidev omnidev > backup.sql
```

---

## Option 3: Azure Container Apps

### Requirements
- Azure CLI installed (`az`)
- Azure subscription
- OpenSSL (for generating secrets)

### Deploy

1. **Login to Azure:**
   ```bash
   az login
   ```

2. **Run deployment script:**
   ```bash
   chmod +x azure/deploy.sh
   bash azure/deploy.sh
   ```

   This script automatically:
   - Creates a Resource Group
   - Creates Azure Container Registry (ACR)
   - Builds & pushes Docker images
   - Creates PostgreSQL Flexible Server
   - Creates Azure Cache for Redis
   - Deploys Backend, Frontend, and Celery Worker as Container Apps
   - Outputs all URLs and credentials

3. **Post-deploy — update CORS:**
   ```bash
   az containerapp update \
     --name omnidev-backend \
     --resource-group omnidev-ai-rg \
     --set-env-vars "CORS_ORIGINS=https://<frontend-fqdn>"
   ```

4. **Custom domain (optional):**
   ```bash
   az containerapp hostname add \
     --name omnidev-frontend \
     --resource-group omnidev-ai-rg \
     --hostname www.yourdomain.com
   ```

### Estimated Azure Cost
| Service | SKU | ~Monthly Cost |
|---------|-----|--------------|
| Container Apps (3) | Consumption | $15-40 |
| PostgreSQL Flexible | B1ms | ~$13 |
| Redis Cache | Basic C0 | ~$16 |
| Container Registry | Basic | ~$5 |
| **Total** | | **~$50-75/mo** |

---

## Option 4: Render

### Setup

1. **Connect GitHub repo** to [Render Dashboard](https://dashboard.render.com)

2. **Create Blueprint:**
   - Go to Dashboard → New → Blueprint
   - Select your repo
   - Render auto-detects `render.yaml` and creates all services

3. **Set secret env vars** in Render dashboard:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_WEBHOOK_SECRET`
   - `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`

4. **Deploy** — Render auto-deploys on push to `main`

### Render Services Created
| Service | Type | Plan |
|---------|------|------|
| omnidev-backend | Web Service | Starter ($7/mo) |
| omnidev-frontend | Web Service | Starter ($7/mo) |
| omnidev-worker | Background Worker | Starter ($7/mo) |
| omnidev-redis | Redis | Starter ($0) |
| omnidev-db | PostgreSQL | Starter ($0) |
| **Total** | | **~$21/mo** |

---

## CI/CD Pipeline

GitHub Actions workflow at `.github/workflows/deploy.yml` handles:

1. **On every push/PR:**
   - Run backend tests (Python + PostgreSQL + Redis)
   - Build frontend (Next.js)

2. **On push to `main`:**
   - Build & push Docker images to GitHub Container Registry
   - Trigger Render deploy (via webhook)
   - Deploy to Railway (via CLI)
   - Deploy to Vercel (via action)

### Setup GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Required For | Description |
|--------|-------------|-------------|
| `RAILWAY_TOKEN` | Railway | From `railway login --browserless` |
| `VERCEL_TOKEN` | Vercel | From Vercel dashboard → Settings → Tokens |
| `VERCEL_ORG_ID` | Vercel | From `.vercel/project.json` after `vercel link` |
| `VERCEL_PROJECT_ID` | Vercel | From `.vercel/project.json` after `vercel link` |
| `RENDER_DEPLOY_HOOK_URL` | Render | From Render dashboard → Service → Settings → Deploy Hook |

### Setup GitHub Variables

Go to **Settings → Secrets and variables → Actions → Variables**:

| Variable | Value |
|----------|-------|
| `API_URL` | Your backend URL (e.g., `https://api.omnidev.ai`) |
| `WS_URL` | Your WebSocket URL (e.g., `wss://api.omnidev.ai/ws`) |

---

## Environment Variables Reference

### Backend (Required)
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | — |
| `SECRET_KEY` | JWT signing key (min 32 chars) | — |
| `ENVIRONMENT` | `production` | `development` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `http://localhost:3000` |

### Backend (Optional)
| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `STRIPE_SECRET_KEY` | Stripe payments | — |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhooks | — |
| `SMTP_HOST` | Email server | — |
| `SMTP_PORT` | Email port | `587` |
| `SMTP_USER` | Email username | — |
| `SMTP_PASSWORD` | Email password | — |

### Frontend (Required)
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL |
| `NEXT_PUBLIC_APP_NAME` | App display name |
