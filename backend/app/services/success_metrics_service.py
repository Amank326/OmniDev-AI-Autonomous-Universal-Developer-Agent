"""
Customer Success Metrics Service - Health scoring and CSM recommendations
Calculates health scores, identifies expansion opportunities, and recommends CSM actions
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class HealthMetric(Enum):
    """Health score components"""
    NPS = "nps"
    FEATURE_ADOPTION = "feature_adoption"
    ENGAGEMENT = "engagement"
    SUPPORT_SENTIMENT = "support_sentiment"
    REVENUE_TREND = "revenue_trend"
    EXPANSION_CAPACITY = "expansion_capacity"


class CustomerHealthLevel(Enum):
    """Customer health classification"""
    THRIVING = "thriving"  # Score 80-100
    HEALTHY = "healthy"     # Score 60-79
    AT_RISK = "at_risk"     # Score 40-59
    CRITICAL = "critical"   # Score 0-39


class SuccessMetricsService:
    """
    Calculate customer success metrics and health scores
    Identifies expansion opportunities and CSM recommendations
    """
    
    def __init__(self):
        """Initialize success metrics service"""
        self.health_scores = {}
        self.csm_recommendations = {}
        self.nps_scores = {}
        self.feature_adoption = {}
        self.engagement_trends = {}
        self.revenue_metrics = {}
        self.expansion_opportunities = {}
    
    # ========================================================================
    # HEALTH SCORE CALCULATION (0-100 scale)
    # ========================================================================
    
    def calculate_health_score(
        self,
        customer_id: str,
        usage_metrics: Dict,
        support_metrics: Dict,
        engagement_metrics: Dict,
        revenue_metrics: Dict,
        nps_score: Optional[float] = None,
    ) -> Dict:
        """
        Calculate comprehensive customer health score
        
        Components (weighted):
        - Feature Adoption (25%): % features in use
        - Engagement Level (25%): Login frequency, API calls
        - Support Sentiment (15%): Support ticket sentiment
        - Revenue Trend (20%): MRR growth/decline
        - NPS Score (15%): Net Promoter Score (if available)
        
        Returns:
        - Overall score (0-100)
        - Component scores
        - Health level classification
        - Key drivers
        - Risk factors
        """
        
        # Calculate component scores
        adoption_score = self._calculate_adoption_score(usage_metrics)
        engagement_score = self._calculate_engagement_score(engagement_metrics)
        support_score = self._calculate_support_score(support_metrics)
        revenue_score = self._calculate_revenue_score(revenue_metrics)
        nps_component = self._calculate_nps_component(nps_score)
        
        # Weighted calculation
        overall_score = (
            adoption_score * 0.25 +
            engagement_score * 0.25 +
            support_score * 0.15 +
            revenue_score * 0.20 +
            nps_component * 0.15
        )
        
        # Determine health level
        if overall_score >= 80:
            health_level = CustomerHealthLevel.THRIVING
        elif overall_score >= 60:
            health_level = CustomerHealthLevel.HEALTHY
        elif overall_score >= 40:
            health_level = CustomerHealthLevel.AT_RISK
        else:
            health_level = CustomerHealthLevel.CRITICAL
        
        # Identify key drivers and risks
        key_drivers = self._identify_key_drivers({
            "adoption": adoption_score,
            "engagement": engagement_score,
            "support": support_score,
            "revenue": revenue_score,
            "nps": nps_component,
        })
        
        risk_factors = self._identify_risk_factors({
            "adoption": adoption_score,
            "engagement": engagement_score,
            "support": support_score,
            "revenue": revenue_score,
        })
        
        result = {
            "customer_id": customer_id,
            "overall_score": round(overall_score, 1),
            "health_level": health_level.value,
            "calculated_at": datetime.utcnow().isoformat(),
            "component_scores": {
                "feature_adoption": round(adoption_score, 1),
                "engagement": round(engagement_score, 1),
                "support_sentiment": round(support_score, 1),
                "revenue_trend": round(revenue_score, 1),
                "nps": round(nps_component, 1),
            },
            "key_drivers": key_drivers,
            "risk_factors": risk_factors,
            "trend": self._calculate_health_trend(customer_id, overall_score),
        }
        
        # Store health score
        self.health_scores[customer_id] = result
        return result
    
    def _calculate_adoption_score(self, usage_metrics: Dict) -> float:
        """Calculate feature adoption score (0-100)"""
        if not usage_metrics:
            return 0
        
        total_features = usage_metrics.get("total_features", 1)
        features_used = usage_metrics.get("features_used", 0)
        unique_users_per_feature = usage_metrics.get("unique_users_per_feature", 0)
        
        # Feature breadth (% features used)
        breadth_score = (features_used / total_features * 100) if total_features > 0 else 0
        
        # Feature depth (% users per feature)
        depth_score = min(100, (unique_users_per_feature / total_features * 100)) if total_features > 0 else 0
        
        # Combined adoption (60% breadth, 40% depth)
        adoption = (breadth_score * 0.6) + (depth_score * 0.4)
        
        return min(100, adoption)
    
    def _calculate_engagement_score(self, engagement_metrics: Dict) -> float:
        """Calculate engagement score (0-100)"""
        if not engagement_metrics:
            return 0
        
        logins_30d = engagement_metrics.get("logins_last_30_days", 0)
        api_calls_30d = engagement_metrics.get("api_calls_last_30_days", 0)
        days_since_activity = engagement_metrics.get("days_since_last_activity", 30)
        
        # Login frequency (0-40 points)
        login_score = min(40, logins_30d / 30 * 40)  # Target: 1+ login per day
        
        # API usage (0-30 points)
        api_score = min(30, api_calls_30d / 300 * 30)  # Target: 10+ calls per day
        
        # Recency (0-30 points)
        if days_since_activity == 0:
            recency_score = 30
        elif days_since_activity <= 7:
            recency_score = 25
        elif days_since_activity <= 14:
            recency_score = 20
        elif days_since_activity <= 30:
            recency_score = 10
        else:
            recency_score = 0
        
        return login_score + api_score + recency_score
    
    def _calculate_support_score(self, support_metrics: Dict) -> float:
        """Calculate support sentiment score (0-100)"""
        if not support_metrics:
            return 50  # Default to neutral
        
        avg_sentiment = support_metrics.get("average_sentiment", 0)  # -1 to 1
        response_time_hours = support_metrics.get("avg_response_time_hours", 24)
        issue_resolution_days = support_metrics.get("avg_resolution_days", 7)
        satisfaction_rating = support_metrics.get("satisfaction_rating", 3)  # 1-5 scale
        
        # Sentiment score (0-50 points)
        # -1 = 0, 0 = 25, 1 = 50
        sentiment_score = (avg_sentiment + 1) / 2 * 50
        
        # Response time (0-25 points)
        if response_time_hours <= 4:
            response_score = 25
        elif response_time_hours <= 8:
            response_score = 20
        elif response_time_hours <= 24:
            response_score = 15
        else:
            response_score = max(0, 15 - (response_time_hours - 24) / 24)
        
        # Resolution time (0-25 points)
        if issue_resolution_days <= 1:
            resolution_score = 25
        elif issue_resolution_days <= 3:
            resolution_score = 20
        elif issue_resolution_days <= 7:
            resolution_score = 15
        else:
            resolution_score = max(0, 15 - (issue_resolution_days - 7) / 7)
        
        return sentiment_score + response_score + resolution_score
    
    def _calculate_revenue_score(self, revenue_metrics: Dict) -> float:
        """Calculate revenue health score (0-100)"""
        if not revenue_metrics:
            return 50
        
        mrr_trend = revenue_metrics.get("mrr_trend", 0)  # -1 to 1
        expansion_revenue = revenue_metrics.get("expansion_revenue", 0)
        contraction_revenue = revenue_metrics.get("contraction_revenue", 0)
        
        # Trend score (0-60 points)
        # Positive trend = higher score
        if mrr_trend > 0.1:
            trend_score = 60
        elif mrr_trend > 0:
            trend_score = 45
        elif mrr_trend > -0.1:
            trend_score = 30
        else:
            trend_score = max(0, 30 + (mrr_trend * 300))
        
        # Expansion bonus (0-40 points)
        net_expansion = expansion_revenue - contraction_revenue
        expansion_score = min(40, max(0, net_expansion / 100 * 40))
        
        return trend_score + expansion_score
    
    def _calculate_nps_component(self, nps_score: Optional[float]) -> float:
        """Convert NPS score to health component (0-100)"""
        if nps_score is None:
            return 50  # Default to neutral
        
        # NPS ranges from -100 to 100, convert to 0-100
        return (nps_score + 100) / 2
    
    def _identify_key_drivers(self, component_scores: Dict) -> List[str]:
        """Identify top 2-3 drivers of health score"""
        sorted_components = sorted(
            component_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        drivers = []
        component_names = {
            "adoption": "Strong feature adoption",
            "engagement": "High engagement levels",
            "support": "Positive support experience",
            "revenue": "Growing revenue",
            "nps": "High NPS/customer satisfaction",
        }
        
        for component, score in sorted_components[:3]:
            if score > 60:
                drivers.append(component_names.get(component, component))
        
        return drivers or ["Stable account baseline"]
    
    def _identify_risk_factors(self, component_scores: Dict) -> List[str]:
        """Identify risk factors (low-scoring components)"""
        risks = []
        risk_names = {
            "adoption": "Low feature adoption",
            "engagement": "Declining engagement",
            "support": "Support issues/negative sentiment",
            "revenue": "Declining revenue/contraction",
        }
        
        for component, score in component_scores.items():
            if score < 40:
                risks.append(risk_names.get(component, component))
        
        return risks
    
    def _calculate_health_trend(
        self,
        customer_id: str,
        current_score: float
    ) -> str:
        """Determine if health is improving/declining/stable"""
        if customer_id not in self.health_scores:
            return "stable"
        
        previous_score = self.health_scores[customer_id]["overall_score"]
        diff = current_score - previous_score
        
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"
    
    # ========================================================================
    # NPS MANAGEMENT
    # ========================================================================
    
    def record_nps_response(
        self,
        customer_id: str,
        score: int,
        feedback: Optional[str] = None,
    ) -> Dict:
        """
        Record NPS (Net Promoter Score) response
        
        Score: 0-10
        - 0-6: Detractors
        - 7-8: Passives
        - 9-10: Promoters
        """
        
        if not 0 <= score <= 10:
            raise ValueError("NPS score must be between 0 and 10")
        
        # Determine segment
        if score <= 6:
            segment = "detractors"
            segment_name = "Detractor"
        elif score <= 8:
            segment = "passives"
            segment_name = "Passive"
        else:
            segment = "promoters"
            segment_name = "Promoter"
        
        response = {
            "customer_id": customer_id,
            "score": score,
            "segment": segment,
            "segment_name": segment_name,
            "feedback": feedback,
            "recorded_at": datetime.utcnow().isoformat(),
        }
        
        # Store response
        if customer_id not in self.nps_scores:
            self.nps_scores[customer_id] = []
        self.nps_scores[customer_id].append(response)
        
        return response
    
    def get_nps_trends(self, lookback_days: int = 90) -> Dict:
        """
        Get NPS trends across customer base
        
        Returns:
        - Overall NPS (% promoters - % detractors)
        - Distribution (promoters, passives, detractors)
        - Trend (improving/declining/stable)
        """
        
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        total = 0
        promoters = 0
        passives = 0
        detractors = 0
        
        for customer_scores in self.nps_scores.values():
            for response in customer_scores:
                response_date = datetime.fromisoformat(response["recorded_at"])
                if response_date < cutoff_date:
                    continue
                
                total += 1
                if response["segment"] == "promoters":
                    promoters += 1
                elif response["segment"] == "passives":
                    passives += 1
                else:
                    detractors += 1
        
        if total == 0:
            return {
                "overall_nps": 0,
                "promoters_percent": 0,
                "passives_percent": 0,
                "detractors_percent": 0,
                "sample_size": 0,
            }
        
        nps = (promoters - detractors) / total * 100
        
        return {
            "overall_nps": round(nps, 1),
            "promoters_percent": round(promoters / total * 100, 1),
            "passives_percent": round(passives / total * 100, 1),
            "detractors_percent": round(detractors / total * 100, 1),
            "sample_size": total,
            "promoters_count": promoters,
            "passives_count": passives,
            "detractors_count": detractors,
        }
    
    # ========================================================================
    # EXPANSION OPPORTUNITY IDENTIFICATION
    # ========================================================================
    
    def identify_expansion_opportunities(
        self,
        customer_id: str,
        current_tier: str,
        usage_metrics: Dict,
        engagement_metrics: Dict,
        support_interactions: int,
    ) -> List[Dict]:
        """
        Identify expansion opportunities based on customer health and usage
        
        Opportunities:
        1. Tier upgrade (high usage approaching limits)
        2. Feature adoption (unused paid features)
        3. Seat expansion (growing team)
        4. Add-on services (complementary offerings)
        5. Enterprise features (scaling needs)
        """
        
        opportunities = []
        
        # Check tier upgrade opportunity
        usage_percent = usage_metrics.get("usage_percent", 0)
        if usage_percent > 70:
            opportunities.append({
                "type": "tier_upgrade",
                "title": "Upgrade Plan",
                "description": f"You're using {usage_percent}% of your plan limits",
                "priority": "high" if usage_percent > 80 else "medium",
                "potential_arpu_increase": 50,  # Estimated
                "confidence": 0.85,
            })
        
        # Check seat expansion opportunity
        active_users = engagement_metrics.get("unique_active_users", 0)
        allocated_seats = engagement_metrics.get("allocated_seats", 0)
        
        if active_users > allocated_seats * 0.7:
            opportunities.append({
                "type": "seat_expansion",
                "title": "Add Team Members",
                "description": f"{active_users} active users, but only {allocated_seats} seats allocated",
                "priority": "high",
                "potential_arpu_increase": 30 * (active_users - allocated_seats),
                "confidence": 0.90,
            })
        
        # Check feature adoption opportunity
        features_available = usage_metrics.get("features_available", 0)
        features_used = usage_metrics.get("features_used", 0)
        adoption_rate = (features_used / features_available * 100) if features_available > 0 else 0
        
        if adoption_rate < 60:
            opportunities.append({
                "type": "feature_adoption",
                "title": "Unlock More Value",
                "description": f"Only using {adoption_rate:.0f}% of available features",
                "priority": "medium",
                "potential_arpu_increase": 20,
                "confidence": 0.75,
                "unused_features": features_available - features_used,
            })
        
        # Check support engagement opportunity
        if support_interactions > 10:  # Engaged customer
            opportunities.append({
                "type": "premium_support",
                "title": "Priority Support Package",
                "description": "Your usage patterns suggest premium support would be valuable",
                "priority": "medium",
                "potential_arpu_increase": 50,
                "confidence": 0.70,
            })
        
        # Check professional services opportunity
        if current_tier == "Professional" and engagement_metrics.get("is_growing", False):
            opportunities.append({
                "type": "professional_services",
                "title": "Implementation Services",
                "description": "Optimize your setup with our implementation team",
                "priority": "low",
                "potential_arpu_increase": 200,
                "confidence": 0.60,
            })
        
        self.expansion_opportunities[customer_id] = opportunities
        return opportunities
    
    # ========================================================================
    # CSM RECOMMENDATIONS
    # ========================================================================
    
    def generate_csm_recommendations(
        self,
        customer_id: str,
        health_score: Dict,
        expansion_opportunities: List[Dict],
        recent_interactions: int,
    ) -> List[Dict]:
        """
        Generate CSM action recommendations based on customer health
        
        Recommendation Types:
        - Business Review: Deep dive on usage and goals
        - Training: Feature adoption workshops
        - Expansion: Upsell/cross-sell opportunities
        - Retention: At-risk customer interventions
        - Success: Best practice sharing
        """
        
        recommendations = []
        health_level = health_score.get("health_level")
        score = health_score.get("overall_score", 0)
        
        # Thriving customers - expansion focus
        if health_level == "thriving":
            if expansion_opportunities:
                recommendations.append({
                    "type": "expansion",
                    "action": "Schedule expansion conversation",
                    "description": "Customer is thriving and ready to expand",
                    "priority": "high",
                    "csm_activity": "Quarterly business review with expansion focus",
                    "timeline": "This week",
                    "expected_outcome": "Identify expansion opportunities",
                })
            
            recommendations.append({
                "type": "success",
                "action": "Share best practices",
                "description": "Learn from this success story",
                "priority": "medium",
                "csm_activity": "Case study interview",
                "timeline": "This month",
                "expected_outcome": "Marketing asset and peer learning",
            })
        
        # Healthy customers - engagement focus
        elif health_level == "healthy":
            recommendations.append({
                "type": "business_review",
                "action": "Conduct business review",
                "description": "Align on goals and progress",
                "priority": "medium",
                "csm_activity": "Quarterly business review",
                "timeline": "This month",
                "expected_outcome": "Ensure alignment and identify gaps",
            })
            
            if expansion_opportunities:
                recommendations.append({
                    "type": "expansion",
                    "action": "Explore growth opportunities",
                    "description": f"{len(expansion_opportunities)} expansion opportunities identified",
                    "priority": "medium",
                    "csm_activity": "Opportunity deep-dive call",
                    "timeline": "Next 2 weeks",
                    "expected_outcome": "Path to expansion",
                })
        
        # At-risk customers - retention focus
        elif health_level == "at_risk":
            recommendations.append({
                "type": "retention",
                "action": "Immediate outreach required",
                "description": "Customer health declining",
                "priority": "critical",
                "csm_activity": "Executive check-in call",
                "timeline": "ASAP",
                "expected_outcome": "Understand issues and create recovery plan",
            })
            
            if score < 50:
                recommendations.append({
                    "type": "training",
                    "action": "Feature adoption training",
                    "description": "Low feature adoption contributing to at-risk status",
                    "priority": "high",
                    "csm_activity": "Personalized training session",
                    "timeline": "This week",
                    "expected_outcome": "Increase feature adoption and value realization",
                })
        
        # Critical customers - emergency intervention
        else:  # critical
            recommendations.append({
                "type": "retention",
                "action": "Emergency intervention",
                "description": "Customer at critical risk of churn",
                "priority": "critical",
                "csm_activity": "Leadership escalation + retention offer",
                "timeline": "TODAY",
                "expected_outcome": "Save account or understand exit",
            })
        
        # Add quarterly touchpoint if no recent interactions
        if recent_interactions == 0:
            recommendations.append({
                "type": "business_review",
                "action": "Schedule quarterly check-in",
                "description": "No recent interactions with customer",
                "priority": "medium",
                "csm_activity": "Schedule call with customer",
                "timeline": "This week",
                "expected_outcome": "Confirm customer health and priorities",
            })
        
        self.csm_recommendations[customer_id] = recommendations
        return recommendations
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    def get_health_distribution(self) -> Dict:
        """Get distribution of customer health across all accounts"""
        
        distribution = {
            "thriving": 0,
            "healthy": 0,
            "at_risk": 0,
            "critical": 0,
            "total": len(self.health_scores),
        }
        
        for score_data in self.health_scores.values():
            level = score_data["health_level"]
            distribution[level] += 1
        
        if distribution["total"] == 0:
            return distribution
        
        # Calculate percentages
        for level in ["thriving", "healthy", "at_risk", "critical"]:
            distribution[f"{level}_percent"] = round(
                distribution[level] / distribution["total"] * 100, 1
            )
        
        return distribution
    
    def get_top_expansion_customers(self, limit: int = 10) -> List[Dict]:
        """Get customers with highest expansion potential"""
        
        expansion_list = []
        
        for customer_id, opportunities in self.expansion_opportunities.items():
            if not opportunities:
                continue
            
            total_potential = sum(
                opp.get("potential_arpu_increase", 0) for opp in opportunities
            )
            avg_confidence = sum(
                opp.get("confidence", 0) for opp in opportunities
            ) / len(opportunities) if opportunities else 0
            
            expansion_list.append({
                "customer_id": customer_id,
                "opportunities_count": len(opportunities),
                "total_potential_arpu": round(total_potential, 0),
                "avg_confidence": round(avg_confidence, 2),
                "top_opportunity": opportunities[0]["type"] if opportunities else None,
            })
        
        # Sort by potential revenue * confidence
        expansion_list.sort(
            key=lambda x: x["total_potential_arpu"] * x["avg_confidence"],
            reverse=True
        )
        
        return expansion_list[:limit]
    
    def get_at_risk_summary(self) -> Dict:
        """Get summary of at-risk and critical accounts"""
        
        at_risk_customers = []
        critical_customers = []
        
        for customer_id, score_data in self.health_scores.items():
            level = score_data["health_level"]
            
            if level == "at_risk":
                at_risk_customers.append({
                    "customer_id": customer_id,
                    "score": score_data["overall_score"],
                    "trend": score_data["trend"],
                    "key_risk": score_data["risk_factors"][0] if score_data["risk_factors"] else None,
                })
            elif level == "critical":
                critical_customers.append({
                    "customer_id": customer_id,
                    "score": score_data["overall_score"],
                    "trend": score_data["trend"],
                    "key_risk": score_data["risk_factors"][0] if score_data["risk_factors"] else None,
                })
        
        return {
            "critical_count": len(critical_customers),
            "at_risk_count": len(at_risk_customers),
            "critical_customers": critical_customers,
            "at_risk_customers": at_risk_customers,
            "total_mrr_at_risk": len(critical_customers) * 500 + len(at_risk_customers) * 250,  # Placeholder
        }
