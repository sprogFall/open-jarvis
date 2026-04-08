from __future__ import annotations

import io
import zipfile

from fastapi.testclient import TestClient

from gateway.main import create_app
from gateway.settings import GatewaySettings


def _setup(tmp_path, dashboard_origins: list[str] | None = None) -> tuple[TestClient, dict[str, str]]:
    settings = GatewaySettings(
        database_url=str(tmp_path / "test.db"),
        jwt_secret="test-secret-test-secret-test-secret",
        admin_username="operator",
        admin_password="passw0rd",
        device_keys={"device-alpha": "device-secret"},
        dashboard_origins=dashboard_origins or [],
    )
    client = TestClient(create_app(settings))
    token = client.post(
        "/auth/login",
        json={"username": "operator", "password": "passw0rd"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return client, headers


def _build_skill_archive(
    skill_id: str,
    *,
    root: str | None = None,
    include_skill_md: bool = True,
) -> bytes:
    archive = io.BytesIO()
    prefix = f"{root.strip('/')}/" if root else ""
    with zipfile.ZipFile(archive, "w") as bundle:
        if include_skill_md:
            bundle.writestr(
                f"{prefix}SKILL.md",
                (
                    "---\n"
                    f"name: {skill_id}\n"
                    "description: Test skill\n"
                    "---\n\n"
                    "Body.\n"
                ),
            )
        bundle.writestr(f"{prefix}references/guide.md", "# Guide\n")
    return archive.getvalue()


def _read_zip_text(payload: bytes, suffix: str) -> str:
    with zipfile.ZipFile(io.BytesIO(payload)) as bundle:
        matched = next(name for name in bundle.namelist() if name.endswith(suffix))
        return bundle.read(matched).decode("utf-8")


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


def test_dashboard_api_supports_configured_cors_origin(tmp_path):
    client, _headers = _setup(tmp_path, ["https://dashboard.example.com"])

    response = client.options(
        "/dashboard/api/overview",
        headers={
            "Origin": "https://dashboard.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://dashboard.example.com"


def test_overview_returns_stats(tmp_path):
    client, headers = _setup(tmp_path)
    resp = client.get("/dashboard/api/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["device_count"] >= 1
    assert isinstance(data["connected_devices"], list)
    assert isinstance(data["task_counts"], dict)


def test_create_list_delete_device(tmp_path):
    client, headers = _setup(tmp_path)

    resp = client.post("/dashboard/api/devices", headers=headers, json={
        "device_id": "dev-new", "name": "新设备", "type": "cli", "device_key": "key123"
    })
    assert resp.status_code == 201
    assert resp.json()["device_id"] == "dev-new"
    assert "device_key" not in resp.json()
    assert "created_at" not in resp.json()

    resp = client.get("/dashboard/api/devices", headers=headers)
    devices = resp.json()
    ids = [d["device_id"] for d in devices]
    assert "dev-new" in ids
    assert "device-alpha" in ids
    assert all("device_key" not in device for device in devices)
    assert all("created_at" not in device for device in devices)

    resp = client.get("/dashboard/api/devices/dev-new", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "新设备"
    assert "device_key" not in resp.json()
    assert "created_at" not in resp.json()

    resp = client.put("/dashboard/api/devices/dev-new", headers=headers, json={"name": "改名设备"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "改名设备"
    assert "device_key" not in resp.json()
    assert "created_at" not in resp.json()

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
    assert "device_key" not in resp.json()
    stored = client.app.state.store.get_device("auto-key")
    assert stored is not None
    assert stored["device_key"]


def test_generate_client_package_registers_device_assigns_skills_and_returns_zip(tmp_path):
    client, headers = _setup(tmp_path)

    response = client.post(
        "/dashboard/api/client-packages",
        headers=headers,
        json={
            "device_id": "edge-box",
            "name": "边缘节点",
            "gateway_url": "https://gw.example.com/jarvis/api",
            "repo_url": "https://github.com/example/open-jarvis.git",
            "repo_ref": "main",
            "network_profile": "cn",
            "skill_ids": ["builtin-docker", "builtin-filesystem"],
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/zip")
    assert "attachment;" in response.headers["content-disposition"]

    env_text = _read_zip_text(response.content, "client-package.env")
    compose_text = _read_zip_text(response.content, "docker-compose.client.generated.yml")
    script_text = _read_zip_text(response.content, "deploy-client.sh")
    readme_text = _read_zip_text(response.content, "README.md")

    assert "OMNI_AGENT_DEVICE_ID=edge-box" in env_text
    assert "OMNI_AGENT_GATEWAY_URL=https://gw.example.com/jarvis/api" in env_text
    assert "DEPLOY_NETWORK_PROFILE=cn" in env_text
    assert "CLIENT_DOCKERFILE=client/Dockerfile.cn" in env_text
    assert "/var/run/docker.sock:/var/run/docker.sock" in compose_text
    assert "./client-package-workspace:/workspace:ro" in compose_text
    assert "JARVISCTL_COMPOSE_FILE" in script_text
    assert "./jarvisctl deploy client" in script_text
    assert "边缘节点" in readme_text

    stored = client.app.state.store.get_device("edge-box")
    assert stored is not None
    assert stored["name"] == "边缘节点"
    assert stored["device_key"]
    assert client.app.state.settings.device_keys["edge-box"] == stored["device_key"]

    assignments = client.app.state.store.list_device_skills("edge-box")
    assert {item["skill_id"] for item in assignments} == {
        "builtin-docker",
        "builtin-filesystem",
    }

    devices = client.get("/dashboard/api/devices", headers=headers).json()
    assert all("device_key" not in item for item in devices)


def test_generate_client_package_omits_optional_mounts_when_skills_do_not_need_them(tmp_path):
    client, headers = _setup(tmp_path)

    response = client.post(
        "/dashboard/api/client-packages",
        headers=headers,
        json={
            "device_id": "process-box",
            "name": "巡检节点",
            "gateway_url": "https://gw.example.com/jarvis/api",
            "repo_url": "https://github.com/example/open-jarvis.git",
            "repo_ref": "main",
            "skill_ids": ["builtin-process"],
        },
    )

    assert response.status_code == 200

    compose_text = _read_zip_text(response.content, "docker-compose.client.generated.yml")

    assert "/var/run/docker.sock:/var/run/docker.sock" not in compose_text
    assert "./client-package-workspace:/workspace:ro" not in compose_text


def test_generate_client_package_rejects_unknown_skill_without_creating_device(tmp_path):
    client, headers = _setup(tmp_path)

    response = client.post(
        "/dashboard/api/client-packages",
        headers=headers,
        json={
            "device_id": "broken-box",
            "name": "异常节点",
            "gateway_url": "https://gw.example.com/jarvis/api",
            "repo_url": "https://github.com/example/open-jarvis.git",
            "repo_ref": "main",
            "skill_ids": ["missing-skill"],
        },
    )

    assert response.status_code == 404
    assert client.app.state.store.get_device("broken-box") is None


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


def test_upload_skill_archive_updates_skill_metadata(tmp_path):
    client, headers = _setup(tmp_path)
    client.post(
        "/dashboard/api/skills",
        headers=headers,
        json={"skill_id": "web-search", "name": "网页搜索"},
    )

    payload = _build_skill_archive("web-search", root="skills/web-search")
    resp = client.put(
        "/dashboard/api/skills/web-search/archive",
        headers={
            **headers,
            "Content-Type": "application/zip",
            "X-Skill-Archive-Name": "web-search.zip",
        },
        content=payload,
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["archive_ready"] is True
    assert body["archive_filename"] == "web-search.zip"
    assert body["archive_size"] == len(payload)
    assert len(body["archive_sha256"]) == 64
    assert body["archive_updated_at"]


def test_upload_skill_archive_rejects_invalid_zip(tmp_path):
    client, headers = _setup(tmp_path)
    client.post(
        "/dashboard/api/skills",
        headers=headers,
        json={"skill_id": "broken-skill", "name": "损坏 Skill"},
    )

    resp = client.put(
        "/dashboard/api/skills/broken-skill/archive",
        headers={
            **headers,
            "Content-Type": "application/zip",
            "X-Skill-Archive-Name": "broken.zip",
        },
        content=_build_skill_archive("broken-skill", include_skill_md=False),
    )

    assert resp.status_code == 400
    assert "SKILL.md" in resp.json()["detail"]


def test_create_duplicate_skill_fails(tmp_path):
    client, headers = _setup(tmp_path)
    client.post("/dashboard/api/skills", headers=headers, json={"skill_id": "s1", "name": "A"})
    resp = client.post("/dashboard/api/skills", headers=headers, json={"skill_id": "s1", "name": "B"})
    assert resp.status_code == 400


def test_assign_and_unassign_skill(tmp_path):
    client, headers = _setup(tmp_path)

    client.post("/dashboard/api/skills", headers=headers, json={
        "skill_id": "code-exec", "name": "代码执行"
    })
    upload_resp = client.put(
        "/dashboard/api/skills/code-exec/archive",
        headers={
            **headers,
            "Content-Type": "application/zip",
            "X-Skill-Archive-Name": "code-exec.zip",
        },
        content=_build_skill_archive("code-exec", root="code-exec"),
    )
    assert upload_resp.status_code == 200

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


def test_assign_skill_without_archive_fails(tmp_path):
    client, headers = _setup(tmp_path)
    client.post("/dashboard/api/skills", headers=headers, json={"skill_id": "s1", "name": "A"})

    resp = client.post(
        "/dashboard/api/devices/device-alpha/skills",
        headers=headers,
        json={"skill_id": "s1"},
    )

    assert resp.status_code == 400
    assert "压缩包" in resp.json()["detail"]


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


def test_system_info(tmp_path):
    client, headers = _setup(tmp_path, ["https://dashboard.example.com"])
    resp = client.get("/dashboard/api/system", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data == {
        "gateway_ai": None,
        "client_ai": [],
    }
    assert "database_url" not in data
    assert "jwt_algorithm" not in data
    assert "admin_username" not in data
    assert "configured_devices" not in data
    assert "dashboard_origins" not in data
    assert "skill_archives_path" not in data


def test_dashboard_ai_override_is_write_only_for_gateway(tmp_path):
    client, headers = _setup(tmp_path)

    response = client.put(
        "/dashboard/api/ai/gateway",
        headers=headers,
        json={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "gateway-secret",
        },
    )

    assert response.status_code == 204
    assert client.get("/dashboard/api/ai/gateway", headers=headers).status_code == 405
    stored = client.app.state.store.get_ai_config("gateway")
    assert stored["provider"] == "openai"
    assert stored["model"] == "gpt-4o-mini"
    assert stored["api_key"] == "gateway-secret"

    system_info = client.get("/dashboard/api/system", headers=headers).json()
    assert system_info["gateway_ai"] == {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "base_url": None,
        "api_key_masked": "gate...cret",
        "source": "gateway_default",
    }
    assert system_info["client_ai"] == [
        {
            "device_id": "device-alpha",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "base_url": None,
            "api_key_masked": "gate...cret",
            "source": "gateway_default",
        }
    ]


def test_dashboard_ai_override_can_target_device_without_readback(tmp_path):
    client, headers = _setup(tmp_path)

    response = client.put(
        "/dashboard/api/ai/devices/device-alpha",
        headers=headers,
        json={
            "provider": "custom",
            "model": "qwen-max",
            "api_key": "client-secret",
            "base_url": "https://llm.example/v1/chat/completions",
        },
    )

    assert response.status_code == 204
    assert client.get("/dashboard/api/ai/devices/device-alpha", headers=headers).status_code == 405
    stored = client.app.state.store.get_ai_config("client", device_id="device-alpha")
    assert stored["provider"] == "custom"
    assert stored["model"] == "qwen-max"
    assert stored["base_url"] == "https://llm.example/v1/chat/completions"

    system_info = client.get("/dashboard/api/system", headers=headers).json()
    assert system_info["client_ai"] == [
        {
            "device_id": "device-alpha",
            "provider": "custom",
            "model": "qwen-max",
            "base_url": "https://llm.example/v1/chat/completions",
            "api_key_masked": "clie...cret",
            "source": "device_override",
        }
    ]


class StubModelClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[tuple[str, str]] = []

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.calls.append((system_prompt, user_prompt))
        return self.payload


def test_dashboard_can_test_current_gateway_ai_config_and_persist_call_log(tmp_path):
    client, headers = _setup(tmp_path)
    stub = StubModelClient({"ok": True, "summary": "模型响应正常"})
    client.app.state.ai_model_client_factory = lambda _config: stub

    save_response = client.put(
        "/dashboard/api/ai/gateway",
        headers=headers,
        json={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "gateway-secret",
        },
    )
    assert save_response.status_code == 204

    response = client.post("/dashboard/api/ai/test/gateway", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "response": {"ok": True, "summary": "模型响应正常"},
    }
    assert "连通性检查" in stub.calls[0][0]
    assert "结构化 JSON" in stub.calls[0][1]

    call_logs = client.get("/dashboard/api/ai/calls", headers=headers).json()
    assert len(call_logs) == 1
    assert call_logs[0]["source"] == "config_test"
    assert call_logs[0]["provider"] == "openai"
    assert call_logs[0]["model"] == "gpt-4o-mini"
    assert call_logs[0]["response"] == {"ok": True, "summary": "模型响应正常"}
    assert call_logs[0]["error"] is None


def test_dashboard_can_test_current_device_ai_effective_config(tmp_path):
    client, headers = _setup(tmp_path)
    stub = StubModelClient({"ok": True, "summary": "设备配置可用"})
    client.app.state.ai_model_client_factory = lambda _config: stub

    save_response = client.put(
        "/dashboard/api/ai/gateway",
        headers=headers,
        json={
            "provider": "custom",
            "model": "deepseek-chat",
            "api_key": "gateway-secret",
            "base_url": "https://llm.example/v1/chat/completions",
        },
    )
    assert save_response.status_code == 204

    response = client.post("/dashboard/api/ai/test/devices/device-alpha", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "provider": "custom",
        "model": "deepseek-chat",
        "response": {"ok": True, "summary": "设备配置可用"},
    }
    assert len(stub.calls) == 1

    call_logs = client.get("/dashboard/api/ai/calls", headers=headers).json()
    assert len(call_logs) == 1
    assert call_logs[0]["source"] == "config_test"
    assert call_logs[0]["device_id"] == "device-alpha"
    assert call_logs[0]["endpoint"] == "https://llm.example/v1/chat/completions"


def test_dashboard_ai_test_normalizes_openai_compatible_root_base_url(tmp_path):
    client, headers = _setup(tmp_path)
    stub = StubModelClient({"ok": True, "summary": "ModelScope 连通"})
    client.app.state.ai_model_client_factory = lambda _config: stub

    save_response = client.put(
        "/dashboard/api/ai/gateway",
        headers=headers,
        json={
            "provider": "custom",
            "model": "Qwen/Qwen2.5-72B-Instruct",
            "api_key": "gateway-secret",
            "base_url": "https://api-inference.modelscope.cn/v1",
        },
    )
    assert save_response.status_code == 204

    response = client.post("/dashboard/api/ai/test/gateway", headers=headers)

    assert response.status_code == 200
    call_logs = client.get("/dashboard/api/ai/calls", headers=headers).json()
    assert call_logs[0]["endpoint"] == "https://api-inference.modelscope.cn/v1/chat/completions"


def test_existing_gateway_health(tmp_path):
    client, _ = _setup(tmp_path)
    assert client.get("/health").json() == {"status": "ok"}
