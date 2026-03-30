from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import jwt

from gateway.settings import GatewaySettings


def issue_access_token(settings: GatewaySettings, subject: str) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=12)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_access_token(settings: GatewaySettings, token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def sign_device_request(device_id: str, timestamp: int, device_key: str) -> str:
    payload = f"{device_id}:{timestamp}".encode("utf-8")
    return hmac.new(device_key.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_device_signature(
    settings: GatewaySettings,
    device_id: str,
    timestamp: int,
    signature: str,
) -> bool:
    device_key = settings.device_keys.get(device_id)
    if not device_key:
        return False
    expected = sign_device_request(device_id, timestamp, device_key)
    return hmac.compare_digest(expected, signature)

