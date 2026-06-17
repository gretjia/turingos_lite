"""Provider profiles: auth modes, thinking knobs, worker OAuth vs API (Software 3.0 broker)."""
from __future__ import annotations

from typing import Any, Literal

AuthMode = Literal["api_key", "oauth", "cli", "env"]

# Facilitator / Meta AI — OpenAI-compatible API brokers
PROVIDER_PROFILES: dict[str, dict[str, Any]] = {
    "deepseek": {
        "label": "DeepSeek",
        "docs_url": "https://api-docs.deepseek.com/",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "models": {
            "deepseek-chat": {"thinking": False},
            "deepseek-reasoner": {"thinking": True, "note": "内置 reasoning，无需 extra_body"},
        },
        "auth_modes": ["api_key"],
        "token_prefixes": ["sk-"],
        "keywords": ["deepseek", "深度求索"],
        "extra_body_default": None,
    },
    "openai": {
        "label": "OpenAI",
        "docs_url": "https://platform.openai.com/docs/api-reference",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "models": {"gpt-4o-mini": {"thinking": False}, "o3-mini": {"thinking": True}},
        "auth_modes": ["api_key", "oauth"],
        "token_prefixes": ["sk-"],
        "keywords": ["openai", "chatgpt"],
        "extra_body_default": None,
    },
    "nvidia": {
        "label": "NVIDIA Integrate",
        "docs_url": "https://docs.api.nvidia.com/nim/reference/",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "default_model": "google/gemma-3-27b-it",
        "models": {
            "google/diffusiongemma-26b-a4b-it": {
                "thinking": False,
                "facilitator_default": True,
            },
            "nvidia/nemotron-4-340b-instruct": {"thinking": True},
        },
        "auth_modes": ["api_key"],
        "token_prefixes": ["nvapi-"],
        "keywords": ["nvidia", "nvapi", "nemotron", "diffusiongemma"],
        "extra_body_default": {"chat_template_kwargs": {"enable_thinking": True}},
        "thinking_toggle": "extra_body.chat_template_kwargs.enable_thinking",
    },
    "anthropic": {
        "label": "Anthropic",
        "docs_url": "https://docs.anthropic.com/en/api/getting-started",
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-sonnet-4-20250514",
        "auth_modes": ["api_key", "oauth"],
        "token_prefixes": ["sk-ant-"],
        "keywords": ["anthropic", "claude"],
        "extra_body_default": None,
    },
    "groq": {
        "label": "Groq",
        "docs_url": "https://console.groq.com/docs/quickstart",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "auth_modes": ["api_key"],
        "token_prefixes": ["gsk_"],
        "keywords": ["groq"],
    },
}

# Worker execution — OAuth CLI vs API whitebox
WORKER_PROFILES: dict[str, dict[str, Any]] = {
    "codex": {
        "label": "OpenAI Codex",
        "auth_modes": ["oauth", "cli"],
        "skill_id": "setup-worker-codex-oauth",
        "docs_url": "https://developers.openai.com/codex",
        "keywords": ["codex"],
    },
    "claude_cli": {
        "label": "Claude Code CLI",
        "auth_modes": ["oauth", "cli"],
        "skill_id": "setup-worker-claude-cli",
        "docs_url": "https://docs.anthropic.com/en/docs/claude-code",
        "keywords": ["claude cli", "claude code"],
    },
    "grok_build": {
        "label": "Grok Build",
        "auth_modes": ["api_key", "cli"],
        "skill_id": "setup-worker-grok-build",
        "keywords": ["grok build"],
    },
    "api_worker": {
        "label": "API Worker (OpenAI-compatible)",
        "auth_modes": ["api_key"],
        "skill_id": "setup-worker-api-openai",
        "docs_url": "https://platform.openai.com/docs/api-reference",
        "keywords": ["worker api", "api worker"],
    },
}


def list_provider_ids() -> list[str]:
    return list(PROVIDER_PROFILES.keys())


def get_profile(provider_id: str) -> dict[str, Any] | None:
    return PROVIDER_PROFILES.get(provider_id)


def get_worker_profile(worker_id: str) -> dict[str, Any] | None:
    return WORKER_PROFILES.get(worker_id)