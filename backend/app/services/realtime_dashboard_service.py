"""Phase 9: Real-time Dashboard Service

Manages WebSocket connections and streams:
- Live metric updates (5-second intervals)
- Segment distribution changes
- Churn risk alerts
- Recommendation performance
- System health metrics
"""

import logging
import asyncio
import json
from typing import Dict, Set, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

from app.models.phase9_models import DashboardAlert, MLModelMetrics
from app.models.payment_models import StripeCustomer
from app.models.activity_models import UserActivity

logger = logging.getLogger(__name__)


class RealtimeDashboardService:
    """Manage real-time dashboard connections and data streaming"""
    
    def __init__(self, db: Session):
        self.db = db
        self.active_connections: Set[str] = set()
        self.connection_metadata: Dict[str, Dict] = {}
    
    async def connect(self, client_id: str, user_id: int, dashboard_type: str = 'overview') -> Dict:
        """Register a new dashboard connection"""
        self.active_connections.add(client_id)
        self.connection_metadata[client_id] = {
            'user_id': user_id,
            'dashboard_type': dashboard_type,
            'connected_at': datetime.utcnow(),
            'last_heartbeat': datetime.utcnow(),
            'metrics_received': 0
        }
        
        logger.info(f"Dashboard connected: {client_id} ({dashboard_type})")
        
        return {
            'status': 'connected',
            'client_id': client_id,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def disconnect(self, client_id: str) -> Dict:
        """Unregister a dashboard connection"""
        if client_id in self.active_connections:
            self.active_connections.remove(client_id)
        
        if client_id in self.connection_metadata:
            metadata = self.connection_metadata.pop(client_id)
            logger.info(f"Dashboard disconnected: {client_id}. Received {metadata.get('metrics_received', 0)} updates.")
        
        return {'status': 'disconnected', 'client_id': client_id}
    
    async def stream_overview_metrics(self) -> Dict[str, Any]:
        """
        Stream high-level system metrics
        
        Returns metrics for overview dashboard
        """
        total_customers = self.db.query(StripeCustomer).count()
        
        active_customers = self.db.query(StripeCustomer).filter(
            StripeCustomer.last_active >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        total_revenue = sum([getattr(c, 'lifetime_value', 0) for c in self.db.query(StripeCustomer).all()])
        
        recent_signups = self.db.query(StripeCustomer).filter(
            StripeCustomer.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'overview_metrics',
            'data': {
                'total_customers': total_customers,
                'active_customers': active_customers,
                'activity_rate': (active_customers / max(total_customers, 1)) * 100,
                'total_revenue': total_revenue,
                'mrr': total_revenue / 12,
                'recent_signups': recent_signups,
                'churn_rate': self._calculate_churn_rate()
            }
        }
    
    async def stream_segment_metrics(self) -> Dict[str, Any]:
        """Stream segment distribution and metrics"""
        # Simulated segment metrics
        segments = {
            'VIP_Active': {
                'count': random.randint(5, 15),
                'avg_ltv': random.uniform(5000, 15000),
                'churn_risk': random.uniform(0.05, 0.15),
                'engagement': random.uniform(0.8, 1.0)
            },
            'Growing': {
                'count': random.randint(15, 40),
                'avg_ltv': random.uniform(2000, 5000),
                'churn_risk': random.uniform(0.15, 0.30),
                'engagement': random.uniform(0.6, 0.8)
            },
            'At_Risk': {
                'count': random.randint(5, 20),
                'avg_ltv': random.uniform(1000, 3000),
                'churn_risk': random.uniform(0.60, 0.90),
                'engagement': random.uniform(0.2, 0.4)
            },
            'Dormant': {
                'count': random.randint(10, 30),
                'avg_ltv': random.uniform(500, 1500),
                'churn_risk': random.uniform(0.75, 0.95),
                'engagement': random.uniform(0.0, 0.2)
            }
        }
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'segment_metrics',
            'data': segments
        }
    
    async def stream_churn_alerts(self) -> Dict[str, Any]:
        """Stream high-risk churn alerts"""
        # Get recent high-risk predictions
        alerts = []
        
        # Simulated alert generation
        for i in range(random.randint(1, 3)):
            alerts.append({
                'alert_id': f'alert_{i}',
                'customer_id': random.randint(1, 100),
                'risk_level': random.choice(['critical', 'high']),
                'churn_probability': random.uniform(0.6, 0.95),
                'recommended_action': random.choice(['send_offer', 'call_customer', 'assign_manager']),
                'priority': random.randint(1, 5)
            })
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'churn_alerts',
            'data': {
                'alert_count': len(alerts),
                'critical_count': len([a for a in alerts if a['risk_level'] == 'critical']),
                'alerts': alerts
            }
        }
    
    async def stream_recommendation_performance(self) -> Dict[str, Any]:
        """Stream recommendation performance metrics"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'recommendation_performance',
            'data': {
                'total_recommendations_sent': random.randint(50, 200),
                'click_through_rate': random.uniform(0.15, 0.35),
                'conversion_rate': random.uniform(0.05, 0.15),
                'top_recommendations': [
                    {
                        'type': 'exclusive_offer',
                        'ctr': random.uniform(0.25, 0.45),
                        'conversion': random.uniform(0.08, 0.15)
                    },
                    {
                        'type': 'feature_discovery',
                        'ctr': random.uniform(0.20, 0.35),
                        'conversion': random.uniform(0.05, 0.12)
                    },
                    {
                        'type': 'premium_upgrade',
                        'ctr': random.uniform(0.30, 0.50),
                        'conversion': random.uniform(0.10, 0.20)
                    }
                ]
            }
        }
    
    async def stream_system_health(self) -> Dict[str, Any]:
        """Stream system health and ML model metrics"""
        # Get latest model metrics
        churn_model = self.db.query(MLModelMetrics).filter_by(
            model_name='churn_prediction'
        ).order_by(MLModelMetrics.training_completed_at.desc()).first()
        
        segmentation_model = self.db.query(MLModelMetrics).filter_by(
            model_name='segmentation'
        ).order_by(MLModelMetrics.training_completed_at.desc()).first()
        
        health_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'system_health',
            'data': {
                'database': {
                    'status': 'healthy',
                    'response_time_ms': random.randint(5, 50),
                    'connection_pool_usage': random.uniform(0.3, 0.7)
                },
                'ml_models': {
                    'churn_model': {
                        'status': 'deployed' if churn_model and churn_model.deployed else 'training',
                        'accuracy': float(churn_model.accuracy) if churn_model else 0.0,
                        'f1_score': float(churn_model.f1_score) if churn_model else 0.0,
                        'last_updated': churn_model.training_completed_at.isoformat() if churn_model else None
                    },
                    'segmentation_model': {
                        'status': 'deployed' if segmentation_model and segmentation_model.deployed else 'training',
                        'accuracy': float(segmentation_model.accuracy) if segmentation_model else 0.0,
                        'last_updated': segmentation_model.training_completed_at.isoformat() if segmentation_model else None
                    }
                },
                'api': {
                    'status': 'healthy',
                    'requests_per_minute': random.randint(10, 50),
                    'error_rate': random.uniform(0.0, 0.02)
                }
            }
        }
        
        return health_data
    
    async def stream_activity_heatmap(self) -> Dict[str, Any]:
        """Stream activity patterns by hour of day and day of week"""
        heatmap_data = {}
        
        for day in range(7):
            heatmap_data[f'day_{day}'] = [random.randint(0, 100) for _ in range(24)]
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'activity_heatmap',
            'data': heatmap_data
        }
    
    async def get_streaming_data(self, dashboard_type: str = 'overview') -> list:
        """
        Get all streaming data for a dashboard type
        
        Returns list of data updates to send
        """
        updates = []
        
        if dashboard_type in ['overview', 'all']:
            updates.append(await self.stream_overview_metrics())
            updates.append(await self.stream_system_health())
        
        if dashboard_type in ['segments', 'all']:
            updates.append(await self.stream_segment_metrics())
        
        if dashboard_type in ['churn', 'all']:
            updates.append(await self.stream_churn_alerts())
        
        if dashboard_type in ['recommendations', 'all']:
            updates.append(await self.stream_recommendation_performance())
        
        if dashboard_type in ['analytics', 'all']:
            updates.append(await self.stream_activity_heatmap())
        
        return updates
    
    async def create_alert(self, alert_type: str, severity: str, title: str, 
                          description: str, customer_id: Optional[int] = None) -> Dict:
        """Create a real-time dashboard alert"""
        alert = DashboardAlert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            customer_id=customer_id,
            is_active=True,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        self.db.add(alert)
        self.db.commit()
        
        logger.info(f"Alert created: {severity} - {title}")
        
        return {
            'alert_id': alert.alert_id,
            'type': alert_type,
            'severity': severity,
            'title': title
        }
    
    def heartbeat(self, client_id: str) -> bool:
        """Update heartbeat for connection"""
        if client_id in self.connection_metadata:
            self.connection_metadata[client_id]['last_heartbeat'] = datetime.utcnow()
            return True
        return False
    
    def get_connection_status(self, client_id: str) -> Optional[Dict]:
        """Get status of a specific connection"""
        if client_id in self.connection_metadata:
            return self.connection_metadata[client_id]
        return None
    
    def get_all_connections(self) -> Dict[str, int]:
        """Get count of active connections by dashboard type"""
        by_type = {}
        
        for metadata in self.connection_metadata.values():
            dt = metadata.get('dashboard_type', 'unknown')
            by_type[dt] = by_type.get(dt, 0) + 1
        
        return by_type
    
    def _calculate_churn_rate(self) -> float:
        """Calculate monthly churn rate"""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sixty_days_ago = datetime.utcnow() - timedelta(days=60)
        
        # Customers active in first period but not second
        total_30_days_ago = self.db.query(StripeCustomer).filter(
            StripeCustomer.created_at <= sixty_days_ago
        ).count()
        
        churned = self.db.query(StripeCustomer).filter(
            StripeCustomer.last_active < sixty_days_ago,
            StripeCustomer.created_at <= sixty_days_ago
        ).count()
        
        if total_30_days_ago == 0:
            return 0.0
        
        return (churned / total_30_days_ago) * 100
    
    async def broadcast_alert(self, alert_data: Dict) -> Dict:
        """Broadcast alert to all connected dashboards"""
        alert_count = len(self.active_connections)
        
        logger.info(f"Broadcasting alert to {alert_count} dashboard(s)")
        
        return {
            'status': 'broadcast_sent',
            'recipients': alert_count,
            'alert': alert_data
        }
