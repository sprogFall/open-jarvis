"""队列消费者：从 Redis run_queue 领取待运行任务并驱动 LangGraph 工作流。"""

from __future__ import annotations


async def consume() -> None:
    """消费运行队列。

    TODO: 从 Redis run_queue 消费组领取待运行任务，使用 run_id 作为
    LangGraph thread_id，驱动图执行并写入事件流。
    """
    raise NotImplementedError("Worker 消费循环待实现")


__all__ = ["consume"]
