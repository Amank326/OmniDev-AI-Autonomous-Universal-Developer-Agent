"""Planner Agent - Central decision-making unit"""

import json
from typing import Dict, List, Optional
import logging
from app.agents.base_agent import BaseAgent
from app.agents.code_agent import CodeAgent
from app.agents.web_agent import WebAgent
from app.agents.devops_agent import DevOpsAgent

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    """Main planning agent that coordinates all other agents"""
    
    def __init__(self, memory=None):
        super().__init__("PlannerAgent", memory)
        self.capabilities = [
            "goal_analysis",
            "task_breakdown",
            "agent_coordination",
            "progress_tracking",
            "error_recovery"
        ]
        
        # Initialize skill agents
        self.code_agent = CodeAgent(memory=memory)
        self.web_agent = WebAgent(memory=memory)
        self.devops_agent = DevOpsAgent(memory=memory)
        
        self.agents = {
            "code": self.code_agent,
            "web": self.web_agent,
            "devops": self.devops_agent
        }
    
    async def process(self, task: str, context: Dict) -> Dict:
        """
        Break down task and coordinate agent execution
        
        Example:
        User: "Create e-commerce website"
        
        Planner output:
        1. Design UI (Web Agent)
        2. Create backend (Code Agent)
        3. Setup database (Code Agent)
        4. Deploy (DevOps Agent)
        """
        
        logger.info(f"Analyzing task: {task}")
        
        # Parse task and generate plan
        plan = await self._generate_plan(task, context)
        
        if not plan:
            return {
                "status": "error",
                "message": "Could not generate valid plan"
            }
        
        logger.info(f"Generated plan with {len(plan['steps'])} steps")
        
        # Execute plan
        results = []
        for step in plan['steps']:
            result = await self._execute_step(step, context)
            results.append(result)
            
            if result['status'] == 'error':
                logger.error(f"Step failed: {step['description']}")
                break
        
        return {
            "status": "completed",
            "plan": plan,
            "execution_results": results,
            "summary": self._summarize_results(results)
        }
    
    async def _generate_plan(self, task: str, context: Dict) -> Optional[Dict]:
        """Generate execution plan from task"""
        
        # Simple task classification
        task_lower = task.lower()
        
        plan = {
            "task": task,
            "steps": [],
            "estimated_time": "30 minutes"
        }
        
        # E-commerce website
        if "e-commerce" in task_lower or "shop" in task_lower:
            plan['steps'] = [
                {
                    "id": 1,
                    "agent": "web",
                    "description": "Design UI/UX",
                    "subtasks": ["Homepage", "Product page", "Cart", "Checkout"]
                },
                {
                    "id": 2,
                    "agent": "code",
                    "description": "Create backend API",
                    "subtasks": ["User endpoints", "Product endpoints", "Order endpoints"]
                },
                {
                    "id": 3,
                    "agent": "code",
                    "description": "Setup database",
                    "subtasks": ["Users", "Products", "Orders", "Payments"]
                },
                {
                    "id": 4,
                    "agent": "devops",
                    "description": "Deploy",
                    "subtasks": ["Docker", "CI/CD", "Production"]
                }
            ]
        
        # Web app
        elif "web" in task_lower or "website" in task_lower:
            plan['steps'] = [
                {
                    "id": 1,
                    "agent": "web",
                    "description": "Design and create frontend",
                    "subtasks": ["Layout", "Components", "Styling"]
                },
                {
                    "id": 2,
                    "agent": "code",
                    "description": "Create backend",
                    "subtasks": ["API", "Database", "Authentication"]
                },
                {
                    "id": 3,
                    "agent": "devops",
                    "description": "Deploy application",
                    "subtasks": ["Setup", "CI/CD", "Monitoring"]
                }
            ]
        
        # Python app
        elif "python" in task_lower or "script" in task_lower:
            plan['steps'] = [
                {
                    "id": 1,
                    "agent": "code",
                    "description": "Create Python application",
                    "subtasks": ["Core logic", "Error handling", "Testing"]
                },
                {
                    "id": 2,
                    "agent": "devops",
                    "description": "Package and deploy",
                    "subtasks": ["Requirements", "Docker", "Deployment"]
                }
            ]
        
        else:
            plan['steps'] = [
                {
                    "id": 1,
                    "agent": "code",
                    "description": "Create project",
                    "subtasks": ["Initialize", "Structure", "Core logic"]
                }
            ]
        
        return plan
    
    async def _execute_step(self, step: Dict, context: Dict) -> Dict:
        """Execute single step using appropriate agent"""
        
        agent_name = step.get('agent')
        agent = self.agents.get(agent_name)
        
        if not agent:
            return {
                "step_id": step['id'],
                "status": "error",
                "error": f"Unknown agent: {agent_name}"
            }
        
        # Execute with agent
        result = await agent.execute(
            task=step['description'],
            context={
                **context,
                "subtasks": step.get('subtasks', [])
            }
        )
        
        return {
            "step_id": step['id'],
            "description": step['description'],
            "agent": agent_name,
            **result
        }
    
    def _summarize_results(self, results: List[Dict]) -> Dict:
        """Summarize execution results"""
        
        total = len(results)
        successful = sum(1 for r in results if r.get('status') != 'error')
        failed = total - successful
        
        return {
            "total_steps": total,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/total)*100:.1f}%"
        }
