from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class GatewaySettings:
    database_url: str = "sqlite:///gateway/gateway.db"
    jwt_secret: str = "change-me-change-me-change-me-1234"
    jwt_algorithm: str = "HS256"
    admin_username: str = "operator"
    admin_password: str = "passw0rd"
    device_keys: dict[str, str] = field(default_factory=lambda: {"device-alpha": "device-secret"})
    dashboard_origins: list[str] = field(default_factory=list)

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
                database_url = str(Path(legacy_database).expanduser())
        raw_dashboard_origins = os.getenv("OMNI_AGENT_DASHBOARD_ORIGINS", "")
        dashboard_origins = [
            origin.strip()
            for origin in raw_dashboard_origins.split(",")
            if origin.strip()
        ]
        return cls(
            database_url=database_url or "sqlite:///gateway/gateway.db",
            jwt_secret=os.getenv(
                "OMNI_AGENT_JWT_SECRET", "change-me-change-me-change-me-1234"
            ),
            admin_username=os.getenv("OMNI_AGENT_ADMIN_USERNAME", "operator"),
            admin_password=os.getenv("OMNI_AGENT_ADMIN_PASSWORD", "passw0rd"),
            device_keys=device_keys or {"device-alpha": "device-secret"},
            dashboard_origins=dashboard_origins,
        )
