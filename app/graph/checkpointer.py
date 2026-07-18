"""PostgreSQL Checkpointer 生命周期管理。

对应架构设计第 8.1 节：图快照由 LangGraph PostgreSQL Checkpointer 管理表承载，
可从节点边界恢复执行。使用 psycopg3 + AsyncConnectionPool，API 与未来独立 Worker
进程共享同一套 checkpoint 表。

惰性初始化：首次 get_checkpointer() 时创建连接池、构造 saver、执行 setup() 建表；
close_checkpointer() 在应用退出时关闭连接池。测试中若直接注入 fake graph 则不会
触发本模块（get_graph 在 _graph 已缓存时直接返回）。
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.config import get_settings
from app.graph.serde import make_serde

logger = logging.getLogger(__name__)

_pool: AsyncConnectionPool[Any] | None = None
_saver: Any | None = None
_lock: asyncio.Lock | None = None


def _sanitize_url(url: str) -> str:
    """移除数据库 URL 中的密码，避免泄漏到日志。"""
    return re.sub(r"(://[^:]+):([^@]+)@", r"\1:***@", url)


def _get_lock() -> asyncio.Lock:
    global _lock
    if _lock is None:
        _lock = asyncio.Lock()
    return _lock


def _to_psycopg_conn_string(database_url: str) -> str:
    """将 SQLAlchemy 风格的 database_url 转为 psycopg 可用的连接串。

    postgresql+asyncpg://... → postgresql://...
    纯 postgresql:// 连接串原样返回。
    """
    return database_url.replace("+asyncpg", "")


async def get_checkpointer() -> Any:
    """惰性创建并返回 AsyncPostgresSaver（含连接池与建表）。

    首次调用时创建连接池、构造 saver、执行 setup() 建表；后续直接返回缓存。
    使用 asyncio.Lock 保证并发首次调用安全。
    """
    global _pool, _saver
    if _saver is not None:
        return _saver

    async with _get_lock():
        if _saver is not None:
            return _saver

        # 延迟导入：避免未使用 postgres checkpointer 的场景（如健康检查、fake graph 测试）
        # 在 import 阶段就拉起 psycopg。
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        settings = get_settings()
        conn_string = _to_psycopg_conn_string(settings.database_url)
        serde = make_serde()

        _pool = AsyncConnectionPool(
            conninfo=conn_string,
            kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
            open=False,
        )
        try:
            await _pool.open()
            _saver = AsyncPostgresSaver(conn=_pool, serde=serde)
            await _saver.setup()
        except Exception:
            await _pool.close()
            _pool = None
            raise
        logger.info("PostgreSQL checkpointer 已就绪: %s", _sanitize_url(conn_string))
        return _saver


async def close_checkpointer() -> None:
    """关闭连接池，应用退出时调用。未初始化时为空操作。"""
    global _pool, _saver
    _saver = None
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL checkpointer 连接池已关闭")


__all__ = ["get_checkpointer", "close_checkpointer"]
