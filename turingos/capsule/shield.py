"""P4 shield.py: Shield Compiler for min context + hide predicates (FC-A05, 1.5, 3.3).

After WorkOrder (per 3.3 flow), before WorkCapsuleBuilt.
Visible capsule for worker gets minimized view; predicates/budget/private stay in private_contract (CAS).
Surgical, no state writes here (compiler orchestrates writes).
"""

from typing import Any


def compile_shield(known_failures: list[str] | None = None, context_budget: int = 4000, **kw: Any) -> dict:
    """Compile a shield descriptor from known failures + law.
    Returns shield config used to derive visible capsule + private hidden set.
    Min context principle: worker sees mission/atom/law/allowed/forbidden/output/macro_contract only.
    """
    kf = known_failures or []
    # Quantize/summarize failures for shield (full detail hidden)
    summary = kf[:3] + (["... (see private)"] if len(kf) > 3 else [])
    # Identify what to hide (predicates, budget etc never visible)
    to_hide = ["budget", "budget_detail", "private_contract", "hidden_predicates", "full_failure_log", "predicate_impl", "shield"]
    # Add any failure that smells internal
    for f in kf:
        fs = str(f).lower()
        if "predicate" in fs or "private" in fs or "budget" in fs:
            to_hide.append(str(f)[:64])

    hidden = list(dict.fromkeys(to_hide))  # dedup order
    return {
        "min_context": "mission+atom+law+allowed+forbidden+macro_contract+output_contract; failures summarized",
        "hidden_predicates_count": len([h for h in hidden if "predicate" in h or "budget" in h]),
        "hidden": hidden,
        "known_failures_summary": summary,
        "min_context_tokens": min(2000, max(800, context_budget // 2)),
        "law": "Micro Predicate Kernel is daily gate (stats/CI/LLM are evidence only). Scale naming mandatory.",
    }


def apply_shield(raw_capsule: dict | str, shield: dict | None = None) -> str:
    """Apply shield to raw capsule content -> worker-visible markdown text.
    Hides anything matching shield["hidden"]; ensures no leak of private/hidden_predicates etc.
    Returns markdown string for .turingos/capsules/<id>.md (visible to external bundle worker).
    """
    if shield is None:
        shield = compile_shield()
    hide_set = set(shield.get("hidden", []))
    hide_set.update({"private_contract", "hidden_predicates", "budget", "shield", "full_raw"})

    if isinstance(raw_capsule, str):
        # already text; defensive strip common leaks
        md = raw_capsule
        for h in list(hide_set):
            if h in md:
                md = md.replace(h, "[HIDDEN-BY-SHIELD]")
        return md

    if not isinstance(raw_capsule, dict):
        raw_capsule = {"capsule_id": "unknown", "mission": str(raw_capsule)}

    vis: dict = {}
    for k, v in raw_capsule.items():
        kl = k.lower()
        if k in hide_set or any(h in kl for h in ["private", "hidden", "budget", "shield", "full"]):
            continue
        vis[k] = v

    # Build canonical visible capsule md (per task spec: mission/atom/law/allowed/forbidden/known_failures/output_contract + macro_completion_contract)
    cap_id = vis.get("capsule_id", raw_capsule.get("capsule_id", "wc_unknown"))
    lines = [f"# Work Capsule {cap_id}", ""]
    order = ["mission", "atom", "law", "allowed", "forbidden", "known_failures", "output_contract", "macro_completion_contract"]
    for key in order:
        if key in vis:
            val = vis[key]
            if isinstance(val, (list, tuple)):
                val_str = "\n  - " + "\n  - ".join(str(x) for x in val)
            else:
                val_str = str(val)
            lines.append(f"**{key}:** {val_str}")
            lines.append("")

    # Fallbacks if missing keys
    if "mission" not in vis:
        lines.append("**mission:** (from intent)")
    if "macro_completion_contract" not in vis:
        lines.append("**macro_completion_contract:** (declared pre-dispatch per FC-A08)")

    md = "\n".join(lines).strip() + "\n"
    # Final leak guard (per 1.5 / FC-A05)
    for bad in ["private_contract", "hidden_predicates", "budget", "shield"]:
        if bad in md:
            md = md.replace(bad, "[SHIELD-REDUCTED]")
    return md
