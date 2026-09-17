"""Тесты Notification Service.

Основной сценарий (обязателен по заданию): приём вебхука о созданной задаче
и фиксация уведомления. Плюс проверки обработки некорректных данных и
дедупликации повторной доставки.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app, sent_notifications, _seen_task_ids

VALID_TASK = {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "title": "Купить билеты",
    "description": "На поезд",
    "status": "new",
    "created_at": "2026-09-17T10:15:30.123456+00:00",
}


@pytest.fixture(autouse=True)
def clear_state():
    sent_notifications.clear()
    _seen_task_ids.clear()
    yield
    sent_notifications.clear()
    _seen_task_ids.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_webhook_accepts_valid_task_and_records_notification(client):
    response = client.post("/api/webhooks/task_created", json=VALID_TASK)

    assert response.status_code == 200
    assert response.json() == {"received": True}
    assert len(sent_notifications) == 1
    assert VALID_TASK["title"] in sent_notifications[0]["message"]


def test_webhook_rejects_invalid_payload(client):
    invalid = {"title": "Без id и без даты"}
    response = client.post("/api/webhooks/task_created", json=invalid)
    assert response.status_code == 422
    assert len(sent_notifications) == 0


def test_webhook_duplicate_delivery_is_ignored(client):
    first = client.post("/api/webhooks/task_created", json=VALID_TASK)
    second = client.post("/api/webhooks/task_created", json=VALID_TASK)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json().get("duplicate") is True
    assert len(sent_notifications) == 1  # не задублировалось


def test_list_notifications_endpoint(client):
    client.post("/api/webhooks/task_created", json=VALID_TASK)
    response = client.get("/api/notifications")
    assert response.status_code == 200
    assert len(response.json()) == 1
