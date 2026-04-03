from __future__ import annotations

from fastapi.testclient import TestClient

from gateway.main import create_app
from gateway.security import sign_device_request
from gateway.settings import GatewaySettings


def _setup(tmp_path) -> tuple[TestClient, GatewaySettings, dict[str, str]]:
    settings = GatewaySettings(
        database_url=str(tmp_path / "gateway.db"),
        jwt_secret="test-secret-test-secret-test-secret",
        admin_username="operator",
        admin_password="passw0rd",
        device_keys={"device-alpha": "device-secret"},
    )
    client = TestClient(create_app(settings))
    token = client.post(
        "/auth/login",
        json={"username": "operator", "password": "passw0rd"},
    ).json()["access_token"]
    return client, settings, {"Authorization": f"Bearer {token}"}


def _receive_non_empty_skill_sync(device_ws) -> dict:
    for _ in range(4):
        payload = device_ws.receive_json()
        if payload.get("type") != "DEVICE_SKILLS_SYNC":
            continue
        if payload.get("skills"):
            return payload
    raise AssertionError("Did not receive a non-empty DEVICE_SKILLS_SYNC payload")


def test_builtin_skills_are_bootstrapped_into_dashboard_catalog(tmp_path):
    client, _settings, headers = _setup(tmp_path)

    response = client.get("/dashboard/api/skills", headers=headers)

    assert response.status_code == 200
    catalog = {skill["skill_id"]: skill for skill in response.json()}
    assert {"builtin-shell", "builtin-docker", "builtin-process", "builtin-filesystem"} <= set(
        catalog
    )
    assert catalog["builtin-shell"]["source"] == "builtin"
    assert catalog["builtin-shell"]["archive_ready"] is True
    assert catalog["builtin-shell"]["action_names"] == ["shell.exec"]
    assert "docker.restart" in catalog["builtin-docker"]["action_names"]


def test_assigning_builtin_skill_streams_action_metadata_without_zip(tmp_path):
    client, settings, headers = _setup(tmp_path)
    timestamp = 1700000200
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
            headers=headers,
            json={"skill_id": "builtin-docker"},
        )

        assert assign_response.status_code == 201
        payload = _receive_non_empty_skill_sync(device_ws)
        builtin_skill = payload["skills"][0]
        assert builtin_skill["skill_id"] == "builtin-docker"
        assert builtin_skill["source"] == "builtin"
        assert builtin_skill["archive_ready"] is True
        assert builtin_skill["action_names"] == [
            "docker.list_containers",
            "docker.restart",
        ]
        assert "download_path" not in builtin_skill
