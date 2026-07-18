"""Run 相关路由：创建运行、查询状态、计划、SSE 事件、取消。

对应架构设计第 9 节 API 与事件协议。
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.run import create_run, get_run_result

router = APIRouter()

class CreateRunRequest(BaseModel):
    user_request: str = Field(..., min_length=1, description="用户目标/需求")

class CreateRunResponse(BaseModel):
    run_id: str
    status: str

@router.post("", response_model=CreateRunResponse)
async def create_run_endpoint(req: CreateRunRequest) -> CreateRunResponse:
    """POST 创建运行"""
    run_id = await create_run(req.user_request)
    return CreateRunResponse(run_id=run_id, status="created")

@router.get("/{run_id}")
async def get_run(run_id: str) -> dict:
    """GET /runs/{run_id} 查询状态、预算和最终结果。"""
    result = await get_run_result(run_id)
    if result is None:
        return {"run_id": run_id, "status": "not_found"}
    return result
