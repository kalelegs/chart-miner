from __future__ import annotations

import os
from typing import Literal, cast

from agents import set_default_openai_api, set_default_openai_client, set_tracing_disabled
from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field, field_validator


OpenAIAPI = Literal["chat_completions", "responses"]


class LLMSettings(BaseModel):
    """OpenAI or OpenAI-compatible model settings."""

    model_config = ConfigDict(frozen=True)

    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    api: OpenAIAPI | None = None
    tracing_enabled: bool | None = None

    @field_validator("model", "api_key", "base_url", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def uses_custom_endpoint(self) -> bool:
        return self.base_url is not None

    @property
    def resolved_api(self) -> OpenAIAPI | None:
        if self.api is not None:
            return self.api
        if self.uses_custom_endpoint:
            return "chat_completions"
        return None

    @property
    def resolved_api_key(self) -> str | None:
        if self.api_key is not None:
            return self.api_key
        if self.uses_custom_endpoint:
            return "local-api-key"
        return None

    @classmethod
    def from_env(cls) -> "LLMSettings":
        return cls(
            model=os.getenv("CHART_MINER_MODEL") or os.getenv("OPENAI_MODEL"),
            api_key=os.getenv("CHART_MINER_API_KEY") or os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("CHART_MINER_BASE_URL") or os.getenv("OPENAI_BASE_URL"),
            api=_read_api(),
            tracing_enabled=_read_optional_bool("CHART_MINER_ENABLE_TRACING"),
        )


class LLMRuntimeConfig(BaseModel):
    """Display-safe LLM configuration used for this run."""

    model_config = ConfigDict(frozen=True)

    model: str | None
    endpoint: str
    api: OpenAIAPI | None


def configure_llm(settings: LLMSettings | None = None) -> LLMRuntimeConfig:
    settings = settings or LLMSettings.from_env()

    if settings.resolved_api is not None:
        set_default_openai_api(settings.resolved_api)

    if settings.uses_custom_endpoint:
        client = AsyncOpenAI(
            api_key=settings.resolved_api_key,
            base_url=settings.base_url,
        )
        set_default_openai_client(
            client,
            use_for_tracing=bool(settings.tracing_enabled),
        )

        if settings.tracing_enabled is not True:
            set_tracing_disabled(True)

    return LLMRuntimeConfig(
        model=settings.model,
        endpoint=settings.base_url or "OpenAI default endpoint",
        api=settings.resolved_api,
    )


def _read_api() -> OpenAIAPI | None:
    value = os.getenv("CHART_MINER_OPENAI_API")
    if value is None or not value.strip():
        return None

    normalized = value.strip().lower()
    if normalized not in {"chat_completions", "responses"}:
        raise ValueError(
            "CHART_MINER_OPENAI_API must be either 'chat_completions' or 'responses'."
        )
    return cast(OpenAIAPI, normalized)


def _read_optional_bool(name: str) -> bool | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(f"{name} must be true or false.")
