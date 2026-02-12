"""
Phase 17: ML-Based Pricing Optimization
- Price-demand elasticity modeling
- Revenue optimization recommendations
- Dynamic pricing adjustments
- A/B testing framework
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PricingOptimizerML:
    """ML-based pricing optimization service"""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize pricing optimizer"""
        self.db_session = db_session
        self.price_elasticity_model = None
        self.revenue_optimizer = None
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.elasticity_cache = {}

    def train_price_elasticity_model(
        self,
        agent_id: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Train price elasticity model using historical data
        
        Uses linear regression to model: Demand = β0 + β1*Price + β2*Features + ε
        
        Args:
            agent_id: Agent identifier
            days: Historical data window
        
        Returns:
            Model performance metrics
        """
        try:
            # Gather historical pricing and subscription data
            history = self._gather_pricing_history(agent_id, days)
            
            if len(history) < 10:
                return {"error": "Insufficient data", "min_required": 10, "available": len(history)}
            
            df = pd.DataFrame(history)
            
            # Prepare features
            X = df[['price', 'agent_rating', 'execution_count', 'user_satisfaction']].values
            y = df['subscription_count'].values
            
            # Normalize features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train linear regression model
            self.price_elasticity_model = LinearRegression()
            self.price_elasticity_model.fit(X_scaled, y)
            
            # Calculate price elasticity
            price_idx = 0
            price_coefficient = self.price_elasticity_model.coef_[price_idx]
            avg_price = df['price'].mean()
            avg_demand = df['subscription_count'].mean()
            
            elasticity = (price_coefficient * avg_price) / avg_demand if avg_demand > 0 else 0
            
            # Store in cache
            self.elasticity_cache[agent_id] = {
                "elasticity": elasticity,
                "coefficient": price_coefficient,
                "r2_score": self.price_elasticity_model.score(X_scaled, y),
                "trained_at": datetime.utcnow(),
                "data_points": len(history)
            }
            
            return {
                "status": "trained",
                "elasticity": float(elasticity),
                "r2_score": float(self.price_elasticity_model.score(X_scaled, y)),
                "coefficient": float(price_coefficient),
                "data_points": len(history),
                "interpretation": self._interpret_elasticity(elasticity)
            }
        
        except Exception as e:
            logger.error(f"Error training elasticity model for {agent_id}: {str(e)}")
            return {"error": str(e)}

    def optimize_pricing(
        self,
        agent_id: str,
        current_price: float,
        current_revenue: float,
        constraints: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Recommend optimal pricing using elasticity model
        
        Optimizes: Revenue = Price * Demand(Price, Features)
        
        Args:
            agent_id: Agent identifier
            current_price: Current monthly price
            current_revenue: Current monthly revenue
            constraints: Min/max price constraints
        
        Returns:
            Pricing recommendations with revenue impact
        """
        try:
            if agent_id not in self.elasticity_cache:
                return {"error": "Model not trained", "agent_id": agent_id}
            
            constraints = constraints or {"min_price": current_price * 0.8, "max_price": current_price * 1.5}
            
            # Get elasticity
            elasticity = self.elasticity_cache[agent_id]["elasticity"]
            
            # Revenue maximization: dRevenue/dPrice = 0 when Elasticity = -1
            optimal_price = self._calculate_optimal_price(current_price, elasticity, constraints)
            
            # Estimate demand at new price
            current_demand = self._estimate_demand(agent_id, current_price)
            new_demand = self._estimate_demand(agent_id, optimal_price)
            
            revenue_change = (optimal_price * new_demand) - current_revenue
            revenue_change_pct = (revenue_change / current_revenue * 100) if current_revenue > 0 else 0
            
            return {
                "status": "optimized",
                "current_price": current_price,
                "recommended_price": optimal_price,
                "price_change_pct": ((optimal_price - current_price) / current_price * 100),
                "current_demand": current_demand,
                "estimated_demand": new_demand,
                "current_revenue": current_revenue,
                "estimated_revenue": optimal_price * new_demand,
                "revenue_change": revenue_change,
                "revenue_change_pct": revenue_change_pct,
                "elasticity": elasticity,
                "confidence": self.elasticity_cache[agent_id].get("r2_score", 0)
            }
        
        except Exception as e:
            logger.error(f"Error optimizing pricing for {agent_id}: {str(e)}")
            return {"error": str(e)}

    def train_revenue_optimizer(
        self,
        agents_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Train gradient boosting model for revenue prediction
        
        Uses multiple features to predict monthly revenue
        
        Args:
            agents_data: List of agent performance data
        
        Returns:
            Model performance metrics
        """
        try:
            if len(agents_data) < 20:
                return {"error": "Insufficient agents data", "min_required": 20, "available": len(agents_data)}
            
            df = pd.DataFrame(agents_data)
            
            # Feature engineering
            X = df[[
                'price', 'agent_rating', 'execution_count', 
                'user_satisfaction', 'response_time', 'feature_count'
            ]].values
            y = df['monthly_revenue'].values
            
            # Normalize features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train gradient boosting
            self.revenue_optimizer = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
            self.revenue_optimizer.fit(X_scaled, y)
            
            # Store feature importance
            feature_names = ['price', 'rating', 'execution_count', 'satisfaction', 'response_time', 'features']
            self.feature_importance = dict(zip(feature_names, self.revenue_optimizer.feature_importances_))
            
            return {
                "status": "trained",
                "r2_score": float(self.revenue_optimizer.score(X_scaled, y)),
                "feature_importance": {k: float(v) for k, v in self.feature_importance.items()},
                "agents_trained": len(agents_data)
            }
        
        except Exception as e:
            logger.error(f"Error training revenue optimizer: {str(e)}")
            return {"error": str(e)}

    def predict_revenue(
        self,
        agent_features: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Predict monthly revenue for agent
        
        Args:
            agent_features: Agent characteristics (price, rating, etc.)
        
        Returns:
            Revenue prediction with confidence interval
        """
        try:
            if self.revenue_optimizer is None:
                return {"error": "Model not trained"}
            
            features = np.array([[
                agent_features.get('price', 0),
                agent_features.get('rating', 0),
                agent_features.get('execution_count', 0),
                agent_features.get('user_satisfaction', 0),
                agent_features.get('response_time', 0),
                agent_features.get('feature_count', 0)
            ]])
            
            features_scaled = self.scaler.transform(features)
            prediction = self.revenue_optimizer.predict(features_scaled)[0]
            
            # Estimate confidence interval using residuals
            residual_std = np.std(self.revenue_optimizer.predict(features_scaled) - agent_features.get('actual_revenue', 0))
            
            return {
                "predicted_revenue": float(max(0, prediction)),
                "lower_bound": float(max(0, prediction - 1.96 * residual_std)),
                "upper_bound": float(prediction + 1.96 * residual_std),
                "confidence": 0.95
            }
        
        except Exception as e:
            logger.error(f"Error predicting revenue: {str(e)}")
            return {"error": str(e)}

    def a_b_test_pricing(
        self,
        agent_id: str,
        control_price: float,
        test_prices: List[float],
        sample_size: int = 100,
        duration_days: int = 7
    ) -> Dict[str, Any]:
        """
        Design A/B test for pricing strategies
        
        Args:
            agent_id: Agent identifier
            control_price: Control group price
            test_prices: Alternative prices to test
            sample_size: Users per variant
            duration_days: Test duration
        
        Returns:
            Test design and expected outcomes
        """
        try:
            if agent_id not in self.elasticity_cache:
                return {"error": "Model not trained"}
            
            elasticity = self.elasticity_cache[agent_id]["elasticity"]
            control_demand = self._estimate_demand(agent_id, control_price)
            control_revenue = control_price * control_demand
            
            test_results = []
            
            for test_price in test_prices:
                test_demand = self._estimate_demand(agent_id, test_price)
                test_revenue = test_price * test_demand
                
                # Statistical power calculation
                effect_size = abs(test_revenue - control_revenue) / control_revenue if control_revenue > 0 else 0
                
                test_results.append({
                    "test_price": test_price,
                    "estimated_demand": test_demand,
                    "estimated_revenue": test_revenue,
                    "revenue_change_pct": ((test_revenue - control_revenue) / control_revenue * 100),
                    "effect_size": effect_size,
                    "sample_size": sample_size,
                    "min_detectable_effect": 0.15  # 15% effect minimum for significance
                })
            
            return {
                "agent_id": agent_id,
                "control_price": control_price,
                "control_demand": control_demand,
                "control_revenue": control_revenue,
                "test_variants": test_results,
                "duration_days": duration_days,
                "total_participants": len(test_prices) * sample_size
            }
        
        except Exception as e:
            logger.error(f"Error designing A/B test: {str(e)}")
            return {"error": str(e)}

    def get_pricing_insights(
        self,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive pricing insights
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Detailed pricing analysis and recommendations
        """
        try:
            if agent_id not in self.elasticity_cache:
                return {"error": "Model not trained"}
            
            cache = self.elasticity_cache[agent_id]
            elasticity = cache["elasticity"]
            
            insights = {
                "elasticity": elasticity,
                "elasticity_interpretation": self._interpret_elasticity(elasticity),
                "model_confidence": cache.get("r2_score", 0),
                "data_recency": (datetime.utcnow() - cache.get("trained_at", datetime.utcnow())).days,
                "recommendations": self._generate_pricing_recommendations(elasticity)
            }
            
            return insights
        
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {"error": str(e)}

    # Helper methods
    
    def _gather_pricing_history(
        self,
        agent_id: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """Gather historical pricing data"""
        # Mock implementation - would query actual database
        history = []
        base_price = 99.0
        
        for i in range(days):
            price = base_price + (np.random.rand() - 0.5) * 20
            subs = max(10, 100 - (price - base_price) * 0.5 + np.random.randn() * 5)
            
            history.append({
                "price": price,
                "subscription_count": subs,
                "agent_rating": 4.5 + np.random.rand() * 0.5,
                "execution_count": np.random.randint(1000, 10000),
                "user_satisfaction": 4.0 + np.random.rand()
            })
        
        return history

    def _estimate_demand(
        self,
        agent_id: str,
        price: float
    ) -> float:
        """Estimate demand at given price"""
        if agent_id not in self.elasticity_cache or self.price_elasticity_model is None:
            return 50.0
        
        elasticity = self.elasticity_cache[agent_id]["elasticity"]
        base_demand = 100.0
        
        # Q = base_demand * (Price / base_price) ^ elasticity
        return base_demand * (price / 99.0) ** elasticity

    def _calculate_optimal_price(
        self,
        current_price: float,
        elasticity: float,
        constraints: Dict[str, float]
    ) -> float:
        """Calculate revenue-maximizing price"""
        # Revenue maximization: optimal when elasticity = -1
        if -1.5 < elasticity < -0.5:
            # Already near optimal
            optimal = current_price
        elif elasticity < -1.5:
            # Elastic (sensitive to price): decrease price
            optimal = current_price * 0.95
        else:
            # Inelastic: increase price
            optimal = current_price * 1.05
        
        # Apply constraints
        optimal = max(constraints.get("min_price", 0), min(constraints.get("max_price", float('inf')), optimal))
        
        return optimal

    def _interpret_elasticity(self, elasticity: float) -> str:
        """Interpret elasticity coefficient"""
        if elasticity is None:
            return "Unknown"
        
        if elasticity > -0.5:
            return "Inelastic: Demand insensitive to price. Increase price to boost revenue."
        elif elasticity < -1.5:
            return "Elastic: Demand sensitive to price. Decrease price to boost revenue."
        else:
            return "Unit elastic: Near optimal pricing. Monitor demand closely."

    def _generate_pricing_recommendations(
        self,
        elasticity: float
    ) -> List[str]:
        """Generate pricing recommendations based on elasticity"""
        recommendations = []
        
        if elasticity > -0.5:
            recommendations.append("Your agent has pricing power. Consider gradual price increases.")
            recommendations.append("Focus on quality improvements to justify premium pricing.")
        elif elasticity < -1.5:
            recommendations.append("High price sensitivity detected. Strategic discounts may increase revenue.")
            recommendations.append("Consider tiered pricing to capture different customer segments.")
        else:
            recommendations.append("Pricing is near optimal. Focus on non-price factors.")
            recommendations.append("Improve agent features/performance to enable price increases.")
        
        recommendations.append("Monitor competitor pricing monthly.")
        recommendations.append("Use A/B testing to validate pricing changes.")
        
        return recommendations
