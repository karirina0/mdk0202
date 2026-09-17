# Умный планировщик задач — ЛР №2 МДК 02.02

Прототип из двух микросервисов, взаимодействующих по HTTP-вебхуку:

- **task-service** — CRUD задач, порт `8000`.
- **notification-service** — приём вебхука и эмуляция уведомлений, порт `8001`.

Контракт между сервисами — `API_CONTRACT.md`. Отчёт о конфликте при слиянии — `REPORT.md`.

## Состав команды

| Участник   | Роль                          | Ветка                            |
|------------|-------------------------------|------------------------------------|
| Морозова К.А. | Архитектор / Tech Lead        | ревью PR, финальный мердж в `main` |
| Козлов И.И. | Backend Task Service          | `feature/tasks-service`            |
| Кубрак А.А. | Backend Notification Service  | `feature/notifications-service`    |

## Запуск сервисов

Каждый сервис — самостоятельное FastAPI-приложение, запускается локально.

### 1. Установить зависимости

```bash
cd task-service
pip install -r requirements.txt
```
```bash
cd notification-service
pip install -r requirements.txt
```

### 2. Запустить оба сервиса (два отдельных окна терминала)

**Терминал 1 — Notification Service:**
```bash
cd notification-service
uvicorn app.main:app --reload --port 8001
```

**Терминал 2 — Task Service:**
```bash
cd task-service
set NOTIFICATION_SERVICE_URL=http://localhost:8001
uvicorn app.main:app --reload --port 8000
```

### 3. Открыть Swagger в браузере

- Task Service: **http://127.0.0.1:8000/docs**
- Notification Service: **http://127.0.0.1:8001/docs**

Открывать нужно именно `/docs` — корень (`http://127.0.0.1:8000/`) вернёт `404`, так как отдельного обработчика для него не предусмотрено.

## Пример ручного (end-to-end) теста

1. На странице `http://127.0.0.1:8000/docs` раскрыть **POST /api/tasks** → **Try it out**.
2. Ввести в тело запроса:
   ```json
   {
     "title": "Купить билеты",
     "description": "На поезд до Москвы"
   }
   ```
3. Нажать **Execute**. Ожидаемый ответ — код **201** и полный объект задачи с заполненными `id` и `created_at`.
4. Перейти на `http://127.0.0.1:8001/docs` → раскрыть **GET /api/notifications** → **Try it out** → **Execute**.
5. В ответе должна появиться запись с уведомлением о только что созданной задаче — это подтверждает, что вебхук от Task Service дошёл до Notification Service.

Проверка отказоустойчивости: остановить Notification Service (закрыть его терминал) и повторить шаг 1–3 — ответ всё равно будет `201` (Task Service не падает), а событие появится в `GET http://127.0.0.1:8000/api/tasks/_debug/failed_events`.

## Тесты

```bash
cd task-service
pytest -v
```
```bash
cd notification-service
pytest -v
```

## Как велась совместная работа (через сайт GitHub, без терминала для git)

Все git-операции — создание веток, добавление файлов, коммиты, Pull Request'ы — выполнялись через веб-интерфейс github.com, без использования git-команд в терминале:

1. **Tech Lead** через **Add file → Upload files** в ветке `main` загрузил `API_CONTRACT.md`, `README.md`, `REPORT.md`.
2. Через переключатель веток создана ветка **`dev`** от `main`.
3. От `dev` созданы ветки **`feature/tasks-service`** и **`feature/notifications-service`** (каждым участником под своим GitHub-аккаунтом).
4. Каждый участник, находясь в своей ветке, через **Add file → Upload files** загрузил папку своего сервиса.
5. Через вкладку **Pull requests → New pull request** оба участника открыли PR: `feature/tasks-service → dev` и `feature/notifications-service → dev`.
6. Tech Lead проревьюил (**Files changed → Review changes → Approve**) и смёржил (**Merge pull request → Confirm merge**) оба PR — оба слились в `dev` без конфликтов.
7. Открыт финальный Pull Request **`dev → main`** — на этом этапе возник конфликт слияния (подробности и решение — в `REPORT.md`).
8. Конфликт разрешён встроенным редактором GitHub (**Resolve conflicts → Mark as resolved → Commit merge**).
9. PR одобрен вторым участником (**Review changes → Approve**, так как ветка `main` защищена правилом "Require a pull request before merging" с обязательным ревью) и смёржен (**Merge pull request → Confirm merge**).

Итоговая схема веток:

```
main  
 └─ dev
     ├─ feature/tasks-service          
     └─ feature/notifications-service 
```
