"""Facilitator v2: MCQ clarify/propose turns with project brief context."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from turingos.config import load_facilitator_config
from turingos.facilitator.config_wizard import is_config_flow, run_config_wizard
from turingos.facilitator.project_brief import format_project_cognition
from turingos.facilitator.provider_setup import (
    answer_project_question,
    auto_setup_turn,
    is_project_question,
)
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


def continue_after_skip_turn(
    project_brief: dict | None = None,
    session_turns: list[dict] | None = None,
) -> dict[str, Any]:
    """Deterministic handoff after「不需要，继续」— never a silent no-op."""
    brief = project_brief or {}
    cognition = format_project_cognition(brief)
    had_proposals = any(
        t.get("turn_type") == "propose" for t in (session_turns or [])
    )
    note = (
        "若要写入 Micro tape，请点「我理解对了，可以提交」再 Approve。"
        if not had_proposals
        else "提案已写入 tape。可继续说明任务，或点 Execute 推进 worker。"
    )
    return normalize_turn({
        "turn_type": "clarify",
        "summary": (
            f"**项目认知**\n\n{cognition}\n\n"
            "已跳过可选补充。请选择下一步，或点「我理解对了，可以提交」。"
        ),
        "choices": [
            {"id": "explore_confirm", "label": "开始扫描并汇报项目背景", "hint": "只读探索 capsule"},
            {"id": "task", "label": "我有具体任务要说", "hint": "自由输入或「其他需求」"},
            {"id": "ai_setup", "label": "配置 Meta AI / Worker", "skill_id": "setup-meta-ai-openai"},
        ],
        "proposals": [],
        "facilitator_note": note,
        "project_cognition": cognition,
    })


def mock_facilitate_turn(
    *,
    user_text: str = "",
    selected_choice_id: str | None = None,
    select_action: str | None = None,
    project_brief: dict | None = None,
    session_turns: list[dict] | None = None,
    boot: bool = False,
    config_draft: dict | None = None,
    choice: dict | None = None,
) -> dict[str, Any]:
    """Deterministic facilitator for tests and offline use."""
    pid = (project_brief or {}).get("project_id", "demo_app")
    brief = project_brief or {}
    text = (user_text or "").lower()

    if user_text and not selected_choice_id and not select_action:
        role = "facilitator" if (config_draft or {}).get("kind") == "facilitator" else "meta"
        setup = auto_setup_turn(user_text, role=role, force_mock_test=True)
        if setup:
            return setup
        if is_project_question(user_text):
            return answer_project_question(user_text, brief)

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

    if selected_choice_id == "explore":
        return normalize_turn({
            "turn_type": "clarify",
            "summary": "你想先读懂已有项目（git 历史、目录、README），再决定任务。",
            "choices": [
                {"id": "explore_confirm", "label": "开始扫描项目背景", "hint": "adopt + macro observe + 探索 capsule"},
                {"id": "ai_setup", "label": "先配置 Meta AI / Worker", "skill_id": "setup-meta-ai-openai"},
            ],
            "proposals": [],
        })

    if is_config_flow(
        config_draft=config_draft,
        selected_choice_id=selected_choice_id,
        select_action=select_action,
    ):
        turn, _draft = run_config_wizard(
            config_draft=config_draft,
            selected_choice_id=selected_choice_id,
            select_action=select_action,
            user_text=user_text,
            choice=choice,
        )
        return turn

    if selected_choice_id and selected_choice_id.startswith("worker_"):
        skill_map = {
            "worker_codex": "setup-worker-codex-oauth",
            "worker_claude": "setup-worker-claude-cli",
            "worker_grok": "setup-worker-grok-build",
        }
        sid = skill_map.get(selected_choice_id, "setup-worker-codex-oauth")
        doc = _load_skill(sid)
        return normalize_turn({
            "turn_type": "clarify",
            "wizard_mode": True,
            "summary": f"**Worker 说明**\n\n{doc[:1200]}",
            "choices": [
                {"id": "skill_worker", "label": "← 退回 Worker 列表"},
                {"id": "cfg_back_menu", "label": "← 退回配置菜单", "select_action": "cfg_back_menu"},
            ],
            "skill_id": sid,
        })

    if selected_choice_id == "ai_setup" or (
        not config_draft and ("config" in text or "meta" in text or "api" in text)
    ):
        turn, _ = run_config_wizard(selected_choice_id="ai_setup")
        return turn

    if select_action == "skip" or selected_choice_id == "skip":
        return continue_after_skip_turn(brief, session_turns)

    if boot or (not user_text and not selected_choice_id):
        has_git = brief.get("has_git")
        meta_ok = brief.get("config_status", {}).get("meta_ai") == "ok"
        cognition = format_project_cognition(brief)
        return normalize_turn({
            "turn_type": "clarify",
            "summary": (
                f"**项目认知**\n\n{cognition}\n\n"
                f"项目 **{pid}**"
                + ("，已有 git" if has_git else "")
                + ("，Meta AI 已配置" if meta_ok else "，Meta AI 未配置")
                + "。请选择下一步。"
            ),
            "project_cognition": cognition,
            "choices": [
                {"id": "explore", "label": "扫描并理解这个项目", "hint": "读取 README、目录、最近 commit"},
                {"id": "task", "label": "我有具体任务要说", "hint": "在下方输入或选「其他需求」"},
                {"id": "ai_setup", "label": "配置 Meta AI / Worker", "skill_id": "setup-meta-ai-openai"},
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
            {"id": "ai_setup", "label": "配置 AI / Worker", "skill_id": "setup-meta-ai-openai"},
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
            {"id": "ai_setup", "label": "配置 Meta AI / Worker", "skill_id": "setup-meta-ai-openai"},
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
    config_draft: dict | None = None,
    choice: dict | None = None,
) -> dict[str, Any]:
    if select_action == "skip" or selected_choice_id == "skip":
        return continue_after_skip_turn(project_brief, session_turns)
    if user_text and not boot:
        role = "meta"
        if config_draft:
            role = "facilitator" if config_draft.get("kind") == "facilitator" else "meta"
        setup = auto_setup_turn(
            user_text, role=role, force_mock_test=force_mock,
        )
        if setup:
            return setup
        if not selected_choice_id and not select_action:
            if is_project_question(user_text):
                return answer_project_question(user_text, project_brief)
    if is_config_flow(
        config_draft=config_draft,
        selected_choice_id=selected_choice_id,
        select_action=select_action,
    ):
        turn, _ = run_config_wizard(
            config_draft=config_draft,
            selected_choice_id=selected_choice_id,
            select_action=select_action,
            user_text=user_text,
            choice=choice,
        )
        return turn
    cfg = config or load_facilitator_config()
    if force_mock or not cfg.get("api_key"):
        return mock_facilitate_turn(
            user_text=user_text,
            selected_choice_id=selected_choice_id,
            select_action=select_action,
            project_brief=project_brief,
            session_turns=session_turns,
            boot=boot,
            config_draft=config_draft,
            choice=choice,
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
            config_draft=config_draft,
            choice=choice,
        )