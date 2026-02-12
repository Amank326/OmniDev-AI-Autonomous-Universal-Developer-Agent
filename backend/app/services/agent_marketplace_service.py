"""
Phase 15: Agent Marketplace Service
- Agent discovery and search
- Agent deployment management
- Version control and updates
- Deployment orchestration
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import json


class AgentMarketplaceService:
    """Manage agent discovery, deployment, and marketplace operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============ DISCOVERY & SEARCH ============
    
    def search_agents(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_rating: float = 0.0,
        is_paid_only: bool = False,
        sort_by: str = "rating",  # rating, downloads, trending, newest
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Full-text search agents with filters"""
        from app.models.agent_models import AIAgent
        
        q = self.db.query(AIAgent).filter(
            AIAgent.is_public == True,
            AIAgent.is_archived == False
        )
        
        # Text search
        if query:
            search_term = f"%{query}%"
            q = q.filter(
                (AIAgent.name.ilike(search_term)) |
                (AIAgent.description.ilike(search_term)) |
                (AIAgent.tags.astext.ilike(search_term))
            )
        
        # Category filter
        if category:
            q = q.filter(AIAgent.category == category)
        
        # Tags filter
        if tags:
            for tag in tags:
                q = q.filter(AIAgent.tags.astext.contains(tag))
        
        # Rating filter
        if min_rating > 0:
            q = q.filter(AIAgent.average_rating >= min_rating)
        
        # Paid filter
        if is_paid_only:
            q = q.filter(AIAgent.is_paid == True)
        
        # Sorting
        sort_map = {
            "rating": desc(AIAgent.average_rating),
            "downloads": desc(AIAgent.downloads),
            "trending": desc(AIAgent.deployments),
            "newest": desc(AIAgent.created_at)
        }
        q = q.order_by(sort_map.get(sort_by, desc(AIAgent.average_rating)))
        
        total_count = q.count()
        agents = q.limit(limit).offset(offset).all()
        
        return {
            "agents": agents,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
    
    def get_featured_agents(self, limit: int = 10) -> List[Any]:
        """Get featured agents for homepage"""
        from app.models.agent_models import AIAgent
        
        return self.db.query(AIAgent).filter(
            AIAgent.is_featured == True,
            AIAgent.is_public == True,
            AIAgent.is_archived == False
        ).order_by(desc(AIAgent.average_rating)).limit(limit).all()
    
    def get_trending_agents(self, days: int = 30, limit: int = 10) -> List[Any]:
        """Get trending agents based on recent activity"""
        from app.models.agent_models import AIAgent
        from app.models.agent_models import AgentExecution
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        trending = self.db.query(
            AIAgent,
            func.count(AgentExecution.id).label('recent_executions')
        ).join(
            AgentExecution, AIAgent.id == AgentExecution.agent_id
        ).filter(
            AIAgent.is_public == True,
            AIAgent.is_archived == False,
            AgentExecution.created_at >= cutoff_date
        ).group_by(
            AIAgent.id
        ).order_by(
            desc('recent_executions')
        ).limit(limit).all()
        
        return [agent for agent, _ in trending]
    
    def get_agent_by_id(self, agent_id: str) -> Optional[Any]:
        """Get agent details"""
        from app.models.agent_models import AIAgent
        
        return self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    
    def get_agent_by_slug(self, slug: str) -> Optional[Any]:
        """Get agent by slug"""
        from app.models.agent_models import AIAgent
        
        return self.db.query(AIAgent).filter(AIAgent.slug == slug).first()
    
    # ============ CATEGORIES & TAGS ============
    
    def get_categories(self) -> List[str]:
        """Get all agent categories"""
        from app.models.agent_models import AIAgent
        
        categories = self.db.query(
            AIAgent.category
        ).filter(
            AIAgent.is_public == True
        ).distinct().all()
        
        return [cat[0] for cat in categories if cat[0]]
    
    def get_popular_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most popular tags with usage counts"""
        from app.models.agent_models import AIAgent
        
        # This is a simplified version - in production, parse JSON tags
        # For now, return category-based aggregation
        categories = self.db.query(
            AIAgent.category,
            func.count(AIAgent.id).label('count')
        ).filter(
            AIAgent.is_public == True
        ).group_by(
            AIAgent.category
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return [{"tag": cat, "count": count} for cat, count in categories]
    
    # ============ DEPLOYMENT MANAGEMENT ============
    
    def create_deployment(
        self,
        agent_id: str,
        user_id: str,
        name: str,
        environment: str,
        custom_system_prompt: Optional[str] = None,
        custom_parameters: Optional[Dict] = None,
        api_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a deployment of an agent"""
        from app.models.agent_models import AIAgent, AgentDeployment
        import uuid
        
        # Verify agent exists
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        deployment_id = str(uuid.uuid4())
        
        deployment = AgentDeployment(
            id=deployment_id,
            agent_id=agent_id,
            user_id=user_id,
            name=name,
            version=agent.latest_version,
            environment=environment,
            custom_system_prompt=custom_system_prompt,
            custom_parameters=custom_parameters or {},
            api_keys_configured=api_keys or [],
            created_at=datetime.utcnow()
        )
        
        self.db.add(deployment)
        self.db.commit()
        
        return {
            "deployment_id": deployment_id,
            "agent_id": agent_id,
            "name": name,
            "environment": environment,
            "status": "active",
            "created_at": deployment.created_at.isoformat()
        }
    
    def get_user_deployments(self, user_id: str) -> List[Any]:
        """Get all deployments for a user"""
        from app.models.agent_models import AgentDeployment
        
        return self.db.query(AgentDeployment).filter(
            AgentDeployment.user_id == user_id,
            AgentDeployment.is_active == True
        ).order_by(desc(AgentDeployment.created_at)).all()
    
    def update_deployment_config(
        self,
        deployment_id: str,
        custom_system_prompt: Optional[str] = None,
        custom_parameters: Optional[Dict] = None
    ) -> bool:
        """Update deployment configuration"""
        from app.models.agent_models import AgentDeployment
        
        deployment = self.db.query(AgentDeployment).filter(
            AgentDeployment.id == deployment_id
        ).first()
        
        if not deployment:
            return False
        
        if custom_system_prompt is not None:
            deployment.custom_system_prompt = custom_system_prompt
        
        if custom_parameters is not None:
            deployment.custom_parameters = custom_parameters
        
        deployment.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def deactivate_deployment(self, deployment_id: str) -> bool:
        """Deactivate a deployment"""
        from app.models.agent_models import AgentDeployment
        
        deployment = self.db.query(AgentDeployment).filter(
            AgentDeployment.id == deployment_id
        ).first()
        
        if not deployment:
            return False
        
        deployment.is_active = False
        deployment.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    # ============ RATINGS & REVIEWS ============
    
    def rate_agent(
        self,
        agent_id: str,
        user_id: str,
        rating: int,
        review_title: Optional[str] = None,
        review_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit rating for an agent"""
        from app.models.agent_models import AIAgent, AgentRating
        import uuid
        
        # Check if user already rated
        existing = self.db.query(AgentRating).filter(
            AgentRating.agent_id == agent_id,
            AgentRating.user_id == user_id
        ).first()
        
        if existing:
            # Update rating
            existing.rating = rating
            existing.review_title = review_title
            existing.review_text = review_text
            rating_id = existing.id
        else:
            # Create new rating
            rating_id = str(uuid.uuid4())
            agent_rating = AgentRating(
                id=rating_id,
                agent_id=agent_id,
                user_id=user_id,
                rating=rating,
                review_title=review_title,
                review_text=review_text,
                created_at=datetime.utcnow()
            )
            self.db.add(agent_rating)
        
        # Update agent average rating
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if agent:
            ratings = self.db.query(AgentRating).filter(
                AgentRating.agent_id == agent_id
            ).all()
            
            if ratings:
                agent.average_rating = sum(r.rating for r in ratings) / len(ratings)
                agent.rating_count = len(ratings)
        
        self.db.commit()
        
        return {
            "rating_id": rating_id,
            "agent_id": agent_id,
            "rating": rating,
            "average_rating": agent.average_rating if agent else rating
        }
    
    def get_agent_reviews(self, agent_id: str, limit: int = 20) -> List[Any]:
        """Get reviews for an agent"""
        from app.models.agent_models import AgentRating
        
        return self.db.query(AgentRating).filter(
            AgentRating.agent_id == agent_id
        ).order_by(desc(AgentRating.helpful_count)).limit(limit).all()
    
    # ============ AGENT STATS & ANALYTICS ============
    
    def record_deployment(self, agent_id: str) -> None:
        """Record when an agent is deployed"""
        from app.models.agent_models import AIAgent
        
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if agent:
            agent.deployments += 1
            self.db.commit()
    
    def record_download(self, agent_id: str) -> None:
        """Record agent download/clone"""
        from app.models.agent_models import AIAgent
        
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if agent:
            agent.downloads += 1
            self.db.commit()
    
    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive agent statistics"""
        from app.models.agent_models import AIAgent, AgentExecution, AgentPerformance
        
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not agent:
            return {}
        
        # Recent executions
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_executions = self.db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id,
            AgentExecution.created_at >= seven_days_ago,
            AgentExecution.status == "completed"
        ).count()
        
        # Total executions today
        today = datetime.utcnow().date()
        executions_today = self.db.query(AgentExecution).filter(
            AgentExecution.agent_id == agent_id,
            func.date(AgentExecution.created_at) == today
        ).count()
        
        return {
            "agent_id": agent_id,
            "downloads": agent.downloads,
            "deployments": agent.deployments,
            "total_executions": agent.executions,
            "recent_executions_7days": recent_executions,
            "executions_today": executions_today,
            "average_rating": agent.average_rating,
            "rating_count": agent.rating_count,
            "success_rate": agent.success_rate,
            "average_execution_time": agent.average_execution_time
        }
    
    # ============ VERSIONING ============
    
    def publish_new_version(
        self,
        agent_id: str,
        version: str,
        changelog: str
    ) -> Dict[str, Any]:
        """Publish a new version of an agent"""
        from app.models.agent_models import AIAgent
        
        agent = self.db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent.latest_version = version
        agent.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "agent_id": agent_id,
            "version": version,
            "published_at": agent.updated_at.isoformat()
        }
    
    # ============ CLONING & FORKING ============
    
    def clone_agent(
        self,
        source_agent_id: str,
        user_id: str,
        new_name: str
    ) -> Dict[str, Any]:
        """Clone an agent as a new version"""
        from app.models.agent_models import AIAgent
        import uuid
        
        source = self.db.query(AIAgent).filter(AIAgent.id == source_agent_id).first()
        if not source:
            raise ValueError(f"Source agent {source_agent_id} not found")
        
        new_agent_id = str(uuid.uuid4())
        
        cloned_agent = AIAgent(
            id=new_agent_id,
            author_id=user_id,
            name=new_name,
            slug=new_name.lower().replace(" ", "-"),
            description=source.description,
            full_description=source.full_description,
            icon_url=source.icon_url,
            agent_type=source.agent_type,
            version="1.0.0",
            model_provider=source.model_provider,
            model_name=source.model_name,
            temperature=source.temperature,
            max_tokens=source.max_tokens,
            system_prompt=source.system_prompt,
            capabilities=source.capabilities,
            supported_integrations=source.supported_integrations,
            is_autonomous=source.is_autonomous,
            can_make_decisions=source.can_make_decisions,
            can_execute_code=source.can_execute_code,
            tags=source.tags,
            category=source.category,
            is_public=False,  # Start as private
            created_at=datetime.utcnow()
        )
        
        self.db.add(cloned_agent)
        self.db.commit()
        
        return {
            "agent_id": new_agent_id,
            "name": new_name,
            "source_agent_id": source_agent_id,
            "created_at": cloned_agent.created_at.isoformat()
        }
