"""聚合所有 v1 路由。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import runs, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(runs.router, prefix="/runs", tags=["runs"])
