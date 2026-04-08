from __future__ import annotations

import secrets
from urllib.parse import urlsplit, urlunsplit

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator, model_validator

from client.ai import AIModelConfig, StructuredModelClient, resolve_model_endpoint
from gateway.client_package import ClientPackageSpec, PackageSkill, build_client_package
from gateway.quick_deploy import (
    QUICK_DEPLOY_MODULES,
    build_package_skills,
    build_quick_deploy_archive,
    build_quick_deploy_draft,
    normalize_module_env,
    render_module_env,
    required_field_label,
)
from gateway.security import verify_access_token
from gateway.store import GatewayStore
from gateway.settings import GatewaySettings


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


class ClientPackageCreate(BaseModel):
    device_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    device_key: str = Field(default="")
    gateway_url: str = Field(min_length=1)
    repo_url: str = Field(min_length=1)
    repo_ref: str = Field(default="main", min_length=1)
    network_profile: str = Field(default="global", pattern="^(global|cn)$")
    skill_ids: list[str] = Field(default_factory=list)

    @field_validator("gateway_url")
    @classmethod
    def validate_gateway_url(cls, value: str) -> str:
        trimmed = value.strip().rstrip("/")
        parsed = urlsplit(trimmed)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Gateway 地址必须是可访问的 http(s) 绝对地址")
        return trimmed

    @field_validator("repo_url", "repo_ref", "device_id", "name")
    @classmethod
    def strip_non_empty_value(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("字段不能为空")
        return trimmed

    @field_validator("skill_ids")
    @classmethod
    def normalize_skill_ids(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for skill_id in value:
            candidate = str(skill_id).strip()
            if not candidate or candidate in seen:
                continue
            normalized.append(candidate)
            seen.add(candidate)
        return normalized


class QuickDeployClientPackage(BaseModel):
    device_name: str = Field(min_length=1)
    repo_url: str = Field(min_length=1)
    repo_ref: str = Field(default="main", min_length=1)
    register_device: bool = True
    skill_ids: list[str] = Field(default_factory=list)

    @field_validator("device_name", "repo_url", "repo_ref")
    @classmethod
    def strip_required_fields(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("字段不能为空")
        return trimmed

    @field_validator("skill_ids")
    @classmethod
    def normalize_skill_ids(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for skill_id in value:
            candidate = str(skill_id).strip()
            if not candidate or candidate in seen:
                continue
            normalized.append(candidate)
            seen.add(candidate)
        return normalized


class QuickDeployPackageCreate(BaseModel):
    targets: list[str] = Field(default_factory=lambda: ["client"])
    modules: dict[str, dict[str, str]] = Field(default_factory=dict)
    client_package: QuickDeployClientPackage | None = None

    @field_validator("targets")
    @classmethod
    def normalize_targets(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for target in value:
            candidate = str(target).strip()
            if candidate not in QUICK_DEPLOY_MODULES:
                raise ValueError("存在不支持的部署目标")
            if candidate not in normalized:
                normalized.append(candidate)
        if not normalized:
            raise ValueError("至少选择一个部署目标")
        return normalized

    @model_validator(mode="after")
    def validate_client_target(self) -> "QuickDeployPackageCreate":
        if "client" in self.targets and self.client_package is None:
            raise ValueError("选择 Client 时必须提供客户端部署信息")
        return self


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


def _mask_api_key(api_key: str) -> str:
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}...{api_key[-4:]}"


def _build_ai_summary(
    payload: dict,
    *,
    source: str,
    device_id: str | None = None,
) -> dict:
    summary = {
        "provider": payload["provider"],
        "model": payload["model"],
        "base_url": _sanitize_url_for_dashboard(payload.get("base_url")),
        "api_key_masked": _mask_api_key(str(payload["api_key"])),
        "source": source,
    }
    if device_id:
        summary["device_id"] = device_id
    return summary


def _resolve_gateway_ai_summary(store: GatewayStore, request: Request) -> dict | None:
    stored = store.get_ai_config("gateway")
    if stored is not None:
        return _build_ai_summary(stored, source="gateway_default")
    fallback = request.app.state.settings.ai_config()
    if fallback is None:
        return None
    return _build_ai_summary(fallback.to_dict(), source="environment_fallback")


def _resolve_client_ai_summaries(store: GatewayStore, request: Request) -> list[dict]:
    gateway_summary = _resolve_gateway_ai_summary(store, request)
    gateway_source = gateway_summary["source"] if gateway_summary else None
    gateway_payload = store.get_ai_config("gateway")
    if gateway_payload is None:
        gateway_fallback = request.app.state.settings.ai_config()
        gateway_payload = gateway_fallback.to_dict() if gateway_fallback is not None else None

    summaries: list[dict] = []
    for device in store.list_devices():
        if device.get("type") != "cli":
            continue
        device_id = str(device["device_id"])
        override = store.get_ai_config("client", device_id=device_id)
        if override is not None:
            summaries.append(
                _build_ai_summary(override, source="device_override", device_id=device_id)
            )
            continue
        if gateway_payload is not None and gateway_source is not None:
            summaries.append(
                _build_ai_summary(gateway_payload, source=gateway_source, device_id=device_id)
            )
    summaries.sort(key=lambda summary: str(summary.get("device_id") or ""))
    return summaries


def _resolve_effective_client_ai_config(
    store: GatewayStore,
    settings: GatewaySettings,
    device_id: str,
) -> dict | None:
    override = store.get_ai_config("client", device_id=device_id)
    if override is not None:
        return override
    gateway_default = store.get_ai_config("gateway")
    if gateway_default is not None:
        return gateway_default
    gateway_fallback = settings.ai_config()
    return gateway_fallback.to_dict() if gateway_fallback is not None else None


def build_device_skill_sync_payload(store: GatewayStore, device_id: str) -> dict:
    skills = []
    for skill in store.list_device_skills(device_id):
        payload = dict(skill)
        if payload.get("source") == "archive":
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


def build_device_ai_config_sync_payload(
    store: GatewayStore,
    settings: GatewaySettings,
    device_id: str,
) -> dict:
    config = _resolve_effective_client_ai_config(store, settings, device_id)
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
    payload = build_device_ai_config_sync_payload(
        request.app.state.store,
        request.app.state.settings,
        device_id,
    )
    await request.app.state.manager.send_device_ai_config_sync(device_id, payload)


def _sanitize_url_for_dashboard(raw_url: str | None) -> str | None:
    if raw_url is None:
        return None
    trimmed = str(raw_url).strip()
    if not trimmed:
        return None
    parsed = urlsplit(trimmed)
    if not parsed.scheme and not parsed.netloc:
        return urlunsplit(("", "", parsed.path, "", ""))
    hostname = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    return urlunsplit((parsed.scheme, f"{hostname}{port}", parsed.path, "", ""))


def _resolve_package_skills(store: GatewayStore, skill_ids: list[str]) -> list[dict]:
    selected_skills: list[dict] = []
    for skill_id in skill_ids:
        skill = store.get_skill(skill_id)
        if not skill:
            raise HTTPException(404, "Skill 不存在")
        if not skill.get("archive_ready"):
            raise HTTPException(400, "Skill 尚未就绪，不能写入部署包")
        selected_skills.append(skill)
    return selected_skills


def _serialize_device(
    device: dict,
    *,
    connected: bool,
    skills: list[dict] | None = None,
) -> dict:
    payload = {
        "device_id": device["device_id"],
        "name": device["name"],
        "type": device["type"],
        "last_seen_at": device.get("last_seen_at"),
        "connected": connected,
    }
    if skills is not None:
        payload["skills"] = skills
    return payload


def _serialize_ai_call(call: dict) -> dict:
    payload = dict(call)
    payload["endpoint"] = _sanitize_url_for_dashboard(payload.get("endpoint"))
    return payload


def _test_ai_config(
    request: Request,
    *,
    config: dict,
    source: str,
    device_id: str | None = None,
) -> dict:
    model_client_factory = getattr(request.app.state, "ai_model_client_factory", StructuredModelClient)
    model_config = AIModelConfig.from_dict(config)
    if model_config is None:
        raise HTTPException(400, "当前没有可测试的 AI 配置")

    system_prompt = (
        "你是 OpenJarvis 的 AI 连通性检查器。"
        "请仅返回 JSON 对象，格式为 "
        "{\"ok\":true,\"summary\":\"一句话说明当前模型可正常返回结构化 JSON\"}。"
    )
    user_prompt = "请返回一条结构化 JSON 连通性检查结果。"
    endpoint = resolve_model_endpoint(model_config)
    try:
        response = model_client_factory(model_config).generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    except Exception as exc:
        request.app.state.store.record_ai_call(
            source=source,
            device_id=device_id,
            provider=model_config.provider,
            model=model_config.model,
            endpoint=endpoint,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            error=str(exc),
        )
        raise HTTPException(502, str(exc)) from exc

    request.app.state.store.record_ai_call(
        source=source,
        device_id=device_id,
        provider=model_config.provider,
        model=model_config.model,
        endpoint=endpoint,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response=response,
    )
    return {
        "provider": model_config.provider,
        "model": model_config.model,
        "response": response,
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
    return [
        _serialize_device(
            device,
            connected=device["device_id"] in conn_info["connected_devices"],
        )
        for device in devices
    ]


@dashboard_api.post("/devices", status_code=201)
def create_device(
    body: DeviceCreate,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    if store.get_device(body.device_id):
        raise HTTPException(400, "设备ID已存在")
    key = str(body.device_key or "").strip() or secrets.token_hex(16)
    device = store.create_device(body.device_id, body.name, body.type, key)
    request.app.state.settings.device_keys[body.device_id] = key
    conn_info = _get_connection_info(request)
    return _serialize_device(
        device,
        connected=body.device_id in conn_info["connected_devices"],
    )


@dashboard_api.post("/client-packages")
def create_client_package(
    body: ClientPackageCreate,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> Response:
    if store.get_device(body.device_id):
        raise HTTPException(400, "设备ID已存在")

    selected_skills = _resolve_package_skills(store, body.skill_ids)

    device_key = str(body.device_key or "").strip() or secrets.token_hex(16)
    filename, archive = build_client_package(
        ClientPackageSpec(
            device_id=body.device_id,
            device_name=body.name,
            device_key=device_key,
            gateway_url=body.gateway_url,
            repo_url=body.repo_url,
            repo_ref=body.repo_ref,
            network_profile=body.network_profile,
            skills=tuple(
                PackageSkill(
                    skill_id=str(skill["skill_id"]),
                    name=str(skill["name"]),
                    source=str(skill["source"]),
                )
                for skill in selected_skills
            ),
        )
    )

    try:
        store.create_device(body.device_id, body.name, "cli", device_key)
        request.app.state.settings.device_keys[body.device_id] = device_key
        for skill in selected_skills:
            store.assign_skill(body.device_id, str(skill["skill_id"]), {})
    except Exception:
        store.delete_device(body.device_id)
        request.app.state.settings.device_keys.pop(body.device_id, None)
        raise

    return Response(
        content=archive,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@dashboard_api.get("/quick-deploy/draft")
def get_quick_deploy_draft() -> dict:
    return build_quick_deploy_draft()


@dashboard_api.post("/quick-deploy/package")
def create_quick_deploy_package(
    body: QuickDeployPackageCreate,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> Response:
    targets = tuple(body.targets)
    rendered_envs: dict = {}
    client_values: dict[str, str] | None = None
    selected_skills: list[dict] = []
    client_spec: ClientPackageSpec | None = None

    if "client" in targets:
        client_values = normalize_module_env("client", body.modules.get("client"))
        missing_label = required_field_label("client", client_values)
        if missing_label:
            raise HTTPException(400, f"{missing_label}不能为空")

        assert body.client_package is not None
        device_id = client_values["OMNI_AGENT_DEVICE_ID"]
        device_key = client_values["OMNI_AGENT_DEVICE_KEY"] or secrets.token_hex(16)
        client_values["OMNI_AGENT_DEVICE_KEY"] = device_key

        if body.client_package.register_device and store.get_device(device_id):
            raise HTTPException(400, "设备ID已存在")

        selected_skills = _resolve_package_skills(store, body.client_package.skill_ids)
        client_spec = ClientPackageSpec(
            device_id=device_id,
            device_name=body.client_package.device_name,
            device_key=device_key,
            gateway_url=client_values["OMNI_AGENT_GATEWAY_URL"],
            repo_url=body.client_package.repo_url,
            repo_ref=body.client_package.repo_ref,
            network_profile=client_values["DEPLOY_NETWORK_PROFILE"],
            skills=build_package_skills(selected_skills),
        )
        rendered_envs["client"] = render_module_env("client", client_values)

    if "gateway" in targets:
        gateway_values = normalize_module_env("gateway", body.modules.get("gateway"))
        missing_label = required_field_label("gateway", gateway_values)
        if missing_label:
            raise HTTPException(400, f"{missing_label}不能为空")
        if client_values is not None and body.client_package and body.client_package.register_device:
            gateway_values["OMNI_AGENT_DEVICE_KEYS"] = (
                f"{client_values['OMNI_AGENT_DEVICE_ID']}="
                f"{client_values['OMNI_AGENT_DEVICE_KEY']}"
            )
        rendered_envs["gateway"] = render_module_env("gateway", gateway_values)

    if "dashboard" in targets:
        dashboard_values = normalize_module_env("dashboard", body.modules.get("dashboard"))
        missing_label = required_field_label("dashboard", dashboard_values)
        if missing_label:
            raise HTTPException(400, f"{missing_label}不能为空")
        rendered_envs["dashboard"] = render_module_env("dashboard", dashboard_values)

    filename, archive = build_quick_deploy_archive(
        targets=targets,
        rendered_envs=rendered_envs,
        client_spec=client_spec,
    )

    if client_values is not None and body.client_package and body.client_package.register_device:
        device_id = client_values["OMNI_AGENT_DEVICE_ID"]
        device_key = client_values["OMNI_AGENT_DEVICE_KEY"]
        try:
            store.create_device(device_id, body.client_package.device_name, "cli", device_key)
            request.app.state.settings.device_keys[device_id] = device_key
            for skill in selected_skills:
                store.assign_skill(device_id, str(skill["skill_id"]), {})
        except Exception:
            store.delete_device(device_id)
            request.app.state.settings.device_keys.pop(device_id, None)
            raise

    return Response(
        content=archive,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


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
    return _serialize_device(
        device,
        connected=device_id in conn_info["connected_devices"],
        skills=store.list_device_skills(device_id),
    )


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
    next_device_key = str(body.device_key or "").strip()
    if next_device_key:
        updates["device_key"] = next_device_key
    else:
        updates.pop("device_key", None)
    device = store.update_device(device_id, **updates)
    if next_device_key:
        request.app.state.settings.device_keys[device_id] = next_device_key
    conn_info = _get_connection_info(request)
    return _serialize_device(
        device,
        connected=device_id in conn_info["connected_devices"],
    )


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
    skill = store.get_skill(skill_id)
    if not skill:
        raise HTTPException(404, "Skill 不存在")
    if skill.get("source") == "builtin":
        raise HTTPException(400, "内建 Skill 不支持上传压缩包")
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
    skill = store.get_skill(skill_id)
    if skill and skill.get("source") == "builtin":
        raise HTTPException(400, "内建 Skill 不支持删除")
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


@dashboard_api.post("/ai/test/gateway")
def test_gateway_ai_config(
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    config = store.get_ai_config("gateway")
    if config is None:
        fallback = request.app.state.settings.ai_config()
        config = fallback.to_dict() if fallback is not None else None
    if config is None:
        raise HTTPException(404, "当前没有可测试的 Gateway AI 配置")
    return _test_ai_config(request, config=config, source="config_test")


@dashboard_api.post("/ai/test/devices/{device_id}")
def test_device_ai_config(
    device_id: str,
    request: Request,
    store: GatewayStore = Depends(_get_store),
) -> dict:
    if not store.get_device(device_id):
        raise HTTPException(404, "设备不存在")
    config = _resolve_effective_client_ai_config(store, request.app.state.settings, device_id)
    if config is None:
        raise HTTPException(404, "当前设备没有可测试的 AI 配置")
    return _test_ai_config(
        request,
        config=config,
        source="config_test",
        device_id=device_id,
    )


@dashboard_api.get("/ai/calls")
def list_ai_calls(
    request: Request,
    source: str | None = None,
    device_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    store: GatewayStore = request.app.state.store
    return [
        _serialize_ai_call(call)
        for call in store.list_ai_calls(source=source, device_id=device_id, limit=limit)
    ]


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
    store: GatewayStore = request.app.state.store
    return {
        "gateway_ai": _resolve_gateway_ai_summary(store, request),
        "client_ai": _resolve_client_ai_summaries(store, request),
    }
