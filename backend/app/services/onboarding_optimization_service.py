"""
Onboarding Optimization Service - Personalized onboarding paths and milestone tracking
Segments customers and guides them through success milestones
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class CustomerSegment(Enum):
    """Customer onboarding segments"""
    STARTUP = "startup"                  # SMB, first-time user
    GROWING_TEAM = "growing_team"        # 10-50 people
    ENTERPRISE = "enterprise"            # 50+ people
    TECHNICAL = "technical"              # Engineers/developers


class OnboardingPhase(Enum):
    """Onboarding phases"""
    WELCOME = "welcome"
    SETUP = "setup"
    FIRST_SUCCESS = "first_success"
    EXPLORATION = "exploration"
    OPTIMIZATION = "optimization"
    SUCCESS = "success"


class OnboardingMilestone(Enum):
    """Key onboarding milestones"""
    ACCOUNT_CREATED = "account_created"
    PROFILE_COMPLETED = "profile_completed"
    FIRST_PROJECT = "first_project"
    FIRST_EXECUTION = "first_execution"
    TEAM_INVITED = "team_invited"
    INTEGRATION_CONNECTED = "integration_connected"
    FIRST_AUTOMATION = "first_automation"
    TEAM_ACTIVE = "team_active"
    EXPANDED_USAGE = "expanded_usage"
    ADVANCED_FEATURES = "advanced_features"


class OnboardingOptimizationService:
    """
    Personalize onboarding experience based on customer segment
    Track milestone progression and provide contextual guidance
    """
    
    def __init__(self):
        """Initialize onboarding service"""
        self.customer_segments = {}
        self.onboarding_journeys = {}
        self.milestone_tracking = {}
        self.onboarding_completions = {}
        self.segment_cohorts = {}
        self.success_metrics = {}
    
    # ========================================================================
    # CUSTOMER SEGMENTATION
    # ========================================================================
    
    def segment_customer(
        self,
        customer_id: str,
        industry: Optional[str],
        team_size: Optional[int],
        use_case: Optional[str],
        technical_expertise: Optional[str],
    ) -> Dict:
        """
        Segment customer to determine onboarding path
        
        Factors:
        - Team size (startup vs enterprise)
        - Use case (automation, analytics, etc.)
        - Technical expertise (non-technical vs engineer)
        - Industry context
        """
        
        # Determine segment
        if team_size and team_size >= 50:
            segment = CustomerSegment.ENTERPRISE
        elif team_size and team_size >= 10:
            segment = CustomerSegment.GROWING_TEAM
        elif technical_expertise and technical_expertise in ["engineer", "developer", "technical"]:
            segment = CustomerSegment.TECHNICAL
        else:
            segment = CustomerSegment.STARTUP
        
        segmentation = {
            "customer_id": customer_id,
            "segment": segment.value,
            "team_size": team_size,
            "industry": industry,
            "use_case": use_case,
            "technical_expertise": technical_expertise,
            "segmented_at": datetime.utcnow().isoformat(),
        }
        
        # Store segmentation
        self.customer_segments[customer_id] = segmentation
        
        # Initialize journey for this segment
        journey = self._create_journey_for_segment(customer_id, segment)
        self.onboarding_journeys[customer_id] = journey
        
        return segmentation
    
    def _create_journey_for_segment(
        self,
        customer_id: str,
        segment: CustomerSegment,
    ) -> Dict:
        """Create customized onboarding journey for segment"""
        
        if segment == CustomerSegment.STARTUP:
            journey = {
                "customer_id": customer_id,
                "segment": segment.value,
                "phases": [
                    {
                        "phase": OnboardingPhase.WELCOME.value,
                        "duration_days": 1,
                        "activities": [
                            "Welcome email with quick start guide",
                            "Product walkthrough video (3 min)",
                            "Access to community Slack channel",
                        ],
                        "expected_milestone": OnboardingMilestone.PROFILE_COMPLETED.value,
                    },
                    {
                        "phase": OnboardingPhase.SETUP.value,
                        "duration_days": 3,
                        "activities": [
                            "Guided setup wizard",
                            "Project template selection",
                            "First integration connection",
                        ],
                        "expected_milestone": OnboardingMilestone.FIRST_PROJECT.value,
                    },
                    {
                        "phase": OnboardingPhase.FIRST_SUCCESS.value,
                        "duration_days": 7,
                        "activities": [
                            "First workflow execution",
                            "Success celebration (email + in-app)",
                            "Next steps recommendations",
                        ],
                        "expected_milestone": OnboardingMilestone.FIRST_EXECUTION.value,
                    },
                    {
                        "phase": OnboardingPhase.EXPLORATION.value,
                        "duration_days": 14,
                        "activities": [
                            "Feature discovery tour",
                            "Use case-specific guides",
                            "Best practice tips (weekly)",
                        ],
                        "expected_milestone": OnboardingMilestone.EXPANDED_USAGE.value,
                    },
                    {
                        "phase": OnboardingPhase.SUCCESS.value,
                        "duration_days": 0,
                        "activities": [
                            "Graduation email",
                            "Advanced features invitation",
                            "Tier upgrade recommendation",
                        ],
                        "expected_milestone": None,
                    },
                ],
                "created_at": datetime.utcnow().isoformat(),
            }
        
        elif segment == CustomerSegment.GROWING_TEAM:
            journey = {
                "customer_id": customer_id,
                "segment": segment.value,
                "phases": [
                    {
                        "phase": OnboardingPhase.WELCOME.value,
                        "duration_days": 1,
                        "activities": [
                            "Welcome call with onboarding specialist",
                            "Team training video series",
                            "Admin setup checklist",
                        ],
                        "expected_milestone": OnboardingMilestone.PROFILE_COMPLETED.value,
                    },
                    {
                        "phase": OnboardingPhase.SETUP.value,
                        "duration_days": 5,
                        "activities": [
                            "Team workspace setup",
                            "Role and permission configuration",
                            "Multiple project templates",
                            "Integration setup (3-5 key systems)",
                        ],
                        "expected_milestone": OnboardingMilestone.TEAM_INVITED.value,
                    },
                    {
                        "phase": OnboardingPhase.FIRST_SUCCESS.value,
                        "duration_days": 7,
                        "activities": [
                            "Team kickoff meeting",
                            "First workflow deployment",
                            "Success celebration and ROI calculation",
                        ],
                        "expected_milestone": OnboardingMilestone.FIRST_EXECUTION.value,
                    },
                    {
                        "phase": OnboardingPhase.EXPLORATION.value,
                        "duration_days": 21,
                        "activities": [
                            "Advanced features workshop",
                            "Team best practices session",
                            "Collaboration features deep-dive",
                            "API/webhook integration training",
                        ],
                        "expected_milestone": OnboardingMilestone.TEAM_ACTIVE.value,
                    },
                    {
                        "phase": OnboardingPhase.OPTIMIZATION.value,
                        "duration_days": 30,
                        "activities": [
                            "Performance optimization review",
                            "Custom reporting setup",
                            "Advanced automation patterns",
                        ],
                        "expected_milestone": OnboardingMilestone.ADVANCED_FEATURES.value,
                    },
                    {
                        "phase": OnboardingPhase.SUCCESS.value,
                        "duration_days": 0,
                        "activities": [
                            "Tier optimization recommendation",
                            "Account review and expansion planning",
                            "Access to dedicated success manager",
                        ],
                        "expected_milestone": None,
                    },
                ],
                "created_at": datetime.utcnow().isoformat(),
            }
        
        elif segment == CustomerSegment.ENTERPRISE:
            journey = {
                "customer_id": customer_id,
                "segment": segment.value,
                "phases": [
                    {
                        "phase": OnboardingPhase.WELCOME.value,
                        "duration_days": 1,
                        "activities": [
                            "Executive welcome call",
                            "Org chart and stakeholder mapping",
                            "Requirements gathering session",
                        ],
                        "expected_milestone": OnboardingMilestone.PROFILE_COMPLETED.value,
                    },
                    {
                        "phase": OnboardingPhase.SETUP.value,
                        "duration_days": 10,
                        "activities": [
                            "Custom implementation plan",
                            "Enterprise SSO/directory integration",
                            "Multi-workspace setup",
                            "Custom security policies",
                            "Audit logging configuration",
                        ],
                        "expected_milestone": OnboardingMilestone.INTEGRATION_CONNECTED.value,
                    },
                    {
                        "phase": OnboardingPhase.FIRST_SUCCESS.value,
                        "duration_days": 14,
                        "activities": [
                            "Pilot program launch",
                            "Dept-specific training sessions",
                            "Success metrics baseline establishment",
                        ],
                        "expected_milestone": OnboardingMilestone.FIRST_AUTOMATION.value,
                    },
                    {
                        "phase": OnboardingPhase.EXPLORATION.value,
                        "duration_days": 30,
                        "activities": [
                            "Department expansion workshops",
                            "Custom integration development",
                            "Advanced governance setup",
                            "Cross-functional training",
                        ],
                        "expected_milestone": OnboardingMilestone.EXPANDED_USAGE.value,
                    },
                    {
                        "phase": OnboardingPhase.OPTIMIZATION.value,
                        "duration_days": 45,
                        "activities": [
                            "Organization-wide best practices",
                            "Custom reporting dashboards",
                            "Governance and compliance review",
                            "Optimization recommendations",
                        ],
                        "expected_milestone": OnboardingMilestone.ADVANCED_FEATURES.value,
                    },
                    {
                        "phase": OnboardingPhase.SUCCESS.value,
                        "duration_days": 0,
                        "activities": [
                            "Executive business review",
                            "Dedicated success manager assignment",
                            "Quarterly planning calls",
                            "Innovation roadmap discussion",
                        ],
                        "expected_milestone": None,
                    },
                ],
                "created_at": datetime.utcnow().isoformat(),
            }
        
        else:  # TECHNICAL segment
            journey = {
                "customer_id": customer_id,
                "segment": segment.value,
                "phases": [
                    {
                        "phase": OnboardingPhase.WELCOME.value,
                        "duration_days": 0,
                        "activities": [
                            "API documentation access",
                            "GitHub repository templates",
                            "Quick start code examples",
                        ],
                        "expected_milestone": OnboardingMilestone.PROFILE_COMPLETED.value,
                    },
                    {
                        "phase": OnboardingPhase.SETUP.value,
                        "duration_days": 3,
                        "activities": [
                            "API key generation",
                            "SDK installation",
                            "Authentication setup",
                            "Sample application deployment",
                        ],
                        "expected_milestone": OnboardingMilestone.FIRST_PROJECT.value,
                    },
                    {
                        "phase": OnboardingPhase.FIRST_SUCCESS.value,
                        "duration_days": 5,
                        "activities": [
                            "First API call",
                            "Webhook integration",
                            "Error handling patterns",
                        ],
                        "expected_milestone": OnboardingMilestone.FIRST_EXECUTION.value,
                    },
                    {
                        "phase": OnboardingPhase.EXPLORATION.value,
                        "duration_days": 14,
                        "activities": [
                            "Advanced API features",
                            "CLI tool usage",
                            "Custom integration patterns",
                            "Performance optimization tips",
                        ],
                        "expected_milestone": OnboardingMilestone.ADVANCED_FEATURES.value,
                    },
                    {
                        "phase": OnboardingPhase.SUCCESS.value,
                        "duration_days": 0,
                        "activities": [
                            "Technical excellence certification",
                            "Access to beta features",
                            "Direct engineering support",
                        ],
                        "expected_milestone": None,
                    },
                ],
                "created_at": datetime.utcnow().isoformat(),
            }
        
        return journey
    
    # ========================================================================
    # MILESTONE TRACKING
    # ========================================================================
    
    def track_milestone(
        self,
        customer_id: str,
        milestone: str,
    ) -> Dict:
        """
        Track customer milestone achievement
        
        Triggers:
        - Milestone-specific celebration
        - Next phase initiation
        - Progress assessment
        """
        
        milestone_data = {
            "customer_id": customer_id,
            "milestone": milestone,
            "achieved_at": datetime.utcnow().isoformat(),
        }
        
        # Store milestone
        if customer_id not in self.milestone_tracking:
            self.milestone_tracking[customer_id] = []
        self.milestone_tracking[customer_id].append(milestone_data)
        
        # Determine next milestone based on journey
        if customer_id in self.onboarding_journeys:
            journey = self.onboarding_journeys[customer_id]
            next_milestone = self._determine_next_milestone(journey, milestone)
        else:
            next_milestone = None
        
        return {
            "milestone": milestone,
            "achieved_at": milestone_data["achieved_at"],
            "next_milestone": next_milestone,
            "celebration_message": self._get_celebration_message(milestone),
            "next_actions": self._get_next_actions(milestone),
        }
    
    def _determine_next_milestone(self, journey: Dict, current_milestone: str) -> Optional[str]:
        """Determine next expected milestone"""
        
        for phase in journey.get("phases", []):
            if phase.get("expected_milestone") == current_milestone:
                # Find next phase with a milestone
                current_idx = journey["phases"].index(phase)
                for next_phase in journey["phases"][current_idx + 1:]:
                    if next_phase.get("expected_milestone"):
                        return next_phase["expected_milestone"]
        
        return None
    
    def _get_celebration_message(self, milestone: str) -> str:
        """Get celebration message for milestone"""
        
        messages = {
            OnboardingMilestone.ACCOUNT_CREATED.value: "🎉 Welcome! Your journey begins now.",
            OnboardingMilestone.PROFILE_COMPLETED.value: "✅ Profile complete! You're all set up.",
            OnboardingMilestone.FIRST_PROJECT.value: "🚀 First project created! Let's automate.",
            OnboardingMilestone.FIRST_EXECUTION.value: "⚡ First automation executed! You're doing great.",
            OnboardingMilestone.TEAM_INVITED.value: "👥 Team joined! Collaboration starts now.",
            OnboardingMilestone.INTEGRATION_CONNECTED.value: "🔗 Integration connected! Systems unified.",
            OnboardingMilestone.FIRST_AUTOMATION.value: "🤖 First automation live! Time savings incoming.",
            OnboardingMilestone.TEAM_ACTIVE.value: "💪 Team fully activated! Momentum building.",
            OnboardingMilestone.EXPANDED_USAGE.value: "📈 Expanding usage! Growing with us.",
            OnboardingMilestone.ADVANCED_FEATURES.value: "🌟 Advanced features unlocked! Expert level.",
        }
        
        return messages.get(milestone, "✨ Great progress!")
    
    def _get_next_actions(self, milestone: str) -> List[str]:
        """Get recommended next actions after milestone"""
        
        actions = {
            OnboardingMilestone.PROFILE_COMPLETED.value: [
                "Invite your first team member",
                "Connect your first integration",
            ],
            OnboardingMilestone.FIRST_PROJECT.value: [
                "Create your first automation",
                "Test with sample data",
            ],
            OnboardingMilestone.FIRST_EXECUTION.value: [
                "Review execution results",
                "Optimize your workflow",
                "Try another automation",
            ],
            OnboardingMilestone.TEAM_INVITED.value: [
                "Assign team roles",
                "Set up team workflows",
                "Create team guidelines",
            ],
            OnboardingMilestone.ADVANCED_FEATURES.value: [
                "Explore API integrations",
                "Create custom dashboards",
                "Optimize advanced settings",
            ],
        }
        
        return actions.get(milestone, ["Continue exploring features"])
    
    # ========================================================================
    # ONBOARDING PROGRESS & COMPLETION
    # ========================================================================
    
    def get_onboarding_progress(self, customer_id: str) -> Dict:
        """
        Get customer's onboarding progress
        
        Returns:
        - Current phase
        - Milestone completion %
        - Time to completion estimate
        - Phase-specific actions
        """
        
        if customer_id not in self.onboarding_journeys:
            return {"error": "No onboarding journey found"}
        
        journey = self.onboarding_journeys[customer_id]
        completed_milestones = set()
        
        if customer_id in self.milestone_tracking:
            completed_milestones = {
                m["milestone"] for m in self.milestone_tracking[customer_id]
            }
        
        # Determine current phase
        current_phase_idx = 0
        for idx, phase in enumerate(journey.get("phases", [])):
            milestone = phase.get("expected_milestone")
            if milestone and milestone not in completed_milestones:
                current_phase_idx = idx
                break
        else:
            # All milestones completed
            current_phase_idx = len(journey.get("phases", [])) - 1
        
        current_phase = journey.get("phases", [])[current_phase_idx] if journey.get("phases") else {}
        
        # Calculate completion percentage
        total_phases = len(journey.get("phases", []))
        completion_percent = round((current_phase_idx / total_phases * 100), 1) if total_phases > 0 else 0
        
        # Calculate days remaining
        days_to_complete = 0
        for phase in journey.get("phases", [current_phase_idx:]):
            days_to_complete += phase.get("duration_days", 0)
        
        return {
            "customer_id": customer_id,
            "segment": journey.get("segment"),
            "completion_percent": completion_percent,
            "current_phase": current_phase.get("phase"),
            "current_phase_number": current_phase_idx + 1,
            "total_phases": total_phases,
            "completed_milestones": len(completed_milestones),
            "days_remaining": max(0, days_to_complete),
            "current_activities": current_phase.get("activities", []),
            "next_milestone": current_phase.get("expected_milestone"),
            "phase_progress": {
                "phase": current_phase.get("phase"),
                "duration_days": current_phase.get("duration_days"),
                "activities": current_phase.get("activities", []),
            },
        }
    
    def complete_onboarding(self, customer_id: str) -> Dict:
        """
        Mark onboarding as complete
        Triggers graduation email and advanced feature access
        """
        
        completion = {
            "customer_id": customer_id,
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed",
            "graduation_benefits": [
                "Access to advanced features",
                "Priority support",
                "Exclusive webinars and training",
                "Tier upgrade eligibility",
            ],
            "next_milestones": [
                "Schedule quarterly business review",
                "Explore tier upgrade opportunities",
                "Join customer advisory council",
            ],
        }
        
        self.onboarding_completions[customer_id] = completion
        return completion
    
    # ========================================================================
    # COHORT ANALYTICS
    # ========================================================================
    
    def get_segment_performance(self, segment: str) -> Dict:
        """
        Get onboarding performance by segment
        
        Metrics:
        - Average time to completion
        - Milestone achievement rates
        - Dropout rates
        - Success correlation
        """
        
        segment_customers = [
            cid for cid, data in self.customer_segments.items()
            if data["segment"] == segment
        ]
        
        if not segment_customers:
            return {"segment": segment, "customers": 0}
        
        total = len(segment_customers)
        completed = sum(
            1 for cid in segment_customers
            if cid in self.onboarding_completions
        )
        
        avg_completion_days = 0
        if completed > 0:
            completion_days = []
            for cid in segment_customers:
                if cid in self.onboarding_completions:
                    created = datetime.fromisoformat(
                        self.customer_segments[cid].get("created_at", datetime.utcnow().isoformat())
                    )
                    completed_date = datetime.fromisoformat(
                        self.onboarding_completions[cid]["completed_at"]
                    )
                    completion_days.append((completed_date - created).days)
            
            avg_completion_days = round(sum(completion_days) / len(completion_days), 1)
        
        return {
            "segment": segment,
            "total_customers": total,
            "completed_count": completed,
            "completion_rate": round(completed / total * 100, 1),
            "avg_days_to_completion": avg_completion_days,
            "dropout_rate": round((total - completed) / total * 100, 1) if total > 0 else 0,
        }
    
    def get_milestone_achievement_rates(self, segment: Optional[str] = None) -> Dict:
        """Get achievement rates for each milestone"""
        
        all_milestones = [m.value for m in OnboardingMilestone]
        milestone_counts = {m: 0 for m in all_milestones}
        total_customers = 0
        
        for customer_id, milestones in self.milestone_tracking.items():
            if segment:
                customer_segment = self.customer_segments.get(customer_id, {}).get("segment")
                if customer_segment != segment:
                    continue
            
            total_customers += 1
            for m in milestones:
                milestone_counts[m["milestone"]] += 1
        
        if total_customers == 0:
            return {"error": "No customers found"}
        
        return {
            "segment": segment or "all",
            "total_customers": total_customers,
            "milestones": {
                milestone: {
                    "achieved_count": count,
                    "achievement_rate": round(count / total_customers * 100, 1),
                }
                for milestone, count in milestone_counts.items()
            },
        }
