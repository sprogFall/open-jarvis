from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from gateway.main import create_app
from gateway.security import sign_device_request
from gateway.settings import GatewaySettings


def build_test_client(tmp_path) -> tuple[TestClient, GatewaySettings]:
    settings = GatewaySettings(
        database_url=str(tmp_path / "gateway.db"),
        jwt_secret="test-secret-test-secret-test-secret",
        admin_username="operator",
        admin_password="passw0rd",
        device_keys={"device-alpha": "device-secret"},
    )
    return TestClient(create_app(settings)), settings


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient) -> str:
    response = client.post(
        "/auth/login",
        json={"username": "operator", "password": "passw0rd"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def receive_until_task_status(websocket, status: str) -> dict:
    for _ in range(5):
        payload = websocket.receive_json()
        if payload.get("type") == "TASK_SNAPSHOT" and payload["task"]["status"] == status:
            return payload
    raise AssertionError(f"Did not receive task status {status!r}")


def wait_for_task_status(client: TestClient, token: str, task_id: str, status: str) -> dict:
    for _ in range(20):
        response = client.get(f"/tasks/{task_id}", headers=auth_headers(token))
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] == status:
            return payload
        time.sleep(0.05)
    raise AssertionError(f"Task {task_id!r} did not reach status {status!r}")


def test_task_lifecycle_routes_interrupts_and_approval(tmp_path):
    client, settings = build_test_client(tmp_path)
    token = login(client)
    timestamp = 1700000000
    signature = sign_device_request(
        device_id="device-alpha",
        timestamp=timestamp,
        device_key=settings.device_keys["device-alpha"],
    )

    with client.websocket_connect(
        f"/ws/client?device_id=device-alpha&timestamp={timestamp}&signature={signature}"
    ) as device_ws:
        with client.websocket_connect(f"/ws/app?token={token}") as app_ws:
            create_response = client.post(
                "/tasks",
                headers=auth_headers(token),
                json={
                    "device_id": "device-alpha",
                    "instruction": "查看系统负载，然后重启容器 api-service",
                },
            )
            assert create_response.status_code == 201
            created_task = create_response.json()
            assert created_task["status"] == "PENDING_DISPATCH"
            create_snapshot = app_ws.receive_json()
            assert create_snapshot["type"] == "TASK_SNAPSHOT"
            assert create_snapshot["task"]["status"] == "PENDING_DISPATCH"

            task_assignment = device_ws.receive_json()
            assert task_assignment["type"] == "TASK_ASSIGNED"
            task_id = task_assignment["task"]["task_id"]

            device_ws.send_json(
                {
                    "type": "TASK_STATUS",
                    "task_id": task_id,
                    "status": "RUNNING",
                }
            )
            running_task = wait_for_task_status(client, token, task_id, "RUNNING")
            assert running_task["task_id"] == task_id

            device_ws.send_json(
                {
                    "type": "INTERRUPT_REQUEST",
                    "task_id": task_id,
                    "checkpoint_id": "cp_001",
                    "command": "docker restart api-service",
                    "reason": "重启容器会打断服务，需要人工确认",
                }
            )
            approval_task = wait_for_task_status(client, token, task_id, "AWAITING_APPROVAL")
            assert approval_task["command"] == "docker restart api-service"

            pending_response = client.get(
                "/tasks/pending_approvals",
                headers=auth_headers(token),
            )
            assert pending_response.status_code == 200
            assert pending_response.json() == [
                {
                    "task_id": task_id,
                    "device_id": "device-alpha",
                    "instruction": "查看系统负载，然后重启容器 api-service",
                    "status": "AWAITING_APPROVAL",
                    "checkpoint_id": "cp_001",
                    "command": "docker restart api-service",
                    "reason": "重启容器会打断服务，需要人工确认",
                    "result": None,
                    "error": None,
                    "logs": [],
                }
            ]

            decision_response = client.post(
                f"/tasks/{task_id}/decision",
                headers=auth_headers(token),
                json={"approved": True},
            )
            assert decision_response.status_code == 202
            assert decision_response.json()["status"] == "APPROVED"
            approved_task = wait_for_task_status(client, token, task_id, "APPROVED")
            assert approved_task["task_id"] == task_id

            decision_message = device_ws.receive_json()
            assert decision_message == {
                "type": "APPROVAL_DECISION",
                "task_id": task_id,
                "approved": True,
            }


def test_pending_approval_is_restored_after_app_reconnect(tmp_path):
    client, settings = build_test_client(tmp_path)
    token = login(client)
    timestamp = 1700000001
    signature = sign_device_request(
        device_id="device-alpha",
        timestamp=timestamp,
        device_key=settings.device_keys["device-alpha"],
    )

    with client.websocket_connect(
        f"/ws/client?device_id=device-alpha&timestamp={timestamp}&signature={signature}"
    ) as device_ws:
        create_response = client.post(
            "/tasks",
            headers=auth_headers(token),
            json={
                "device_id": "device-alpha",
                "instruction": "查看系统负载，然后重启容器 api-service",
            },
        )
        task_id = create_response.json()["task_id"]
        device_ws.receive_json()
        device_ws.send_json(
            {
                "type": "INTERRUPT_REQUEST",
                "task_id": task_id,
                "checkpoint_id": "cp_restore",
                "command": "docker restart api-service",
                "reason": "需要用户确认",
            }
        )

    pending_response = client.get(
        "/tasks/pending_approvals",
        headers=auth_headers(token),
    )
    assert pending_response.status_code == 200
    assert pending_response.json()[0]["task_id"] == task_id
    assert pending_response.json()[0]["status"] == "AWAITING_APPROVAL"


def test_rejects_invalid_client_signature(tmp_path):
    client, _settings = build_test_client(tmp_path)

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            "/ws/client?device_id=device-alpha&timestamp=1700000000&signature=bad"
        ):
            pass


def test_rejects_invalid_app_token(tmp_path):
    client, _settings = build_test_client(tmp_path)

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/app?token=bad-token"):
            pass
