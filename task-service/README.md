# Task Service

Реализует создание, чтение, обновление и удаление задач согласно `API_CONTRACT.md`.

## Запуск

```bash
cd task-service
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export NOTIFICATION_SERVICE_URL=http://localhost:8001   # Windows: set NOTIFICATION_SERVICE_URL=...
uvicorn app.main:app --reload --port 8000
```

Документация Swagger: http://localhost:8000/docs

## Тесты

```bash
pytest -v
```

## Локальные точки отказа (документация, п.5 Этапа 3)

1. **Notification Service недоступен или отвечает ошибкой.**
   Реализовано 3 повторные попытки с экспоненциальной задержкой
   (`app/webhook_client.py`). После исчерпания попыток событие сохраняется
   в очередь `failed_events` в памяти и пишется `WARNING` в лог — сам запрос
   создания задачи клиенту при этом всё равно завершается `201 Created`.
   Посмотреть очередь: `GET /api/tasks/_debug/failed_events`.

2. **Хранилище данных — в памяти.** При перезапуске сервиса все задачи
   теряются. Для продакшена нужна БД (Postgres/SQLite); вне рамок ЛР.

3. **Нет идемпотентности при повторной отправке вебхука.** Если Task Service
   перезапустится ровно между отправкой запроса и получением ответа,
   возможна повторная доставка одного и того же события. Notification
   Service должен уметь безопасно обработать дубликат (см. его README).

4. **Нет аутентификации между сервисами.** В рамках ЛР эндпоинты открыты;
   в реальной системе нужен внутренний токен/mTLS.
