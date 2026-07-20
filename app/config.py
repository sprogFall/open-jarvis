"""应用配置。

通过 pydantic-settings 从环境变量加载，密钥只从这里注入，不进入 Prompt、
Checkpoint、日志和 SSE。
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用
    app_env: str = Field(default="development", description="运行环境")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_log_level: str = Field(default="INFO")

    # PostgreSQL
    database_url: str = Field(
        default="postgresql+asyncpg://jarvis:jarvis@localhost:5432/open_jarvis"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # LLM 密钥：仅从环境变量注入
    openai_api_key: str = Field(default="")
    openai_api_url: str = Field(default="")

    # LLM 路由配置（新增）
    llm_fast_model: str = Field(default="deepseek-ai/DeepSeek-V4-Flash", description="fast 档位模型名")
    llm_standard_model: str = Field(default="deepseek-ai/DeepSeek-V4-Pro", description="standard 档位模型名")
    llm_reasoning_model: str = Field(default="zai-org/GLM-5.2", description="reasoning 档位模型名")
    llm_temperature: float = Field(default=0.0, description="采样温度，0 表示尽量确定性")
    llm_request_timeout: int = Field(default=60, description="单次模型调用超时（秒）")
    llm_max_retries: int = Field(default=2, ge=0, description="OpenAI SDK 单次调用重试次数")
    llm_sdk_log_level: str = Field(
        default="DEBUG",
        description="OpenAI SDK 日志级别；DEBUG 会显示每次重试前的底层异常",
    )

    # 可观测性
    otel_exporter_otlp_endpoint: str = Field(default="")
    otel_service_name: str = Field(default="open-jarvis")

    # tool配置
    tavily_api_key: str = Field(default="", description="tavily服务的api_key,通过https://app.tavily.com 获取")

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
