from __future__ import annotations

from typing import Any

from client.ai import AIModelConfig, StructuredModelClient, coerce_ai_config, resolve_model_endpoint
from gateway.settings import GatewaySettings
from gateway.store import GatewayStore


GATEWAY_LOCAL_DEVICE_ID = "gateway-local"


class GatewayAIConfigResolver:
    def __init__(self, store: GatewayStore, settings: GatewaySettings) -> None:
        self.store = store
        self.settings = settings

    def resolve(self) -> AIModelConfig | None:
        return coerce_ai_config(self.store.get_ai_config("gateway") or self.settings.ai_config())


class GatewayTaskRouter:
    def __init__(
        self,
        store: GatewayStore,
        settings: GatewaySettings,
        *,
        model_client_factory=None,
    ) -> None:
        self.store = store
        self.settings = settings
        self.model_client_factory = model_client_factory or StructuredModelClient
        self.config_resolver = GatewayAIConfigResolver(store, settings)

    def route(self, instruction: str, candidates: list[dict[str, Any]]) -> dict[str, str]:
        config = self.config_resolver.resolve()
        if config is None:
            raise RuntimeError("未指定 device_id 时，Gateway 需要先配置 AI 供应商")
        system_prompt = self._system_prompt(candidates)
        user_prompt = f"用户任务：{instruction}"
        try:
            response = self.model_client_factory(config).generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except Exception as exc:
            self.store.record_ai_call(
                source="gateway_router",
                provider=config.provider,
                model=config.model,
                endpoint=resolve_model_endpoint(config),
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                error=str(exc),
            )
            raise
        device_id = str(response.get("device_id", "")).strip()
        if device_id not in {candidate["device_id"] for candidate in candidates}:
            raise ValueError(f"AI routed to unknown device: {device_id}")
        rewritten_instruction = str(response.get("instruction") or instruction).strip()
        self.store.record_ai_call(
            source="gateway_router",
            device_id=device_id,
            provider=config.provider,
            model=config.model,
            endpoint=resolve_model_endpoint(config),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response=response,
        )
        return {
            "device_id": device_id,
            "instruction": rewritten_instruction or instruction,
            "reason": str(response.get("reason") or "").strip(),
        }

    @staticmethod
    def _system_prompt(candidates: list[dict[str, Any]]) -> str:
        rendered_candidates = []
        for candidate in candidates:
            skills = ", ".join(candidate.get("skills") or []) or "无"
            rendered_candidates.append(
                f"- device_id={candidate['device_id']} "
                f"name={candidate.get('name') or candidate['device_id']} "
                f"type={candidate.get('type') or 'cli'} "
                f"skills={skills}"
            )
        return (
            "你是 OpenJarvis Gateway 的任务分发器。"
            "你必须从候选执行端中选择唯一一个 device_id，并只返回 JSON 对象。"
            "优先选择技能和任务语义更匹配的执行端；如果任务适合在网关本机执行，可选择 gateway-local。"
            "返回格式："
            "{\"device_id\":\"...\",\"instruction\":\"可选的重写任务描述\",\"reason\":\"简短原因\"}\n"
            f"候选执行端：\n{chr(10).join(rendered_candidates)}"
        )
