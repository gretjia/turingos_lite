"""Software 3.0 Facilitator Agent — detect, configure, propose code, auto-execute."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from turingos.facilitator.project_brief import format_project_cognition
from turingos.facilitator.provider_setup import auto_setup_turn, is_provider_paste
from turingos.facilitator.schema import normalize_turn
from turingos.tools.whitebox import infer_target_path

_CODE_VERBS = (
    "fix", "implement", "add", "write", "patch", "refactor", "create", "update",
    "修改", "实现", "添加", "修复", "编写", "创建", "改", "写代码", "加功能",
)


def is_code_task(text: str) -> bool:
    t = (text or "").lower()
    if re.search(r"[\w./-]+\.py\b", t):
        return True
    if "写代码" in t or "改代码" in t:
        return True
    code_ctx = (".py", "代码", "文件", "函数", "模块", "bug", "patch", "refactor", "cli.py")
    if any(s in t for s in code_ctx):
        return any(v in t for v in _CODE_VERBS)
    return False


def build_tool_plan(task: str, brief: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministic tool plan for mock / offline agent execution."""
    root = Path(brief.get("cwd") or Path.cwd())
    target = infer_target_path(task, root)
    plan: list[dict[str, Any]] = [{"tool": "list_dir", "args": {"path": "."}}]
    if target:
        plan.append({"tool": "read_file", "args": {"path": target}})
        stamp = hashlib.sha256(task.encode()).hexdigest()[:8]
        marker = f"\n# TuringOS agent ({stamp}): {task[:120]}\n"
        plan.append({
            "tool": "write_file",
            "args": {"path": target, "content": marker, "append": True},
        })
    else:
        plan.append({
            "tool": "write_file",
            "args": {
                "path": ".turingos/agent_task.md",
                "content": f"# Agent task\n\n{task}\n",
            },
        })
    return plan


def agent_proposals_for_code(task: str, pid: str, brief: dict[str, Any]) -> list[dict]:
    tool_plan = build_tool_plan(task, brief)
    target = infer_target_path(task, Path(brief.get("cwd") or Path.cwd()))
    vis = (
        f"# 代码任务（Agent 提案）\n\n"
        f"**任务**: {task}\n\n"
        f"**目标文件**: `{target or '.turingos/agent_task.md'}`\n\n"
        f"**执行计划**: {len(tool_plan)} 步白盒工具（read → patch/write）\n\n"
        "批准后 Worker API 将在后台写入 Macro 代码（Micro 收据全程记录）。"
    )
    return [
        {
            "event_type": "IntentCaptured",
            "payload": {"task": task, "from": "facilitator-agent"},
        },
        {
            "event_type": "WorkCapsuleBuilt",
            "payload": {
                "capsule_id": "wc_agent_code",
                "visible_markdown": vis,
                "contract": f"macro:git:{pid}:agent_patch",
                "auto_execute": True,
                "worker": "api",
                "tool_plan": tool_plan,
                "macro_root": brief.get("cwd"),
            },
        },
        {
            "event_type": "WorkerDispatchPrepared",
            "payload": {
                "capsule_id": "wc_agent_code",
                "worker": "api",
                "tool_plan": tool_plan,
                "macro_root": brief.get("cwd"),
            },
        },
    ]


def agent_boot_turn(brief: dict[str, Any]) -> dict[str, Any]:
    """Agent-first boot — paste or speak; less wizard friction."""
    pid = brief.get("project_id", "demo_app")
    cognition = format_project_cognition(brief)
    cfg = brief.get("config_status") or {}
    worker_ok = cfg.get("worker", "missing") == "ok"
    fac_ok = cfg.get("facilitator", "missing") == "ok"

    hints = []
    if not worker_ok:
        hints.append("粘贴 DeepSeek/NVIDIA 官网示例到输入框 → **自动配置 Worker**")
    if not fac_ok:
        hints.append("粘贴 API 配置片段 → 自动配置 Facilitator")
    hints.append("直接说「修复 turingos/cli.py …」→ **自动写代码**（Worker 白盒）")
    hint_block = "\n".join(f"- {h}" for h in hints)

    return normalize_turn({
        "turn_type": "clarify",
        "summary": (
            f"**项目认知** · TuringOS Facilitator Agent\n\n{cognition}\n\n"
            f"我是具备检测与执行能力的副驾驶（Software 3.0）。"
            f"当前假设 AI 善意；Autonomy ≥50% 时批准后**自动后台执行**。\n\n"
            f"{hint_block}"
        ),
        "project_cognition": cognition,
        "choices": [
            {"id": "explore", "label": "扫描项目背景", "hint": "只读探索"},
            {"id": "task", "label": "我有代码/功能任务", "hint": "Agent 自动提案+执行"},
            {"id": "ai_setup", "label": "手动打开配置向导", "skill_id": "setup-meta-ai-openai"},
        ],
        "proposals": [],
        "facilitator_note": "粘贴配置或描述任务即可；不必逐步点向导。",
        "agent_mode": True,
    })


def try_agent_turn(
    *,
    user_text: str = "",
    project_brief: dict | None = None,
    force_mock: bool = False,
    boot: bool = False,
) -> dict[str, Any] | None:
    """Agent fast-path before wizard/MCQ maze."""
    brief = project_brief or {}
    pid = brief.get("project_id", "demo_app")

    if boot:
        return agent_boot_turn(brief)

    if not user_text:
        return None

    if is_provider_paste(user_text):
        role = "worker"
        setup = auto_setup_turn(user_text, role=role, force_mock_test=force_mock)
        if setup:
            return setup

    if is_code_task(user_text):
        props = agent_proposals_for_code(user_text, pid, brief)
        return normalize_turn({
            "turn_type": "propose",
            "summary": (
                f"**Agent 已理解代码任务**\n\n{user_text[:300]}\n\n"
                "将创建 `wc_agent_code` 胶囊并由 Worker API 后台写入。"
                "点 Approve（或 Autonomy≥50% 自动批准+执行）。"
            ),
            "choices": [],
            "proposals": props,
            "facilitator_note": "Software 3.0：提案→批准→白盒写码。",
            "agent_mode": True,
        })

    return None