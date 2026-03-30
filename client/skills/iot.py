from __future__ import annotations

import json
from urllib import request


class IoTSkill:
    def __init__(self, base_url: str | None, token: str | None) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.token = token

    def set_device_state(self, entity_id: str, state: str) -> str:
        if not self.base_url:
            raise RuntimeError("IoT base URL is not configured")
        payload = json.dumps({"entity_id": entity_id, "state": state}).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/devices/state",
            data=payload,
            headers={
                "Content-Type": "application/json",
                **(
                    {"Authorization": f"Bearer {self.token}"}
                    if self.token
                    else {}
                ),
            },
            method="POST",
        )
        with request.urlopen(req, timeout=5) as response:
            return response.read().decode("utf-8")
