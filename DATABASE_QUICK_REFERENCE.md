# 🗄️ Database Quick Reference Guide

## Connection & Setup

### Initialize Database
```python
from app.database import init_db
init_db()  # Creates all tables
```

### Get Database Session
```python
from app.database import SessionLocal
session = SessionLocal()
try:
    # Use session
    pass
finally:
    session.close()
```

### Dependency Injection (FastAPI)
```python
from fastapi import Depends
from app.database import get_db

@app.get("/items")
async def read_items(db: Session = Depends(get_db)):
    # Use db session
    return db.query(Item).all()
```

## ORM Models Usage

### 1. User Model

**Create User**
```python
from app.database import User, SessionLocal

session = SessionLocal()
user = User(
    username="john",
    email="john@example.com",
    hashed_password="hashed_pwd",
    full_name="John Doe",
    is_active=True,
    is_admin=False
)
session.add(user)
session.commit()
```

**Query Users**
```python
# Get by ID
user = session.query(User).filter(User.id == 1).first()

# Get by username
user = session.query(User).filter(User.username == "john").first()

# List all
users = session.query(User).all()

# Paginated
users = session.query(User).offset(0).limit(10).all()
```

### 2. Project Model

**Create Project**
```python
from app.database import Project, ProjectStatus
from datetime import datetime

project = Project(
    title="E-Commerce Platform",
    description="Build a modern e-commerce solution",
    project_type="web",
    status=ProjectStatus.IN_PROGRESS,
    tech_stack=["FastAPI", "React", "PostgreSQL"],
    owner_id=1,  # User ID
    start_date=datetime.now(),
    estimated_completion=None,
    completion_percentage=45.0
)
session.add(project)
session.commit()
```

**Update Project Status**
```python
project = session.query(Project).filter(Project.id == 1).first()
project.status = ProjectStatus.COMPLETED
session.commit()
```

### 3. Task Model

**Create Task**
```python
from app.database import Task, TaskStatus

task = Task(
    title="Implement user authentication",
    description="Add JWT-based auth",
    description="Add JWT-based authentication system",
    status=TaskStatus.IN_PROGRESS,
    priority="high",
    project_id=1,
    assigned_to_id=2,  # User ID
    agent_type="code",
    context={"framework": "FastAPI"},
    progress=50.0
)
session.add(task)
session.commit()
```

**Query Tasks**
```python
# By project
tasks = session.query(Task).filter(Task.project_id == 1).all()

# By status
pending = session.query(Task).filter(Task.status == TaskStatus.PENDING).all()

# By assignee
my_tasks = session.query(Task).filter(Task.assigned_to_id == 2).all()
```

### 4. Agent Model

**Create Agent**
```python
from app.database import Agent, AgentType

agent = Agent(
    name="CodeAgent",
    agent_type=AgentType.CODE,
    status="active",
    assigned_project_id=1
)
session.add(agent)
session.commit()
```

**Update Agent Statistics**
```python
agent = session.query(Agent).filter(Agent.id == 1).first()
agent.tasks_processed += 1
agent.files_generated += 5
agent.success_rate = 98.5
session.commit()
```

### 5. Memory Model

**Create Memory**
```python
from app.database import Memory

memory = Memory(
    content="User prefers dark mode interface",
    memory_type="user_preference",
    project_id=1,
    user_id=1,
    meta_info={"confidence": 0.95, "source": "user_settings"}
)
session.add(memory)
session.commit()
```

**Query Memory**
```python
# By project
project_memory = session.query(Memory).filter(Memory.project_id == 1).all()

# By type
preferences = session.query(Memory).filter(Memory.memory_type == "user_preference").all()
```

## Service Layer Usage

### UserService

```python
from app.database.services import UserService

service = UserService(db=session)

# Create user
user = service.create_user(
    username="john",
    email="john@example.com",
    password="plaintext_password",
    full_name="John Doe"
)

# Get user
user = service.get_user_by_username("john")
user = service.get_user_by_email("john@example.com")
user = service.get_user(user_id=1)

# List users
users = service.list_users(skip=0, limit=10)
```

### ProjectService

```python
from app.database.services import ProjectService

service = ProjectService(db=session)

# Create
project = service.create_project(
    title="New Project",
    description="Description",
    project_type="web",
    tech_stack=["FastAPI"],
    owner_id=1
)

# Read
project = service.get_project(project_id=1)
projects = service.list_projects(owner_id=1)

# Update status
service.update_project_status(project_id=1, status="completed")

# Delete
service.delete_project(project_id=1)
```

### TaskService

```python
from app.database.services import TaskService

service = TaskService(db=session)

# Create
task = service.create_task(
    title="Task Title",
    project_id=1,
    assigned_to_id=2
)

# Read
task = service.get_task(task_id=1)
tasks = service.list_tasks(project_id=1, status="pending")

# Update
service.update_task_status(task_id=1, status="completed")
service.update_task_progress(task_id=1, progress=100.0)
```

### AgentService

```python
from app.database.services import AgentService

service = AgentService(db=session)

# Create
agent = service.create_agent(
    name="CodeAgent",
    agent_type="code",
    assigned_project_id=1
)

# Read
agent = service.get_agent(agent_id=1)
code_agent = service.get_agent_by_type(agent_type="code")
agents = service.list_agents()

# Update
service.update_agent_status(agent_id=1, status="inactive")
service.increment_agent_stats(agent_id=1, tasks_processed=1)
```

## Advanced Queries

### Relationships

```python
# Get user's projects
user = session.query(User).filter(User.id == 1).first()
projects = user.projects  # Lazy loaded

# Get project's tasks
project = session.query(Project).filter(Project.id == 1).first()
tasks = project.tasks

# Get task's assigned user
task = session.query(Task).filter(Task.id == 1).first()
assigned_user = task.assigned_user
```

### Joins

```python
# Tasks with user information
from sqlalchemy import join

query = session.query(Task, User).join(User).filter(Task.project_id == 1)
for task, user in query:
    print(f"{task.title} assigned to {user.username}")
```

### Filtering & Ordering

```python
# Multiple conditions
tasks = session.query(Task).filter(
    (Task.project_id == 1) & 
    (Task.status == "in_progress")
).order_by(Task.priority.desc()).all()

# Using IN
high_priority_tasks = session.query(Task).filter(
    Task.priority.in_(["high", "critical"])
).all()
```

### Aggregations

```python
from sqlalchemy import func

# Count
task_count = session.query(func.count(Task.id)).filter(Task.project_id == 1).scalar()

# Sum
total_progress = session.query(func.sum(Task.progress)).filter(
    Task.project_id == 1
).scalar()
```

## Error Handling

```python
from sqlalchemy.exc import SQLAlchemyError

try:
    session.add(new_user)
    session.commit()
except SQLAlchemyError as e:
    session.rollback()
    print(f"Database error: {e}")
finally:
    session.close()
```

## Transactions

```python
# Automatic transaction with context manager
from app.database import SessionLocal

session = SessionLocal()
try:
    # All changes are in a transaction
    session.add(user1)
    session.add(user2)
    session.commit()  # Atomically saves both
except Exception as e:
    session.rollback()  # Reverts all changes
    raise
finally:
    session.close()
```

## Best Practices

1. **Always close sessions** - Use try/finally or context managers
2. **Use services layer** - Don't query directly in routes
3. **Eager load when needed** - Avoid N+1 queries
4. **Use parameters** - Prevent SQL injection with parameterized queries
5. **Index foreign keys** - Already configured in models
6. **Cascade deletes** - Configured to maintain referential integrity
7. **Type hints** - All models have type annotations
8. **Timestamps** - All models track created_at and updated_at

## Database Maintenance

### Reset Database
```python
from app.database import drop_db, init_db

drop_db()   # Delete all tables
init_db()   # Recreate all tables
```

### Seed Data
```python
from app.database.seed import seed_database

seed_database()  # Populate with sample data
```

### Export Data
```sql
-- PostgreSQL command line
psql -U user -d omnidev -c "SELECT * FROM users;" > users.csv
```

---

**Last Updated**: February 2025  
**Database**: PostgreSQL 16  
**ORM**: SQLAlchemy 2.0.46  
**Status**: ✅ Production Ready
