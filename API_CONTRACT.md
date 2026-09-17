# API Contract — «Умный планировщик задач»

Версия: 1.1 (согласована после разрешения конфликта на Этапе 4, см. REPORT.md)

## 1. Схема данных `Task`

| Поле          | Тип                                   | Описание                              |
|---------------|----------------------------------------|----------------------------------------|
| `id`          | string (UUID v4)                       | Генерируется Task Service              |
| `title`       | string                                  | Обязательное, не пустое                |
| `description` | string                                  | Необязательное, по умолчанию `""`      |
| `status`      | enum: `new`, `in_progress`, `done`      | По умолчанию `new`                     |
| `created_at`  | string (ISO 8601, UTC)                  | Генерируется Task Service              |

Пример:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "title": "Купить билеты",
  "description": "На поезд до Москвы",
  "status": "new",
  "created_at": "2026-09-17T10:15:30.123456+00:00"
}
```

## 2. Endpoint 1 — Task Service

`POST /api/tasks`

Запрос (без `id` и `created_at`):
```json
{
  "title": "Купить билеты",
  "description": "На поезд до Москвы",
  "status": "new"
}
```
- `title` — обязательное поле. Если отсутствует/пустое → `422 Unprocessable Entity`.
- `description`, `status` — необязательные.

Ответ: `201 Created`, тело — полный объект `Task` (см. п.1).

Дополнительно реализованы (для полноты CRUD согласно легенде проекта):
- `GET /api/tasks` — список всех задач, `200 OK`.
- `GET /api/tasks/{id}` — одна задача, `200 OK` / `404 Not Found`.
- `PUT /api/tasks/{id}` — обновление задачи, `200 OK` / `404 Not Found`.
- `DELETE /api/tasks/{id}` — удаление, `204 No Content` / `404 Not Found`.

## 3. Endpoint 2 — Notification Service

`POST /api/webhooks/task_created`

Запрос — тело объекта `Task` целиком (см. п.1, п.4).

Ответ: `200 OK`
```json
{ "received": true }
```

При некорректном теле запроса → `422 Unprocessable Entity`, уведомление не создаётся.

## 4. Формат вебхука Task Service → Notification Service

Task Service отправляет **весь объект Task** (созданный, со всеми полями из п.1) синхронным HTTP POST-запросом на:

```
POST {NOTIFICATION_SERVICE_URL}/api/webhooks/task_created
Content-Type: application/json
```

Тело идентично ответу на `POST /api/tasks` (см. п.2).

### Обработка ошибок доставки (Task Service)

Если Notification Service недоступен или возвращает код ≥ 400:
1. Выполняется до **3 повторных попыток** с экспоненциальной задержкой (0.5s, 1s, 2s).
2. Если все попытки неудачны — событие кладётся в **очередь в памяти** (`failed_events`) и пишется запись в лог с уровнем `WARNING`.
3. Сам Task Service при этом **не падает** и продолжает отвечать `201 Created` клиенту — создание задачи не должно зависеть от доступности Notification Service (эта точка отказа задокументирована в `task-service/README.md`).
