from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from gateway.main import create_app
from gateway.security import sign_device_request
from gateway.settings import GatewaySettings
from gateway.store import GatewayStore


def build_settings(db_path, device_keys: dict[str, str] | None = None) -> GatewaySettings:
    return GatewaySettings(
        database_url=str(db_path),
        jwt_secret="test-secret-test-secret-test-secret",
        admin_username="operator",
        admin_password="passw0rd",
        device_keys=device_keys or {"device-alpha": "device-secret"},
    )


def login(client: TestClient) -> str:
    response = client.post(
        "/auth/login",
        json={"username": "operator", "password": "passw0rd"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_store_migrates_legacy_tasks_table(tmp_path):
    db_path = tmp_path / "gateway.db"
    connection = sqlite3.connect(db_path)
    connection.execute(
        """
        CREATE TABLE tasks (
            task_id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            instruction TEXT NOT NULL,
            status TEXT NOT NULL,
            checkpoint_id TEXT,
            command TEXT,
            reason TEXT,
            result TEXT,
            error TEXT,
            logs_json TEXT NOT NULL DEFAULT '[]'
        )
        """
    )
    connection.execute(
        """
        INSERT INTO tasks (
            task_id, device_id, instruction, status, checkpoint_id,
            command, reason, result, error, logs_json
        )
        VALUES (?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, '[]')
        """,
        ("legacy-task", "device-alpha", "旧任务", "AWAITING_APPROVAL"),
    )
    connection.commit()
    connection.close()

    store = GatewayStore(str(db_path))

    created = store.create_task("new-task", "device-alpha", "新任务")
    pending = store.list_pending_approvals()

    assert created["task_id"] == "new-task"
    assert [task["task_id"] for task in pending] == ["legacy-task"]


def test_dashboard_created_device_survives_restart(tmp_path):
    db_path = tmp_path / "gateway.db"
    first_client = TestClient(create_app(build_settings(db_path)))
    first_token = login(first_client)
    create_response = first_client.post(
        "/dashboard/api/devices",
        headers=auth_headers(first_token),
        json={
            "device_id": "device-bravo",
            "name": "Bravo",
            "type": "cli",
            "device_key": "bravo-secret",
        },
    )
    assert create_response.status_code == 201
    first_client.close()

    restarted_client = TestClient(create_app(build_settings(db_path)))
    restarted_token = login(restarted_client)
    timestamp = 1700000100
    signature = sign_device_request("device-bravo", timestamp, "bravo-secret")

    with restarted_client.websocket_connect(
        f"/ws/client?device_id=device-bravo&timestamp={timestamp}&signature={signature}"
    ) as device_ws:
        task_response = restarted_client.post(
            "/tasks",
            headers=auth_headers(restarted_token),
            json={"device_id": "device-bravo", "instruction": "执行一次重启后的任务"},
        )
        assert task_response.status_code == 201
        skill_sync = device_ws.receive_json()
        assert skill_sync["type"] == "DEVICE_SKILLS_SYNC"
        assert skill_sync["skills"] == []
        assignment = device_ws.receive_json()
        assert assignment["type"] == "TASK_ASSIGNED"
        assert assignment["task"]["device_id"] == "device-bravo"

    restarted_client.close()


def test_deleted_env_device_is_not_reseeded_on_restart(tmp_path):
    db_path = tmp_path / "gateway.db"
    first_client = TestClient(
        create_app(build_settings(db_path, {"device-alpha": "device-secret"}))
    )
    first_token = login(first_client)
    delete_response = first_client.delete(
        "/dashboard/api/devices/device-alpha",
        headers=auth_headers(first_token),
    )
    assert delete_response.status_code == 204
    first_client.close()

    restarted_client = TestClient(
        create_app(build_settings(db_path, {"device-alpha": "device-secret"}))
    )
    restarted_token = login(restarted_client)

    list_response = restarted_client.get(
        "/dashboard/api/devices",
        headers=auth_headers(restarted_token),
    )
    assert list_response.status_code == 200
    assert list_response.json() == []

    task_response = restarted_client.post(
        "/tasks",
        headers=auth_headers(restarted_token),
        json={"device_id": "device-alpha", "instruction": "不应重新出现"},
    )
    assert task_response.status_code == 404
    restarted_client.close()


def test_rotated_env_device_key_persists_across_restart(tmp_path):
    db_path = tmp_path / "gateway.db"
    first_client = TestClient(
        create_app(build_settings(db_path, {"device-alpha": "device-secret"}))
    )
    first_token = login(first_client)
    update_response = first_client.put(
        "/dashboard/api/devices/device-alpha",
        headers=auth_headers(first_token),
        json={"device_key": "rotated-secret"},
    )
    assert update_response.status_code == 200
    first_client.close()

    restarted_client = TestClient(
        create_app(build_settings(db_path, {"device-alpha": "device-secret"}))
    )
    rotated_timestamp = 1700000101
    rotated_signature = sign_device_request(
        "device-alpha",
        rotated_timestamp,
        "rotated-secret",
    )
    with restarted_client.websocket_connect(
        f"/ws/client?device_id=device-alpha&timestamp={rotated_timestamp}&signature={rotated_signature}"
    ):
        pass

    stale_timestamp = 1700000102
    stale_signature = sign_device_request(
        "device-alpha",
        stale_timestamp,
        "device-secret",
    )
    with pytest.raises(WebSocketDisconnect):
        with restarted_client.websocket_connect(
            f"/ws/client?device_id=device-alpha&timestamp={stale_timestamp}&signature={stale_signature}"
        ):
            pass

    restarted_client.close()


def test_from_env_reads_legacy_gateway_db_variable(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("OMNI_AGENT_GATEWAY_DB", "gateway/legacy.db")

    settings = GatewaySettings.from_env()

    assert settings.database_url == "gateway/legacy.db"
