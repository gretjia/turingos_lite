"""P4 variants.py: Shield variants derived from broadcast rules (failure memory feedback).

Per charter: broadcast rules feed next variant for shield (context min + hide update).
Used in Failure Memory loop (3.8) to evolve shields for subsequent capsules.
Surgical min: dict transform only, no side effects, no external state.
"""

from typing import Any


def get_shield_variant(broadcast_rule: dict, base_shield: dict) -> dict:
    """Produce next shield variant from a broadcast failure rule.
    Applies rule to tighten min_context, extend hidden set for next capsule iteration.
    Returns new shield dict (for use by compiler + SHIELD_RULE_UPDATED payload).
    """
    if not isinstance(broadcast_rule, dict):
        broadcast_rule = {}
    if not isinstance(base_shield, dict):
        base_shield = compile_shield_fallback()

    variant = dict(base_shield)  # copy
    rule_type = broadcast_rule.get("rule") or broadcast_rule.get("type", "")
    next_v = broadcast_rule.get("next_variant") or "shield-min-via-broadcast"

    variant["variant"] = next_v
    variant["rule_ref"] = broadcast_rule.get("from_failure") or str(broadcast_rule)[:64]

    # tighten: reduce context, add rule-derived hides (progressive min per loop)
    base_tokens = base_shield.get("min_context_tokens", 1500)
    variant["min_context_tokens"] = max(800, int(base_tokens * 0.85))

    hides = list(base_shield.get("hidden", []))
    if "avoid" in str(rule_type).lower() or "failure" in str(rule_type).lower():
        hides.append("amplified_prior_failures")
    # dedup preserve order
    seen = set()
    variant["hidden"] = [h for h in hides if not (h in seen or seen.add(h))]

    # summary update
    variant["min_context"] = base_shield.get("min_context", "mission+atom+law+allowed+forbidden+macro_contract") + " + broadcast-variant"
    return variant


def compile_shield_fallback() -> dict:
    """Internal fallback (avoid import cycle in variants)."""
    return {
        "min_context": "mission+atom+law+allowed+forbidden+macro_contract only; failures summarized",
        "hidden_predicates_count": 2,
        "hidden": ["budget_detail", "predicate_impl"],
        "known_failures_summary": [],
        "min_context_tokens": 1500,
    }
