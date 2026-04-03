from __future__ import annotations

import io
import time
import zipfile

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


def build_skill_archive(skill_id: str, *, root: str = "skill") -> bytes:
    archive = io.BytesIO()
    prefix = f"{root.strip('/')}/"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(
            f"{prefix}SKILL.md",
            (
                "---\n"
                f"name: {skill_id}\n"
                "description: test skill\n"
                "---\n\n"
                "Hello.\n"
            ),
        )
        bundle.writestr(f"{prefix}references/guide.md", "# Guide\n")
    return archive.getvalue()


def receive_until_task_status(websocket, status: str) -> dict:
    for _ in range(5):
        payload = websocket.receive_json()
        if payload.get("type") == "TASK_SNAPSHOT" and payload["task"]["status"] == status:
            return payload
    raise AssertionError(f"Did not receive task status {status!r}")


def receive_until_message_type(websocket, message_type: str) -> dict:
    for _ in range(6):
        payload = websocket.receive_json()
        if payload.get("type") == message_type:
            return payload
    raise AssertionError(f"Did not receive message type {message_type!r}")


def receive_until_non_empty_skill_sync(websocket) -> dict:
    for _ in range(6):
        payload = websocket.receive_json()
        if payload.get("type") == "DEVICE_SKILLS_SYNC" and payload.get("skills"):
            return payload
    raise AssertionError("Did not receive a non-empty skill sync")


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

            skill_sync = receive_until_message_type(device_ws, "DEVICE_SKILLS_SYNC")
            assert skill_sync["skills"] == []
            task_assignment = receive_until_message_type(device_ws, "TASK_ASSIGNED")
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
        skill_sync = receive_until_message_type(device_ws, "DEVICE_SKILLS_SYNC")
        assert skill_sync["skills"] == []
        receive_until_message_type(device_ws, "TASK_ASSIGNED")
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


def test_connected_device_receives_skill_sync_and_can_download_archive(tmp_path):
    client, settings = build_test_client(tmp_path)
    token = login(client)
    client.post(
        "/dashboard/api/skills",
        headers=auth_headers(token),
        json={"skill_id": "incident-kit", "name": "Incident Kit"},
    )
    archive = build_skill_archive("incident-kit", root="skills/incident-kit")
    upload_response = client.put(
        "/dashboard/api/skills/incident-kit/archive",
        headers={
            **auth_headers(token),
            "Content-Type": "application/zip",
            "X-Skill-Archive-Name": "incident-kit.zip",
        },
        content=archive,
    )
    assert upload_response.status_code == 200

    timestamp = 1700000002
    signature = sign_device_request(
        device_id="device-alpha",
        timestamp=timestamp,
        device_key=settings.device_keys["device-alpha"],
    )

    with client.websocket_connect(
        f"/ws/client?device_id=device-alpha&timestamp={timestamp}&signature={signature}"
    ) as device_ws:
        assign_response = client.post(
            "/dashboard/api/devices/device-alpha/skills",
            headers=auth_headers(token),
            json={"skill_id": "incident-kit", "config": {"workspace": ".codex/skills"}},
        )
        assert assign_response.status_code == 201

        empty_sync = receive_until_message_type(device_ws, "DEVICE_SKILLS_SYNC")
        assert empty_sync["skills"] == []
        sync_payload = receive_until_non_empty_skill_sync(device_ws)
        assert sync_payload["type"] == "DEVICE_SKILLS_SYNC"
        assert sync_payload["device_id"] == "device-alpha"
        assert sync_payload["skills"] == [
            {
                "skill_id": "incident-kit",
                "name": "Incident Kit",
                "description": "",
                "source": "archive",
                "action_names": [],
                "assigned_at": assign_response.json()["assigned_at"],
                "config": {"workspace": ".codex/skills"},
                "skill_config": {},
                "archive_filename": "incident-kit.zip",
                "archive_sha256": upload_response.json()["archive_sha256"],
                "archive_size": len(archive),
                "archive_updated_at": upload_response.json()["archive_updated_at"],
                "archive_ready": True,
                "download_path": "/client/skills/incident-kit/archive",
            }
        ]

        download_response = client.get(
            "/client/skills/incident-kit/archive",
            params={
                "device_id": "device-alpha",
                "timestamp": timestamp,
                "signature": signature,
            },
        )
        assert download_response.status_code == 200
        assert download_response.content == archive
        assert download_response.headers["content-type"] == "application/zip"


def test_device_connect_receives_skill_sync_before_pending_tasks(tmp_path):
    client, settings = build_test_client(tmp_path)
    token = login(client)
    client.post(
        "/dashboard/api/skills",
        headers=auth_headers(token),
        json={"skill_id": "runbook", "name": "Runbook"},
    )
    client.put(
        "/dashboard/api/skills/runbook/archive",
        headers={
            **auth_headers(token),
            "Content-Type": "application/zip",
            "X-Skill-Archive-Name": "runbook.zip",
        },
        content=build_skill_archive("runbook"),
    )
    client.post(
        "/dashboard/api/devices/device-alpha/skills",
        headers=auth_headers(token),
        json={"skill_id": "runbook"},
    )
    create_response = client.post(
        "/tasks",
        headers=auth_headers(token),
        json={
            "device_id": "device-alpha",
            "instruction": "查看系统负载",
        },
    )
    assert create_response.status_code == 201

    timestamp = 1700000003
    signature = sign_device_request(
        device_id="device-alpha",
        timestamp=timestamp,
        device_key=settings.device_keys["device-alpha"],
    )

    with client.websocket_connect(
        f"/ws/client?device_id=device-alpha&timestamp={timestamp}&signature={signature}"
    ) as device_ws:
        first_payload = device_ws.receive_json()
        second_payload = device_ws.receive_json()

    assert first_payload["type"] == "DEVICE_SKILLS_SYNC"
    assert first_payload["skills"][0]["skill_id"] == "runbook"
    assert second_payload["type"] == "TASK_ASSIGNED"


def test_device_connect_receives_ai_config_sync_before_pending_tasks(tmp_path):
    client, settings = build_test_client(tmp_path)
    token = login(client)
    config_response = client.put(
        "/dashboard/api/ai/devices/device-alpha",
        headers=auth_headers(token),
        json={
            "provider": "custom",
            "model": "deepseek-chat",
            "api_key": "device-secret-key",
            "base_url": "https://llm.example/v1/chat/completions",
        },
    )
    assert config_response.status_code == 204

    create_response = client.post(
        "/tasks",
        headers=auth_headers(token),
        json={
            "device_id": "device-alpha",
            "instruction": "查看系统负载",
        },
    )
    assert create_response.status_code == 201

    timestamp = 1700000004
    signature = sign_device_request(
        device_id="device-alpha",
        timestamp=timestamp,
        device_key=settings.device_keys["device-alpha"],
    )

    with client.websocket_connect(
        f"/ws/client?device_id=device-alpha&timestamp={timestamp}&signature={signature}"
    ) as device_ws:
        first_payload = device_ws.receive_json()
        second_payload = device_ws.receive_json()
        third_payload = device_ws.receive_json()

    assert first_payload == {
        "type": "DEVICE_SKILLS_SYNC",
        "device_id": "device-alpha",
        "skills": [],
    }
    assert second_payload == {
        "type": "DEVICE_AI_CONFIG_SYNC",
        "device_id": "device-alpha",
        "config": {
            "provider": "custom",
            "model": "deepseek-chat",
            "api_key": "device-secret-key",
            "base_url": "https://llm.example/v1/chat/completions",
        },
    }
    assert third_payload["type"] == "TASK_ASSIGNED"
