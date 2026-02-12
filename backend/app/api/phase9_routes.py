"""Phase 9: Advanced Analytics API Endpoints

Routes for:
- Segmentation analysis
- Churn prediction
- LTV forecasting
- Recommendations
- Real-time dashboard
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
import asyncio
import json

from app.auth.dependencies import get_current_user
from app.database.config import get_db
from app.services.segmentation_service import AdvancedSegmentationService
from app.services.predictive_service import PredictiveAnalyticsService
from app.services.recommendation_service import RecommendationEngine
from app.services.realtime_dashboard_service import RealtimeDashboardService
from app.models.payment_models import StripeCustomer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/phase9", tags=["phase9"])


# ==================== Segmentation Endpoints ====================

@router.post("/segmentation/analyze")
async def analyze_customer_segments(
    n_clusters: Optional[int] = None,
    lookback_days: int = 90,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run behavioral segmentation analysis
    
    Endpoint: POST /api/v1/phase9/segmentation/analyze
    """
    try:
        service = AdvancedSegmentationService(db)
        result = service.perform_behavioral_segmentation(n_clusters, lookback_days)
        
        return {
            'status': 'success',
            'message': 'Segmentation analysis completed',
            'data': result,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Segmentation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/segmentation/segments")
async def list_segments(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all customer segments with metrics"""
    try:
        from app.models.phase9_models import CustomerSegment
        
        segments = db.query(CustomerSegment).all()
        
        return {
            'status': 'success',
            'data': [
                {
                    'segment_id': s.segment_id,
                    'segment_name': s.segment_name,
                    'customer_count': len(s.segment_assignments),
                    'avg_ltv': s.avg_ltv,
                    'churn_risk': s.avg_churn_risk,
                    'characteristics': s.characteristics
                }
                for s in segments
            ],
            'total': len(segments)
        }
    except Exception as e:
        logger.error(f"List segments error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/segmentation/customer/{customer_id}")
async def get_customer_segment(
    customer_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get segment assignment for a specific customer"""
    try:
        from app.models.phase9_models import SegmentAssignment
        
        assignment = db.query(SegmentAssignment).filter_by(
            customer_id=customer_id
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Customer segment not found")
        
        return {
            'status': 'success',
            'customer_id': customer_id,
            'segment_id': assignment.segment_id,
            'confidence': assignment.distance_to_center,
            'assigned_at': assignment.assigned_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get customer segment error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Churn Prediction Endpoints ====================

@router.post("/predictions/churn")
async def predict_churn(
    customer_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Predict churn probability for a customer
    
    Endpoint: POST /api/v1/phase9/predictions/churn?customer_id=123
    """
    try:
        service = PredictiveAnalyticsService(db)
        result = service.predict_churn_risk(customer_id)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return {
            'status': 'success',
            'data': result,
            'timestamp': datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Churn prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predictions/ltv")
async def forecast_ltv(
    customer_id: int,
    forecast_months: int = 12,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Forecast customer lifetime value
    
    Endpoint: POST /api/v1/phase9/predictions/ltv?customer_id=123&forecast_months=12
    """
    try:
        service = PredictiveAnalyticsService(db)
        result = service.forecast_ltv(customer_id, forecast_months)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return {
            'status': 'success',
            'data': result,
            'timestamp': datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LTV forecast error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predictions/anomalies")
async def detect_anomalies(
    metric: str = 'revenue',
    threshold: float = 0.95,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Detect anomalies in customer activity
    
    Endpoint: POST /api/v1/phase9/predictions/anomalies?metric=revenue&threshold=0.95
    """
    try:
        service = PredictiveAnalyticsService(db)
        anomalies = service.detect_anomalies(metric=metric, threshold=threshold)
        
        return {
            'status': 'success',
            'data': anomalies,
            'count': len(anomalies),
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Anomaly detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predictions/train")
async def train_models(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Train/retrain all predictive models
    
    Endpoint: POST /api/v1/phase9/predictions/train
    """
    try:
        service = PredictiveAnalyticsService(db)
        churn_result = service.train_churn_model()
        
        return {
            'status': 'success',
            'churn_model': churn_result,
            'message': 'Models trained successfully',
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Model training error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Recommendation Endpoints ====================

@router.post("/recommendations/generate")
async def generate_recommendations(
    customer_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate personalized recommendations for a customer
    
    Endpoint: POST /api/v1/phase9/recommendations/generate?customer_id=123
    """
    try:
        # Get churn risk and LTV
        predictive = PredictiveAnalyticsService(db)
        churn_data = predictive.predict_churn_risk(customer_id)
        ltv_data = predictive.forecast_ltv(customer_id)
        
        engine = RecommendationEngine(db)
        recommendations = engine.generate_recommendations(
            customer_id,
            churn_risk=churn_data.get('churn_probability'),
            ltv_forecast=ltv_data.get('forecasted_ltv')
        )
        
        return {
            'status': 'success',
            'customer_id': customer_id,
            'recommendations': recommendations,
            'count': len(recommendations),
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Recommendation generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/customer/{customer_id}")
async def get_customer_recommendations(
    customer_id: int,
    limit: int = 5,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recommendations for a customer"""
    try:
        from app.models.phase9_models import Recommendation
        
        recs = db.query(Recommendation).filter_by(
            customer_id=customer_id
        ).order_by(Recommendation.priority_score.desc()).limit(limit).all()
        
        return {
            'status': 'success',
            'customer_id': customer_id,
            'recommendations': [
                {
                    'recommendation_id': r.recommendation_id,
                    'type': r.recommendation_type,
                    'title': r.title,
                    'description': r.description,
                    'impact': r.estimated_impact,
                    'confidence': r.confidence_score,
                    'priority': r.priority_score,
                    'ctr': getattr(r, 'click_through_rate', 0)
                }
                for r in recs
            ]
        }
    except Exception as e:
        logger.error(f"Get recommendations error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations/{recommendation_id}/track")
async def track_recommendation(
    recommendation_id: int,
    action_taken: bool = False,
    conversion: bool = False,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track recommendation interaction"""
    try:
        engine = RecommendationEngine(db)
        result = engine.track_recommendation_performance(
            recommendation_id, action_taken, conversion
        )
        
        return {
            'status': 'success',
            'data': result,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Track recommendation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Real-time Dashboard Endpoints ====================

@router.get("/dashboard/overview")
async def get_dashboard_overview(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard overview metrics"""
    try:
        service = RealtimeDashboardService(db)
        updates = await service.get_streaming_data('overview')
        
        return {
            'status': 'success',
            'data': updates,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Dashboard overview error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/health")
async def get_system_health(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system health metrics"""
    try:
        service = RealtimeDashboardService(db)
        health = await service.stream_system_health()
        
        return health
    except Exception as e:
        logger.error(f"System health error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/dashboard/{client_id}")
async def websocket_dashboard(websocket: WebSocket, client_id: str, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time dashboard
    
    Endpoint: WS /api/v1/phase9/ws/dashboard/{client_id}
    """
    await websocket.accept()
    service = RealtimeDashboardService(db)
    
    try:
        # Connect client
        await service.connect(client_id, user_id=1, dashboard_type='overview')
        
        while True:
            # Receive heartbeat or commands
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                message = json.loads(data)
                
                if message.get('type') == 'heartbeat':
                    service.heartbeat(client_id)
                    await websocket.send_json({
                        'type': 'heartbeat_ack',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                elif message.get('type') == 'subscribe':
                    # Subscribe to metric type
                    pass
                    
            except asyncio.TimeoutError:
                # Send periodic updates
                updates = await service.get_streaming_data('overview')
                
                for update in updates:
                    await websocket.send_json(update)
                
                # Wait before next update
                await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        await service.disconnect(client_id)
        logger.info(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await service.disconnect(client_id)
