"""Phase 9: AI Recommendation Engine

Generates personalized recommendations based on:
- Customer segment
- Churn risk
- LTV potential
- Feature adoption patterns
- Cross-sell/upsell opportunities
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random

from app.models.phase9_models import Recommendation, CustomerSegment
from app.models.payment_models import StripeCustomer
from app.models.activity_models import UserActivity

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generate personalized AI recommendations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_recommendations(self, customer_id: int, churn_risk: Optional[float] = None, 
                                ltv_forecast: Optional[float] = None) -> List[Dict]:
        """
        Generate personalized recommendations for a customer
        
        Args:
            customer_id: Customer ID
            churn_risk: Churn probability (0-1)
            ltv_forecast: Forecasted LTV
        
        Returns:
            List of recommendations with priorities
        """
        customer = self.db.query(StripeCustomer).filter_by(customer_id=customer_id).first()
        
        if not customer:
            return []
        
        recommendations = []
        
        # Get customer segment
        segment = self.db.query(CustomerSegment).filter(
            CustomerSegment.segment_assignments.any(customer_id=customer_id)
        ).first()
        
        # Churn risk recommendations
        if churn_risk and churn_risk > 0.5:
            recommendations.extend(self._generate_retention_recommendations(customer, churn_risk))
        
        # Engagement recommendations
        recommendations.extend(self._generate_engagement_recommendations(customer, segment))
        
        # Growth recommendations
        if ltv_forecast and ltv_forecast > 1000:
            recommendations.extend(self._generate_growth_recommendations(customer, ltv_forecast))
        
        # Feature adoption recommendations
        recommendations.extend(self._generate_adoption_recommendations(customer))
        
        # Cross-sell/upsell
        recommendations.extend(self._generate_cross_sell_recommendations(customer))
        
        # Sort by priority and save
        recommendations.sort(key=lambda x: x['priority_score'], reverse=True)
        
        for i, rec in enumerate(recommendations[:5]):  # Top 5
            recommendation = Recommendation(
                customer_id=customer_id,
                recommendation_type=rec['type'],
                title=rec['title'],
                description=rec['description'],
                action_url=rec['action_url'],
                estimated_impact=rec['impact'],
                confidence_score=rec['confidence'],
                priority_score=rec['priority_score'],
                category=rec['category'],
                priority_order=i + 1,
                reason=rec['reason'],
                explanation=rec['explanation'],
                ab_test_variant=rec.get('ab_variant', 'control'),
                recommended_at=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=30)
            )
            self.db.add(recommendation)
        
        self.db.commit()
        
        return recommendations[:5]
    
    def _generate_retention_recommendations(self, customer: StripeCustomer, churn_risk: float) -> List[Dict]:
        """Generate recommendations to prevent churn"""
        recommendations = []
        
        if churn_risk > 0.7:
            recommendations.append({
                'type': 'exclusive_offer',
                'title': '🎁 Special Retention Offer - 30% Off',
                'description': 'Exclusive discount for valued customers to re-engage with our platform',
                'action_url': '/offers/retention-30-off',
                'impact': 0.45,
                'confidence': 0.88,
                'priority_score': 95.0,
                'category': 'retention',
                'reason': f'Critical churn risk detected ({churn_risk:.1%})',
                'explanation': 'Based on your recent inactivity and engagement patterns, we\'ve identified a high risk of churn. This exclusive offer is designed to re-engage you with our platform.',
                'ab_variant': random.choice(['control', 'variant_a', 'variant_b'])
            })
        
        if churn_risk > 0.5:
            recommendations.append({
                'type': 'onboarding_refresh',
                'title': '📚 Personalized Learning Path',
                'description': 'Reintroduce key features you might have missed',
                'action_url': '/learning/personalized-path',
                'impact': 0.35,
                'confidence': 0.82,
                'priority_score': 85.0,
                'category': 'engagement',
                'reason': f'Moderate churn risk detected ({churn_risk:.1%})',
                'explanation': 'Low feature adoption detected. This personalized learning path will help you maximize value from the platform.'
            })
        
        recommendations.append({
            'type': 'dedicated_support',
            'title': '🤝 Dedicated Account Manager',
            'description': 'Get priority support and personalized guidance',
            'action_url': '/support/request-manager',
            'impact': 0.40,
            'confidence': 0.85,
            'priority_score': 80.0,
            'category': 'support',
            'reason': 'At-risk customer requires white-glove service',
            'explanation': 'Based on your account value and current engagement trends, we\'d like to assign a dedicated support specialist to your account.'
        })
        
        return recommendations
    
    def _generate_engagement_recommendations(self, customer: StripeCustomer, segment: Optional[CustomerSegment]) -> List[Dict]:
        """Generate recommendations to increase engagement"""
        recommendations = []
        
        # Check activity patterns
        recent_activity = self.db.query(UserActivity).filter(
            UserActivity.customer_id == customer.customer_id,
            UserActivity.created_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        if recent_activity < 5:
            recommendations.append({
                'type': 'webinar_invitation',
                'title': '🎓 Live Webinar: Advanced Features',
                'description': 'Join our expert team for a deep dive into platform features',
                'action_url': '/events/webinar-advanced-features',
                'impact': 0.30,
                'confidence': 0.75,
                'priority_score': 70.0,
                'category': 'education',
                'reason': 'Low recent engagement detected',
                'explanation': 'We notice you haven\'t been active recently. Join our interactive webinar to discover advanced features and best practices.'
            })
        
        if segment:
            recommendations.append({
                'type': 'community_engagement',
                'title': '👥 Community Forum Discussion',
                'description': f'Join {segment.segment_name} community members in discussions',
                'action_url': '/community/discussions',
                'impact': 0.25,
                'confidence': 0.70,
                'priority_score': 65.0,
                'category': 'community',
                'reason': f'Matched with similar {segment.segment_name} customers',
                'explanation': 'Connect with peers who share similar use cases and learn from their experiences.'
            })
        
        return recommendations
    
    def _generate_growth_recommendations(self, customer: StripeCustomer, ltv_forecast: float) -> List[Dict]:
        """Generate recommendations for high-value customers"""
        recommendations = []
        
        if ltv_forecast > 5000:
            recommendations.append({
                'type': 'premium_tier',
                'title': '⭐ Upgrade to Premium Tier',
                'description': 'Unlock enterprise features and unlimited access',
                'action_url': '/upgrade/premium',
                'impact': 0.60,
                'confidence': 0.80,
                'priority_score': 85.0,
                'category': 'upsell',
                'reason': f'High LTV forecast (${ltv_forecast:.2f})',
                'explanation': 'Your usage patterns and projected value suggest you\'d benefit significantly from our premium tier with advanced features and priority support.'
            })
        
        if ltv_forecast > 2000:
            recommendations.append({
                'type': 'advanced_analytics',
                'title': '📊 Advanced Analytics Suite',
                'description': 'Get deeper insights with premium reporting tools',
                'action_url': '/features/advanced-analytics',
                'impact': 0.50,
                'confidence': 0.78,
                'priority_score': 75.0,
                'category': 'feature',
                'reason': f'Projected to benefit from analytics tools',
                'explanation': 'Our advanced analytics suite will help you extract more value from your data and make better business decisions.'
            })
        
        return recommendations
    
    def _generate_adoption_recommendations(self, customer: StripeCustomer) -> List[Dict]:
        """Generate recommendations for feature adoption"""
        recommendations = []
        
        # Get adopted features
        adopted_features = self.db.query(UserActivity).filter(
            UserActivity.customer_id == customer.customer_id,
            UserActivity.created_at >= datetime.utcnow() - timedelta(days=90)
        ).distinct(UserActivity.feature_id).count()
        
        unadopted_features = max(0, 12 - adopted_features)  # Assuming 12 total features
        
        if unadopted_features > 5:
            recommendations.append({
                'type': 'feature_discovery',
                'title': '🔍 Discover Untapped Features',
                'description': f'You\'re only using {adopted_features} of our key features. Explore the rest!',
                'action_url': '/features/discovery',
                'impact': 0.45,
                'confidence': 0.82,
                'priority_score': 72.0,
                'category': 'adoption',
                'reason': f'Low feature adoption ({adopted_features}/12)',
                'explanation': f'You\'re currently using {adopted_features} features. Our data shows customers who adopt more features see {35}% higher satisfaction and ROI.'
            })
        
        recommendations.append({
            'type': 'personalized_tutorial',
            'title': '📖 Personalized Feature Tutorials',
            'description': 'Video guides tailored to your usage patterns',
            'action_url': '/tutorials/personalized',
            'impact': 0.35,
            'confidence': 0.75,
            'priority_score': 65.0,
            'category': 'education',
            'reason': 'Optimize feature adoption',
            'explanation': 'We\'ve created personalized video tutorials based on features similar customers use effectively.'
        })
        
        return recommendations
    
    def _generate_cross_sell_recommendations(self, customer: StripeCustomer) -> List[Dict]:
        """Generate cross-sell and upsell recommendations"""
        recommendations = []
        
        # Check current subscription
        current_plan = getattr(customer, 'subscription_tier', 'basic')
        
        if current_plan == 'basic':
            recommendations.append({
                'type': 'upsell_pro',
                'title': '🚀 Upgrade to Pro Plan',
                'description': 'Get 5x more API calls, priority support, and advanced integrations',
                'action_url': '/pricing/pro-plan',
                'impact': 0.55,
                'confidence': 0.80,
                'priority_score': 78.0,
                'category': 'upsell',
                'reason': 'Usage patterns suggest Pro tier benefits',
                'explanation': 'Your current usage indicates you\'ve outgrown the Basic plan. Pro includes features like advanced analytics and webhook support.'
            })
        
        recommendations.append({
            'type': 'addon_integration',
            'title': '🔌 Slack Integration Add-on',
            'description': 'Get real-time alerts and insights directly in Slack',
            'action_url': '/addons/slack',
            'impact': 0.40,
            'confidence': 0.72,
            'priority_score': 70.0,
            'category': 'addon',
            'reason': 'Complements your existing usage',
            'explanation': 'The Slack integration helps teams stay synchronized and respond faster to alerts. Popular with customers using your features.'
        })
        
        return recommendations
    
    def track_recommendation_performance(self, recommendation_id: int, action_taken: bool, 
                                        conversion: bool = False) -> Dict:
        """Track if recommendations are effective"""
        recommendation = self.db.query(Recommendation).filter_by(
            recommendation_id=recommendation_id
        ).first()
        
        if not recommendation:
            return {'error': 'recommendation_not_found'}
        
        # Update tracking
        recommendation.last_shown_at = datetime.utcnow()
        recommendation.show_count = (recommendation.show_count or 0) + 1
        
        if action_taken:
            recommendation.action_taken_count = (recommendation.action_taken_count or 0) + 1
        
        if conversion:
            recommendation.conversion_count = (recommendation.conversion_count or 0) + 1
            recommendation.last_converted_at = datetime.utcnow()
        
        # Calculate CTR
        if recommendation.show_count:
            ctr = recommendation.action_taken_count / recommendation.show_count
            recommendation.click_through_rate = ctr
        
        self.db.commit()
        
        return {
            'recommendation_id': recommendation_id,
            'action_taken': action_taken,
            'conversion': conversion,
            'ctr': getattr(recommendation, 'click_through_rate', 0)
        }
    
    def get_ab_test_variant(self, customer_id: int, test_name: str) -> str:
        """Get A/B test variant for a customer"""
        # Simple deterministic assignment based on customer_id
        variants = ['control', 'variant_a', 'variant_b']
        return variants[customer_id % len(variants)]
