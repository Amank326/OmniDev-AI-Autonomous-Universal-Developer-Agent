"""
Phase 15: Agent Monitoring Service
- Agent execution metrics
- Performance tracking
- Cost analysis per agent
- Health monitoring
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import statistics


class AgentMonitoringService:
    """Monitor and analyze agent performance"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ EXECUTION TRACKING ============
    
    def record_agent_execution(
        self,
        agent_id: str,
        deployment_id: str,
        user_id: str,
        prompt: str,
        output: str,
        status: str,
        duration_seconds: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error_message: Optional[str] = None
    ) -> str:
        """Record an agent execution"""
        from app.models.agent_models import AgentExecution
        import uuid
        
        execution_id = str(uuid.uuid4())
        
        execution = AgentExecution(
            id=execution_id,
            agent_id=agent_id,
            user_id=user_id,
            deployment_id=deployment_id,
            prompt=prompt,
            output=output,
            status=status,
            start_time=datetime.utcnow() - timedelta(seconds=duration_seconds),
            end_time=datetime.utcnow(),
            duration_seconds=duration_seconds,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            error_message=error_message,
            created_at=datetime.utcnow()
        )
        
        self.db.add(execution)
        
        # Update agent execution count
        from app.models.agent_models import AIAgent
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if agent:
            agent.executions += 1
            if status == "completed":
                agent.average_execution_time = (
                    agent.average_execution_time * 0.7 +
                    duration_seconds * 0.3
                )
        
        self.db.commit()
        
        return execution_id
    
    def update_agent_stats(self, agent_id: str) -> None:
        """Update aggregated agent statistics"""
        from app.models.agent_models import AIAgent, AgentExecution, AgentPerformance
        from datetime import date
        
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not agent:
            return
        
        # Get today's executions
        today = date.today()
        today_executions = self.db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id,
            func.date(AgentExecution.created_at) == today
        ).all()
        
        if not today_executions:
            return
        
        # Calculate metrics
        successful = sum(1 for e in today_executions if e.status == "completed")
        failed = sum(1 for e in today_executions if e.status == "failed")
        total_duration = sum(e.duration_seconds for e in today_executions if e.duration_seconds)
        total_tokens = sum(e.total_tokens for e in today_executions)
        
        # Create performance record
        performance = AgentPerformance(
            id=f"{agent_id}_{today}",
            agent_id=agent_id,
            metric_date=str(today),
            execution_count=len(today_executions),
            successful_executions=successful,
            failed_executions=failed,
            total_execution_time=total_duration,
            average_execution_time=total_duration / len(today_executions) if today_executions else 0,
            total_tokens_used=total_tokens,
            success_rate=(successful / len(today_executions) * 100) if today_executions else 0,
            error_rate=(failed / len(today_executions) * 100) if today_executions else 0,
            created_at=datetime.utcnow()
        )
        
        self.db.merge(performance)
        
        # Update agent-level stats
        agent.success_rate = (successful / len(today_executions) * 100) if today_executions else agent.success_rate
        agent.error_rate = (failed / len(today_executions) * 100) if today_executions else agent.error_rate
        
        self.db.commit()
    
    # ============ PERFORMANCE METRICS ============
    
    def get_agent_performance(
        self,
        agent_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get agent performance over time period"""
        from app.models.agent_models import AgentPerformance
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()
        
        performance = self.db.query(AgentPerformance).filter(
            AgentPerformance.agent_id == agent_id,
            AgentPerformance.metric_date >= str(cutoff_date)
        ).order_by(AgentPerformance.metric_date).all()
        
        if not performance:
            return {
                "agent_id": agent_id,
                "metrics": [],
                "period_days": days
            }
        
        # Calculate aggregates
        total_executions = sum(p.execution_count for p in performance)
        total_successful = sum(p.successful_executions for p in performance)
        total_tokens = sum(p.total_tokens_used for p in performance)
        
        avg_success_rate = (
            sum(p.success_rate * p.execution_count for p in performance) / total_executions
            if total_executions > 0 else 0
        )
        
        avg_duration = (
            sum(p.average_execution_time * p.execution_count for p in performance) / total_executions
            if total_executions > 0 else 0
        )
        
        return {
            "agent_id": agent_id,
            "period_days": days,
            "total_executions": total_executions,
            "successful_executions": total_successful,
            "success_rate": avg_success_rate,
            "average_execution_time_seconds": avg_duration,
            "total_tokens_used": total_tokens,
            "daily_metrics": [
                {
                    "date": p.metric_date,
                    "executions": p.execution_count,
                    "success_rate": p.success_rate,
                    "avg_duration": p.average_execution_time,
                    "tokens_used": p.total_tokens_used
                }
                for p in performance
            ]
        }
    
    def get_percentile_metrics(self, agent_id: str, days: int = 30) -> Dict[str, Any]:
        """Get execution time percentiles"""
        from app.models.agent_models import AgentExecution
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        executions = self.db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id,
            AgentExecution.created_at >= cutoff_date,
            AgentExecution.status == "completed"
        ).all()
        
        if not executions:
            return {}
        
        durations = sorted([e.duration_seconds for e in executions if e.duration_seconds])
        
        if not durations:
            return {}
        
        return {
            "agent_id": agent_id,
            "p50": durations[int(len(durations) * 0.5)],
            "p95": durations[int(len(durations) * 0.95)],
            "p99": durations[int(len(durations) * 0.99)],
            "min": min(durations),
            "max": max(durations),
            "avg": sum(durations) / len(durations),
            "stddev": statistics.stdev(durations) if len(durations) > 1 else 0,
            "sample_count": len(durations)
        }
    
    # ============ HEALTH MONITORING ============
    
    def check_agent_health(self, agent_id: str) -> Dict[str, Any]:
        """Check current agent health status"""
        from app.models.agent_models import AIAgent, AgentExecution
        
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not agent:
            return {"status": "unknown"}
        
        # Check recent executions (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent = self.db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id,
            AgentExecution.created_at >= recent_cutoff
        ).all()
        
        if not recent:
            return {
                "status": "idle",
                "agent_id": agent_id,
                "last_seen": agent.updated_at.isoformat() if agent.updated_at else None
            }
        
        # Calculate health score
        success_count = sum(1 for e in recent if e.status == "completed")
        success_rate = (success_count / len(recent) * 100) if recent else 0
        
        # Determine health status
        if success_rate >= 95:
            status = "healthy"
        elif success_rate >= 80:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "agent_id": agent_id,
            "executions_24h": len(recent),
            "success_rate": success_rate,
            "last_execution": recent[-1].created_at.isoformat() if recent else None
        }
    
    def get_agent_health_history(self, agent_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get agent health status over time"""
        from app.models.agent_models import AgentExecution
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        executions = self.db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id,
            AgentExecution.created_at >= cutoff_date
        ).order_by(AgentExecution.created_at).all()
        
        # Group by day
        daily_health = {}
        for execution in executions:
            date_key = execution.created_at.date()
            if date_key not in daily_health:
                daily_health[date_key] = {"total": 0, "successful": 0}
            
            daily_health[date_key]["total"] += 1
            if execution.status == "completed":
                daily_health[date_key]["successful"] += 1
        
        # Convert to list
        return [
            {
                "date": str(date),
                "executions": counts["total"],
                "success_rate": (counts["successful"] / counts["total"] * 100) if counts["total"] > 0 else 0,
                "status": "healthy" if (counts["successful"] / counts["total"] * 100 >= 95) else "degraded"
            }
            for date, counts in sorted(daily_health.items())
        ]
    
    # ============ COST ANALYSIS ============
    
    def calculate_agent_cost(
        self,
        agent_id: str,
        input_tokens: int,
        output_tokens: int,
        deployment_id: Optional[str] = None
    ) -> Dict[str, float]:
        """Calculate execution cost for an agent"""
        from app.models.agent_models import AIAgent, AgentDeployment
        
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not agent:
            return {"total_cost": 0.0}
        
        # Base cost per execution
        base_cost = agent.base_cost_per_execution
        
        # Token cost
        token_cost = (
            (input_tokens + output_tokens) / 1000 * agent.token_cost_per_1k
        )
        
        total_cost = base_cost + token_cost
        
        return {
            "base_cost": base_cost,
            "token_cost": token_cost,
            "total_cost": total_cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }
    
    def get_agent_cost_analytics(self, agent_id: str, days: int = 30) -> Dict[str, Any]:
        """Get cost analytics for an agent"""
        from app.models.agent_models import AgentExecution
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        executions = self.db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id,
            AgentExecution.created_at >= cutoff_date
        ).all()
        
        if not executions:
            return {
                "agent_id": agent_id,
                "period_days": days,
                "total_cost": 0.0,
                "executions": 0
            }
        
        total_cost = sum(e.estimated_cost or 0 for e in executions)
        total_tokens = sum(e.total_tokens or 0 for e in executions)
        
        # Calculate cost trends
        daily_costs = {}
        for execution in executions:
            date_key = execution.created_at.date()
            if date_key not in daily_costs:
                daily_costs[date_key] = 0.0
            daily_costs[date_key] += execution.estimated_cost or 0
        
        return {
            "agent_id": agent_id,
            "period_days": days,
            "total_cost": total_cost,
            "total_executions": len(executions),
            "cost_per_execution": total_cost / len(executions) if executions else 0,
            "total_tokens": total_tokens,
            "average_tokens_per_execution": total_tokens / len(executions) if executions else 0,
            "daily_costs": [
                {
                    "date": str(date),
                    "cost": cost,
                    "executions": sum(1 for e in executions if e.created_at.date() == date)
                }
                for date, cost in sorted(daily_costs.items())
            ],
            "cost_trend": self._calculate_cost_trend(sorted(daily_costs.items()))
        }
    
    def _calculate_cost_trend(self, daily_data: List[tuple]) -> str:
        """Calculate cost trend (increasing, stable, decreasing)"""
        if len(daily_data) < 2:
            return "stable"
        
        first_half_avg = sum(cost for _, cost in daily_data[:len(daily_data)//2]) / (len(daily_data)//2 or 1)
        second_half_avg = sum(cost for _, cost in daily_data[len(daily_data)//2:]) / (len(daily_data) - len(daily_data)//2 or 1)
        
        change_percent = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
        
        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    # ============ ERROR TRACKING ============
    
    def get_error_analytics(self, agent_id: str, days: int = 30) -> Dict[str, Any]:
        """Get error analytics for an agent"""
        from app.models.agent_models import AgentExecution
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        failed_executions = self.db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id,
            AgentExecution.status == "failed",
            AgentExecution.created_at >= cutoff_date
        ).all()
        
        if not failed_executions:
            return {
                "agent_id": agent_id,
                "total_errors": 0,
                "error_types": []
            }
        
        # Group by error type
        error_types = {}
        for execution in failed_executions:
            error_type = execution.error_type or "unknown"
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "agent_id": agent_id,
            "total_errors": len(failed_executions),
            "error_rate": (len(failed_executions) / (len(failed_executions) + 
                self.db.query(AgentExecution).filter(
                    AgentExecution.agent_id == agent_id,
                    AgentExecution.status == "completed",
                    AgentExecution.created_at >= cutoff_date
                ).count()) * 100),
            "error_types": [
                {
                    "type": error_type,
                    "count": count,
                    "percentage": (count / len(failed_executions) * 100) if failed_executions else 0
                }
                for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)
            ],
            "recent_errors": [
                {
                    "execution_id": e.id,
                    "error_type": e.error_type,
                    "error_message": e.error_message,
                    "timestamp": e.created_at.isoformat()
                }
                for e in failed_executions[-5:]
            ]
        }
