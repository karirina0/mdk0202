"""Модель входящего объекта Task — должна соответствовать API_CONTRACT.md."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class TaskStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class IncomingTask(BaseModel):
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.NEW
    created_at: str
