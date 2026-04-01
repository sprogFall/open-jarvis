from __future__ import annotations

from fastapi.testclient import TestClient

from gateway.main import create_app
from gateway.settings import GatewaySettings


def _setup(tmp_path) -> tuple[TestClient, dict[str, str]]:
    settings = GatewaySettings(
        database_url=str(tmp_path / "test.db"),
        jwt_secret="test-secret-test-secret-test-secret",
        admin_username="operator",
        admin_password="passw0rd",
        device_keys={"device-alpha": "device-secret"},
    )
    client = TestClient(create_app(settings))
    token = client.post("/auth/login", json={
        "username": "operator", "password": "passw0rd"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return client, headers


# ── auth required ────────────────────────────────────────────────────────────

def test_dashboard_api_returns_401_without_token(tmp_path):
    settings = GatewaySettings(
        database_url=str(tmp_path / "test.db"),
        jwt_secret="test-secret-test-secret-test-secret",
    )
    client = TestClient(create_app(settings))
    assert client.get("/dashboard/api/overview").status_code == 401
    assert client.get("/dashboard/api/devices").status_code == 401
    assert client.get("/dashboard/api/skills").status_code == 401
    assert client.get("/dashboard/api/tasks").status_code == 401
    assert client.get("/dashboard/api/system").status_code == 401


def test_dashboard_page_is_public(tmp_path):
    settings = GatewaySettings(
        database_url=str(tmp_path / "test.db"),
        jwt_secret="test-secret-test-secret-test-secret",
    )
    client = TestClient(create_app(settings))
    resp = client.get("/dashboard/")
    assert resp.status_code == 200
    assert "OpenJarvis" in resp.text


# ── overview ─────────────────────────────────────────────────────────────────

def test_overview_returns_stats(tmp_path):
    client, headers = _setup(tmp_path)
    resp = client.get("/dashboard/api/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["device_count"] >= 1
    assert isinstance(data["connected_devices"], list)
    assert isinstance(data["task_counts"], dict)


# ── device CRUD ──────────────────────────────────────────────────────────────

def test_create_list_delete_device(tmp_path):
    client, headers = _setup(tmp_path)

    resp = client.post("/dashboard/api/devices", headers=headers, json={
        "device_id": "dev-new", "name": "新设备", "type": "cli", "device_key": "key123"
    })
    assert resp.status_code == 201
    assert resp.json()["device_id"] == "dev-new"

    resp = client.get("/dashboard/api/devices", headers=headers)
    ids = [d["device_id"] for d in resp.json()]
    assert "dev-new" in ids
    assert "device-alpha" in ids

    resp = client.get("/dashboard/api/devices/dev-new", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "新设备"

    resp = client.put("/dashboard/api/devices/dev-new", headers=headers, json={"name": "改名设备"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "改名设备"

    resp = client.delete("/dashboard/api/devices/dev-new", headers=headers)
    assert resp.status_code == 204

    resp = client.get("/dashboard/api/devices/dev-new", headers=headers)
    assert resp.status_code == 404


def test_create_duplicate_device_fails(tmp_path):
    client, headers = _setup(tmp_path)
    client.post("/dashboard/api/devices", headers=headers, json={
        "device_id": "dup", "name": "A", "type": "cli", "device_key": "k"
    })
    resp = client.post("/dashboard/api/devices", headers=headers, json={
        "device_id": "dup", "name": "B", "type": "cli", "device_key": "k"
    })
    assert resp.status_code == 400


def test_create_device_auto_generates_key(tmp_path):
    client, headers = _setup(tmp_path)
    resp = client.post("/dashboard/api/devices", headers=headers, json={
        "device_id": "auto-key", "name": "自动密钥"
    })
    assert resp.status_code == 201
    assert resp.json()["device_key"]


# ── skill CRUD ───────────────────────────────────────────────────────────────

def test_create_list_delete_skill(tmp_path):
    client, headers = _setup(tmp_path)

    resp = client.post("/dashboard/api/skills", headers=headers, json={
        "skill_id": "web-search", "name": "网页搜索", "description": "搜索互联网"
    })
    assert resp.status_code == 201

    resp = client.get("/dashboard/api/skills", headers=headers)
    assert any(s["skill_id"] == "web-search" for s in resp.json())

    resp = client.put("/dashboard/api/skills/web-search", headers=headers, json={"name": "搜索引擎"})
    assert resp.json()["name"] == "搜索引擎"

    resp = client.delete("/dashboard/api/skills/web-search", headers=headers)
    assert resp.status_code == 204

    resp = client.get("/dashboard/api/skills/web-search", headers=headers)
    assert resp.status_code == 404


def test_create_duplicate_skill_fails(tmp_path):
    client, headers = _setup(tmp_path)
    client.post("/dashboard/api/skills", headers=headers, json={"skill_id": "s1", "name": "A"})
    resp = client.post("/dashboard/api/skills", headers=headers, json={"skill_id": "s1", "name": "B"})
    assert resp.status_code == 400


# ── device-skill assignment ──────────────────────────────────────────────────

def test_assign_and_unassign_skill(tmp_path):
    client, headers = _setup(tmp_path)

    client.post("/dashboard/api/skills", headers=headers, json={
        "skill_id": "code-exec", "name": "代码执行"
    })

    resp = client.post("/dashboard/api/devices/device-alpha/skills", headers=headers, json={
        "skill_id": "code-exec"
    })
    assert resp.status_code == 201

    resp = client.get("/dashboard/api/devices/device-alpha/skills", headers=headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["skill_id"] == "code-exec"

    resp = client.delete("/dashboard/api/devices/device-alpha/skills/code-exec", headers=headers)
    assert resp.status_code == 204

    resp = client.get("/dashboard/api/devices/device-alpha/skills", headers=headers)
    assert len(resp.json()) == 0


def test_assign_skill_to_nonexistent_device_fails(tmp_path):
    client, headers = _setup(tmp_path)
    client.post("/dashboard/api/skills", headers=headers, json={"skill_id": "s1", "name": "A"})
    resp = client.post("/dashboard/api/devices/no-such/skills", headers=headers, json={"skill_id": "s1"})
    assert resp.status_code == 404


def test_assign_nonexistent_skill_fails(tmp_path):
    client, headers = _setup(tmp_path)
    resp = client.post("/dashboard/api/devices/device-alpha/skills", headers=headers, json={"skill_id": "nope"})
    assert resp.status_code == 404


# ── tasks (read-only) ────────────────────────────────────────────────────────

def test_list_tasks_empty(tmp_path):
    client, headers = _setup(tmp_path)
    resp = client.get("/dashboard/api/tasks", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tasks_with_filters(tmp_path):
    client, headers = _setup(tmp_path)
    client.post("/tasks", json={
        "device_id": "device-alpha", "instruction": "测试任务"
    }, headers=headers)

    resp = client.get("/dashboard/api/tasks", headers=headers)
    assert len(resp.json()) == 1

    resp = client.get("/dashboard/api/tasks?status=PENDING_DISPATCH", headers=headers)
    assert len(resp.json()) == 1

    resp = client.get("/dashboard/api/tasks?status=COMPLETED", headers=headers)
    assert len(resp.json()) == 0

    resp = client.get("/dashboard/api/tasks?device_id=device-alpha", headers=headers)
    assert len(resp.json()) == 1


# ── system info ──────────────────────────────────────────────────────────────

def test_system_info(tmp_path):
    client, headers = _setup(tmp_path)
    resp = client.get("/dashboard/api/system", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["admin_username"] == "operator"
    assert "device-alpha" in data["configured_devices"]


# ── dashboard HTML ───────────────────────────────────────────────────────────

def test_dashboard_page_no_trailing_slash(tmp_path):
    settings = GatewaySettings(
        database_url=str(tmp_path / "test.db"),
        jwt_secret="test-secret-test-secret-test-secret",
    )
    client = TestClient(create_app(settings))
    resp = client.get("/dashboard")
    assert resp.status_code == 200


# ── existing gateway tests still pass ────────────────────────────────────────

def test_existing_gateway_health(tmp_path):
    client, _ = _setup(tmp_path)
    assert client.get("/health").json() == {"status": "ok"}
