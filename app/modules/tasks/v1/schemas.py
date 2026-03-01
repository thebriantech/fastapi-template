from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskCreate(BaseModel):
    title: str
    description: str
    status: TaskStatus = TaskStatus.TODO
    assignee: str


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    assignee: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    title: str
    description: str
    status: TaskStatus
    assignee: str
