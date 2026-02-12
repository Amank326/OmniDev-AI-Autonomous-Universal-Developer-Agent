# OmniDev-AI Platform Deployment Guide

**Phase 40: Final Integration & Platform Stabilization**

## Table of Contents
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Local Development Setup](#local-development-setup)
5. [Production Deployment](#production-deployment)
6. [Configuration Management](#configuration-management)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Disaster Recovery](#backup--disaster-recovery)
9. [Troubleshooting](#troubleshooting)
10. [Support & Maintenance](#support--maintenance)

---

## Introduction

This guide provides comprehensive instructions for deploying the OmniDev-AI platform (Phases 1-40, 113,550+ LOC) across development, staging, and production environments.

**Platform Scope:**
- 40 complete phases with 113,550+ lines of code
- 47 integrated services
- Multi-layer caching (L1 memory, L2 Redis, L3 database)
- Enterprise-grade security (AES-256 encryption, JWT tokens, API key management)
- Real-time performance optimization and analytics
- Distributed deployment support

---

## System Requirements

### Hardware Requirements

**Development Environment:**
- CPU: 4+ cores (Intel i5/AMD Ryzen 5 or equivalent)
- RAM: 8GB minimum (16GB recommended)
- Storage: 50GB free space
- Network: 100Mbps connection

**Staging Environment:**
- CPU: 8+ cores
- RAM: 32GB
- Storage: 200GB SSD
- Network: 1Gbps connection

**Production Environment (per container/VM):**
- CPU: 16+ cores (or 2x 8-core for HA)
- RAM: 64GB
- Storage: 500GB+ SSD (with replication)
- Network: 10Gbps or higher
- Load Balancer: Hardware or software LB for HA

### Software Requirements

**Backend:**
- Python 3.10+
- Node.js 18+ (for frontend build)
- Docker 20.10+
- Docker Compose 2.0+ (for local development)
- PostgreSQL 13+ or compatible database
- Redis 6.0+ (for distributed caching)
- Git 2.30+

**Frontend:**
- Node.js 18+
- npm 8+ or yarn 3+
- Modern browser (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)

**Observability:**
- Prometheus 2.30+ (metrics)
- ELK Stack or Datadog (logging/analytics)
- Grafana 8.0+ (visualization)

---

## Pre-Deployment Checklist

### Code Quality
- [ ] All 40 phases complete and tested
- [ ] 100% build success rate (0 errors)
- [ ] Test coverage >= 87.5%
- [ ] No critical security vulnerabilities
- [ ] Code review completed for all changes

### Integration Validation
- [ ] Service registry initialized with all 47 services
- [ ] Dependency graph validated (no circular dependencies)
- [ ] Version compatibility verified
- [ ] Cross-phase integration tests passing
- [ ] API endpoint tests passing (100%)

### Security
- [ ] Encryption keys rotated
- [ ] API keys updated
- [ ] CORS policies configured
- [ ] Rate limiting rules configured
- [ ] Audit logging enabled
- [ ] Security policy audit completed

### Infrastructure
- [ ] Database migrations completed
- [ ] Redis cluster configured (if using distributed caching)
- [ ] Load balancer configured
- [ ] SSL/TLS certificates valid
- [ ] Monitoring and alerting configured
- [ ] Backup systems tested

### Documentation
- [ ] Deployment guide reviewed
- [ ] Configuration guide prepared
- [ ] Runbook created for common issues
- [ ] API documentation generated
- [ ] Architecture diagram updated

---

## Local Development Setup

### 1. Clone and Setup Repository

```bash
# Clone the repository
git clone <repository-url>
cd omnidev-ai

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure Local Environment

Create `.env.local` in project root:

```bash
# Backend Configuration
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here-min-32-chars
DATABASE_URL=postgresql://user:password@localhost:5432/omnidev_dev
REDIS_URL=redis://localhost:6379/0

# Security
MASTER_KEY=your-master-encryption-key
JWT_SECRET_KEY=your-jwt-secret-key
API_KEY_SECRET=your-api-key-secret

# Frontend Configuration
REACT_APP_API_BASE_URL=http://localhost:5000
REACT_APP_WS_URL=ws://localhost:5000

# Monitoring
LOG_LEVEL=INFO
METRICS_ENABLED=true
TRACES_ENABLED=false

# Phase Feature Flags
ENABLE_PHASE_39_SECURITY=true
ENABLE_PHASE_40_INTEGRATION=true
```

### 3. Initialize Database

```bash
# Create database (if using PostgreSQL)
createdb omnidev_dev

# Run migrations
flask db upgrade

# Seed initial data (optional)
python backend/scripts/seed_data.py
```

### 4. Start Local Development Services

**Terminal 1 - Backend:**
```bash
cd backend
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

**Terminal 3 - Redis (if using Docker):**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Terminal 4 - PostgreSQL (if using Docker):**
```bash
docker run -d \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=omnidev_dev \
  -p 5432:5432 \
  postgres:14-alpine
```

### 5. Verify Local Setup

```bash
# Test backend health
curl http://localhost:5000/api/v1/health

# Test frontend
open http://localhost:3000

# Check service registration
curl http://localhost:5000/api/v1/integration/services

# Run tests
pytest backend/app/tests/ -v
npm test --prefix frontend
```

---

## Production Deployment

### Docker Deployment

**1. Build Docker Images**

```bash
# Backend image
docker build -f backend/docker/Dockerfile -t omnidev-backend:1.0.0 .

# Frontend image
docker build -f frontend/Dockerfile -t omnidev-frontend:1.0.0 .

# Tag for registry
docker tag omnidev-backend:1.0.0 registry.example.com/omnidev-backend:1.0.0
docker tag omnidev-frontend:1.0.0 registry.example.com/omnidev-frontend:1.0.0

# Push to registry
docker push registry.example.com/omnidev-backend:1.0.0
docker push registry.example.com/omnidev-frontend:1.0.0
```

**2. Docker Compose for Multi-Container Deployment**

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: omnidev
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: omnidev_prod
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    image: registry.example.com/omnidev-backend:1.0.0
    environment:
      FLASK_ENV: production
      DATABASE_URL: postgresql://omnidev:${DB_PASSWORD}@postgres:5432/omnidev_prod
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "5000:5000"
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: registry.example.com/omnidev-frontend:1.0.0
    environment:
      REACT_APP_API_BASE_URL: https://api.example.com
      REACT_APP_WS_URL: wss://api.example.com
    ports:
      - "3000:3000"
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:
```

**Deploy:**
```bash
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
docker-compose logs -f
docker-compose ps
```

### Kubernetes Deployment

**1. Create Kubernetes Manifests**

Backend Deployment (`k8s/backend-deployment.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: omnidev-backend
  labels:
    app: omnidev-backend
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: omnidev-backend
  template:
    metadata:
      labels:
        app: omnidev-backend
    spec:
      containers:
      - name: backend
        image: registry.example.com/omnidev-backend:1.0.0
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: omnidev-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**2. Deploy to Kubernetes**

```bash
# Create secrets
kubectl create secret generic omnidev-secrets \
  --from-literal=database-url=postgresql://... \
  --from-literal=secret-key=...

# Deploy
kubectl apply -f k8s/

# Verify deployment
kubectl get pods
kubectl get services
kubectl logs -l app=omnidev-backend
```

---

## Configuration Management

### Environment Variables

Create `.env.prod` for production:

```bash
# Flask
FLASK_ENV=production
SECRET_KEY=<production-secret-key>

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis (Distributed Caching)
REDIS_URL=redis://host:6379/0
REDIS_CLUSTER_ENABLED=true
CACHE_TTL_SECONDS=3600

# Security
MASTER_KEY=<encryption-master-key>
JWT_SECRET_KEY=<jwt-secret>
JWT_EXPIRY_HOURS=24
PASSWORD_MIN_LENGTH=12
AUDIT_RETENTION_DAYS=365

# Performance
ENABLE_QUERY_CACHE=true
CACHE_LEVEL=L2
COMPRESSION_ENABLED=true
CONNECTION_POOL_SIZE=50

# API
API_RATE_LIMIT=1000
API_TIMEOUT_SECONDS=30
MAX_REQUEST_SIZE_MB=100

# Monitoring
LOG_LEVEL=INFO
METRICS_ENABLED=true
PROMETHEUS_PORT=9090
DATADOG_ENABLED=false
DATADOG_API_KEY=<if-using-datadog>

# Features
ENABLE_PHASE_39_SECURITY=true
ENABLE_PHASE_40_INTEGRATION=true
```

### Service Configuration

Create `backend/config/production.json`:

```json
{
  "services": {
    "cache_manager": {
      "enabled": true,
      "max_memory_mb": 4096,
      "eviction_policy": "lru",
      "enable_redis": true,
      "redis_url": "redis://cluster:6379/0"
    },
    "security_service": {
      "enabled": true,
      "password_policy": {
        "min_length": 12,
        "require_uppercase": true,
        "require_digits": true,
        "require_special": true
      },
      "token_expiry_hours": 24,
      "audit_retention_days": 365
    },
    "performance_optimizer": {
      "enabled": true,
      "slow_query_threshold_ms": 100,
      "bottleneck_detection": true
    }
  },
  "health_check": {
    "interval_seconds": 60,
    "startup_timeout_seconds": 30,
    "shutdown_timeout_seconds": 10
  }
}
```

---

## Monitoring & Logging

### Prometheus Metrics

Configure Prometheus scrape config:

```yaml
scrape_configs:
  - job_name: 'omnidev-backend'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s
```

### ELK Stack Logging

Configure Filebeat to ship logs:

```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/omnidev/*.log

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

### Grafana Dashboards

Import dashboard templates:
```bash
# Import from JSON files
grafana-cli admin import-dashboard backend/monitoring/grafana-dashboards/
```

### Health Check Endpoints

```bash
# Service registry status
GET /api/v1/integration/services

# Dependency validation
GET /api/v1/integration/validate

# Metrics
GET /api/v1/metrics/health

# Extended health report
GET /api/v1/integration/health-report
```

---

## Backup & Disaster Recovery

### Database Backups

```bash
# Daily backup (add to crontab)
0 2 * * * pg_dump -Fc omnidev_prod > /backups/omnidev_$(date +\%Y\%m\%d).dump

# Restore from backup
pg_restore -d omnidev_prod /backups/omnidev_20260209.dump
```

### Redis Data Persistence

Configure Redis RDB snapshots:

```conf
# /etc/redis/redis.conf
save 900 1
save 300 10
save 60 10000
appendonly yes
```

### Disaster Recovery Plan

**Recovery Time Objective (RTO):** 4 hours
**Recovery Point Objective (RPO):** 1 hour

1. **Detect incident** (within 5 min)
2. **Activate standby** (within 15 min)
3. **Restore data** (within 1 hour)
4. **Validate system** (within 2 hours)
5. **Cutover to primary** (within 4 hours)

---

## Troubleshooting

### Common Issues

**Issue: Service health checks failing**
```bash
# Check service logs
docker logs omnidev-backend
kubectl logs -l app=omnidev-backend

# Validate configuration
curl http://localhost:5000/api/v1/integration/services

# Check dependencies
curl http://localhost:5000/api/v1/integration/validate
```

**Issue: High memory usage**
```bash
# Check cache statistics
curl http://localhost:5000/api/v1/cache/stats

# Adjust cache configuration
# Reduce max_memory_mb or adjust eviction_policy
```

**Issue: Database connection errors**
```bash
# Check connection pool
psql postgresql://user:pass@host:5432/db -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Increase pool size in configuration
```

**Issue: Redis connection issues**
```bash
# Check Redis connectivity
redis-cli -h localhost PING

# Verify Redis memory
redis-cli -h localhost INFO memory
```

---

## Support & Maintenance

### Regular Maintenance Tasks

**Daily:**
- Monitor health dashboards
- Review error logs
- Check system metrics

**Weekly:**
- Review slow query logs
- Analyze performance trends
- Update security patches

**Monthly:**
- Rotate encryption keys
- Audit access logs
- Review backup integrity
- Update dependencies

**Quarterly:**
- Security audit
- Performance optimization review
- Capacity planning
- Disaster recovery drill

### Contact & Escalation

**Support Contacts:**
- Platform Team: platform@example.com
- On-call Engineer: See PagerDuty rotation
- Security Issues: security@example.com

**Documentation:**
- API Documentation: `/api/docs`
- Architecture: `./docs/ARCHITECTURE.md`
- Runbook: `./docs/RUNBOOK.md`

---

**Last Updated:** 2026-02-09
**Maintained by:** OmniDev-AI Platform Team
**Version:** 1.0.0 (Phase 40)
