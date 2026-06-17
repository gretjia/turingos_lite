"""Facilitator v2: MCQ clarify/propose turns with project brief context."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from turingos.config import load_facilitator_config
from turingos.facilitator.schema import (
    OTHER_CHOICE,
    SUBMIT_CHOICE,
    ensure_standard_choices,
    normalize_turn,
    parse_turn,
)

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_SKILLS_DIR = Path(__file__).parent / "skills"


def _load_prompt(name: str) -> str:
    p = _PROMPTS_DIR / name
    return p.read_text() if p.is_file() else ""


def _load_skill(skill_id: str | None) -> str:
    if not skill_id:
        return ""
    p = _SKILLS_DIR / f"{skill_id}.md"
    return p.read_text()[:3000] if p.is_file() else ""


def _system_prompt() -> str:
    return "\n\n".join(
        filter(None, [_load_prompt("role.md"), _load_prompt("output_schema.md")])
    )


def mock_facilitate_turn(
    *,
    user_text: str = "",
    selected_choice_id: str | None = None,
    select_action: str | None = None,
    project_brief: dict | None = None,
    session_turns: list[dict] | None = None,
    boot: bool = False,
) -> dict[str, Any]:
    """Deterministic facilitator for tests and offline use."""
    pid = (project_brief or {}).get("project_id", "demo_app")
    brief = project_brief or {}
    text = (user_text or "").lower()

    if select_action == "propose" or selected_choice_id == "submit":
        return normalize_turn({
            "turn_type": "propose",
            "summary": f"提交：{user_text or '按当前理解执行'}",
            "choices": [],
            "proposals": _proposals_for_intent(user_text or "explore project", pid, brief),
            "facilitator_note": "批准后写入 Micro tape。",
        })

    if selected_choice_id in ("explore_confirm", "task", "stack_sqlite", "stack_default"):
        return normalize_turn({
            "turn_type": "propose",
            "summary": f"执行选项：{selected_choice_id}",
            "choices": [],
            "proposals": _proposals_for_intent(user_text or selected_choice_id, pid, brief),
            "facilitator_note": "请 Approve 写入 tape。",
        })

    if selected_choice_id == "explore" or "explore" in (selected_choice_id or ""):
        return normalize_turn({
            "turn_type": "clarify",
            "summary": "你想先读懂已有项目（git 历史、目录、README），再决定任务。",
            "choices": [
                {"id": "explore_confirm", "label": "开始扫描项目背景", "hint": "adopt + macro observe + 探索 capsule"},
                {"id": "config", "label": "先配置 Meta AI / Worker", "skill_id": "setup-meta-ai-openai"},
            ],
            "proposals": [],
        })

    if selected_choice_id == "config" or "config" in text or "meta" in text or "api" in text:
        return normalize_turn({
            "turn_type": "clarify",
            "summary": "需要配置模型：Facilitator（对话）、Meta AI（提案）、Worker（执行）。",
            "choices": [
                {"id": "skill_nvidia", "label": "配置 Facilitator（NVIDIA Diffusion Gemma）", "skill_id": "setup-facilitator-nvidia"},
                {"id": "skill_openai", "label": "配置 Meta AI（OpenAI 格式）", "skill_id": "setup-meta-ai-openai"},
                {"id": "skill_worker", "label": "配置 Worker（Codex / Claude / Grok）", "skill_id": "setup-worker-codex-oauth"},
            ],
            "proposals": [],
            "skill_id": "setup-meta-ai-openai",
        })

    if boot or (not user_text and not selected_choice_id):
        has_git = brief.get("has_git")
        meta_ok = brief.get("config_status", {}).get("meta_ai") == "ok"
        return normalize_turn({
            "turn_type": "clarify",
            "summary": (
                f"项目 **{pid}**"
                + ("，已有 git" if has_git else "")
                + ("，Meta AI 已配置" if meta_ok else "，Meta AI 未配置")
                + "。请选择下一步。"
            ),
            "choices": [
                {"id": "explore", "label": "扫描并理解这个项目", "hint": "读取 README、目录、最近 commit"},
                {"id": "task", "label": "我有具体任务要说", "hint": "在下方输入或选「其他需求」"},
                {"id": "config", "label": "配置 Meta AI / Worker", "skill_id": "setup-meta-ai-openai"},
            ],
            "proposals": [],
            "facilitator_note": "冷静副驾驶：点选项即可，不必记命令。",
        })

    if any(w in text for w in ("github", "git", "exist", "已有", "历史", "macro", "理解", "ready", "准备")):
        return normalize_turn({
            "turn_type": "clarify",
            "summary": "你在已有 repo 中，希望系统先理解 Macro/项目历史，再等你 ready。",
            "choices": [
                {"id": "explore", "label": "先扫描项目背景再汇报", "hint": "只读探索"},
                {"id": "task", "label": "跳过探索，直接说任务", "hint": "自由输入"},
            ],
            "proposals": [],
        })

    if selected_choice_id == "other" or select_action == "freeform":
        return normalize_turn({
            "turn_type": "clarify",
            "summary": f"收到补充：{user_text[:200] or '（请在输入框说明）'}",
            "choices": [
                {"id": "explore", "label": "按补充内容先探索项目", "hint": "探索 capsule"},
                {"id": "task", "label": "按补充内容创建任务胶囊", "hint": "WorkCapsuleBuilt"},
            ],
            "proposals": [],
        })

    if any(w in text for w in ("todo", "create", "app", "创建")):
        return normalize_turn({
            "turn_type": "clarify",
            "summary": f"你想创建应用相关任务：{user_text[:120]}",
            "choices": [
                {"id": "stack_sqlite", "label": "使用 sqlite + 前端", "hint": "写入 capsule"},
                {"id": "stack_default", "label": "默认技术栈即可", "hint": "写入 capsule"},
            ],
            "proposals": [],
        })

    return normalize_turn({
        "turn_type": "clarify",
        "summary": f"理解：{user_text[:200] or '等待你的说明'}",
        "choices": [
            {"id": "explore", "label": "先理解当前项目", "hint": "探索"},
            {"id": "config", "label": "配置 AI / Worker", "skill_id": "setup-meta-ai-openai"},
        ],
        "proposals": [],
    })


def _proposals_for_intent(text: str, pid: str, brief: dict) -> list[dict]:
    t = text.lower()
    proposals: list[dict] = []
    if any(w in t for w in ("github", "git", "exist", "已有", "历史", "macro", "理解", "explore", "扫描")):
        macro = brief.get("macro_head") or f"macro:git:{pid}:HEAD"
        proposals.append({
            "event_type": "IntentCaptured",
            "payload": {"task": text, "from": "facilitator-v2"},
        })
        if brief.get("has_git"):
            proposals.append({
                "event_type": "MacroObservationImported",
                "payload": {"capsule_id": "wc_explore", "obs": {"macro_ref": macro}},
            })
        proposals.append({
            "event_type": "WorkCapsuleBuilt",
            "payload": {
                "capsule_id": "wc_explore",
                "visible_markdown": f"# 项目探索\n\n{text}\n\n只读：README、目录、git log。",
                "contract": f"macro:git:{pid}:explore",
            },
        })
        return proposals
    if any(w in t for w in ("deliver", "交付", "finish")):
        proposals.append({"event_type": "HumanDecision", "payload": {"decision": "approve", "from": "facilitator"}})
        proposals.append({
            "event_type": "WorkCapsuleBuilt",
            "payload": {"capsule_id": "wc_delivered", "visible_markdown": "# Delivered", "status": "delivered"},
        })
        return proposals
    proposals.append({
        "event_type": "IntentCaptured",
        "payload": {"task": text, "from": "facilitator-v2"},
    })
    proposals.append({
        "event_type": "WorkCapsuleBuilt",
        "payload": {
            "capsule_id": "wc_task",
            "visible_markdown": f"# Task\n\n{text}",
            "contract": f"macro:git:{pid}:task",
        },
    })
    return proposals


def mock_enrich_turn(last_mid: str) -> dict[str, Any]:
    return normalize_turn({
        "turn_type": "enrich",
        "summary": f"已批准并写入 tape（{last_mid}）。是否补充外部资料？",
        "choices": [
            {"id": "url", "label": "粘贴 URL（抓取摘要，需确认）", "select_action": "freeform"},
            {"id": "paste", "label": "粘贴文本/文档片段", "select_action": "freeform"},
            {"id": "config", "label": "配置 Meta AI / Worker", "skill_id": "setup-meta-ai-openai"},
            {"id": "skip", "label": "不需要，继续", "select_action": "skip"},
            dict(OTHER_CHOICE),
        ],
        "proposals": [],
    })


def _call_llm(
    cfg: dict[str, Any],
    user_msg: str,
) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(base_url=cfg.get("base_url"), api_key=cfg.get("api_key") or "ollama")
    kwargs: dict[str, Any] = {
        "model": cfg.get("model", "google/diffusiongemma-26b-a4b-it"),
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": user_msg},
        ],
        "temperature": cfg.get("temperature", 1.0),
        "max_tokens": cfg.get("max_tokens", 4096),
    }
    if cfg.get("top_p") is not None:
        kwargs["top_p"] = cfg["top_p"]
    extra = cfg.get("extra_body")
    if extra:
        kwargs["extra_body"] = extra
    resp = client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content or "{}"
    return parse_turn(content)


def _build_user_message(
    project_brief: dict | None,
    session_turns: list[dict] | None,
    user_text: str,
    selected_choice_id: str | None,
    select_action: str | None,
    skill_id: str | None,
) -> str:
    parts = []
    if project_brief:
        parts.append(f"project_brief:\n{json.dumps(project_brief, default=str)[:6000]}")
    if session_turns:
        parts.append(f"session_turns:\n{json.dumps(session_turns[-8:], default=str)[:4000]}")
    if selected_choice_id:
        parts.append(f"selected_choice_id: {selected_choice_id}")
    if select_action:
        parts.append(f"select_action: {select_action}")
    if skill_id:
        parts.append(f"skill:\n{_load_skill(skill_id)}")
    if user_text:
        parts.append(f"user_input:\n{user_text}")
    parts.append("Respond with one JSON turn object only.")
    return "\n\n".join(parts)


def facilitate_turn(
    *,
    user_text: str = "",
    selected_choice_id: str | None = None,
    select_action: str | None = None,
    project_brief: dict | None = None,
    session_turns: list[dict] | None = None,
    boot: bool = False,
    force_mock: bool = False,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = config or load_facilitator_config()
    if force_mock or not cfg.get("api_key"):
        return mock_facilitate_turn(
            user_text=user_text,
            selected_choice_id=selected_choice_id,
            select_action=select_action,
            project_brief=project_brief,
            session_turns=session_turns,
            boot=boot,
        )
    skill_id = None
    if session_turns:
        skill_id = session_turns[-1].get("skill_id")
    try:
        user_msg = _build_user_message(
            project_brief, session_turns, user_text,
            selected_choice_id, select_action, skill_id,
        )
        return _call_llm(cfg, user_msg)
    except Exception:
        return mock_facilitate_turn(
            user_text=user_text,
            selected_choice_id=selected_choice_id,
            select_action=select_action,
            project_brief=project_brief,
            session_turns=session_turns,
            boot=boot,
        )