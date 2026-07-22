"""单次运行的权威时钟上下文。

在 create_run 时写入一次，整次 run（含 replan）保持不变，供 Planner /
Executor / Reviewer / Finalizer 注入 Prompt，避免模型把训练截止日当成“现在”。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RunContext(BaseModel):
    """运行级环境事实（非用户请求）。"""

    now_iso: str = Field(description="权威当前时刻的 ISO8601 表示（含时区偏移）")
    timezone: str = Field(description="IANA 时区名，如 Asia/Shanghai")
    date_local: str = Field(description="本地日历日期 YYYY-MM-DD")
    time_local: str = Field(description="本地时间 HH:MM")
    weekday_local: str = Field(description="本地星期，如 星期三")


__all__ = ["RunContext"]
