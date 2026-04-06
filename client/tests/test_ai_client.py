from __future__ import annotations

from client.ai import AIModelConfig, resolve_model_endpoint


def test_resolve_model_endpoint_appends_chat_completions_for_openai_compatible_root_url():
    config = AIModelConfig(
        provider="custom",
        model="qwen-max",
        api_key="test-secret",
        base_url="https://api-inference.modelscope.cn/v1",
    )

    assert (
        resolve_model_endpoint(config)
        == "https://api-inference.modelscope.cn/v1/chat/completions"
    )


def test_resolve_model_endpoint_appends_messages_for_anthropic_root_url():
    config = AIModelConfig(
        provider="anthropic",
        model="claude-3-5-sonnet",
        api_key="test-secret",
        base_url="https://api.anthropic.com/v1",
    )

    assert resolve_model_endpoint(config) == "https://api.anthropic.com/v1/messages"
