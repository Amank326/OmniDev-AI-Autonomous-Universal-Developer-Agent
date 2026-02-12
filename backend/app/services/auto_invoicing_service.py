"""
Auto Invoicing Service - Automate recurring invoice generation based on subscriptions
Handles subscription billing cycles, recurring invoices, and automated payment collection
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BillingCycle(str, Enum):
    """Billing cycle types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"


class InvoiceStatus(str, Enum):
    """Recurring invoice status"""
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    DRAFT = "draft"


class SubscriptionModel(Base):
    """SQLAlchemy model for subscriptions"""
    __tablename__ = "subscriptions"
    
    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey("customers.id"))
    agent_id = Column(String(36), ForeignKey("agents.id"))
    amount = Column(Float)
    currency = Column(String(3), default="USD")
    billing_cycle = Column(String(20))
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    next_billing_date = Column(DateTime)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class AutoInvoicingService:
    """
    Service for automated recurring invoice generation and subscription billing.
    Manages subscription lifecycle, billing cycles, and recurring invoices.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize auto-invoicing service"""
        self.db = db
        self.subscriptions = {}
        self.recurring_invoices = {}
        self.billing_logs = {}
        self.subscription_counter = 1000
        self.invoice_counter = 2000
        
        # Billing cycle intervals (days)
        self.cycle_intervals = {
            BillingCycle.DAILY: 1,
            BillingCycle.WEEKLY: 7,
            BillingCycle.MONTHLY: 30,
            BillingCycle.QUARTERLY: 90,
            BillingCycle.ANNUAL: 365,
        }
    
    def create_subscription(
        self,
        customer_id: str,
        agent_id: str,
        amount: float,
        currency: str,
        billing_cycle: BillingCycle,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Create subscription for recurring billing.
        Establishes automatic invoice generation schedule.
        
        Args:
            customer_id: Customer subscribing
            agent_id: Agent being subscribed to
            amount: Recurring payment amount
            currency: Currency code
            billing_cycle: Frequency (daily, weekly, monthly, etc.)
            start_date: Subscription start
            end_date: Optional end date
            metadata: Additional subscription data
        
        Returns:
            Subscription details
        """
        self.subscription_counter += 1
        subscription_id = f"sub_{self.subscription_counter}"
        start = start_date or datetime.utcnow()
        
        # Calculate next billing date
        cycle_days = self.cycle_intervals.get(billing_cycle, 30)
        next_billing = start + timedelta(days=cycle_days)
        
        subscription = {
            "id": subscription_id,
            "customer_id": customer_id,
            "agent_id": agent_id,
            "amount": amount,
            "currency": currency,
            "billing_cycle": billing_cycle.value,
            "start_date": start.isoformat(),
            "end_date": end_date.isoformat() if end_date else None,
            "next_billing_date": next_billing.isoformat(),
            "status": InvoiceStatus.ACTIVE.value,
            "invoices_generated": 0,
            "total_revenue": 0.0,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        self.subscriptions[subscription_id] = subscription
        return subscription
    
    def schedule_invoices(
        self,
        subscription_id: str,
        num_cycles: int = 12,
        auto_charge: bool = True,
    ) -> Dict:
        """
        Schedule invoices for subscription over multiple cycles.
        Pre-generates invoice schedule without creating actual invoices.
        
        Args:
            subscription_id: Subscription ID
            num_cycles: Number of billing cycles to schedule
            auto_charge: Auto-charge customers on due date
        
        Returns:
            Invoice schedule with dates and amounts
        """
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        sub = self.subscriptions[subscription_id]
        cycle_days = self.cycle_intervals.get(sub["billing_cycle"], 30)
        
        schedule_id = f"sch_{subscription_id}_{len(self.recurring_invoices)}"
        
        # Generate invoice schedule
        invoices = []
        current_date = datetime.fromisoformat(sub["next_billing_date"])
        
        for cycle in range(1, num_cycles + 1):
            invoice = {
                "cycle": cycle,
                "scheduled_date": current_date.isoformat(),
                "amount": sub["amount"],
                "currency": sub["currency"],
                "status": "scheduled",
                "auto_charge": auto_charge,
            }
            invoices.append(invoice)
            current_date += timedelta(days=cycle_days)
        
        schedule = {
            "schedule_id": schedule_id,
            "subscription_id": subscription_id,
            "num_cycles": num_cycles,
            "cycle_days": cycle_days,
            "invoices": invoices,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self.recurring_invoices[schedule_id] = schedule
        return schedule
    
    def generate_recurring_invoice(
        self,
        subscription_id: str,
        attempt_payment: bool = True,
    ) -> Dict:
        """
        Generate invoice for current billing cycle.
        Creates actual invoice and attempts payment if enabled.
        
        Args:
            subscription_id: Subscription ID
            attempt_payment: Auto-attempt payment collection
        
        Returns:
            Generated invoice details
        """
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        sub = self.subscriptions[subscription_id]
        
        if sub["status"] != InvoiceStatus.ACTIVE.value:
            raise ValueError(f"Subscription {subscription_id} is not active")
        
        self.invoice_counter += 1
        invoice_id = f"inv_rec_{self.invoice_counter}"
        
        # Create invoice
        invoice = {
            "invoice_id": invoice_id,
            "invoice_number": f"REC-{self.invoice_counter}",
            "subscription_id": subscription_id,
            "customer_id": sub["customer_id"],
            "agent_id": sub["agent_id"],
            "amount": sub["amount"],
            "currency": sub["currency"],
            "issued_date": datetime.utcnow().isoformat(),
            "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "status": "issued",
            "payment_attempted": attempt_payment,
            "payment_status": "pending",
        }
        
        # Update subscription
        cycle_days = self.cycle_intervals.get(sub["billing_cycle"], 30)
        sub["next_billing_date"] = (
            datetime.fromisoformat(sub["next_billing_date"]) + 
            timedelta(days=cycle_days)
        ).isoformat()
        sub["invoices_generated"] += 1
        sub["total_revenue"] += sub["amount"]
        sub["updated_at"] = datetime.utcnow().isoformat()
        
        # Attempt payment if enabled
        payment_result = None
        if attempt_payment:
            payment_result = self._attempt_payment(invoice)
            invoice["payment_status"] = payment_result["status"]
        
        # Log billing event
        self._log_billing_event(subscription_id, "invoice_generated", invoice_id)
        
        return {
            "invoice": invoice,
            "payment_result": payment_result,
            "next_billing_date": sub["next_billing_date"],
        }
    
    def apply_subscription_pricing(
        self,
        subscription_id: str,
        new_amount: float,
        effective_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Change subscription price (mid-cycle adjustment).
        Applies new pricing from specified date forward.
        
        Args:
            subscription_id: Subscription ID
            new_amount: New billing amount
            effective_date: Date change takes effect
        
        Returns:
            Updated subscription
        """
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        sub = self.subscriptions[subscription_id]
        old_amount = sub["amount"]
        
        effective = effective_date or datetime.utcnow()
        
        # Calculate proration if mid-cycle
        proration_data = self._calculate_proration(sub, new_amount, effective)
        
        sub["amount"] = new_amount
        sub["price_changed_date"] = effective.isoformat()
        sub["price_change_history"] = sub.get("price_change_history", [])
        sub["price_change_history"].append({
            "old_amount": old_amount,
            "new_amount": new_amount,
            "effective_date": effective.isoformat(),
            "proration": proration_data,
        })
        
        self._log_billing_event(
            subscription_id, 
            "price_changed", 
            f"from ${old_amount} to ${new_amount}"
        )
        
        return {
            "subscription_id": subscription_id,
            "old_amount": old_amount,
            "new_amount": new_amount,
            "effective_date": effective.isoformat(),
            "proration": proration_data,
        }
    
    def _calculate_proration(
        self,
        subscription: Dict,
        new_amount: float,
        effective_date: datetime,
    ) -> Dict:
        """Calculate proration for mid-cycle price changes"""
        next_billing = datetime.fromisoformat(subscription["next_billing_date"])
        days_remaining = (next_billing - effective_date).days
        cycle_days = self.cycle_intervals.get(subscription["billing_cycle"], 30)
        
        old_amount = subscription["amount"]
        
        # Prorated adjustments
        old_daily = old_amount / cycle_days
        new_daily = new_amount / cycle_days
        
        old_prorated = old_daily * days_remaining
        new_prorated = new_daily * days_remaining
        credit = old_prorated - new_prorated
        
        return {
            "old_prorated_amount": round(old_prorated, 2),
            "new_prorated_amount": round(new_prorated, 2),
            "credit_to_apply": round(credit, 2),
            "days_remaining": days_remaining,
        }
    
    def pause_subscription(
        self,
        subscription_id: str,
        pause_until: Optional[datetime] = None,
    ) -> Dict:
        """
        Pause subscription (stop invoicing temporarily).
        Resume on specified date or manually.
        
        Args:
            subscription_id: Subscription ID
            pause_until: Date to automatically resume
        
        Returns:
            Updated subscription
        """
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        sub = self.subscriptions[subscription_id]
        sub["status"] = InvoiceStatus.PAUSED.value
        sub["paused_at"] = datetime.utcnow().isoformat()
        sub["pause_until"] = pause_until.isoformat() if pause_until else None
        
        self._log_billing_event(subscription_id, "paused")
        
        return sub
    
    def resume_subscription(self, subscription_id: str) -> Dict:
        """Resume paused subscription"""
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        sub = self.subscriptions[subscription_id]
        sub["status"] = InvoiceStatus.ACTIVE.value
        sub["resumed_at"] = datetime.utcnow().isoformat()
        
        self._log_billing_event(subscription_id, "resumed")
        
        return sub
    
    def cancel_subscription(
        self,
        subscription_id: str,
        reason: str = "",
        refund_unused: bool = False,
    ) -> Dict:
        """
        Cancel subscription (end recurring billing).
        Optionally refund unused portion.
        
        Args:
            subscription_id: Subscription ID
            reason: Cancellation reason
            refund_unused: Refund prorated unused amount
        
        Returns:
            Cancellation summary
        """
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        sub = self.subscriptions[subscription_id]
        old_status = sub["status"]
        sub["status"] = InvoiceStatus.CANCELLED.value
        sub["cancelled_at"] = datetime.utcnow().isoformat()
        sub["cancellation_reason"] = reason
        
        # Calculate refund if enabled
        refund = None
        if refund_unused:
            refund = self._calculate_refund(sub)
        
        self._log_billing_event(
            subscription_id, 
            "cancelled",
            f"reason: {reason}"
        )
        
        return {
            "subscription_id": subscription_id,
            "cancelled_at": sub["cancelled_at"],
            "cancellation_reason": reason,
            "refund": refund,
            "total_invoices": sub.get("invoices_generated", 0),
            "lifetime_value": sub.get("total_revenue", 0),
        }
    
    def _calculate_refund(self, subscription: Dict) -> Dict:
        """Calculate refund for unused subscription time"""
        next_billing = datetime.fromisoformat(subscription["next_billing_date"])
        now = datetime.utcnow()
        days_remaining = (next_billing - now).days
        cycle_days = self.cycle_intervals.get(subscription["billing_cycle"], 30)
        
        daily_rate = subscription["amount"] / cycle_days
        refund_amount = daily_rate * days_remaining
        
        return {
            "amount": round(refund_amount, 2),
            "currency": subscription["currency"],
            "days_remaining": days_remaining,
            "reason": "unused_subscription_time",
        }
    
    def track_billing_cycles(
        self,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Dict:
        """
        Track billing cycle metrics for customer or agent.
        Shows revenue, churn, upgrade/downgrade patterns.
        
        Args:
            customer_id: Optional customer filter
            agent_id: Optional agent filter
        
        Returns:
            Billing cycle metrics
        """
        active_subs = 0
        paused_subs = 0
        cancelled_subs = 0
        
        total_mrr = 0.0  # Monthly recurring revenue
        total_arr = 0.0  # Annual recurring revenue
        
        revenue_by_cycle = {}
        
        for sub in self.subscriptions.values():
            if customer_id and sub["customer_id"] != customer_id:
                continue
            if agent_id and sub["agent_id"] != agent_id:
                continue
            
            status = sub["status"]
            if status == InvoiceStatus.ACTIVE.value:
                active_subs += 1
            elif status == InvoiceStatus.PAUSED.value:
                paused_subs += 1
            elif status == InvoiceStatus.CANCELLED.value:
                cancelled_subs += 1
            
            # Calculate MRR and ARR
            if status == InvoiceStatus.ACTIVE.value:
                cycle = sub["billing_cycle"]
                if cycle == BillingCycle.MONTHLY.value:
                    total_mrr += sub["amount"]
                    total_arr += sub["amount"] * 12
                elif cycle == BillingCycle.ANNUAL.value:
                    total_arr += sub["amount"]
                    total_mrr += sub["amount"] / 12
                elif cycle == BillingCycle.WEEKLY.value:
                    total_mrr += sub["amount"] * 52 / 12
                    total_arr += sub["amount"] * 52
            
            # Revenue by cycle type
            cycle = sub["billing_cycle"]
            revenue_by_cycle[cycle] = revenue_by_cycle.get(cycle, 0) + sub["amount"]
        
        return {
            "active_subscriptions": active_subs,
            "paused_subscriptions": paused_subs,
            "cancelled_subscriptions": cancelled_subs,
            "total_subscriptions": active_subs + paused_subs + cancelled_subs,
            "monthly_recurring_revenue": round(total_mrr, 2),
            "annual_recurring_revenue": round(total_arr, 2),
            "revenue_by_cycle": revenue_by_cycle,
            "churn_rate": self._calculate_churn_rate(),
        }
    
    def _calculate_churn_rate(self) -> float:
        """Calculate monthly subscription churn rate"""
        cancelled_count = sum(
            1 for sub in self.subscriptions.values()
            if sub["status"] == InvoiceStatus.CANCELLED.value
        )
        total_count = len(self.subscriptions)
        
        return (cancelled_count / total_count * 100) if total_count > 0 else 0
    
    def _attempt_payment(self, invoice: Dict) -> Dict:
        """Simulate payment attempt"""
        return {
            "invoice_id": invoice["invoice_id"],
            "status": "success",  # In production: call payment processor
            "transaction_id": f"txn_{invoice['invoice_id']}",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _log_billing_event(
        self,
        subscription_id: str,
        event_type: str,
        detail: str = "",
    ):
        """Log billing event for audit"""
        event_id = f"evt_{len(self.billing_logs) + 1}"
        self.billing_logs[event_id] = {
            "subscription_id": subscription_id,
            "event_type": event_type,
            "detail": detail,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def get_billing_history(
        self,
        subscription_id: str,
        limit: int = 50,
    ) -> List[Dict]:
        """Get billing event history for subscription"""
        history = [
            event for event in self.billing_logs.values()
            if event["subscription_id"] == subscription_id
        ]
        
        # Sort by timestamp descending
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history[:limit]
    
    def get_subscriptions(
        self,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> List[Dict]:
        """Get subscriptions matching criteria"""
        results = []
        
        for sub in self.subscriptions.values():
            if customer_id and sub["customer_id"] != customer_id:
                continue
            if agent_id and sub["agent_id"] != agent_id:
                continue
            if status_filter and sub["status"] != status_filter:
                continue
            
            results.append(sub)
        
        return results
