"""
Phase 26: Shared Insights Service
Insight sharing, consensus scoring, comments, reactions
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Set
import uuid

# ========================================================================
# ENUMS
# ========================================================================

class ReactionType(Enum):
    """Emoji reactions on insights"""
    THUMBS_UP = "👍"
    THUMBS_DOWN = "👎"
    LIGHTBULB = "💡"
    WARNING = "⚠️"
    FIRE = "🔥"
    THINKING = "🤔"

class InsightVisibility(Enum):
    """Insight visibility levels"""
    PERSONAL = "personal"
    TEAM = "team"
    DEPARTMENT = "department"
    ORGANIZATION = "organization"


# ========================================================================
# DATACLASSES
# ========================================================================

@dataclass
class InsightComment:
    """Comment on shared insight"""
    comment_id: str
    insight_id: str
    user_id: str
    text: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    mentions: List[str] = field(default_factory=list)

@dataclass
class InsightReaction:
    """Reaction to insight"""
    reaction_id: str
    insight_id: str
    user_id: str
    reaction_type: ReactionType
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class SharedInsight:
    """Shared insight with collaboration metadata"""
    insight_id: str
    original_insight_id: str
    workspace_id: str
    shared_by: str
    shared_at: datetime
    visibility: InsightVisibility
    description: Optional[str] = None
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # reaction_type -> [user_ids]
    comments: List[InsightComment] = field(default_factory=list)
    followers: Set[str] = field(default_factory=set)
    consensus_score: float = 0.0
    agreement_count: int = 0
    disagreement_count: int = 0

@dataclass
class InsightThread:
    """Discussion thread on insight"""
    thread_id: str
    insight_id: str
    title: str
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    comments: List[InsightComment] = field(default_factory=list)
    participants: Set[str] = field(default_factory=set)


# ========================================================================
# SHARED INSIGHTS SERVICE
# ========================================================================

class SharedInsightsService:
    """Manages shared insights, comments, reactions, and consensus"""
    
    def __init__(self):
        self.shared_insights: Dict[str, SharedInsight] = {}
        self.insight_comments: Dict[str, List[InsightComment]] = {}
        self.insight_reactions: Dict[str, List[InsightReaction]] = {}
        self.insight_followers: Dict[str, Set[str]] = {}
        self.insight_threads: Dict[str, InsightThread] = {}
    
    
    # ====================================================================
    # SHARING
    # ====================================================================
    
    def share_insight(self, original_insight_id: str, workspace_id: str,
                     shared_by: str, visibility: InsightVisibility,
                     description: Optional[str] = None) -> SharedInsight:
        """Share insight with team"""
        insight_id = str(uuid.uuid4())
        
        insight = SharedInsight(
            insight_id=insight_id,
            original_insight_id=original_insight_id,
            workspace_id=workspace_id,
            shared_by=shared_by,
            shared_at=datetime.utcnow(),
            visibility=visibility,
            description=description
        )
        
        self.shared_insights[insight_id] = insight
        self.insight_followers[insight_id] = {shared_by}
        self.insight_comments[insight_id] = []
        self.insight_reactions[insight_id] = []
        
        return insight
    
    def get_shared_insight(self, insight_id: str) -> Optional[SharedInsight]:
        """Get shared insight"""
        return self.shared_insights.get(insight_id)
    
    def unshare_insight(self, insight_id: str) -> bool:
        """Unshare insight"""
        if insight_id in self.shared_insights:
            del self.shared_insights[insight_id]
            if insight_id in self.insight_comments:
                del self.insight_comments[insight_id]
            if insight_id in self.insight_reactions:
                del self.insight_reactions[insight_id]
            if insight_id in self.insight_followers:
                del self.insight_followers[insight_id]
            return True
        return False
    
    
    # ====================================================================
    # COMMENTS
    # ====================================================================
    
    def add_comment(self, insight_id: str, user_id: str, text: str,
                   mentions: Optional[List[str]] = None) -> InsightComment:
        """Add comment to insight"""
        comment = InsightComment(
            comment_id=str(uuid.uuid4()),
            insight_id=insight_id,
            user_id=user_id,
            text=text,
            mentions=mentions or []
        )
        
        if insight_id not in self.insight_comments:
            self.insight_comments[insight_id] = []
        
        self.insight_comments[insight_id].append(comment)
        
        # Add to insight if it exists
        if insight_id in self.shared_insights:
            self.shared_insights[insight_id].comments.append(comment)
        
        return comment
    
    def get_comments(self, insight_id: str) -> List[InsightComment]:
        """Get all comments on insight"""
        return self.insight_comments.get(insight_id, [])
    
    def update_comment(self, comment_id: str, new_text: str) -> Optional[InsightComment]:
        """Update comment"""
        for comments_list in self.insight_comments.values():
            for comment in comments_list:
                if comment.comment_id == comment_id:
                    comment.text = new_text
                    comment.updated_at = datetime.utcnow()
                    return comment
        return None
    
    def delete_comment(self, insight_id: str, comment_id: str) -> bool:
        """Delete comment"""
        if insight_id in self.insight_comments:
            self.insight_comments[insight_id] = [
                c for c in self.insight_comments[insight_id]
                if c.comment_id != comment_id
            ]
            return True
        return False
    
    
    # ====================================================================
    # REACTIONS
    # ====================================================================
    
    def add_reaction(self, insight_id: str, user_id: str,
                    reaction_type: ReactionType) -> InsightReaction:
        """Add reaction to insight"""
        # Remove previous reaction from user
        if insight_id in self.insight_reactions:
            self.insight_reactions[insight_id] = [
                r for r in self.insight_reactions[insight_id]
                if r.user_id != user_id
            ]
        
        reaction = InsightReaction(
            reaction_id=str(uuid.uuid4()),
            insight_id=insight_id,
            user_id=user_id,
            reaction_type=reaction_type
        )
        
        if insight_id not in self.insight_reactions:
            self.insight_reactions[insight_id] = []
        
        self.insight_reactions[insight_id].append(reaction)
        
        # Update shared insight reactions
        if insight_id in self.shared_insights:
            insight = self.shared_insights[insight_id]
            reaction_key = reaction_type.value
            if reaction_key not in insight.reactions:
                insight.reactions[reaction_key] = []
            if user_id not in insight.reactions[reaction_key]:
                insight.reactions[reaction_key].append(user_id)
            
            # Update consensus score
            self._update_consensus_score(insight)
        
        return reaction
    
    def get_reactions(self, insight_id: str) -> List[InsightReaction]:
        """Get all reactions on insight"""
        return self.insight_reactions.get(insight_id, [])
    
    def get_reactions_summary(self, insight_id: str) -> Dict[str, int]:
        """Get summary of reactions"""
        reactions = self.get_reactions(insight_id)
        summary = {}
        for reaction in reactions:
            emoji = reaction.reaction_type.value
            summary[emoji] = summary.get(emoji, 0) + 1
        return summary
    
    
    # ====================================================================
    # CONSENSUS SCORING
    # ====================================================================
    
    def _update_consensus_score(self, insight: SharedInsight) -> None:
        """Calculate consensus score"""
        total_reactions = sum(len(users) for users in insight.reactions.values())
        
        if total_reactions == 0:
            insight.consensus_score = 0.0
            insight.agreement_count = 0
            insight.disagreement_count = 0
            return
        
        # Count positive and negative reactions
        agreement = (
            len(insight.reactions.get("👍", [])) +
            len(insight.reactions.get("💡", [])) +
            len(insight.reactions.get("🔥", []))
        )
        
        disagreement = len(insight.reactions.get("👎", []))
        
        # Consensus score: (agreement - disagreement) / total
        consensus = (agreement - disagreement) / total_reactions
        insight.consensus_score = max(0, min(1, (consensus + 1) / 2))  # Normalize to 0-1
        
        insight.agreement_count = agreement
        insight.disagreement_count = disagreement
    
    def get_consensus_score(self, insight_id: str) -> float:
        """Get insight consensus score"""
        insight = self.shared_insights.get(insight_id)
        return insight.consensus_score if insight else 0.0
    
    
    # ====================================================================
    # FOLLOWING
    # ====================================================================
    
    def follow_insight(self, insight_id: str, user_id: str) -> bool:
        """Follow insight for notifications"""
        if insight_id not in self.insight_followers:
            self.insight_followers[insight_id] = set()
        
        self.insight_followers[insight_id].add(user_id)
        
        # Add to insight
        if insight_id in self.shared_insights:
            self.shared_insights[insight_id].followers.add(user_id)
        
        return True
    
    def unfollow_insight(self, insight_id: str, user_id: str) -> bool:
        """Unfollow insight"""
        if insight_id in self.insight_followers:
            self.insight_followers[insight_id].discard(user_id)
            
            if insight_id in self.shared_insights:
                self.shared_insights[insight_id].followers.discard(user_id)
            
            return True
        return False
    
    def get_followers(self, insight_id: str) -> Set[str]:
        """Get insight followers"""
        return self.insight_followers.get(insight_id, set())
    
    
    # ====================================================================
    # INSIGHT FEED
    # ====================================================================
    
    def get_workspace_insight_feed(self, workspace_id: str, limit: int = 50) -> List[SharedInsight]:
        """Get shared insights feed for workspace"""
        insights = [i for i in self.shared_insights.values()
                   if i.workspace_id == workspace_id]
        
        # Sort by recency
        insights = sorted(insights, key=lambda i: i.shared_at, reverse=True)
        return insights[:limit]
    
    def get_user_insight_feed(self, user_id: str, workspace_id: str,
                             limit: int = 50) -> List[SharedInsight]:
        """Get insights user is following"""
        following = [i for i in self.shared_insights.values()
                    if (i.workspace_id == workspace_id and user_id in i.followers)]
        
        following = sorted(following, key=lambda i: i.shared_at, reverse=True)
        return following[:limit]
    
    def get_trending_insights(self, workspace_id: str, limit: int = 10) -> List[SharedInsight]:
        """Get trending insights by reactions"""
        insights = [i for i in self.shared_insights.values()
                   if i.workspace_id == workspace_id]
        
        # Sort by total reactions
        insights = sorted(insights,
                         key=lambda i: sum(len(users) for users in i.reactions.values()),
                         reverse=True)
        return insights[:limit]
    
    
    # ========================================================================
    # THREADS
    # ========================================================================
    
    def create_thread(self, insight_id: str, title: str, created_by: str) -> InsightThread:
        """Create discussion thread on insight"""
        thread_id = str(uuid.uuid4())
        
        thread = InsightThread(
            thread_id=thread_id,
            insight_id=insight_id,
            title=title,
            created_by=created_by,
            participants={created_by}
        )
        
        self.insight_threads[thread_id] = thread
        return thread
    
    def add_thread_comment(self, thread_id: str, user_id: str, text: str) -> Optional[InsightComment]:
        """Add comment to thread"""
        if thread_id not in self.insight_threads:
            return None
        
        comment = InsightComment(
            comment_id=str(uuid.uuid4()),
            insight_id="",  # Not linked to specific insight
            user_id=user_id,
            text=text
        )
        
        thread = self.insight_threads[thread_id]
        thread.comments.append(comment)
        thread.participants.add(user_id)
        
        return comment
    
    def get_thread(self, thread_id: str) -> Optional[InsightThread]:
        """Get discussion thread"""
        return self.insight_threads.get(thread_id)
    
    def get_insight_threads(self, insight_id: str) -> List[InsightThread]:
        """Get all threads on insight"""
        return [t for t in self.insight_threads.values()
               if t.insight_id == insight_id]
