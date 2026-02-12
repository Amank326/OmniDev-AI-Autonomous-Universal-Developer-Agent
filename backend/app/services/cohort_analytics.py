"""
Phase 17: Cohort Analysis Service
- Track user segments by signup date, tier, and behavior
- Retention curves and lifecycle analysis
- Revenue trends by cohort
- Churn analysis and patterns
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CohortAnalytics:
    """Cohort-based user segmentation and analysis"""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize cohort analytics"""
        self.db_session = db_session
        self.cohort_data = {}

    def create_cohort_definition(
        self,
        cohort_name: str,
        definition_type: str,  # "signup_date", "subscription_tier", "agent_category", "behavior"
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create cohort definition
        
        Args:
            cohort_name: Name for cohort
            definition_type: Type of cohort segmentation
            filters: Filters to define cohort membership
        
        Returns:
            Cohort definition
        """
        try:
            cohort_def = {
                "cohort_id": f"cohort_{cohort_name}",
                "name": cohort_name,
                "definition_type": definition_type,
                "filters": filters,
                "created_at": datetime.utcnow(),
                "status": "active"
            }
            
            self.cohort_data[cohort_def["cohort_id"]] = cohort_def
            
            return {
                "status": "created",
                "cohort_id": cohort_def["cohort_id"],
                "cohort_name": cohort_name,
                "definition_type": definition_type
            }
        
        except Exception as e:
            logger.error(f"Error creating cohort: {str(e)}")
            return {"error": str(e)}

    def build_signup_cohorts(
        self,
        users_data: List[Dict[str, Any]],
        bucket_days: int = 30
    ) -> Dict[str, Any]:
        """
        Build cohorts based on signup date
        
        Args:
            users_data: User list with signup dates
            bucket_days: Days per cohort bucket
        
        Returns:
            Signup cohorts and member counts
        """
        try:
            cohorts = {}
            now = datetime.utcnow()
            
            for user in users_data:
                signup_date = user.get("created_at")
                if not signup_date:
                    continue
                
                # Calculate cohort bucket
                days_since_signup = (now - signup_date).days
                cohort_bucket = (days_since_signup // bucket_days) * bucket_days
                cohort_key = f"signup_{cohort_bucket}_{cohort_bucket + bucket_days}_days_ago"
                
                if cohort_key not in cohorts:
                    cohorts[cohort_key] = {
                        "cohort_name": f"{cohort_bucket}-{cohort_bucket + bucket_days} days ago",
                        "members": [],
                        "signup_range": {
                            "min_days_ago": cohort_bucket,
                            "max_days_ago": cohort_bucket + bucket_days
                        }
                    }
                
                cohorts[cohort_key]["members"].append(user["user_id"])
            
            # Calculate cohort stats
            cohort_stats = {}
            for cohort_key, cohort_data in cohorts.items():
                cohort_stats[cohort_key] = {
                    "cohort_name": cohort_data["cohort_name"],
                    "member_count": len(cohort_data["members"]),
                    "signup_range": cohort_data["signup_range"]
                }
            
            return {
                "status": "built",
                "cohort_type": "signup_date",
                "bucket_days": bucket_days,
                "cohorts": cohort_stats,
                "total_cohorts": len(cohort_stats)
            }
        
        except Exception as e:
            logger.error(f"Error building signup cohorts: {str(e)}")
            return {"error": str(e)}

    def calculate_retention_curve(
        self,
        cohort_id: str,
        cohort_members: List[str],
        subscription_data: List[Dict[str, Any]],
        max_weeks: int = 52
    ) -> Dict[str, Any]:
        """
        Calculate retention curve for cohort
        
        Shows % of cohort still active over time
        
        Args:
            cohort_id: Cohort identifier
            cohort_members: List of user IDs in cohort
            subscription_data: Subscription history
            max_weeks: Time horizon (weeks)
        
        Returns:
            Retention curve data
        """
        try:
            retention_by_week = {}
            
            for week in range(0, max_weeks + 1):
                week_label = f"week_{week}"
                active_count = 0
                
                for user_id in cohort_members:
                    # Check if user was active in this week
                    user_subs = [s for s in subscription_data if s.get("user_id") == user_id]
                    
                    if user_subs:
                        latest_sub = max(user_subs, key=lambda x: x.get("created_at", datetime.min))
                        
                        # Check if subscription covers this week
                        created_date = latest_sub.get("created_at")
                        if created_date:
                            weeks_since_signup = (datetime.utcnow() - created_date).days / 7
                            
                            # User is retained if still subscribed in this week
                            status = latest_sub.get("status", "active")
                            if status == "active" and weeks_since_signup >= week:
                                active_count += 1
                
                retention_pct = (active_count / len(cohort_members) * 100) if cohort_members else 0
                retention_by_week[week_label] = {
                    "week": week,
                    "active_users": active_count,
                    "retention_pct": retention_pct
                }
            
            # Calculate retention metrics
            initial_retention = retention_by_week.get("week_0", {}).get("retention_pct", 100)
            week4_retention = retention_by_week.get("week_4", {}).get("retention_pct", 0)
            week12_retention = retention_by_week.get("week_12", {}).get("retention_pct", 0)
            
            return {
                "cohort_id": cohort_id,
                "retention_curve": retention_by_week,
                "metrics": {
                    "week_0_retention": initial_retention,
                    "week_4_retention": week4_retention,
                    "week_12_retention": week12_retention,
                    "retention_trend": self._calculate_trend(retention_by_week)
                }
            }
        
        except Exception as e:
            logger.error(f"Error calculating retention: {str(e)}")
            return {"error": str(e)}

    def analyze_cohort_revenue(
        self,
        cohort_id: str,
        cohort_members: List[str],
        transaction_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze revenue trends by cohort
        
        Args:
            cohort_id: Cohort identifier
            cohort_members: List of user IDs
            transaction_data: Transaction history
        
        Returns:
            Cohort revenue metrics
        """
        try:
            monthly_revenue = {}
            lifetime_value = {}
            
            for user_id in cohort_members:
                user_transactions = [t for t in transaction_data if t.get("user_id") == user_id]
                
                for trans in user_transactions:
                    month_key = trans.get("created_at").strftime("%Y-%m") if trans.get("created_at") else "unknown"
                    amount = trans.get("amount", 0)
                    
                    if month_key not in monthly_revenue:
                        monthly_revenue[month_key] = 0
                    monthly_revenue[month_key] += amount
                
                # Calculate LTV
                ltv = sum(t.get("amount", 0) for t in user_transactions)
                lifetime_value[user_id] = ltv
            
            avg_revenue_per_user = np.mean(list(lifetime_value.values())) if lifetime_value else 0
            total_cohort_revenue = sum(lifetime_value.values())
            
            return {
                "cohort_id": cohort_id,
                "monthly_revenue": monthly_revenue,
                "lifetime_value": {
                    "total": total_cohort_revenue,
                    "avg_per_user": avg_revenue_per_user,
                    "median_per_user": float(np.median(list(lifetime_value.values()))) if lifetime_value else 0
                },
                "revenue_trend": self._calculate_trend(monthly_revenue)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing cohort revenue: {str(e)}")
            return {"error": str(e)}

    def analyze_cohort_churn(
        self,
        cohort_id: str,
        cohort_members: List[str],
        subscription_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze churn patterns by cohort
        
        Args:
            cohort_id: Cohort identifier
            cohort_members: List of user IDs
            subscription_data: Subscription history
        
        Returns:
            Cohort churn metrics
        """
        try:
            churned_count = 0
            churn_by_month = {}
            
            for user_id in cohort_members:
                user_subs = [s for s in subscription_data if s.get("user_id") == user_id]
                
                if user_subs:
                    latest_sub = max(user_subs, key=lambda x: x.get("updated_at", datetime.min))
                    
                    if latest_sub.get("status") == "cancelled":
                        churned_count += 1
                        
                        # Track churn month
                        churn_date = latest_sub.get("updated_at")
                        month_key = churn_date.strftime("%Y-%m") if churn_date else "unknown"
                        
                        if month_key not in churn_by_month:
                            churn_by_month[month_key] = 0
                        churn_by_month[month_key] += 1
            
            churn_rate = (churned_count / len(cohort_members) * 100) if cohort_members else 0
            avg_tenure_days = self._calculate_avg_tenure(cohort_members, subscription_data)
            
            return {
                "cohort_id": cohort_id,
                "churned_count": churned_count,
                "churn_rate": churn_rate,
                "retained_count": len(cohort_members) - churned_count,
                "churn_by_month": churn_by_month,
                "avg_customer_tenure_days": avg_tenure_days
            }
        
        except Exception as e:
            logger.error(f"Error analyzing cohort churn: {str(e)}")
            return {"error": str(e)}

    def compare_cohorts(
        self,
        cohorts_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare metrics across multiple cohorts
        
        Args:
            cohorts_data: Dictionary of cohort metrics
        
        Returns:
            Comparative analysis
        """
        try:
            comparison = {
                "cohorts": {},
                "best_performers": {},
                "trends": {}
            }
            
            # Extract key metrics for each cohort
            for cohort_id, metrics in cohorts_data.items():
                comparison["cohorts"][cohort_id] = {
                    "member_count": metrics.get("member_count", 0),
                    "churn_rate": metrics.get("churn_rate", 0),
                    "ltv": metrics.get("ltv", 0),
                    "retention_week4": metrics.get("retention_week4", 0)
                }
            
            # Identify best performers
            comparison["best_performers"]["lowest_churn"] = min(
                comparison["cohorts"].items(),
                key=lambda x: x[1]["churn_rate"],
                default=("N/A", {})
            )[0]
            
            comparison["best_performers"]["highest_ltv"] = max(
                comparison["cohorts"].items(),
                key=lambda x: x[1]["ltv"],
                default=("N/A", {})
            )[0]
            
            return comparison
        
        except Exception as e:
            logger.error(f"Error comparing cohorts: {str(e)}")
            return {"error": str(e)}

    def get_cohort_insights(
        self,
        cohort_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate actionable insights from cohort analysis
        
        Args:
            cohort_analysis: Comprehensive cohort data
        
        Returns:
            Insights and recommendations
        """
        try:
            insights = {
                "findings": [],
                "recommendations": []
            }
            
            # Analyze churn patterns
            if "churn_rate" in cohort_analysis:
                churn_rate = cohort_analysis["churn_rate"]
                
                if churn_rate > 20:
                    insights["findings"].append(f"High churn rate detected ({churn_rate:.1f}%)")
                    insights["recommendations"].append("Implement retention campaigns for this cohort")
                elif churn_rate < 5:
                    insights["findings"].append(f"Excellent retention ({churn_rate:.1f}%)")
                    insights["recommendations"].append("Use this cohort as benchmark for retention best practices")
            
            # Analyze revenue trends
            if "revenue_trend" in cohort_analysis:
                trend = cohort_analysis["revenue_trend"]
                
                if trend == "increasing":
                    insights["findings"].append("Revenue trending upward")
                    insights["recommendations"].append("Analyze what's driving growth and replicate")
                elif trend == "decreasing":
                    insights["findings"].append("Revenue trending downward")
                    insights["recommendations"].append("Investigate causes and launch recovery initiatives")
            
            # Analyze retention
            if "retention_week4" in cohort_analysis:
                week4_ret = cohort_analysis["retention_week4"]
                
                if week4_ret < 60:
                    insights["findings"].append(f"Low week-4 retention ({week4_ret:.1f}%)")
                    insights["recommendations"].append("Improve onboarding experience for this cohort")
            
            return insights
        
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {"error": str(e)}

    # Helper methods
    
    def _calculate_trend(self, data_dict: Dict) -> str:
        """Determine trend direction"""
        if not data_dict or len(data_dict) < 2:
            return "insufficient_data"
        
        values = list(data_dict.values())
        if isinstance(values[0], dict) and "retention_pct" in values[0]:
            values = [v["retention_pct"] for v in values]
        elif isinstance(values[0], (int, float)):
            pass  # Already numeric
        else:
            return "unknown"
        
        if len(values) < 2:
            return "insufficient_data"
        
        # Compare first half vs second half
        midpoint = len(values) // 2
        first_half_avg = np.mean(values[:midpoint])
        second_half_avg = np.mean(values[midpoint:])
        
        if second_half_avg > first_half_avg * 1.05:
            return "increasing"
        elif second_half_avg < first_half_avg * 0.95:
            return "decreasing"
        else:
            return "stable"

    def _calculate_avg_tenure(
        self,
        user_ids: List[str],
        subscription_data: List[Dict[str, Any]]
    ) -> float:
        """Calculate average subscription tenure"""
        tenures = []
        
        for user_id in user_ids:
            user_subs = [s for s in subscription_data if s.get("user_id") == user_id]
            
            if user_subs:
                created = user_subs[0].get("created_at")
                ended = user_subs[-1].get("updated_at", datetime.utcnow())
                
                if created:
                    tenure = (ended - created).days
                    tenures.append(tenure)
        
        return float(np.mean(tenures)) if tenures else 0
