"""Worker 恢复逻辑：读取最近 Checkpoint 继续执行。

已经成功写入的幂等任务不会重复产生副作用。
"""

from __future__ import annotations


__all__: list[str] = []
