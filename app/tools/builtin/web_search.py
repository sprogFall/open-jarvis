"""网络搜索工具"""

from __future__ import annotations

from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from tavily import TavilyClient

from app.config import get_settings
from app.tools import ToolSpec


def _get_tavily_client() -> TavilyClient:
    api_key = get_settings().tavily_api_key
    if not api_key:
        raise RuntimeError("Tavily的APIKEY未配置")
    return TavilyClient(api_key=api_key)


class WebSearchInput(BaseModel):
    query: str = Field(description="搜索关键词")
    max_results: int = Field(default=5, description="搜索返回结果最大数量，默认 5")
    include_answer: bool = Field(default=False, description="是否包含 AI 生成的摘要答案")
    include_raw_content: bool = Field(default=False, description="是否包含原始网页内容")
    search_depth: Literal["basic", "advanced"] = Field(
        default="basic",
        description="搜索深度: 'basic'(快速) 或 'advanced'(深度搜索，耗时更长)",
    )


@tool(args_schema=WebSearchInput,
      description=(
              "使用 Tavily 搜索引擎搜索互联网，获取实时网页信息。"
              "适用于需要最新资讯、事实查询等场景。"
      ))
async def web_search_tool(
        query: str,
        max_results: int = 5,
        include_answer: bool = False,
        include_raw_content: bool = False,
        search_depth: Literal["basic", "advanced"] = "basic",
) -> list[str]:
    try:
        client = _get_tavily_client()
        response = client.search(
            query=query,
            max_results=max_results,
            include_answer=include_answer,
            include_raw_content=include_raw_content,
            search_depth=search_depth,
        )
    except Exception as e:
        return [f"搜索失败: {e}"]
    results: list[str] = []

    # 如果有 AI 摘要，放在最前面
    if include_answer and response.get("answer"):
        results.append(f"[摘要] {response['answer']}")

    for item in response.get("results", []):
        title = item.get("title", "无标题")
        url = item.get("url", "")
        content = item.get("content", "")
        results.append(f"[{title}]({url})\n{content}")

    if not results:
        return ["未找到相关结果。"]

    return results


web_search_spec = ToolSpec(
    name="web_search",
    description=(
        "使用 Tavily 搜索引擎搜索互联网，获取实时网页信息。"
        "适用于需要最新资讯、事实查询等场景。"
    ),
    parameters_schema=web_search_tool.args_schema.model_json_schema(),
    idempotent=True,
    executor=web_search_tool
)
