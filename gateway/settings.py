from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from client.ai import AIModelConfig, coerce_ai_config


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_storage_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = _project_root() / path
    return path.resolve()


def _normalize_database_url(raw_url: str | None) -> str:
    if not raw_url:
        return f"sqlite:///{_resolve_storage_path('gateway/gateway.db')}"
    return _normalize_storage_target(raw_url, "gateway/gateway.db")


def _normalize_storage_target(raw_target: str | None, default_relative_path: str) -> str:
    if not raw_target:
        raw_target = default_relative_path
    if raw_target.startswith("postgresql://"):
        return raw_target
    for prefix in ("sqlite:///", "sqlite://"):
        if raw_target.startswith(prefix):
            return f"sqlite:///{_resolve_storage_path(raw_target[len(prefix):])}"
    return str(_resolve_storage_path(raw_target))


@dataclass(slots=True)
class GatewaySettings:
    database_url: str = f"sqlite:///{_project_root() / 'gateway' / 'gateway.db'}"
    jwt_secret: str = "change-me-change-me-change-me-1234"
    jwt_algorithm: str = "HS256"
    admin_username: str = "operator"
    admin_password: str = "passw0rd"
    device_keys: dict[str, str] = field(default_factory=lambda: {"device-alpha": "device-secret"})
    dashboard_origins: list[str] = field(default_factory=list)
    skill_archives_path: Path | None = None
    allowed_roots: list[Path] = field(default_factory=lambda: [Path.cwd().resolve()])
    iot_base_url: str | None = None
    iot_token: str | None = None
    local_checkpoint_path: str = str(_resolve_storage_path("gateway/local-client.db"))
    local_workflow_store_path: str = str(_resolve_storage_path("gateway/local-langgraph.db"))
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_api_key: str | None = None
    ai_base_url: str | None = None

    def ai_config(self) -> AIModelConfig | None:
        return coerce_ai_config(
            {
                "provider": self.ai_provider,
                "model": self.ai_model,
                "api_key": self.ai_api_key,
                "base_url": self.ai_base_url,
            }
        )

    @classmethod
    def from_env(cls) -> "GatewaySettings":
        raw_device_keys = os.getenv("OMNI_AGENT_DEVICE_KEYS", "device-alpha=device-secret")
        device_keys: dict[str, str] = {}
        for pair in raw_device_keys.split(","):
            if not pair.strip():
                continue
            device_id, device_key = pair.split("=", 1)
            device_keys[device_id.strip()] = device_key.strip()
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            legacy_database = os.getenv("OMNI_AGENT_GATEWAY_DB")
            if legacy_database:
                database_url = legacy_database
        raw_dashboard_origins = os.getenv("OMNI_AGENT_DASHBOARD_ORIGINS", "")
        dashboard_origins = [
            origin.strip()
            for origin in raw_dashboard_origins.split(",")
            if origin.strip()
        ]
        roots = os.getenv("OMNI_AGENT_GATEWAY_ALLOWED_ROOTS", str(Path.cwd())).split(":")
        normalized_database_url = _normalize_database_url(database_url)
        raw_local_checkpoint_path = os.getenv("OMNI_AGENT_GATEWAY_LOCAL_CHECKPOINT_DB", "").strip()
        raw_local_workflow_store_path = os.getenv(
            "OMNI_AGENT_GATEWAY_LOCAL_LANGGRAPH_DB",
            "",
        ).strip()
        return cls(
            database_url=normalized_database_url,
            jwt_secret=os.getenv(
                "OMNI_AGENT_JWT_SECRET", "change-me-change-me-change-me-1234"
            ),
            admin_username=os.getenv("OMNI_AGENT_ADMIN_USERNAME", "operator"),
            admin_password=os.getenv("OMNI_AGENT_ADMIN_PASSWORD", "passw0rd"),
            device_keys=device_keys or {"device-alpha": "device-secret"},
            dashboard_origins=dashboard_origins,
            skill_archives_path=(
                Path(os.getenv("OMNI_AGENT_SKILL_ARCHIVES_DIR")).expanduser().resolve()
                if os.getenv("OMNI_AGENT_SKILL_ARCHIVES_DIR")
                else None
            ),
            allowed_roots=[Path(root).expanduser().resolve() for root in roots if root],
            iot_base_url=os.getenv("OMNI_AGENT_GATEWAY_IOT_BASE_URL"),
            iot_token=os.getenv("OMNI_AGENT_GATEWAY_IOT_TOKEN"),
            local_checkpoint_path=_normalize_storage_target(
                raw_local_checkpoint_path or (
                    normalized_database_url
                    if normalized_database_url.startswith("postgresql://")
                    else None
                ),
                "gateway/local-client.db",
            ),
            local_workflow_store_path=_normalize_storage_target(
                raw_local_workflow_store_path or (
                    normalized_database_url
                    if normalized_database_url.startswith("postgresql://")
                    else None
                ),
                "gateway/local-langgraph.db",
            ),
            ai_provider=os.getenv("OMNI_AGENT_GATEWAY_AI_PROVIDER"),
            ai_model=os.getenv("OMNI_AGENT_GATEWAY_AI_MODEL"),
            ai_api_key=os.getenv("OMNI_AGENT_GATEWAY_AI_API_KEY"),
            ai_base_url=os.getenv("OMNI_AGENT_GATEWAY_AI_BASE_URL"),
        )
