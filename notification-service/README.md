# Notification Service

Принимает вебхук о создании задачи и эмулирует отправку уведомления
записью в лог/консоль, согласно `API_CONTRACT.md`.

## Запуск

```bash
cd notification-service
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Документация Swagger: http://localhost:8001/docs

## Тесты

```bash
pytest -v
```

## Локальные точки отказа

1. **Некорректный/неполный payload** (например, без `id`) → Pydantic
   возвращает `422`, уведомление не создаётся и не логируется.
2. **Повторная доставка одного и того же события** (например, если Task
   Service переотправил вебхук после таймаута) — обрабатывается
   дедупликацией по `task.id` в памяти (`_seen_task_ids`), чтобы
   пользователь не получил одно и то же уведомление дважды.
3. **Хранилище уведомлений — в памяти**, при перезапуске сервиса журнал
   `sent_notifications` очищается.
