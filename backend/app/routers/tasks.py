"""Tasks router — CRUD for auto-generated and manual tasks."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task_generator import generate_tasks_for_user

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

VALID_STATUSES = {"pending", "completed", "dismissed"}


def _task_to_response(task: Task) -> TaskResponse:
    """Convert a Task ORM model to a TaskResponse."""
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        source=task.source,
        status=task.status,
        container_id=task.container_id,
        planting_id=task.planting_id,
        variety_id=task.variety_id,
        container_name=task.container.name if task.container else None,
        variety_name=task.variety.name if task.variety else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    task_status: str | None = Query(default=None, alias="status", description="Filter by status"),
    source: str | None = Query(default=None, description="Filter by source (auto/manual)"),
    start_date: date | None = Query(default=None, description="Due date range start"),
    end_date: date | None = Query(default=None, description="Due date range end"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tasks for the current user with optional filters."""
    stmt = (
        select(Task)
        .options(selectinload(Task.container), selectinload(Task.variety))
        .where(Task.user_id == current_user.id)
        .order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
    )

    if task_status:
        stmt = stmt.where(Task.status == task_status)
    if source:
        stmt = stmt.where(Task.source == source)
    if start_date:
        stmt = stmt.where(Task.due_date >= start_date)
    if end_date:
        stmt = stmt.where(Task.due_date <= end_date)

    result = await db.execute(stmt)
    tasks = result.scalars().all()
    return [_task_to_response(t) for t in tasks]


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a manual task."""
    task = Task(
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        due_date=body.due_date,
        source="manual",
        container_id=body.container_id,
        planting_id=body.planting_id,
        variety_id=body.variety_id,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    # Re-fetch with relationships
    stmt = (
        select(Task)
        .options(selectinload(Task.container), selectinload(Task.variety))
        .where(Task.id == task.id)
    )
    result = await db.execute(stmt)
    task = result.scalar_one()
    return _task_to_response(task)


@router.get("/generate", response_model=dict)
async def trigger_task_generation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually trigger task auto-generation for the current user."""
    count = await generate_tasks_for_user(db, current_user.id)
    return {"generated": count}


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single task by ID."""
    stmt = (
        select(Task)
        .options(selectinload(Task.container), selectinload(Task.variety))
        .where(Task.id == task_id, Task.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return _task_to_response(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    body: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a task (change status, edit details)."""
    stmt = (
        select(Task)
        .options(selectinload(Task.container), selectinload(Task.variety))
        .where(Task.id == task_id, Task.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    update_data = body.model_dump(exclude_unset=True)

    if "status" in update_data and update_data["status"] not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    for field, value in update_data.items():
        setattr(task, field, value)

    await db.flush()
    await db.refresh(task)
    return _task_to_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a task."""
    stmt = select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await db.delete(task)
