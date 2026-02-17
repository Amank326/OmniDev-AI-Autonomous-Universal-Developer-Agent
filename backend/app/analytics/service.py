"""Analytics service for tracking platform usage and metrics."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User
from app.models.agent import Agent, AgentTask, AgentStatus
from app.models.subscription import Subscription, SubscriptionPlan

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for platform analytics and metrics."""

    async def get_platform_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get overall platform statistics."""
        # Total users
        user_count = await db.execute(select(func.count(User.id)))
        total_users = user_count.scalar() or 0

        # Active users
        active_count = await db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_count.scalar() or 0

        # Total agents
        agent_count = await db.execute(select(func.count(Agent.id)))
        total_agents = agent_count.scalar() or 0

        # Total tasks
        task_count = await db.execute(select(func.count(AgentTask.id)))
        total_tasks = task_count.scalar() or 0

        # Completed tasks
        completed_count = await db.execute(
            select(func.count(AgentTask.id)).where(
                AgentTask.status == AgentStatus.COMPLETED
            )
        )
        completed_tasks = completed_count.scalar() or 0

        # Subscription breakdown
        sub_counts = await db.execute(
            select(Subscription.plan, func.count(Subscription.id)).group_by(
                Subscription.plan
            )
        )
        subscription_breakdown = {
            str(plan): count for plan, count in sub_counts.all()
        }

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_agents": total_agents,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "task_success_rate": (
                round(completed_tasks / total_tasks * 100, 2)
                if total_tasks > 0
                else 0
            ),
            "subscription_breakdown": subscription_breakdown,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_user_activity(
        self, db: AsyncSession, user_id: int
    ) -> Dict[str, Any]:
        """Get activity metrics for a specific user."""
        task_count = await db.execute(
            select(func.count(AgentTask.id)).where(AgentTask.agent_id.in_(
                select(Agent.id)
            ))
        )
        total_tasks = task_count.scalar() or 0

        return {
            "user_id": user_id,
            "total_tasks": total_tasks,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


analytics_service = AnalyticsService()
