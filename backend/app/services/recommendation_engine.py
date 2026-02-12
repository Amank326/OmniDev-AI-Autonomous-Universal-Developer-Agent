"""
Phase 17: Personalized Recommendation Engine
- Collaborative filtering for agent recommendations
- Content-based filtering for tier upgrades
- Personalized tier recommendations
- Agent discovery optimization
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Optional, Tuple, Any
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Personalized recommendation service"""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize recommendation engine"""
        self.db_session = db_session
        self.user_agent_matrix = None
        self.user_similarity_matrix = None
        self.agent_features_matrix = None
        self.agent_similarity_matrix = None
        self.user_profiles = {}
        self.agent_profiles = {}

    def build_user_agent_matrix(
        self,
        users_data: List[Dict[str, Any]],
        agents_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build user-agent interaction matrix for collaborative filtering
        
        Args:
            users_data: User subscription history
            agents_data: Agent metadata
        
        Returns:
            Matrix statistics
        """
        try:
            # Create interaction matrix: users × agents
            # Values: engagement score (0-100)
            
            user_ids = [u["user_id"] for u in users_data]
            agent_ids = [a["agent_id"] for a in agents_data]
            
            # Initialize matrix with zeros
            matrix = np.zeros((len(user_ids), len(agent_ids)))
            
            # Fill matrix with engagement scores
            for user_data in users_data:
                user_idx = user_ids.index(user_data["user_id"])
                
                for interaction in user_data.get("interactions", []):
                    agent_id = interaction.get("agent_id")
                    if agent_id in agent_ids:
                        agent_idx = agent_ids.index(agent_id)
                        
                        # Engagement score = usage * rating * satisfaction
                        engagement_score = (
                            interaction.get("usage_count", 0) * 0.5 +
                            interaction.get("rating", 5) * 10 +
                            interaction.get("satisfaction", 5) * 10
                        )
                        matrix[user_idx, agent_idx] = min(100, engagement_score)
            
            self.user_agent_matrix = matrix
            
            # Calculate user-user similarity
            self.user_similarity_matrix = cosine_similarity(matrix)
            
            # Calculate agent-agent similarity
            self.agent_similarity_matrix = cosine_similarity(matrix.T)
            
            return {
                "status": "built",
                "users": len(user_ids),
                "agents": len(agent_ids),
                "matrix_shape": matrix.shape,
                "sparsity": float(np.sum(matrix == 0) / matrix.size),
                "avg_engagement": float(np.mean(matrix[matrix > 0])) if np.any(matrix > 0) else 0
            }
        
        except Exception as e:
            logger.error(f"Error building user-agent matrix: {str(e)}")
            return {"error": str(e)}

    def collaborative_filtering_recommendations(
        self,
        user_id: str,
        user_ids_map: Dict[str, int],
        agent_ids_map: Dict[int, str],
        n_recommendations: int = 5
    ) -> Dict[str, Any]:
        """
        Generate recommendations using collaborative filtering
        
        Find similar users and recommend agents they liked
        
        Args:
            user_id: Target user
            user_ids_map: Mapping of user_id to matrix index
            agent_ids_map: Mapping of matrix index to agent_id
            n_recommendations: Number of recommendations
        
        Returns:
            Recommended agents with scores
        """
        try:
            if self.user_similarity_matrix is None:
                return {"error": "Matrix not built"}
            
            if user_id not in user_ids_map:
                return {"error": f"User {user_id} not found"}
            
            user_idx = user_ids_map[user_id]
            
            # Get similar users (excluding self)
            similarities = self.user_similarity_matrix[user_idx].copy()
            similarities[user_idx] = -1  # Exclude self
            
            similar_user_indices = np.argsort(similarities)[::-1][:10]  # Top 10 similar users
            
            # Get agents liked by similar users
            user_ratings = self.user_agent_matrix[user_idx]
            recommended_scores = np.zeros(self.user_agent_matrix.shape[1])
            
            for similar_idx in similar_user_indices:
                if similarities[similar_idx] > 0:
                    # Weight by similarity
                    weight = similarities[similar_idx]
                    recommended_scores += self.user_agent_matrix[similar_idx] * weight
            
            # Subtract agents already used by this user
            recommended_scores[user_ratings > 0] = -1
            
            # Get top recommendations
            top_indices = np.argsort(recommended_scores)[::-1][:n_recommendations]
            
            recommendations = []
            for rank, idx in enumerate(top_indices, 1):
                if recommended_scores[idx] > 0:
                    recommendations.append({
                        "rank": rank,
                        "agent_id": agent_ids_map.get(idx, f"agent_{idx}"),
                        "score": float(recommended_scores[idx]),
                        "reason": "Users like you found this helpful",
                        "expected_engagement": float(recommended_scores[idx] / 100)
                    })
            
            return {
                "user_id": user_id,
                "method": "collaborative_filtering",
                "recommendations": recommendations,
                "similar_users_count": len([s for s in similarities if s > 0])
            }
        
        except Exception as e:
            logger.error(f"Error in collaborative filtering: {str(e)}")
            return {"error": str(e)}

    def content_based_recommendations(
        self,
        user_profile: Dict[str, Any],
        available_agents: List[Dict[str, Any]],
        n_recommendations: int = 5
    ) -> Dict[str, Any]:
        """
        Generate recommendations using content-based filtering
        
        Recommend agents similar to user's preferences
        
        Args:
            user_profile: User's preferences and history
            available_agents: Agents to recommend from
            n_recommendations: Number of recommendations
        
        Returns:
            Recommended agents based on content similarity
        """
        try:
            user_preferences = {
                "category": user_profile.get("preferred_category"),
                "price_range": user_profile.get("price_range"),
                "features": user_profile.get("preferred_features", []),
                "rating_threshold": user_profile.get("rating_threshold", 3.5)
            }
            
            scored_agents = []
            
            for agent in available_agents:
                score = 0
                reasons = []
                
                # Category match (30%)
                if agent.get("category") == user_preferences["category"]:
                    score += 30
                    reasons.append("Matches your preferred category")
                
                # Price range match (25%)
                price = agent.get("monthly_price", 0)
                price_range = user_preferences.get("price_range", {"min": 0, "max": 1000})
                if price_range["min"] <= price <= price_range["max"]:
                    score += 25
                    reasons.append("Within your price range")
                
                # Rating match (20%)
                rating = agent.get("rating", 0)
                if rating >= user_preferences["rating_threshold"]:
                    score += 20 * (rating / 5)  # Up to 20 points
                    reasons.append(f"Highly rated ({rating:.1f}★)")
                
                # Feature overlap (25%)
                agent_features = set(agent.get("features", []))
                preferred_features = set(user_preferences.get("features", []))
                if preferred_features:
                    overlap = len(agent_features & preferred_features)
                    feature_score = (overlap / len(preferred_features)) * 25
                    score += feature_score
                    reasons.append(f"Has {overlap}/{len(preferred_features)} features you want")
                
                scored_agents.append({
                    "agent_id": agent.get("agent_id"),
                    "agent_name": agent.get("name"),
                    "score": score,
                    "rating": rating,
                    "price": price,
                    "reasons": reasons
                })
            
            # Sort by score and get top N
            scored_agents.sort(key=lambda x: x["score"], reverse=True)
            
            return {
                "user_id": user_profile.get("user_id"),
                "method": "content_based",
                "recommendations": scored_agents[:n_recommendations],
                "total_evaluated": len(available_agents)
            }
        
        except Exception as e:
            logger.error(f"Error in content-based filtering: {str(e)}")
            return {"error": str(e)}

    def recommend_tier_upgrade(
        self,
        user_id: str,
        current_usage: Dict[str, int],
        current_tier: Dict[str, Any],
        available_tiers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Recommend tier upgrades based on usage patterns
        
        Args:
            user_id: User identifier
            current_usage: Current month's usage metrics
            current_tier: Current subscription tier
            available_tiers: Available upgrade options
        
        Returns:
            Tier upgrade recommendations
        """
        try:
            current_tier_id = current_tier.get("tier_id")
            monthly_price = current_tier.get("monthly_price", 0)
            executions_limit = current_tier.get("monthly_executions", 1000)
            tokens_limit = current_tier.get("monthly_tokens", 100000)
            
            usage_pct_exec = (current_usage.get("executions", 0) / executions_limit * 100) if executions_limit > 0 else 0
            usage_pct_tokens = (current_usage.get("tokens", 0) / tokens_limit * 100) if tokens_limit > 0 else 0
            
            recommendations = []
            
            # Check if usage is near limits
            if usage_pct_exec > 80 or usage_pct_tokens > 80:
                # Find next tier up
                current_tier_idx = None
                for idx, tier in enumerate(available_tiers):
                    if tier.get("tier_id") == current_tier_id:
                        current_tier_idx = idx
                        break
                
                if current_tier_idx is not None and current_tier_idx < len(available_tiers) - 1:
                    upgrade_tier = available_tiers[current_tier_idx + 1]
                    
                    price_increase = upgrade_tier.get("monthly_price", 0) - monthly_price
                    exec_increase = upgrade_tier.get("monthly_executions", executions_limit) - executions_limit
                    token_increase = upgrade_tier.get("monthly_tokens", tokens_limit) - tokens_limit
                    
                    roi = 0
                    if price_increase > 0:
                        # Value gained per dollar
                        value = (exec_increase / 100) + (token_increase / 10000)
                        roi = value / (price_increase / 10)
                    
                    recommendations.append({
                        "tier_id": upgrade_tier.get("tier_id"),
                        "tier_name": upgrade_tier.get("name"),
                        "monthly_price": upgrade_tier.get("monthly_price"),
                        "price_increase": price_increase,
                        "executions_increase": exec_increase,
                        "tokens_increase": token_increase,
                        "priority": "high" if usage_pct_exec > 90 else "medium",
                        "reason": f"You are at {max(usage_pct_exec, usage_pct_tokens):.0f}% of your {current_tier.get('name')} limits",
                        "roi": roi
                    })
            
            # Check for unused features (potential downgrade)
            elif max(usage_pct_exec, usage_pct_tokens) < 20:
                current_tier_idx = None
                for idx, tier in enumerate(available_tiers):
                    if tier.get("tier_id") == current_tier_id:
                        current_tier_idx = idx
                        break
                
                if current_tier_idx is not None and current_tier_idx > 0:
                    downgrade_tier = available_tiers[current_tier_idx - 1]
                    
                    potential_savings = monthly_price - downgrade_tier.get("monthly_price", 0)
                    
                    recommendations.append({
                        "tier_id": downgrade_tier.get("tier_id"),
                        "tier_name": downgrade_tier.get("name"),
                        "monthly_price": downgrade_tier.get("monthly_price"),
                        "price_change": -potential_savings,
                        "priority": "low",
                        "reason": "You're using less than 20% of your tier limits",
                        "potential_savings": potential_savings,
                        "type": "downgrade"
                    })
            
            return {
                "user_id": user_id,
                "current_tier": current_tier.get("name"),
                "usage_percentage": float(max(usage_pct_exec, usage_pct_tokens)),
                "recommendations": recommendations
            }
        
        except Exception as e:
            logger.error(f"Error recommending tier upgrade: {str(e)}")
            return {"error": str(e)}

    def personalized_agent_discovery(
        self,
        user_id: str,
        user_profile: Dict[str, Any],
        available_agents: List[Dict[str, Any]],
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Generate personalized agent discovery recommendations
        
        Combines multiple recommendation strategies
        
        Args:
            user_id: User identifier
            user_profile: User profile and preferences
            available_agents: Agents to recommend from
            limit: Number of recommendations
        
        Returns:
            Personalized agent discovery list
        """
        try:
            # Get content-based recommendations
            content_recs = self.content_based_recommendations(
                user_profile,
                available_agents,
                n_recommendations=limit
            )
            
            if "error" in content_recs:
                # Fallback to simple ranking
                return self._fallback_agent_discovery(available_agents, limit)
            
            # Enhance with metadata
            enriched_recommendations = []
            for rec in content_recs.get("recommendations", []):
                agent = next((a for a in available_agents if a.get("agent_id") == rec["agent_id"]), {})
                
                enriched_recommendations.append({
                    "rank": len(enriched_recommendations) + 1,
                    "agent_id": rec["agent_id"],
                    "agent_name": rec.get("agent_name"),
                    "category": agent.get("category"),
                    "rating": rec["rating"],
                    "monthly_price": rec["price"],
                    "relevance_score": rec["score"],
                    "reasons": rec["reasons"],
                    "free_trial": agent.get("free_trial", False),
                    "trial_days": agent.get("trial_days", 14),
                    "user_count": agent.get("user_count", 0),
                    "primary_reason": rec["reasons"][0] if rec["reasons"] else "Recommended for you"
                })
            
            return {
                "user_id": user_id,
                "method": "personalized_discovery",
                "recommendations": enriched_recommendations,
                "total_evaluated": len(available_agents)
            }
        
        except Exception as e:
            logger.error(f"Error in personalized discovery: {str(e)}")
            return {"error": str(e)}

    def get_recommendation_insights(self) -> Dict[str, Any]:
        """Get recommendation system performance insights"""
        try:
            return {
                "system_status": "operational",
                "matrices_built": self.user_agent_matrix is not None,
                "recommendation_methods": [
                    "collaborative_filtering",
                    "content_based",
                    "upgrade_recommendations",
                    "personalized_discovery"
                ],
                "last_update": datetime.utcnow().isoformat() if hasattr(self, 'last_update') else None
            }
        except Exception as e:
            return {"error": str(e)}

    # Helper methods
    
    def _fallback_agent_discovery(
        self,
        agents: List[Dict[str, Any]],
        limit: int
    ) -> Dict[str, Any]:
        """Fallback agent discovery using simple popularity/rating"""
        scored = []
        
        for agent in agents:
            score = agent.get("rating", 0) * 30 + agent.get("user_count", 0) / 10
            scored.append((agent, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for rank, (agent, score) in enumerate(scored[:limit], 1):
            recommendations.append({
                "rank": rank,
                "agent_id": agent.get("agent_id"),
                "agent_name": agent.get("name"),
                "rating": agent.get("rating"),
                "reasons": ["Popular choice", f"{agent.get('user_count', 0)} users trust this agent"]
            })
        
        return {
            "method": "popularity_ranking",
            "recommendations": recommendations
        }


from datetime import datetime
