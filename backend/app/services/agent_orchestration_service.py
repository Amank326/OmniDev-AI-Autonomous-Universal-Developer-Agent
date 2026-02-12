"""
Phase 15: Agent Orchestration Service
- Agent-to-agent communication
- Workflow creation from agent chains
- Execution coordination
- State management
"""

from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
from sqlalchemy.orm import Session
from enum import Enum
import json
import uuid


class WorkflowStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class AgentOrchestrationService:
    """Orchestrate agent chains and workflows"""
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_registry: Dict[str, Callable] = {}
    
    # ============ AGENT REGISTRATION ============
    
    def register_agent(self, agent_id: str, executor: Callable) -> None:
        """Register an agent's execution function"""
        self.agent_registry[agent_id] = executor
    
    def get_registered_agent(self, agent_id: str) -> Optional[Callable]:
        """Get registered agent executor"""
        return self.agent_registry.get(agent_id)
    
    # ============ WORKFLOW DEFINITION ============
    
    def create_workflow(
        self,
        name: str,
        description: str,
        user_id: str,
        agents: List[Dict[str, Any]],  # [{"agent_id": "...", "config": {...}}]
        routing: Optional[List[Dict[str, Any]]] = None  # Connections between agents
    ) -> Dict[str, Any]:
        """Create an agent workflow"""
        from app.models.agent_models import AgentWorkflow, AgentWorkflowStep
        
        workflow_id = str(uuid.uuid4())
        
        workflow = AgentWorkflow(
            id=workflow_id,
            user_id=user_id,
            name=name,
            description=description,
            workflow_definition={
                "agents": agents,
                "routing": routing or []
            },
            status="draft",
            created_at=datetime.utcnow()
        )
        
        self.db.add(workflow)
        
        # Create workflow steps
        for i, agent_config in enumerate(agents):
            step = AgentWorkflowStep(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                agent_id=agent_config.get("agent_id"),
                step_number=i + 1,
                config=agent_config.get("config", {}),
                created_at=datetime.utcnow()
            )
            self.db.add(step)
        
        self.db.commit()
        
        return {
            "workflow_id": workflow_id,
            "name": name,
            "status": "draft",
            "agent_count": len(agents),
            "created_at": workflow.created_at.isoformat()
        }
    
    def get_workflow(self, workflow_id: str) -> Optional[Any]:
        """Get workflow definition"""
        from app.models.agent_models import AgentWorkflow
        
        return self.db.query(AgentWorkflow).filter(
            AgentWorkflow.id == workflow_id
        ).first()
    
    def list_user_workflows(self, user_id: str) -> List[Any]:
        """Get all workflows for a user"""
        from app.models.agent_models import AgentWorkflow
        
        return self.db.query(AgentWorkflow).filter(
            AgentWorkflow.user_id == user_id
        ).order_by(AgentWorkflow.created_at.desc()).all()
    
    # ============ WORKFLOW EXECUTION ============
    
    def execute_workflow(
        self,
        workflow_id: str,
        user_id: str,
        initial_input: Any,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute a workflow with the given input"""
        from app.models.agent_models import (
            AgentWorkflow, AgentWorkflowExecution, 
            AgentWorkflowStepExecution
        )
        
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        execution_id = str(uuid.uuid4())
        
        # Create workflow execution record
        execution = AgentWorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            user_id=user_id,
            status=WorkflowStatus.PENDING,
            input_data=initial_input,
            context_data=context or {},
            created_at=datetime.utcnow()
        )
        
        self.db.add(execution)
        self.db.commit()
        
        # Start execution in background
        try:
            self._execute_workflow_async(execution_id, workflow, initial_input, context)
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            self.db.commit()
        
        return {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": "pending",
            "created_at": execution.created_at.isoformat()
        }
    
    def _execute_workflow_async(
        self,
        execution_id: str,
        workflow: Any,
        initial_input: Any,
        context: Optional[Dict]
    ) -> None:
        """Execute workflow steps in sequence"""
        from app.models.agent_models import (
            AgentWorkflowExecution, AgentWorkflowStepExecution
        )
        
        execution = self.db.query(AgentWorkflowExecution).filter(
            AgentWorkflowExecution.id == execution_id
        ).first()
        
        if not execution:
            return
        
        execution.status = WorkflowStatus.RUNNING
        execution.start_time = datetime.utcnow()
        self.db.commit()
        
        steps = workflow.workflow_definition.get("agents", [])
        current_output = initial_input
        
        try:
            for i, agent_config in enumerate(steps):
                agent_id = agent_config.get("agent_id")
                config = agent_config.get("config", {})
                
                step_execution_id = str(uuid.uuid4())
                
                # Execute agent
                step_start = datetime.utcnow()
                step_result = self._execute_agent_in_workflow(
                    agent_id,
                    current_output,
                    config,
                    context
                )
                step_end = datetime.utcnow()
                
                # Record step execution
                step_execution = AgentWorkflowStepExecution(
                    id=step_execution_id,
                    execution_id=execution_id,
                    agent_id=agent_id,
                    step_number=i + 1,
                    input_data=current_output,
                    output_data=step_result.get("output"),
                    status=step_result.get("status", "completed"),
                    duration_seconds=(step_end - step_start).total_seconds(),
                    error_message=step_result.get("error"),
                    created_at=datetime.utcnow()
                )
                
                self.db.add(step_execution)
                self.db.commit()
                
                # Stop if step failed
                if step_result.get("status") == "failed":
                    execution.status = WorkflowStatus.FAILED
                    execution.error_message = step_result.get("error")
                    break
                
                # Use output as input for next step
                current_output = step_result.get("output")
            
            # Mark execution as complete
            execution.status = WorkflowStatus.COMPLETED
            execution.output_data = current_output
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
        
        execution.end_time = datetime.utcnow()
        self.db.commit()
    
    def _execute_agent_in_workflow(
        self,
        agent_id: str,
        input_data: Any,
        config: Dict,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Execute a single agent in workflow context"""
        try:
            executor = self.get_registered_agent(agent_id)
            if not executor:
                return {
                    "status": "failed",
                    "error": f"Agent {agent_id} not registered"
                }
            
            # Call agent executor
            result = executor(
                input=input_data,
                config=config,
                context=context
            )
            
            return {
                "status": "completed",
                "output": result,
                "error": None
            }
        except Exception as e:
            return {
                "status": "failed",
                "output": None,
                "error": str(e)
            }
    
    def get_workflow_execution(self, execution_id: str) -> Optional[Any]:
        """Get workflow execution details"""
        from app.models.agent_models import AgentWorkflowExecution
        
        return self.db.query(AgentWorkflowExecution).filter(
            AgentWorkflowExecution.id == execution_id
        ).first()
    
    def cancel_workflow_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow"""
        from app.models.agent_models import AgentWorkflowExecution
        
        execution = self.db.query(AgentWorkflowExecution).filter(
            AgentWorkflowExecution.id == execution_id
        ).first()
        
        if not execution:
            return False
        
        if execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.CANCELLED
            execution.end_time = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    # ============ AGENT-TO-AGENT COMMUNICATION ============
    
    def send_message_to_agent(
        self,
        from_agent_id: str,
        to_agent_id: str,
        message_type: str,
        payload: Dict,
        execution_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send message between agents"""
        from app.models.agent_models import AgentMessage
        
        message_id = str(uuid.uuid4())
        
        message = AgentMessage(
            id=message_id,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=message_type,
            payload=payload,
            execution_context=execution_context,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self.db.add(message)
        self.db.commit()
        
        return {
            "message_id": message_id,
            "from_agent_id": from_agent_id,
            "to_agent_id": to_agent_id,
            "status": "pending",
            "created_at": message.created_at.isoformat()
        }
    
    def get_agent_messages(self, agent_id: str, unread_only: bool = False) -> List[Any]:
        """Get messages for an agent"""
        from app.models.agent_models import AgentMessage
        
        q = self.db.query(AgentMessage).filter(
            AgentMessage.to_agent_id == agent_id
        )
        
        if unread_only:
            q = q.filter(AgentMessage.status == "pending")
        
        return q.order_by(AgentMessage.created_at.desc()).all()
    
    def mark_message_processed(self, message_id: str, response: Optional[Dict] = None) -> bool:
        """Mark agent message as processed"""
        from app.models.agent_models import AgentMessage
        
        message = self.db.query(AgentMessage).filter(
            AgentMessage.id == message_id
        ).first()
        
        if not message:
            return False
        
        message.status = "processed"
        message.response = response
        message.processed_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    # ============ WORKFLOW TEMPLATES ============
    
    def publish_workflow_template(
        self,
        workflow_id: str,
        user_id: str,
        template_name: str,
        description: str,
        tags: List[str]
    ) -> Dict[str, Any]:
        """Publish workflow as a reusable template"""
        from app.models.agent_models import WorkflowTemplate
        
        template_id = str(uuid.uuid4())
        
        template = WorkflowTemplate(
            id=template_id,
            workflow_id=workflow_id,
            author_id=user_id,
            name=template_name,
            description=description,
            tags=tags,
            is_public=False,
            created_at=datetime.utcnow()
        )
        
        self.db.add(template)
        self.db.commit()
        
        return {
            "template_id": template_id,
            "workflow_id": workflow_id,
            "name": template_name,
            "created_at": template.created_at.isoformat()
        }
    
    def get_workflow_templates(self, category: Optional[str] = None) -> List[Any]:
        """Get public workflow templates"""
        from app.models.agent_models import WorkflowTemplate
        
        q = self.db.query(WorkflowTemplate).filter(
            WorkflowTemplate.is_public == True
        )
        
        if category:
            q = q.filter(WorkflowTemplate.tags.astext.contains(category))
        
        return q.order_by(WorkflowTemplate.created_at.desc()).all()
    
    # ============ WORKFLOW MONITORING ============
    
    def get_workflow_execution_history(
        self,
        workflow_id: str,
        limit: int = 20
    ) -> List[Any]:
        """Get execution history for a workflow"""
        from app.models.agent_models import AgentWorkflowExecution
        
        return self.db.query(AgentWorkflowExecution).filter(
            AgentWorkflowExecution.workflow_id == workflow_id
        ).order_by(
            AgentWorkflowExecution.created_at.desc()
        ).limit(limit).all()
    
    def get_workflow_stats(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow statistics"""
        from app.models.agent_models import AgentWorkflowExecution
        
        executions = self.db.query(AgentWorkflowExecution).filter(
            AgentWorkflowExecution.workflow_id == workflow_id
        ).all()
        
        if not executions:
            return {
                "workflow_id": workflow_id,
                "total_executions": 0,
                "success_rate": 0.0
            }
        
        successful = sum(1 for e in executions if e.status == WorkflowStatus.COMPLETED)
        
        durations = [
            (e.end_time - e.start_time).total_seconds()
            for e in executions
            if e.end_time and e.start_time
        ]
        
        return {
            "workflow_id": workflow_id,
            "total_executions": len(executions),
            "successful_executions": successful,
            "success_rate": (successful / len(executions) * 100) if executions else 0,
            "average_duration_seconds": sum(durations) / len(durations) if durations else 0,
            "last_execution": executions[0].created_at.isoformat() if executions else None
        }
