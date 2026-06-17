"""Facilitator transcription: human NL → charter-compliant event proposals.

Uses OpenAI-compatible API when configured; falls back to deterministic mock
for tests and offline development.
"""
from __future__ import annotations

import json
import re
from typing import Any

from turingos.config import load_meta_config

TRANSCRIBE_SYSTEM = """You are the TuringOS Facilitator (quick transcriber).
Turn the human's natural language intent into precise, charter-compliant TuringOS action items.
Rules (non-negotiable):
- Every object MUST name its scale (μ:<oid> for Micro, macro:git:<pid>:<oid> for Macro).
- TUI is projection only — you only propose; the human confirms and the system dispatches.
- Failures always append. accepted_head only on accepted state events.
- Output ONLY a JSON array of proposed actions. Each has "event_type" and "payload".
- For WorkCapsuleBuilt include "visible_markdown" and "capsule_id".
Known event_types: IntentCaptured, WorkCapsuleBuilt, HumanDecision, WorkerDispatchPrepared,
MacroObservationImported, FailureNode, BroadcastRuleUpdated, ShieldRuleUpdated.
"""

TRANSCRIBE_USER_TEMPLATE = """Current projection: {projection}
Charter rules: projection-only TUI, predicate gates, scale-named objects.
User vibe: {input}
{refine}
Output strict JSON array only."""


def _strip_vibe_prefix(text: str) -> str:
    t = text.strip()
    if t.lower().startswith("vibe:"):
        return t[5:].strip()
    return t


def mock_transcribe(nl: str, projection: dict | None = None) -> list[dict]:
    """Deterministic mock transcriber for tests and offline use."""
    text = _strip_vibe_prefix(nl).lower()
    pid = (projection or {}).get("project_id", "demo_app")
    proposals: list[dict] = []

    if any(w in text for w in ("deliver", "交付", "complete", "finish")):
        proposals.append({
            "event_type": "HumanDecision",
            "payload": {"decision": "approve", "from": "vibe-deliver"},
        })
        proposals.append({
            "event_type": "WorkCapsuleBuilt",
            "payload": {
                "capsule_id": "wc_delivered",
                "visible_markdown": "# Project Delivered\n\nStatus: **Delivered**",
                "status": "delivered",
            },
        })
        return proposals

    if any(w in text for w in ("auth", "认证", "login", "user")):
        proposals.append({
            "event_type": "IntentCaptured",
            "payload": {"task": nl, "from": "vibe-mock"},
        })
        proposals.append({
            "event_type": "WorkCapsuleBuilt",
            "payload": {
                "capsule_id": "wc_auth",
                "visible_markdown": f"# Auth Feature\n\n{nl}\n\nStack: sqlite + React",
                "contract": f"macro:git:{pid}:auth",
            },
        })
        return proposals

    if any(w in text for w in ("todo", "capsule", "app", "create", "创建")):
        stack = "sqlite + React" if "sqlite" in text or "react" in text else "default stack"
        proposals.append({
            "event_type": "IntentCaptured",
            "payload": {"task": nl, "from": "vibe-mock"},
        })
        proposals.append({
            "event_type": "WorkCapsuleBuilt",
            "payload": {
                "capsule_id": "wc_todo_app",
                "visible_markdown": (
                    f"# Todo App Capsule\n\nMission: {nl}\n\n"
                    f"Persistence: {stack}\n\nWill hit tape as μ: nodes."
                ),
                "contract": f"macro:git:{pid}:todo",
            },
        })
        return proposals

    proposals.append({
        "event_type": "IntentCaptured",
        "payload": {"task": nl, "from": "vibe-mock"},
    })
    return proposals


def _parse_json_array(raw: str) -> list[dict]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw)
    if isinstance(data, dict) and "proposals" in data:
        data = data["proposals"]
    if not isinstance(data, list):
        raise ValueError("Expected JSON array of proposals")
    out = []
    for item in data:
        if not isinstance(item, dict) or "event_type" not in item:
            raise ValueError(f"Invalid proposal item: {item}")
        out.append({
            "event_type": item["event_type"],
            "payload": item.get("payload", {}),
        })
    return out


def _call_openai_compatible(
    cfg: dict[str, Any],
    projection: dict,
    nl: str,
    refine_context: str | None,
) -> list[dict]:
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError("openai package required for real LLM transcription") from e

    refine = f"Refine context: {refine_context}" if refine_context else ""
    user_msg = TRANSCRIBE_USER_TEMPLATE.format(
        projection=json.dumps(projection, default=str)[:4000],
        input=nl,
        refine=refine,
    )
    client = OpenAI(base_url=cfg.get("base_url"), api_key=cfg.get("api_key") or "ollama")
    kwargs: dict[str, Any] = {
        "model": cfg.get("model", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": TRANSCRIBE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.2,
    }
    if cfg.get("structured"):
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content or "[]"
    if cfg.get("structured") and content.strip().startswith("{"):
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return _parse_json_array(json.dumps(parsed))
        for key in ("proposals", "actions", "events"):
            if key in parsed:
                return _parse_json_array(json.dumps(parsed[key]))
    return _parse_json_array(content)


def transcribe_intent(
    nl: str,
    projection: dict | None = None,
    *,
    refine_context: str | None = None,
    force_mock: bool = False,
    config: dict[str, Any] | None = None,
) -> list[dict]:
    """Transcribe NL vibe to formal event proposals. Mock when no API or force_mock."""
    projection = projection or {}
    cfg = config or load_meta_config()
    if force_mock or not cfg.get("api_key"):
        return mock_transcribe(nl, projection)
    try:
        return _call_openai_compatible(cfg, projection, nl, refine_context)
    except Exception:
        return mock_transcribe(nl, projection)