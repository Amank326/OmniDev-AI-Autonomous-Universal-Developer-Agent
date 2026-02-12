"""
Task Queue Service for OmniDev AI
Manages agent task queues, scheduling, and execution priorities
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
import json


class TaskStatus(str, Enum):
    """Task lifecycle states"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task execution priority levels"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class TaskType(str, Enum):
    """Task classification types"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DEBUGGING = "debugging"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    INTEGRATION = "integration"
    MONITORING = "monitoring"


@dataclass
class TaskDependency:
    """Represents a task dependency"""
    task_id: str
    required_status: TaskStatus = TaskStatus.COMPLETED
    must_succeed: bool = True


@dataclass
class TaskMetrics:
    """Performance metrics for a task"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time_seconds: float = 0.0
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    retry_count: int = 0
    wait_time_seconds: float = 0.0


@dataclass
class Task:
    """Task object for agent execution"""
    id: str
    name: str
    description: str
    task_type: TaskType
    assigned_agent: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    payload: Dict = field(default_factory=dict)
    dependencies: List[TaskDependency] = field(default_factory=list)
    result: Optional[str] = None
    error: Optional[str] = None
    estimated_duration_seconds: int = 300
    timeout_seconds: int = 3600
    retry_policy: Dict = field(default_factory=lambda: {"max_retries": 3, "backoff_multiplier": 2})
    tags: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metrics: TaskMetrics = field(default_factory=TaskMetrics)
    parent_task_id: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    workspace_id: str = ""
    metadata: Dict = field(default_factory=dict)


class TaskQueueService:
    """Service for managing agent task queues and scheduling"""

    def __init__(self):
        """Initialize task queue service"""
        self.tasks: Dict[str, Task] = {}
        self.agent_queues: Dict[str, List[str]] = {}  # agent_id -> [task_ids]
        self.task_history: List[str] = []
        self.scheduled_tasks: Dict[str, datetime] = {}  # task_id -> scheduled_time
        self.waiting_tasks: Dict[str, List[str]] = {}  # task_id -> [blocked_task_ids]

    def create_task(
        self,
        name: str,
        description: str,
        task_type: TaskType,
        assigned_agent: str,
        payload: Dict,
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[List[TaskDependency]] = None,
        estimated_duration: int = 300,
        timeout: int = 3600,
        retry_policy: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
        created_by: str = "",
        workspace_id: str = "",
        metadata: Optional[Dict] = None,
    ) -> Task:
        """
        Create a new task and add to queue
        
        Args:
            name: Task name
            description: Task description
            task_type: Type of task
            assigned_agent: Agent ID to handle task
            payload: Task data/parameters
            priority: Execution priority (default: MEDIUM)
            dependencies: List of task dependencies
            estimated_duration: Estimated seconds to complete
            timeout: Maximum execution time in seconds
            retry_policy: Retry configuration
            tags: Task tags for categorization
            created_by: User who created task
            workspace_id: Workspace scope
            metadata: Additional metadata
            
        Returns:
            Created Task object
        """
        task_id = str(uuid4())
        
        task = Task(
            id=task_id,
            name=name,
            description=description,
            task_type=task_type,
            assigned_agent=assigned_agent,
            payload=payload,
            priority=priority,
            dependencies=dependencies or [],
            estimated_duration_seconds=estimated_duration,
            timeout_seconds=timeout,
            retry_policy=retry_policy or {"max_retries": 3, "backoff_multiplier": 2},
            tags=tags or [],
            created_by=created_by,
            workspace_id=workspace_id,
            metadata=metadata or {},
        )
        
        self.tasks[task_id] = task
        
        # Add to agent queue if no dependencies
        if not dependencies:
            self._add_to_agent_queue(assigned_agent, task_id)
            task.status = TaskStatus.QUEUED
        else:
            task.status = TaskStatus.BLOCKED
            
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.tasks.get(task_id)

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task current status"""
        task = self.tasks.get(task_id)
        return task.status if task else None

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        Update task status and handle downstream effects
        
        Args:
            task_id: Task ID
            status: New status
            result: Execution result
            error: Error message if failed
            
        Returns:
            True if successful
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        old_status = task.status
        task.status = status
        task.result = result
        task.error = error

        # Update timestamps
        if status == TaskStatus.RUNNING:
            task.started_at = datetime.utcnow()
            task.metrics.start_time = task.started_at
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.utcnow()
            task.metrics.end_time = task.completed_at
            if task.metrics.start_time:
                task.metrics.execution_time_seconds = (
                    task.completed_at - task.metrics.start_time
                ).total_seconds()
            self.task_history.append(task_id)

        # Handle dependent tasks when this task completes successfully
        if status == TaskStatus.COMPLETED:
            self._unblock_dependent_tasks(task_id)

        return True

    def _add_to_agent_queue(self, agent_id: str, task_id: str) -> None:
        """Add task to agent's queue"""
        if agent_id not in self.agent_queues:
            self.agent_queues[agent_id] = []
        self.agent_queues[agent_id].append(task_id)

    def get_agent_queue(self, agent_id: str) -> List[Task]:
        """Get all tasks in agent's queue, sorted by priority"""
        if agent_id not in self.agent_queues:
            return []

        task_ids = self.agent_queues[agent_id]
        tasks = [self.tasks[tid] for tid in task_ids if tid in self.tasks]

        # Sort by priority (high to low), then by creation time
        return sorted(
            tasks,
            key=lambda t: (-t.priority.value, t.created_at),
        )

    def get_next_task_for_agent(self, agent_id: str) -> Optional[Task]:
        """Get the next task to execute for an agent"""
        queue = self.get_agent_queue(agent_id)
        
        for task in queue:
            if task.status == TaskStatus.QUEUED:
                return task
            
        return None

    def pop_next_task(self, agent_id: str) -> Optional[Task]:
        """
        Remove and return next queued task for agent
        """
        task = self.get_next_task_for_agent(agent_id)
        if task and agent_id in self.agent_queues:
            self.agent_queues[agent_id].remove(task.id)
        return task

    def schedule_task(
        self,
        task_id: str,
        scheduled_time: datetime,
    ) -> bool:
        """
        Schedule task for future execution
        
        Args:
            task_id: Task ID
            scheduled_time: When to execute
            
        Returns:
            True if successful
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.scheduled_at = scheduled_time
        task.status = TaskStatus.SCHEDULED
        self.scheduled_tasks[task_id] = scheduled_time

        return True

    def get_scheduled_tasks(self) -> List[Task]:
        """Get all scheduled tasks sorted by scheduled time"""
        scheduled_task_ids = [
            tid for tid, scheduled_time in self.scheduled_tasks.items()
            if scheduled_time <= datetime.utcnow()
        ]
        
        tasks = [self.tasks[tid] for tid in scheduled_task_ids if tid in self.tasks]
        return sorted(tasks, key=lambda t: t.scheduled_at or t.created_at)

    def activate_scheduled_tasks(self) -> List[Task]:
        """Move due scheduled tasks to ready queues"""
        activated = []
        due_tasks = self.get_scheduled_tasks()

        for task in due_tasks:
            # Check dependencies
            if self._dependencies_met(task):
                self._add_to_agent_queue(task.assigned_agent, task.id)
                task.status = TaskStatus.QUEUED
                activated.append(task)
            else:
                task.status = TaskStatus.BLOCKED

        return activated

    def _dependencies_met(self, task: Task) -> bool:
        """Check if all dependencies are satisfied"""
        if not task.dependencies:
            return True

        for dep in task.dependencies:
            dep_task = self.tasks.get(dep.task_id)
            if not dep_task:
                return False

            if dep.required_status == TaskStatus.COMPLETED:
                if dep_task.status != TaskStatus.COMPLETED:
                    return not dep.must_succeed
            elif dep_task.status != dep.required_status:
                if dep.must_succeed:
                    return False

        return True

    def _unblock_dependent_tasks(self, completed_task_id: str) -> List[Task]:
        """Unblock tasks that depend on this completed task"""
        unblocked = []

        for task in self.tasks.values():
            if task.status == TaskStatus.BLOCKED:
                for dep in task.dependencies:
                    if dep.task_id == completed_task_id:
                        if self._dependencies_met(task):
                            self._add_to_agent_queue(task.assigned_agent, task.id)
                            task.status = TaskStatus.QUEUED
                            unblocked.append(task)

        return unblocked

    def pause_task(self, task_id: str) -> bool:
        """Pause a running task"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.RUNNING:
            task.status = TaskStatus.PAUSED
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PAUSED:
            task.status = TaskStatus.RUNNING
            return True
        return False

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        task = self.tasks.get(task_id)
        if task and task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            self.task_history.append(task_id)
            return True
        return False

    def retry_task(self, task_id: str) -> bool:
        """Retry a failed task"""
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.FAILED:
            return False

        max_retries = task.retry_policy.get("max_retries", 3)
        if task.metrics.retry_count >= max_retries:
            return False

        task.metrics.retry_count += 1
        task.status = TaskStatus.RETRYING
        task.error = None
        task.result = None

        # Re-queue after backoff
        backoff = task.retry_policy.get("backoff_multiplier", 2)
        wait_seconds = (backoff ** (task.metrics.retry_count - 1)) * 5
        self.schedule_task(task_id, datetime.utcnow() + timedelta(seconds=wait_seconds))

        return True

    def get_task_dependencies(self, task_id: str) -> List[Task]:
        """Get all dependencies for a task"""
        task = self.tasks.get(task_id)
        if not task:
            return []

        dependencies = []
        for dep in task.dependencies:
            dep_task = self.tasks.get(dep.task_id)
            if dep_task:
                dependencies.append(dep_task)

        return dependencies

    def get_dependent_tasks(self, task_id: str) -> List[Task]:
        """Get all tasks that depend on this task"""
        dependents = []
        for task in self.tasks.values():
            for dep in task.dependencies:
                if dep.task_id == task_id:
                    dependents.append(task)

        return dependents

    def get_task_subtasks(self, task_id: str) -> List[Task]:
        """Get all subtasks for a parent task"""
        task = self.tasks.get(task_id)
        if not task:
            return []

        subtasks = [self.tasks[sid] for sid in task.subtasks if sid in self.tasks]
        return subtasks

    def add_subtask(
        self,
        parent_task_id: str,
        subtask_id: str,
    ) -> bool:
        """Add a subtask to parent task"""
        parent = self.tasks.get(parent_task_id)
        subtask = self.tasks.get(subtask_id)

        if parent and subtask:
            parent.subtasks.append(subtask_id)
            subtask.parent_task_id = parent_task_id
            return True

        return False

    def get_queue_stats(self, agent_id: Optional[str] = None) -> Dict:
        """Get queue statistics"""
        if agent_id:
            queue_tasks = self.get_agent_queue(agent_id)
            return {
                "agent_id": agent_id,
                "total_tasks": len(queue_tasks),
                "pending": len([t for t in queue_tasks if t.status == TaskStatus.PENDING]),
                "queued": len([t for t in queue_tasks if t.status == TaskStatus.QUEUED]),
                "running": len([t for t in queue_tasks if t.status == TaskStatus.RUNNING]),
                "blocked": len([t for t in queue_tasks if t.status == TaskStatus.BLOCKED]),
                "completed": len([t for t in queue_tasks if t.status == TaskStatus.COMPLETED]),
                "failed": len([t for t in queue_tasks if t.status == TaskStatus.FAILED]),
                "avg_wait_time": self._calculate_avg_wait_time(queue_tasks),
            }
        else:
            stats = {
                "total_tasks": len(self.tasks),
                "total_agents": len(self.agent_queues),
                "pending": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
                "queued": len([t for t in self.tasks.values() if t.status == TaskStatus.QUEUED]),
                "running": len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]),
                "blocked": len([t for t in self.tasks.values() if t.status == TaskStatus.BLOCKED]),
                "completed": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
                "failed": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
                "scheduled": len(self.scheduled_tasks),
                "agent_stats": {
                    agent_id: len(self.agent_queues.get(agent_id, []))
                    for agent_id in self.agent_queues
                },
            }
            return stats

    def _calculate_avg_wait_time(self, tasks: List[Task]) -> float:
        """Calculate average wait time"""
        wait_times = [
            t.metrics.wait_time_seconds for t in tasks
            if t.metrics.wait_time_seconds > 0
        ]
        return sum(wait_times) / len(wait_times) if wait_times else 0.0

    def cleanup_completed_tasks(self, age_hours: int = 24) -> int:
        """Remove completed/failed tasks older than specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=age_hours)
        removed_ids = []

        for task_id, task in list(self.tasks.items()):
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                and task.completed_at
                and task.completed_at < cutoff_time):
                del self.tasks[task_id]
                removed_ids.append(task_id)

        return len(removed_ids)

    def get_all_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[Task]:
        """Get all tasks, optionally filtered by status"""
        tasks = list(self.tasks.values())
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def search_tasks(self, query: str, workspace_id: Optional[str] = None) -> List[Task]:
        """Search tasks by name, description, or tags"""
        query_lower = query.lower()
        results = []

        for task in self.tasks.values():
            if workspace_id and task.workspace_id != workspace_id:
                continue

            if (query_lower in task.name.lower()
                or query_lower in task.description.lower()
                or any(query_lower in tag.lower() for tag in task.tags)):
                results.append(task)

        return sorted(results, key=lambda t: t.created_at, reverse=True)

    def export_task_history(self, agent_id: Optional[str] = None, hours: int = 24) -> List[Dict]:
        """Export task history for analysis"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        history = []

        for task_id in self.task_history:
            task = self.tasks.get(task_id)
            if task and task.completed_at and task.completed_at >= cutoff_time:
                if agent_id is None or task.assigned_agent == agent_id:
                    history.append(asdict(task))

        return history
