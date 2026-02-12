"""
Task management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from app.database.config import get_db
from app.database.models import Task, Project, User
from app.auth.dependencies import get_current_user
from app.websockets.manager import manager
from pydantic import BaseModel, Field

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    project_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new task"""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == task_data.project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    task = Task(
        id=str(uuid4()),
        project_id=task_data.project_id,
        title=task_data.title,
        description=task_data.description,
        status='pending',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    await manager.broadcast_to_room(
        room_id=f"project:{task.project_id}",
        message={
            "type": "task_created",
            "task": TaskResponse.from_orm(task).model_dump(),
            "project_id": task.project_id,
        },
    )
    return TaskResponse.from_orm(task)


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """List tasks with optional filtering"""
    query = db.query(Task).join(Project).filter(
        Project.owner_id == current_user.id
    )
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    tasks = query.offset(skip).limit(limit).all()
    return [TaskResponse.from_orm(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get task by ID"""
    task = db.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.from_orm(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    update_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task"""
    task = db.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if update_data.title:
        task.title = update_data.title
    if update_data.description is not None:
        task.description = update_data.description
    if update_data.status:
        task.status = update_data.status
    
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    await manager.broadcast_to_room(
        room_id=f"project:{task.project_id}",
        message={
            "type": "task_updated",
            "task": TaskResponse.from_orm(task).model_dump(),
            "project_id": task.project_id,
        },
    )
    return TaskResponse.from_orm(task)


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete task"""
    task = db.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    project_id = task.project_id
    task_id_to_delete = task.id
    db.delete(task)
    db.commit()
    await manager.broadcast_to_room(
        room_id=f"project:{project_id}",
        message={
            "type": "task_deleted",
            "task_id": task_id_to_delete,
            "project_id": project_id,
        },
    )
    return {"message": "Task deleted successfully"}


@router.post("/{task_id}/status/{new_status}")
async def update_task_status(
    task_id: str,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task status"""
    valid_statuses = ['pending', 'running', 'completed', 'failed']
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
    
    task = db.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = new_status
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    await manager.broadcast_to_room(
        room_id=f"project:{task.project_id}",
        message={
            "type": "task_status_updated",
            "task": TaskResponse.from_orm(task).model_dump(),
            "project_id": task.project_id,
        },
    )
    return TaskResponse.from_orm(task)
