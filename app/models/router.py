"""模型路由：根据 Assignment.model_tier 返回对应 LangChain 模型实例。"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from pydantic import SecretStr

from app.config import get_settings
from app.models.base import ModelTier

_TIER_TO_SETTING_KEY: dict[str, str] = {
    ModelTier.fast: "llm_fast_model",
    ModelTier.standard: "llm_standard_model",
    ModelTier.reasoning: "llm_reasoning_model",
}


def get_model(tier: str) -> BaseChatModel:
    """按 fast / standard / reasoning 三档返回模型实例。
    """
    settings = get_settings()
    # 当前模型
    model_setting_key = _TIER_TO_SETTING_KEY.get(tier, "llm_standard_model")
    model_name = getattr(settings, model_setting_key)
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model_name,
        temperature=settings.llm_temperature,
        base_url=settings.openai_api_url,
        api_key=SecretStr(settings.openai_api_key),
        timeout=settings.llm_request_timeout
    )

def get_model_for_run(config: RunnableConfig | None, tier: str) -> BaseChatModel:
    """节点统一入口：优先从 config 注入取模型，回退到生产工厂。

    用法：
        async def planner(state, config):
            model = get_model_for_run(config, ModelTier.standard)

    测试时通过 graph.ainvoke(state, config={"configurable": {
        "thread_id": ..., "models": {ModelTier.standard: fake_model}
    }}) 注入 fake model，不烧 Token。
    """
    if config is not None:
        configurable = config.get("configurable", {})
        models = configurable.get("models")
        if models and tier in models:
            return models[tier]
    return get_model(tier)

__all__ = ["get_model", "get_model_for_run"]
