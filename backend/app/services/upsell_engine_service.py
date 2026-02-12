"""
Upsell Engine Service - Intelligent upselling and engagement optimization
Recommends upsells based on usage patterns, engagement, and churn risk
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json


class UpsellOpportunity(str, Enum):
    """Types of upsell opportunities"""
    USAGE_APPROACHING = "usage_approaching"
    FEATURE_REQUEST = "feature_request"
    CHURN_RISK = "churn_risk"
    ENGAGEMENT_LOW = "engagement_low"
    EXPANSION_POTENTIAL = "expansion_potential"
    COMPETITIVE = "competitive"


class ConversionStage(str, Enum):
    """Upsell conversion stages"""
    IDENTIFIED = "identified"
    TARGETED = "targeted"
    ENGAGED = "engaged"
    PROPOSED = "proposed"
    NEGOTIATING = "negotiating"
    CONVERTED = "converted"
    LOST = "lost"


class UpsellEngineService:
    """
    Service for identifying upsell opportunities, optimizing conversion,
    and tracking engagement metrics.
    """
    
    def __init__(self):
        """Initialize upsell engine"""
        self.opportunities = {}
        self.engagement_scores = {}
        self.conversion_funnels = {}
        self.churn_risk_profiles = {}
        self.upsell_history = {}
        self.trigger_thresholds = self._initialize_triggers()
    
    def _initialize_triggers(self) -> Dict:
        """Initialize upsell trigger thresholds"""
        return {
            "execution_usage_percent": 80,  # Trigger at 80% of quota
            "api_calls_usage_percent": 85,
            "storage_usage_percent": 75,
            "engagement_threshold_days": 14,  # No activity in 14 days
            "churn_risk_score": 0.6,  # High risk if > 0.6
            "expansion_monthly_growth": 0.15,  # Growing 15% MoM
        }
    
    def identify_upsell_opportunities(
        self,
        customer_id: str,
        current_tier: str,
        usage_metrics: Dict,
        engagement_data: Dict,
        customer_profile: Dict,
    ) -> List[Dict]:
        """
        Identify upsell opportunities for customer.
        
        Args:
            customer_id: Customer ID
            current_tier: Current tier level
            usage_metrics: Current usage data
            engagement_data: Engagement metrics
            customer_profile: Customer profile data
        
        Returns:
            List of identified opportunities
        """
        opportunities = []
        
        # Check usage approaching limits
        usage_opportunity = self._check_usage_limits(
            customer_id=customer_id,
            usage_metrics=usage_metrics,
        )
        if usage_opportunity:
            opportunities.append(usage_opportunity)
        
        # Check engagement patterns
        engagement_opportunity = self._check_engagement_patterns(
            customer_id=customer_id,
            engagement_data=engagement_data,
        )
        if engagement_opportunity:
            opportunities.append(engagement_opportunity)
        
        # Check churn risk
        churn_opportunity = self._assess_churn_risk(
            customer_id=customer_id,
            customer_profile=customer_profile,
            engagement_data=engagement_data,
        )
        if churn_opportunity:
            opportunities.append(churn_opportunity)
        
        # Check expansion potential
        expansion_opportunity = self._assess_expansion_potential(
            customer_id=customer_id,
            customer_profile=customer_profile,
            usage_metrics=usage_metrics,
        )
        if expansion_opportunity:
            opportunities.append(expansion_opportunity)
        
        # Store opportunities
        self.opportunities[customer_id] = opportunities
        
        return opportunities
    
    def _check_usage_limits(
        self,
        customer_id: str,
        usage_metrics: Dict,
    ) -> Optional[Dict]:
        """Check if customer approaching usage limits"""
        metrics_to_check = ["executions", "api_calls", "storage"]
        
        approaching_limits = []
        
        for metric in metrics_to_check:
            current = usage_metrics.get(f"{metric}_current", 0)
            limit = usage_metrics.get(f"{metric}_limit")
            
            if limit and current > 0:
                usage_percent = (current / limit) * 100
                
                threshold = self.trigger_thresholds.get(f"{metric}_usage_percent", 80)
                
                if usage_percent >= threshold:
                    approaching_limits.append({
                        "metric": metric,
                        "current": current,
                        "limit": limit,
                        "usage_percent": round(usage_percent, 1),
                    })
        
        if approaching_limits:
            return {
                "customer_id": customer_id,
                "opportunity_type": UpsellOpportunity.USAGE_APPROACHING.value,
                "severity": "high" if any(m["usage_percent"] > 95 for m in approaching_limits) else "medium",
                "metrics_affected": approaching_limits,
                "recommended_action": "Upgrade to higher tier",
                "identified_at": datetime.utcnow().isoformat(),
                "confidence": min(100, max(approaching_limits, key=lambda x: x["usage_percent"])["usage_percent"]),
            }
        
        return None
    
    def _check_engagement_patterns(
        self,
        customer_id: str,
        engagement_data: Dict,
    ) -> Optional[Dict]:
        """Check engagement patterns to identify at-risk customers"""
        last_activity = engagement_data.get("last_activity_date")
        login_frequency = engagement_data.get("logins_last_30_days", 0)
        feature_usage = engagement_data.get("features_used", 0)
        
        if not last_activity:
            return None
        
        days_since_activity = (datetime.utcnow() - datetime.fromisoformat(last_activity)).days
        inactivity_threshold = self.trigger_thresholds.get("engagement_threshold_days", 14)
        
        if days_since_activity > inactivity_threshold:
            return {
                "customer_id": customer_id,
                "opportunity_type": UpsellOpportunity.ENGAGEMENT_LOW.value,
                "severity": "high" if days_since_activity > inactivity_threshold * 2 else "medium",
                "days_since_activity": days_since_activity,
                "logins_last_30_days": login_frequency,
                "features_used": feature_usage,
                "recommended_action": "Win-back campaign or feature education",
                "identified_at": datetime.utcnow().isoformat(),
                "confidence": min(100, (days_since_activity / inactivity_threshold) * 50),
            }
        
        return None
    
    def _assess_churn_risk(
        self,
        customer_id: str,
        customer_profile: Dict,
        engagement_data: Dict,
    ) -> Optional[Dict]:
        """Assess churn risk and identify prevention opportunities"""
        churn_score = self._calculate_churn_score(customer_profile, engagement_data)
        
        risk_threshold = self.trigger_thresholds.get("churn_risk_score", 0.6)
        
        if churn_score > risk_threshold:
            return {
                "customer_id": customer_id,
                "opportunity_type": UpsellOpportunity.CHURN_RISK.value,
                "churn_risk_score": round(churn_score, 2),
                "risk_level": "critical" if churn_score > 0.8 else "high" if churn_score > 0.7 else "medium",
                "risk_factors": self._identify_churn_factors(customer_profile, engagement_data),
                "recommended_action": "Retention offer or account review",
                "identified_at": datetime.utcnow().isoformat(),
                "confidence": min(100, churn_score * 100),
                "estimated_ltv": customer_profile.get("lifetime_value", 0),
            }
        
        return None
    
    def _calculate_churn_score(
        self,
        customer_profile: Dict,
        engagement_data: Dict,
    ) -> float:
        """Calculate churn risk score (0-1 scale)"""
        score = 0.0
        weights = {
            "inactivity": 0.3,
            "support_tickets": 0.2,
            "feature_usage": 0.2,
            "price_sensitivity": 0.15,
            "contract_age": 0.15,
        }
        
        # Inactivity factor
        last_activity = engagement_data.get("last_activity_date")
        if last_activity:
            days_inactive = (datetime.utcnow() - datetime.fromisoformat(last_activity)).days
            inactivity_factor = min(1.0, days_inactive / 60)
            score += inactivity_factor * weights["inactivity"]
        
        # Support tickets (complaints indicate risk)
        support_tickets = engagement_data.get("support_tickets_last_30_days", 0)
        tickets_factor = min(1.0, support_tickets / 5)
        score += tickets_factor * weights["support_tickets"]
        
        # Feature usage
        features_used = engagement_data.get("features_used", 0)
        expected_features = engagement_data.get("expected_features", 10)
        usage_factor = 1.0 - min(1.0, features_used / max(expected_features, 1))
        score += usage_factor * weights["feature_usage"]
        
        # Price sensitivity (high for lower tier)
        tier = customer_profile.get("tier", "starter")
        price_sensitivity = {"starter": 0.4, "professional": 0.2, "enterprise": 0.05}.get(tier, 0.2)
        score += price_sensitivity * weights["price_sensitivity"]
        
        # Contract age (newer customers more risky)
        account_age_days = customer_profile.get("account_age_days", 365)
        age_factor = max(0, 1.0 - (account_age_days / 180))
        score += age_factor * weights["contract_age"]
        
        return min(1.0, score)
    
    def _identify_churn_factors(
        self,
        customer_profile: Dict,
        engagement_data: Dict,
    ) -> List[str]:
        """Identify specific churn risk factors"""
        factors = []
        
        # Check each risk indicator
        last_activity = engagement_data.get("last_activity_date")
        if last_activity:
            days_inactive = (datetime.utcnow() - datetime.fromisoformat(last_activity)).days
            if days_inactive > 30:
                factors.append(f"No activity for {days_inactive} days")
        
        support_tickets = engagement_data.get("support_tickets_last_30_days", 0)
        if support_tickets > 3:
            factors.append(f"High support ticket volume ({support_tickets} in last 30 days)")
        
        features_used = engagement_data.get("features_used", 0)
        if features_used < 3:
            factors.append("Low feature adoption")
        
        if customer_profile.get("tier") == "starter":
            factors.append("Lower-tier customer (higher churn rate)")
        
        ltv = customer_profile.get("lifetime_value", 0)
        if ltv < 500:
            factors.append("Low lifetime value")
        
        return factors
    
    def _assess_expansion_potential(
        self,
        customer_id: str,
        customer_profile: Dict,
        usage_metrics: Dict,
    ) -> Optional[Dict]:
        """Assess potential for expansion/upsell growth"""
        growth_rate = customer_profile.get("monthly_growth_rate", 0)
        ltv = customer_profile.get("lifetime_value", 0)
        current_tier = customer_profile.get("tier", "starter")
        
        # Look for expansion signals
        expansion_threshold = self.trigger_thresholds.get("expansion_monthly_growth", 0.15)
        
        if growth_rate > expansion_threshold and ltv > 1000 and current_tier != "enterprise":
            return {
                "customer_id": customer_id,
                "opportunity_type": UpsellOpportunity.EXPANSION_POTENTIAL.value,
                "severity": "medium",
                "growth_rate": round(growth_rate * 100, 1),
                "lifetime_value": ltv,
                "current_tier": current_tier,
                "recommended_upgrade": self._recommend_upgrade(current_tier, growth_rate),
                "potential_annual_increase": round(ltv * growth_rate * 12, 2),
                "identified_at": datetime.utcnow().isoformat(),
                "confidence": min(100, (growth_rate / expansion_threshold) * 70),
            }
        
        return None
    
    def _recommend_upgrade(self, current_tier: str, growth_rate: float) -> str:
        """Recommend upgrade tier based on growth"""
        if current_tier == "starter":
            return "professional" if growth_rate > 0.1 else "starter"
        elif current_tier == "professional":
            return "enterprise" if growth_rate > 0.2 else "professional"
        else:
            return "enterprise"
    
    def calculate_engagement_score(
        self,
        customer_id: str,
        engagement_data: Dict,
    ) -> Dict:
        """
        Calculate overall engagement score for customer.
        
        Args:
            customer_id: Customer ID
            engagement_data: Engagement metrics
        
        Returns:
            Engagement score and breakdown
        """
        score = 0.0
        components = {}
        
        # Login frequency (max 30 points)
        logins = engagement_data.get("logins_last_30_days", 0)
        login_score = min(30, (logins / 10) * 30)
        components["login_frequency"] = round(login_score, 1)
        score += login_score
        
        # Feature usage (max 25 points)
        features_used = engagement_data.get("features_used", 0)
        expected_features = engagement_data.get("expected_features", 10)
        feature_score = (features_used / expected_features) * 25
        components["feature_adoption"] = round(feature_score, 1)
        score += feature_score
        
        # API usage (max 20 points)
        api_calls = engagement_data.get("api_calls_last_30_days", 0)
        api_score = min(20, (api_calls / 1000) * 20)
        components["api_usage"] = round(api_score, 1)
        score += api_score
        
        # Support interaction (max 15 points - positive engagement)
        support_interactions = engagement_data.get("support_interactions", 0)
        support_score = min(15, (support_interactions / 5) * 15)
        components["support_engagement"] = round(support_score, 1)
        score += support_score
        
        # Recency (max 10 points)
        last_activity = engagement_data.get("last_activity_date")
        if last_activity:
            days_since = (datetime.utcnow() - datetime.fromisoformat(last_activity)).days
            recency_score = max(0, 10 - (days_since / 10))
            components["recency"] = round(recency_score, 1)
            score += recency_score
        
        self.engagement_scores[customer_id] = {
            "score": round(score, 1),
            "components": components,
            "level": "high" if score > 75 else "medium" if score > 50 else "low",
            "calculated_at": datetime.utcnow().isoformat(),
        }
        
        return self.engagement_scores[customer_id]
    
    def create_upsell_campaign(
        self,
        customer_id: str,
        opportunity_type: str,
        target_tier: str,
        messaging: Dict,
        trigger_condition: str,
    ) -> Dict:
        """
        Create targeted upsell campaign for customer.
        
        Args:
            customer_id: Customer ID
            opportunity_type: Type of opportunity
            target_tier: Tier being promoted
            messaging: Campaign messaging
            trigger_condition: When to show offer
        
        Returns:
            Campaign configuration
        """
        campaign_id = f"campaign_{datetime.utcnow().timestamp()}"
        
        campaign = {
            "campaign_id": campaign_id,
            "customer_id": customer_id,
            "opportunity_type": opportunity_type,
            "target_tier": target_tier,
            "messaging": messaging,
            "trigger_condition": trigger_condition,
            "status": ConversionStage.IDENTIFIED.value,
            "created_at": datetime.utcnow().isoformat(),
            "views": 0,
            "clicks": 0,
            "conversions": 0,
            "ctr": 0,
            "conversion_rate": 0,
        }
        
        if customer_id not in self.conversion_funnels:
            self.conversion_funnels[customer_id] = []
        
        self.conversion_funnels[customer_id].append(campaign)
        
        return campaign
    
    def track_campaign_engagement(
        self,
        campaign_id: str,
        customer_id: str,
        event_type: str,
    ) -> Dict:
        """
        Track campaign engagement (views, clicks, conversions).
        
        Args:
            campaign_id: Campaign ID
            customer_id: Customer ID
            event_type: Event type (view, click, convert)
        
        Returns:
            Updated campaign metrics
        """
        campaigns = self.conversion_funnels.get(customer_id, [])
        campaign = next((c for c in campaigns if c["campaign_id"] == campaign_id), None)
        
        if not campaign:
            return {"status": "error"}
        
        if event_type == "view":
            campaign["views"] += 1
        elif event_type == "click":
            campaign["clicks"] += 1
            campaign["status"] = ConversionStage.ENGAGED.value
        elif event_type == "convert":
            campaign["conversions"] += 1
            campaign["status"] = ConversionStage.CONVERTED.value
        
        # Calculate metrics
        campaign["ctr"] = (campaign["clicks"] / max(campaign["views"], 1)) * 100
        campaign["conversion_rate"] = (campaign["conversions"] / max(campaign["views"], 1)) * 100
        
        return {
            "campaign_id": campaign_id,
            "views": campaign["views"],
            "clicks": campaign["clicks"],
            "conversions": campaign["conversions"],
            "ctr": round(campaign["ctr"], 2),
            "conversion_rate": round(campaign["conversion_rate"], 2),
        }
    
    def get_upsell_recommendations(self, customer_id: str) -> List[Dict]:
        """Get current upsell recommendations for customer"""
        return self.opportunities.get(customer_id, [])
    
    def get_conversion_funnel(self, customer_id: str) -> Dict:
        """Get conversion funnel status for customer"""
        campaigns = self.conversion_funnels.get(customer_id, [])
        
        return {
            "customer_id": customer_id,
            "total_campaigns": len(campaigns),
            "campaigns_by_stage": {
                stage.value: len([c for c in campaigns if c["status"] == stage.value])
                for stage in ConversionStage
            },
            "total_views": sum(c["views"] for c in campaigns),
            "total_clicks": sum(c["clicks"] for c in campaigns),
            "total_conversions": sum(c["conversions"] for c in campaigns),
            "overall_ctr": (sum(c["clicks"] for c in campaigns) / max(sum(c["views"] for c in campaigns), 1)) * 100 if campaigns else 0,
            "overall_conversion_rate": (sum(c["conversions"] for c in campaigns) / max(sum(c["views"] for c in campaigns), 1)) * 100 if campaigns else 0,
        }
