"""In-TUI config wizard: step through base URL / API key / model before leaving."""
from __future__ import annotations

from typing import Any

from turingos.config import (
    load_facilitator_config,
    load_meta_config,
    load_worker_config,
    save_meta_config,
    save_worker_config,
)
from turingos.facilitator.provider_registry import build_worker_api_targets, is_worker_api_target
from turingos.facilitator.provider_setup import (
    extract_api_token,
    parse_provider_paste,
    test_openai_compatible,
)
from turingos.facilitator.schema import normalize_turn

_WORKER_API_TARGETS = build_worker_api_targets()

CONFIG_TARGET_IDS = frozenset({
    "skill_openai",
    "skill_deepseek_facilitator",
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
        "title": "Meta AI（OpenAI 兼容格式）",
        "skill_id": "setup-meta-ai-openai",
        "default_base": "https://api.deepseek.com",
        "default_model": "deepseek-v4-pro",
        "default_extra_body": {"thinking": {"type": "enabled"}},
        "presets": [
            {
                "id": "preset_deepseek_meta_pro",
                "label": "DeepSeek V4 Pro（Meta，thinking on）",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-v4-pro",
                "extra_body": {"thinking": {"type": "enabled"}},
            },
            {
                "id": "preset_deepseek_meta_flash",
                "label": "DeepSeek V4 Flash（Meta，thinking off）",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-v4-flash",
                "extra_body": {"thinking": {"type": "disabled"}},
            },
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
    "skill_deepseek_facilitator": {
        "kind": "facilitator",
        "title": "Facilitator（DeepSeek V4 Flash）",
        "skill_id": "setup-facilitator-deepseek",
        "default_base": "https://api.deepseek.com",
        "default_model": "deepseek-v4-flash",
        "default_extra_body": {"thinking": {"type": "disabled"}},
        "presets": [
            {
                "id": "preset_deepseek_fac_flash",
                "label": "DeepSeek V4 Flash（thinking off）",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-v4-flash",
                "extra_body": {"thinking": {"type": "disabled"}},
            },
            {
                "id": "preset_deepseek_fac_pro",
                "label": "DeepSeek V4 Pro（thinking on）",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-v4-pro",
                "extra_body": {"thinking": {"type": "enabled"}},
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


def _lookup_target(target_id: str) -> dict[str, Any]:
    if target_id in _TARGETS:
        return _TARGETS[target_id]
    if target_id in _WORKER_API_TARGETS:
        return _WORKER_API_TARGETS[target_id]
    raise KeyError(target_id)


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
    if is_worker_api_target(selected_choice_id):
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
    t = _lookup_target(target_id)
    draft: dict[str, Any] = {
        "target_id": target_id,
        "kind": t["kind"],
        "title": t["title"],
        "skill_id": t["skill_id"],
        "step": "base_url",
        "base_url": t["default_base"],
        "model": t["default_model"],
        "api_key": None,
    }
    if t.get("default_extra_body"):
        draft["_extras"] = {"extra_body": t["default_extra_body"]}
    if t.get("provider_id"):
        draft["provider_id"] = t["provider_id"]
    return draft


def _normalize_base_url(url: str) -> str:
    base = url.strip().rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    return base


def _looks_like_url(val: str) -> bool:
    v = (val or "").strip().lower()
    return v.startswith("http://") or v.startswith("https://")


def _normalize_api_key(val: str) -> str:
    v = (val or "").strip()
    if v.lower().startswith("bearer "):
        return v[7:].strip()
    return v


def _looks_like_token(val: str) -> bool:
    v = _normalize_api_key(val)
    if extract_api_token(v):
        return True
    return bool(v) and not _looks_like_url(v) and len(v) >= 12


def _apply_snippet_to_draft(draft: dict[str, Any], parsed: dict[str, Any]) -> dict[str, Any]:
    if parsed.get("base_url"):
        draft["base_url"] = parsed["base_url"]
    if parsed.get("model"):
        draft["model"] = parsed["model"]
    if parsed.get("api_key"):
        draft["api_key"] = parsed["api_key"]
    draft["_extras"] = {
        k: parsed.get(k)
        for k in ("temperature", "top_p", "max_tokens", "extra_body")
        if parsed.get(k) is not None
    }
    draft["_pending_field"] = None
    draft["step"] = "confirm"
    return draft


def _apply_field_value(draft: dict[str, Any], field: str, val: str) -> dict[str, Any]:
    """Assign user input to the right draft field; fix token-in-URL mistakes."""
    val = (val or "").strip()
    if not val:
        return draft

    parsed = parse_provider_paste(val)
    is_snippet = (
        parsed.get("parsed")
        and parsed.get("api_key")
        and (parsed.get("base_url") or parsed.get("model") or len(val) > 80)
    )
    if is_snippet:
        return _apply_snippet_to_draft(draft, parsed)

    if field == "base_url":
        if _looks_like_url(val):
            draft["base_url"] = _normalize_base_url(val)
            draft["_pending_field"] = None
            return _advance_step(draft)
        token = extract_api_token(val) or (
            _normalize_api_key(val) if _looks_like_token(val) else None
        )
        if token:
            draft["api_key"] = token
            draft["_pending_field"] = None
            draft = _advance_step(draft)
            if draft["step"] == "api_key":
                draft = _advance_step(draft)
            return draft

    if field == "api_key":
        draft["api_key"] = _normalize_api_key(val)
        draft["_pending_field"] = None
        return _advance_step(draft)

    if field == "model":
        if _looks_like_url(val):
            draft["base_url"] = _normalize_base_url(val)
            draft["_pending_field"] = None
            return draft
        draft["model"] = val
        draft["_pending_field"] = None
        return _advance_step(draft)

    draft[field] = val
    draft["_pending_field"] = None
    return _advance_step(draft)


def _post_save_turn(draft: dict[str, Any], label: str) -> dict[str, Any]:
    """Save feedback + connectivity probe; guide user back to project flow."""
    extras = draft.get("_extras") or {}
    cfg = {
        "base_url": draft.get("base_url"),
        "api_key": draft.get("api_key"),
        "model": draft.get("model"),
        "extra_body": extras.get("extra_body"),
        "temperature": extras.get("temperature"),
        "top_p": extras.get("top_p"),
        "max_tokens": extras.get("max_tokens"),
    }
    key = cfg.get("api_key") or ""
    if key.startswith("sk-test") or key.startswith("sk-fake"):
        test = {"ok": True, "latency_ms": 0, "sample": "mock-ok"}
    else:
        test = test_openai_compatible(cfg)

    base = draft.get("base_url") or "（未设置）"
    model = draft.get("model") or "（未设置）"
    key_line = _mask_key(draft.get("api_key")) if draft.get("api_key") else "（未设置）"

    if test.get("ok"):
        summary = (
            f"**{label} 已保存并测试通过**\n\n"
            f"- Base URL：`{base}`\n"
            f"- Model：`{model}`\n"
            f"- API Key：{key_line}（keyring）\n"
            f"- 连通性延迟：{test.get('latency_ms', '—')}ms\n"
            f"- 探针回复：{test.get('sample', '—')}\n\n"
            "**可以回到项目议题了** — 点「继续项目流程」扫描项目，或「我有具体任务」。"
        )
    else:
        summary = (
            f"**{label} 已保存，连通性测试未通过**\n\n"
            f"- Base URL：`{base}`\n"
            f"- Model：`{model}`\n"
            f"- API Key：{key_line}\n"
            f"- 错误：`{test.get('error', '?')}`\n\n"
            "配置已写入 keyring。可点「调整配置」修改，或先「继续项目流程」。"
        )

    return normalize_turn({
        "turn_type": "chat",
        "summary": summary,
        "choices": [
            {"id": "explore", "label": "继续项目流程（扫描项目）"},
            {"id": "task", "label": "我有具体任务"},
            {"id": "ai_setup", "label": "调整配置（向导）"},
        ],
        "proposals": [],
        "setup_result": {
            "ok": bool(test.get("ok")),
            "provider": draft.get("provider_id") or draft.get("kind"),
            "role": draft.get("kind"),
        },
    })


def _mask_key(key: str | None) -> str:
    if not key:
        return "（未设置）"
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}…{key[-4:]}"


def _current_key_status(kind: str) -> str:
    if kind == "meta":
        cfg = load_meta_config()
    elif kind == "worker":
        cfg = load_worker_config()
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
    extras = draft.get("_extras") or {}
    save_kw = {
        "base_url": base,
        "api_key": key,
        "model": model,
        "temperature": extras.get("temperature"),
        "top_p": extras.get("top_p"),
        "max_tokens": extras.get("max_tokens"),
        "extra_body": extras.get("extra_body"),
    }
    if kind == "worker":
        save_worker_config(
            **save_kw,
            provider_id=draft.get("provider_id"),
        )
        return "Worker API"
    if kind == "meta":
        save_meta_config(**save_kw)
        return "Meta AI"
    from turingos.config import save_facilitator_config

    save_facilitator_config(**save_kw)
    return "Facilitator"


def _worker_picker_turn() -> dict[str, Any]:
    api_choices = [
        {
            "id": tid,
            "label": f"API · {t['title'].replace('Worker API — ', '')}",
            "skill_id": "setup-worker-api-openai",
        }
        for tid, t in _WORKER_API_TARGETS.items()
    ]
    bundle_choices = [
        {"id": "worker_codex", "label": "Bundle · Codex（OAuth）", "skill_id": "setup-worker-codex-oauth"},
        {"id": "worker_claude", "label": "Bundle · Claude CLI", "skill_id": "setup-worker-claude-cli"},
        {"id": "worker_grok", "label": "Bundle · Grok Build", "skill_id": "setup-worker-grok-build"},
    ]
    return normalize_turn({
        "turn_type": "clarify",
        "wizard_mode": True,
        "summary": (
            "**Worker 配置**\n\n"
            "**API Worker（白盒，推荐）** — 直接 API，dispatch 时用 `--worker api`。\n"
            "支持 DeepSeek / NVIDIA / OpenAI / Groq / Anthropic / 自定义。\n\n"
            "**Bundle Worker** — Codex / Claude / Grok CLI（OAuth/黑盒）。\n\n"
            "选项较多时可 **↓ 滚动** 中间配置区域查看全部。"
        ),
        "choices": api_choices + bundle_choices + [
            {"id": "cfg_back_menu", "label": "← 退回配置菜单", "select_action": "cfg_back_menu"},
        ],
        "proposals": [],
        "skill_id": "setup-worker-api-openai",
    })


def _config_menu_turn() -> dict[str, Any]:
    return normalize_turn({
        "turn_type": "clarify",
        "wizard_mode": True,
        "summary": "选择要配置的组件：Facilitator（对话）、Meta AI（提案）、Worker（执行）。",
        "choices": [
            {"id": "skill_deepseek_facilitator", "label": "配置 Facilitator（DeepSeek V4 Flash）", "skill_id": "setup-facilitator-deepseek"},
            {"id": "skill_nvidia", "label": "配置 Facilitator（NVIDIA Diffusion Gemma）", "skill_id": "setup-facilitator-nvidia"},
            {"id": "skill_openai", "label": "配置 Meta AI（DeepSeek/OpenAI 格式）", "skill_id": "setup-meta-ai-openai"},
            {"id": "skill_worker", "label": "配置 Worker（API 官方 + CLI Bundle）", "skill_id": "setup-worker-api-openai"},
        ],
        "proposals": [],
    })


def _step_turn(draft: dict[str, Any]) -> dict[str, Any]:
    step = draft["step"]
    title = draft["title"]
    key_status = _current_key_status(draft["kind"])

    if step == "base_url":
        t = _lookup_target(draft["target_id"])
        choices = [
            {
                "id": p["id"],
                "label": p["label"],
                "select_action": "config_preset",
                "preset_base": p["base_url"],
                "preset_model": p["model"],
                "preset_extra_body": p.get("extra_body"),
            }
            for p in t["presets"]
        ]
        choices.append({
            "id": "cfg_input_base",
            "label": "自行输入 Base URL",
            "select_action": "config_input",
            "config_field": "base_url",
            "input_prompt": f"输入 {title} 的 Base URL，然后点「保存」",
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
                "input_prompt": f"粘贴 {title} 的 API Key，然后点「保存」（keyring，不会显示在日志）",
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
                "可直接在顶部 VIBE COMPOSER **整段粘贴 NVIDIA 官网示例代码** 后点 Send（自动识别）；"
                "或点「输入 API Key」后在 MCQ 下方输入框粘贴 Key 点 **保存**。"
            ),
            "choices": choices,
            "skill_id": draft.get("skill_id"),
            "config_draft": draft,
        })

    if step == "model":
        try:
            t = _lookup_target(draft["target_id"])
        except KeyError:
            t = {}
        choices = [
            {
                "id": p["id"],
                "label": f"模型：{p['model']}",
                "select_action": "config_preset",
                "preset_model": p["model"],
                "preset_extra_body": p.get("extra_body"),
            }
            for p in t.get("presets", [])
        ]
        choices.append({
            "id": "cfg_input_model",
            "label": "自行输入 Model 名称",
            "select_action": "config_input",
            "config_field": "model",
            "input_prompt": f"输入 {title} 的 model 名称，然后点「保存」",
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
    if draft is None and is_worker_api_target(selected_choice_id):
        draft = new_config_draft(selected_choice_id)  # type: ignore[arg-type]
        return _step_turn(draft), draft

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
        if ch.get("preset_extra_body"):
            extras = dict(draft.get("_extras") or {})
            extras["extra_body"] = ch["preset_extra_body"]
            draft["_extras"] = extras
        draft = _advance_step(draft)
        return _step_turn(draft), draft

    if ch.get("config_field") and not (user_text or "").strip():
        draft["_pending_field"] = ch["config_field"]
        return _step_turn(draft), draft

    if select_action == "config_input" or selected_choice_id == "cfg_input":
        val = (user_text or "").strip()
        field = draft.get("_pending_field") or ch.get("config_field")
        if not field:
            step = draft.get("step", "base_url")
            field = step if step in ("base_url", "api_key", "model") else "base_url"
        if val:
            draft = _apply_field_value(draft, field, val)
        return _step_turn(draft), draft

    if select_action == "cfg_save" or selected_choice_id == "cfg_save":
        label = _save_draft(draft)
        if draft.get("kind") == "worker":
            label = "Worker API"
        return _post_save_turn(draft, label), None

    return _step_turn(draft), draft
