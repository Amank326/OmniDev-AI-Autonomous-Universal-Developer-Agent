# Architecture Overview

## System Architecture

OmniDev AI is built with a microservices-inspired architecture that separates concerns while maintaining simplicity for deployment.

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
│                      (nginx/traefik)                         │
└───────────────────┬─────────────────────┬───────────────────┘
                    │                     │
        ┌───────────▼──────────┐ ┌───────▼──────────┐
        │   Frontend (Next.js)  │ │  Backend (FastAPI)│
        │   - React Components  │ │  - REST API       │
        │   - Static Assets     │ │  - WebSocket      │
        │   - SSR/SSG          │ │  - Authentication │
        └───────────┬──────────┘ └───────┬──────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
    ┌───────▼────────┐ ┌──────▼──────┐ ┌────────▼────────┐
    │   PostgreSQL    │ │    Redis     │ │  Celery Worker  │
    │   - User Data   │ │  - Cache     │ │  - Async Tasks  │
    │   - Agents      │ │  - Sessions  │ │  - AI Agents    │
    │   - Subscr.     │ │  - Queues    │ │  - Notifications│
    └────────────────┘ └──────────────┘ └─────────────────┘
```

## Components

### Frontend (Next.js + TypeScript)

- **Purpose**: User interface and client-side logic
- **Technology**: Next.js 15, React 19, TypeScript
- **Features**:
  - Server-Side Rendering (SSR)
  - Static Site Generation (SSG)
  - API routes for BFF pattern
  - Real-time updates via WebSocket
  - Responsive design with Tailwind CSS

### Backend (FastAPI + Python)

- **Purpose**: API server and business logic
- **Technology**: FastAPI, Python 3.11+, async/await
- **Features**:
  - RESTful API endpoints
  - WebSocket support
  - JWT authentication
  - OpenAPI documentation
  - Async database operations

### Database (PostgreSQL)

- **Purpose**: Persistent data storage
- **Technology**: PostgreSQL 15+
- **Features**:
  - Relational data model
  - ACID compliance
  - Full-text search
  - JSON support
  - Connection pooling

### Cache Layer (Redis)

- **Purpose**: Caching and session management
- **Technology**: Redis 7+
- **Features**:
  - Session storage
  - Rate limiting
  - Pub/Sub for real-time features
  - Task queue for Celery

### Task Queue (Celery)

- **Purpose**: Asynchronous task processing
- **Technology**: Celery, Redis broker
- **Features**:
  - AI agent execution
  - Email sending
  - Background processing
  - Scheduled tasks

## Data Flow

### Authentication Flow

```
┌────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│ Client │─────▶│ Frontend │─────▶│ Backend  │─────▶│ Database │
└────────┘      └──────────┘      └──────────┘      └──────────┘
    │               │                  │                  │
    │               │                  │  Query User      │
    │               │                  │◀─────────────────┤
    │               │                  │                  │
    │               │                  │ Verify Password  │
    │               │                  │                  │
    │               │  JWT Tokens      │                  │
    │               │◀─────────────────┤                  │
    │  JWT Tokens   │                  │                  │
    │◀──────────────┤                  │                  │
    │               │                  │                  │
```

### AI Agent Execution Flow

```
┌────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│ Client │─────▶│ Backend  │─────▶│  Celery  │─────▶│   Agent  │
└────────┘      └──────────┘      └──────────┘      └──────────┘
    │               │                  │                  │
    │               │  Queue Task      │                  │
    │               │─────────────────▶│                  │
    │               │                  │  Execute         │
    │               │                  │─────────────────▶│
    │               │                  │                  │
    │               │                  │  Result          │
    │               │                  │◀─────────────────┤
    │               │  Task Result     │                  │
    │               │◀─────────────────┤                  │
    │  Response     │                  │                  │
    │◀──────────────┤                  │                  │
    │               │                  │                  │
```

### Real-Time Notification Flow

```
┌────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│ Client │◀─────│ WebSocket│◀─────│ Backend  │─────▶│  Redis   │
└────────┘      └──────────┘      └──────────┘      └──────────┘
    │               │                  │                  │
    │  Subscribe    │                  │                  │
    │──────────────▶│                  │                  │
    │               │                  │  Pub/Sub         │
    │               │                  │─────────────────▶│
    │               │                  │                  │
    │               │  Notification    │                  │
    │               │◀─────────────────┤                  │
    │  Push Notif.  │                  │                  │
    │◀──────────────┤                  │                  │
    │               │                  │                  │
```

## Security Architecture

### Authentication & Authorization

1. **JWT Tokens**
   - Access token (short-lived, 30 min)
   - Refresh token (long-lived, 7 days)
   - Stored in httpOnly cookies or localStorage

2. **Password Security**
   - bcrypt hashing
   - Salt rounds: 12
   - Minimum length: 8 characters

3. **API Security**
   - HTTPS only in production
   - CORS configuration
   - Rate limiting
   - Input validation

### Data Security

1. **At Rest**
   - Database encryption
   - Encrypted backups
   - Secure credential storage

2. **In Transit**
   - TLS 1.3
   - SSL certificates
   - Secure WebSocket (WSS)

## Scalability

### Horizontal Scaling

- **Frontend**: Multiple Next.js instances behind load balancer
- **Backend**: Multiple FastAPI instances with shared Redis session
- **Database**: Read replicas for scaling reads
- **Workers**: Scale Celery workers independently

### Vertical Scaling

- Increase CPU/memory for compute-intensive tasks
- Database optimization (indexes, query tuning)
- Connection pooling

### Caching Strategy

1. **Application Cache**: Redis for API responses
2. **Database Cache**: Query result caching
3. **CDN**: Static asset delivery
4. **Browser Cache**: Client-side caching

## Monitoring & Observability

### Metrics

- **Application Metrics**: Request count, latency, errors
- **System Metrics**: CPU, memory, disk, network
- **Business Metrics**: User registrations, agent executions

### Logging

- **Structured Logging**: JSON format
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Aggregation**: Centralized logging with ELK/Loki

### Tracing

- **Distributed Tracing**: Request flow across services
- **Performance Monitoring**: Bottleneck identification
- **Error Tracking**: Sentry integration

## Deployment Architecture

### Development

```
┌─────────────────────────────────────────┐
│         Docker Compose                   │
│  ┌─────────┐ ┌─────────┐ ┌────────────┐│
│  │Frontend │ │ Backend │ │ PostgreSQL ││
│  └─────────┘ └─────────┘ └────────────┘│
│  ┌─────────┐ ┌─────────┐               │
│  │  Redis  │ │ Celery  │               │
│  └─────────┘ └─────────┘               │
└─────────────────────────────────────────┘
```

### Production (Kubernetes)

```
┌────────────────────────────────────────────────┐
│            Kubernetes Cluster                   │
│  ┌──────────────┐  ┌──────────────┐           │
│  │   Ingress    │  │   Frontend   │           │
│  │  Controller  │  │    Pods      │           │
│  └──────────────┘  └──────────────┘           │
│  ┌──────────────┐  ┌──────────────┐           │
│  │   Backend    │  │   Workers    │           │
│  │    Pods      │  │    Pods      │           │
│  └──────────────┘  └──────────────┘           │
│  ┌──────────────┐  ┌──────────────┐           │
│  │  PostgreSQL  │  │    Redis     │           │
│  │  StatefulSet │  │  StatefulSet │           │
│  └──────────────┘  └──────────────┘           │
└────────────────────────────────────────────────┘
```

## Technology Choices

### Why FastAPI?

- Modern, fast (async/await)
- Automatic API documentation
- Type hints and validation
- Built-in dependency injection
- WebSocket support

### Why Next.js?

- Server-Side Rendering (SEO)
- Static Site Generation (performance)
- File-based routing
- API routes
- TypeScript support

### Why PostgreSQL?

- ACID compliance
- Rich query capabilities
- JSON support
- Mature ecosystem
- Excellent performance

### Why Redis?

- In-memory speed
- Versatile data structures
- Pub/Sub capabilities
- TTL support
- Lua scripting

## Future Enhancements

1. **Microservices**: Split into dedicated services
2. **GraphQL**: Alternative to REST API
3. **Event Sourcing**: For audit trails
4. **Service Mesh**: Istio for advanced networking
5. **Machine Learning**: Model serving infrastructure
6. **Multi-tenancy**: Isolated customer data
7. **API Gateway**: Kong or AWS API Gateway
8. **Message Queue**: RabbitMQ or Kafka for events
