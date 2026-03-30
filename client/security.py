from __future__ import annotations

import hashlib
import hmac


def build_device_signature(device_id: str, timestamp: int, device_key: str) -> str:
    payload = f"{device_id}:{timestamp}".encode("utf-8")
    return hmac.new(device_key.encode("utf-8"), payload, hashlib.sha256).hexdigest()
