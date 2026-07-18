"""Run 相关路由：创建运行、查询状态、计划、SSE 事件、取消。

对应架构设计第 9 节 API 与事件协议。
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post("")
async def create_run() -> dict[str, str]:
    """POST /runs 创建运行；支持 Idempotency-Key。"""
    return {"status": "not_implemented"}


@router.get("/{run_id}")
async def get_run(run_id: str) -> dict[str, str]:
    """GET /runs/{run_id} 查询状态、预算和最终结果。"""
    return {"run_id": run_id, "status": "not_implemented"}


@router.get("/{run_id}/plan")
async def get_run_plan(run_id: str) -> dict[str, str]:
    """GET /runs/{run_id}/plan 获取当前计划、任务状态及版本。"""
    return {"run_id": run_id, "status": "not_implemented"}


@router.get("/{run_id}/events")
async def stream_run_events(run_id: str) -> dict[str, str]:
    """GET /runs/{run_id}/events SSE 实时事件；支持 Last-Event-ID。"""
    return {"run_id": run_id, "status": "not_implemented"}


@router.post("/{run_id}/cancel")
async def cancel_run(run_id: str) -> dict[str, str]:
    """POST /runs/{run_id}/cancel 发起协作式取消。"""
    return {"run_id": run_id, "status": "not_implemented"}
