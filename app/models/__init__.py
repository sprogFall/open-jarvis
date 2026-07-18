"""LLM 配置与模型路由。

对应架构设计第 6 节：模型通过 LangChain 接口适配，按 fast / standard / reasoning
三档配置，业务代码不绑定具体厂商。
"""
from app.models.base import ModelTier
from app.models.router import get_model, get_model_for_run

__all__: ["ModelTier", "get_model", "get_model_for_run"]