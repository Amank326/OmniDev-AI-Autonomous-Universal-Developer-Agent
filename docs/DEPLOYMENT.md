# Deployment Guide

## Local Development

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git
- Android Studio (optional)

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/omnidev-ai.git
cd omnidev-ai

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with Docker
docker-compose -f docker/docker-compose.yml up

# Backend will be available at http://localhost:8000
```

### Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# API documentation
http://localhost:8000/docs

# Android emulator connection
adb connect 192.168.1.x:5555  # Update with your IP
```

## Docker Deployment

### Build Images

```bash
# Build backend image
docker build -f backend/docker/Dockerfile -t omnidev-ai:latest .

# Run container
docker run -d -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/omnidev \
  --name omnidev-backend \
  omnidev-ai:latest
```

### Docker Compose Setup

```bash
# Start all services
docker-compose -f backend/docker/docker-compose.yml up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## Cloud Deployment

### AWS Deployment

#### Using Elastic Container Service (ECS)

```bash
# Create ECR repository
aws ecr create-repository --repository-name omnidev-ai

# Build and push image
docker build -t omnidev-ai:latest .
docker tag omnidev-ai:latest \
  <account-id>.dkr.ecr.<region>.amazonaws.com/omnidev-ai:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/omnidev-ai:latest

# Create ECS task definition (task-definition.json)
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster omnidev-cluster \
  --service-name omnidev-service \
  --task-definition omnidev-task \
  --desired-count 1
```

#### Using Elastic Beanstalk

```bash
# Create application
eb create omnidev-ai-env

# Deploy
eb deploy

# View logs
eb logs

# Configure environment
eb config
```

### Azure Deployment

#### Using Azure Container Instances

```bash
# Create container group
az container create \
  --resource-group myResourceGroup \
  --name omnidev-ai \
  --image omnidev-ai:latest \
  --port 8000 \
  --environment-variables \
    DATABASE_URL=postgresql://... \
    OPENAI_API_KEY=...
```

#### Using Azure App Service

```bash
# Create app service plan
az appservice plan create \
  --name omnidevplan \
  --resource-group myResourceGroup

# Create web app
az webapp create \
  --resource-group myResourceGroup \
  --plan omnidevplan \
  --name omnidev-ai

# Deploy from Docker
az webapp up --docker-custom-image-name omnidev-ai:latest
```

### GCP Deployment

#### Using Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/omnidev-ai

# Deploy to Cloud Run
gcloud run deploy omnidev-ai \
  --image gcr.io/PROJECT_ID/omnidev-ai \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --set-env-vars DATABASE_URL=postgresql://...
```

## Database Setup

### PostgreSQL

```bash
# Local installation
docker run --name omnidev-postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=omnidev \
  -p 5432:5432 \
  -d postgres:16

# Create tables
psql -U user -d omnidev < schema.sql

# Backup database
pg_dump -U user omnidev > backup.sql

# Restore database
psql -U user omnidev < backup.sql
```

### Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add users table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build and test
        run: |
          docker build -t omnidev-ai .
          docker run omnidev-ai pytest
      - name: Push to registry
        run: docker push omnidev-ai:latest
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - docker build -t omnidev-ai .

test:
  stage: test
  script:
    - docker run omnidev-ai pytest

deploy:
  stage: deploy
  script:
    - docker push omnidev-ai:latest
```

## Monitoring & Logging

### Docker Logs

```bash
# View real-time logs
docker logs -f omnidev-ai-backend

# Get last 100 lines
docker logs --tail 100 omnidev-ai-backend
```

### Application Logs

```python
# In FastAPI app
import logging

logger = logging.getLogger(__name__)
logger.info("Application started")
logger.error("An error occurred")
```

### Health Monitoring

```bash
# Check health endpoint
curl http://localhost:8000/health

# Continuous monitoring
watch -n 5 'curl http://localhost:8000/health'
```

## Performance Optimization

### Gunicorn Configuration

```bash
# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 \
  --worker-class uvicorn.workers.UvicornWorker \
  app.main:app
```

### Nginx Reverse Proxy

```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name omnidev.ai;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
    }
}
```

## SSL/TLS Configuration

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# Run with HTTPS
uvicorn app.main:app \
  --ssl-keyfile=key.pem \
  --ssl-certfile=cert.pem
```

## Environment Configuration

```bash
# .env file
DATABASE_URL=postgresql://user:password@localhost:5432/omnidev
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...
REDIS_URL=redis://localhost:6379
DEBUG=false
LOG_LEVEL=INFO
```

## Scaling

### Horizontal Scaling

```bash
# Run multiple instances
for i in {1..3}; do
  docker run -d -p 800$i:8000 \
    --name omnidev-backend-$i \
    omnidev-ai:latest
done
```

### Load Balancing

```bash
# Using HAProxy
global
    mode http
    timeout connect 5000

frontend web
    bind :80
    default_backend servers

backend servers
    server web1 localhost:8001
    server web2 localhost:8002
    server web3 localhost:8003
```

## Disaster Recovery

### Backup Strategy

```bash
# Daily backup
0 2 * * * pg_dump -U user omnidev > /backups/omnidev-$(date +\%Y\%m\%d).sql

# Upload to cloud
0 3 * * * aws s3 cp /backups/ s3://omnidev-backups/
```

### Failover Configuration

```bash
# PostgreSQL replication
# Configure standby servers
# Setup automatic failover
# Regular failover testing
```

## Troubleshooting

### Common Issues

```bash
# Check port availability
lsof -i :8000

# View container resources
docker stats

# Inspect container network
docker network inspect bridge
```

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG uvicorn app.main:app

# Interactive debugging
python -m pdb -c continue app/main.py
```

---

For more information, see `README.md` and `ARCHITECTURE.md`.
