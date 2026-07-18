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
    anthropic_api_key: str = Field(default="")

    # 可观测性
    otel_exporter_otlp_endpoint: str = Field(default="")
    otel_service_name: str = Field(default="open-jarvis")

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
