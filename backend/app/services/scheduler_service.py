"""
Phase 10: Task Scheduler Service
Cron-based task scheduling with timezone support
"""

import uuid
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from croniter import croniter

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Cron-based task scheduler
    Manages scheduled task execution with retry logic
    """

    def __init__(self):
        self.tasks = {}  # task_id -> task definition
        self.executions = {}  # execution_id -> execution data
        self.job_queue = asyncio.Queue()
        self.action_handlers = {}  # action_type -> handler

    def register_action(self, action_type: str, handler: Callable):
        """Register an action handler"""
        self.action_handlers[action_type] = handler

    def schedule_task(self, task_config: Dict[str, Any]) -> str:
        """Create a scheduled task"""
        task_id = str(uuid.uuid4())

        # Validate cron expression
        try:
            croniter(task_config.get("cron_expression", "0 0 * * *"))
        except Exception as e:
            logger.error(f"Invalid cron expression: {e}")
            raise ValueError(f"Invalid cron expression: {e}")

        task = {
            "id": task_id,
            "name": task_config.get("name", "Unnamed Task"),
            "description": task_config.get("description"),
            "is_enabled": task_config.get("is_enabled", True),
            "cron_expression": task_config.get("cron_expression"),
            "timezone": task_config.get("timezone", "UTC"),
            "workflow_id": task_config.get("workflow_id"),
            "task_config": task_config.get("task_config", {}),
            "max_retries": task_config.get("max_retries", 3),
            "retry_delay": task_config.get("retry_delay", 300),
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time": 0.0,
            "last_execution": None,
            "next_execution": self._calculate_next_execution(
                task_config.get("cron_expression"),
                task_config.get("timezone", "UTC")
            ),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        self.tasks[task_id] = task
        logger.info(f"Created scheduled task: {task_id} - {task['name']}")
        return task_id

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a scheduled task"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        # Validate cron if changed
        if "cron_expression" in updates:
            try:
                croniter(updates["cron_expression"])
            except Exception as e:
                logger.error(f"Invalid cron expression: {e}")
                return False

        task.update(updates)
        task["updated_at"] = datetime.now(timezone.utc)
        
        # Recalculate next execution
        if "cron_expression" in updates or "timezone" in updates:
            task["next_execution"] = self._calculate_next_execution(
                task["cron_expression"],
                task["timezone"]
            )

        logger.info(f"Updated task: {task_id}")
        return True

    def delete_task(self, task_id: str) -> bool:
        """Delete a scheduled task"""
        if task_id not in self.tasks:
            return False

        del self.tasks[task_id]
        logger.info(f"Deleted task: {task_id}")
        return True

    def enable_task(self, task_id: str) -> bool:
        """Enable a task"""
        if task_id in self.tasks:
            self.tasks[task_id]["is_enabled"] = True
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """Disable a task"""
        if task_id in self.tasks:
            self.tasks[task_id]["is_enabled"] = False
            return True
        return False

    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a scheduled task"""
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}

        if not task["is_enabled"]:
            return {"success": False, "error": "Task is disabled"}

        execution_id = str(uuid.uuid4())
        execution = {
            "id": execution_id,
            "task_id": task_id,
            "status": "running",
            "start_time": datetime.now(timezone.utc),
            "result": None,
            "error": None,
            "retries": 0,
        }

        self.executions[execution_id] = execution

        try:
            # Execute with retry logic
            max_retries = task.get("max_retries", 3)
            retry_delay = task.get("retry_delay", 300)
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    logger.info(f"Executing task {task_id} (attempt {attempt + 1}/{max_retries + 1})")

                    # Execute workflow if configured
                    if task.get("workflow_id"):
                        result = await self._execute_workflow(task)
                    else:
                        result = await self._execute_action(task)

                    execution["status"] = "success"
                    execution["result"] = result
                    task["successful_executions"] += 1
                    break

                except Exception as e:
                    last_error = str(e)
                    logger.error(f"Task execution failed (attempt {attempt + 1}): {e}")
                    
                    if attempt < max_retries:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        execution["retries"] = attempt + 1
                    else:
                        execution["status"] = "failed"
                        execution["error"] = last_error
                        task["failed_executions"] += 1

        except Exception as e:
            execution["status"] = "failed"
            execution["error"] = str(e)
            task["failed_executions"] += 1
            logger.error(f"Task {task_id} execution failed: {e}")

        finally:
            execution["end_time"] = datetime.now(timezone.utc)
            execution_time = (
                execution["end_time"] - execution["start_time"]
            ).total_seconds()

            # Update task stats
            task["total_executions"] += 1
            task["last_execution"] = execution["end_time"]
            
            # Update average execution time
            avg = task.get("avg_execution_time", 0.0)
            count = task["total_executions"]
            task["avg_execution_time"] = (avg * (count - 1) + execution_time) / count

            # Schedule next execution
            task["next_execution"] = self._calculate_next_execution(
                task["cron_expression"],
                task["timezone"]
            )

        return execution

    async def _execute_workflow(self, task: Dict) -> Dict:
        """Execute a workflow-based task"""
        # This would integrate with the workflow engine
        return {
            "type": "workflow",
            "workflow_id": task.get("workflow_id"),
            "status": "executed",
        }

    async def _execute_action(self, task: Dict) -> Dict:
        """Execute an action-based task"""
        task_config = task.get("task_config", {})
        action_type = task_config.get("action_type")

        if action_type not in self.action_handlers:
            raise ValueError(f"Unknown action type: {action_type}")

        handler = self.action_handlers[action_type]
        return await handler(task_config)

    def _calculate_next_execution(self, cron_expr: str, tz: str) -> datetime:
        """Calculate next execution time"""
        try:
            # Create cron iterator from now
            now = datetime.now(timezone.utc)
            cron = croniter(cron_expr, now)
            next_run = cron.get_next(datetime)
            return next_run
        except Exception as e:
            logger.error(f"Error calculating next execution: {e}")
            return now + timedelta(hours=1)

    async def check_due_tasks(self) -> List[str]:
        """Check for tasks that are due to execute"""
        now = datetime.now(timezone.utc)
        due_tasks = []

        for task_id, task in self.tasks.items():
            if not task["is_enabled"]:
                continue

            next_exec = task.get("next_execution")
            if next_exec and next_exec <= now:
                due_tasks.append(task_id)
                # Execute task asynchronously
                asyncio.create_task(self.execute_task(task_id))

        return due_tasks

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a specific task"""
        return self.tasks.get(task_id)

    def list_tasks(self, enabled_only: bool = False) -> List[Dict]:
        """List all tasks"""
        tasks = list(self.tasks.values())
        
        if enabled_only:
            tasks = [t for t in tasks if t.get("is_enabled")]

        return sorted(tasks, key=lambda x: x.get("next_execution") or datetime.max)

    def get_task_executions(self, task_id: str, limit: int = 100) -> List[Dict]:
        """Get execution history for a task"""
        executions = [
            exec_data
            for exec_data in self.executions.values()
            if exec_data.get("task_id") == task_id
        ]
        return sorted(executions, key=lambda x: x.get("start_time"), reverse=True)[:limit]

    def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        """Get status of a specific execution"""
        return self.executions.get(execution_id)

    def get_upcoming_tasks(self, hours: int = 24) -> List[Dict]:
        """Get tasks scheduled to run in the next N hours"""
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=hours)

        upcoming = [
            task
            for task in self.tasks.values()
            if task.get("is_enabled") and task.get("next_execution")
            and now <= task["next_execution"] <= future
        ]

        return sorted(upcoming, key=lambda x: x.get("next_execution"))

    def get_performance_stats(self) -> Dict:
        """Get overall scheduler performance statistics"""
        total_tasks = len(self.tasks)
        enabled_tasks = sum(1 for t in self.tasks.values() if t.get("is_enabled"))
        
        total_executions = sum(t.get("total_executions", 0) for t in self.tasks.values())
        total_successful = sum(t.get("successful_executions", 0) for t in self.tasks.values())
        total_failed = sum(t.get("failed_executions", 0) for t in self.tasks.values())

        success_rate = (
            (total_successful / total_executions * 100)
            if total_executions > 0
            else 0.0
        )

        avg_execution_time = (
            sum(t.get("avg_execution_time", 0) for t in self.tasks.values()) / total_tasks
            if total_tasks > 0
            else 0.0
        )

        return {
            "total_tasks": total_tasks,
            "enabled_tasks": enabled_tasks,
            "total_executions": total_executions,
            "successful_executions": total_successful,
            "failed_executions": total_failed,
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
        }
