"""Task Service — согласно API_CONTRACT.md.

Запуск:
    uvicorn app.main:app --reload --port 8000

Переменная окружения:
    NOTIFICATION_SERVICE_URL (по умолчанию http://localhost:8001)
"""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException, status

from app.models import Task, TaskCreate, TaskUpdate
from app.webhook_client import failed_events, send_task_created_webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("task_service")

NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8001")

app = FastAPI(title="Task Service", version="1.0.0")

# Хранилище задач в памяти: id -> Task
_tasks: dict[str, Task] = {}


@app.post("/api/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate) -> Task:
    task = Task(
        title=payload.title,
        description=payload.description,
        status=payload.status,
    )
    _tasks[task.id] = task
    logger.info("task created id=%s title=%r", task.id, task.title)

    # Уведомляем Notification Service. Неудача не должна ронять запрос клиента.
    await send_task_created_webhook(task, NOTIFICATION_SERVICE_URL)

    return task


@app.get("/api/tasks", response_model=list[Task])
async def list_tasks() -> list[Task]:
    return list(_tasks.values())


@app.get("/api/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str) -> Task:
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/api/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, payload: TaskUpdate) -> Task:
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = payload.model_dump(exclude_unset=True)
    updated = task.model_copy(update=update_data)
    _tasks[task_id] = updated
    return updated


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str) -> None:
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del _tasks[task_id]


@app.get("/api/tasks/_debug/failed_events")
async def get_failed_events() -> list[dict]:
    """Вспомогательный эндпоинт для лабораторной: посмотреть очередь недоставленных вебхуков."""
    return list(failed_events)
