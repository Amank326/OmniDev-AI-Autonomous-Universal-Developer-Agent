"""
Phase 11: Cost Analyzer
Calculate and optimize workflow execution costs
"""

import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class CostAnalyzer:
    """
    Analyzes workflow execution costs and suggests cost optimizations
    Tracks per-action costs, monthly forecasts, and cost-saving strategies
    """

    def __init__(self):
        # Cost per action type (in cents)
        self.action_costs = {
            "send_email": 0.01,
            "send_slack": 0.005,
            "send_sms": 0.10,
            "create_record": 0.02,
            "update_record": 0.02,
            "delete_record": 0.01,
            "query_data": 0.01,
            "call_api": 0.05,
            "export_data": 0.10,
            "log_event": 0.001,
            "create_alert": 0.02,
            "send_notification": 0.01,
        }

        # Infrastructure costs (per execution in cents)
        self.infra_cost_per_execution = 0.10

        # Monthly fixed costs (in dollars)
        self.fixed_monthly_costs = {
            "platform_fee": 99.99,
            "database": 50.00,
            "storage": 25.00,
        }

        self.execution_history = []
        self.cost_optimizations = []

    def calculate_execution_cost(self, execution: Dict) -> float:
        """Calculate total cost for a workflow execution"""
        cost = 0.0

        # Add action costs
        nodes = execution.get("nodes", [])
        for node in nodes:
            action_type = node.get("action_type")
            action_cost = self.action_costs.get(action_type, 0.02)

            # Multiply by count if action executed multiple times
            exec_count = node.get("execution_count", 1)
            cost += action_cost * exec_count

        # Add infrastructure cost
        cost += self.infra_cost_per_execution

        # Add data transfer cost if applicable
        data_transfer_mb = sum(
            n.get("data_transfer_mb", 0) for n in nodes
        )
        cost += data_transfer_mb * 0.10  # $0.10 per MB

        return round(cost / 100, 4)  # Convert cents to dollars

    def analyze_workflow_costs(self, workflow_id: str, executions: List[Dict]) -> Dict:
        """
        Analyze costs for a specific workflow
        Returns detailed cost breakdown and savings opportunities
        """
        logger.info(f"Analyzing costs for workflow {workflow_id}")

        if not executions:
            return {"status": "no_data"}

        # Calculate costs
        total_cost = 0
        per_action_costs = defaultdict(float)
        execution_costs = []

        for execution in executions:
            exec_cost = self.calculate_execution_cost(execution)
            total_cost += exec_cost
            execution_costs.append(exec_cost)

            # Track per-action costs
            for node in execution.get("nodes", []):
                action_type = node.get("action_type")
                action_cost = self.action_costs.get(action_type, 0.02) / 100
                per_action_costs[action_type] += action_cost

        # Calculate statistics
        avg_cost = total_cost / len(executions) if executions else 0
        min_cost = min(execution_costs) if execution_costs else 0
        max_cost = max(execution_costs) if execution_costs else 0

        # Find cost drivers
        cost_drivers = sorted(
            per_action_costs.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Identify optimization opportunities
        optimization_opportunities = self._find_cost_optimizations(
            workflow_id, executions, per_action_costs
        )

        # Monthly forecast
        monthly_forecast = self._calculate_monthly_forecast(
            len(executions),
            avg_cost
        )

        analysis = {
            "workflow_id": workflow_id,
            "total_executions": len(executions),
            "total_cost": round(total_cost, 4),
            "avg_cost_per_execution": round(avg_cost, 4),
            "min_cost": round(min_cost, 4),
            "max_cost": round(max_cost, 4),
            "cost_drivers": [
                {"action": action, "total_cost": round(cost, 4)}
                for action, cost in cost_drivers
            ],
            "optimization_opportunities": optimization_opportunities,
            "monthly_forecast": monthly_forecast,
        }

        self.execution_history.extend(executions)
        return analysis

    def _find_cost_optimizations(self, workflow_id: str, executions: List,
                                 per_action_costs: Dict) -> List[Dict]:
        """Find opportunities to reduce costs"""
        opportunities = []

        # Find expensive actions
        for action, cost in per_action_costs.items():
            if cost > 1.0:  # More than $1
                opportunities.append({
                    "type": "expensive_action",
                    "action": action,
                    "current_cost": round(cost, 4),
                    "suggestion": self._get_action_alternative(action),
                    "potential_savings": round(cost * 0.3, 4),
                })

        # Find inefficient execution patterns
        inefficient = self._find_inefficient_patterns(executions)
        opportunities.extend(inefficient)

        # Find caching opportunities
        caching = self._find_caching_opportunities(executions)
        if caching:
            opportunities.append(caching)

        return opportunities[:5]

    def _get_action_alternative(self, action: str) -> str:
        """Suggest cheaper alternative for an action"""
        alternatives = {
            "send_sms": "Use cheaper bulk SMS provider",
            "call_api": "Implement caching for API calls",
            "export_data": "Use scheduled batch exports instead",
        }
        return alternatives.get(action, "Consider bulk operations")

    def _find_inefficient_patterns(self, executions: List) -> List[Dict]:
        """Find inefficient execution patterns"""
        opportunities = []

        # Find repeated actions in same workflow
        for execution in executions[:10]:  # Sample first 10
            action_counts = defaultdict(int)
            for node in execution.get("nodes", []):
                action_type = node.get("action_type")
                action_counts[action_type] += 1

            for action, count in action_counts.items():
                if count > 3:
                    opportunities.append({
                        "type": "repeated_action",
                        "action": action,
                        "occurrences": count,
                        "suggestion": "Consolidate repeated actions into single batch operation",
                        "potential_savings": round(self.action_costs.get(action, 0.02) / 100 * count * 0.5, 4),
                    })

        return opportunities

    def _find_caching_opportunities(self, executions: List) -> Dict:
        """Find caching opportunities"""
        # Identify query actions that repeat frequently
        query_actions = [
            node for exec in executions
            for node in exec.get("nodes", [])
            if node.get("action_type") == "query_data"
        ]

        if len(query_actions) > 5:
            total_query_cost = len(query_actions) * (self.action_costs.get("query_data", 0.01) / 100)
            return {
                "type": "caching_opportunity",
                "suggestion": "Implement caching for frequently executed queries",
                "current_cost": round(total_query_cost, 4),
                "potential_savings": round(total_query_cost * 0.7, 4),
                "implementation_effort": "medium",
            }

        return None

    def _calculate_monthly_forecast(self, executions_in_sample: int,
                                    avg_cost_per_execution: float) -> Dict:
        """Forecast monthly costs based on execution frequency"""
        # Assume sample represents one day
        daily_executions = executions_in_sample
        monthly_executions = daily_executions * 30

        variable_cost = monthly_executions * avg_cost_per_execution
        total_monthly_cost = variable_cost + sum(self.fixed_monthly_costs.values())

        return {
            "estimated_monthly_executions": monthly_executions,
            "estimated_variable_cost": round(variable_cost, 2),
            "fixed_costs": self.fixed_monthly_costs,
            "total_estimated_monthly": round(total_monthly_cost, 2),
        }

    def get_cost_breakdown_by_action(self) -> Dict[str, float]:
        """Get cost breakdown across all actions"""
        breakdown = {}

        for action, unit_cost in self.action_costs.items():
            # Count executions in history
            exec_count = sum(
                1 for exec in self.execution_history
                for node in exec.get("nodes", [])
                if node.get("action_type") == action
            )

            breakdown[action] = {
                "unit_cost": unit_cost / 100,
                "total_executions": exec_count,
                "total_cost": round(exec_count * unit_cost / 100, 4),
            }

        return breakdown

    def apply_cost_optimization(self, workflow_id: str,
                               optimization: Dict) -> Dict:
        """Apply a cost optimization to a workflow"""
        result = {
            "workflow_id": workflow_id,
            "optimization": optimization.get("type"),
            "status": "applied",
            "estimated_monthly_savings": optimization.get("potential_savings", 0),
        }

        self.cost_optimizations.append({
            "workflow_id": workflow_id,
            "optimization": optimization,
            "applied_at": datetime.utcnow().isoformat(),
        })

        return result

    def compare_cost_scenarios(self, scenario_a: Dict, scenario_b: Dict) -> Dict:
        """Compare costs between two workflow scenarios"""
        cost_a = sum(
            self.action_costs.get(node.get("action_type"), 0.02) / 100
            for node in scenario_a.get("nodes", [])
        )

        cost_b = sum(
            self.action_costs.get(node.get("action_type"), 0.02) / 100
            for node in scenario_b.get("nodes", [])
        )

        savings = cost_a - cost_b
        savings_percent = (savings / cost_a * 100) if cost_a > 0 else 0

        return {
            "scenario_a_cost": round(cost_a, 4),
            "scenario_b_cost": round(cost_b, 4),
            "potential_savings": round(savings, 4),
            "savings_percentage": round(savings_percent, 2),
            "better_scenario": "B" if cost_b < cost_a else "A",
        }

    def get_most_expensive_workflows(self, top_k: int = 10) -> List[Dict]:
        """Get most expensive workflows from history"""
        workflow_costs = defaultdict(float)
        workflow_executions = defaultdict(int)

        for execution in self.execution_history:
            workflow_id = execution.get("workflow_id")
            cost = self.calculate_execution_cost(execution)
            workflow_costs[workflow_id] += cost
            workflow_executions[workflow_id] += 1

        expensive = [
            {
                "workflow_id": wf_id,
                "total_cost": round(cost, 4),
                "executions": workflow_executions[wf_id],
                "avg_cost_per_execution": round(cost / workflow_executions[wf_id], 4),
            }
            for wf_id, cost in workflow_costs.items()
        ]

        expensive.sort(key=lambda x: x["total_cost"], reverse=True)
        return expensive[:top_k]

    def generate_cost_report(self, workflow_id: str = None) -> str:
        """Generate human-readable cost report"""
        if workflow_id:
            executions = [e for e in self.execution_history if e.get("workflow_id") == workflow_id]
            if not executions:
                return f"No cost data for workflow {workflow_id}"

            analysis = self.analyze_workflow_costs(workflow_id, executions)
        else:
            if not self.execution_history:
                return "No cost data available"

            total_cost = sum(
                self.calculate_execution_cost(e)
                for e in self.execution_history
            )
            analysis = {
                "total_cost": total_cost,
                "total_executions": len(self.execution_history),
            }

        report = f"""
Cost Report: {workflow_id or 'All Workflows'}

Total Cost: ${analysis.get('total_cost', 0):.2f}
Total Executions: {analysis.get('total_executions', 0)}
Average Cost per Execution: ${analysis.get('avg_cost_per_execution', 0):.4f}

Cost Drivers:
"""
        for driver in analysis.get('cost_drivers', [])[:5]:
            report += f"- {driver['action']}: ${driver['total_cost']:.4f}\n"

        report += f"\nOptimization Opportunities:\n"
        for opp in analysis.get('optimization_opportunities', [])[:3]:
            report += f"- {opp['suggestion']} (Save: ${opp.get('potential_savings', 0):.2f})\n"

        if analysis.get('monthly_forecast'):
            forecast = analysis['monthly_forecast']
            report += f"\nMonthly Forecast:\n"
            report += f"- Estimated executions: {forecast.get('estimated_monthly_executions', 0)}\n"
            report += f"- Total estimated cost: ${forecast.get('total_estimated_monthly', 0):.2f}\n"

        return report
