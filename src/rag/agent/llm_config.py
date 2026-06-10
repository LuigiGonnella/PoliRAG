"""LLM provider configuration used by the agent graph."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LLMConfig:
    key: str | None
    base_url: str
    model: str

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            key=os.environ.get("LLM_API_KEY"),
            base_url=os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
            model=os.environ.get("LLM_MODEL", "deepseek/deepseek-v4-pro"),
        )

    @classmethod
    def coerce(cls, value: "LLMConfig | dict[str, Any] | Any") -> "LLMConfig":
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                key=value.get("key") or value.get("api_key"),
                base_url=value.get("base_url") or "https://openrouter.ai/api/v1",
                model=value.get("model") or "deepseek/deepseek-v4-pro",
            )
        return cls(
            key=getattr(value, "key", None),
            base_url=getattr(value, "base_url", "https://openrouter.ai/api/v1"),
            model=getattr(value, "model", "deepseek/deepseek-v4-pro"),
        )

    def require_api_key(self) -> str:
        if not self.key:
            raise ValueError("LLM_API_KEY is required to initialize the chat model.")
        return self.key


class LLMconfig(LLMConfig):
    """Backward-compatible alias for existing imports."""

    def __init__(self):
        config = LLMConfig.from_env()
        super().__init__(key=config.key, base_url=config.base_url, model=config.model)
