"""
Dynamic Pricing Service - Demand-based pricing optimization
Adjusts prices based on demand, market conditions, and revenue optimization
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json


class PricingOptimization(str, Enum):
    """Pricing optimization objectives"""
    REVENUE_MAXIMIZATION = "revenue"
    VOLUME_MAXIMIZATION = "volume"
    MARKET_PENETRATION = "penetration"
    MARGIN_PROTECTION = "margin"
    COMPETITIVE_ALIGNMENT = "competitive"


class DynamicPricingService:
    """
    Service for dynamic pricing based on demand, market conditions, and revenue optimization.
    Automatically adjusts prices to maximize revenue while maintaining competitiveness.
    """
    
    def __init__(self):
        """Initialize dynamic pricing service"""
        self.pricing_rules = {}
        self.demand_curves = {}
        self.price_history = {}
        self.optimization_history = {}
        self.rule_counter = 0
        
        # Market baseline prices
        self.baseline_prices = {}
        
        # Demand elasticity by agent
        self.elasticity_coefficients = {}
    
    def calculate_optimal_price(
        self,
        agent_id: str,
        base_price: float,
        current_demand: float,
        inventory: Optional[int] = None,
        optimization_goal: PricingOptimization = PricingOptimization.REVENUE_MAXIMIZATION,
    ) -> Dict:
        """
        Calculate optimal price based on demand and optimization goal.
        Uses elasticity and market factors to maximize objective.
        
        Args:
            agent_id: Agent ID
            base_price: Original/cost price
            current_demand: Current demand level (0-1 scale)
            inventory: Optional inventory level (for supply constraints)
            optimization_goal: What to optimize for
        
        Returns:
            Optimal price with justification
        """
        # Get or estimate elasticity
        elasticity = self.elasticity_coefficients.get(agent_id, -1.5)  # Default unit elastic
        
        # Detect demand level
        demand_level = self._categorize_demand(current_demand)
        
        # Calculate price multipliers
        if optimization_goal == PricingOptimization.REVENUE_MAXIMIZATION:
            # Revenue = Price * Quantity
            # Higher demand → higher prices
            # Lower demand → lower prices
            multiplier = self._calculate_revenue_multiplier(demand_level, elasticity)
        
        elif optimization_goal == PricingOptimization.VOLUME_MAXIMIZATION:
            # Maximize quantity sold
            multiplier = 0.85  # Always discount
        
        elif optimization_goal == PricingOptimization.MARKET_PENETRATION:
            # Aggressive price to gain market share
            multiplier = 0.75 if demand_level == "high" else 0.80
        
        elif optimization_goal == PricingOptimization.MARGIN_PROTECTION:
            # Maintain margins
            multiplier = 1.0 + (current_demand * 0.2)
        
        else:  # COMPETITIVE_ALIGNMENT
            # Match market
            multiplier = 1.0
        
        # Apply inventory constraint if provided
        if inventory is not None:
            if inventory < 10:
                multiplier *= 1.2  # Low inventory, increase price
            elif inventory > 100:
                multiplier *= 0.85  # High inventory, discount
        
        optimal_price = base_price * multiplier
        
        # Calculate expected metrics
        expected_quantity = self._estimate_quantity(
            current_demand, 
            optimal_price / base_price
        )
        expected_revenue = optimal_price * expected_quantity
        
        return {
            "agent_id": agent_id,
            "base_price": base_price,
            "optimal_price": round(optimal_price, 2),
            "price_multiplier": round(multiplier, 2),
            "price_change_percent": round((multiplier - 1) * 100, 1),
            "demand_level": demand_level,
            "current_demand": current_demand,
            "optimization_goal": optimization_goal.value,
            "elasticity": elasticity,
            "expected_quantity": round(expected_quantity, 1),
            "expected_revenue": round(expected_revenue, 2),
            "confidence": self._calculate_price_confidence(agent_id),
            "recommended_at": datetime.utcnow().isoformat(),
        }
    
    def _categorize_demand(self, demand: float) -> str:
        """Categorize demand level"""
        if demand >= 0.8:
            return "very_high"
        elif demand >= 0.6:
            return "high"
        elif demand >= 0.4:
            return "medium"
        elif demand >= 0.2:
            return "low"
        else:
            return "very_low"
    
    def _calculate_revenue_multiplier(
        self,
        demand_level: str,
        elasticity: float,
    ) -> float:
        """Calculate price multiplier for revenue maximization"""
        # Price elasticity rule: at optimal price, elasticity = -1
        # Above optimal: elastic (price decrease increases revenue)
        # Below optimal: inelastic (price increase increases revenue)
        
        multipliers = {
            "very_high": 1.35,  # High demand justifies premium pricing
            "high": 1.20,
            "medium": 1.00,  # Keep baseline
            "low": 0.90,      # Reduce to stimulate demand
            "very_low": 0.75, # Significant discount
        }
        
        return multipliers.get(demand_level, 1.0)
    
    def _estimate_quantity(
        self,
        demand: float,
        price_ratio: float,  # New price / old price
    ) -> float:
        """Estimate quantity change from demand and price"""
        # Base quantity on demand
        base_quantity = demand * 100  # Normalize to 0-100
        
        # Apply price elasticity (-1.5 typical)
        # 10% price increase → ~15% quantity decrease
        quantity_change = (price_ratio - 1.0) * -1.5
        
        new_quantity = base_quantity * (1 + quantity_change)
        return max(0, new_quantity)
    
    def _calculate_price_confidence(self, agent_id: str) -> float:
        """Calculate confidence in price recommendation"""
        history = self.price_history.get(agent_id, [])
        
        # More history = higher confidence
        confidence = min(0.95, 0.5 + (len(history) / 50))
        return round(confidence, 2)
    
    def detect_demand_changes(
        self,
        agent_id: str,
        recent_metrics: Dict,
    ) -> Dict:
        """
        Detect significant demand changes requiring price adjustment.
        Analyzes usage, conversions, and engagement trends.
        
        Args:
            agent_id: Agent ID
            recent_metrics: Recent performance metrics
        
        Returns:
            Demand analysis and change detection
        """
        # Extract metrics
        current_executions = recent_metrics.get("executions", 0)
        previous_executions = recent_metrics.get("previous_executions", 0)
        conversion_rate = recent_metrics.get("conversion_rate", 0)
        satisfaction = recent_metrics.get("satisfaction_score", 0)
        
        # Calculate execution growth
        execution_growth = (
            (current_executions - previous_executions) / max(previous_executions, 1)
        )
        
        # Detect demand shifts
        if execution_growth > 0.5:
            demand_signal = "increasing"
            demand_strength = "strong"
        elif execution_growth > 0.2:
            demand_signal = "increasing"
            demand_strength = "moderate"
        elif execution_growth > -0.2:
            demand_signal = "stable"
            demand_strength = "neutral"
        elif execution_growth > -0.5:
            demand_signal = "decreasing"
            demand_strength = "moderate"
        else:
            demand_signal = "decreasing"
            demand_strength = "strong"
        
        # Calculate demand score
        demand_score = (
            (current_executions / max(current_executions + previous_executions, 1)) +
            (conversion_rate / 100) +
            (satisfaction / 100)
        ) / 3
        
        # Recommend action
        recommendation = self._demand_action_recommendation(
            demand_signal, 
            demand_strength
        )
        
        return {
            "agent_id": agent_id,
            "demand_signal": demand_signal,
            "demand_strength": demand_strength,
            "demand_score": round(demand_score, 2),
            "execution_growth": round(execution_growth * 100, 1),
            "current_executions": current_executions,
            "conversion_rate": conversion_rate,
            "satisfaction_score": satisfaction,
            "recommendation": recommendation,
            "detected_at": datetime.utcnow().isoformat(),
        }
    
    def _demand_action_recommendation(
        self,
        signal: str,
        strength: str,
    ) -> str:
        """Get recommendation based on demand signal"""
        if signal == "increasing":
            if strength == "strong":
                return "Increase price to capture value and optimize revenue"
            else:
                return "Consider modest price increase"
        elif signal == "decreasing":
            if strength == "strong":
                return "Decrease price significantly to maintain volume"
            else:
                return "Monitor closely, may need to discount"
        else:
            return "No immediate pricing action needed"
    
    def apply_market_conditions(
        self,
        agent_id: str,
        base_price: float,
        market_data: Dict,
    ) -> Dict:
        """
        Apply market conditions to pricing (competition, seasonality, etc).
        Adjusts base price based on external market factors.
        
        Args:
            agent_id: Agent ID
            base_price: Base price to adjust
            market_data: Market conditions (competitors, season, region)
        
        Returns:
            Adjusted price with market justifications
        """
        multiplier = 1.0
        adjustments = []
        
        # Competitive positioning
        competitor_price = market_data.get("average_competitor_price", base_price)
        if competitor_price > 0:
            competition_multiplier = base_price / competitor_price
            multiplier *= competition_multiplier
            adjustments.append({
                "factor": "competition",
                "adjustment": round((competition_multiplier - 1) * 100, 1),
            })
        
        # Seasonality
        month = datetime.now().month
        seasonality_index = self._get_seasonality_index(month)
        multiplier *= seasonality_index
        adjustments.append({
            "factor": "seasonality",
            "adjustment": round((seasonality_index - 1) * 100, 1),
        })
        
        # Regional demand
        region = market_data.get("region", "us")
        region_multiplier = {
            "us": 1.0,
            "europe": 1.1,
            "apac": 0.9,
            "latam": 0.85,
        }.get(region, 1.0)
        multiplier *= region_multiplier
        adjustments.append({
            "factor": "region",
            "adjustment": round((region_multiplier - 1) * 100, 1),
        })
        
        adjusted_price = base_price * multiplier
        
        return {
            "agent_id": agent_id,
            "base_price": base_price,
            "adjusted_price": round(adjusted_price, 2),
            "total_multiplier": round(multiplier, 2),
            "adjustments": adjustments,
            "market_conditions": market_data,
            "applied_at": datetime.utcnow().isoformat(),
        }
    
    def _get_seasonality_index(self, month: int) -> float:
        """Get seasonality multiplier by month"""
        seasonality = {
            1: 0.9,   # January - slow
            2: 0.9,   # February - slow
            3: 1.0,   # March
            4: 1.05,  # April
            5: 1.15,  # May - spring peak
            6: 1.2,   # June - peak
            7: 1.15,  # July
            8: 1.1,   # August
            9: 1.05,  # September
            10: 1.0,  # October
            11: 0.95, # November
            12: 1.25, # December - holiday peak
        }
        return seasonality.get(month, 1.0)
    
    def optimize_revenue(
        self,
        agent_id: str,
        current_price: float,
        demand_estimate: float,
        cost: float,
    ) -> Dict:
        """
        Optimize pricing to maximize revenue given constraints.
        Finds revenue-maximizing price point.
        
        Args:
            agent_id: Agent ID
            current_price: Current price
            demand_estimate: Estimated demand at current price (0-1)
            cost: Cost to deliver service
        
        Returns:
            Revenue optimization analysis
        """
        # Test different prices around current
        test_prices = [
            current_price * 0.7,
            current_price * 0.85,
            current_price,
            current_price * 1.15,
            current_price * 1.3,
        ]
        
        best_revenue = 0
        best_price = current_price
        results = []
        
        for test_price in test_prices:
            price_ratio = test_price / current_price
            estimated_quantity = self._estimate_quantity(demand_estimate, price_ratio)
            revenue = test_price * estimated_quantity
            profit_margin = ((test_price - cost) / test_price) * 100
            
            results.append({
                "price": round(test_price, 2),
                "estimated_quantity": round(estimated_quantity, 1),
                "revenue": round(revenue, 2),
                "profit_margin": round(profit_margin, 1),
            })
            
            if revenue > best_revenue:
                best_revenue = revenue
                best_price = test_price
        
        # Sort by revenue descending
        results.sort(key=lambda x: x["revenue"], reverse=True)
        
        return {
            "agent_id": agent_id,
            "current_price": current_price,
            "recommended_price": round(best_price, 2),
            "expected_revenue": round(best_revenue, 2),
            "profit_margin": round(((best_price - cost) / best_price) * 100, 1),
            "price_options": results,
            "optimization_analysis": self._analyze_optimization(results),
        }
    
    def _analyze_optimization(self, results: List[Dict]) -> Dict:
        """Analyze optimization results"""
        top = results[0] if results else {}
        bottom = results[-1] if results else {}
        
        if not top or "revenue" not in top:
            return {}
        
        revenue_spread = top["revenue"] - bottom.get("revenue", 0)
        
        return {
            "revenue_sensitivity": "high" if revenue_spread > 100 else "moderate",
            "optimal_margin": top.get("profit_margin", 0),
            "price_elasticity_evident": revenue_spread > 50,
        }
    
    def track_pricing_performance(
        self,
        agent_id: str,
        price: float,
        quantity_sold: int,
        period_days: int = 30,
    ):
        """Track actual pricing performance vs estimates"""
        if agent_id not in self.price_history:
            self.price_history[agent_id] = []
        
        actual_revenue = price * quantity_sold
        
        record = {
            "price": price,
            "quantity": quantity_sold,
            "revenue": actual_revenue,
            "recorded_at": datetime.utcnow().isoformat(),
        }
        
        self.price_history[agent_id].append(record)
        
        # Keep last 12 months
        self.price_history[agent_id] = self.price_history[agent_id][-365:]
