"""模型路由：根据 Assignment.model_tier 返回对应 LangChain 模型实例。"""

from __future__ import annotations


def get_model(tier: str) -> object:
    """按 fast / standard / reasoning 三档返回模型实例。

    TODO: 通过 LangChain 接口适配，业务代码不绑定具体厂商。
    """
    raise NotImplementedError(f"模型档位 {tier} 未配置")


__all__ = ["get_model"]
