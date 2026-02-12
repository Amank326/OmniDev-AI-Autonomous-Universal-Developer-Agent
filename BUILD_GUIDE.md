# OmniDev AI - Full-Stack Platform Build Guide

Complete setup and deployment guide for the OmniDev AI full-stack platform.

## 📋 Project Structure

```
omnidev-ai/
├── backend/           # FastAPI Python backend
├── frontend/          # Next.js web application
├── mobile/            # React Native mobile app
├── docker/            # Docker configuration
└── docs/              # Documentation
```

## 🚀 Quick Start (5 minutes)

### 1. Backend (Already Running ✅)

```bash
# Status: All 8 services running in Docker
docker ps --format "table {{.Names}}\t{{.Status}}"
```

**Services Running:**
- ✅ Backend API (port 8000)
- ✅ PostgreSQL Database (port 5432)
- ✅ Redis Cache (port 6379)
- ✅ Prometheus Metrics (port 9090)
- ✅ Grafana Dashboard (port 3000)
- ✅ Nginx Reverse Proxy (ports 80/443)
- ✅ Celery Worker
- ✅ Celery Beat Scheduler

### 2. Frontend Setup (10 minutes)

```bash
cd frontend
npm install
npm run dev
```

**Access:** http://localhost:3000

**Default Credentials:**
```
Email: demo@omnidev.ai
Password: demo123
```

### 3. Mobile Setup (15 minutes)

```bash
cd mobile
npm install
npm start

# iOS Simulator
npm run ios

# Android Emulator
npm run android

# Or use Expo Go app (scan QR code)
```

## 📦 Full Installation Guide

### Prerequisites

- Node.js 18+
- npm or yarn
- Docker & Docker Compose (backend already running)
- Git
- macOS/Linux/Windows WSL2

### Step 1: Clone Repository

```bash
cd c:\Users\amank\OneDrive\Desktop\omnidev-ai
```

### Step 2: Backend Verification

```bash
# Check all services
docker-compose -f docker/docker-compose.yml ps

# View backend logs
docker-compose -f docker/docker-compose.yml logs backend -f

# Test API health
curl http://localhost:8000/health
```

### Step 3: Frontend Installation

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_APP_NAME=OmniDev AI
EOF

# Start development server
npm run dev

# Build for production
npm run build
npm run start
```

**Access Points:**
- Development: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Step 4: Mobile Installation

```bash
cd mobile

# Install dependencies
npm install

# Start Expo server
npm start

# Option 1: Use Expo Go App
# Scan QR code with Expo Go app on your phone

# Option 2: iOS Simulator
npm run ios

# Option 3: Android Emulator
npm run android

# Option 4: Web (testing)
npm run web
```

### Step 5: Database Setup

The database is already initialized with Alembic migrations:

```bash
# View migrations
docker exec omnidev-backend ls /app/app/migrations/versions/

# Run migrations manually
docker exec omnidev-backend alembic upgrade head

# Rollback (if needed)
docker exec omnidev-backend alembic downgrade -1
```

## 🔧 Configuration

### Backend Environment Variables

Located in `.env` (created from `.env.template`):

```bash
# Database
DATABASE_URL=postgresql://omnidev_user:secure_password_change_me@postgres:5432/omnidev_db

# Cache
REDIS_URL=redis://:redis_password_change_me@redis:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# AI Models
OPENAI_API_KEY=your_key_here

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Frontend Environment Variables

Located in `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_APP_NAME=OmniDev AI
```

### Mobile Environment Variables

Update in `mobile/App.tsx`:

```bash
const API_URL = 'http://localhost:8000';
```

## 📊 Monitoring & Debugging

### Real-time Logs

```bash
# Backend logs
docker-compose -f docker/docker-compose.yml logs -f backend

# Database logs
docker-compose -f docker/docker-compose.yml logs -f postgres

# Celery worker logs
docker-compose -f docker/docker-compose.yml logs -f celery-worker
```

### Access Monitoring Dashboards

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (admin/admin)
- **API Docs:** http://localhost:8000/docs
- **Backend Status:** http://localhost:8000/health

### Database Access

```bash
# Connect to PostgreSQL
psql -h localhost -U omnidev_user -d omnidev_db

# Redis CLI
redis-cli -h localhost -p 6379 -a redis_password_change_me

# Common commands
SELECT 0;          # Select database
KEYS *;            # List all keys
GET key_name;      # Get value
```

## 🌐 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/logout` - User logout

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Tasks
- `GET /api/tasks` - List tasks
- `POST /api/tasks` - Create task
- `GET /api/tasks/{id}` - Get task
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task

### Agents
- `GET /api/agents` - List agents
- `GET /api/agents/{id}` - Get agent
- `POST /api/agents/{id}/execute` - Execute agent

### WebSocket
- `WS /ws/projects/{project_id}` - Project updates
- `WS /ws/tasks/{task_id}` - Task updates
- `WS /ws/agents/{agent_id}` - Agent execution

Full API documentation: http://localhost:8000/docs

## 🚀 Deployment

### Docker Build & Push

```bash
# Build image
docker build -t omnidev-ai:latest -f backend/Dockerfile ./backend

# Tag for registry
docker tag omnidev-ai:latest your_registry/omnidev-ai:latest

# Push to registry
docker push your_registry/omnidev-ai:latest
```

### Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace omnidev

# Deploy backend
kubectl -n omnidev apply -f k8s/backend-deployment.yaml

# Deploy frontend
kubectl -n omnidev apply -f k8s/frontend-deployment.yaml

# Check status
kubectl -n omnidev get pods
```

### Cloud Deployment

**Vercel (Frontend)**
```bash
vercel --prod
```

**Heroku (Backend)**
```bash
heroku create omnidev-api
heroku config:set DATABASE_URL=your_postgres_url
git push heroku main
```

**AWS ECS**
```bash
aws ecs create-service --cluster omnidev --service-name backend ...
```

## 🧪 Testing

### Frontend Tests

```bash
cd frontend
npm run test
npm run test:coverage
```

### Backend Tests

```bash
cd backend
pytest tests/
pytest tests/ --cov=app
```

### API Integration Tests

```bash
cd backend
pytest tests/integration/
```

### Load Testing

```bash
# Using Locust
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## 📈 Performance Optimization

### Frontend
- Enable code splitting
- Image optimization with Next.js Image
- Static site generation where possible
- Caching strategies

### Backend
- Database connection pooling
- Redis caching for queries
- API rate limiting
- Gzip compression

### Database
- Index optimization
- Query optimization
- Connection pooling

### Infrastructure
- Load balancing (Nginx)
- Auto-scaling (Kubernetes)
- CDN for static assets
- DNS caching

## 🔐 Security Checklist

- [ ] Change default passwords
- [ ] Enable HTTPS/TLS
- [ ] Set up API rate limiting
- [ ] Configure CORS properly
- [ ] Enable database encryption
- [ ] Set up SSH keys
- [ ] Enable MFA for admin
- [ ] Regular security audits
- [ ] Keep dependencies updated
- [ ] Set up DDoS protection

## 🐛 Troubleshooting

### Backend Issues

```bash
# Database connection
docker exec omnidev-backend ping postgres

# Redis connection
docker exec omnidev-redis redis-cli ping

# API health
curl -v http://localhost:8000/health
```

### Frontend Issues

```bash
# Clear cache
rm -rf .next node_modules package-lock.json
npm install

# Check API connection
curl http://localhost:8000/api/projects
```

### Database Issues

```bash
# Restart database
docker-compose -f docker/docker-compose.yml restart postgres

# Check database status
docker exec omnidev-postgres pg_isready

# Reset database (⚠️ WARNING: Deletes data)
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up postgres
```

## 📚 Additional Resources

- **Backend Docs:** [backend/README.md](backend/README.md)
- **Frontend Docs:** [frontend/README.md](frontend/README.md)
- **Mobile Docs:** [mobile/README.md](mobile/README.md)
- **API Documentation:** http://localhost:8000/docs
- **Deployment Guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## 🎯 Next Steps

1. ✅ Backend running - Complete
2. 🔄 **Frontend setup** - Run `cd frontend && npm install`
3. 🔄 **Mobile setup** - Run `cd mobile && npm install`
4. 🔄 **Feature development** - Start building features
5. 🔄 **Testing & QA** - Run test suites
6. 🔄 **Deployment** - Deploy to production

## 💬 Support

For issues or questions:
1. Check troubleshooting section
2. Review API docs at http://localhost:8000/docs
3. Check backend logs: `docker-compose logs backend`
4. Check frontend console: Browser DevTools (F12)

---

**Status:** ✅ Full-Stack Platform Ready for Development

**Last Updated:** February 6, 2026
