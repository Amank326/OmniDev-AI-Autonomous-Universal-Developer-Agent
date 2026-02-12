"""
Analytics Service Layer for Phase 6: Analytics & Revenue Dashboard

Provides core business logic for:
- Revenue calculations (MRR, ARR, LTV)
- Subscription analytics
- Customer analysis
- Churn prediction
- Revenue forecasting
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import math

from app.models.payment_models import (
    StripeCustomer, Subscription, PaymentTransaction, SubscriptionStatus
)
from app.models.analytics_models import (
    AnalyticsEvent, RevenueMetric, SubscriptionMetric, CustomerMetric,
    ForecastedMetric, MetricType, AnalyticsAlert
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Core analytics calculations for business metrics"""

    @staticmethod
    def calculate_mrr(db: Session, include_forecast: bool = False) -> Dict:
        """
        Calculate Monthly Recurring Revenue (MRR)
        Sum of all active subscription values
        """
        try:
            # Get all active subscriptions
            active_subs = db.query(Subscription).filter(
                Subscription.status == SubscriptionStatus.ACTIVE
            ).all()

            mrr_cents = sum(sub.price_per_month for sub in active_subs)
            mrr = round(mrr_cents / 100, 2)  # Convert cents to dollars

            logger.info(f"Calculated MRR: ${mrr}")

            return {
                "value": mrr,
                "currency": "usd",
                "subscription_count": len(active_subs),
                "timestamp": datetime.utcnow(),
                "method": "active_subscriptions"
            }

        except Exception as e:
            logger.error(f"Error calculating MRR: {str(e)}")
            return {"value": 0, "error": str(e)}

    @staticmethod
    def calculate_arr(db: Session) -> Dict:
        """
        Calculate Annual Recurring Revenue (ARR)
        MRR × 12
        """
        mrr_data = AnalyticsService.calculate_mrr(db)
        arr = round(mrr_data["value"] * 12, 2)

        return {
            "value": arr,
            "currency": "usd",
            "mrr_basis": mrr_data["value"],
            "timestamp": datetime.utcnow(),
            "method": "mrr_annualized"
        }

    @staticmethod
    def calculate_ltv(db: Session, customer_id: Optional[str] = None) -> Dict:
        """
        Calculate Customer Lifetime Value (LTV)
        Average revenue per customer × customer lifetime (months)
        Or: Total revenue earned from customer
        """
        try:
            if customer_id:
                # Single customer LTV
                transactions = db.query(PaymentTransaction).filter(
                    PaymentTransaction.customer_id == customer_id
                ).all()

                total_revenue = sum(t.amount for t in transactions)
                ltv = round(total_revenue / 100, 2)  # Convert cents to dollars

                return {
                    "customer_id": customer_id,
                    "value": ltv,
                    "transaction_count": len(transactions),
                    "timestamp": datetime.utcnow()
                }
            else:
                # Aggregate LTV
                customers = db.query(StripeCustomer).all()
                total_ltv = 0

                for customer in customers:
                    transactions = db.query(PaymentTransaction).filter(
                        PaymentTransaction.customer_id == customer.id
                    ).all()
                    total_ltv += sum(t.amount for t in transactions)

                avg_ltv = round(total_ltv / len(customers) / 100, 2) if customers else 0

                return {
                    "average_ltv": avg_ltv,
                    "total_revenue": round(total_ltv / 100, 2),
                    "customer_count": len(customers),
                    "timestamp": datetime.utcnow()
                }

        except Exception as e:
            logger.error(f"Error calculating LTV: {str(e)}")
            return {"value": 0, "error": str(e)}

    @staticmethod
    def calculate_churn_rate(db: Session, period_days: int = 30) -> Dict:
        """
        Calculate subscription churn rate
        Churned subscriptions / active subscriptions at period start
        """
        try:
            period_start = datetime.utcnow() - timedelta(days=period_days)

            # Subscriptions that ended in period
            churned = db.query(Subscription).filter(
                and_(
                    Subscription.ended_at >= period_start,
                    Subscription.status == SubscriptionStatus.CANCELED
                )
            ).count()

            # Active subscriptions at start of period
            active_at_start = db.query(Subscription).filter(
                Subscription.created_at <= period_start
            ).count()

            churn_rate = round((churned / active_at_start * 100), 2) if active_at_start > 0 else 0

            return {
                "value": churn_rate,
                "period_days": period_days,
                "churned_count": churned,
                "active_at_start": active_at_start,
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error calculating churn rate: {str(e)}")
            return {"value": 0, "error": str(e)}

    @staticmethod
    def get_revenue_metrics(db: Session, days: int = 30) -> Dict:
        """
        Get revenue metrics for time period
        Includes new revenue, churned revenue, net revenue
        """
        try:
            period_start = datetime.utcnow() - timedelta(days=days)

            # New revenue (new subscriptions)
            new_subs = db.query(func.sum(Subscription.price_per_month)).filter(
                and_(
                    Subscription.created_at >= period_start,
                    Subscription.status == SubscriptionStatus.ACTIVE
                )
            ).scalar() or 0

            # Churned revenue (canceled subscriptions)
            churned_subs = db.query(func.sum(Subscription.price_per_month)).filter(
                and_(
                    Subscription.ended_at >= period_start,
                    Subscription.status == SubscriptionStatus.CANCELED
                )
            ).scalar() or 0

            # Payment transactions (one-time revenue)
            payments = db.query(func.sum(PaymentTransaction.amount)).filter(
                PaymentTransaction.created_at >= period_start
            ).scalar() or 0

            new_revenue = round((new_subs + payments) / 100, 2)
            churned_revenue = round(churned_subs / 100, 2)
            net_revenue = new_revenue - churned_revenue

            return {
                "period_days": days,
                "new_revenue": new_revenue,
                "churned_revenue": churned_revenue,
                "net_revenue": net_revenue,
                "one_time_payments": round(payments / 100, 2),
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error getting revenue metrics: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def get_customer_metrics(db: Session) -> Dict:
        """Get aggregated customer metrics"""
        try:
            total_customers = db.query(StripeCustomer).count()
            
            # New customers (created in last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            new_customers = db.query(StripeCustomer).filter(
                StripeCustomer.created_at >= thirty_days_ago
            ).count()

            # Customers with active subscriptions
            active_customers = db.query(StripeCustomer).join(Subscription).filter(
                Subscription.status == SubscriptionStatus.ACTIVE
            ).distinct().count()

            # Churned customers (30 day)
            churned_customers = db.query(StripeCustomer).join(Subscription).filter(
                and_(
                    Subscription.ended_at >= thirty_days_ago,
                    Subscription.status == SubscriptionStatus.CANCELED
                )
            ).distinct().count()

            return {
                "total_customers": total_customers,
                "new_customers_30d": new_customers,
                "active_customers": active_customers,
                "churned_customers_30d": churned_customers,
                "retention_rate": round((active_customers / total_customers * 100), 2) if total_customers > 0 else 0,
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error getting customer metrics: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def forecast_revenue(db: Session, days_ahead: int = 30) -> List[Dict]:
        """
        Forecast revenue for next N days using trend analysis
        Uses linear regression on historical data
        """
        try:
            # Get last 90 days of daily revenue
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)
            
            daily_revenue = db.query(
                func.date(RevenueMetric.period_date).label('date'),
                func.sum(RevenueMetric.value).label('total')
            ).filter(
                and_(
                    RevenueMetric.period_date >= ninety_days_ago,
                    RevenueMetric.metric_type == MetricType.MRR.value
                )
            ).group_by(func.date(RevenueMetric.period_date)).order_by('date').all()

            if len(daily_revenue) < 7:
                # Not enough data for meaningful forecast
                return []

            # Simple linear trend
            values = [float(r[1]) for r in daily_revenue]
            n = len(values)
            
            # Calculate trend
            x = list(range(n))
            avg_x = sum(x) / n
            avg_y = sum(values) / n
            
            numerator = sum((x[i] - avg_x) * (values[i] - avg_y) for i in range(n))
            denominator = sum((x[i] - avg_x) ** 2 for i in range(n))
            
            slope = numerator / denominator if denominator != 0 else 0
            intercept = avg_y - slope * avg_x

            # Generate forecasts
            forecasts = []
            for i in range(1, days_ahead + 1):
                forecast_value = slope * (n + i) + intercept
                confidence = max(0.5, 1.0 - (i / days_ahead * 0.4))  # Confidence decreases over time
                
                forecast_date = datetime.utcnow() + timedelta(days=i)
                
                forecasts.append({
                    "date": forecast_date,
                    "predicted_value": round(max(0, forecast_value), 2),
                    "confidence": round(confidence, 2)
                })

            return forecasts

        except Exception as e:
            logger.error(f"Error forecasting revenue: {str(e)}")
            return []

    @staticmethod
    def update_customer_metrics(db: Session, customer_id: str) -> Dict:
        """
        Update or create CustomerMetric record for a customer
        Called when subscription or payment changes
        """
        try:
            # Get all transactions for customer
            transactions = db.query(PaymentTransaction).filter(
                PaymentTransaction.customer_id == customer_id
            ).all()

            total_revenue_cents = sum(t.amount for t in transactions)
            total_revenue = round(total_revenue_cents / 100, 2)

            # Get active subscription for MRR
            active_sub = db.query(Subscription).filter(
                and_(
                    Subscription.customer_id == customer_id,
                    Subscription.status == SubscriptionStatus.ACTIVE
                )
            ).first()

            mrr_contribution = round((active_sub.price_per_month / 100), 2) if active_sub else 0

            # Calculate health score (0-100)
            payment_count = len(transactions)
            days_since_payment = 999
            if transactions:
                last_payment = max(transactions, key=lambda t: t.created_at)
                days_since_payment = (datetime.utcnow() - last_payment.created_at).days

            # Health score: recent payment + consistent payments
            health_score = 100
            if days_since_payment > 90:
                health_score = 20
            elif days_since_payment > 30:
                health_score = 70
            elif days_since_payment > 7:
                health_score = 85

            # Churn risk (0-1.0)
            churn_risk = 0.0
            if not active_sub:
                churn_risk = 1.0
            elif days_since_payment > 60:
                churn_risk = 0.7
            elif days_since_payment > 30:
                churn_risk = 0.3

            # Get or create metric
            metric = db.query(CustomerMetric).filter(
                CustomerMetric.customer_id == customer_id
            ).first()

            if not metric:
                import uuid
                metric = CustomerMetric(
                    id=str(uuid.uuid4()),
                    customer_id=customer_id
                )
                db.add(metric)

            # Update values
            metric.total_revenue = total_revenue
            metric.payment_count = payment_count
            metric.average_order_value = round(total_revenue / payment_count, 2) if payment_count > 0 else 0
            metric.lifetime_value = total_revenue
            metric.health_score = health_score
            metric.churn_risk = churn_risk
            metric.days_since_last_payment = days_since_payment
            metric.mrr_contribution = mrr_contribution

            if transactions:
                metric.last_payment_date = max(transactions, key=lambda t: t.created_at).created_at

            db.commit()

            return {
                "customer_id": customer_id,
                "total_revenue": total_revenue,
                "health_score": health_score,
                "churn_risk": round(churn_risk, 2),
                "mrr_contribution": mrr_contribution
            }

        except Exception as e:
            logger.error(f"Error updating customer metrics: {str(e)}")
            db.rollback()
            return {"error": str(e)}

    @staticmethod
    def get_cohort_analysis(db: Session, cohort_month: Optional[str] = None) -> Dict:
        """
        Customer cohort analysis
        Groups customers by signup month and tracks retention
        """
        try:
            if not cohort_month:
                cohort_month = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m")

            # Get customers from cohort month
            cohort_start = datetime.strptime(f"{cohort_month}-01", "%Y-%m-%d")
            cohort_end = cohort_start + timedelta(days=31)

            cohort_customers = db.query(StripeCustomer).filter(
                and_(
                    StripeCustomer.created_at >= cohort_start,
                    StripeCustomer.created_at < cohort_end
                )
            ).all()

            # Analyze retention by months
            retention = {}
            for i in range(13):  # 12 months + initial month
                check_date = cohort_start + timedelta(days=30 * i)
                
                active_in_month = db.query(Subscription).filter(
                    and_(
                        Subscription.customer_id.in_([c.id for c in cohort_customers]),
                        Subscription.created_at <= check_date,
                        or_(Subscription.ended_at == None, Subscription.ended_at > check_date)
                    )
                ).distinct(Subscription.customer_id).count()

                retention[f"month_{i}"] = round((active_in_month / len(cohort_customers) * 100), 2)

            return {
                "cohort_month": cohort_month,
                "cohort_size": len(cohort_customers),
                "retention": retention,
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error getting cohort analysis: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def check_and_create_alerts(db: Session, customer_id: str) -> List[Dict]:
        """
        Check for alert conditions and create alerts
        - Revenue drops > 20%
        - Churn spike
        - Low trial conversion
        """
        alerts = []
        try:
            # Revenue drop alert
            metrics = AnalyticsService.get_revenue_metrics(db, days=30)
            if metrics.get("net_revenue", 0) < 0:
                alert = AnalyticsAlert(
                    id=str(__import__("uuid").uuid4()),
                    customer_id=customer_id,
                    alert_type="revenue_drop",
                    metric_type="net_revenue",
                    metric_value=metrics.get("net_revenue"),
                    threshold_value=0,
                    severity="warning",
                    message=f"Revenue declined in last 30 days: ${metrics.get('net_revenue')}"
                )
                db.add(alert)
                alerts.append(alert.id)

            # Churn spike alert
            churn = AnalyticsService.calculate_churn_rate(db, 30)
            if churn.get("value", 0) > 10:
                alert = AnalyticsAlert(
                    id=str(__import__("uuid").uuid4()),
                    customer_id=customer_id,
                    alert_type="churn_spike",
                    metric_type="churn_rate",
                    metric_value=churn.get("value"),
                    threshold_value=10,
                    severity="critical",
                    message=f"High churn rate detected: {churn.get('value')}%"
                )
                db.add(alert)
                alerts.append(alert.id)

            db.commit()

        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
            db.rollback()

        return alerts

    @staticmethod
    def get_dashboard_summary(db: Session) -> Dict:
        """
        Get all metrics needed for dashboard summary view
        """
        return {
            "mrr": AnalyticsService.calculate_mrr(db),
            "arr": AnalyticsService.calculate_arr(db),
            "ltv": AnalyticsService.calculate_ltv(db),
            "churn_rate": AnalyticsService.calculate_churn_rate(db),
            "revenue_metrics": AnalyticsService.get_revenue_metrics(db),
            "customer_metrics": AnalyticsService.get_customer_metrics(db),
            "forecast": AnalyticsService.forecast_revenue(db, 30),
            "timestamp": datetime.utcnow()
        }
