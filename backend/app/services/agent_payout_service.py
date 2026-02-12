"""
Phase 16: Agent Payout Service
- Payout scheduling and processing
- Financial reporting and analytics
- Batch payout management
- Threshold and frequency configuration
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import uuid


class AgentPayoutService:
    """Manage payouts to agent developers"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ PAYOUT CONFIGURATION ============
    
    def set_payout_threshold(self, agent_id: str, threshold: float) -> bool:
        """Set minimum payout threshold for an agent"""
        # Stored as metadata in agent settings
        # For now, just validates the threshold is reasonable
        return threshold > 0
    
    def set_payout_frequency(self, agent_id: str, frequency: str) -> bool:
        """Set payout frequency: weekly, monthly, quarterly"""
        valid_frequencies = ["weekly", "monthly", "quarterly"]
        return frequency in valid_frequencies
    
    # ============ PAYMENT METHODS ============
    
    def save_payout_method(
        self,
        agent_id: str,
        user_id: str,
        method_type: str,  # bank_account, stripe, paypal
        account_details: Dict[str, str]
    ) -> bool:
        """Save payout method details"""
        # In production, integrate with Stripe Connect
        if method_type not in ["bank_account", "stripe", "paypal"]:
            return False
        
        # Validate based on method type
        if method_type == "bank_account":
            return "account_number" in account_details and "routing_number" in account_details
        
        return True
    
    # ============ REVENUE CALCULATIONS ============
    
    def calculate_earned_revenue(
        self,
        agent_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """Calculate revenue earned in period"""
        from app.models.agent_monetization_models import AgentSale
        
        sales = self.db.query(AgentSale).filter(
            AgentSale.agent_id == agent_id,
            AgentSale.created_at >= period_start,
            AgentSale.created_at <= period_end,
            AgentSale.status == "completed"
        ).all()
        
        if not sales:
            return {
                "agent_id": agent_id,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "earned_revenue": 0.0,
                "sale_count": 0
            }
        
        earned_revenue = sum(s.agent_revenue for s in sales)
        
        # Subtract refunds
        refunds = sum(s.refund_amount or 0 for s in sales if s.status == "refunded")
        net_revenue = earned_revenue - (refunds * 0.50)  # Author's share of refunds
        
        return {
            "agent_id": agent_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "sale_count": len(sales),
            "gross_revenue": earned_revenue,
            "refund_deductions": refunds * 0.50,
            "earned_revenue": max(0, net_revenue),
            "subscription_revenue": sum(s.agent_revenue for s in sales if s.sale_type == "subscription"),
            "one_time_revenue": sum(s.agent_revenue for s in sales if s.sale_type == "one_time")
        }
    
    def get_pending_payout_amount(self, agent_id: str) -> float:
        """Get amount pending payout"""
        from app.models.agent_monetization_models import AgentSale, AgentPayment
        
        # Get earned revenue since last payout
        last_payout = self.db.query(AgentPayment).filter(
            AgentPayment.agent_id == agent_id,
            AgentPayment.status == "completed"
        ).order_by(desc(AgentPayment.processed_at)).first()
        
        period_start = last_payout.processed_at if last_payout else datetime.utcnow() - timedelta(days=365)
        period_end = datetime.utcnow()
        
        revenue_data = self.calculate_earned_revenue(agent_id, period_start, period_end)
        return revenue_data.get("earned_revenue", 0.0)
    
    # ============ PAYOUT PROCESSING ============
    
    def create_payout(
        self,
        agent_id: str,
        user_id: str,
        amount: float,
        payout_method: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create and queue a payout"""
        from app.models.agent_monetization_models import AgentPayment
        
        # Validate amount
        if amount <= 0:
            raise ValueError("Payout amount must be positive")
        
        payment = AgentPayment(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            user_id=user_id,
            amount=amount,
            payment_type=payout_method,
            status="pending",
            requested_at=datetime.utcnow(),
            notes=notes,
            created_at=datetime.utcnow()
        )
        
        self.db.add(payment)
        self.db.commit()
        
        return {
            "payment_id": payment.id,
            "agent_id": agent_id,
            "amount": amount,
            "status": "pending",
            "requested_at": payment.requested_at.isoformat()
        }
    
    def process_payout_batch(
        self,
        payout_date: datetime,
        stripe_batch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a batch of pending payouts"""
        from app.models.agent_monetization_models import AgentPayment, AgentPayoutBatch
        
        # Get all pending payouts
        pending_payouts = self.db.query(AgentPayment).filter(
            AgentPayment.status == "pending",
            AgentPayment.requested_at <= payout_date
        ).all()
        
        if not pending_payouts:
            return {
                "batch_id": str(uuid.uuid4()),
                "status": "empty",
                "total_payouts": 0,
                "total_amount": 0.0
            }
        
        batch_id = str(uuid.uuid4())
        total_amount = sum(p.amount for p in pending_payouts)
        
        # Create batch record
        batch = AgentPayoutBatch(
            id=batch_id,
            payout_period_start=payout_date - timedelta(days=30),
            payout_period_end=payout_date,
            status="processing",
            total_agents=len(set(p.agent_id for p in pending_payouts)),
            total_amount=total_amount,
            total_payments=len(pending_payouts),
            stripe_batch_id=stripe_batch_id,
            processing_started_at=datetime.utcnow()
        )
        
        self.db.add(batch)
        
        # Update payment statuses
        successful = 0
        failed = 0
        errors = []
        
        for payment in pending_payouts:
            try:
                # In production, integrate with Stripe/PayPal
                payment.status = "completed"
                payment.processed_at = datetime.utcnow()
                successful += 1
            except Exception as e:
                payment.status = "failed"
                failed += 1
                errors.append({
                    "payment_id": payment.id,
                    "error": str(e)
                })
        
        batch.status = "completed" if failed == 0 else "partial"
        batch.successful_count = successful
        batch.failed_count = failed
        batch.errors = errors
        batch.completed_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "batch_id": batch_id,
            "status": batch.status,
            "total_payouts": len(pending_payouts),
            "successful": successful,
            "failed": failed,
            "total_amount": total_amount,
            "completed_at": batch.completed_at.isoformat()
        }
    
    def get_payout_status(self, payment_id: str) -> Dict[str, Any]:
        """Get status of a specific payout"""
        from app.models.agent_monetization_models import AgentPayment
        
        payment = self.db.query(AgentPayment).filter(
            AgentPayment.id == payment_id
        ).first()
        
        if not payment:
            return {"status": "not_found"}
        
        return {
            "payment_id": payment.id,
            "agent_id": payment.agent_id,
            "amount": payment.amount,
            "status": payment.status,
            "requested_at": payment.requested_at.isoformat(),
            "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
            "stripe_transfer_id": payment.stripe_transfer_id
        }
    
    def get_payout_history(
        self,
        agent_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get payout history for an agent"""
        from app.models.agent_monetization_models import AgentPayment
        
        payouts = self.db.query(AgentPayment).filter(
            AgentPayment.agent_id == agent_id,
            AgentPayment.status.in_(["completed", "failed"])
        ).order_by(desc(AgentPayment.processed_at)).limit(limit).all()
        
        return [
            {
                "payment_id": p.id,
                "amount": p.amount,
                "status": p.status,
                "processed_at": p.processed_at.isoformat() if p.processed_at else None,
                "payment_type": p.payment_type
            }
            for p in payouts
        ]
    
    # ============ FINANCIAL REPORTING ============
    
    def generate_monthly_report(self, agent_id: str, month: str) -> Dict[str, Any]:
        """Generate monthly financial report"""
        from app.models.agent_monetization_models import AgentSale, RevenueAnalytics
        
        # Parse month (YYYY-MM)
        year, month_num = month.split("-")
        period_start = datetime(int(year), int(month_num), 1)
        
        if int(month_num) == 12:
            period_end = datetime(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = datetime(int(year), int(month_num) + 1, 1) - timedelta(days=1)
        
        sales = self.db.query(AgentSale).filter(
            AgentSale.agent_id == agent_id,
            AgentSale.created_at >= period_start,
            AgentSale.created_at <= period_end,
            AgentSale.status == "completed"
        ).all()
        
        total_revenue = sum(s.amount for s in sales)
        author_revenue = sum(s.agent_revenue for s in sales)
        
        return {
            "agent_id": agent_id,
            "month": month,
            "total_sales": len(sales),
            "total_revenue": total_revenue,
            "author_revenue": author_revenue,
            "platform_revenue": total_revenue * 0.30,
            "subscription_sales": sum(1 for s in sales if s.sale_type == "subscription"),
            "one_time_sales": sum(1 for s in sales if s.sale_type == "one_time"),
            "refund_count": sum(1 for s in sales if s.status == "refunded"),
            "refund_amount": sum(s.refund_amount or 0 for s in sales if s.status == "refunded"),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat()
        }
    
    def get_yearly_summary(self, agent_id: str, year: int) -> Dict[str, Any]:
        """Get yearly financial summary"""
        from app.models.agent_monetization_models import AgentSale
        
        period_start = datetime(year, 1, 1)
        period_end = datetime(year, 12, 31)
        
        sales = self.db.query(AgentSale).filter(
            AgentSale.agent_id == agent_id,
            AgentSale.created_at >= period_start,
            AgentSale.created_at <= period_end,
            AgentSale.status == "completed"
        ).all()
        
        if not sales:
            return {
                "agent_id": agent_id,
                "year": year,
                "total_revenue": 0.0
            }
        
        total_revenue = sum(s.amount for s in sales)
        
        return {
            "agent_id": agent_id,
            "year": year,
            "total_sales": len(sales),
            "total_revenue": total_revenue,
            "author_revenue": sum(s.agent_revenue for s in sales),
            "average_transaction": total_revenue / len(sales),
            "highest_transaction": max(s.amount for s in sales),
            "monthly_breakdown": self._calculate_monthly_breakdown(sales)
        }
    
    def _calculate_monthly_breakdown(self, sales: list) -> Dict[str, float]:
        """Calculate monthly revenue breakdown"""
        breakdown = {}
        
        for sale in sales:
            month_key = sale.created_at.strftime("%Y-%m")
            breakdown[month_key] = breakdown.get(month_key, 0.0) + sale.agent_revenue
        
        return breakdown
    
    def get_top_agents(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        """Get top performing agents by revenue"""
        from app.models.agent_monetization_models import AgentSale
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        top_agents = self.db.query(
            AgentSale.agent_id,
            func.sum(AgentSale.agent_revenue).label("total_revenue"),
            func.count(AgentSale.id).label("sale_count")
        ).filter(
            AgentSale.created_at >= cutoff_date,
            AgentSale.status == "completed"
        ).group_by(
            AgentSale.agent_id
        ).order_by(
            desc("total_revenue")
        ).limit(limit).all()
        
        return [
            {
                "agent_id": agent_id,
                "revenue": total_revenue,
                "sale_count": sale_count
            }
            for agent_id, total_revenue, sale_count in top_agents
        ]
    
    def get_revenue_trends(self, agent_id: str, days: int = 30) -> Dict[str, Any]:
        """Get revenue trends over time"""
        from app.models.agent_monetization_models import AgentSale
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        sales = self.db.query(AgentSale).filter(
            AgentSale.agent_id == agent_id,
            AgentSale.created_at >= cutoff_date,
            AgentSale.status == "completed"
        ).order_by(AgentSale.created_at).all()
        
        # Group by day
        daily_revenue = {}
        for sale in sales:
            date_key = sale.created_at.date()
            daily_revenue[date_key] = daily_revenue.get(date_key, 0.0) + sale.agent_revenue
        
        dates = sorted(daily_revenue.keys())
        revenues = [daily_revenue[date] for date in dates]
        
        # Calculate trend
        if len(revenues) > 1:
            first_half_avg = sum(revenues[:len(revenues)//2]) / (len(revenues)//2 or 1)
            second_half_avg = sum(revenues[len(revenues)//2:]) / (len(revenues) - len(revenues)//2 or 1)
            trend = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
        else:
            trend = 0
        
        return {
            "agent_id": agent_id,
            "period_days": days,
            "total_revenue": sum(revenues),
            "daily_data": [
                {
                    "date": str(date),
                    "revenue": daily_revenue[date]
                }
                for date in dates
            ],
            "trend_percentage": trend,
            "trend_direction": "increasing" if trend > 5 else "decreasing" if trend < -5 else "stable"
        }
