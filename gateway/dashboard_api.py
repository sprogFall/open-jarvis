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


class AIConfigUpdate(BaseModel):
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    base_url: str | None = None


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


def build_device_skill_sync_payload(store: GatewayStore, device_id: str) -> dict:
    skills = []
    for skill in store.list_device_skills(device_id):
        payload = dict(skill)
        payload["download_path"] = f"/client/skills/{skill['skill_id']}/archive"
        skills.append(payload)
    return {
        "type": "DEVICE_SKILLS_SYNC",
        "device_id": device_id,
        "skills": skills,
    }


async def _sync_device_skills(request: Request, device_id: str) -> None:
    payload = build_device_skill_sync_payload(request.app.state.store, device_id)
    await request.app.state.manager.send_device_skills_sync(device_id, payload)


async def _sync_skill_targets(request: Request, skill_id: str) -> None:
    store: GatewayStore = request.app.state.store
    for device_id in store.list_devices_for_skill(skill_id):
        await _sync_device_skills(request, device_id)


def build_device_ai_config_sync_payload(store: GatewayStore, device_id: str) -> dict:
    config = store.get_ai_config("client", device_id=device_id)
    if config is not None:
        config = {
            "provider": config["provider"],
            "model": config["model"],
            "api_key": config["api_key"],
            "base_url": config.get("base_url"),
        }
    return {
        "type": "DEVICE_AI_CONFIG_SYNC",
        "device_id": device_id,
        "config": config,
    }


async def _sync_device_ai_config(request: Request, device_id: str) -> None:
    payload = build_device_ai_config_sync_payload(request.app.state.store, device_id)
    await request.app.state.manager.send_device_ai_config_sync(device_id, payload)


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
async def update_skill(
    skill_id: str,
    body: SkillUpdate,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    if not store.get_skill(skill_id):
        raise HTTPException(404, "Skill 不存在")
    updates = body.model_dump(exclude_none=True)
    updated = store.update_skill(skill_id, **updates)
    if updates:
        await _sync_skill_targets(request, skill_id)
    return updated


@dashboard_api.put("/skills/{skill_id}/archive")
async def upload_skill_archive(
    skill_id: str,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    if not store.get_skill(skill_id):
        raise HTTPException(404, "Skill 不存在")
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in {"application/zip", "application/octet-stream"}:
        raise HTTPException(415, "Skill 压缩包必须使用 application/zip 上传")
    try:
        archive = await request.body()
        metadata = request.app.state.skill_archives.write_archive(
            skill_id,
            archive,
            request.headers.get("X-Skill-Archive-Name"),
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    updated = store.set_skill_archive(
        skill_id,
        filename=metadata.filename,
        sha256=metadata.sha256,
        size=metadata.size,
    )
    await _sync_skill_targets(request, skill_id)
    return updated


@dashboard_api.delete("/skills/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> None:
    device_ids = store.list_devices_for_skill(skill_id)
    if not store.delete_skill(skill_id):
        raise HTTPException(404, "Skill 不存在")
    request.app.state.skill_archives.delete_archive(skill_id)
    for device_id in device_ids:
        await _sync_device_skills(request, device_id)


@dashboard_api.get("/devices/{device_id}/skills")
def list_device_skills(
    device_id: str,
    store: GatewayStore = Depends(_get_store),
) -> list[dict]:
    if not store.get_device(device_id):
        raise HTTPException(404, "设备不存在")
    return store.list_device_skills(device_id)


@dashboard_api.post("/devices/{device_id}/skills", status_code=201)
async def assign_skill_to_device(
    device_id: str,
    body: AssignSkill,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    if not store.get_device(device_id):
        raise HTTPException(404, "设备不存在")
    skill = store.get_skill(body.skill_id)
    if not skill:
        raise HTTPException(404, "Skill 不存在")
    if not skill.get("archive_ready"):
        raise HTTPException(400, "Skill 尚未上传压缩包，不能分配到设备")
    assignment = store.assign_skill(device_id, body.skill_id, body.config)
    await _sync_device_skills(request, device_id)
    return assignment


@dashboard_api.delete("/devices/{device_id}/skills/{skill_id}", status_code=204)
async def unassign_skill_from_device(
    device_id: str,
    skill_id: str,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> None:
    if not store.unassign_skill(device_id, skill_id):
        raise HTTPException(404, "分配关系不存在")
    await _sync_device_skills(request, device_id)


@dashboard_api.put("/ai/gateway", status_code=204)
def update_gateway_ai_config(
    body: AIConfigUpdate,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> None:
    store.save_ai_config(
        "gateway",
        provider=body.provider,
        model=body.model,
        api_key=body.api_key,
        base_url=body.base_url,
    )
    del request


@dashboard_api.delete("/ai/gateway", status_code=204)
def delete_gateway_ai_config(store: GatewayStore = Depends(_get_store)) -> None:
    store.delete_ai_config("gateway")


@dashboard_api.put("/ai/devices/{device_id}", status_code=204)
async def update_device_ai_config(
    device_id: str,
    body: AIConfigUpdate,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> None:
    if not store.get_device(device_id):
        raise HTTPException(404, "设备不存在")
    store.save_ai_config(
        "client",
        device_id=device_id,
        provider=body.provider,
        model=body.model,
        api_key=body.api_key,
        base_url=body.base_url,
    )
    await _sync_device_ai_config(request, device_id)


@dashboard_api.delete("/ai/devices/{device_id}", status_code=204)
async def delete_device_ai_config(
    device_id: str,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> None:
    if not store.get_device(device_id):
        raise HTTPException(404, "设备不存在")
    store.delete_ai_config("client", device_id=device_id)
    await _sync_device_ai_config(request, device_id)


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
        "skill_archives_path": str(settings.skill_archives_path),
    }
