"""
Phase 10: Workflow & Automation API Routes
13 REST endpoints + WebSocket for workflow management, rules, scheduling, and analytics
"""

from fastapi import APIRouter, WebSocket, HTTPException, Query, Body
from typing import Dict, List, Any, Optional
import uuid
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/phase10", tags=["Phase 10 - Workflows & Automation"])

# In-memory storage (replace with database in production)
workflows_db = {}
rules_db = {}
scheduler_db = {}
websocket_connections = {}


# ============================================================================
# WORKFLOW MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/workflows/create")
async def create_workflow(workflow_data: Dict[str, Any] = Body(...)):
    """Create a new workflow"""
    try:
        workflow_id = str(uuid.uuid4())
        
        workflow = {
            "id": workflow_id,
            "name": workflow_data.get("name", "Unnamed Workflow"),
            "description": workflow_data.get("description"),
            "nodes": workflow_data.get("nodes", {}),
            "edges": workflow_data.get("edges", []),
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "executions": [],
        }
        
        workflows_db[workflow_id] = workflow
        logger.info(f"Created workflow: {workflow_id}")
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Workflow created successfully",
        }
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workflows")
async def list_workflows(status: Optional[str] = Query(None), limit: int = Query(100)):
    """List all workflows"""
    try:
        workflows = list(workflows_db.values())
        
        if status:
            workflows = [w for w in workflows if w.get("status") == status]
        
        return {
            "success": True,
            "total": len(workflows),
            "workflows": workflows[:limit],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a specific workflow"""
    try:
        workflow = workflows_db.get(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "success": True,
            "workflow": workflow,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/workflows/{workflow_id}")
async def update_workflow(workflow_id: str, updates: Dict[str, Any] = Body(...)):
    """Update a workflow"""
    try:
        workflow = workflows_db.get(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow.update(updates)
        workflow["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Updated workflow: {workflow_id}")
        
        return {
            "success": True,
            "message": "Workflow updated successfully",
            "workflow": workflow,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    try:
        if workflow_id not in workflows_db:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        del workflows_db[workflow_id]
        logger.info(f"Deleted workflow: {workflow_id}")
        
        return {
            "success": True,
            "message": "Workflow deleted successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, input_data: Dict[str, Any] = Body(...)):
    """Execute a workflow"""
    try:
        workflow = workflows_db.get(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        execution_id = str(uuid.uuid4())
        
        execution = {
            "id": execution_id,
            "workflow_id": workflow_id,
            "status": "running",
            "input_data": input_data,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": None,
            "result": None,
        }
        
        workflow.setdefault("executions", []).append(execution)
        
        logger.info(f"Started execution {execution_id} for workflow {workflow_id}")
        
        return {
            "success": True,
            "execution_id": execution_id,
            "status": "running",
            "message": "Workflow execution started",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workflows/{workflow_id}/executions")
async def get_workflow_executions(workflow_id: str, limit: int = Query(100)):
    """Get execution history for a workflow"""
    try:
        workflow = workflows_db.get(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        executions = workflow.get("executions", [])
        
        return {
            "success": True,
            "total": len(executions),
            "executions": executions[-limit:],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# AUTOMATION RULES ENDPOINTS
# ============================================================================

@router.post("/rules/create")
async def create_rule(rule_data: Dict[str, Any] = Body(...)):
    """Create an automation rule"""
    try:
        rule_id = str(uuid.uuid4())
        
        rule = {
            "id": rule_id,
            "name": rule_data.get("name", "Unnamed Rule"),
            "description": rule_data.get("description"),
            "trigger_type": rule_data.get("trigger_type", "event"),
            "trigger_config": rule_data.get("trigger_config", {}),
            "conditions": rule_data.get("conditions", []),
            "actions": rule_data.get("actions", []),
            "is_enabled": rule_data.get("is_enabled", True),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "executions": [],
        }
        
        rules_db[rule_id] = rule
        logger.info(f"Created rule: {rule_id}")
        
        return {
            "success": True,
            "rule_id": rule_id,
            "message": "Rule created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rules")
async def list_rules(enabled_only: bool = Query(False), limit: int = Query(100)):
    """List all automation rules"""
    try:
        rules = list(rules_db.values())
        
        if enabled_only:
            rules = [r for r in rules if r.get("is_enabled")]
        
        return {
            "success": True,
            "total": len(rules),
            "rules": rules[:limit],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, updates: Dict[str, Any] = Body(...)):
    """Update an automation rule"""
    try:
        rule = rules_db.get(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        rule.update(updates)
        rule["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Updated rule: {rule_id}")
        
        return {
            "success": True,
            "message": "Rule updated successfully",
            "rule": rule,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete an automation rule"""
    try:
        if rule_id not in rules_db:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        del rules_db[rule_id]
        logger.info(f"Deleted rule: {rule_id}")
        
        return {
            "success": True,
            "message": "Rule deleted successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rules/{rule_id}/test")
async def test_rule(rule_id: str, test_data: Dict[str, Any] = Body(...)):
    """Test a rule with sample data"""
    try:
        rule = rules_db.get(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Evaluate conditions
        conditions = rule.get("conditions", [])
        would_trigger = len(conditions) == 0  # Default: trigger if no conditions
        
        # Check conditions against test data
        for condition in conditions:
            field = condition.get("field", "")
            operator = condition.get("operator", "equals")
            value = condition.get("value")
            
            test_value = test_data.get(field)
            
            if operator == "equals" and test_value == value:
                would_trigger = True
            elif operator == "contains" and value in str(test_value):
                would_trigger = True
        
        logger.info(f"Tested rule {rule_id}: would_trigger={would_trigger}")
        
        return {
            "success": True,
            "rule_id": rule_id,
            "would_trigger": would_trigger,
            "conditions_count": len(conditions),
            "actions_count": len(rule.get("actions", [])),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# SCHEDULER ENDPOINTS
# ============================================================================

@router.post("/scheduler/create")
async def create_scheduled_task(task_data: Dict[str, Any] = Body(...)):
    """Create a scheduled task"""
    try:
        task_id = str(uuid.uuid4())
        
        task = {
            "id": task_id,
            "name": task_data.get("name", "Unnamed Task"),
            "description": task_data.get("description"),
            "cron_expression": task_data.get("cron_expression"),
            "timezone": task_data.get("timezone", "UTC"),
            "workflow_id": task_data.get("workflow_id"),
            "is_enabled": task_data.get("is_enabled", True),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "executions": [],
        }
        
        scheduler_db[task_id] = task
        logger.info(f"Created scheduled task: {task_id}")
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Scheduled task created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scheduler/tasks")
async def list_scheduled_tasks(enabled_only: bool = Query(False), limit: int = Query(100)):
    """List all scheduled tasks"""
    try:
        tasks = list(scheduler_db.values())
        
        if enabled_only:
            tasks = [t for t in tasks if t.get("is_enabled")]
        
        return {
            "success": True,
            "total": len(tasks),
            "tasks": tasks[:limit],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/scheduler/{task_id}")
async def update_scheduled_task(task_id: str, updates: Dict[str, Any] = Body(...)):
    """Update a scheduled task"""
    try:
        task = scheduler_db.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.update(updates)
        task["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Updated task: {task_id}")
        
        return {
            "success": True,
            "message": "Task updated successfully",
            "task": task,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/workflows/{workflow_id}/analytics")
async def get_workflow_analytics(workflow_id: str):
    """Get analytics for a workflow"""
    try:
        workflow = workflows_db.get(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        executions = workflow.get("executions", [])
        
        total = len(executions)
        successful = sum(1 for e in executions if e.get("status") == "success")
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "analytics": {
                "total_executions": total,
                "successful": successful,
                "failed": total - successful,
                "success_rate": success_rate,
                "avg_execution_time": 0.0,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/actions/available")
async def list_available_actions():
    """Get list of available actions"""
    try:
        actions = {
            "communication": [
                {"name": "send_email", "display_name": "Send Email"},
                {"name": "send_slack", "display_name": "Send Slack Message"},
                {"name": "send_sms", "display_name": "Send SMS"},
                {"name": "send_webhook", "display_name": "Send Webhook"},
                {"name": "send_notification", "display_name": "Send Notification"},
            ],
            "data": [
                {"name": "create_record", "display_name": "Create Record"},
                {"name": "update_record", "display_name": "Update Record"},
                {"name": "delete_record", "display_name": "Delete Record"},
                {"name": "query_data", "display_name": "Query Data"},
                {"name": "export_data", "display_name": "Export Data"},
            ],
            "workflow": [
                {"name": "trigger_workflow", "display_name": "Trigger Workflow"},
                {"name": "call_api", "display_name": "Call API"},
                {"name": "wait_event", "display_name": "Wait for Event"},
                {"name": "parallel_execute", "display_name": "Parallel Execute"},
            ],
            "alerts": [
                {"name": "create_alert", "display_name": "Create Alert"},
                {"name": "log_event", "display_name": "Log Event"},
                {"name": "publish_metric", "display_name": "Publish Metric"},
            ],
            "system": [
                {"name": "execute_script", "display_name": "Execute Script"},
                {"name": "run_command", "display_name": "Run Command"},
                {"name": "file_operation", "display_name": "File Operation"},
                {"name": "archive_data", "display_name": "Archive Data"},
            ],
        }
        
        return {
            "success": True,
            "actions": actions,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@router.websocket("/ws/workflows/{client_id}")
async def websocket_workflow_updates(websocket: WebSocket, client_id: str):
    """WebSocket for real-time workflow execution updates"""
    await websocket.accept()
    websocket_connections[client_id] = websocket
    
    try:
        logger.info(f"Client {client_id} connected to workflow updates")
        
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            message_type = message.get("type")
            
            if message_type == "subscribe":
                workflow_id = message.get("workflow_id")
                logger.info(f"Client {client_id} subscribed to workflow {workflow_id}")
                
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "workflow_id": workflow_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            
            elif message_type == "get_status":
                workflow_id = message.get("workflow_id")
                workflow = workflows_db.get(workflow_id, {})
                
                await websocket.send_json({
                    "type": "status",
                    "workflow_id": workflow_id,
                    "total_executions": len(workflow.get("executions", [])),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            
            elif message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
    
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    
    finally:
        if client_id in websocket_connections:
            del websocket_connections[client_id]
        logger.info(f"Client {client_id} disconnected")
