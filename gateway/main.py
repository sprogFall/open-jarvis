from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketException, status
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from client.ai import StructuredModelClient
from gateway.ai import GATEWAY_LOCAL_DEVICE_ID, GatewayTaskRouter
from gateway.dashboard_api import build_device_skill_sync_payload, dashboard_api
from gateway.dashboard_api import build_device_ai_config_sync_payload
from gateway.local_executor import GatewayLocalExecutor
from gateway.skill_archive import SkillArchiveStore
from gateway.security import (
    issue_access_token,
    verify_access_token,
    verify_device_signature,
)
from gateway.settings import GatewaySettings
from gateway.store import GatewayStore
from skill_catalog import BUILTIN_SKILLS


bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str


class CreateTaskRequest(BaseModel):
    device_id: str | None = None
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

    async def broadcast_task_deleted(self, task_id: str) -> None:
        stale_connections = []
        payload = {"type": "TASK_DELETED", "task_id": task_id}
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

    async def send_device_skills_sync(self, device_id: str, payload: dict) -> None:
        await self._send_client_payload(device_id, payload)

    async def send_device_ai_config_sync(self, device_id: str, payload: dict) -> None:
        await self._send_client_payload(device_id, payload)

    async def _send_client_payload(self, device_id: str, payload: dict) -> None:
        websocket = self.client_connections.get(device_id)
        if websocket is None:
            return
        try:
            await websocket.send_json(payload)
        except Exception:
            self.disconnect_client(device_id, websocket)


def _build_task_router_candidates(store: GatewayStore) -> list[dict]:
    candidates: list[dict] = []
    for device in store.list_devices():
        skills: list[str] = []
        for skill in store.list_device_skills(device["device_id"]):
            skills.extend(skill.get("action_names") or [])
        candidates.append(
            {
                "device_id": device["device_id"],
                "name": device.get("name"),
                "type": device.get("type"),
                "skills": skills,
            }
        )
    candidates.append(
        {
            "device_id": GATEWAY_LOCAL_DEVICE_ID,
            "name": "Gateway Local",
            "type": "gateway",
            "skills": [
                "filesystem.read_file",
                "filesystem.search_suffix",
                "process.inspect_load",
                "process.list_processes",
                "docker.list_containers",
                "docker.restart",
                "shell.exec",
            ],
        }
    )
    return candidates


def _resolve_skill_archives_path(settings: GatewaySettings) -> Path:
    if settings.skill_archives_path is not None:
        return settings.skill_archives_path
    database_url = settings.database_url
    if database_url.startswith("sqlite:///"):
        database_url = database_url[len("sqlite:///"):]
    elif database_url.startswith("sqlite://"):
        database_url = database_url[len("sqlite://"):]
    if database_url.startswith("postgresql"):
        return Path("gateway/skill_archives").resolve()
    return (Path(database_url).expanduser().resolve().parent / "skill_archives")


def _bootstrap_builtin_skills(store: GatewayStore) -> None:
    for skill in BUILTIN_SKILLS:
        if store.get_skill(skill.skill_id) is not None:
            continue
        store.create_skill(
            skill.skill_id,
            skill.name,
            skill.description,
            {},
        )


def create_app(settings: GatewaySettings | None = None) -> FastAPI:
    settings = settings or GatewaySettings.from_env()
    store = GatewayStore(settings.database_url)
    settings.skill_archives_path = _resolve_skill_archives_path(settings)
    skill_archives = SkillArchiveStore(settings.skill_archives_path)
    manager = ConnectionManager()
    settings.device_keys = store.initialize_device_registry(settings.device_keys)
    _bootstrap_builtin_skills(store)

    app = FastAPI(title="Omni-Agent Gateway")
    app.state.settings = settings
    app.state.store = store
    app.state.skill_archives = skill_archives
    app.state.manager = manager
    app.state.task_router = GatewayTaskRouter(store, settings)
    app.state.local_executor = GatewayLocalExecutor(store, manager, settings)
    app.state.ai_model_client_factory = StructuredModelClient
    if settings.dashboard_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.dashboard_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(dashboard_api)

    def require_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> dict:
        if credentials is None:
            raise HTTPException(status_code=401, detail="Missing bearer token")
        try:
            return verify_access_token(settings, credentials.credentials)
        except Exception as exc:
            raise HTTPException(status_code=401, detail="Invalid token") from exc

    def require_device_request(
        device_id: str,
        timestamp: int,
        signature: str,
    ) -> str:
        if not verify_device_signature(settings, device_id, timestamp, signature):
            raise HTTPException(status_code=401, detail="Invalid device signature")
        return device_id

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
        resolved_device_id = request.device_id
        resolved_instruction = request.instruction
        if not resolved_device_id:
            try:
                routing = app.state.task_router.route(
                    request.instruction,
                    _build_task_router_candidates(store),
                )
            except Exception as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            resolved_device_id = routing["device_id"]
            resolved_instruction = routing.get("instruction") or request.instruction
        if (
            resolved_device_id != GATEWAY_LOCAL_DEVICE_ID
            and resolved_device_id not in settings.device_keys
        ):
            raise HTTPException(status_code=404, detail="Unknown device")
        task_id = uuid4().hex[:12]
        task = store.create_task(task_id, resolved_device_id, resolved_instruction)
        await manager.broadcast_task(task)
        if resolved_device_id == GATEWAY_LOCAL_DEVICE_ID:
            if hasattr(app.state.local_executor, "bind_loop"):
                app.state.local_executor.bind_loop(asyncio.get_running_loop())
            app.state.local_executor.handle_assignment(task_id, resolved_instruction)
        else:
            await manager.send_task_assignment(resolved_device_id, task)
        return task

    @app.get("/tasks/pending_approvals")
    def list_pending_approvals(
        _user: dict = Depends(require_user),
    ) -> list[dict]:
        return store.list_pending_approvals()

    @app.get("/tasks")
    def list_tasks(
        limit: int = 100,
        _user: dict = Depends(require_user),
    ) -> list[dict]:
        return store.list_tasks_filtered(limit=limit)

    @app.get("/tasks/{task_id}")
    def get_task(
        task_id: str,
        _user: dict = Depends(require_user),
    ) -> dict:
        task = store.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    @app.delete("/tasks/{task_id}", status_code=204)
    async def delete_task(
        task_id: str,
        _user: dict = Depends(require_user),
    ) -> None:
        task = store.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task["status"] not in {"COMPLETED", "FAILED", "REJECTED"}:
            raise HTTPException(
                status_code=409,
                detail="只有已结束的历史记录才允许删除",
            )
        if not store.delete_task(task_id):
            raise HTTPException(status_code=404, detail="Task not found")
        await manager.broadcast_task_deleted(task_id)

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

    @app.get("/client/skills/{skill_id}/archive")
    def download_skill_archive(
        skill_id: str,
        device_id: str = Depends(require_device_request),
    ) -> Response:
        assigned = {
            skill["skill_id"]
            for skill in store.list_device_skills(device_id)
            if skill.get("source") == "archive" and skill.get("archive_ready")
        }
        if skill_id not in assigned:
            raise HTTPException(status_code=404, detail="Skill archive not assigned")
        skill = store.get_skill(skill_id)
        if not skill or skill.get("source") != "archive" or not skill.get("archive_ready"):
            raise HTTPException(status_code=404, detail="Skill archive not found")
        try:
            archive = skill_archives.read_archive(skill_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Skill archive not found") from exc
        return Response(
            content=archive,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{skill["archive_filename"]}"',
            },
        )

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
        if task["device_id"] == GATEWAY_LOCAL_DEVICE_ID:
            if hasattr(app.state.local_executor, "bind_loop"):
                app.state.local_executor.bind_loop(asyncio.get_running_loop())
            app.state.local_executor.handle_approval(task_id, request.approved)
        else:
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
            await websocket.send_json(
                {
                    "type": "TASK_HISTORY_SYNC",
                    "tasks": store.list_tasks_filtered(limit=100),
                }
            )
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
        store.touch_device(device_id)
        skill_sync = build_device_skill_sync_payload(store, device_id)
        await manager.send_device_skills_sync(device_id, skill_sync)
        ai_sync = build_device_ai_config_sync_payload(store, settings, device_id)
        if ai_sync["config"] is not None:
            await manager.send_device_ai_config_sync(device_id, ai_sync)
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
                elif message_type == "AI_CALL_LOG":
                    store.record_ai_call(
                        source=payload["source"],
                        device_id=payload.get("device_id"),
                        task_id=payload.get("task_id"),
                        provider=payload["provider"],
                        model=payload["model"],
                        endpoint=payload.get("endpoint"),
                        system_prompt=payload["system_prompt"],
                        user_prompt=payload["user_prompt"],
                        response=payload.get("response"),
                        error=payload.get("error"),
                    )
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
