"""Phase 8 failure/shield_policy.py (per charter section 12, 3.8).

Shield policy: apply broadcast rule (from cluster/quantized FailureNode) to produce next shield variant for subsequent capsules.
Min surgical: dict transform + tighten (progressive context min + hide priors).
Used in failure feedback loop to evolve for next variant.
Integrates via memory; does not write tape (caller wtool + broadcast_failure does).
"""

from typing import Any


def compile_shield_fallback() -> dict:
    """Min fallback (matches style of related capsule code; avoids cross at import time)."""
    return {
        "min_context": "mission+atom+law+allowed+forbidden+macro_contract only; failures summarized",
        "hidden_predicates_count": 2,
        "hidden": ["budget_detail", "predicate_impl"],
        "known_failures_summary": [],
        "min_context_tokens": 1500,
    }


def apply_broadcast_rule_to_shield(broadcast_rule: dict, base_shield: dict | None = None) -> dict:
    """Policy: derive tightened shield variant from failure broadcast rule.
    Tightens min_context_tokens, augments hidden for amplified priors.
    Returns variant dict (for SHIELD_RULE_UPDATED + next capsule shield).
    """
    if not isinstance(broadcast_rule, dict):
        broadcast_rule = {}
    if not isinstance(base_shield, dict) or not base_shield:
        base_shield = compile_shield_fallback()

    variant = dict(base_shield)  # copy
    rule_type = broadcast_rule.get("rule") or broadcast_rule.get("type", "")
    next_v = broadcast_rule.get("next_variant") or "shield-min-via-broadcast"

    variant["variant"] = next_v
    variant["rule_ref"] = broadcast_rule.get("from_failure") or str(broadcast_rule)[:64]

    # tighten: reduce context budget, hide more on failure patterns (evolve)
    base_tokens = base_shield.get("min_context_tokens", 1500)
    variant["min_context_tokens"] = max(800, int(base_tokens * 0.85))

    hides = list(base_shield.get("hidden", []))
    if "avoid" in str(rule_type).lower() or "failure" in str(rule_type).lower():
        hides.append("amplified_prior_failures")
    # dedup order preserving
    seen = set()
    variant["hidden"] = [h for h in hides if not (h in seen or seen.add(h))]

    # min_context update signals evolve
    base_min = base_shield.get("min_context", "mission+atom+law+allowed+forbidden+macro_contract")
    variant["min_context"] = base_min + " + broadcast-variant"
    return variant
