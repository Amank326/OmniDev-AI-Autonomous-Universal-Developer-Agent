# Phase 9 Quick Reference - DevOps & Deployment

## 🚀 Get Started in 5 Minutes

### Local Development
```bash
# 1. Clone and setup
git clone <repo>
cd omnidev-ai
cp .env.example .env

# 2. Start all services
docker-compose up -d

# 3. Verify health
curl http://localhost:8000/health
curl http://localhost:3000 # Grafana

# 4. View logs
docker-compose logs -f backend
```

### Deploy to Kubernetes
```bash
# 1. Create namespace and secrets
kubectl create namespace omnidev
kubectl create secret generic omnidev-secrets \
  --from-literal=database-url="postgresql://..." \
  -n omnidev

# 2. Deploy
kubectl apply -f k8s/deployment.yaml

# 3. Check status
kubectl get pods -n omnidev
kubectl logs -f deployment/omnidev-backend -n omnidev

# 4. Access service
kubectl port-forward svc/omnidev-backend 8000:8000 -n omnidev
```

---

## 📋 Essential Commands

### Docker
```bash
docker build -t omnidev/backend:latest backend/
docker-compose up -d
docker-compose logs -f <service>
docker-compose down
docker inspect <container> | grep -A 20 "Health"
```

### Kubernetes
```bash
kubectl apply -f k8s/deployment.yaml
kubectl get pods -n omnidev
kubectl logs pod/<name> -n omnidev
kubectl describe pod/<name> -n omnidev
kubectl port-forward pod/<name> 8000:8000
kubectl rollout status deployment/omnidev-backend -n omnidev
kubectl scale deployment omnidev-backend --replicas=5
```

### Health Checks
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
curl http://localhost:8000/health/metrics/basic
```

### Monitoring
```bash
# Grafana
http://localhost:3000

# Prometheus
http://localhost:9090

# Metrics query
curl http://localhost:9090/api/v1/query?query=up
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Pod stuck pending | Check node resources: `kubectl top nodes` |
| Database won't connect | Verify SECRET: `kubectl get secret omnidev-secrets -n omnidev` |
| High memory usage | `kubectl top pods -n omnidev`, scale replicas down |
| Build timeout | Increase timeout: `kubectl rollout status ... --timeout=10m` |
| Service not responding | Check health: `curl http://localhost:8000/health/detailed` |

---

## 📚 Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Basic health check |
| `GET /health/detailed` | All component status |
| `GET /health/readiness` | K8s readiness probe |
| `GET /health/liveness` | K8s liveness probe |
| `GET /health/startup` | K8s startup probe |
| `GET /health/metrics/basic` | System metrics |
| `POST /api/...` | Business logic endpoints |
| `GET /metrics` | Prometheus metrics |

---

## 🔐 Security Essentials

```bash
# Create secrets
kubectl create secret generic omnidev-secrets \
  --from-literal=database-url="..." \
  --from-literal=redis-password="..." \
  --from-literal=api-key="..." \
  -n omnidev

# Verify no secrets in git
git log -p | grep -i "password\|secret\|key"

# Scan image for vulnerabilities
docker scan omnidev/backend:latest
```

---

## 📊 Monitoring Queries

### Prometheus
```promql
# Request rate (requests/sec)
rate(http_requests_total[5m])

# Error rate (%)
rate(http_errors_total[5m]) / rate(http_requests_total[5m])

# Latency (p95)
histogram_quantile(0.95, http_request_duration_seconds)

# Database connections
pg_stat_activity_count

# Memory usage
process_resident_memory_bytes / 1024 / 1024
```

### Grafana
1. Open http://localhost:3000
2. Login: admin / admin
3. Import dashboards from Grafana.com or create custom

---

## 🔄 CI/CD Pipeline

**GitHub Actions Stages:**

1. **Test** (5min)
   - Linting, type checking, unit tests
   - Coverage >80% required

2. **Security** (3min)
   - Bandit code scan
   - Safety dependency check

3. **Build** (10min)
   - Docker multi-stage build
   - Push to ghcr.io

4. **Deploy Dev** (5min)
   - kubectl deploy to dev
   - Smoke tests

5. **Deploy Prod** (5min)
   - kubectl deploy to prod
   - Health checks
   - Slack notification

**Triggers:**
- Push to `main` or `develop`
- Pull requests on `main` or `develop`

---

## 📦 Service Overview

| Service | Port | Purpose |
|---------|------|---------|
| Backend | 8000 | FastAPI application |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache & Celery |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Dashboards |
| Nginx | 80/443 | Reverse proxy |

---

## 🎯 Scaling

### Horizontal Scaling
```bash
# Manual scale
kubectl scale deployment omnidev-backend --replicas=10 -n omnidev

# Auto-scale (already configured)
# 3-10 replicas based on CPU/Memory usage
```

### Database Scaling
- PostgreSQL: Read replicas for read scaling
- Redis: Cluster mode for distributed caching

---

## ⚡ Performance Tips

1. **Enable query caching** in Redis
2. **Use database indexes** (already configured)
3. **Monitor slow queries** in PostgreSQL
4. **Optimize Prometheus queries**
5. **Use connection pooling**
6. **Batch database operations**
7. **Cache API responses**

---

## 🔔 Alerting Rules

Example Prometheus alert rules:

```yaml
# High error rate
rate(http_errors_total[5m]) > 0.05

# High latency
histogram_quantile(0.95, http_request_duration_seconds) > 1

# Database down
pg_up == 0

# Redis down
redis_up == 0

# High memory usage
process_resident_memory_bytes / 1024 / 1024 > 1024
```

---

## 📞 Support

**Documentation:**
- [PHASE9_GUIDE.md](PHASE9_GUIDE.md) - Complete guide
- [PHASE9_COMPLETE.md](PHASE9_COMPLETE.md) - Phase summary
- API Docs: http://localhost:8000/docs

**Troubleshooting:**
1. Check health endpoints
2. Review logs: `docker-compose logs` or `kubectl logs`
3. Check metrics in Prometheus/Grafana
4. Read troubleshooting section in PHASE9_GUIDE.md

---

**Phase 9 Infrastructure Ready** ✅
