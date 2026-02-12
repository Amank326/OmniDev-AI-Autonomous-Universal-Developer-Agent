"""
Phase 10: Automation Rules Engine
Trigger-based automation with conditions and actions
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Trigger types"""
    EVENT = "event"
    TIME = "time"
    CONDITION = "condition"
    DATA = "data"
    WEBHOOK = "webhook"
    MANUAL = "manual"


class ConditionOperator(Enum):
    """Condition operators"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    MATCHES_REGEX = "matches_regex"


class AutomationRulesEngine:
    """
    Trigger-based automation engine
    Evaluates conditions and executes actions
    """

    def __init__(self):
        self.rules = {}  # rule_id -> rule definition
        self.action_handlers = {}  # action_type -> handler
        self.event_handlers = {}  # event_type -> list of rule_ids
        self.execution_history = {}  # execution tracking

    def register_action(self, action_type: str, handler: Callable):
        """Register an action handler"""
        self.action_handlers[action_type] = handler

    def create_rule(self, rule_config: Dict[str, Any]) -> str:
        """Create a new automation rule"""
        rule_id = str(uuid.uuid4())

        rule = {
            "id": rule_id,
            "name": rule_config.get("name", "Unnamed Rule"),
            "description": rule_config.get("description"),
            "is_enabled": rule_config.get("is_enabled", True),
            "trigger_type": rule_config.get("trigger_type", TriggerType.EVENT.value),
            "trigger_config": rule_config.get("trigger_config", {}),
            "conditions": rule_config.get("conditions", []),
            "condition_logic": rule_config.get("condition_logic", "AND"),
            "actions": rule_config.get("actions", []),
            "max_executions_per_day": rule_config.get("max_executions_per_day"),
            "execution_count_today": 0,
            "total_triggers": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "last_triggered_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        self.rules[rule_id] = rule

        # Register event listeners
        if rule["trigger_type"] == TriggerType.EVENT.value:
            event_type = rule["trigger_config"].get("event_type")
            if event_type:
                if event_type not in self.event_handlers:
                    self.event_handlers[event_type] = []
                self.event_handlers[event_type].append(rule_id)

        logger.info(f"Created rule: {rule_id} - {rule['name']}")
        return rule_id

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an automation rule"""
        if rule_id not in self.rules:
            return False

        rule = self.rules[rule_id]
        rule.update(updates)
        rule["updated_at"] = datetime.now(timezone.utc)

        logger.info(f"Updated rule: {rule_id}")
        return True

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule"""
        if rule_id not in self.rules:
            return False

        rule = self.rules[rule_id]
        
        # Unregister event listeners
        if rule["trigger_type"] == TriggerType.EVENT.value:
            event_type = rule["trigger_config"].get("event_type")
            if event_type and event_type in self.event_handlers:
                self.event_handlers[event_type].remove(rule_id)

        del self.rules[rule_id]
        logger.info(f"Deleted rule: {rule_id}")
        return True

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id]["is_enabled"] = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id]["is_enabled"] = False
            return True
        return False

    def evaluate_event(self, event_type: str, event_data: Dict[str, Any]) -> List[str]:
        """
        Evaluate rules triggered by an event
        Returns list of triggered rule IDs
        """
        triggered_rules = []

        rule_ids = self.event_handlers.get(event_type, [])

        for rule_id in rule_ids:
            rule = self.rules.get(rule_id)
            if not rule or not rule["is_enabled"]:
                continue

            # Check execution limits
            if self._check_execution_limit(rule):
                logger.warning(f"Rule {rule_id} execution limit reached")
                continue

            # Evaluate conditions
            if self._evaluate_conditions(rule.get("conditions", []),
                                        rule.get("condition_logic", "AND"),
                                        event_data):
                triggered_rules.append(rule_id)
                self._execute_rule(rule_id, event_data)

        return triggered_rules

    def evaluate_conditions(self, conditions: List[Dict], event_data: Dict) -> bool:
        """
        Evaluate a list of conditions
        Supports AND/OR logic
        """
        return self._evaluate_conditions(conditions, "AND", event_data)

    def _evaluate_conditions(self, conditions: List[Dict], logic: str,
                            data: Dict) -> bool:
        """Internal condition evaluation with AND/OR logic"""
        if not conditions:
            return True

        results = [self._evaluate_condition(cond, data) for cond in conditions]

        if logic.upper() == "AND":
            return all(results)
        elif logic.upper() == "OR":
            return any(results)
        else:
            return True

    def _evaluate_condition(self, condition: Dict, data: Dict) -> bool:
        """Evaluate a single condition"""
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        # Get field value from data
        field_value = self._get_nested_value(data, field)

        # Evaluate based on operator
        try:
            if operator == ConditionOperator.EQUALS.value:
                return field_value == value

            elif operator == ConditionOperator.NOT_EQUALS.value:
                return field_value != value

            elif operator == ConditionOperator.GREATER_THAN.value:
                return field_value > value

            elif operator == ConditionOperator.LESS_THAN.value:
                return field_value < value

            elif operator == ConditionOperator.CONTAINS.value:
                return value in str(field_value)

            elif operator == ConditionOperator.NOT_CONTAINS.value:
                return value not in str(field_value)

            elif operator == ConditionOperator.IN.value:
                return field_value in value if isinstance(value, list) else False

            elif operator == ConditionOperator.NOT_IN.value:
                return field_value not in value if isinstance(value, list) else True

            elif operator == ConditionOperator.EXISTS.value:
                return field_value is not None

            elif operator == ConditionOperator.NOT_EXISTS.value:
                return field_value is None

            elif operator == ConditionOperator.MATCHES_REGEX.value:
                import re
                return bool(re.match(value, str(field_value)))

            else:
                return False

        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        parts = path.split(".")
        value = data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def _check_execution_limit(self, rule: Dict) -> bool:
        """Check if rule has hit execution limit"""
        max_per_day = rule.get("max_executions_per_day")
        
        if max_per_day and rule.get("execution_count_today", 0) >= max_per_day:
            return True

        return False

    async def _execute_rule(self, rule_id: str, event_data: Dict[str, Any]):
        """Execute rule actions"""
        rule = self.rules.get(rule_id)
        if not rule:
            return

        execution_id = str(uuid.uuid4())
        execution = {
            "id": execution_id,
            "rule_id": rule_id,
            "status": "running",
            "start_time": datetime.now(timezone.utc),
            "event_data": event_data,
            "results": [],
            "errors": [],
        }

        self.execution_history[execution_id] = execution

        try:
            # Execute each action
            for action in rule.get("actions", []):
                action_type = action.get("type")
                action_config = action.get("config", {})

                if action_type not in self.action_handlers:
                    logger.warning(f"Unknown action type: {action_type}")
                    execution["errors"].append(f"Unknown action: {action_type}")
                    continue

                try:
                    handler = self.action_handlers[action_type]
                    result = await handler(action_config, event_data)
                    execution["results"].append({
                        "action": action_type,
                        "status": "success",
                        "result": result,
                    })
                except Exception as e:
                    logger.error(f"Action {action_type} failed: {e}")
                    execution["errors"].append(f"{action_type}: {str(e)}")
                    execution["results"].append({
                        "action": action_type,
                        "status": "failed",
                        "error": str(e),
                    })

            # Update rule stats
            rule["total_triggers"] += 1
            rule["last_triggered_at"] = datetime.now(timezone.utc)
            rule["execution_count_today"] += 1

            if execution["errors"]:
                rule["failed_executions"] += 1
                execution["status"] = "failed"
            else:
                rule["successful_executions"] += 1
                execution["status"] = "success"

        except Exception as e:
            execution["status"] = "failed"
            execution["errors"].append(str(e))
            logger.error(f"Rule execution failed: {e}")

        finally:
            execution["end_time"] = datetime.now(timezone.utc)

    def test_rule(self, rule_id: str, test_data: Dict[str, Any]) -> Dict:
        """Test a rule with sample data"""
        rule = self.rules.get(rule_id)
        if not rule:
            return {"success": False, "error": "Rule not found"}

        try:
            # Check conditions
            conditions_pass = self._evaluate_conditions(
                rule.get("conditions", []),
                rule.get("condition_logic", "AND"),
                test_data
            )

            return {
                "success": True,
                "rule_id": rule_id,
                "conditions_pass": conditions_pass,
                "actions_count": len(rule.get("actions", [])),
                "would_trigger": conditions_pass and rule.get("is_enabled", True),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_rule(self, rule_id: str) -> Optional[Dict]:
        """Get a specific rule"""
        return self.rules.get(rule_id)

    def list_rules(self, enabled_only: bool = False) -> List[Dict]:
        """List all rules"""
        rules = list(self.rules.values())
        
        if enabled_only:
            rules = [r for r in rules if r.get("is_enabled")]

        return rules

    def get_rule_history(self, rule_id: str, limit: int = 100) -> List[Dict]:
        """Get execution history for a rule"""
        history = [
            exec_data
            for exec_data in self.execution_history.values()
            if exec_data.get("rule_id") == rule_id
        ]
        return sorted(history, key=lambda x: x.get("start_time"), reverse=True)[:limit]

    def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        """Get status of a specific execution"""
        return self.execution_history.get(execution_id)

    def reset_daily_limits(self):
        """Reset daily execution counters (call once per day)"""
        for rule in self.rules.values():
            rule["execution_count_today"] = 0
