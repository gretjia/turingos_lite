"""Facilitator turn JSON schema helpers."""
from __future__ import annotations

import json
import re
from typing import Any

OTHER_CHOICE: dict[str, Any] = {
    "id": "other",
    "label": "其他需求（自行输入）",
    "input_prompt": "你还有什么其他需求？请在下方输入框补充说明。",
    "select_action": "freeform",
}

SUBMIT_CHOICE: dict[str, Any] = {
    "id": "submit",
    "label": "我理解对了，可以提交",
    "select_action": "propose",
}


def _extract_json_blob(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        json.loads(raw)
        return raw
    except json.JSONDecodeError:
        pass
    for pattern in (r"\{[\s\S]*\}", r"\[[\s\S]*\]"):
        m = re.search(pattern, raw)
        if m:
            try:
                json.loads(m.group(0))
                return m.group(0)
            except json.JSONDecodeError:
                continue
    return raw


def ensure_standard_choices(choices: list[dict]) -> list[dict]:
    """Always include submit + other freeform options at end of MCQ."""
    ids = {c.get("id") for c in choices}
    out = [c for c in choices if c.get("id") not in ("other", "submit")]
    if "submit" not in ids:
        out.append(dict(SUBMIT_CHOICE))
    else:
        out.extend(c for c in choices if c.get("id") == "submit")
    if "other" not in ids:
        out.append(dict(OTHER_CHOICE))
    else:
        out.extend(c for c in choices if c.get("id") == "other")
    return out


def normalize_turn(data: dict[str, Any]) -> dict[str, Any]:
    turn_type = data.get("turn_type", "clarify")
    if turn_type not in ("clarify", "propose", "enrich"):
        turn_type = "clarify"
    choices = data.get("choices") or []
    if turn_type == "clarify":
        choices = ensure_standard_choices(choices)
    proposals = data.get("proposals") or []
    if turn_type == "propose" and not proposals:
        turn_type = "clarify"
    out: dict[str, Any] = {
        "turn_type": turn_type,
        "summary": str(data.get("summary", "")).strip(),
        "choices": choices,
        "proposals": proposals,
        "facilitator_note": str(data.get("facilitator_note", "")).strip(),
        "skill_id": data.get("skill_id"),
    }
    cog = data.get("project_cognition")
    if cog:
        out["project_cognition"] = str(cog).strip()
    return out


def parse_turn(raw: str) -> dict[str, Any]:
    blob = _extract_json_blob(raw)
    data = json.loads(blob)
    if not isinstance(data, dict):
        raise ValueError("Facilitator turn must be a JSON object")
    return normalize_turn(data)