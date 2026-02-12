# OmniDev AI - Backend Setup Guide

## 📦 OmniDev Standalone Backend

This is the **production-ready backend** for OmniDev AI - an autonomous developer agent system.

---

## ✨ What's Inside

```
omnidev-ai/
├── backend/                          # FastAPI backend (main)
│   ├── app/
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── agents/                  # Multi-agent system
│   │   │   ├── planner.py           # Task orchestrator
│   │   │   ├── code_agent.py        # Code generation
│   │   │   ├── web_agent.py         # UI/UX design
│   │   │   ├── devops_agent.py      # Infrastructure automation
│   │   │   └── base_agent.py        # Agent foundation
│   │   ├── memory/                  # Vector memory system
│   │   ├── execution/               # Task execution engine
│   │   └── api/                     # REST endpoints (12+)
│   ├── docker/
│   │   ├── Dockerfile               # Container image
│   │   └── docker-compose.yml       # Multi-service setup
│   └── requirements.txt              # Python dependencies
├── docs/                             # Documentation
├── .github/workflows/                # CI/CD pipelines
└── .env.example                      # Configuration template
```

---

## 🚀 Quick Start

### **Method 1: Direct Python (Fastest)**

```bash
# 1. Navigate to project
cd c:\Users\amank\OneDrive\Desktop\omnidev-ai\backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate it (Windows)
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Visit API docs
# Open: http://localhost:8000/docs
```

### **Method 2: Docker (Recommended)**

```bash
# From project root
cd c:\Users\amank\OneDrive\Desktop\omnidev-ai\backend

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Check status
docker-compose -f docker/docker-compose.yml ps

# Stop services
docker-compose -f docker/docker-compose.yml down
```

### **Method 3: Using setup.sh Script**

```bash
cd c:\Users\amank\OneDrive\Desktop\omnidev-ai

# On Linux/Mac
bash setup.sh

# On Windows (PowerShell)
# Manually run the commands from setup.sh
```

---

## 🔧 Configuration

### **Environment Variables**

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/omnidev
REDIS_URL=redis://localhost:6379

# LLM Configuration
OPENAI_API_KEY=your_key_here
# or
CLAUDE_API_KEY=your_key_here

# Memory System
MEMORY_BACKEND=chromadb
VECTOR_DIMENSION=768

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
```

---

## 🧪 Testing

### **Run Backend Tests**

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_agents.py

# With coverage
pytest --cov=app tests/
```

### **API Health Check**

```bash
# Simple health check
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "service": "OmniDev AI"}

# Get full stats
curl http://localhost:8000/api/stats
```

---

## 📡 API Endpoints

### **Project Management**
```
POST   /api/projects              # Create project
GET    /api/projects              # List all projects  
GET    /api/projects/{id}         # Get project details
DELETE /api/projects/{id}         # Delete project
```

### **Task Execution**
```
POST   /api/tasks/execute         # Execute task
GET    /api/tasks/{id}            # Get task status
GET    /api/tasks/{id}/logs       # Get task logs
```

### **Agent Control**
```
GET    /api/agents/status         # All agents status
GET    /api/agents/{name}         # Specific agent info
```

### **Memory & Learning**
```
POST   /api/memory/search         # Search AI memory
GET    /api/memory/stats          # Memory statistics
```

### **Chat Interface**
```
POST   /api/chat                  # Chat with AI
GET    /api/chat/history          # Chat history
WS     /api/ws/updates/{id}       # WebSocket for real-time
```

### **System**
```
GET    /health                    # Health status
GET    /api/stats                 # System statistics
```

---

## 📚 Key Files Reference

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI application entry point |
| `backend/app/agents/planner.py` | Central task orchestrator |
| `backend/app/agents/code_agent.py` | Code generation agent |
| `backend/app/agents/web_agent.py` | UI/UX design agent |
| `backend/app/agents/devops_agent.py` | Infrastructure automation |
| `backend/app/memory/vector_store.py` | AI memory system |
| `backend/app/execution/executor.py` | Task execution engine |
| `backend/app/api/routes.py` | All REST endpoints |

---

## 🐳 Docker Details

### **Services Included**

```yaml
backend:
  - FastAPI on port 8000
  - Health checks enabled
  - Auto-restart on crash

postgres:
  - Port 5432
  - Database: omnidev
  - Auto-initialized

redis:
  - Port 6379
  - Optional caching layer
```

### **Docker Commands**

```bash
# Start services
docker-compose -f backend/docker/docker-compose.yml up

# Start in background
docker-compose -f backend/docker/docker-compose.yml up -d

# View logs
docker-compose -f backend/docker/docker-compose.yml logs -f backend

# Stop services
docker-compose -f backend/docker/docker-compose.yml down

# Full cleanup
docker-compose -f backend/docker/docker-compose.yml down -v
```

---

## 🤖 Agent System

### **How Agents Work**

```
User Request
    ↓
PlannerAgent
├─ Analyzes task
├─ Creates execution plan
└─ Delegates to specialized agents
    ├─ CodeAgent (code generation)
    ├─ WebAgent (UI/UX design)
    └─ DevOpsAgent (infrastructure)
         ↓
    Results combined & returned
```

### **Creating Custom Task**

```python
# Example: Create e-commerce website
task = {
    "type": "create_project",
    "description": "Build an e-commerce website with user management",
    "requirements": {
        "frontend": "React",
        "backend": "FastAPI",
        "database": "PostgreSQL"
    }
}

# Send to /api/tasks/execute
response = requests.post("http://localhost:8000/api/tasks/execute", json=task)
```

---

## 📊 Common Use Cases

### **Use Case 1: Generate Python Code**

```bash
curl -X POST http://localhost:8000/api/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "type": "code",
    "description": "Create a web scraper for news websites",
    "language": "python"
  }'
```

### **Use Case 2: Design UI Component**

```bash
curl -X POST http://localhost:8000/api/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "type": "web",
    "description": "Design a modern analytics dashboard",
    "style": "glassmorphic"
  }'
```

### **Use Case 3: Generate Deployment Files**

```bash
curl -X POST http://localhost:8000/api/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "type": "devops",
    "description": "Create Docker setup for FastAPI app",
    "services": ["postgres", "redis"]
  }'
```

---

## 🔌 Integration Examples

### **Python Client**

```python
import requests

API_URL = "http://localhost:8000"

# Create project
response = requests.post(
    f"{API_URL}/api/projects",
    json={"name": "My Project", "description": "Test project"}
)
project_id = response.json()["id"]

# Execute task
task = {
    "project_id": project_id,
    "description": "Create a user management system"
}
result = requests.post(f"{API_URL}/api/tasks/execute", json=task)
```

### **JavaScript/Node.js Client**

```javascript
const API_URL = 'http://localhost:8000';

// Create project
const project = await fetch(`${API_URL}/api/projects`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'My Project' })
});

// Get results
const result = await project.json();
console.log(result);
```

### **WebSocket for Real-time Updates**

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/updates/task-123');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Task update:', update);
};
```

---

## 🆘 Troubleshooting

### **Problem: Port 8000 Already in Use**

```bash
# Use different port
python -m uvicorn app.main:app --port 8001

# Or kill process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### **Problem: Database Connection Error**

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Or use SQLite for development
DATABASE_URL=sqlite:///./test.db
```

### **Problem: Module Not Found**

```bash
# Reinstall dependencies
pip install --upgrade --force-reinstall -r requirements.txt

# Or create fresh virtual environment
python -m venv venv_fresh
source venv_fresh/bin/activate  # or venv_fresh\Scripts\activate on Windows
pip install -r requirements.txt
```

### **Problem: Docker Build Fails**

```bash
# Clean build cache
docker-compose -f backend/docker/docker-compose.yml build --no-cache

# Check Docker is running
docker ps
```

---

## 📈 Performance Optimization

### **Production Settings**

```env
API_DEBUG=false
WORKERS=4
RELOAD=false
```

### **Database Optimization**

```bash
# Create indexes (in PostgreSQL)
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
```

### **Caching with Redis**

```python
# Enabled automatically if REDIS_URL is set
REDIS_URL=redis://localhost:6379
```

---

## 🚢 Deployment

### **AWS ECS**

```bash
# Build and push Docker image
docker build -f backend/docker/Dockerfile -t omnidev-ai:latest .
docker tag omnidev-ai:latest <AWS_ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/omnidev-ai:latest
docker push <AWS_ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/omnidev-ai:latest
```

### **Azure Container Instances**

```bash
az container create \
  --resource-group myResourceGroup \
  --name omnidev-ai \
  --image omnidev-ai:latest \
  --ports 8000
```

### **Google Cloud Run**

```bash
gcloud run deploy omnidev-ai \
  --source backend/ \
  --platform managed \
  --region us-central1
```

---

## 📚 Documentation Files

- **README.md** - Project overview
- **QUICKSTART.md** - 5-minute setup
- **ARCHITECTURE.md** - System design
- **AGENTS.md** - Agent implementation guide
- **DEPLOYMENT.md** - Deployment strategies
- **DEVELOPER_GUIDE.md** - Complete reference

---

## 🎯 Next Steps

1. ✅ Choose startup method (Python/Docker)
2. ✅ Configure `.env` file
3. ✅ Start backend server
4. ✅ Test API endpoints
5. ✅ Create first project via API
6. ✅ Execute tasks
7. ✅ Monitor agent operations
8. ✅ Deploy to production

---

## 📞 Support

Check documentation files for detailed information:
- Architecture issues → `docs/ARCHITECTURE.md`
- Agent customization → `docs/AGENTS.md`
- Deployment help → `docs/DEPLOYMENT.md`
- API usage → Swagger UI at `/docs`

---

**OmniDev AI Backend - Production Ready** ✅

Ready to automate your development workflow!
