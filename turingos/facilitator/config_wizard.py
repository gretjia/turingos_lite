"""In-TUI config wizard: step through base URL / API key / model before leaving."""
from __future__ import annotations

from typing import Any

from turingos.config import load_facilitator_config, load_meta_config, save_meta_config
from turingos.facilitator.schema import normalize_turn

CONFIG_TARGET_IDS = frozenset({
    "skill_openai",
    "skill_nvidia",
    "skill_worker",
})

_CONFIG_ACTIONS = frozenset({
    "config_input",
    "cfg_step_back",
    "cfg_back_menu",
    "cfg_save",
    "cfg_skip_key",
})

_TARGETS: dict[str, dict[str, Any]] = {
    "skill_openai": {
        "kind": "meta",
        "title": "Meta AI（OpenAI 格式）",
        "skill_id": "setup-meta-ai-openai",
        "default_base": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "presets": [
            {
                "id": "preset_openai",
                "label": "OpenAI 官方 API",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini",
            },
            {
                "id": "preset_nvidia_meta",
                "label": "NVIDIA Integrate API",
                "base_url": "https://integrate.api.nvidia.com/v1",
                "model": "nvidia/nemotron-mini-4b-instruct",
            },
        ],
    },
    "skill_nvidia": {
        "kind": "facilitator",
        "title": "Facilitator（NVIDIA Diffusion Gemma）",
        "skill_id": "setup-facilitator-nvidia",
        "default_base": "https://integrate.api.nvidia.com/v1",
        "default_model": "google/diffusiongemma-26b-a4b-it",
        "presets": [
            {
                "id": "preset_nvidia_fac",
                "label": "NVIDIA Integrate（推荐）",
                "base_url": "https://integrate.api.nvidia.com/v1",
                "model": "google/diffusiongemma-26b-a4b-it",
            },
        ],
    },
}


def is_config_flow(
    *,
    config_draft: dict | None,
    selected_choice_id: str | None,
    select_action: str | None,
) -> bool:
    if config_draft:
        return True
    if selected_choice_id == "ai_setup":
        return True
    if selected_choice_id in CONFIG_TARGET_IDS:
        return True
    if selected_choice_id and selected_choice_id.startswith("worker_"):
        return True
    if select_action in _CONFIG_ACTIONS:
        return True
    if selected_choice_id and selected_choice_id.startswith("preset_"):
        return True
    if selected_choice_id in ("cfg_input", "cfg_save", "cfg_skip_key", "cfg_step_back", "cfg_back_menu"):
        return True
    return False


def new_config_draft(target_id: str) -> dict[str, Any]:
    t = _TARGETS[target_id]
    return {
        "target_id": target_id,
        "kind": t["kind"],
        "title": t["title"],
        "skill_id": t["skill_id"],
        "step": "base_url",
        "base_url": t["default_base"],
        "model": t["default_model"],
        "api_key": None,
    }


def _mask_key(key: str | None) -> str:
    if not key:
        return "（未设置）"
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}…{key[-4:]}"


def _current_key_status(kind: str) -> str:
    if kind == "meta":
        cfg = load_meta_config()
    else:
        cfg = load_facilitator_config()
    if cfg.get("api_key"):
        return f"已配置 {_mask_key(cfg['api_key'])}"
    return "未配置"


def _save_draft(draft: dict) -> str:
    kind = draft["kind"]
    base = draft.get("base_url")
    model = draft.get("model")
    key = draft.get("api_key")
    if kind == "meta":
        save_meta_config(base_url=base, api_key=key, model=model)
        return "Meta AI"
    from turingos.config import save_facilitator_config

    save_facilitator_config(base_url=base, api_key=key, model=model)
    return "Facilitator"


def _worker_picker_turn() -> dict[str, Any]:
    return normalize_turn({
        "turn_type": "clarify",
        "wizard_mode": True,
        "summary": (
            "**Worker 配置**\n\n"
            "Worker 通过 CLI/OAuth 接入（Codex、Claude、Grok）。"
            "选择一种查看说明；API Worker 在 dispatch 时配置。"
        ),
        "choices": [
            {"id": "worker_codex", "label": "Codex（OAuth）", "skill_id": "setup-worker-codex-oauth"},
            {"id": "worker_claude", "label": "Claude CLI", "skill_id": "setup-worker-claude-cli"},
            {"id": "worker_grok", "label": "Grok Build", "skill_id": "setup-worker-grok-build"},
            {"id": "cfg_back_menu", "label": "← 退回配置菜单", "select_action": "cfg_back_menu"},
        ],
        "proposals": [],
        "skill_id": "setup-worker-codex-oauth",
    })


def _config_menu_turn() -> dict[str, Any]:
    return normalize_turn({
        "turn_type": "clarify",
        "wizard_mode": True,
        "summary": "选择要配置的组件：Facilitator（对话）、Meta AI（提案）、Worker（执行）。",
        "choices": [
            {"id": "skill_nvidia", "label": "配置 Facilitator（NVIDIA Diffusion Gemma）", "skill_id": "setup-facilitator-nvidia"},
            {"id": "skill_openai", "label": "配置 Meta AI（OpenAI 格式）", "skill_id": "setup-meta-ai-openai"},
            {"id": "skill_worker", "label": "配置 Worker（Codex / Claude / Grok）", "skill_id": "setup-worker-codex-oauth"},
        ],
        "proposals": [],
    })


def _step_turn(draft: dict[str, Any]) -> dict[str, Any]:
    step = draft["step"]
    title = draft["title"]
    key_status = _current_key_status(draft["kind"])

    if step == "base_url":
        t = _TARGETS[draft["target_id"]]
        choices = [
            {
                "id": p["id"],
                "label": p["label"],
                "select_action": "config_preset",
                "preset_base": p["base_url"],
                "preset_model": p["model"],
            }
            for p in t["presets"]
        ]
        choices.append({
            "id": "cfg_input_base",
            "label": "自行输入 Base URL",
            "select_action": "config_input",
            "config_field": "base_url",
            "input_prompt": f"输入 {title} 的 Base URL，然后点 Transcribe",
        })
        return normalize_turn({
            "turn_type": "clarify",
            "wizard_mode": True,
            "summary": (
                f"**{title}** — 步骤 1/3：Base URL\n\n"
                f"当前默认：`{draft.get('base_url', '')}`\n"
                f"API Key 状态：{key_status}"
            ),
            "choices": choices,
            "skill_id": draft.get("skill_id"),
            "config_draft": draft,
        })

    if step == "api_key":
        choices = [
            {
                "id": "cfg_input_key",
                "label": "输入 API Key（keyring 安全存储）",
                "select_action": "config_input",
                "config_field": "api_key",
                "input_prompt": f"粘贴 {title} 的 API Key，然后点 Transcribe（不会显示在日志）",
            },
        ]
        if "已配置" in key_status:
            choices.insert(0, {
                "id": "cfg_skip_key",
                "label": "保留现有 API Key，下一步",
                "select_action": "cfg_skip_key",
            })
        return normalize_turn({
            "turn_type": "clarify",
            "wizard_mode": True,
            "summary": (
                f"**{title}** — 步骤 2/3：API Key\n\n"
                f"Base URL：`{draft.get('base_url', '')}`\n"
                f"当前 Key：{key_status}\n\n"
                "在下方输入框粘贴 Key，点 **Transcribe** 保存到 keyring。"
            ),
            "choices": choices,
            "skill_id": draft.get("skill_id"),
            "config_draft": draft,
        })

    if step == "model":
        t = _TARGETS.get(draft["target_id"], {})
        choices = [
            {
                "id": p["id"],
                "label": f"模型：{p['model']}",
                "select_action": "config_preset",
                "preset_model": p["model"],
            }
            for p in t.get("presets", [])
        ]
        choices.append({
            "id": "cfg_input_model",
            "label": "自行输入 Model 名称",
            "select_action": "config_input",
            "config_field": "model",
            "input_prompt": f"输入 {title} 的 model 名称，然后点 Transcribe",
        })
        return normalize_turn({
            "turn_type": "clarify",
            "wizard_mode": True,
            "summary": (
                f"**{title}** — 步骤 3/3：Model\n\n"
                f"Base URL：`{draft.get('base_url', '')}`\n"
                f"API Key：{_mask_key(draft.get('api_key')) if draft.get('api_key') else key_status}"
            ),
            "choices": choices,
            "skill_id": draft.get("skill_id"),
            "config_draft": draft,
        })

    # confirm
    return normalize_turn({
        "turn_type": "clarify",
        "wizard_mode": True,
        "summary": (
            f"**{title}** — 确认保存\n\n"
            f"- Base URL：`{draft.get('base_url', '')}`\n"
            f"- Model：`{draft.get('model', '')}`\n"
            f"- API Key：{_mask_key(draft.get('api_key')) if draft.get('api_key') else key_status}\n\n"
            "点「保存配置」写入 keyring；或退回修改。"
        ),
        "choices": [
            {"id": "cfg_save", "label": "保存配置", "select_action": "cfg_save"},
            {"id": "cfg_step_back", "label": "← 上一步修改", "select_action": "cfg_step_back"},
            {"id": "cfg_back_menu", "label": "← 退回配置菜单", "select_action": "cfg_back_menu"},
        ],
        "skill_id": draft.get("skill_id"),
        "config_draft": draft,
    })


def _advance_step(draft: dict[str, Any]) -> dict[str, Any]:
    order = ["base_url", "api_key", "model", "confirm"]
    idx = order.index(draft["step"])
    if idx < len(order) - 1:
        draft = {**draft, "step": order[idx + 1]}
    return draft


def _retreat_step(draft: dict[str, Any]) -> dict[str, Any]:
    order = ["base_url", "api_key", "model", "confirm"]
    idx = order.index(draft["step"])
    if idx > 0:
        draft = {**draft, "step": order[idx - 1]}
    return draft


def run_config_wizard(
    *,
    config_draft: dict | None = None,
    selected_choice_id: str | None = None,
    select_action: str | None = None,
    user_text: str = "",
    choice: dict | None = None,
) -> tuple[dict[str, Any], dict | None]:
    """Returns (turn, config_draft). draft None when wizard exited."""
    if selected_choice_id == "cfg_back_menu" or select_action == "cfg_back_menu":
        return _config_menu_turn(), None

    if selected_choice_id == "ai_setup":
        return _config_menu_turn(), None

    if selected_choice_id == "skill_worker" and not config_draft:
        return _worker_picker_turn(), None

    draft = dict(config_draft) if config_draft else None
    if selected_choice_id in CONFIG_TARGET_IDS and draft is None:
        if selected_choice_id == "skill_worker":
            return _worker_picker_turn(), None
        draft = new_config_draft(selected_choice_id)
        return _step_turn(draft), draft

    if draft is None:
        return _config_menu_turn(), None

    ch = choice or {}

    if select_action == "cfg_step_back" or selected_choice_id == "cfg_step_back":
        draft = _retreat_step(draft)
        return _step_turn(draft), draft

    if select_action == "cfg_skip_key" or selected_choice_id == "cfg_skip_key":
        draft = _advance_step(draft)
        return _step_turn(draft), draft

    if select_action == "config_preset" or (selected_choice_id or "").startswith("preset_"):
        if ch.get("preset_base"):
            draft["base_url"] = ch["preset_base"]
        if ch.get("preset_model"):
            draft["model"] = ch["preset_model"]
        draft = _advance_step(draft)
        return _step_turn(draft), draft

    if ch.get("config_field") and not (user_text or "").strip():
        draft["_pending_field"] = ch["config_field"]
        return _step_turn(draft), draft

    if select_action == "config_input" or selected_choice_id == "cfg_input":
        field = draft.get("_pending_field") or ch.get("config_field") or "base_url"
        val = (user_text or "").strip()
        if val:
            draft[field] = val
            draft["_pending_field"] = None
            draft = _advance_step(draft)
        return _step_turn(draft), draft

    if select_action == "cfg_save" or selected_choice_id == "cfg_save":
        label = _save_draft(draft)
        turn = normalize_turn({
            "turn_type": "clarify",
            "wizard_mode": True,
            "summary": f"**{label} 已保存**（keyring + 元数据）。可继续配置或返回主流程。",
            "choices": [
                {"id": "ai_setup", "label": "继续配置其他组件"},
                {"id": "explore", "label": "返回：扫描项目"},
                {"id": "task", "label": "返回：我有具体任务"},
            ],
            "proposals": [],
        })
        return turn, None

    return _step_turn(draft), draft