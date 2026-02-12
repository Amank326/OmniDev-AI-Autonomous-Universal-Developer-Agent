"""
Real-Time Metrics WebSocket Service
====================================

WebSocket support for real-time analytics dashboard updates.
"""

import asyncio
import logging
import json
from typing import Dict, Set, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.orm import Session

from app.database.config import SessionLocal
from app.analytics.models import SystemMetrics, UserActivity, EngagementMetrics
from app.analytics.aggregation import dashboard_service

logger = logging.getLogger(__name__)


class MetricsStreamType(str, Enum):
    """Types of metrics that can be streamed via WebSocket."""
    SYSTEM_HEALTH = "system_health"
    USER_ACTIVITY = "user_activity"
    PROJECT_METRICS = "project_metrics"
    ENGAGEMENT_METRICS = "engagement_metrics"
    DASHBOARD_SUMMARY = "dashboard_summary"


class MetricsStreamFilter:
    """Filter for metrics stream subscriptions."""
    
    def __init__(
        self,
        stream_type: MetricsStreamType,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        interval_seconds: int = 5,
    ):
        """
        Initialize stream filter.
        
        Args:
            stream_type: Type of metrics to stream
            user_id: Filter by user ID (optional)
            project_id: Filter by project ID (optional)
            interval_seconds: Update interval in seconds
        """
        self.stream_type = stream_type
        self.user_id = user_id
        self.project_id = project_id
        self.interval_seconds = max(1, min(interval_seconds, 300))  # 1-300 seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stream_type": self.stream_type.value,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "interval_seconds": self.interval_seconds,
        }


class RealtimeMetricsService:
    """
    Service for streaming real-time metrics via WebSocket.
    """
    
    def __init__(self):
        """Initialize the real-time metrics service."""
        self.active_connections: Dict[str, Set] = {}  # connection_id -> set of filters
        self.db = SessionLocal()
    
    # ========================================================================
    # Connection Management
    # ========================================================================
    
    def register_connection(self, connection_id: str) -> None:
        """
        Register a new WebSocket connection.
        
        Args:
            connection_id: Unique connection ID
        """
        if connection_id not in self.active_connections:
            self.active_connections[connection_id] = set()
            logger.info(f"Registered connection: {connection_id}")
    
    def unregister_connection(self, connection_id: str) -> None:
        """
        Unregister a WebSocket connection.
        
        Args:
            connection_id: Connection ID to remove
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"Unregistered connection: {connection_id}")
    
    def subscribe(
        self,
        connection_id: str,
        stream_filter: MetricsStreamFilter
    ) -> bool:
        """
        Subscribe a connection to a metrics stream.
        
        Args:
            connection_id: Connection ID
            stream_filter: Stream filter with type and parameters
        
        Returns:
            True if subscription added, False if connection not found
        """
        if connection_id not in self.active_connections:
            return False
        
        self.active_connections[connection_id].add(stream_filter)
        logger.info(f"Subscribed {connection_id} to {stream_filter.stream_type.value}")
        return True
    
    def unsubscribe(
        self,
        connection_id: str,
        stream_type: MetricsStreamType
    ) -> bool:
        """
        Unsubscribe connection from a metrics stream.
        
        Args:
            connection_id: Connection ID
            stream_type: Type of stream to unsubscribe from
        
        Returns:
            True if unsubscribed, False if not found
        """
        if connection_id not in self.active_connections:
            return False
        
        # Remove filters matching this stream type
        self.active_connections[connection_id] = {
            f for f in self.active_connections[connection_id]
            if f.stream_type != stream_type
        }
        logger.info(f"Unsubscribed {connection_id} from {stream_type.value}")
        return True
    
    # ========================================================================
    # Metrics Generation
    # ========================================================================
    
    def get_system_health_metrics(self) -> Dict[str, Any]:
        """
        Get current system health metrics.
        
        Returns:
            Dictionary with system metrics
        """
        try:
            metrics = self.db.query(SystemMetrics).order_by(
                SystemMetrics.recorded_at.desc()
            ).first()
            
            return {
                "stream_type": MetricsStreamType.SYSTEM_HEALTH.value,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics.to_dict() if metrics else {},
            }
        except Exception as e:
            logger.error(f"Failed to get system health metrics: {str(e)}")
            return {
                "stream_type": MetricsStreamType.SYSTEM_HEALTH.value,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
    
    def get_user_activity_metrics(
        self,
        user_id: Optional[int] = None,
        minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Get recent user activity metrics.
        
        Args:
            user_id: Optional filter by user
            minutes: Last N minutes of activities
        
        Returns:
            Dictionary with activity metrics
        """
        try:
            cutoff = datetime.utcnow() - timedelta(minutes=minutes)
            
            query = self.db.query(UserActivity).filter(
                UserActivity.timestamp >= cutoff
            )
            
            if user_id:
                query = query.filter(UserActivity.user_id == user_id)
            
            activities = query.all()
            
            # Calculate summary
            total = len(activities)
            successful = sum(1 for a in activities if a.success)
            failed = total - successful
            
            return {
                "stream_type": MetricsStreamType.USER_ACTIVITY.value,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "period_minutes": minutes,
                "summary": {
                    "total_activities": total,
                    "successful": successful,
                    "failed": failed,
                    "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%",
                },
                "recent_activities": [a.to_dict() for a in activities[-20:]],
            }
        except Exception as e:
            logger.error(f"Failed to get user activity metrics: {str(e)}")
            return {
                "stream_type": MetricsStreamType.USER_ACTIVITY.value,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
    
    def get_dashboard_summary(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get dashboard summary metrics.
        
        Args:
            days: Number of days to summarize
        
        Returns:
            Dictionary with dashboard summary
        """
        try:
            # Use the aggregation service
            summary = dashboard_service.get_team_dashboard(days=days, limit=5)
            
            return {
                "stream_type": MetricsStreamType.DASHBOARD_SUMMARY.value,
                "timestamp": datetime.utcnow().isoformat(),
                "data": summary,
            }
        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {str(e)}")
            return {
                "stream_type": MetricsStreamType.DASHBOARD_SUMMARY.value,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
    
    def get_engagement_metrics(
        self,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get top user engagement metrics.
        
        Args:
            limit: Number of top users to return
        
        Returns:
            Dictionary with engagement metrics
        """
        try:
            engagements = self.db.query(EngagementMetrics).order_by(
                EngagementMetrics.overall_engagement_score.desc()
            ).limit(limit).all()
            
            return {
                "stream_type": MetricsStreamType.ENGAGEMENT_METRICS.value,
                "timestamp": datetime.utcnow().isoformat(),
                "top_users": [e.to_dict() for e in engagements],
            }
        except Exception as e:
            logger.error(f"Failed to get engagement metrics: {str(e)}")
            return {
                "stream_type": MetricsStreamType.ENGAGEMENT_METRICS.value,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
    
    # ========================================================================
    # Stream Processing
    # ========================================================================
    
    async def stream_metrics(
        self,
        connection_id: str,
        stream_filter: MetricsStreamFilter,
        send_callback,
    ) -> None:
        """
        Stream metrics to a WebSocket connection.
        
        Args:
            connection_id: Connection ID
            stream_filter: Filter for stream type and parameters
            send_callback: Async callback to send data
        """
        try:
            interval = stream_filter.interval_seconds
            
            while connection_id in self.active_connections:
                # Get appropriate metrics based on stream type
                if stream_filter.stream_type == MetricsStreamType.SYSTEM_HEALTH:
                    metrics = self.get_system_health_metrics()
                
                elif stream_filter.stream_type == MetricsStreamType.USER_ACTIVITY:
                    metrics = self.get_user_activity_metrics(
                        user_id=stream_filter.user_id
                    )
                
                elif stream_filter.stream_type == MetricsStreamType.ENGAGEMENT_METRICS:
                    metrics = self.get_engagement_metrics()
                
                elif stream_filter.stream_type == MetricsStreamType.DASHBOARD_SUMMARY:
                    metrics = self.get_dashboard_summary()
                
                else:
                    metrics = {"error": "Unknown stream type"}
                
                # Send metrics
                try:
                    await send_callback(json.dumps(metrics))
                except Exception as e:
                    logger.error(f"Failed to send metrics: {str(e)}")
                    break
                
                # Wait before next update
                await asyncio.sleep(interval)
        
        except Exception as e:
            logger.error(f"Stream error for {connection_id}: {str(e)}")
        
        finally:
            logger.info(f"Stopped streaming {stream_filter.stream_type.value} to {connection_id}")
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
    
    def get_subscription_count(self, connection_id: str) -> int:
        """Get number of active subscriptions for a connection."""
        return len(self.active_connections.get(connection_id, set()))
    
    def get_all_connections_info(self) -> Dict[str, Any]:
        """Get information about all active connections."""
        return {
            "total_connections": len(self.active_connections),
            "connections": {
                conn_id: {
                    "subscriptions": len(filters),
                    "stream_types": [f.stream_type.value for f in filters],
                }
                for conn_id, filters in self.active_connections.items()
            },
        }
    
    def close(self):
        """Close service and clean up resources."""
        if self.db:
            self.db.close()
            logger.info("Closed RealtimeMetricsService")


# Global service instance
realtime_metrics_service = RealtimeMetricsService()
