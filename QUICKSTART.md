# Quick Start Guide

## 5-Minute Setup

### Step 1: Clone & Navigate
```bash
cd omnidev-ai
```

### Step 2: Start Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Backend runs at: **http://localhost:8000**

### Step 3: Test the API
```bash
# In another terminal
curl http://localhost:8000/health

# View API docs
http://localhost:8000/docs
```

### Step 4: Create First Project
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First AI Project",
    "description": "E-commerce website",
    "project_type": "web",
    "tech_stack": ["Python", "React"]
  }'
```

### Step 5: Execute a Task
```bash
curl -X POST http://localhost:8000/api/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create e-commerce website",
    "context": {
      "language": "Python",
      "framework": "FastAPI"
    }
  }'
```

### Step 6: Chat with AI
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a Python calculator"}'
```

## Docker Quick Start

```bash
# Start all services
docker-compose -f backend/docker/docker-compose.yml up

# In another terminal
# Backend will be ready in ~30 seconds
curl http://localhost:8000/health
```

## Android Setup

```bash
cd android

# Build APK
./gradlew build

# Install on emulator
./gradlew installDebug

# Or open in Android Studio and run
```

## Architecture at a Glance

```
┌─────────────────┐
│ Android App     │
│ 3D UI/UX        │
└────────┬────────┘
         │
    ┌────▼──────────────┐
    │ FastAPI Gateway   │
    │ :8000            │
    └────┬──────────────┘
         │
    ┌────▼──────────────┐
    │ Planner Agent     │
    │ (Main Brain)     │
    └────┬──────────────┘
         │
    ┌────┴───────────────┬────────────┬──────────┐
    │                    │            │          │
┌───▼──┐          ┌─────▼──┐   ┌────▼──┐   ┌───▼──┐
│Code  │          │Web     │   │DevOps │   │Data  │
│Agent │          │Agent   │   │Agent  │   │Agent │
└──────┘          └────────┘   └───────┘   └──────┘
```

## Key Features to Try

### 1. Task Planning
```
POST /api/tasks/execute
- AI breaks down task
- Plans execution
- Assigns to agents
```

### 2. Code Generation
```
Web Agent creates:
- React components
- CSS animations
- Glassmorphism UI
```

### 3. DevOps Automation
```
DevOps Agent generates:
- Dockerfile
- CI/CD workflows
- Deployment scripts
```

### 4. Real-time Updates
```
WS /api/ws/updates/{task_id}
- Live progress
- Step completion
- Error alerts
```

## API Endpoints Overview

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/projects` | Create project |
| GET | `/api/projects` | List projects |
| POST | `/api/tasks/execute` | Execute task |
| GET | `/api/tasks/{id}` | Get task status |
| POST | `/api/chat` | Chat with AI |
| GET | `/api/agents/status` | Agent status |
| WS | `/api/ws/updates/{id}` | Real-time updates |

## Configuration

Copy `.env.example` to `.env` and update:
```bash
cp .env.example .env
# Edit API keys, database URL, etc.
```

## Troubleshooting

### Backend won't start?
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check port availability
lsof -i :8000  # On macOS/Linux
```

### Docker issues?
```bash
# Clean up containers
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Start fresh
docker-compose up
```

### Android connection issues?
```bash
# Get your machine IP
ipconfig getifaddr en0  # macOS
hostname -I            # Linux
ipconfig               # Windows

# Update MainActivity.kt with IP
const val API_URL = "http://YOUR_IP:8000"
```

## Next Steps

1. **Explore API Docs**: http://localhost:8000/docs
2. **Read Architecture**: See `docs/ARCHITECTURE.md`
3. **Understand Agents**: See `docs/AGENTS.md`
4. **Deploy**: See `docs/DEPLOYMENT.md`
5. **Customize**: Modify agents for your needs

## Example: Create Website

```bash
# 1. Create project
curl -X POST http://localhost:8000/api/projects \
  -d '{"title": "My Website", "project_type": "web"}'

# 2. Execute task
curl -X POST http://localhost:8000/api/tasks/execute \
  -d '{"task": "Create professional website"}'

# 3. Watch progress (in Android app or WebSocket)
# - Planner breaks down task
# - Web Agent creates UI
# - Code Agent creates API
# - DevOps Agent creates deployment

# 4. View generated files in projects/
```

## Performance Tips

- Use Docker for consistent environment
- Enable Redis for caching (optional)
- Run tests before deployment
- Monitor logs in production

## Support

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Logs**: Check Docker output or `docker logs`

---

You're all set! Start building with OmniDev AI 🚀
