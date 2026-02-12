from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.api import routes
from app.auth.routes import router as auth_router
from app.email.routes import router as email_router
from app.realtime.routes import router as websocket_router
from app.api.worker_routes import router as worker_router
# from app.api.analytics_routes import router as analytics_router  # FIXED: Temporarily disabled
from app.api.collaboration_routes import router as collaboration_router
from app.api.users_routes import router as users_router
from app.api.projects_routes import router as projects_router
from app.api.tasks_routes import router as tasks_router
from app.api.agents_routes import router as agents_router
from app.api.websocket_routes import router as new_websocket_router
from app.api.payment_routes import router as payment_router
from app.api.webhooks import router as webhook_router
# Phase 7B: Advanced Analytics
from app.api.activity_routes import router as activity_router
from app.api.metrics_websocket_routes import router as metrics_websocket_router
# Phase 8: Advanced Cohort Analytics
from app.api.cohort_routes import router as cohort_router
from app.api.custom_metrics_routes import router as custom_metrics_router
# Phase 49: Enterprise Analytics & Business Intelligence
from app.api.analytics_routes_phase49 import router as analytics_phase49_router
# Phase 50: Advanced API Gateway & Rate Limiting
from app.api.gateway_routes_phase50 import router as gateway_phase50_router
from app.middleware.rate_limit import limiter, setup_rate_limiting
from app.agents.planner import PlannerAgent
from app.memory.vector_store import VectorMemory
from app.database.config import init_db, SessionLocal
from app.database.seed import seed_database
from app.scheduler.config import start_scheduler, stop_scheduler
# Phase 8: Advanced AI Features
from app.rag.retrieval import rag_service
from app.agents.orchestrator import agent_orchestrator
from app.realtime.collaboration import collaboration_manager, handle_websocket_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
planner_agent = None
vector_memory = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global planner_agent, vector_memory
    logger.info("Initializing OmniDev AI...")
    
    # Initialize database
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
        
        # Seed database if empty
        try:
            db = SessionLocal()
            from app.database.models import User
            user_count = db.query(User).count()
            db.close()
            if user_count == 0:
                logger.info("Seeding database with initial data...")
                seed_database()
                logger.info("Database seeded successfully")
        except Exception as e:
            logger.warning(f"Database seeding skipped: {e}")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    # Initialize AI systems
    vector_memory = VectorMemory()
    planner_agent = PlannerAgent(memory=vector_memory)
    
    # Phase 8: Initialize Advanced AI Features
    try:
        logger.info("Initializing Phase 8 - Advanced AI Features...")
        # RAG service initialization
        logger.info("Initializing RAG service...")
        # rag_service is already initialized globally
        logger.info("RAG service ready")
        
        # Agent orchestrator is ready
        logger.info(f"Agent orchestrator ready with {len(agent_orchestrator.available_agents)} agents")
    except Exception as e:
        logger.warning(f"Phase 8 initialization warning: {e}")
    
    logger.info("OmniDev AI Ready!")
    
    # Start scheduler for periodic tasks
    try:
        start_scheduler()
        logger.info("Task scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start scheduler: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down OmniDev AI...")
    try:
        stop_scheduler()
        logger.info("Task scheduler stopped")
    except Exception as e:
        logger.warning(f"Failed to stop scheduler: {e}")

app = FastAPI(
    title="OmniDev AI",
    description="Autonomous Universal Developer Agent",
    version="1.0.0",
    lifespan=lifespan
)

# Setup rate limiting
app.state.limiter = limiter
setup_rate_limiting(app)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth_router)
app.include_router(email_router)
app.include_router(routes.router)
app.include_router(worker_router)
# app.include_router(analytics_router)  # FIXED: Temporarily disabled - file needs migration from Flask to FastAPI
app.include_router(websocket_router)
app.include_router(users_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(payment_router)
app.include_router(webhook_router)
app.include_router(new_websocket_router)
# Phase 8: Collaboration routes
app.include_router(collaboration_router)
# Phase 7B: Advanced Analytics routes
app.include_router(activity_router, prefix="/api/activity", tags=["analytics"])
app.include_router(metrics_websocket_router)
# Phase 8: Cohort Analytics routes
app.include_router(cohort_router, prefix="/api/cohorts", tags=["cohort-analytics"])
app.include_router(custom_metrics_router, prefix="/api/metrics", tags=["custom-metrics"])

# Phase 49: Enterprise Analytics & Business Intelligence routes
app.include_router(analytics_phase49_router)

# Phase 50: Advanced API Gateway & Rate Limiting routes
app.include_router(gateway_phase50_router)

# Phase 9: Advanced Analytics routes
from app.api.phase9_routes import router as phase9_router
app.include_router(phase9_router)

# Phase 10: Workflow & Automation routes
from app.api.phase10_routes import router as phase10_router
app.include_router(phase10_router)

# Phase 11: AI Optimization routes
from app.api.ai_routes import router as ai_router
app.include_router(ai_router)

# Phase 12: Enterprise Features routes
# from app.api.enterprise_routes import router as enterprise_router  # FIXED: Missing enterprise_service module
# app.include_router(enterprise_router)  # FIXED: Disabled until enterprise_service is created

# Phase 13: Monitoring & Observability
from app.services.distributed_tracer import DistributedTracer
from app.services.metrics_aggregator import MetricsAggregator
from app.services.sla_slo_manager import SLAManager
from app.services.anomaly_detector_ml import AnomalyDetector
from app.services.alert_manager import AlertManager
from app.services.cost_optimizer import CostOptimizer
# from app.api.monitoring_routes import router as monitoring_router, set_monitoring_services  # FIXED: Flask import issue
from app.middleware.monitoring_middleware import MonitoringMiddleware

# Initialize monitoring services
distributed_tracer = DistributedTracer()
metrics_aggregator = MetricsAggregator()
sla_manager = SLAManager()
anomaly_detector = AnomalyDetector()
alert_manager = AlertManager()
cost_optimizer = CostOptimizer()

# Inject services into monitoring routes
# set_monitoring_services(  # FIXED: Disabled - monitoring_routes import was commented out
#     distributed_tracer,
#     metrics_aggregator,
#     sla_manager,
#     anomaly_detector,
#     alert_manager,
#     cost_optimizer
# )

# Add monitoring middleware
app.add_middleware(
    MonitoringMiddleware,
    distributed_tracer=distributed_tracer,
    metrics_aggregator=metrics_aggregator
)

# app.include_router(monitoring_router)  # FIXED: Disabled until monitoring_routes Flask import is fixed

# Phase 14: API Marketplace & Workflow Sharing
from app.services.marketplace_service import MarketplaceService
from app.services.workflow_sharing_service import WorkflowSharingService
from app.services.contribution_service import ContributionService
from app.services.revenue_manager import RevenueManager
from app.api.marketplace_routes import router as marketplace_router, set_marketplace_services

# Initialize marketplace services
marketplace_svc = MarketplaceService()
sharing_svc = WorkflowSharingService()
contribution_svc = ContributionService()
revenue_mgr = RevenueManager()

# Inject services into marketplace routes
set_marketplace_services(
    marketplace_svc,
    sharing_svc,
    contribution_svc,
    revenue_mgr
)

app.include_router(marketplace_router)

# Phase 15: AI Agent Marketplace & Autonomous Agents
from app.services.agent_marketplace_service import AgentMarketplaceService
from app.services.agent_orchestration_service import AgentOrchestrationService
from app.services.agent_monitoring_service import AgentMonitoringService
from app.api.agent_routes import router as agent_router, set_agent_services

# Initialize agent services
agent_marketplace_svc = AgentMarketplaceService(SessionLocal())
agent_orchestration_svc = AgentOrchestrationService(SessionLocal())
agent_monitoring_svc = AgentMonitoringService(SessionLocal())

# Inject services into agent routes
set_agent_services(
    agent_marketplace_svc,
    agent_orchestration_svc,
    agent_monitoring_svc
)

app.include_router(agent_router)

# Phase 16: Agent Marketplace Monetization
from app.services.agent_payment_service import AgentPaymentService
from app.services.agent_payout_service import AgentPayoutService
from app.services.agent_pricing_service import AgentPricingService
from app.api.monetization_routes import router as monetization_router, set_monetization_services

# Initialize monetization services
agent_payment_svc = AgentPaymentService(SessionLocal())
agent_payout_svc = AgentPayoutService(SessionLocal())
agent_pricing_svc = AgentPricingService(SessionLocal())

# Inject services into monetization routes
set_monetization_services(
    agent_payment_svc,
    agent_payout_svc,
    agent_pricing_svc
)

app.include_router(monetization_router)

logger.info("Phase 16 - Agent Marketplace Monetization initialized")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "OmniDev AI",
        "version": "1.0.0"
    }


# Phase 8: WebSocket Collaboration Endpoint
@app.websocket("/ws/collaborate/{user_id}")
async def websocket_collaborate(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint for real-time multi-agent collaboration.
    
    Path Parameters:
        user_id: User identifier
    
    Message Types:
        - query: Execute agent query with RAG
        - chat: Team collaboration message
        - subscribe: Subscribe to updates
        - unsubscribe: Unsubscribe from updates
        - get_status: Get team status
    """
    await collaboration_manager.connect_user(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            await handle_websocket_message(websocket, user_id, data)
    except WebSocketDisconnect:
        collaboration_manager.disconnect_user(user_id, websocket)
        logger.info(f"User {user_id} disconnected from collaboration WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        collaboration_manager.disconnect_user(user_id, websocket)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to OmniDev AI - Autonomous Universal Developer Agent",
        "endpoints": {
            "health": "/health",
            "api": "/api",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
