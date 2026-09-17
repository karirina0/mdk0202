"""Модели данных Task Service — согласно API_CONTRACT.md, раздел 1."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    """Тело запроса POST /api/tasks — без id и created_at."""

    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.NEW

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title must not be empty")
        return v


class TaskUpdate(BaseModel):
    """Тело запроса PUT /api/tasks/{id} — частичное обновление."""

    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None


class Task(BaseModel):
    """Полный объект задачи, возвращаемый клиенту и отправляемый в вебхуке."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.NEW
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
