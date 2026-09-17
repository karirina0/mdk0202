"""Notification Service — согласно API_CONTRACT.md.

Эмулирует отправку уведомления пользователю записью в лог/консоль.

Запуск:
    uvicorn app.main:app --reload --port 8001
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, status

from app.models import IncomingTask

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification_service")

app = FastAPI(title="Notification Service", version="1.0.0")

# Журнал "отправленных" уведомлений в памяти — для проверки в ЛР и в тестах.
sent_notifications: list[dict] = []

# Простая дедупликация повторно доставленных вебхуков по id задачи
# (см. task-service/README.md, п.3 "нет идемпотентности").
_seen_task_ids: set[str] = set()


@app.post("/api/webhooks/task_created", status_code=status.HTTP_200_OK)
async def task_created(task: IncomingTask) -> dict:
    if task.id in _seen_task_ids:
        logger.info("duplicate notification ignored task_id=%s", task.id)
        return {"received": True, "duplicate": True}

    _seen_task_ids.add(task.id)
    notification = {
        "task_id": task.id,
        "message": f"Новая задача «{task.title}» создана (статус: {task.status.value})",
    }
    sent_notifications.append(notification)

    # Эмуляция отправки уведомления — запись в лог/консоль.
    logger.info("NOTIFICATION: %s", notification["message"])

    return {"received": True}


@app.get("/api/notifications")
async def list_notifications() -> list[dict]:
    """Вспомогательный эндпоинт для лабораторной: посмотреть, что было 'отправлено'."""
    return sent_notifications
