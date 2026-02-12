# OmniDev AI - Quick Reference Guide

## 🚀 Start/Stop Commands

### Start Everything
```bash
cd backend/docker
docker-compose up -d
```

### Stop Everything
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### View Container Logs
```bash
# All containers
docker-compose logs -f

# Specific container
docker-compose logs -f omnidev-ai-backend
docker-compose logs -f omnidev-postgres
docker-compose logs -f omnidev-redis
```

---

## 📱 API Endpoints

### Health & Status
- **Health Check**: `GET http://localhost:8000/health`
- **API Root**: `GET http://localhost:8000`
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **API ReDoc**: http://localhost:8000/redoc

### Core API Endpoints
- **Projects**: `http://localhost:8000/api/projects`
- **Chat**: `http://localhost:8000/api/chat`
- **Execute**: `http://localhost:8000/api/execute`
- **Tasks**: `http://localhost:8000/api/tasks`
- **Memory**: `http://localhost:8000/api/memory`

---

## 🗄️ Database Access

### PostgreSQL
```
Host: localhost
Port: 5432
Username: user
Password: password
Database: omnidev
```

**Connect via psql**:
```bash
psql -h localhost -U user -d omnidev
```

### Redis
```
Host: localhost
Port: 6379
No authentication required
```

**Connect via redis-cli**:
```bash
redis-cli ping
```

---

## 🐍 Python Development

### Activate Virtual Environment
```bash
cd backend
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac
```

### Run Tests
```bash
pytest backend/tests/
```

### Run Development Server (Non-Docker)
```bash
cd backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📊 Container Status

Check all containers:
```bash
docker ps
```

Inspect specific container:
```bash
docker inspect omnidev-ai-backend
```

---

## 🔑 Configuration

### Environment Variables
File: `.env` in project root

**Key Variables**:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/omnidev

# API
API_HOST=0.0.0.0
API_PORT=8000

# AI Keys (Add your own)
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-your-key

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

## 🛠️ Troubleshooting

### API Not Responding
```bash
# Check container status
docker ps

# View logs
docker-compose logs omnidev-ai-backend

# Restart
docker-compose restart omnidev-ai-backend
```

### Database Connection Error
```bash
# Check PostgreSQL
docker-compose logs omnidev-postgres

# Verify connection
psql -h localhost -U user -d omnidev -c "SELECT 1"
```

### Port Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (Windows)
taskkill /PID <PID> /F

# Or change docker-compose port mapping
```

---

## 📦 Common Tasks

### View Running Containers
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Execute Command in Container
```bash
docker exec omnidev-ai-backend python -c "print('Hello')"
```

### Build Images Without Cache
```bash
docker-compose build --no-cache
```

### Clean Up Everything
```bash
# Remove containers
docker-compose down

# Remove images
docker image prune -a

# Remove volumes
docker volume prune
```

---

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs
- **Project Guide**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- **Setup Guide**: [SETUP.md](SETUP.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Agents**: [docs/AGENTS.md](docs/AGENTS.md)
- **Deployment**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 🎯 Development Workflow

1. **Start Services**
   ```bash
   cd backend/docker
   docker-compose up -d
   ```

2. **Verify Health**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Access API Docs**
   - Open http://localhost:8000/docs

4. **Make Code Changes**
   - Edit files in `backend/app/`
   - Docker hot-reload enabled

5. **Test Changes**
   - Use Swagger UI at `/docs`
   - Or use curl/Postman

6. **View Logs**
   ```bash
   docker-compose logs -f omnidev-ai-backend
   ```

---

## 💡 Tips

- **Hot Reload**: Enabled in development - changes reflect automatically
- **Database Persistence**: Data persists in `docker_postgres_data` volume
- **Environment Variables**: Reload containers after changing `.env`
- **Memory Issues**: Use `docker-compose down` to free resources

---

**Last Updated**: February 5, 2026  
**Status**: ✅ Fully Operational
