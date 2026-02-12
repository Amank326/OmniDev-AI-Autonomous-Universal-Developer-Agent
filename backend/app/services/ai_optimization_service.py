"""
Phase 11: AI Optimization Service
Unified coordination service for all AI optimization features
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .nlp_workflow_generator import NLPWorkflowGenerator
from .ml_action_recommender import MLActionRecommender
from .performance_optimizer import PerformanceOptimizer
from .cost_analyzer import CostAnalyzer
from .anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)


class AIOptimizationService:
    """
    Central coordination service for AI-driven workflow optimization
    Integrates NLP, ML recommendations, performance analysis, cost optimization, and anomaly detection
    """

    def __init__(self):
        self.nlp_generator = NLPWorkflowGenerator()
        self.action_recommender = MLActionRecommender()
        self.performance_optimizer = PerformanceOptimizer()
        self.cost_analyzer = CostAnalyzer()
        self.anomaly_detector = AnomalyDetector()

        self.optimization_history = []
        self.ai_improvements = []

    def generate_workflow_from_description(self, description: str) -> Dict:
        """
        Generate a complete workflow from natural language description
        Returns workflow DAG ready for execution
        """
        logger.info(f"Generating workflow from: {description}")

        workflow = self.nlp_generator.generate_workflow_from_description(description)

        # Validate
        is_valid, errors = self.nlp_generator.validate_generated_workflow(workflow)
        if not is_valid:
            logger.warning(f"Generated workflow has issues: {errors}")

        # Get suggestions for improvement
        suggestions = self.nlp_generator.suggest_improvements(workflow)
        workflow["improvement_suggestions"] = suggestions

        return workflow

    def get_next_action_recommendations(self, current_action: str,
                                       workflow_context: Dict,
                                       top_k: int = 5) -> List[Dict]:
        """
        Get ML-based recommendations for next actions
        Uses execution history to suggest optimal continuations
        """
        recommendations = self.action_recommender.recommend_next_actions(
            current_action, workflow_context, top_k
        )

        # Add success probability predictions
        for rec in recommendations:
            probability, explanation = self.action_recommender.predict_action_success(
                rec["action"], workflow_context
            )
            rec["success_probability"] = probability
            rec["success_explanation"] = explanation

        return recommendations

    def analyze_and_optimize_workflow(self, workflow_id: str,
                                      executions: List[Dict]) -> Dict:
        """
        Comprehensive workflow optimization analysis
        Analyzes performance, costs, and anomalies, returns action plan
        """
        logger.info(f"Running comprehensive optimization for {workflow_id}")

        # Run all analyses
        performance_analysis = self.performance_optimizer.analyze_workflow_performance(
            workflow_id, executions
        )

        cost_analysis = self.cost_analyzer.analyze_workflow_costs(
            workflow_id, executions
        )

        # Check for anomalies
        for execution in executions:
            execution["workflow_id"] = workflow_id
            self.anomaly_detector.record_execution(execution)

        anomalies = self.anomaly_detector.detect_anomalies(workflow_id)

        # Get health score
        health_score = self.anomaly_detector.get_workflow_health_score(workflow_id)

        # Generate optimization plan
        optimization_plan = self._create_optimization_plan(
            performance_analysis, cost_analysis, anomalies
        )

        return {
            "workflow_id": workflow_id,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "health_score": health_score,
            "performance": performance_analysis,
            "cost": cost_analysis,
            "anomalies": anomalies,
            "optimization_plan": optimization_plan,
        }

    def _create_optimization_plan(self, perf_analysis: Dict,
                                  cost_analysis: Dict,
                                  anomalies: List) -> Dict:
        """Create actionable optimization plan from analyses"""
        plan = {
            "priority_improvements": [],
            "quick_wins": [],
            "medium_term": [],
            "estimated_total_improvement": 1.0,
        }

        # Quick wins: Easy to implement, high impact
        if cost_analysis.get("optimization_opportunities"):
            for opp in cost_analysis.get("optimization_opportunities", [])[:2]:
                if opp.get("potential_savings"):
                    plan["quick_wins"].append({
                        "type": opp.get("type"),
                        "description": opp.get("suggestion"),
                        "savings": opp.get("potential_savings"),
                        "effort": "low",
                    })

        # Priority improvements: Address anomalies
        critical_anomalies = [
            a for a in anomalies if a.get("severity") == "critical"
        ]
        if critical_anomalies:
            for anomaly in critical_anomalies:
                root_causes = self.anomaly_detector.find_root_cause(anomaly)
                plan["priority_improvements"].append({
                    "type": anomaly.get("type"),
                    "description": anomaly.get("description"),
                    "potential_causes": root_causes[:2],
                    "severity": "critical",
                })

        # Medium term: Performance improvements
        if perf_analysis.get("parallelization_opportunities"):
            for opp in perf_analysis.get("parallelization_opportunities", [])[:2]:
                plan["medium_term"].append({
                    "type": "parallelize",
                    "nodes": opp.get("nodes"),
                    "speedup": opp.get("potential_speedup"),
                    "effort": "medium",
                })

        return plan

    def get_workflow_auto_improvements(self, workflow_id: str) -> List[Dict]:
        """Get recommended auto-improvements for a workflow"""
        improvements = []

        # Check recent anomalies
        recent_anomalies = [
            a for a in self.anomaly_detector.anomalies
            if a.get("workflow_id") == workflow_id
        ]

        if recent_anomalies:
            for anomaly in recent_anomalies[:3]:
                improvement = {
                    "type": "fix_anomaly",
                    "anomaly_type": anomaly.get("type"),
                    "description": f"Fix {anomaly.get('type')}",
                    "action": anomaly.get("description"),
                }
                improvements.append(improvement)

        # Check for performance improvements
        perf_recs = [
            r for r in self.performance_optimizer.workflow_analytics.get(workflow_id, {}).get("recommendations", [])
        ]
        if perf_recs:
            for rec in perf_recs[:2]:
                improvements.append({
                    "type": "optimize_performance",
                    "description": rec,
                })

        return improvements

    def apply_workflow_optimization(self, workflow_id: str,
                                   optimization: Dict) -> Dict:
        """Apply an optimization to a workflow"""
        result = {
            "workflow_id": workflow_id,
            "optimization": optimization,
            "status": "applied",
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Track improvement
        self.ai_improvements.append(result)

        # Record in history
        self.optimization_history.append({
            "workflow_id": workflow_id,
            "optimization": optimization,
            "applied_at": datetime.utcnow(),
        })

        logger.info(f"Applied optimization to {workflow_id}: {optimization.get('type')}")
        return result

    def get_performance_benchmark(self, workflow_type: str) -> Dict:
        """Get performance benchmarks for a workflow type"""
        # These would be based on similar workflows
        benchmarks = {
            "notification": {
                "avg_duration": 2.5,
                "success_rate": 0.98,
                "typical_cost": 0.15,
            },
            "data_processing": {
                "avg_duration": 15.0,
                "success_rate": 0.95,
                "typical_cost": 0.50,
            },
            "api_integration": {
                "avg_duration": 5.0,
                "success_rate": 0.92,
                "typical_cost": 0.25,
            },
            "monitoring": {
                "avg_duration": 3.0,
                "success_rate": 0.99,
                "typical_cost": 0.10,
            },
        }

        return benchmarks.get(workflow_type, benchmarks["notification"])

    def get_system_insights(self) -> Dict:
        """Get system-wide insights from all optimization services"""
        # Most expensive workflows
        expensive = self.cost_analyzer.get_most_expensive_workflows(top_k=5)

        # Most common actions
        action_insights = {}
        for action_type in self.action_recommender.action_success_rates:
            action_insights[action_type] = self.action_recommender.get_action_insights(action_type)

        # System health
        workflow_health = {}
        for workflow_id in set(e.get("workflow_id") for e in self.anomaly_detector.execution_history):
            workflow_health[workflow_id] = self.anomaly_detector.get_workflow_health_score(workflow_id)

        insights = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_optimizations_applied": len(self.optimization_history),
            "most_expensive_workflows": expensive,
            "action_performance": action_insights,
            "workflow_health_scores": workflow_health,
            "optimization_trend": self._get_optimization_trend(),
        }

        return insights

    def _get_optimization_trend(self) -> str:
        """Analyze trend in optimizations applied"""
        if len(self.optimization_history) < 2:
            return "insufficient_data"

        recent = [
            o for o in self.optimization_history
            if (datetime.utcnow() - o["applied_at"]).days <= 7
        ]
        older = [
            o for o in self.optimization_history
            if (datetime.utcnow() - o["applied_at"]).days > 7 and
            (datetime.utcnow() - o["applied_at"]).days <= 30
        ]

        if len(recent) > len(older):
            return "increasing"
        elif len(recent) < len(older):
            return "decreasing"
        else:
            return "stable"

    def record_execution(self, execution: Dict) -> None:
        """Record workflow execution for learning and analysis"""
        # Record in anomaly detector
        self.anomaly_detector.record_execution(execution)

        # Record action transitions if nodes are available
        nodes = execution.get("nodes", [])
        for i in range(len(nodes) - 1):
            from_action = nodes[i].get("action_type")
            to_action = nodes[i + 1].get("action_type")
            if from_action and to_action:
                self.action_recommender.record_action_transition(from_action, to_action)

        # Record action execution
        for node in nodes:
            action_type = node.get("action_type")
            if action_type:
                self.action_recommender.record_action_execution(
                    execution.get("workflow_id"),
                    action_type,
                    {
                        "status": node.get("status"),
                        "duration": node.get("duration", 0),
                        "error": node.get("error"),
                        "context": node.get("context", {}),
                    }
                )

    def batch_generate_workflows(self, descriptions: List[str]) -> List[Dict]:
        """Generate multiple workflows from descriptions"""
        workflows = self.nlp_generator.batch_generate_workflows(descriptions)
        logger.info(f"Batch generated {len(workflows)} workflows")
        return workflows

    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data for AI optimization"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_insights": self.get_system_insights(),
            "recent_optimizations": [
                {
                    "workflow_id": h.get("workflow_id"),
                    "type": h.get("optimization", {}).get("type"),
                    "applied_at": h.get("applied_at").isoformat(),
                }
                for h in self.optimization_history[-10:]
            ],
            "total_workflows_improved": len(set(
                h.get("workflow_id") for h in self.optimization_history
            )),
            "total_cost_saved": self._calculate_total_cost_saved(),
        }

    def _calculate_total_cost_saved(self) -> float:
        """Calculate estimated total cost saved by optimizations"""
        total_saved = 0.0

        for optimization in self.optimization_history:
            opt_type = optimization.get("optimization", {}).get("type")
            if opt_type == "cost_optimization":
                total_saved += optimization.get("optimization", {}).get("savings", 0)

        return round(total_saved, 2)
