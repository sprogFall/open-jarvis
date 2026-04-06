from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from client.ai import AIModelConfig, coerce_ai_config
from client.storage import (
    StorageTarget,
    is_postgres_target,
    normalize_storage_target,
)


@dataclass(slots=True)
class ClientConfig:
    gateway_http_url: str = "http://127.0.0.1:8000"
    device_id: str = "device-alpha"
    device_key: str = "device-secret"
    checkpoint_path: StorageTarget = normalize_storage_target("client/client.db")
    workflow_store_path: StorageTarget = normalize_storage_target("client/langgraph.db")
    skills_workspace: Path = Path("client/skills-runtime")
    allowed_roots: list[Path] = field(default_factory=lambda: [Path.cwd()])
    iot_base_url: str | None = None
    iot_token: str | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_api_key: str | None = None
    ai_base_url: str | None = None

    @property
    def gateway_ws_url(self) -> str:
        if self.gateway_http_url.startswith("https://"):
            return self.gateway_http_url.replace("https://", "wss://", 1)
        return self.gateway_http_url.replace("http://", "ws://", 1)

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
    def from_env(cls) -> "ClientConfig":
        roots = os.getenv("OMNI_AGENT_ALLOWED_ROOTS", str(Path.cwd())).split(":")
        gateway_http_url = os.getenv("OMNI_AGENT_GATEWAY_URL", "http://127.0.0.1:8000")
        raw_checkpoint_path = os.getenv("OMNI_AGENT_CHECKPOINT_DB", "").strip()
        checkpoint_target = normalize_storage_target(
            raw_checkpoint_path or "client/client.db"
        )
        raw_workflow_store_path = os.getenv("OMNI_AGENT_LANGGRAPH_DB", "").strip()
        workflow_target = normalize_storage_target(
            raw_workflow_store_path
            or (
                checkpoint_target
                if is_postgres_target(checkpoint_target)
                else "client/langgraph.db"
            )
        )
        return cls(
            gateway_http_url=gateway_http_url,
            device_id=os.getenv("OMNI_AGENT_DEVICE_ID", "device-alpha"),
            device_key=os.getenv("OMNI_AGENT_DEVICE_KEY", "device-secret"),
            checkpoint_path=checkpoint_target,
            workflow_store_path=workflow_target,
            skills_workspace=Path(
                os.getenv("OMNI_AGENT_SKILLS_WORKSPACE", "client/skills-runtime")
            ),
            allowed_roots=[Path(root).expanduser().resolve() for root in roots if root],
            iot_base_url=os.getenv("OMNI_AGENT_IOT_BASE_URL"),
            iot_token=os.getenv("OMNI_AGENT_IOT_TOKEN"),
            ai_provider=os.getenv("OMNI_AGENT_CLIENT_AI_PROVIDER"),
            ai_model=os.getenv("OMNI_AGENT_CLIENT_AI_MODEL"),
            ai_api_key=os.getenv("OMNI_AGENT_CLIENT_AI_API_KEY"),
            ai_base_url=os.getenv("OMNI_AGENT_CLIENT_AI_BASE_URL"),
        )
