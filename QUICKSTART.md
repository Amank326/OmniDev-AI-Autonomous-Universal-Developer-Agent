# OmniDev AI Platform - Quick Start Guide

## Getting Started

### Prerequisites
- Docker & Docker Compose installed
- Git installed

### Quick Start with Docker

1. **Clone the repository:**
```bash
git clone https://github.com/Amank326/OmniDev-AI-Autonomous-Universal-Developer-Agent.git
cd OmniDev-AI-Autonomous-Universal-Developer-Agent
```

2. **Set up environment variables:**
```bash
cp backend/.env.example backend/.env
```

3. **Start all services:**
```bash
docker-compose up -d
```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/api/v1/docs

### Testing the API

Use the provided API gateway script:
```bash
cd backend
python api_gateway.py
```

Or use curl:
```bash
# Health check
curl http://localhost:8000/health

# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

## Key Features

### 1. Autonomous AI Agents
Create and manage AI agents for various tasks:
- Code analysis and review
- Code generation
- Documentation generation
- Testing and quality assurance

### 2. Authentication & Security
- JWT-based authentication
- Email verification
- Password reset functionality
- Role-based access control

### 3. Multi-Channel Notifications
- Email notifications
- SMS notifications (ready for integration)
- Push notifications (ready for integration)
- Real-time WebSocket updates

### 4. Payment & Subscriptions
- Stripe integration
- Multiple subscription plans
- Payment processing
- Invoice management

### 5. Real-Time Collaboration
- WebSocket connections
- Live updates
- Multi-user support

## Project Structure

```
.
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── agents/         # AI agents
│   └── tests/              # Tests
├── frontend/               # Next.js frontend
│   ├── pages/             # Page components
│   ├── components/        # UI components
│   └── lib/               # Utilities
├── docs/                  # Documentation
└── docker-compose.yml     # Docker setup
```

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## Running Tests

```bash
cd backend
pytest
```

## Next Steps

1. Explore the API documentation at http://localhost:8000/api/v1/docs
2. Create your first AI agent
3. Set up notifications
4. Configure payment processing with Stripe
5. Customize the frontend

## Support

- Documentation: See `docs/` directory
- Issues: https://github.com/Amank326/OmniDev-AI-Autonomous-Universal-Developer-Agent/issues

## License

MIT License - See LICENSE file for details
