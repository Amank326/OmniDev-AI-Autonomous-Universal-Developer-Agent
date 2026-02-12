"""
Phase 7B: Real-time Advanced Metrics WebSocket

WebSocket endpoints for live streaming of:
- MRR and subscription changes
- User activity feeds
- Anomaly detection alerts
- Churn risk updates
- System health metrics
"""

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional
from app.database import get_db
from app.auth.tokens import EmailVerificationToken
from app.auth.utils import verify_token

router = APIRouter(tags=["metrics-websocket"])
logger = logging.getLogger(__name__)


class MetricsConnectionManager:
    """Manage WebSocket connections for real-time metric updates"""
    
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}  # customer_id -> set of websockets
        self.subscription_metrics: Dict[int, Dict] = {}  # customer_id -> latest metrics
    
    async def connect(self, websocket: WebSocket, customer_id: int):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        if customer_id not in self.active_connections:
            self.active_connections[customer_id] = set()
        
        self.active_connections[customer_id].add(websocket)
        logger.info(f"Metrics Client {customer_id} connected. Total: {len(self.active_connections[customer_id])}")
    
    def disconnect(self, customer_id: int, websocket: WebSocket):
        """Remove disconnected client"""
        if customer_id in self.active_connections:
            self.active_connections[customer_id].discard(websocket)
            
            if not self.active_connections[customer_id]:
                del self.active_connections[customer_id]
        
        logger.info(f"Metrics Client {customer_id} disconnected")
    
    async def broadcast_to_customer(self, customer_id: int, message: Dict):
        """Send message to all connections for a customer"""
        if customer_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[customer_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected
            for conn in disconnected:
                self.active_connections[customer_id].discard(conn)
    
    async def broadcast_to_all(self, message: Dict):
        """Send message to all customers"""
        for customer_id in list(self.active_connections.keys()):
            await self.broadcast_to_customer(customer_id, message)


metrics_manager = MetricsConnectionManager()


# ==================== WEBSOCKET ENDPOINTS ====================

@router.websocket("/ws/live-metrics/{token}")
async def websocket_live_metrics(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket for real-time MRR, ARR, subscription, and engagement metrics
    
    **Message Types Streamed:**
    - mrr_update: Monthly recurring revenue change
    - arr_update: Annual recurring revenue
    - subscription_change: New/canceled subscriptions
    - engagement_update: Engagement score changes
    - revenue_breakdown: New/churned/net revenue
    
    **Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/live-metrics/{token}');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Metric update:', data);
    };
    ```
    """
    
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    customer_id = payload.get("sub")
    await metrics_manager.connect(websocket, customer_id)
    
    try:
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": datetime.utcnow().isoformat(),
            "customer_id": customer_id,
            "message": "Connected to real-time metrics stream",
            "supported_metrics": [
                "mrr", "arr", "ltv", "churn_rate", "subscriptions",
                "engagement", "revenue_breakdown", "customer_count"
            ]
        })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        metrics_manager.disconnect(customer_id, websocket)
    except Exception as e:
        logger.error(f"Metrics WebSocket error: {e}")
        metrics_manager.disconnect(customer_id, websocket)


@router.websocket("/ws/live-activity/{token}")
async def websocket_live_activity(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Real-time activity feed with user actions, logins, feature usage
    
    **Activity Types:**
    - login/logout
    - feature_used
    - api_call
    - dashboard_view
    - report_generated
    - subscription_change
    - payment_processed
    
    **Stream Update Frequency:** Real-time as events occur
    """
    
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    customer_id = payload.get("sub")
    await metrics_manager.connect(websocket, customer_id)
    
    try:
        await websocket.send_json({
            "type": "activity_stream_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Receiving real-time activity updates"
        })
        
        # Send recent activities on connect
        from app.models.activity_models import UserActivity
        from datetime import timedelta
        from sqlalchemy import and_
        
        start_date = datetime.utcnow() - timedelta(hours=1)
        recent = db.query(UserActivity).filter(
            and_(
                UserActivity.customer_id == customer_id,
                UserActivity.created_at >= start_date
            )
        ).order_by(UserActivity.created_at.desc()).limit(20).all()
        
        if recent:
            await websocket.send_json({
                "type": "recent_activity_batch",
                "activities": [
                    {
                        "id": a.id,
                        "type": a.activity_type,
                        "description": a.description,
                        "endpoint": a.endpoint,
                        "timestamp": a.created_at.isoformat()
                    }
                    for a in recent
                ],
                "count": len(recent)
            })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        metrics_manager.disconnect(customer_id, websocket)
    except Exception as e:
        logger.error(f"Activity WebSocket error: {e}")
        metrics_manager.disconnect(customer_id, websocket)


@router.websocket("/ws/live-alerts/{token}")
async def websocket_live_alerts(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Real-time predictive alerts and anomaly notifications
    
    **Alert Types:**
    - churn_risk: Customer showing churn signals
    - anomaly_detected: System or behavior anomalies
    - engagement_drop: Engagement score declining
    - payment_failure: Failed payment attempts
    - upgrade_opportunity: Customer ready to upgrade
    
    **Priority Levels:**
    - critical: Immediate action needed
    - high: Action within 24 hours
    - medium: Action within 7 days
    - low: Monitoring/routine
    """
    
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    customer_id = payload.get("sub")
    await metrics_manager.connect(websocket, customer_id)
    
    try:
        await websocket.send_json({
            "type": "alert_stream_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Receiving real-time alert notifications"
        })
        
        # Send initial unresolved alerts
        from app.models.activity_models import PredictiveAlert
        
        unresolved = db.query(PredictiveAlert).filter(
            PredictiveAlert.customer_id == customer_id,
            PredictiveAlert.resolved == False
        ).limit(10).all()
        
        if unresolved:
            await websocket.send_json({
                "type": "initial_alerts",
                "alerts": [
                    {
                        "id": a.id,
                        "type": a.alert_type,
                        "title": a.alert_title,
                        "priority": a.priority,
                        "urgency": a.urgency,
                        "recommended_action": a.recommended_action,
                        "created_at": a.created_at.isoformat()
                    }
                    for a in unresolved
                ],
                "count": len(unresolved)
            })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "acknowledge":
                alert_id = message.get("alert_id")
                alert = db.query(PredictiveAlert).filter(
                    PredictiveAlert.id == alert_id
                ).first()
                
                if alert:
                    alert.acknowledged = True
                    db.commit()
                    
                    await websocket.send_json({
                        "type": "alert_acknowledged",
                        "alert_id": alert_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            elif message.get("action") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        metrics_manager.disconnect(customer_id, websocket)
    except Exception as e:
        logger.error(f"Alert WebSocket error: {e}")
        metrics_manager.disconnect(customer_id, websocket)


@router.websocket("/ws/live-engagement/{token}")
async def websocket_live_engagement(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Real-time engagement score and trend updates
    
    **Streamed Metrics:**
    - engagement_score (0-100)
    - trend (increasing/stable/declining)
    - component_scores (login, feature, API, retention)
    - activity_frequency
    - at_risk_status
    
    **Update Frequency:** Every 60 seconds + on activity events
    """
    
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    customer_id = payload.get("sub")
    await metrics_manager.connect(websocket, customer_id)
    
    try:
        await websocket.send_json({
            "type": "engagement_stream_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "update_frequency": "60 seconds + real-time updates"
        })
        
        from app.models.activity_models import EngagementMetrics
        
        metrics = db.query(EngagementMetrics).filter(
            EngagementMetrics.customer_id == customer_id
        ).first()
        
        if metrics:
            await websocket.send_json({
                "type": "engagement_snapshot",
                "engagement_score": metrics.engagement_score,
                "login_frequency_score": metrics.login_frequency_score,
                "feature_usage_score": metrics.feature_usage_score,
                "api_usage_score": metrics.api_usage_score,
                "retention_score": metrics.retention_score,
                "trend": metrics.engagement_trend,
                "logins_30d": metrics.logins_30d,
                "feature_count_used": metrics.feature_count_used,
                "api_calls_30d": metrics.api_calls_30d,
                "at_risk": metrics.engagement_declining,
                "last_activity": metrics.last_activity_at.isoformat() if metrics.last_activity_at else None
            })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "request_update":
                from app.services.advanced_analytics_service import AdvancedAnalyticsService
                
                AdvancedAnalyticsService.calculate_engagement_score(
                    db=db,
                    customer_id=customer_id
                )
                
                metrics = db.query(EngagementMetrics).filter(
                    EngagementMetrics.customer_id == customer_id
                ).first()
                
                if metrics:
                    await websocket.send_json({
                        "type": "engagement_update",
                        "engagement_score": metrics.engagement_score,
                        "trend": metrics.engagement_trend,
                        "updated_at": datetime.utcnow().isoformat()
                    })
            
            elif message.get("action") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        metrics_manager.disconnect(customer_id, websocket)
    except Exception as e:
        logger.error(f"Engagement WebSocket error: {e}")
        metrics_manager.disconnect(customer_id, websocket)


# ==================== BROADCAST HELPER FUNCTIONS ====================

async def broadcast_revenue_update(customer_id: int, mrr: float, arr: float, timestamp: datetime = None):
    """Broadcast revenue metrics update to customer"""
    await metrics_manager.broadcast_to_customer(customer_id, {
        "type": "revenue_update",
        "mrr": mrr,
        "arr": arr,
        "timestamp": (timestamp or datetime.utcnow()).isoformat()
    })


async def broadcast_subscription_event(customer_id: int, event_type: str, count: int):
    """Broadcast subscription change (new/canceled/upgraded)"""
    await metrics_manager.broadcast_to_customer(customer_id, {
        "type": "subscription_event",
        "event_type": event_type,  # new/canceled/upgraded/downgraded
        "count": count,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_anomaly_alert(customer_id: Optional[int], anomaly_type: str, severity: str, description: str):
    """Broadcast anomaly detection alert"""
    message = {
        "type": "anomaly_alert",
        "anomaly_type": anomaly_type,
        "severity": severity,
        "description": description,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if customer_id:
        await metrics_manager.broadcast_to_customer(customer_id, message)
    else:
        await metrics_manager.broadcast_to_all(message)


async def broadcast_churn_warning(customer_id: int, probability: float, risk_level: str):
    """Broadcast churn risk alert"""
    await metrics_manager.broadcast_to_customer(customer_id, {
        "type": "churn_warning",
        "churn_probability": probability,
        "risk_level": risk_level,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_activity_event(customer_id: int, activity_type: str, description: str):
    """Broadcast user activity event"""
    await metrics_manager.broadcast_to_customer(customer_id, {
        "type": "activity_event",
        "activity_type": activity_type,
        "description": description,
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_system_health(cpu: float, memory: float, requests_per_min: float, error_rate: float):
    """Broadcast system health metrics to all"""
    await metrics_manager.broadcast_to_all({
        "type": "system_health",
        "cpu_percent": cpu,
        "memory_percent": memory,
        "requests_per_minute": requests_per_min,
        "error_rate": error_rate,
        "timestamp": datetime.utcnow().isoformat()
    })
