# Agent Implementation Guide

## Overview

Each agent is a specialized AI worker that handles specific aspects of software development.

## Base Agent Architecture

All agents inherit from `BaseAgent` which provides:
- Task execution framework
- Error handling
- Memory integration
- Logging
- Status tracking

## Agent Types

### 1. Code Agent

**Responsibility**: Generate and manage code

**Key Methods**:
- `process(task, context)` - Generate code
- `_generate_code(subtask, context)` - Create code snippets
- `_get_filename(subtask)` - Determine file names
- `_detect_language(context)` - Identify programming language

**Example Usage**:
```python
agent = CodeAgent(memory=memory)
result = await agent.execute(
    task="Create API endpoints",
    context={
        "subtasks": ["user_endpoints", "product_endpoints"],
        "language": "Python"
    }
)
```

**Output**:
```json
{
    "status": "success",
    "files_generated": 2,
    "files": [
        {
            "subtask": "user_endpoints",
            "filename": "user_endpoints.py",
            "code": "...",
            "language": "Python"
        }
    ]
}
```

### 2. Web Agent

**Responsibility**: Create UI/UX and web interfaces

**Key Methods**:
- `process(task, context)` - Create web components
- `_create_component(subtask, context)` - Design UI element
- `_generate_jsx(component_name)` - Create React code
- `_generate_animations(component_name)` - Create CSS animations

**Example Usage**:
```python
agent = WebAgent(memory=memory)
result = await agent.execute(
    task="Design UI",
    context={
        "subtasks": ["homepage", "product_page", "cart"],
        "style": "glassmorphism_3d"
    }
)
```

**Output**:
```json
{
    "status": "success",
    "components_created": 3,
    "design_style": "glassmorphism_with_neon_accents",
    "animation_enabled": true,
    "components": [
        {
            "name": "Homepage",
            "structure": ["Header", "Hero", "Features"],
            "animations": ["Fade-in", "Slide-up"],
            "jsx_code": "..."
        }
    ]
}
```

### 3. DevOps Agent

**Responsibility**: Infrastructure, deployment, CI/CD

**Key Methods**:
- `process(task, context)` - Setup infrastructure
- `_generate_config(subtask, context)` - Create config files
- `_generate_dockerfile(context)` - Create Docker setup
- `_generate_github_actions()` - Create CI/CD workflow
- `_generate_deploy_script()` - Create deployment script

**Example Usage**:
```python
agent = DevOpsAgent(memory=memory)
result = await agent.execute(
    task="Deploy",
    context={
        "subtasks": ["docker", "ci/cd", "production"],
        "platform": "AWS"
    }
)
```

**Output**:
```json
{
    "status": "success",
    "configs_generated": 3,
    "platforms": ["Docker", "GitHub Actions", "AWS"],
    "ready_to_deploy": true,
    "configs": [
        {
            "type": "Dockerfile",
            "content": "...",
            "location": "Dockerfile"
        }
    ]
}
```

### 4. Planner Agent

**Responsibility**: Task planning and agent coordination

**Key Methods**:
- `process(task, context)` - Execute complete plan
- `_generate_plan(task, context)` - Create execution plan
- `_execute_step(step, context)` - Run individual steps
- `_summarize_results(results)` - Aggregate outcomes

**Example Workflow**:
```
Input: "Create e-commerce website"

Analysis Phase:
- Classify task type
- Determine complexity
- Identify required steps

Planning Phase:
- Create step-by-step plan
- Assign to agents
- Set deadlines

Execution Phase:
- Coordinate agents
- Monitor progress
- Handle errors

Summary Phase:
- Aggregate results
- Report status
```

## Creating Custom Agents

### Step 1: Inherit from BaseAgent

```python
from app.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, memory=None):
        super().__init__("MyAgent", memory)
        self.capabilities = ["capability1", "capability2"]
```

### Step 2: Implement process() method

```python
async def process(self, task: str, context: Dict) -> Dict:
    """Process task and return result"""
    try:
        result = await self._do_work(task, context)
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

### Step 3: Add helper methods

```python
async def _do_work(self, task: str, context: Dict) -> Any:
    """Actual work logic"""
    # Your implementation
    pass
```

### Step 4: Use memory (optional)

```python
# Store information
await self.store_memory("key", "value")

# Retrieve information
value = await self.retrieve_memory("key")
```

## Agent Communication Protocol

### Message Format

```json
{
    "type": "task_assignment",
    "from_agent": "PlannerAgent",
    "to_agent": "CodeAgent",
    "task_id": "task_123",
    "task": "Generate code",
    "context": {
        "language": "Python",
        "framework": "FastAPI"
    },
    "deadline": "2026-02-05T11:00:00Z",
    "priority": "high"
}
```

### Response Format

```json
{
    "type": "task_result",
    "from_agent": "CodeAgent",
    "to_agent": "PlannerAgent",
    "task_id": "task_123",
    "status": "success",
    "result": {
        "files_generated": 5,
        "lines_of_code": 1250
    },
    "timestamp": "2026-02-05T10:30:00Z"
}
```

## Agent Lifecycle

### 1. Initialization
```python
agent = CodeAgent(memory=vector_memory)
# Agent ready, status = "idle"
```

### 2. Task Reception
```python
task = "Create API"
context = {...}
```

### 3. Execution
```python
result = await agent.execute(task, context)
# Agent status = "executing"
# Task is logged
# Error handling applied
```

### 4. Completion
```python
# status = "idle"
# task_history updated
# memory stored (if enabled)
```

## Error Handling

### Error Types

1. **Task Error**: Task not understood
2. **Execution Error**: Failed during execution
3. **Resource Error**: Missing dependencies
4. **Timeout Error**: Took too long

### Recovery Strategies

```python
async def execute(self, task: str, context: Dict) -> Dict:
    try:
        result = await self.process(task, context)
    except TimeoutError:
        # Retry with timeout
        result = await self.process_with_retry(task, context)
    except ValueError:
        # Log and return error
        logger.error(f"Invalid task: {task}")
    return result
```

## Testing Agents

### Unit Test Example

```python
import pytest
from app.agents.code_agent import CodeAgent

@pytest.mark.asyncio
async def test_code_generation():
    agent = CodeAgent()
    result = await agent.execute(
        task="Generate endpoints",
        context={"subtasks": ["users", "products"]}
    )
    
    assert result["status"] == "success"
    assert len(result["files"]) == 2
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_agent_coordination():
    planner = PlannerAgent()
    result = await planner.execute(
        task="Create website",
        context={}
    )
    
    assert result["status"] == "completed"
    assert len(result["execution_results"]) > 0
```

## Performance Optimization

### 1. Parallel Execution

```python
# Run multiple agents simultaneously
results = await asyncio.gather(
    code_agent.execute(task1, ctx1),
    web_agent.execute(task2, ctx2),
    devops_agent.execute(task3, ctx3)
)
```

### 2. Caching Results

```python
# Store frequently generated code
cached = await self.retrieve_memory("pattern:rest_api")
if cached:
    return cached
```

### 3. Lazy Loading

```python
# Generate only when needed
if "frontend" in task.lower():
    web_agent = WebAgent()  # Initialize on demand
```

---

For specific agent implementations, see the respective agent files in `app/agents/`.
