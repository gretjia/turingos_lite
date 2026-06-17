"""One-shot provider setup: detect token → configure → test → webfetch docs on failure."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from turingos.config import (
    load_facilitator_config,
    load_meta_config,
    load_worker_config,
    save_facilitator_config,
    save_meta_config,
    save_worker_config,
)
from turingos.facilitator.provider_registry import PROVIDER_PROFILES, get_profile
from turingos.facilitator.schema import normalize_turn

_TOKEN_RE = re.compile(
    r"(?:(?:sk|nvapi|gsk)[-_a-zA-Z0-9]{8,}|sk-ant-[a-zA-Z0-9_-]{20,})"
)
_BEARER_RE = re.compile(r"Bearer\s+([^\s\"']+)", re.I)
_INVOKE_URL_RE = re.compile(
    r"(?:invoke_url|base_url|url)\s*=\s*[\"']([^\"']+)[\"']", re.I
)
_AUTH_HDR_RE = re.compile(
    r"Authorization[\"']?\s*:\s*[\"']Bearer\s+([^\"']+)[\"']", re.I
)
_MODEL_RE = re.compile(r"[\"']?model[\"']?\s*[:=]\s*[\"']([^\"']+)[\"']")
_THINKING_RE = re.compile(r"enable_thinking[\"']?\s*:\s*(True|False)", re.I)
_THINKING_TYPE_RE = re.compile(
    r"[\"']thinking[\"']\s*:\s*\{[^{}]*[\"']type[\"']\s*:\s*[\"'](enabled|disabled)[\"']",
    re.I,
)
_FLOAT_FIELD_RE = re.compile(r"\"(temperature|top_p)\"\s*:\s*([0-9.]+)")
_INT_FIELD_RE = re.compile(r"\"max_tokens\"\s*:\s*(\d+)")


def extract_api_token(text: str) -> str | None:
    raw = text or ""
    m = _TOKEN_RE.search(raw)
    if m:
        return m.group(0)
    for pat in (_BEARER_RE, _AUTH_HDR_RE):
        bm = pat.search(raw)
        if bm:
            return bm.group(1).strip()
    return None


def _normalize_base_url(url: str) -> str:
    base = url.strip().rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    return base


def parse_provider_paste(text: str) -> dict[str, Any]:
    """
    Extract provider config from pasted snippets (NVIDIA requests example, curl, etc.).
    """
    raw = text or ""
    low = raw.lower()
    out: dict[str, Any] = {"parsed": False}

    token = extract_api_token(raw)
    invoke = None
    um = _INVOKE_URL_RE.search(raw)
    if um:
        invoke = um.group(1)
    else:
        url_m = re.search(r"https?://[^\s\"']+", raw)
        if url_m:
            invoke = url_m.group(0)

    base_url = _normalize_base_url(invoke) if invoke else None
    if not base_url and "integrate.api.nvidia.com" in low:
        base_url = "https://integrate.api.nvidia.com/v1"

    model = _MODEL_RE.search(raw)
    model = model.group(1) if model else None

    thinking = None
    extra_body = None
    dtm = _THINKING_TYPE_RE.search(raw)
    if dtm:
        thinking = dtm.group(1).lower() == "enabled"
        extra_body = {
            "thinking": {
                "type": "enabled" if thinking else "disabled",
            },
        }
    tm = _THINKING_RE.search(raw)
    if tm and thinking is None:
        thinking = tm.group(1).lower() == "true"
        extra_body = {"chat_template_kwargs": {"enable_thinking": thinking}}

    temperature = top_p = None
    max_tokens = None
    for fm in _FLOAT_FIELD_RE.finditer(raw):
        if fm.group(1) == "temperature":
            temperature = float(fm.group(2))
        elif fm.group(1) == "top_p":
            top_p = float(fm.group(2))
    im = _INT_FIELD_RE.search(raw)
    if im:
        max_tokens = int(im.group(1))

    pid = detect_provider_id(raw, token)
    if not pid and base_url and "nvidia" in base_url:
        pid = "nvidia"

    if token or (base_url and model):
        out = {
            "parsed": True,
            "provider_id": pid,
            "api_key": token,
            "base_url": base_url,
            "model": model,
            "thinking": thinking,
            "extra_body": extra_body,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }
    return out


def is_provider_paste(text: str) -> bool:
    raw = text or ""
    if not raw.strip():
        return False
    if extract_api_token(raw):
        return True
    low = raw.lower()
    signals = (
        "invoke_url", "authorization", "bearer", "chat/completions",
        "integrate.api.nvidia", "requests.post", "payload", "nvapi",
        "api_key", "api key", "deepseek", "openai.com", "headers",
    )
    return sum(1 for s in signals if s in low) >= 2


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
        extra = cfg.get("extra_body")
        thinking_enabled = (
            isinstance(extra, dict)
            and (extra.get("thinking") or {}).get("type") == "enabled"
        )
        kwargs: dict[str, Any] = {
            "model": cfg.get("model", "gpt-4o-mini"),
            "messages": [{"role": "user", "content": "Reply with exactly: pong"}],
            "max_tokens": 256 if thinking_enabled else 16,
        }
        if extra:
            kwargs["extra_body"] = extra
        resp = client.chat.completions.create(**kwargs)
        latency = int((time.monotonic() - t0) * 1000)
        msg = resp.choices[0].message
        content = (msg.content or "").strip()
        reasoning = (getattr(msg, "reasoning_content", None) or "").strip()
        return {
            "ok": "pong" in content.lower() or len(content) > 0,
            "latency_ms": latency,
            "sample": content[:80],
            "has_reasoning": bool(reasoning),
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
    base_url: str | None = None,
    thinking: bool | None = None,
    extra_body: dict[str, Any] | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    prof = get_profile(provider_id)
    if not prof:
        raise ValueError(f"unknown provider: {provider_id}")
    base = base_url or prof["base_url"]
    mdl = model or prof["default_model"]
    extra = dict(extra_body) if extra_body else None
    if extra is None:
        thinking_map = prof.get("thinking_extra_body")
        if thinking is not None and thinking_map:
            extra = dict(thinking_map[bool(thinking)])
        elif thinking is True and prof.get("extra_body_default"):
            extra = dict(prof["extra_body_default"])
        elif thinking is False and prof.get("thinking_toggle"):
            if prof.get("thinking_toggle") == "extra_body.thinking.type":
                extra = {"thinking": {"type": "disabled"}}
            else:
                extra = {"chat_template_kwargs": {"enable_thinking": False}}

    save_kw: dict[str, Any] = {
        "base_url": base,
        "api_key": api_key,
        "model": mdl,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "extra_body": extra,
    }
    if role == "facilitator":
        save_facilitator_config(**save_kw)
        cfg = load_facilitator_config()
    elif role == "worker":
        save_worker_config(**save_kw, provider_id=provider_id)
        cfg = load_worker_config()
    else:
        save_meta_config(**save_kw)
        cfg = load_meta_config()
    if extra:
        cfg["extra_body"] = extra
    if temperature is not None:
        cfg["temperature"] = temperature
    if top_p is not None:
        cfg["top_p"] = top_p
    if max_tokens is not None:
        cfg["max_tokens"] = max_tokens
    return cfg


def _mask_key(key: str | None) -> str:
    if not key:
        return "（未设置）"
    if len(key) <= 10:
        return "****"
    return f"{key[:6]}…{key[-4:]}"


def _format_extracted(parsed: dict[str, Any], label: str) -> str:
    lines = [f"**从粘贴内容识别到 {label} 配置：**\n"]
    if parsed.get("base_url"):
        lines.append(f"- Base URL: `{parsed['base_url']}`")
    if parsed.get("model"):
        lines.append(f"- Model: `{parsed['model']}`")
    if parsed.get("api_key"):
        lines.append(f"- API Key: `{_mask_key(parsed['api_key'])}` → keyring")
    if parsed.get("thinking") is not None:
        lines.append(f"- Thinking: `{'开启' if parsed['thinking'] else '关闭'}`")
    if parsed.get("temperature") is not None:
        lines.append(f"- Temperature: `{parsed['temperature']}`")
    if parsed.get("top_p") is not None:
        lines.append(f"- Top_p: `{parsed['top_p']}`")
    if parsed.get("max_tokens") is not None:
        lines.append(f"- Max tokens: `{parsed['max_tokens']}`")
    return "\n".join(lines)


def auto_setup_turn(
    user_text: str,
    *,
    role: str = "meta",
    force_mock_test: bool = False,
) -> dict[str, Any] | None:
    """
    Software 3.0 path: paste token OR full provider snippet → configure + test + feedback.
    Returns facilitator turn or None if not a setup message.
    """
    if not is_provider_paste(user_text):
        return None

    parsed = parse_provider_paste(user_text)
    token = parsed.get("api_key") or extract_api_token(user_text)
    pid = parsed.get("provider_id") or detect_provider_id(user_text, token)
    if not pid or not token:
        return None

    prof = get_profile(pid)
    label = prof["label"] if prof else pid
    extracted = _format_extracted({**parsed, "api_key": token}, label)

    try:
        if force_mock_test:
            cfg = {
                "base_url": parsed.get("base_url") or prof["base_url"],
                "api_key": token,
                "model": parsed.get("model") or prof["default_model"],
                "extra_body": parsed.get("extra_body"),
                "temperature": parsed.get("temperature"),
                "top_p": parsed.get("top_p"),
                "max_tokens": parsed.get("max_tokens"),
            }
            test = {"ok": True, "latency_ms": 0, "sample": "mock-ok"}
        else:
            cfg = apply_provider_config(
                pid,
                token,
                role=role,
                model=parsed.get("model"),
                base_url=parsed.get("base_url"),
                thinking=parsed.get("thinking"),
                extra_body=parsed.get("extra_body"),
                temperature=parsed.get("temperature"),
                top_p=parsed.get("top_p"),
                max_tokens=parsed.get("max_tokens"),
            )
            test = test_openai_compatible(cfg)
    except Exception as e:
        test = {"ok": False, "error": str(e)}
        docs = fetch_docs_excerpt(prof.get("docs_url", "")) if prof else ""
        return normalize_turn({
            "turn_type": "chat",
            "summary": (
                f"**{label} 配置失败**\n\n{extracted}\n\n"
                f"错误: `{e}`\n\n"
                f"**官文档摘录**\n{docs[:1200]}"
            ),
            "choices": [
                {"id": "ai_setup", "label": "打开配置向导重试"},
                {"id": "explore", "label": "返回主流程"},
            ],
            "setup_result": {"provider": pid, "ok": False, "parsed": parsed},
        })

    if test.get("ok"):
        summary = (
            f"**{label} 已自动配置并测试通过**（{role}）\n\n"
            f"{extracted}\n\n"
            f"- 连通性延迟: {test.get('latency_ms')}ms\n"
            f"- 探针回复: {test.get('sample', '—')}\n\n"
            "**下一步**：点「继续项目流程」开始扫描项目，或点「调整配置」修改。"
        )
    else:
        docs = fetch_docs_excerpt(prof.get("docs_url", "")) if prof else ""
        summary = (
            f"**{label} 已保存，但连通性测试失败**\n\n"
            f"{extracted}\n\n"
            f"错误: `{test.get('error', '?')}`\n\n"
            f"**从官网文档抓取的建议**（webfetch）:\n{docs[:1200]}\n\n"
            "元数据已写入；若 keyring 不可用可设环境变量 "
            f"`TURINGOS_{'FACILITATOR' if role == 'facilitator' else 'META'}_API_KEY`。"
        )

    return normalize_turn({
        "turn_type": "chat",
        "summary": summary,
        "choices": [
            {"id": "ai_setup", "label": "调整配置（向导）"},
            {"id": "explore", "label": "继续项目流程"},
        ],
        "setup_result": {"provider": pid, "ok": test.get("ok"), "test": test, "parsed": parsed},
        "facilitator_note": "Software 3.0：粘贴官网示例代码即可，harness 自动识别 URL/Key/Model/Thinking。",
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
