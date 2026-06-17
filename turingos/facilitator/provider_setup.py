"""One-shot provider setup: detect token → configure → test → webfetch docs on failure."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from turingos.config import load_facilitator_config, load_meta_config, save_facilitator_config, save_meta_config
from turingos.facilitator.provider_registry import PROVIDER_PROFILES, get_profile
from turingos.facilitator.schema import normalize_turn

_TOKEN_RE = re.compile(
    r"(?:(?:sk|nvapi|gsk)[-_a-zA-Z0-9]{8,}|sk-ant-[a-zA-Z0-9_-]{20,})"
)


def extract_api_token(text: str) -> str | None:
    m = _TOKEN_RE.search(text or "")
    return m.group(0) if m else None


def detect_provider_id(text: str, token: str | None = None) -> str | None:
    low = (text or "").lower()
    token = token or extract_api_token(text) or ""
    for pid, prof in PROVIDER_PROFILES.items():
        for prefix in prof.get("token_prefixes", []):
            if token.startswith(prefix):
                return pid
        for kw in prof.get("keywords", []):
            if kw in low:
                return pid
    return None


def fetch_docs_excerpt(url: str, max_chars: int = 4000) -> str:
    """Best-effort fetch of provider docs (for facilitator skill loop)."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TuringOS-Facilitator/1.0"},
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = resp.read(80000).decode("utf-8", errors="replace")
        text = re.sub(r"<[^>]+>", " ", raw)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars] if text else f"（无法解析 {url} 正文）"
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return f"（webfetch 失败: {e}）"


def test_openai_compatible(cfg: dict[str, Any]) -> dict[str, Any]:
    """Minimal completion probe; returns {ok, latency_ms, error, model}."""
    import time

    api_key = cfg.get("api_key")
    if not api_key:
        return {"ok": False, "error": "missing api_key"}
    try:
        from openai import OpenAI

        client = OpenAI(base_url=cfg.get("base_url"), api_key=api_key)
        t0 = time.monotonic()
        kwargs: dict[str, Any] = {
            "model": cfg.get("model", "gpt-4o-mini"),
            "messages": [{"role": "user", "content": "Reply with exactly: pong"}],
            "max_tokens": 16,
        }
        extra = cfg.get("extra_body")
        if extra:
            kwargs["extra_body"] = extra
        resp = client.chat.completions.create(**kwargs)
        latency = int((time.monotonic() - t0) * 1000)
        content = (resp.choices[0].message.content or "").strip()
        return {
            "ok": "pong" in content.lower() or len(content) > 0,
            "latency_ms": latency,
            "sample": content[:80],
            "model": cfg.get("model"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


def apply_provider_config(
    provider_id: str,
    api_key: str,
    *,
    role: str = "meta",
    model: str | None = None,
    thinking: bool | None = None,
) -> dict[str, Any]:
    prof = get_profile(provider_id)
    if not prof:
        raise ValueError(f"unknown provider: {provider_id}")
    base = prof["base_url"]
    mdl = model or prof["default_model"]
    extra = None
    if thinking is True and prof.get("extra_body_default"):
        extra = dict(prof["extra_body_default"])
    elif thinking is False and prof.get("thinking_toggle"):
        extra = {"chat_template_kwargs": {"enable_thinking": False}}

    if role == "facilitator":
        save_facilitator_config(base_url=base, api_key=api_key, model=mdl)
        cfg = load_facilitator_config()
    else:
        save_meta_config(base_url=base, api_key=api_key, model=mdl)
        cfg = load_meta_config()
    if extra:
        cfg["extra_body"] = extra
    return cfg


def auto_setup_turn(
    user_text: str,
    *,
    role: str = "meta",
    force_mock_test: bool = False,
) -> dict[str, Any] | None:
    """
    Software 3.0 path: user says「我从 deepseek 官网拿了 api」+ token → configure + test.
    Returns facilitator turn or None if not a setup message.
    """
    token = extract_api_token(user_text)
    pid = detect_provider_id(user_text, token)
    if not pid or not token:
        return None
    low = user_text.lower()
    if not any(
        w in low
        for w in (
            "api", "key", "token", "配置", "官网", "deepseek", "openai", "nvidia",
            "nvapi", "密钥", "paste", "粘贴", "取得", "拿到",
        )
    ) and len(user_text) < 40:
        return None

    prof = get_profile(pid)
    label = prof["label"] if prof else pid
    try:
        if force_mock_test:
            cfg = {
                "base_url": prof["base_url"],
                "api_key": token,
                "model": prof["default_model"],
            }
            test = {"ok": True, "latency_ms": 0, "sample": "mock-ok"}
        else:
            cfg = apply_provider_config(pid, token, role=role)
            test = test_openai_compatible(cfg)
    except Exception as e:
        test = {"ok": False, "error": str(e)}
        docs = fetch_docs_excerpt(prof.get("docs_url", "")) if prof else ""
        return normalize_turn({
            "turn_type": "chat",
            "summary": f"**{label} 配置失败**\n\n`{e}`\n\n**官文档摘录**\n{docs[:1500]}",
            "choices": [
                {"id": "ai_setup", "label": "打开配置向导重试"},
                {"id": "explore", "label": "返回主流程"},
            ],
            "setup_result": {"provider": pid, "ok": False},
        })

    if test.get("ok"):
        summary = (
            f"**{label} 已自动配置并测试通过**（{role}）\n\n"
            f"- Base URL: `{cfg.get('base_url')}`\n"
            f"- Model: `{cfg.get('model')}`\n"
            f"- 延迟: {test.get('latency_ms')}ms\n"
            f"- 探针回复: {test.get('sample', '—')}\n\n"
            "密钥已写入 keyring；你无需再手动填 Base URL。"
        )
    else:
        docs = fetch_docs_excerpt(prof.get("docs_url", "")) if prof else ""
        summary = (
            f"**{label} 已保存，但连通性测试失败**\n\n"
            f"错误: `{test.get('error', '?')}`\n\n"
            f"**从官网文档抓取的建议**（webfetch）:\n{docs[:1200]}"
        )

    return normalize_turn({
        "turn_type": "chat",
        "summary": summary,
        "choices": [
            {"id": "ai_setup", "label": "调整配置（向导）"},
            {"id": "explore", "label": "继续项目流程"},
        ],
        "setup_result": {"provider": pid, "ok": test.get("ok"), "test": test},
        "facilitator_note": "Software 3.0：你只提供 token，harness 负责配置+验证。",
    })


def answer_project_question(user_text: str, project_brief: dict | None) -> dict[str, Any]:
    """Deterministic Q&A from project_brief when user asks about the project."""
    from turingos.facilitator.project_brief import format_project_cognition

    brief = project_brief or {}
    cognition = format_project_cognition(brief)
    q = user_text.strip()
    answer_parts = [f"**关于你的问题**\n\n> {q[:500]}\n\n**项目认知**\n\n{cognition}"]
    if brief.get("readme_excerpt"):
        answer_parts.append(
            f"\n**README 片段**\n{brief['readme_excerpt'][:600]}"
        )
    answer_parts.append(
        "\n如需写入任务到 tape，请点「我理解对了，可以提交」；"
        "若要配置 API，直接粘贴 token 并说明品牌（如 DeepSeek）。"
    )
    return normalize_turn({
        "turn_type": "chat",
        "summary": "\n".join(answer_parts),
        "choices": [
            {"id": "explore_confirm", "label": "按此理解开始扫描项目"},
            {"id": "ai_setup", "label": "配置 AI / Worker"},
        ],
        "facilitator_note": "对话模式：未写入 Micro tape，除非你选择提交。",
    })


def _marker_hit(low: str, marker: str) -> bool:
    if marker in ("?", "？"):
        return marker in low
    if len(marker) <= 4:
        return bool(re.search(rf"\b{re.escape(marker)}\b", low))
    return marker in low


def is_project_question(text: str) -> bool:
    low = (text or "").lower()
    if extract_api_token(text):
        return False
    if len(text.strip()) <= 8:
        return False
    markers = (
        "?", "？", "什么", "如何", "为什么", "项目", "readme", "结构",
        "what", "how", "why", "explain", "tell me", "介绍", "问题",
    )
    return any(_marker_hit(low, m) for m in markers)