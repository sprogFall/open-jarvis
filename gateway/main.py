from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from gateway.security import (
    issue_access_token,
    verify_access_token,
    verify_device_signature,
)
from gateway.settings import GatewaySettings
from gateway.store import GatewayStore


bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str


class CreateTaskRequest(BaseModel):
    device_id: str
    instruction: str = Field(min_length=1)


class ApprovalDecisionRequest(BaseModel):
    approved: bool


class ConnectionManager:
    def __init__(self) -> None:
        self.app_connections: set[WebSocket] = set()
        self.client_connections: dict[str, WebSocket] = {}

    async def connect_app(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.app_connections.add(websocket)

    async def connect_client(self, device_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.client_connections[device_id] = websocket

    def disconnect_app(self, websocket: WebSocket) -> None:
        self.app_connections.discard(websocket)

    def disconnect_client(self, device_id: str, websocket: WebSocket) -> None:
        current = self.client_connections.get(device_id)
        if current is websocket:
            self.client_connections.pop(device_id, None)

    async def broadcast_task(self, task: dict) -> None:
        stale_connections = []
        payload = {"type": "TASK_SNAPSHOT", "task": task}
        for websocket in self.app_connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale_connections.append(websocket)
        for websocket in stale_connections:
            self.disconnect_app(websocket)

    async def broadcast_log(self, task_id: str, message: str) -> None:
        stale_connections = []
        payload = {"type": "TASK_LOG", "task_id": task_id, "message": message}
        for websocket in self.app_connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale_connections.append(websocket)
        for websocket in stale_connections:
            self.disconnect_app(websocket)

    async def send_task_assignment(self, device_id: str, task: dict) -> None:
        websocket = self.client_connections.get(device_id)
        if websocket is None:
            return
        await websocket.send_json({"type": "TASK_ASSIGNED", "task": task})

    async def send_approval_decision(self, device_id: str, task_id: str, approved: bool) -> None:
        websocket = self.client_connections.get(device_id)
        if websocket is None:
            return
        await websocket.send_json(
            {"type": "APPROVAL_DECISION", "task_id": task_id, "approved": approved}
        )


def create_app(settings: GatewaySettings | None = None) -> FastAPI:
    settings = settings or GatewaySettings.from_env()
    store = GatewayStore(settings.database_path)
    manager = ConnectionManager()
    app = FastAPI(title="Omni-Agent Gateway")
    app.state.settings = settings
    app.state.store = store
    app.state.manager = manager

    def require_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> dict:
        if credentials is None:
            raise HTTPException(status_code=401, detail="Missing bearer token")
        try:
            return verify_access_token(settings, credentials.credentials)
        except Exception as exc:
            raise HTTPException(status_code=401, detail="Invalid token") from exc

    @app.get("/health")
    def healthcheck() -> dict:
        return {"status": "ok"}

    @app.post("/auth/login", response_model=LoginResponse)
    def login(request: LoginRequest) -> LoginResponse:
        if (
            request.username != settings.admin_username
            or request.password != settings.admin_password
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return LoginResponse(
            access_token=issue_access_token(settings, subject=request.username)
        )

    @app.post("/tasks", status_code=201)
    async def create_task(
        request: CreateTaskRequest,
        _user: dict = Depends(require_user),
    ) -> dict:
        if request.device_id not in settings.device_keys:
            raise HTTPException(status_code=404, detail="Unknown device")
        task_id = uuid4().hex[:12]
        task = store.create_task(task_id, request.device_id, request.instruction)
        await manager.broadcast_task(task)
        await manager.send_task_assignment(request.device_id, task)
        return task

    @app.get("/tasks/pending_approvals")
    def list_pending_approvals(
        _user: dict = Depends(require_user),
    ) -> list[dict]:
        return store.list_pending_approvals()

    @app.get("/tasks/{task_id}")
    def get_task(
        task_id: str,
        _user: dict = Depends(require_user),
    ) -> dict:
        task = store.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    @app.get("/devices")
    def list_devices(
        _user: dict = Depends(require_user),
    ) -> list[dict]:
        devices = []
        for device_id in settings.device_keys:
            devices.append(
                {
                    "device_id": device_id,
                    "connected": device_id in manager.client_connections,
                }
            )
        return devices

    @app.post("/tasks/{task_id}/decision", status_code=202)
    async def submit_decision(
        task_id: str,
        request: ApprovalDecisionRequest,
        _user: dict = Depends(require_user),
    ) -> dict:
        task = store.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        status_value = "APPROVED" if request.approved else "REJECTED"
        updated = store.update_task(task_id, status=status_value)
        await manager.broadcast_task(updated)
        await manager.send_approval_decision(
            task["device_id"],
            task_id=task_id,
            approved=request.approved,
        )
        return updated

    @app.websocket("/ws/app")
    async def app_socket(websocket: WebSocket) -> None:
        token = websocket.query_params.get("token")
        if not token:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        try:
            verify_access_token(settings, token)
        except Exception as exc:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION) from exc
        await manager.connect_app(websocket)
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            manager.disconnect_app(websocket)

    @app.websocket("/ws/client")
    async def client_socket(websocket: WebSocket) -> None:
        device_id = websocket.query_params.get("device_id")
        timestamp = websocket.query_params.get("timestamp")
        signature = websocket.query_params.get("signature")
        if not device_id or not timestamp or not signature:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        if not verify_device_signature(settings, device_id, int(timestamp), signature):
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

        await manager.connect_client(device_id, websocket)
        for task in store.list_tasks_for_device(device_id, ["PENDING_DISPATCH"]):
            await manager.send_task_assignment(device_id, task)
        try:
            while True:
                payload = await websocket.receive_json()
                message_type = payload.get("type")
                task_id = payload.get("task_id")
                if not task_id:
                    continue
                if message_type == "TASK_STATUS":
                    updated = store.update_task(task_id, status=payload["status"])
                    await manager.broadcast_task(updated)
                elif message_type == "TASK_LOG":
                    updated = store.append_log(task_id, payload["message"])
                    await manager.broadcast_log(task_id, payload["message"])
                    await manager.broadcast_task(updated)
                elif message_type == "INTERRUPT_REQUEST":
                    updated = store.update_task(
                        task_id,
                        status="AWAITING_APPROVAL",
                        checkpoint_id=payload["checkpoint_id"],
                        command=payload["command"],
                        reason=payload["reason"],
                    )
                    await manager.broadcast_task(updated)
                elif message_type == "TASK_COMPLETED":
                    updated = store.update_task(
                        task_id,
                        status="COMPLETED",
                        result=payload["result"],
                        checkpoint_id=None,
                    )
                    await manager.broadcast_task(updated)
                elif message_type == "TASK_FAILED":
                    updated = store.update_task(
                        task_id,
                        status="FAILED",
                        error=payload["error"],
                        checkpoint_id=None,
                    )
                    await manager.broadcast_task(updated)
        except Exception:
            manager.disconnect_client(device_id, websocket)

    return app


app = create_app()
