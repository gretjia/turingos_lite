"""Complete human journey catalog — every UX path a real user can take."""
from __future__ import annotations

from turingos.facilitator.provider_registry import build_worker_api_targets

# All Worker API provider MCQ ids (must be clickable after scroll)
WORKER_API_MCQ_IDS = list(build_worker_api_targets().keys())

# Config menu top-level
CONFIG_MENU_MCQS = ("skill_nvidia", "skill_openai", "skill_worker")

# Main boot MCQs
BOOT_MCQS = ("explore", "task", "ai_setup", "submit", "other")

# Bundle workers
WORKER_BUNDLE_MCQS = ("worker_codex", "worker_claude", "worker_grok")

# Short NVIDIA paste detectable by auto_setup (human types key-by-key in strict mode)
NVIDIA_PASTE_SHORT = (
    'invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"\n'
    'headers = {"Authorization": "Bearer nvapi-test1234567890abcdefghijklmnop"}\n'
    'payload = {"model": "google/diffusiongemma-26b-a4b-it",'
    '"chat_template_kwargs": {"enable_thinking":True}}\n'
)

DEEPSEEK_TOKEN_MSG = (
    "我从 deepseek 官网取得了 api key: sk-fake1234567890abcdef"
)

PROJECT_QUESTION = "这个项目的主要结构是什么？README 讲了什么？"