"""
Phase 10: Workflow Execution Engine
DAG-based workflow executor with conditional branching and error handling
"""

import uuid
import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails"""
    pass


class WorkflowExecutionError(Exception):
    """Raised during workflow execution"""
    pass


class WorkflowEngine:
    """
    DAG-based workflow execution engine
    Supports sequential, parallel, and conditional execution
    """

    def __init__(self):
        self.executions = {}  # execution_id -> execution context
        self.action_handlers = {}  # action_type -> handler function

    def register_action(self, action_type: str, handler: callable):
        """Register an action handler"""
        self.action_handlers[action_type] = handler

    def validate_workflow(self, workflow: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate workflow structure
        Returns: (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        if not workflow.get("name"):
            errors.append("Workflow must have a name")

        nodes = workflow.get("nodes", {})
        edges = workflow.get("edges", [])

        if not nodes:
            errors.append("Workflow must have at least one node")

        # Check node structure
        for node_id, node in nodes.items():
            if not node.get("name"):
                errors.append(f"Node {node_id} must have a name")
            if not node.get("type"):
                errors.append(f"Node {node_id} must have a type")

        # Check edges reference valid nodes
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source not in nodes:
                errors.append(f"Edge references non-existent source node: {source}")
            if target not in nodes:
                errors.append(f"Edge references non-existent target node: {target}")

        # Check for cycles
        has_cycle, cycle_path = self._detect_cycle(nodes, edges)
        if has_cycle:
            errors.append(f"Workflow contains cycle: {' -> '.join(cycle_path)}")

        # Check for isolated nodes
        referenced_nodes = set()
        for edge in edges:
            referenced_nodes.add(edge["source"])
            referenced_nodes.add(edge["target"])

        start_nodes = [n for n in nodes.values() if n.get("type") == "start"]
        if not start_nodes:
            errors.append("Workflow must have at least one START node")

        return len(errors) == 0, errors

    def _detect_cycle(self, nodes: Dict, edges: List) -> Tuple[bool, List]:
        """DFS-based cycle detection"""
        # Build adjacency list
        graph = defaultdict(list)
        for edge in edges:
            graph[edge["source"]].append(edge["target"])

        visited = set()
        rec_stack = set()
        path = []

        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for neighbor in graph[node_id]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            path.pop()
            rec_stack.remove(node_id)
            return False

        for node_id in nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True, path

        return False, []

    async def execute_workflow(self, workflow: Dict, input_data: Dict = None, 
                              execution_id: str = None) -> Dict[str, Any]:
        """
        Execute a complete workflow
        Returns execution result with output data
        """
        if not execution_id:
            execution_id = str(uuid.uuid4())

        # Validate workflow
        is_valid, errors = self.validate_workflow(workflow)
        if not is_valid:
            raise WorkflowValidationError(f"Invalid workflow: {', '.join(errors)}")

        # Initialize execution context
        execution_context = {
            "id": execution_id,
            "workflow_id": workflow.get("id"),
            "status": "running",
            "start_time": datetime.now(timezone.utc),
            "input_data": input_data or {},
            "variables": workflow.get("variables", {}).copy(),
            "output_data": {},
            "node_results": {},
            "executed_nodes": set(),
            "failed": False,
            "error": None,
        }

        self.executions[execution_id] = execution_context

        try:
            # Find start node
            nodes = workflow.get("nodes", {})
            edges = workflow.get("edges", [])
            
            start_node_id = next(
                (nid for nid, node in nodes.items() if node.get("type") == "start"),
                None
            )

            if not start_node_id:
                raise WorkflowExecutionError("No START node found")

            # Execute from start node
            await self._execute_from_node(
                start_node_id, nodes, edges, execution_context
            )

            execution_context["status"] = "completed" if not execution_context["failed"] else "failed"

        except Exception as e:
            execution_context["status"] = "failed"
            execution_context["error"] = str(e)
            execution_context["failed"] = True
            logger.error(f"Workflow execution failed: {e}")

        finally:
            execution_context["end_time"] = datetime.now(timezone.utc)
            execution_context["execution_time"] = (
                execution_context["end_time"] - execution_context["start_time"]
            ).total_seconds()

        return execution_context

    async def _execute_from_node(self, node_id: str, nodes: Dict, edges: List,
                                  context: Dict) -> Any:
        """Execute from a specific node and follow execution path"""
        if node_id in context["executed_nodes"]:
            return context["node_results"].get(node_id)

        node = nodes.get(node_id)
        if not node:
            raise WorkflowExecutionError(f"Node not found: {node_id}")

        node_type = node.get("type")

        # Execute node
        start_time = time.time()
        result = None

        try:
            if node_type == "start":
                result = context["input_data"]

            elif node_type == "action":
                result = await self._execute_action(node, context)

            elif node_type == "decision":
                result = self._evaluate_decision(node, context)

            elif node_type == "parallel":
                result = await self._execute_parallel(node, nodes, edges, context)

            elif node_type == "wait":
                await asyncio.sleep(node.get("duration", 1))
                result = {"waited": True}

            elif node_type == "end":
                result = context["variables"]

            # Store result
            execution_time = time.time() - start_time
            context["node_results"][node_id] = result
            context["executed_nodes"].add(node_id)

            logger.info(f"Node {node_id} executed in {execution_time:.2f}s")

            # Follow outgoing edges
            outgoing_edges = [e for e in edges if e.get("source") == node_id]

            if node_type == "decision":
                # Conditional routing
                for edge in outgoing_edges:
                    condition = edge.get("condition")
                    if self._evaluate_condition(condition, result, context):
                        next_node = edge.get("target")
                        await self._execute_from_node(next_node, nodes, edges, context)
                        break

            elif node_type == "parallel":
                # Execute all outgoing nodes in parallel
                next_nodes = [e.get("target") for e in outgoing_edges]
                tasks = [
                    self._execute_from_node(nid, nodes, edges, context)
                    for nid in next_nodes
                ]
                await asyncio.gather(*tasks)

            else:
                # Sequential execution
                if outgoing_edges:
                    next_node = outgoing_edges[0].get("target")
                    await self._execute_from_node(next_node, nodes, edges, context)

        except Exception as e:
            context["failed"] = True
            context["error"] = str(e)
            
            # Handle error node routing if configured
            error_handling = node.get("on_error", "fail")
            logger.error(f"Error in node {node_id}: {e}. Handler: {error_handling}")

            if error_handling == "retry":
                retries = node.get("retry_count", 3)
                for attempt in range(retries):
                    try:
                        await asyncio.sleep(node.get("retry_delay", 1) * (attempt + 1))
                        await self._execute_action(node, context)
                        context["failed"] = False
                        break
                    except Exception:
                        continue

        return result

    async def _execute_action(self, node: Dict, context: Dict) -> Any:
        """Execute an action node"""
        action_type = node.get("action_type")
        
        if action_type not in self.action_handlers:
            raise WorkflowExecutionError(f"Unknown action type: {action_type}")

        handler = self.action_handlers[action_type]
        config = node.get("config", {})
        
        # Map inputs
        mapped_inputs = self._map_inputs(config, node.get("input_mapping", {}), context)

        # Execute handler
        result = await handler(mapped_inputs, context)

        # Map outputs
        return self._map_outputs(result, node.get("output_mapping", {}), context)

    def _evaluate_decision(self, node: Dict, context: Dict) -> Dict:
        """Evaluate decision node condition"""
        condition = node.get("condition")
        result = self._evaluate_condition(condition, None, context)
        return {"decision": result, "condition_result": condition}

    def _evaluate_condition(self, condition: str, value: Any, context: Dict) -> bool:
        """Evaluate a condition expression"""
        if not condition:
            return True

        try:
            # Build evaluation context
            eval_context = {
                "value": value,
                "variables": context.get("variables", {}),
                "output": context.get("node_results", {}),
            }

            # Safe evaluation (limited scope)
            result = eval(condition, {"__builtins__": {}}, eval_context)
            return bool(result)
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False

    async def _execute_parallel(self, node: Dict, nodes: Dict, edges: List,
                                context: Dict) -> Dict:
        """Execute parallel branches"""
        parallel_nodes = node.get("parallel_nodes", [])
        
        tasks = [
            self._execute_from_node(nid, nodes, edges, context)
            for nid in parallel_nodes
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "parallel_results": {
                nid: (results[i] if not isinstance(results[i], Exception) else None)
                for i, nid in enumerate(parallel_nodes)
            },
            "errors": [str(r) for r in results if isinstance(r, Exception)],
        }

    def _map_inputs(self, config: Dict, mapping: Dict, context: Dict) -> Dict:
        """Map workflow variables to action inputs"""
        mapped = config.copy()

        for key, source in mapping.items():
            if isinstance(source, str) and source.startswith("$."):
                # JSONPath reference
                path = source[2:].split(".")
                value = context["node_results"]
                try:
                    for part in path:
                        value = value[part]
                    mapped[key] = value
                except (KeyError, TypeError):
                    pass

        return mapped

    def _map_outputs(self, result: Any, mapping: Dict, context: Dict) -> Dict:
        """Map action outputs to workflow context"""
        if not mapping:
            return result

        mapped = {}
        for key, target in mapping.items():
            if isinstance(target, str) and target.startswith("$."):
                # Store in context
                path = target[2:].split(".")
                self._set_nested(context["variables"], path, result.get(key))
            else:
                mapped[key] = result.get(key)

        return mapped

    @staticmethod
    def _set_nested(obj: Dict, path: List[str], value: Any):
        """Set value in nested dictionary using path"""
        for key in path[:-1]:
            obj = obj.setdefault(key, {})
        obj[path[-1]] = value

    def get_execution_status(self, execution_id: str) -> Dict:
        """Get current execution status"""
        return self.executions.get(execution_id, {})

    def cancel_execution(self, execution_id: str):
        """Cancel an ongoing execution"""
        if execution_id in self.executions:
            self.executions[execution_id]["status"] = "cancelled"

    def get_execution_history(self, workflow_id: str, limit: int = 100) -> List[Dict]:
        """Get recent executions for a workflow"""
        return [
            exec_ctx
            for exec_ctx in self.executions.values()
            if exec_ctx.get("workflow_id") == workflow_id
        ][-limit:]
