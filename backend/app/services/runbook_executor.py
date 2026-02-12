"""
Runbook Executor Service
Automated remediation and response execution
Phase 43: Advanced Analytics & ML Features
"""

import json
import threading
import subprocess
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from uuid import uuid4


class StepType(Enum):
    """Types of runbook steps"""
    WEBHOOK = "webhook"
    COMMAND = "command"
    SCRIPT = "script"
    HTTP = "http"
    EMAIL = "email"
    SLACK = "slack"
    CONDITIONAL = "conditional"
    WAIT = "wait"
    NOTIFICATION = "notification"


class ExecutionStatus(Enum):
    """Execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class RunbookStatus(Enum):
    """Runbook status"""
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


@dataclass
class RunbookStep:
    """Individual step in a runbook"""
    id: str
    order: int
    name: str
    step_type: StepType
    config: Dict[str, Any]
    description: str = ""
    timeout_seconds: int = 300
    retry_count: int = 0
    skip_on_error: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "order": self.order,
            "name": self.name,
            "step_type": self.step_type.value,
            "description": self.description,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "skip_on_error": self.skip_on_error,
        }


@dataclass
class StepExecution:
    """Execution of a single step"""
    id: str
    step_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    output: str = ""
    error: str = ""
    duration_seconds: float = 0.0
    retry_attempt: int = 0

    def to_dict(self):
        return {
            "id": self.id,
            "step_id": self.step_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "retry_attempt": self.retry_attempt,
        }


@dataclass
class RunbookExecution:
    """Execution instance of a runbook"""
    id: str
    runbook_id: str
    triggered_by: str
    trigger_source: str  # "alert", "manual", "schedule"
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    step_executions: List[StepExecution] = field(default_factory=list)
    duration_seconds: float = 0.0
    error_message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id,
            "runbook_id": self.runbook_id,
            "triggered_by": self.triggered_by,
            "trigger_source": self.trigger_source,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "step_count": len(self.step_executions),
        }


@dataclass
class Runbook:
    """Automated remediation runbook"""
    id: str
    name: str
    description: str
    status: RunbookStatus
    alert_matcher: Dict[str, str]  # Match on alert properties
    steps: List[RunbookStep]
    created_by: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    execution_count: int = 0
    last_execution_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "execution_count": self.execution_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class RunbookExecutor:
    """Executes automated runbooks"""

    def __init__(self):
        self.runbooks: Dict[str, Runbook] = {}
        self.executions: Dict[str, RunbookExecution] = {}
        self.execution_history: List[RunbookExecution] = []
        self.callbacks: List[Callable] = []
        self.lock = threading.RLock()

    def create_runbook(
        self, name: str, description: str, alert_matcher: Dict[str, str], created_by: str
    ) -> Runbook:
        """Create new runbook"""
        with self.lock:
            runbook_id = f"runbook_{uuid4().hex[:8]}"

            runbook = Runbook(
                id=runbook_id,
                name=name,
                description=description,
                status=RunbookStatus.DRAFT,
                alert_matcher=alert_matcher,
                steps=[],
                created_by=created_by,
            )

            self.runbooks[runbook_id] = runbook

            self._notify_callbacks({
                "event": "runbook_created",
                "runbook_id": runbook_id,
                "name": name,
            })

            return runbook

    def add_step(
        self,
        runbook_id: str,
        name: str,
        step_type: StepType,
        config: Dict[str, Any],
        description: str = "",
        timeout_seconds: int = 300,
    ) -> Optional[RunbookStep]:
        """Add step to runbook"""
        with self.lock:
            runbook = self.runbooks.get(runbook_id)
            if not runbook or runbook.status == RunbookStatus.PUBLISHED:
                return None

            step_id = f"step_{uuid4().hex[:8]}"
            order = len(runbook.steps) + 1

            step = RunbookStep(
                id=step_id,
                order=order,
                name=name,
                step_type=step_type,
                config=config,
                description=description,
                timeout_seconds=timeout_seconds,
            )

            runbook.steps.append(step)
            runbook.updated_at = datetime.now()

            return step

    def publish_runbook(self, runbook_id: str) -> bool:
        """Publish runbook for use"""
        with self.lock:
            runbook = self.runbooks.get(runbook_id)
            if not runbook or not runbook.steps:
                return False

            runbook.status = RunbookStatus.PUBLISHED
            runbook.updated_at = datetime.now()

            self._notify_callbacks({
                "event": "runbook_published",
                "runbook_id": runbook_id,
            })

            return True

    def find_applicable_runbooks(self, alert: Dict[str, Any]) -> List[Runbook]:
        """Find runbooks matching alert"""
        with self.lock:
            applicable = []

            for runbook in self.runbooks.values():
                if runbook.status != RunbookStatus.PUBLISHED:
                    continue

                # Check if alert matches
                if self._matches_alert(runbook.alert_matcher, alert):
                    applicable.append(runbook)

            return applicable

    def _matches_alert(self, matcher: Dict[str, str], alert: Dict[str, Any]) -> bool:
        """Check if alert matches runbook matcher"""
        for key, value in matcher.items():
            if key not in alert or str(alert[key]) != value:
                return False
        return True

    def execute_runbook(
        self,
        runbook_id: str,
        triggered_by: str,
        trigger_source: str = "alert",
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[RunbookExecution]:
        """Execute a runbook"""
        with self.lock:
            runbook = self.runbooks.get(runbook_id)
            if not runbook or runbook.status != RunbookStatus.PUBLISHED:
                return None

            execution_id = f"exec_{uuid4().hex[:8]}"

            execution = RunbookExecution(
                id=execution_id,
                runbook_id=runbook_id,
                triggered_by=triggered_by,
                trigger_source=trigger_source,
                status=ExecutionStatus.RUNNING,
                started_at=datetime.now(),
                context=context or {},
            )

            self.executions[execution_id] = execution

            # Run in background thread
            thread = threading.Thread(
                target=self._execute_runbook_steps,
                args=(execution, runbook),
                daemon=True,
            )
            thread.start()

            self._notify_callbacks({
                "event": "runbook_execution_started",
                "execution_id": execution_id,
                "runbook_id": runbook_id,
            })

            return execution

    def _execute_runbook_steps(self, execution: RunbookExecution, runbook: Runbook) -> None:
        """Execute runbook steps"""
        try:
            for step in runbook.steps:
                # Execute step
                step_exec = StepExecution(
                    id=f"step_exec_{uuid4().hex[:8]}",
                    step_id=step.id,
                    status=ExecutionStatus.RUNNING,
                    started_at=datetime.now(),
                )

                execution.step_executions.append(step_exec)

                try:
                    if step.step_type == StepType.WEBHOOK:
                        self._execute_webhook(step, step_exec)
                    elif step.step_type == StepType.COMMAND:
                        self._execute_command(step, step_exec)
                    elif step.step_type == StepType.HTTP:
                        self._execute_http(step, step_exec)
                    elif step.step_type == StepType.SLACK:
                        self._execute_slack(step, step_exec)
                    elif step.step_type == StepType.WAIT:
                        self._execute_wait(step, step_exec)
                    else:
                        step_exec.status = ExecutionStatus.SKIPPED

                    if step_exec.status == ExecutionStatus.FAILED and not step.skip_on_error:
                        break

                except Exception as e:
                    step_exec.status = ExecutionStatus.FAILED
                    step_exec.error = str(e)

                    if not step.skip_on_error:
                        break

                finally:
                    step_exec.completed_at = datetime.now()
                    step_exec.duration_seconds = (
                        step_exec.completed_at - step_exec.started_at
                    ).total_seconds()

            # Mark execution complete
            execution.status = ExecutionStatus.SUCCESS
            execution.completed_at = datetime.now()
            execution.duration_seconds = (
                execution.completed_at - execution.started_at
            ).total_seconds()

            # Update runbook stats
            with self.lock:
                runbook = self.runbooks[execution.runbook_id]
                runbook.execution_count += 1
                runbook.last_execution_at = datetime.now()

            self._notify_callbacks({
                "event": "runbook_execution_completed",
                "execution_id": execution.id,
                "status": execution.status.value,
            })

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()

            self._notify_callbacks({
                "event": "runbook_execution_failed",
                "execution_id": execution.id,
                "error": str(e),
            })

    def _execute_webhook(self, step: RunbookStep, step_exec: StepExecution) -> None:
        """Execute webhook step"""
        import requests

        url = step.config.get("url")
        method = step.config.get("method", "POST")
        payload = step.config.get("payload", {})

        try:
            if method == "POST":
                response = requests.post(url, json=payload, timeout=step.timeout_seconds)
            else:
                response = requests.get(url, timeout=step.timeout_seconds)

            step_exec.output = json.dumps({"status_code": response.status_code})
            step_exec.status = ExecutionStatus.SUCCESS if response.status_code < 400 else ExecutionStatus.FAILED

        except Exception as e:
            step_exec.error = str(e)
            step_exec.status = ExecutionStatus.FAILED

    def _execute_command(self, step: RunbookStep, step_exec: StepExecution) -> None:
        """Execute shell command"""
        command = step.config.get("command")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=step.timeout_seconds,
            )

            step_exec.output = result.stdout
            step_exec.status = (
                ExecutionStatus.SUCCESS if result.returncode == 0 else ExecutionStatus.FAILED
            )

            if result.returncode != 0:
                step_exec.error = result.stderr

        except subprocess.TimeoutExpired:
            step_exec.error = "Command timeout"
            step_exec.status = ExecutionStatus.FAILED
        except Exception as e:
            step_exec.error = str(e)
            step_exec.status = ExecutionStatus.FAILED

    def _execute_http(self, step: RunbookStep, step_exec: StepExecution) -> None:
        """Execute HTTP request"""
        self._execute_webhook(step, step_exec)

    def _execute_slack(self, step: RunbookStep, step_exec: StepExecution) -> None:
        """Send Slack notification"""
        webhook_url = step.config.get("webhook_url")
        message = step.config.get("message", "Runbook execution notification")

        try:
            import requests

            payload = {"text": message}
            response = requests.post(webhook_url, json=payload, timeout=step.timeout_seconds)

            step_exec.status = ExecutionStatus.SUCCESS if response.status_code == 200 else ExecutionStatus.FAILED

        except Exception as e:
            step_exec.error = str(e)
            step_exec.status = ExecutionStatus.FAILED

    def _execute_wait(self, step: RunbookStep, step_exec: StepExecution) -> None:
        """Wait for specified duration"""
        wait_seconds = step.config.get("seconds", 60)

        try:
            threading.Event().wait(min(wait_seconds, step.timeout_seconds))
            step_exec.status = ExecutionStatus.SUCCESS
        except Exception as e:
            step_exec.error = str(e)
            step_exec.status = ExecutionStatus.FAILED

    def get_execution_status(self, execution_id: str) -> Optional[RunbookExecution]:
        """Get execution status"""
        with self.lock:
            return self.executions.get(execution_id)

    def get_execution_history(
        self, runbook_id: Optional[str] = None, limit: int = 100
    ) -> List[RunbookExecution]:
        """Get execution history"""
        with self.lock:
            history = [e for e in self.execution_history]

            if runbook_id:
                history = [e for e in history if e.runbook_id == runbook_id]

            return sorted(history, key=lambda e: e.started_at, reverse=True)[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get executor statistics"""
        with self.lock:
            total_executions = len(self.execution_history)
            successful = sum(
                1 for e in self.execution_history if e.status == ExecutionStatus.SUCCESS
            )

            return {
                "total_runbooks": len(self.runbooks),
                "published_runbooks": sum(1 for r in self.runbooks.values() if r.status == RunbookStatus.PUBLISHED),
                "total_executions": total_executions,
                "successful_executions": successful,
                "success_rate": (successful / total_executions * 100) if total_executions > 0 else 0,
            }

    def register_callback(self, callback: Callable) -> None:
        """Register callback for execution events"""
        with self.lock:
            self.callbacks.append(callback)

    def _notify_callbacks(self, event: Dict[str, Any]) -> None:
        """Notify callbacks"""
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in runbook callback: {e}")


# Global singleton
_executor = None


def get_runbook_executor() -> RunbookExecutor:
    """Get or create runbook executor singleton"""
    global _executor
    if _executor is None:
        _executor = RunbookExecutor()
    return _executor
