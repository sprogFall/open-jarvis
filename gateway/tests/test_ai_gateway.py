from __future__ import annotations

from fastapi.testclient import TestClient

from gateway.main import GATEWAY_LOCAL_DEVICE_ID, create_app
from gateway.settings import GatewaySettings
from gateway.store import GatewayStore


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient) -> str:
    response = client.post(
        "/auth/login",
        json={"username": "operator", "password": "passw0rd"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class StubTaskRouter:
    def __init__(self, *, device_id: str, instruction: str) -> None:
        self.device_id = device_id
        self.instruction = instruction
        self.calls: list[tuple[str, list[dict]]] = []

    def route(self, instruction: str, candidates: list[dict]) -> dict:
        self.calls.append((instruction, candidates))
        return {
            "device_id": self.device_id,
            "instruction": self.instruction,
            "reason": "stubbed by test",
        }


class RecordingLocalExecutor:
    def __init__(self) -> None:
        self.assignments: list[tuple[str, str]] = []
        self.approvals: list[tuple[str, bool]] = []

    def handle_assignment(self, task_id: str, instruction: str) -> None:
        self.assignments.append((task_id, instruction))

    def handle_approval(self, task_id: str, approved: bool) -> None:
        self.approvals.append((task_id, approved))


def test_store_persists_gateway_and_client_ai_configs(tmp_path):
    db_path = tmp_path / "gateway.db"
    store = GatewayStore(str(db_path))

    store.save_ai_config(
        "gateway",
        provider="openai",
        model="gpt-4o-mini",
        api_key="gateway-secret",
    )
    store.save_ai_config(
        "client",
        device_id="device-alpha",
        provider="custom",
        model="qwen-max",
        api_key="client-secret",
        base_url="https://llm.example/v1/chat/completions",
    )

    restarted = GatewayStore(str(db_path))

    gateway_config = restarted.get_ai_config("gateway")
    client_config = restarted.get_ai_config("client", device_id="device-alpha")
    assert gateway_config["provider"] == "openai"
    assert gateway_config["model"] == "gpt-4o-mini"
    assert gateway_config["api_key"] == "gateway-secret"
    assert client_config["provider"] == "custom"
    assert client_config["model"] == "qwen-max"
    assert client_config["base_url"] == "https://llm.example/v1/chat/completions"


def test_create_task_without_device_uses_ai_router_and_gateway_local_executor(tmp_path):
    settings = GatewaySettings(
        database_url=str(tmp_path / "gateway.db"),
        jwt_secret="test-secret-test-secret-test-secret",
        admin_username="operator",
        admin_password="passw0rd",
        device_keys={"device-alpha": "device-secret"},
    )
    app = create_app(settings)
    router = StubTaskRouter(
        device_id=GATEWAY_LOCAL_DEVICE_ID,
        instruction="查看本机系统负载",
    )
    local_executor = RecordingLocalExecutor()
    app.state.task_router = router
    app.state.local_executor = local_executor

    client = TestClient(app)
    token = login(client)

    response = client.post(
        "/tasks",
        headers=auth_headers(token),
        json={"instruction": "帮我自动选择合适的执行端并执行"},
    )

    assert response.status_code == 201
    task = response.json()
    assert task["device_id"] == GATEWAY_LOCAL_DEVICE_ID
    assert task["instruction"] == "查看本机系统负载"
    assert task["status"] == "PENDING_DISPATCH"
    assert local_executor.assignments == [(task["task_id"], "查看本机系统负载")]
    assert router.calls[0][0] == "帮我自动选择合适的执行端并执行"
    assert router.calls[0][1][-1]["device_id"] == GATEWAY_LOCAL_DEVICE_ID
