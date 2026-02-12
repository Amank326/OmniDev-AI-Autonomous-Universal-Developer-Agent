"""
Workflow Automation Service - Task scheduling and execution
Manages complex workflows, dependencies, and scheduled task execution
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
import json


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Individual task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowAutomationService:
    """
    Service for automating complex workflows with task scheduling,
    dependency management, and execution orchestration.
    """
    
    def __init__(self):
        """Initialize workflow automation service"""
        self.workflows = {}
        self.tasks = {}
        self.execution_history = {}
        self.scheduled_executions = {}
        self.workflow_counter = 0
        self.task_counter = 0
    
    def create_workflow(
        self,
        workflow_name: str,
        description: str,
        owner_id: str,
        tasks: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Create a new workflow with optional initial tasks.
        
        Args:
            workflow_name: Name of workflow
            description: Description
            owner_id: Owner/creator ID
            tasks: Optional list of initial tasks
        
        Returns:
            Created workflow
        """
        workflow_id = f"wf_{self.workflow_counter}"
        self.workflow_counter += 1
        
        workflow = {
            "workflow_id": workflow_id,
            "name": workflow_name,
            "description": description,
            "owner_id": owner_id,
            "status": WorkflowStatus.DRAFT.value,
            "tasks": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "executions": [],
            "total_executions": 0,
            "success_rate": 0,
        }
        
        self.workflows[workflow_id] = workflow
        
        # Add initial tasks if provided
        if tasks:
            for task in tasks:
                self.add_task_to_workflow(
                    workflow_id,
                    task.get("name"),
                    task.get("description", ""),
                    task.get("action"),
                    task.get("parameters", {}),
                    task.get("dependencies", []),
                )
        
        return workflow
    
    def add_task_to_workflow(
        self,
        workflow_id: str,
        task_name: str,
        description: str,
        action: str,
        parameters: Dict,
        dependencies: Optional[List[str]] = None,
    ) -> Dict:
        """
        Add a task to a workflow.
        
        Args:
            workflow_id: Workflow ID
            task_name: Task name
            description: Task description
            action: Action type (e.g., 'send_invoice', 'apply_discount')
            parameters: Task parameters
            dependencies: List of task IDs this depends on
        
        Returns:
            Created task
        """
        task_id = f"task_{self.task_counter}"
        self.task_counter += 1
        
        task = {
            "task_id": task_id,
            "workflow_id": workflow_id,
            "name": task_name,
            "description": description,
            "action": action,
            "parameters": parameters,
            "dependencies": dependencies or [],
            "status": TaskStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "last_executed": None,
            "execution_count": 0,
            "error_count": 0,
            "retry_count": 0,
        }
        
        self.tasks[task_id] = task
        self.workflows[workflow_id]["tasks"].append(task_id)
        
        return task
    
    def schedule_workflow(
        self,
        workflow_id: str,
        trigger_type: str,
        trigger_config: Dict,
        enabled: bool = True,
    ) -> Dict:
        """
        Schedule a workflow to run automatically.
        
        Args:
            workflow_id: Workflow ID
            trigger_type: 'cron', 'event', 'interval', 'webhook'
            trigger_config: Configuration for trigger type
            enabled: Whether schedule is active
        
        Returns:
            Schedule configuration
        """
        schedule = {
            "workflow_id": workflow_id,
            "trigger_type": trigger_type,
            "trigger_config": trigger_config,
            "enabled": enabled,
            "created_at": datetime.utcnow().isoformat(),
            "last_triggered": None,
            "next_run": self._calculate_next_run(trigger_type, trigger_config),
            "run_count": 0,
        }
        
        self.scheduled_executions[workflow_id] = schedule
        self.workflows[workflow_id]["status"] = WorkflowStatus.SCHEDULED.value
        
        return schedule
    
    def _calculate_next_run(self, trigger_type: str, config: Dict) -> str:
        """Calculate next scheduled run time"""
        if trigger_type == "interval":
            interval_minutes = config.get("interval_minutes", 60)
            next_run = datetime.utcnow() + timedelta(minutes=interval_minutes)
        elif trigger_type == "daily":
            hour = config.get("hour", 0)
            next_run = datetime.utcnow().replace(hour=hour, minute=0, second=0)
            if next_run <= datetime.utcnow():
                next_run += timedelta(days=1)
        else:
            next_run = datetime.utcnow() + timedelta(hours=1)
        
        return next_run.isoformat()
    
    def execute_workflow(
        self,
        workflow_id: str,
        context: Dict,
        dry_run: bool = False,
    ) -> Dict:
        """
        Execute a workflow with given context.
        Respects task dependencies and handles failures.
        
        Args:
            workflow_id: Workflow ID
            context: Execution context (data, parameters)
            dry_run: If True, simulate without side effects
        
        Returns:
            Execution result with task results
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"status": "error", "message": "Workflow not found"}
        
        execution_id = f"exec_{datetime.utcnow().timestamp()}"
        task_results = {}
        execution_status = "success"
        
        workflow["status"] = WorkflowStatus.RUNNING.value
        
        # Topologically sort tasks by dependencies
        task_order = self._topological_sort_tasks(workflow_id)
        
        # Execute tasks in order
        for task_id in task_order:
            task = self.tasks[task_id]
            
            # Check if dependencies succeeded
            dependencies_met = all(
                task_results.get(dep, {}).get("status") == "success"
                for dep in task["dependencies"]
            )
            
            if not dependencies_met:
                task_results[task_id] = {
                    "task_id": task_id,
                    "status": "skipped",
                    "reason": "Dependencies not met",
                }
                continue
            
            # Execute task
            result = self._execute_task(
                task,
                context,
                dry_run=dry_run,
            )
            
            task_results[task_id] = result
            
            # Update task status
            task["status"] = TaskStatus.COMPLETED.value if result["status"] == "success" else TaskStatus.FAILED.value
            task["last_executed"] = datetime.utcnow().isoformat()
            task["execution_count"] += 1
            
            if result["status"] != "success":
                execution_status = "failed"
                if task.get("fail_workflow", False):
                    break  # Stop if task is critical
        
        # Record execution
        execution = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": execution_status,
            "task_results": task_results,
            "executed_at": datetime.utcnow().isoformat(),
            "dry_run": dry_run,
            "context": context,
        }
        
        if workflow_id not in self.execution_history:
            self.execution_history[workflow_id] = []
        
        self.execution_history[workflow_id].append(execution)
        
        # Update workflow stats
        workflow["status"] = (
            WorkflowStatus.COMPLETED.value if execution_status == "success"
            else WorkflowStatus.FAILED.value
        )
        workflow["total_executions"] += 1
        workflow["executions"].append(execution_id)
        
        # Calculate success rate
        successes = sum(
            1 for exec in self.execution_history[workflow_id]
            if exec["status"] == "success"
        )
        workflow["success_rate"] = (successes / len(self.execution_history[workflow_id])) * 100
        
        return execution
    
    def _topological_sort_tasks(self, workflow_id: str) -> List[str]:
        """Sort tasks by dependencies (topological sort)"""
        task_ids = self.workflows[workflow_id]["tasks"]
        
        # Build dependency graph
        visited = set()
        result = []
        
        def visit(task_id):
            if task_id in visited:
                return
            visited.add(task_id)
            
            task = self.tasks[task_id]
            for dep in task.get("dependencies", []):
                if dep in task_ids:
                    visit(dep)
            
            result.append(task_id)
        
        for task_id in task_ids:
            visit(task_id)
        
        return result
    
    def _execute_task(
        self,
        task: Dict,
        context: Dict,
        dry_run: bool = False,
    ) -> Dict:
        """Execute individual task"""
        try:
            action = task["action"]
            parameters = {**task["parameters"], **context}
            
            # Simulate task execution
            if dry_run:
                return {
                    "task_id": task["task_id"],
                    "status": "success",
                    "result": f"[DRY RUN] Would execute {action}",
                    "executed_at": datetime.utcnow().isoformat(),
                }
            
            # Execute based on action type
            if action == "send_invoice":
                return self._task_send_invoice(parameters)
            elif action == "apply_discount":
                return self._task_apply_discount(parameters)
            elif action == "send_notification":
                return self._task_send_notification(parameters)
            elif action == "update_status":
                return self._task_update_status(parameters)
            else:
                return self._task_custom_action(action, parameters)
        
        except Exception as e:
            return {
                "task_id": task["task_id"],
                "status": "failed",
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat(),
            }
    
    def _task_send_invoice(self, params: Dict) -> Dict:
        """Task: send invoice"""
        return {
            "status": "success",
            "result": f"Invoice sent to customer {params.get('customer_id')}",
            "action": "send_invoice",
        }
    
    def _task_apply_discount(self, params: Dict) -> Dict:
        """Task: apply discount"""
        return {
            "status": "success",
            "result": f"Discount {params.get('amount')} applied",
            "action": "apply_discount",
        }
    
    def _task_send_notification(self, params: Dict) -> Dict:
        """Task: send notification"""
        return {
            "status": "success",
            "result": f"Notification sent to {params.get('recipient')}",
            "action": "send_notification",
        }
    
    def _task_update_status(self, params: Dict) -> Dict:
        """Task: update status"""
        return {
            "status": "success",
            "result": f"Status updated to {params.get('new_status')}",
            "action": "update_status",
        }
    
    def _task_custom_action(self, action: str, params: Dict) -> Dict:
        """Task: custom action"""
        return {
            "status": "success",
            "result": f"Custom action '{action}' completed",
            "action": action,
        }
    
    def pause_workflow(self, workflow_id: str) -> Dict:
        """Pause a running workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"status": "error"}
        
        workflow["status"] = WorkflowStatus.PAUSED.value
        return {"workflow_id": workflow_id, "status": "paused"}
    
    def resume_workflow(self, workflow_id: str) -> Dict:
        """Resume a paused workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"status": "error"}
        
        workflow["status"] = WorkflowStatus.SCHEDULED.value
        return {"workflow_id": workflow_id, "status": "resumed"}
    
    def get_workflow_status(self, workflow_id: str) -> Dict:
        """Get current workflow status and metrics"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {}
        
        return {
            "workflow_id": workflow_id,
            "name": workflow["name"],
            "status": workflow["status"],
            "task_count": len(workflow["tasks"]),
            "total_executions": workflow["total_executions"],
            "success_rate": round(workflow["success_rate"], 1),
            "last_execution": (
                workflow["executions"][-1] if workflow["executions"] else None
            ),
            "created_at": workflow["created_at"],
        }
    
    def get_execution_history(
        self,
        workflow_id: str,
        limit: int = 10,
    ) -> List[Dict]:
        """Get execution history for a workflow"""
        history = self.execution_history.get(workflow_id, [])
        return history[-limit:]
    
    def retry_failed_tasks(
        self,
        workflow_id: str,
        execution_id: str,
        context: Dict,
    ) -> Dict:
        """Retry only failed tasks from a previous execution"""
        executions = self.execution_history.get(workflow_id, [])
        target_execution = next(
            (e for e in executions if e["execution_id"] == execution_id),
            None,
        )
        
        if not target_execution:
            return {"status": "error", "message": "Execution not found"}
        
        # Get failed task IDs
        failed_tasks = [
            task_id for task_id, result in target_execution["task_results"].items()
            if result.get("status") == "failed"
        ]
        
        if not failed_tasks:
            return {"status": "success", "message": "No failed tasks to retry"}
        
        # Re-execute failed tasks
        retry_results = {}
        for task_id in failed_tasks:
            task = self.tasks[task_id]
            result = self._execute_task(task, context)
            retry_results[task_id] = result
            task["retry_count"] += 1
        
        return {
            "workflow_id": workflow_id,
            "original_execution": execution_id,
            "retried_tasks": len(failed_tasks),
            "results": retry_results,
        }
