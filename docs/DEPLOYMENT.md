# Deployment Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 1.29+
- Kubernetes 1.24+ (for K8s deployment)
- kubectl configured
- Domain name (for production)
- SSL certificate (for production)

## Local Development Deployment

### Using Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/Amank326/OmniDev-AI-Autonomous-Universal-Developer-Agent.git
cd OmniDev-AI-Autonomous-Universal-Developer-Agent
```

2. Set up environment variables:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

3. Start all services:
```bash
docker-compose up -d
```

4. Check service status:
```bash
docker-compose ps
```

5. View logs:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

6. Stop services:
```bash
docker-compose down
```

## Production Deployment

### Environment Setup

1. Set production environment variables:
```bash
# backend/.env
ENVIRONMENT=production
SECRET_KEY=<strong-random-secret-key>
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
REDIS_URL=redis://redis-host:6379/0

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Sentry (optional)
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

### Docker Production Build

1. Build production images:
```bash
docker-compose -f docker-compose.prod.yml build
```

2. Run production containers:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

1. Create namespace:
```bash
kubectl create namespace omnidev
```

2. Create secrets:
```bash
kubectl create secret generic omnidev-secrets \
  --from-literal=database-url=<database-url> \
  --from-literal=secret-key=<secret-key> \
  --from-literal=stripe-secret=<stripe-secret> \
  -n omnidev
```

3. Apply configurations:
```bash
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml
```

4. Check deployment status:
```bash
kubectl get pods -n omnidev
kubectl get services -n omnidev
kubectl get ingress -n omnidev
```

### Database Migrations

Run migrations after deployment:

```bash
# For Docker
docker-compose exec backend alembic upgrade head

# For Kubernetes
kubectl exec -it <backend-pod-name> -n omnidev -- alembic upgrade head
```

### SSL/TLS Configuration

1. Install cert-manager:
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml
```

2. Create ClusterIssuer for Let's Encrypt:
```bash
kubectl apply -f k8s/cert-issuer.yaml
```

3. Update Ingress with TLS:
```yaml
spec:
  tls:
  - hosts:
    - omnidev.example.com
    secretName: omnidev-tls
```

## Monitoring & Logging

### Prometheus & Grafana

1. Install Prometheus:
```bash
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring
```

2. Access Grafana:
```bash
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
```

### Application Logs

View application logs:
```bash
# Backend logs
kubectl logs -f deployment/backend -n omnidev

# Frontend logs
kubectl logs -f deployment/frontend -n omnidev

# Database logs
kubectl logs -f statefulset/postgres -n omnidev
```

## Backup & Recovery

### Database Backup

```bash
# Create backup
kubectl exec -it postgres-0 -n omnidev -- pg_dump -U omnidev omnidev > backup.sql

# Restore backup
kubectl exec -i postgres-0 -n omnidev -- psql -U omnidev omnidev < backup.sql
```

### Automated Backups

Use CronJob for automated backups:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: omnidev
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15-alpine
            command: ["/bin/sh", "-c"]
            args:
            - pg_dump -h postgres -U omnidev omnidev | gzip > /backups/backup-$(date +%Y%m%d).sql.gz
            volumeMounts:
            - name: backups
              mountPath: /backups
          volumes:
          - name: backups
            persistentVolumeClaim:
              claimName: backup-pvc
```

## Scaling

### Horizontal Pod Autoscaling

```bash
kubectl autoscale deployment backend --cpu-percent=70 --min=2 --max=10 -n omnidev
kubectl autoscale deployment frontend --cpu-percent=70 --min=2 --max=10 -n omnidev
```

### Manual Scaling

```bash
kubectl scale deployment backend --replicas=5 -n omnidev
kubectl scale deployment frontend --replicas=3 -n omnidev
```

## Troubleshooting

### Common Issues

1. **Pod not starting**
```bash
kubectl describe pod <pod-name> -n omnidev
kubectl logs <pod-name> -n omnidev
```

2. **Database connection issues**
```bash
# Check database pod
kubectl get pods -n omnidev | grep postgres
kubectl logs postgres-0 -n omnidev

# Test connection
kubectl exec -it backend-pod -n omnidev -- python -c "from app.core.database import engine; print('OK')"
```

3. **Ingress not working**
```bash
kubectl describe ingress omnidev-ingress -n omnidev
kubectl get events -n omnidev
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Check all endpoints
curl http://localhost:8000/api/v1/docs
```

## Rollback

If deployment fails, rollback to previous version:

```bash
# Kubernetes
kubectl rollout undo deployment/backend -n omnidev
kubectl rollout undo deployment/frontend -n omnidev

# Docker Compose
docker-compose down
git checkout <previous-commit>
docker-compose up -d
```

## Performance Optimization

1. **Enable Redis caching**
2. **Use CDN for static assets**
3. **Enable database connection pooling**
4. **Implement rate limiting**
5. **Use horizontal pod autoscaling**
6. **Enable gzip compression**
7. **Optimize database queries**
8. **Use read replicas for database**

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable SSL/TLS
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set up monitoring alerts
- [ ] Regular security updates
- [ ] Enable audit logging
- [ ] Use secrets management
- [ ] Configure CORS properly
