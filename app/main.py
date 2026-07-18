"""FastAPI 应用入口。

生产环境建议通过 `uvicorn app.main:app --host 0.0.0.0 --port 8000` 启动 API 进程，
Worker 进程通过 `python -m app.worker.consumer` 启动。
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.router import api_router
from app.config import get_settings
from app.observability.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(level=settings.app_log_level)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Open Jarvis Agent",
        description="基于 LangChain + LangGraph 的可恢复、多任务 Agent 编排系统",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
