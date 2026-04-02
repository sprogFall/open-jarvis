from __future__ import annotations

import secrets

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from gateway.security import verify_access_token
from gateway.store import GatewayStore


class DeviceCreate(BaseModel):
    device_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: str = Field(default="cli", pattern="^(cli|app)$")
    device_key: str = Field(default="")


class DeviceUpdate(BaseModel):
    name: str | None = None
    type: str | None = Field(default=None, pattern="^(cli|app)$")
    device_key: str | None = None


class SkillCreate(BaseModel):
    skill_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""
    config: dict = Field(default_factory=dict)


class SkillUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    config: dict | None = None


class AssignSkill(BaseModel):
    skill_id: str
    config: dict = Field(default_factory=dict)


_bearer = HTTPBearer(auto_error=False)


def _require_dashboard_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    _token: str | None = Cookie(default=None, alias="dashboard_token"),
) -> dict:
    token = credentials.credentials if credentials else _token
    if not token:
        raise HTTPException(401, "未登录")
    try:
        return verify_access_token(request.app.state.settings, token)
    except Exception as exc:
        raise HTTPException(401, "登录已过期") from exc


def _get_store(request: Request) -> GatewayStore:
    return request.app.state.store


def _get_connection_info(request: Request) -> dict:
    manager = request.app.state.manager
    return {
        "app_count": len(manager.app_connections),
        "connected_devices": list(manager.client_connections.keys()),
    }


dashboard_api = APIRouter(
    prefix="/dashboard/api",
    dependencies=[Depends(_require_dashboard_user)],
)


@dashboard_api.get("/overview")
def overview(
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    stats = store.overview_stats()
    conn_info = _get_connection_info(request)
    stats["app_connections"] = conn_info["app_count"]
    stats["connected_devices"] = conn_info["connected_devices"]
    return stats


@dashboard_api.get("/devices")
def list_devices(
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> list[dict]:
    devices = store.list_devices()
    conn_info = _get_connection_info(request)
    for device in devices:
        device["connected"] = device["device_id"] in conn_info["connected_devices"]
    return devices


@dashboard_api.post("/devices", status_code=201)
def create_device(
    body: DeviceCreate,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    if store.get_device(body.device_id):
        raise HTTPException(400, "设备ID已存在")
    key = body.device_key or secrets.token_hex(16)
    device = store.create_device(body.device_id, body.name, body.type, key)
    request.app.state.settings.device_keys[body.device_id] = key
    return device


@dashboard_api.get("/devices/{device_id}")
def get_device(
    device_id: str,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    device = store.get_device(device_id)
    if not device:
        raise HTTPException(404, "设备不存在")
    conn_info = _get_connection_info(request)
    device["connected"] = device_id in conn_info["connected_devices"]
    device["skills"] = store.list_device_skills(device_id)
    return device


@dashboard_api.put("/devices/{device_id}")
def update_device(
    device_id: str,
    body: DeviceUpdate,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    if not store.get_device(device_id):
        raise HTTPException(404, "设备不存在")
    updates = body.model_dump(exclude_none=True)
    device = store.update_device(device_id, **updates)
    if body.device_key:
        request.app.state.settings.device_keys[device_id] = body.device_key
    return device


@dashboard_api.delete("/devices/{device_id}", status_code=204)
def delete_device(
    device_id: str,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> None:
    if not store.delete_device(device_id):
        raise HTTPException(404, "设备不存在")
    request.app.state.settings.device_keys.pop(device_id, None)


@dashboard_api.get("/skills")
def list_skills(store: GatewayStore = Depends(_get_store)) -> list[dict]:
    return store.list_skills()


@dashboard_api.post("/skills", status_code=201)
def create_skill(
    body: SkillCreate,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    if store.get_skill(body.skill_id):
        raise HTTPException(400, "Skill ID 已存在")
    return store.create_skill(body.skill_id, body.name, body.description, body.config)


@dashboard_api.get("/skills/{skill_id}")
def get_skill(
    skill_id: str,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    skill = store.get_skill(skill_id)
    if not skill:
        raise HTTPException(404, "Skill 不存在")
    return skill


@dashboard_api.put("/skills/{skill_id}")
def update_skill(
    skill_id: str,
    body: SkillUpdate,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    if not store.get_skill(skill_id):
        raise HTTPException(404, "Skill 不存在")
    updates = body.model_dump(exclude_none=True)
    return store.update_skill(skill_id, **updates)


@dashboard_api.delete("/skills/{skill_id}", status_code=204)
def delete_skill(
    skill_id: str,
    store: GatewayStore = Depends(_get_store),
) -> None:
    if not store.delete_skill(skill_id):
        raise HTTPException(404, "Skill 不存在")


@dashboard_api.get("/devices/{device_id}/skills")
def list_device_skills(
    device_id: str,
    store: GatewayStore = Depends(_get_store),
) -> list[dict]:
    if not store.get_device(device_id):
        raise HTTPException(404, "设备不存在")
    return store.list_device_skills(device_id)


@dashboard_api.post("/devices/{device_id}/skills", status_code=201)
def assign_skill_to_device(
    device_id: str,
    body: AssignSkill,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    if not store.get_device(device_id):
        raise HTTPException(404, "设备不存在")
    if not store.get_skill(body.skill_id):
        raise HTTPException(404, "Skill 不存在")
    return store.assign_skill(device_id, body.skill_id, body.config)


@dashboard_api.delete("/devices/{device_id}/skills/{skill_id}", status_code=204)
def unassign_skill_from_device(
    device_id: str,
    skill_id: str,
    store: GatewayStore = Depends(_get_store),
) -> None:
    if not store.unassign_skill(device_id, skill_id):
        raise HTTPException(404, "分配关系不存在")


@dashboard_api.get("/tasks")
def list_tasks(
    request: Request,
    status: str | None = None,
    device_id: str | None = None,
    limit: int = 50,
) -> list[dict]:
    store: GatewayStore = request.app.state.store
    return store.list_tasks_filtered(status=status, device_id=device_id, limit=limit)


@dashboard_api.get("/system")
def system_info(request: Request) -> dict:
    settings = request.app.state.settings
    return {
        "database_url": (
            settings.database_url.split("@")[-1]
            if "@" in settings.database_url
            else settings.database_url
        ),
        "jwt_algorithm": settings.jwt_algorithm,
        "admin_username": settings.admin_username,
        "configured_devices": list(settings.device_keys.keys()),
        "dashboard_origins": settings.dashboard_origins,
    }
