"""
Retention Intervention Service - Churn prevention campaigns and effectiveness tracking
Manages retention campaigns, tracks responses, and measures impact
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class InterventionType(Enum):
    """Types of retention interventions"""
    DISCOUNT = "discount"              # Price reduction
    UPGRADE = "upgrade"                # Feature unlock
    TRAINING = "training"              # Personalized training
    SUPPORT = "support"                # Escalated support
    BUSINESS_REVIEW = "business_review"  # Executive check-in
    CUSTOM_SOLUTION = "custom_solution"  # Custom implementation


class InterventionStatus(Enum):
    """Intervention lifecycle status"""
    IDENTIFIED = "identified"
    PLANNED = "planned"
    OFFERED = "offered"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class InterventionOutcome(Enum):
    """Intervention outcomes"""
    CHURN_PREVENTED = "churn_prevented"
    EXPANDED = "expanded"
    MAINTAINED = "maintained"
    CHURNED = "churned"


class RetentionInterventionService:
    """
    Design and execute retention campaigns
    Track effectiveness and calculate retention ROI
    """
    
    def __init__(self):
        """Initialize retention intervention service"""
        self.interventions = {}
        self.campaigns = {}
        self.responses = {}
        self.outcomes = {}
        self.effectiveness_metrics = {}
        self.intervention_templates = self._create_templates()
    
    def _create_templates(self) -> Dict:
        """Create intervention templates by type"""
        return {
            InterventionType.DISCOUNT.value: {
                "name": "Discount Offer",
                "discount_range": (10, 40),  # 10-40% discount
                "duration_months": 3,
                "message_template": "As a valued customer, we're offering you {discount}% off for {duration} months",
                "cost_per_intervention": 50,
            },
            InterventionType.UPGRADE.value: {
                "name": "Tier Upgrade",
                "duration_months": 1,
                "message_template": "Experience {feature_name} for free for {duration} month with no strings attached",
                "cost_per_intervention": 75,
            },
            InterventionType.TRAINING.value: {
                "name": "Personalized Training",
                "duration_hours": 2,
                "message_template": "We'd love to help you get more value - claim your free {duration} hour training session",
                "cost_per_intervention": 100,
            },
            InterventionType.SUPPORT.value: {
                "name": "Premium Support",
                "duration_months": 3,
                "message_template": "Get priority support from our team for the next {duration} months at no additional cost",
                "cost_per_intervention": 60,
            },
            InterventionType.BUSINESS_REVIEW.value: {
                "name": "Strategic Review",
                "duration_hours": 1.5,
                "message_template": "Let's schedule a strategic review to align on your goals and roadmap",
                "cost_per_intervention": 150,
            },
            InterventionType.CUSTOM_SOLUTION.value: {
                "name": "Custom Implementation",
                "duration_weeks": 4,
                "message_template": "We want to build a custom solution for your unique needs - let's discuss",
                "cost_per_intervention": 500,
            },
        }
    
    # ========================================================================
    # INTERVENTION PLANNING & CREATION
    # ========================================================================
    
    def plan_intervention(
        self,
        customer_id: str,
        intervention_type: str,
        trigger: str,
        urgency: str,
        churn_probability: float,
        potential_mrr: float,
    ) -> Dict:
        """
        Plan retention intervention based on churn signal
        
        Decision logic:
        - Urgency (critical/high/medium) → Select intervention type + timeline
        - Churn probability → Determine offer value
        - MRR → Calculate acceptable intervention cost
        """
        
        intervention_id = f"int_{customer_id}_{datetime.utcnow().timestamp()}"
        
        # Recommend intervention strategy
        if urgency == "critical" and churn_probability > 0.7:
            # High-value account at critical risk
            if potential_mrr > 1000:
                recommended_type = InterventionType.BUSINESS_REVIEW.value
            else:
                recommended_type = InterventionType.DISCOUNT.value
            timeline_hours = 4  # Act immediately
        
        elif urgency == "high" or churn_probability > 0.5:
            # Medium value account at risk
            recommended_type = InterventionType.TRAINING.value
            timeline_hours = 24
        
        else:
            # Lower risk, offer engagement
            recommended_type = InterventionType.SUPPORT.value
            timeline_hours = 72
        
        # Calculate acceptable cost
        acceptable_cost = potential_mrr * 0.25  # Max 25% of MRR as intervention cost
        template = self.intervention_templates[recommended_type]
        
        # Determine if custom solution needed
        if churn_probability > 0.8 and potential_mrr > 2000:
            recommended_type = InterventionType.CUSTOM_SOLUTION.value
            template = self.intervention_templates[recommended_type]
        
        intervention = {
            "intervention_id": intervention_id,
            "customer_id": customer_id,
            "type": recommended_type,
            "trigger": trigger,
            "urgency": urgency,
            "churn_probability": round(churn_probability, 2),
            "potential_mrr": round(potential_mrr, 0),
            "status": InterventionStatus.PLANNED.value,
            "template": template.get("name"),
            "acceptable_cost": round(acceptable_cost, 0),
            "estimated_cost": template.get("cost_per_intervention"),
            "action_timeline_hours": timeline_hours,
            "planned_at": datetime.utcnow().isoformat(),
        }
        
        self.interventions[intervention_id] = intervention
        return intervention
    
    def create_intervention_offer(
        self,
        intervention_id: str,
        offer_details: Dict,
    ) -> Dict:
        """
        Create and send intervention offer to customer
        
        Details include:
        - Offer value (discount %, feature access, etc.)
        - Duration
        - Message/positioning
        - CTA
        """
        
        if intervention_id not in self.interventions:
            raise ValueError(f"Intervention {intervention_id} not found")
        
        intervention = self.interventions[intervention_id]
        customer_id = intervention["customer_id"]
        
        offer = {
            "offer_id": f"offer_{intervention_id}",
            "intervention_id": intervention_id,
            "customer_id": customer_id,
            "offer_type": intervention["type"],
            "offer_details": offer_details,
            "message": offer_details.get("message"),
            "offer_value": offer_details.get("value"),
            "expires_at": (datetime.utcnow() + timedelta(days=offer_details.get("validity_days", 7))).isoformat(),
            "offered_at": datetime.utcnow().isoformat(),
            "status": "pending",
            "channel": offer_details.get("channel", "email"),
        }
        
        # Store offer
        if customer_id not in self.campaigns:
            self.campaigns[customer_id] = []
        self.campaigns[customer_id].append(offer)
        
        # Update intervention status
        intervention["status"] = InterventionStatus.OFFERED.value
        intervention["offer_id"] = offer["offer_id"]
        
        return offer
    
    # ========================================================================
    # RESPONSE TRACKING
    # ========================================================================
    
    def track_offer_response(
        self,
        offer_id: str,
        response_type: str,
        response_detail: Optional[str] = None,
    ) -> Dict:
        """
        Track customer response to intervention offer
        
        Response types:
        - accepted: Customer accepts offer
        - declined: Customer declines
        - expired: Offer expired
        - no_response: No response within validity period
        """
        
        response = {
            "offer_id": offer_id,
            "response_type": response_type,
            "detail": response_detail,
            "responded_at": datetime.utcnow().isoformat(),
        }
        
        # Store response
        if offer_id not in self.responses:
            self.responses[offer_id] = []
        self.responses[offer_id].append(response)
        
        # Find corresponding offer and intervention
        offer = None
        intervention = None
        
        for offers_list in self.campaigns.values():
            for o in offers_list:
                if o["offer_id"] == offer_id:
                    offer = o
                    intervention_id = o["intervention_id"]
                    intervention = self.interventions.get(intervention_id)
                    break
        
        if offer:
            offer["status"] = "accepted" if response_type == "accepted" else "declined"
        
        if intervention:
            if response_type == "accepted":
                intervention["status"] = InterventionStatus.ACCEPTED.value
            elif response_type == "declined":
                intervention["status"] = InterventionStatus.DECLINED.value
        
        return response
    
    def mark_intervention_complete(
        self,
        intervention_id: str,
        completion_details: Dict,
    ) -> Dict:
        """
        Mark intervention as complete
        Records actual outcome (churn prevented, expanded, etc.)
        """
        
        if intervention_id not in self.interventions:
            raise ValueError(f"Intervention {intervention_id} not found")
        
        intervention = self.interventions[intervention_id]
        customer_id = intervention["customer_id"]
        
        completion = {
            "intervention_id": intervention_id,
            "customer_id": customer_id,
            "outcome": completion_details.get("outcome"),
            "outcome_detail": completion_details.get("detail"),
            "revenue_impact": completion_details.get("revenue_impact", 0),
            "completed_at": datetime.utcnow().isoformat(),
        }
        
        # Store outcome
        if customer_id not in self.outcomes:
            self.outcomes[customer_id] = []
        self.outcomes[customer_id].append(completion)
        
        # Update intervention
        intervention["status"] = InterventionStatus.COMPLETED.value
        intervention["outcome"] = completion_details.get("outcome")
        intervention["revenue_impact"] = completion_details.get("revenue_impact", 0)
        
        return completion
    
    # ========================================================================
    # EFFECTIVENESS MEASUREMENT
    # ========================================================================
    
    def calculate_intervention_effectiveness(
        self,
        intervention_id: str,
    ) -> Dict:
        """
        Calculate ROI and effectiveness of intervention
        
        Metrics:
        - Churn prevented (yes/no)
        - Revenue impact ($)
        - ROI (revenue impact / cost)
        - Acceptance rate
        """
        
        if intervention_id not in self.interventions:
            raise ValueError(f"Intervention {intervention_id} not found")
        
        intervention = self.interventions[intervention_id]
        
        # Get intervention outcome
        outcome = None
        customer_id = intervention["customer_id"]
        
        if customer_id in self.outcomes:
            for o in self.outcomes[customer_id]:
                if o["intervention_id"] == intervention_id:
                    outcome = o
                    break
        
        # Calculate metrics
        churn_prevented = outcome and outcome.get("outcome") == "churn_prevented" if outcome else False
        revenue_impact = outcome.get("revenue_impact", 0) if outcome else 0
        cost = intervention.get("estimated_cost", 0)
        
        roi = ((revenue_impact - cost) / cost * 100) if cost > 0 else 0
        
        effectiveness = {
            "intervention_id": intervention_id,
            "intervention_type": intervention["type"],
            "churn_prevented": churn_prevented,
            "revenue_impact": round(revenue_impact, 0),
            "cost": cost,
            "net_impact": round(revenue_impact - cost, 0),
            "roi_percent": round(roi, 1),
            "successful": churn_prevented or revenue_impact > cost,
            "outcome": outcome.get("outcome") if outcome else "unknown",
        }
        
        if customer_id not in self.effectiveness_metrics:
            self.effectiveness_metrics[customer_id] = []
        self.effectiveness_metrics[customer_id].append(effectiveness)
        
        return effectiveness
    
    def get_campaign_performance(
        self,
        intervention_type: Optional[str] = None,
        lookback_days: int = 90,
    ) -> Dict:
        """
        Get performance metrics for intervention campaigns
        
        Grouped by:
        - Intervention type
        - Urgency level
        - Churn probability range
        """
        
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        total_interventions = 0
        total_accepted = 0
        total_churn_prevented = 0
        total_revenue_impact = 0
        total_cost = 0
        
        type_breakdown = {}
        
        for int_id, intervention in self.interventions.items():
            planned_date = datetime.fromisoformat(intervention.get("planned_at"))
            if planned_date < cutoff_date:
                continue
            
            # Filter by type if specified
            if intervention_type and intervention["type"] != intervention_type:
                continue
            
            total_interventions += 1
            
            # Count accepted
            if intervention["status"] == InterventionStatus.ACCEPTED.value:
                total_accepted += 1
            
            # Count churn prevented
            if intervention.get("outcome") == InterventionOutcome.CHURN_PREVENTED.value:
                total_churn_prevented += 1
            
            # Sum revenue impact and cost
            total_revenue_impact += intervention.get("revenue_impact", 0)
            total_cost += intervention.get("estimated_cost", 0)
            
            # Type breakdown
            itype = intervention["type"]
            if itype not in type_breakdown:
                type_breakdown[itype] = {
                    "count": 0,
                    "accepted": 0,
                    "churn_prevented": 0,
                    "revenue_impact": 0,
                    "cost": 0,
                }
            
            type_breakdown[itype]["count"] += 1
            if intervention["status"] == InterventionStatus.ACCEPTED.value:
                type_breakdown[itype]["accepted"] += 1
            if intervention.get("outcome") == InterventionOutcome.CHURN_PREVENTED.value:
                type_breakdown[itype]["churn_prevented"] += 1
            type_breakdown[itype]["revenue_impact"] += intervention.get("revenue_impact", 0)
            type_breakdown[itype]["cost"] += intervention.get("estimated_cost", 0)
        
        # Calculate rates and ROI by type
        for itype in type_breakdown:
            breakdown = type_breakdown[itype]
            breakdown["acceptance_rate"] = round(
                breakdown["accepted"] / breakdown["count"] * 100, 1
            ) if breakdown["count"] > 0 else 0
            breakdown["churn_prevention_rate"] = round(
                breakdown["churn_prevented"] / breakdown["count"] * 100, 1
            ) if breakdown["count"] > 0 else 0
            breakdown["roi_percent"] = round(
                ((breakdown["revenue_impact"] - breakdown["cost"]) / breakdown["cost"] * 100), 1
            ) if breakdown["cost"] > 0 else 0
        
        return {
            "period_days": lookback_days,
            "total_interventions": total_interventions,
            "total_accepted": total_accepted,
            "acceptance_rate": round(total_accepted / total_interventions * 100, 1) if total_interventions > 0 else 0,
            "total_churn_prevented": total_churn_prevented,
            "churn_prevention_rate": round(total_churn_prevented / total_interventions * 100, 1) if total_interventions > 0 else 0,
            "total_revenue_impact": round(total_revenue_impact, 0),
            "total_cost": total_cost,
            "net_impact": round(total_revenue_impact - total_cost, 0),
            "overall_roi_percent": round(((total_revenue_impact - total_cost) / total_cost * 100), 1) if total_cost > 0 else 0,
            "by_intervention_type": type_breakdown,
        }
    
    # ========================================================================
    # RECOMMENDATION ENGINE
    # ========================================================================
    
    def get_intervention_recommendations(
        self,
        customer_id: str,
        churn_signals: Dict,
        potential_ltv: float,
    ) -> List[Dict]:
        """
        Get recommended interventions based on churn signals
        
        Considers:
        - Churn probability
        - Account value
        - Customer segment
        - Reason for churn
        - Effectiveness history
        """
        
        recommendations = []
        churn_prob = churn_signals.get("probability", 0.5)
        primary_reason = churn_signals.get("primary_reason", "unknown")
        
        # High-value accounts get premium interventions
        if potential_ltv > 5000:
            if churn_prob > 0.8:
                recommendations.append({
                    "type": InterventionType.CUSTOM_SOLUTION.value,
                    "priority": "critical",
                    "rationale": f"High-value account at critical risk",
                    "expected_success_rate": 0.70,
                })
            if churn_prob > 0.6:
                recommendations.append({
                    "type": InterventionType.BUSINESS_REVIEW.value,
                    "priority": "high",
                    "rationale": "Executive engagement for strategic alignment",
                    "expected_success_rate": 0.65,
                })
        
        # Match intervention to churn reason
        if "pricing" in primary_reason.lower():
            recommendations.append({
                "type": InterventionType.DISCOUNT.value,
                "priority": "high",
                "rationale": "Pricing sensitivity detected",
                "expected_success_rate": 0.60,
            })
        
        elif "features" in primary_reason.lower() or "functionality" in primary_reason.lower():
            recommendations.append({
                "type": InterventionType.UPGRADE.value,
                "priority": "high",
                "rationale": "Feature gap identified",
                "expected_success_rate": 0.75,
            })
        
        elif "support" in primary_reason.lower():
            recommendations.append({
                "type": InterventionType.SUPPORT.value,
                "priority": "high",
                "rationale": "Support experience issue",
                "expected_success_rate": 0.70,
            })
        
        # Lower risk accounts - focus on engagement
        if churn_prob <= 0.5:
            recommendations.append({
                "type": InterventionType.TRAINING.value,
                "priority": "medium",
                "rationale": "Feature adoption training",
                "expected_success_rate": 0.55,
            })
        
        return recommendations
