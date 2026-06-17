"""anchors.py (P5): Macro anchor helpers (stored under micro commit anchors/ via wtool).
Scale MUST name (macro:*) per 1.3 / FC-A02. Used by observer for declared Macro evidence (TUI replay reconstructs from tape + anchors).
Min: pure makers + basic load. No state.
"""

from typing import Any


def make_macro_anchor(project_id: str, ref: str, kind: str = "git") -> dict:
    """Return anchor dict with canonical scale-named macro_ref. Matches adopt + predicate exercised paths."""
    if kind == "git":
        macro_ref = f"macro:git:{project_id}:{ref or 'HEAD'}"
    elif kind == "pr":
        macro_ref = f"macro:pr:{ref}" if "/" in str(ref) or "#" in str(ref) else f"macro:pr:local/{project_id}#{ref}"
    else:
        macro_ref = ref if str(ref).startswith("macro:") else f"macro:{kind}:{project_id}:{ref or 'HEAD'}"
    return {"macro_ref": macro_ref}


def load_macro_anchors(anchors: dict | None) -> list[dict]:
    """Extract macro anchors from wtool anchors context (for predicate/reducer). Min."""
    if not anchors:
        return []
    res = []
    for v in (anchors.values() if isinstance(anchors, dict) else [anchors]):
        if isinstance(v, dict) and "macro_ref" in v:
            res.append(v)
        elif isinstance(v, str) and v.startswith("macro:"):
            res.append({"macro_ref": v})
    return res
