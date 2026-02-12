"""Database utilities and helpers"""

from sqlalchemy.orm import Session
from .models import User, Project, Task, Agent, AgentType, ProjectStatus, TaskStatus
from datetime import datetime
import uuid


class UserService:
    """User database operations"""

    @staticmethod
    def create_user(db: Session, username: str, email: str, hashed_password: str, full_name: str = None):
        """Create a new user"""
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_by_username(db: Session, username: str):
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user(db: Session, user_id: str):
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 10):
        """List users with pagination"""
        return db.query(User).offset(skip).limit(limit).all()


class ProjectService:
    """Project database operations"""

    @staticmethod
    def create_project(db: Session, title: str, description: str, project_type: str, owner_id: str, tech_stack: list = None):
        """Create a new project"""
        project = Project(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            project_type=project_type,
            owner_id=owner_id,
            tech_stack=tech_stack,
            status=ProjectStatus.PLANNING
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project(db: Session, project_id: str):
        """Get project by ID"""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def list_projects(db: Session, owner_id: str = None, skip: int = 0, limit: int = 10):
        """List projects with optional owner filter"""
        query = db.query(Project)
        if owner_id:
            query = query.filter(Project.owner_id == owner_id)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_project_status(db: Session, project_id: str, status: ProjectStatus):
        """Update project status"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = status
            if status == ProjectStatus.COMPLETED:
                project.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: str):
        """Delete project"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            db.delete(project)
            db.commit()
        return project


class TaskService:
    """Task database operations"""

    @staticmethod
    def create_task(db: Session, title: str, project_id: str, description: str = None, agent_type: AgentType = None, context: dict = None):
        """Create a new task"""
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            project_id=project_id,
            agent_type=agent_type,
            context=context,
            status=TaskStatus.PENDING
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_task(db: Session, task_id: str):
        """Get task by ID"""
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def list_tasks(db: Session, project_id: str = None, status: TaskStatus = None, skip: int = 0, limit: int = 10):
        """List tasks with optional filters"""
        query = db.query(Task)
        if project_id:
            query = query.filter(Task.project_id == project_id)
        if status:
            query = query.filter(Task.status == status)
        return query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_task_status(db: Session, task_id: str, status: TaskStatus):
        """Update task status"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = status
            if status == TaskStatus.IN_PROGRESS:
                task.started_at = datetime.utcnow()
            elif status == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
                task.progress = 100.0
            db.commit()
            db.refresh(task)
        return task

    @staticmethod
    def update_task_progress(db: Session, task_id: str, progress: float, result: dict = None):
        """Update task progress and optionally result"""
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.progress = min(progress, 100.0)
            if result:
                task.result = result
            db.commit()
            db.refresh(task)
        return task


class AgentService:
    """Agent database operations"""

    @staticmethod
    def create_agent(db: Session, name: str, agent_type: AgentType):
        """Create a new agent"""
        agent = Agent(
            id=str(uuid.uuid4()),
            name=name,
            agent_type=agent_type,
            status="idle"
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def get_agent(db: Session, agent_id: str):
        """Get agent by ID"""
        return db.query(Agent).filter(Agent.id == agent_id).first()

    @staticmethod
    def get_agent_by_type(db: Session, agent_type: AgentType):
        """Get agent by type"""
        return db.query(Agent).filter(Agent.agent_type == agent_type).first()

    @staticmethod
    def list_agents(db: Session):
        """List all agents"""
        return db.query(Agent).all()

    @staticmethod
    def update_agent_status(db: Session, agent_id: str, status: str):
        """Update agent status"""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if agent:
            agent.status = status
            agent.last_activity = datetime.utcnow()
            db.commit()
            db.refresh(agent)
        return agent

    @staticmethod
    def increment_agent_stats(db: Session, agent_id: str, **kwargs):
        """Increment agent statistics"""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if agent:
            if 'tasks_processed' in kwargs:
                agent.tasks_processed += kwargs['tasks_processed']
            if 'files_generated' in kwargs:
                agent.files_generated += kwargs['files_generated']
            if 'components_created' in kwargs:
                agent.components_created += kwargs['components_created']
            if 'deployments' in kwargs:
                agent.deployments += kwargs['deployments']
            agent.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(agent)
        return agent
