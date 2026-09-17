"""Отправка вебхука в Notification Service с обработкой ошибок.

Точка отказа (задокументировано в README.md):
Notification Service может быть недоступен или отвечать ошибкой.
Task Service не должен падать и не должен блокировать создание задачи
из-за проблем на стороне Notification Service.
"""
from __future__ import annotations

import asyncio
import logging
from collections import deque

import httpx

from app.models import Task

logger = logging.getLogger("task_service.webhook")

MAX_RETRIES = 3
BASE_DELAY_SECONDS = 0.5

# Очередь неудачных событий в памяти (пункт 4 контракта).
# В реальной системе здесь была бы персистентная очередь сообщений.
failed_events: deque[dict] = deque(maxlen=1000)


async def send_task_created_webhook(task: Task, notification_url: str) -> bool:
    """Пытается доставить событие о создании задачи.

    Возвращает True, если доставлено успешно, False — если ушло в очередь отказов.
    Никогда не выбрасывает исключение наружу.
    """
    payload = task.model_dump()
    url = f"{notification_url.rstrip('/')}/api/webhooks/task_created"

    async with httpx.AsyncClient(timeout=3.0) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.post(url, json=payload)
                if response.status_code < 400:
                    logger.info(
                        "webhook delivered task_id=%s attempt=%d", task.id, attempt
                    )
                    return True
                logger.warning(
                    "webhook rejected task_id=%s attempt=%d status=%d",
                    task.id,
                    attempt,
                    response.status_code,
                )
            except httpx.HTTPError as exc:
                logger.warning(
                    "webhook delivery failed task_id=%s attempt=%d error=%s",
                    task.id,
                    attempt,
                    exc,
                )

            if attempt < MAX_RETRIES:
                await asyncio.sleep(BASE_DELAY_SECONDS * (2 ** (attempt - 1)))

    # Все попытки исчерпаны — не роняем сервис, логируем и складываем в очередь.
    logger.warning(
        "webhook giving up after %d attempts, queued task_id=%s", MAX_RETRIES, task.id
    )
    failed_events.append(payload)
    return False
