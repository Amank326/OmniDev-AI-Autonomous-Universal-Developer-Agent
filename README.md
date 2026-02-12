# OmniDev AI Platform

Production-ready, full-stack AI platform featuring autonomous AI agents, real-time collaboration, and scalable cloud-native architecture.

## 🚀 Features

- **Autonomous AI Agents**: Code analysis, generation, documentation, and testing
- **Secure Authentication**: JWT-based authentication with email verification and password reset
- **Multi-Channel Notifications**: Email, SMS, push notifications, and real-time WebSocket
- **Payment Integration**: Stripe-powered subscription and payment processing
- **Real-Time Collaboration**: WebSocket support for live updates
- **RESTful API**: Comprehensive API with OpenAPI/Swagger documentation
- **Cloud-Native Architecture**: Docker and Kubernetes ready

## 📋 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM with async support
- **Redis** - Caching and session management
- **Celery** - Task queue for async processing
- **Stripe** - Payment processing
- **Alembic** - Database migrations

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **React Query** - Data fetching and caching
- **Axios** - HTTP client

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/Amank326/OmniDev-AI-Autonomous-Universal-Developer-Agent.git
cd OmniDev-AI-Autonomous-Universal-Developer-Agent
```

2. Create environment files:
```bash
cp backend/.env.example backend/.env
```

3. Start services with Docker Compose:
```bash
docker-compose up -d
```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/v1/docs

### Manual Installation

#### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the server:
```bash
uvicorn app.main:app --reload
```

#### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

## 📚 API Documentation

Once the backend is running, access the interactive API documentation at:

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## 🏗️ Project Structure

```
.
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── agents/         # AI agent system
│   │   └── main.py         # Application entry point
│   ├── alembic/            # Database migrations
│   ├── tests/              # Test suite
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── pages/             # Page components
│   ├── components/        # Reusable components
│   ├── lib/               # Utilities and API clients
│   ├── styles/            # Global styles
│   └── package.json       # Node dependencies
├── docs/                  # Documentation
├── docker-compose.yml     # Docker Compose configuration
└── README.md             # This file
```

## 🤖 AI Agents

The platform includes several autonomous AI agents:

- **Code Analyzer**: Analyzes code quality and patterns
- **Code Generator**: Generates code based on specifications
- **Documentation Agent**: Auto-generates documentation
- **Testing Agent**: Creates and runs tests
- **Deployment Agent**: Handles deployment tasks

## 🔐 Authentication

The platform uses JWT-based authentication with:
- User registration with email verification
- Secure login with password hashing (bcrypt)
- Access and refresh tokens
- Password reset functionality

## 💳 Payment Integration

Stripe integration for:
- Subscription management
- One-time payments
- Webhook handling
- Invoice generation

## 🔔 Notifications

Multi-channel notification system:
- **Email**: Transactional emails via SMTP
- **SMS**: SMS notifications (Twilio integration ready)
- **Push**: Push notifications (Firebase integration ready)
- **WebSocket**: Real-time in-app notifications

## 🌐 Deployment

### Docker
```bash
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/
```

## 📊 Monitoring

- Health check endpoint: `/health`
- Prometheus metrics support
- Sentry error tracking (optional)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

Built with modern technologies:
- FastAPI
- Next.js
- PostgreSQL
- Redis
- Stripe
- Docker

## 📧 Support

For support, email support@omnidev.ai or open an issue on GitHub.
