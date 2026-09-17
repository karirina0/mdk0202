# Умный планировщик задач — ЛР №2 МДК 02.02

Прототип из двух микросервисов, взаимодействующих по HTTP-вебхуку:

- **task-service** — CRUD задач, порт `8000`.
- **notification-service** — приём вебхука и эмуляция уведомлений, порт `8001`.

Контракт между сервисами — `API_CONTRACT.md`.

## Быстрый запуск обоих сервисов

Открыть два терминала:

```bash
# Терминал 1
cd notification-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

```bash
# Терминал 2
cd task-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export NOTIFICATION_SERVICE_URL=http://localhost:8001
uvicorn app.main:app --reload --port 8000
```

## Ручное end-to-end тестирование (Этап 4, п.6 задания)

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Купить билеты", "description": "На поезд до Москвы"}'
```

Ожидаемо:
1. Ответ `201 Created` с полным объектом задачи (`id`, `created_at` заполнены).
2. В логе `task-service` — строка `webhook delivered task_id=... attempt=1`.
3. В логе `notification-service` — строка `NOTIFICATION: Новая задача «Купить билеты» создана...`.
4. Проверить журнал уведомлений:
   ```bash
   curl http://localhost:8001/api/notifications
   ```

Проверка отказоустойчивости — выключите `notification-service` и повторите
`curl POST /api/tasks`: ответ всё равно будет `201`, а событие появится в
`GET http://localhost:8000/api/tasks/_debug/failed_events`.

## Тесты

```bash
cd task-service && pytest -v
cd ../notification-service && pytest -v
```

## Git-flow, использованный в команде

```
main  (защищена, только через PR)
 └─ dev
     ├─ feature/tasks-service          (Backend Task Service)
     └─ feature/notifications-service  (Backend Notification Service)
```

1. Обе feature-ветки созданы от `dev` на Этапе 2, сразу после утверждения
   `API_CONTRACT.md`.
2. Каждый разработчик коммитит в свою ветку и открывает PR в `dev`.
3. Tech Lead ревьюит оба PR на соответствие контракту.
4. Первый одобренный PR мерджится в `dev` первым.
5. Второй разработчик выполняет `git pull origin dev`, получает конфликт
   (см. `REPORT.md`), разрешает его вместе с командой, дозаливает.
6. Финальный PR `dev → main` — после успешного end-to-end теста.

Подробности конфликта и принятых решений — см. `REPORT.md`.
