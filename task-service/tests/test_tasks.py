"""Тесты Task Service.

Основной сценарий (обязателен по заданию): создание задачи и корректный
вызов вебхука Notification Service. Плюс базовые проверки CRUD и обработки
ошибок доставки, чтобы показать, что сервис не падает при недоступном
Notification Service (задокументированная точка отказа).
"""
import respx
import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app, NOTIFICATION_SERVICE_URL
from app.webhook_client import failed_events


@pytest.fixture(autouse=True)
def clear_failed_events():
    failed_events.clear()
    yield
    failed_events.clear()


@pytest.fixture
def client():
    return TestClient(app)


@respx.mock
def test_create_task_success_and_webhook_called(client):
    """Основной сценарий: POST /api/tasks -> 201, вебхук уходит в Notification Service."""
    webhook_route = respx.post(
        f"{NOTIFICATION_SERVICE_URL}/api/webhooks/task_created"
    ).mock(return_value=httpx.Response(200, json={"received": True}))

    response = client.post(
        "/api/tasks",
        json={"title": "Купить билеты", "description": "На поезд"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Купить билеты"
    assert body["status"] == "new"
    assert "id" in body and "created_at" in body

    assert webhook_route.called
    assert webhook_route.calls.last.request.method == "POST"


def test_create_task_without_title_returns_422(client):
    response = client.post("/api/tasks", json={"description": "нет заголовка"})
    assert response.status_code == 422


@respx.mock
def test_create_task_when_notification_service_down_does_not_fail(client):
    """Notification Service недоступен -> Task Service всё равно возвращает 201
    и кладёт событие в очередь отказов, а не падает."""
    respx.post(f"{NOTIFICATION_SERVICE_URL}/api/webhooks/task_created").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    response = client.post("/api/tasks", json={"title": "Задача без связи"})

    assert response.status_code == 201
    assert len(failed_events) == 1
    assert failed_events[0]["title"] == "Задача без связи"


def test_list_get_update_delete_task_flow(client):
    with respx.mock:
        respx.post(f"{NOTIFICATION_SERVICE_URL}/api/webhooks/task_created").mock(
            return_value=httpx.Response(200, json={"received": True})
        )
        created = client.post("/api/tasks", json={"title": "Тестовая задача"}).json()

    task_id = created["id"]

    # GET list
    assert len(client.get("/api/tasks").json()) == 1

    # GET by id
    got = client.get(f"/api/tasks/{task_id}")
    assert got.status_code == 200
    assert got.json()["id"] == task_id

    # PUT update
    updated = client.put(f"/api/tasks/{task_id}", json={"status": "done"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"

    # DELETE
    deleted = client.delete(f"/api/tasks/{task_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/tasks/{task_id}").status_code == 404
