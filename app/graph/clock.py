"""运行时钟：生成与格式化权威当前时间，供各节点 Prompt 注入。"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import get_settings
from app.domain.run_context import RunContext
from app.graph.state import RunState

_WEEKDAY_CN = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")

_CLOCK_RULES = (
    "规则：以上时间为系统权威“现在”，不要用你的训练数据截止日当作当前日期。"
    "涉及“最新/近期/今年/本周”时优先用工具查实，并在输出中写明信息截至日期；"
    "无法核实时效时明确标注不确定，不要编造“刚刚发生”的事实。"
)


def build_run_context(
    *,
    timezone_name: str | None = None,
    now: datetime | None = None,
) -> RunContext:
    """构造本次 run 的权威时钟；timezone 非法时回退 UTC。"""
    tz_name = timezone_name or get_settings().app_timezone
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz_name = "UTC"
        tz = ZoneInfo("UTC")
    moment = now.astimezone(tz) if now is not None else datetime.now(tz)
    return RunContext(
        now_iso=moment.isoformat(timespec="seconds"),
        timezone=tz_name,
        date_local=moment.strftime("%Y-%m-%d"),
        time_local=moment.strftime("%H:%M"),
        weekday_local=_WEEKDAY_CN[moment.weekday()],
    )


def format_clock(run_context: RunContext | None) -> str:
    """格式化为 Prompt 可读的时间块（含简短规则）。"""
    if run_context is None:
        return "（系统未注入当前时间）\n" + _CLOCK_RULES
    return (
        f"{run_context.date_local} {run_context.time_local} "
        f"({run_context.weekday_local}, {run_context.timezone})\n"
        f"ISO: {run_context.now_iso}\n"
        f"{_CLOCK_RULES}"
    )


def format_clock_from_state(state: RunState) -> str:
    """从 RunState 读取 run_context 并格式化。"""
    return format_clock(state.get("run_context"))


__all__ = ["build_run_context", "format_clock", "format_clock_from_state"]
