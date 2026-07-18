"""FastAPI 应用入口。

生产环境建议通过 `uvicorn app.main:app --host 0.0.0.0 --port 8000` 启动 API 进程，
Worker 进程通过 `python -m app.worker.consumer` 启动。
"""

from __future__ import annotations

import asyncio
import sys

# Windows 下 psycopg3 异步模式不支持默认的 ProactorEventLoop，
# 必须在事件循环创建前切换到 SelectorEventLoop（uvicorn 导入本模块时即生效）。
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config import get_settings
from app.observability.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(
        level=settings.app_log_level,
        llm_sdk_level=settings.llm_sdk_log_level,
    )
    yield
    # 取消并等待运行中的图任务，避免强制终止导致状态不一致
    from app.services.run import running_tasks

    for _rid, task in list(running_tasks.items()):
        if not task.done():
            task.cancel()
    for _rid, task in list(running_tasks.items()):
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    # 关闭 PostgreSQL checkpointer 连接池（未初始化时为空操作）
    from app.graph.checkpointer import close_checkpointer

    await close_checkpointer()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Open Jarvis Agent",
        description="基于 LangChain + LangGraph 的可恢复、多任务 Agent 编排系统",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
