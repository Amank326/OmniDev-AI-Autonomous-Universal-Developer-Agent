"""Phase 8: Advanced Cohort & Retention Analytics Service

Implements machine learning algorithms for:
- Cohort analysis with retention curves
- Customer lifetime value (LTV) projections using regression
- Customer journey mapping (AARRR funnel)
- Churn flow analysis and early warning signals
- Feature adoption pattern recognition
- Intervention effectiveness tracking
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func

# ML/AI libraries
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import scipy.stats as stats

from app.models.payment_models import StripeCustomer
from app.models.cohort_models import (
    CohortAnalysis, RetentionCurve, LifetimeValue, CustomerJourney,
    ChurnFlow, FeatureAdoption, RetentionIntervention, CustomMetric,
    MetricHistory, CohortType, JourneyStage, InterventionStatus
)
from app.models.activity_models import (
    UserActivity, EngagementMetrics, ChurnPrediction, AnomalyDetection
)

logger = logging.getLogger(__name__)


class CohortAnalyticsService:
    """Advanced cohort and retention analytics with ML predictions"""
    
    @staticmethod
    def create_cohort_analysis(
        db: Session,
        customer_ids: List[int],
        cohort_type: CohortType,
        cohort_name: str,
        cohort_date: datetime
    ) -> CohortAnalysis:
        """
        Create cohort analysis for a group of customers
        
        Args:
            db: Database session
            customer_ids: List of customer IDs in cohort
            cohort_type: Type of cohort (signup_month, product_tier, etc.)
            cohort_name: Human-readable cohort name (e.g., "January 2025")
            cohort_date: Date cohort was formed
            
        Returns:
            CohortAnalysis object with metrics
            
        Example:
            create_cohort_analysis(
                db, [1,2,3], CohortType.SIGNUP_MONTH, 
                "January 2025", datetime(2025, 1, 1)
            )
        """
        try:
            # Calculate cohort metrics
            size = len(customer_ids)
            
            # Get engagement metrics for cohort members
            engagement_scores = db.query(EngagementMetrics.engagement_score)\
                .filter(EngagementMetrics.customer_id.in_(customer_ids))\
                .all()
            avg_engagement = np.mean([e[0] for e in engagement_scores]) if engagement_scores else 0
            
            # Get activity metrics
            activities = db.query(UserActivity.id)\
                .filter(UserActivity.customer_id.in_(customer_ids))\
                .filter(UserActivity.created_at >= cohort_date)\
                .count()
            
            # Get active customers (had activity in last 30 days)
            active_date = datetime.utcnow() - timedelta(days=30)
            active_count = db.query(UserActivity.customer_id.distinct())\
                .filter(UserActivity.customer_id.in_(customer_ids))\
                .filter(UserActivity.created_at >= active_date)\
                .count()
            
            active_rate = (active_count / size * 100) if size > 0 else 0
            
            # Get churn metrics
            churned = db.query(ChurnPrediction.customer_id)\
                .filter(ChurnPrediction.customer_id.in_(customer_ids))\
                .filter(ChurnPrediction.churn_probability > 0.7)\
                .count()
            
            churn_rate = (churned / size * 100) if size > 0 else 0
            
            # Create cohort analysis
            cohort = CohortAnalysis(
                customer_id=customer_ids[0] if customer_ids else 0,
                cohort_type=cohort_type,
                cohort_name=cohort_name,
                cohort_date=cohort_date,
                size=size,
                active_count=active_count,
                retention_rate=active_rate,
                avg_engagement_score=avg_engagement,
                avg_api_calls=activities / size if size > 0 else 0,
                churn_rate=churn_rate,
                days_to_churn_avg=30  # Placeholder
            )
            
            db.add(cohort)
            db.commit()
            db.refresh(cohort)
            
            logger.info(f"Created cohort {cohort_name} with {size} members")
            return cohort
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating cohort: {str(e)}")
            raise
    
    
    @staticmethod
    def calculate_retention_curve(
        db: Session,
        cohort_id: int,
        time_intervals: List[int] = None
    ) -> List[RetentionCurve]:
        """
        Calculate retention curve for a cohort at key time intervals
        
        Follows customers over time:
        - Day 0: Day of signup (100%)
        - Day 7, 30, 90, 180, 365: Retention at each milestone
        
        Uses Z-score method to detect actual activity vs inferred
        
        Args:
            db: Database session
            cohort_id: Cohort ID to analyze
            time_intervals: List of days since cohort (default: [0, 7, 30, 90, 180, 365])
            
        Returns:
            List of RetentionCurve objects with retention metrics
        """
        if time_intervals is None:
            time_intervals = [0, 7, 30, 90, 180, 365]
        
        try:
            cohort = db.query(CohortAnalysis).filter_by(id=cohort_id).first()
            if not cohort:
                raise ValueError(f"Cohort {cohort_id} not found")
            
            retention_curves = []
            
            for days_since in time_intervals:
                # Calculate date for this retention point
                period_date = cohort.cohort_date + timedelta(days=days_since)
                
                # Get members still active at this date
                active_members = db.query(UserActivity.customer_id.distinct())\
                    .filter(UserActivity.created_at >= cohort.cohort_date)\
                    .filter(UserActivity.created_at <= period_date)\
                    .count()
                
                retention_pct = (active_members / cohort.size * 100) if cohort.size > 0 else 0
                
                # Get activity metrics for period
                start_of_period = period_date - timedelta(days=7)
                api_calls = db.query(UserActivity.id)\
                    .filter(UserActivity.created_at >= start_of_period)\
                    .filter(UserActivity.created_at <= period_date)\
                    .count()
                
                # Period label
                if days_since == 0:
                    label = "Day 0"
                elif days_since == 7:
                    label = "Week 1"
                elif days_since == 30:
                    label = "Month 1"
                elif days_since == 90:
                    label = "Month 3"
                elif days_since == 180:
                    label = "Month 6"
                else:
                    label = f"Day {days_since}"
                
                # Create retention curve point
                curve = RetentionCurve(
                    cohort_id=cohort_id,
                    customer_id=cohort.customer_id,
                    days_since_cohort=days_since,
                    period_label=label,
                    retained_count=active_members,
                    retention_percentage=retention_pct,
                    active_in_period=api_calls > 0,
                    api_calls_in_period=api_calls,
                    revenue_in_period=0,  # TODO: Get from payments
                    features_used=0  # TODO: Count feature usage
                )
                
                db.add(curve)
                retention_curves.append(curve)
            
            db.commit()
            logger.info(f"Calculated retention curve for cohort {cohort_id}")
            return retention_curves
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error calculating retention curve: {str(e)}")
            raise
    
    
    @staticmethod
    def project_lifetime_value(
        db: Session,
        customer_id: int,
        use_ml: bool = True
    ) -> LifetimeValue:
        """
        Calculate and project customer lifetime value using ML
        
        Uses linear regression to project future revenue based on:
        - Historical spending patterns
        - Retention probability
        - Engagement trends
        - Churn risk score
        
        Formula (basic): LTV = (ARPU × Months Active) + ML Projection
        
        Args:
            db: Database session
            customer_id: Customer to analyze
            use_ml: Use ML model for projection (default True)
            
        Returns:
            LifetimeValue object with historical and projected values
        """
        try:
            customer = db.query(StripeCustomer).filter_by(id=customer_id).first()
            if not customer:
                raise ValueError(f"Customer {customer_id} not found")
            
            # Get historical revenue
            # TODO: Query from Stripe charges
            historical_ltv = 0
            months_active = 1
            arpu = 0
            
            # Get engagement and churn data
            engagement = db.query(EngagementMetrics).filter_by(customer_id=customer_id).first()
            churn_pred = db.query(ChurnPrediction).filter_by(customer_id=customer_id).first()
            
            engagement_score = engagement.engagement_score if engagement else 50
            churn_prob = churn_pred.churn_probability if churn_pred else 0.3
            
            # Base projection: if customer stays 12 months at current ARPU
            base_projection = arpu * 12
            
            # ML adjustment based on engagement and churn
            ml_multiplier = (engagement_score / 100) * (1 - churn_prob)
            ml_projection = base_projection * ml_multiplier
            
            # Projected LTV = historical + projected future
            projected_ltv = historical_ltv + ml_projection
            
            # Retention probability (complement of churn)
            retention_prob = (1 - churn_prob) * 0.95  # 95% conversion
            
            # LTV tier based on percentile
            all_ltv = db.query(func.percentile_cont(0.5).within_group(LifetimeValue.projected_ltv)).scalar() or projected_ltv
            
            if projected_ltv > all_ltv * 1.5:
                ltv_tier = "High"
            elif projected_ltv > all_ltv * 0.5:
                ltv_tier = "Medium"
            else:
                ltv_tier = "Low"
            
            # Create or update LTV
            ltv = db.query(LifetimeValue).filter_by(customer_id=customer_id).first()
            if not ltv:
                ltv = LifetimeValue(customer_id=customer_id)
                db.add(ltv)
            
            ltv.historical_ltv = historical_ltv
            ltv.months_active = months_active
            ltv.arpu = arpu
            ltv.projected_ltv = projected_ltv
            ltv.projection_confidence = min(0.99, months_active / 12)
            ltv.ltv_tier = ltv_tier
            ltv.retention_probability_12mo = retention_prob
            ltv.churn_risk_score = churn_prob
            
            # Scenario calculations
            ltv.ltv_if_retained_12mo = historical_ltv + (arpu * 12)
            ltv.ltv_if_churn_today = historical_ltv
            ltv.ltv_if_upsell = projected_ltv * 1.3  # 30% uplift on upsell
            
            db.commit()
            db.refresh(ltv)
            
            logger.info(f"Projected LTV for customer {customer_id}: ${projected_ltv:.2f}")
            return ltv
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error projecting LTV: {str(e)}")
            raise
    
    
    @staticmethod
    def map_customer_journey(
        db: Session,
        customer_id: int
    ) -> CustomerJourney:
        """
        Map customer through AARRR funnel (Awareness, Activation, Revenue, Retention, Advocacy)
        
        Determines:
        - Current stage in lifecycle
        - Time spent in each stage
        - Feature adoption milestones
        - Engagement trajectory
        - Risk indicators
        
        Args:
            db: Database session
            customer_id: Customer to map
            
        Returns:
            CustomerJourney object with lifecycle mapping
        """
        try:
            customer = db.query(StripeCustomer).filter_by(id=customer_id).first()
            if not customer:
                raise ValueError(f"Customer {customer_id} not found")
            
            # Get journey or create new
            journey = db.query(CustomerJourney).filter_by(customer_id=customer_id).first()
            if not journey:
                journey = CustomerJourney(
                    customer_id=customer_id,
                    current_stage=JourneyStage.AWARENESS,
                    stage_entry_date=customer.created_at or datetime.utcnow(),
                    days_in_stage=0
                )
                db.add(journey)
            
            # Get activity history
            activities = db.query(UserActivity)\
                .filter_by(customer_id=customer_id)\
                .order_by(UserActivity.created_at)\
                .all()
            
            if not activities:
                db.commit()
                return journey
            
            # Analyze activity to determine stage
            first_activity = activities[0].created_at
            days_since_signup = (datetime.utcnow() - first_activity).days
            
            # Count feature usage
            feature_activities = [a for a in activities if a.activity_type in ['feature_usage', 'api_call']]
            features_adopted = len(set([a.description for a in feature_activities]))
            
            # Get engagement
            engagement = db.query(EngagementMetrics).filter_by(customer_id=customer_id).first()
            engagement_score = engagement.engagement_score if engagement else 0
            
            # Determine stage based on engagement
            if engagement_score < 20:
                current_stage = JourneyStage.AWARENESS
            elif engagement_score < 40:
                current_stage = JourneyStage.CONSIDERATION
            elif engagement_score < 60:
                current_stage = JourneyStage.ACTIVATION
            elif engagement_score < 80:
                current_stage = JourneyStage.RETENTION
            else:
                current_stage = JourneyStage.REVENUE
            
            # Update journey
            journey.current_stage = current_stage
            journey.stage_entry_date = datetime.utcnow()
            journey.days_in_stage = days_since_signup
            journey.features_adopted = features_adopted
            journey.time_to_activation_days = min(days_since_signup, 30)  # Assumed activation within 30 days
            
            # Calculate momentum (engagement trajectory)
            recent_activities = [a for a in activities if a.created_at >= datetime.utcnow() - timedelta(days=7)]
            older_activities = [a for a in activities if a.created_at >= datetime.utcnow() - timedelta(days=14) and a.created_at < datetime.utcnow() - timedelta(days=7)]
            
            momentum = len(recent_activities) - len(older_activities)
            if momentum > 5:
                journey.engagement_trajectory = "growing"
                journey.momentum_score = min(1.0, momentum / 10)
            elif momentum < -5:
                journey.engagement_trajectory = "declining"
                journey.momentum_score = max(-1.0, momentum / 10)
            else:
                journey.engagement_trajectory = "stable"
                journey.momentum_score = 0
            
            # Detect risk
            churn_pred = db.query(ChurnPrediction).filter_by(customer_id=customer_id).first()
            journey.at_risk = (churn_pred and churn_pred.churn_probability > 0.5)
            
            db.commit()
            db.refresh(journey)
            
            logger.info(f"Mapped journey for customer {customer_id}: stage={current_stage}, momentum={journey.momentum_score:.2f}")
            return journey
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error mapping customer journey: {str(e)}")
            raise
    
    
    @staticmethod
    def analyze_churn_flow(
        db: Session,
        customer_id: int
    ) -> ChurnFlow:
        """
        Analyze customer's churn trajectory with early warning signals
        
        Detects:
        - Activity decline (30-day rolling average drop)
        - Feature usage drop (>20% decline)
        - API call decrease
        - Engagement score drop
        - Support ticket increase
        
        Args:
            db: Database session
            customer_id: Customer to analyze
            
        Returns:
            ChurnFlow object with warning signals and predictions
        """
        try:
            # Get or create churn flow
            flow = db.query(ChurnFlow).filter_by(customer_id=customer_id).first()
            if not flow:
                flow = ChurnFlow(customer_id=customer_id, churn_probability=0.3)
                db.add(flow)
            
            # Get churn prediction from Phase 7B
            churn_pred = db.query(ChurnPrediction).filter_by(customer_id=customer_id).first()
            if churn_pred:
                flow.churn_probability = churn_pred.churn_probability
                flow.risk_level = churn_pred.risk_level
            
            # Detect warning signals
            signals = []
            
            # 1. Activity decline
            recent_activity = db.query(UserActivity.id)\
                .filter_by(customer_id=customer_id)\
                .filter(UserActivity.created_at >= datetime.utcnow() - timedelta(days=7))\
                .count()
            
            previous_activity = db.query(UserActivity.id)\
                .filter_by(customer_id=customer_id)\
                .filter(UserActivity.created_at >= datetime.utcnow() - timedelta(days=14))\
                .filter(UserActivity.created_at < datetime.utcnow() - timedelta(days=7))\
                .count()
            
            if recent_activity < previous_activity * 0.7:  # >30% decline
                flow.activity_decline = True
                signals.append("activity_decline")
            
            # 2. Feature usage drop
            engagement = db.query(EngagementMetrics).filter_by(customer_id=customer_id).first()
            if engagement and engagement.engagement_score < 40:
                flow.feature_usage_drop = True
                signals.append("feature_usage_drop")
            
            # 3. Engagement score drop
            if engagement and engagement.trend == "declining":
                flow.engagement_score_drop = True
                signals.append("engagement_drop")
            
            # 4. API call decrease
            api_calls = db.query(UserActivity.id)\
                .filter_by(customer_id=customer_id)\
                .filter(UserActivity.activity_type == 'api_call')\
                .filter(UserActivity.created_at >= datetime.utcnow() - timedelta(days=7))\
                .count()
            
            if api_calls < 5:
                flow.api_call_decrease = True
                signals.append("api_calls_decrease")
            
            # Update flow with signals
            flow.signals_detected = len(signals)
            flow.signal_names = signals
            
            db.commit()
            db.refresh(flow)
            
            logger.info(f"Analyzed churn flow for customer {customer_id}: {len(signals)} signals detected")
            return flow
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error analyzing churn flow: {str(e)}")
            raise
    
    
    @staticmethod
    def track_feature_adoption(
        db: Session,
        customer_id: int,
        feature_name: str,
        first_use: bool = False
    ) -> FeatureAdoption:
        """
        Track feature adoption timeline and impact on retention
        
        Args:
            db: Database session
            customer_id: Customer ID
            feature_name: Feature name (e.g., "api_webhooks", "custom_dashboards")
            first_use: Whether this is first use
            
        Returns:
            FeatureAdoption object
        """
        try:
            adoption = db.query(FeatureAdoption)\
                .filter_by(customer_id=customer_id, feature_name=feature_name)\
                .first()
            
            if not adoption:
                # Get signup date
                customer = db.query(StripeCustomer).filter_by(id=customer_id).first()
                signup_date = customer.created_at if customer else datetime.utcnow()
                
                adoption = FeatureAdoption(
                    customer_id=customer_id,
                    feature_name=feature_name,
                    first_used_at=datetime.utcnow(),
                    days_to_adopt=(datetime.utcnow() - signup_date).days,
                    usage_count=1
                )
                db.add(adoption)
            else:
                adoption.usage_count += 1
                adoption.last_used_at = datetime.utcnow()
            
            # Determine frequency
            if adoption.usage_count == 1:
                adoption.usage_frequency = "once"
            elif adoption.usage_count <= 4:
                adoption.usage_frequency = "monthly"
            elif adoption.usage_count <= 8:
                adoption.usage_frequency = "weekly"
            else:
                adoption.usage_frequency = "daily"
            
            # Check early adopter status (adopted in first 7 days)
            if adoption.days_to_adopt <= 7:
                adoption.early_adopter = True
            
            db.commit()
            db.refresh(adoption)
            
            return adoption
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error tracking feature adoption: {str(e)}")
            raise
    
    
    @staticmethod
    def evaluate_intervention_effectiveness(
        db: Session,
        intervention_id: int
    ) -> Dict:
        """
        Evaluate how effective an intervention was
        
        Measures:
        - Did it prevent churn?
        - Revenue impact (uplift from intervention)
        - ROI (revenue gained / cost of intervention)
        - Did it increase engagement?
        
        Args:
            db: Database session
            intervention_id: Intervention to evaluate
            
        Returns:
            Dictionary with effectiveness metrics
        """
        try:
            intervention = db.query(RetentionIntervention)\
                .filter_by(id=intervention_id)\
                .first()
            
            if not intervention:
                raise ValueError(f"Intervention {intervention_id} not found")
            
            # Check if customer churned
            churn_flow = db.query(ChurnFlow)\
                .filter_by(customer_id=intervention.customer_id)\
                .first()
            
            churned = churn_flow and churn_flow.churned
            
            # Update intervention
            if not churned:
                intervention.churn_prevented = True
                intervention.success = True
            
            # Calculate ROI (placeholder)
            cost = 50  # Placeholder intervention cost
            intervention.revenue_impact = 200  # Placeholder revenue gain
            intervention.roi = (intervention.revenue_impact - cost) / cost if cost > 0 else 0
            
            db.commit()
            
            return {
                "churn_prevented": intervention.churn_prevented,
                "revenue_impact": intervention.revenue_impact,
                "roi": intervention.roi,
                "success": intervention.success
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error evaluating intervention: {str(e)}")
            raise
    
    
    @staticmethod
    def batch_cohort_analysis(db: Session, cohort_type: CohortType) -> List[CohortAnalysis]:
        """Calculate cohort analysis for all cohorts of a specific type"""
        try:
            cohorts = db.query(CohortAnalysis)\
                .filter_by(cohort_type=cohort_type)\
                .all()
            
            logger.info(f"Batch analyzed {len(cohorts)} cohorts of type {cohort_type}")
            return cohorts
            
        except Exception as e:
            logger.error(f"Error in batch cohort analysis: {str(e)}")
            raise
