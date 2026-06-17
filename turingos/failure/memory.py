"""Phase 8 failure/memory.py (per charter section 12, 3.8 Failure Memory Feedback Loop).

Failure Memory: FailureNode -> Quantization (clustering) -> Cluster Reducer -> Broadcast rule + Shield policy update for next variant.
Core of feedback: produces typed Micro events (BROADCAST_RULE_UPDATED, SHIELD_RULE_UPDATED) for wtool.append.
Pure functions; caller (broadcast_failure / fake / dispatch) does appends to ensure predicate kernel + append-only + scale μ: + FC-A.
Integrates with existing broadcast_failure (thin delegation), wtool, capsule shield/variants for compat.
Every object names scale (μ: from tape).
"""

from typing import Any

from ..events import make_event, BROADCAST_RULE_UPDATED, SHIELD_RULE_UPDATED

from .clustering import failure_to_quantized_cluster
from .shield_policy import apply_broadcast_rule_to_shield, compile_shield_fallback


def process_failure_memory(
    failure: dict, pid: str | None = None, data_dir: Any = None
) -> dict:
    """Main entry for failure feedback loop.
    Input: FailureNode dict (or {"reason":.., "capsule_id":..} from tape or direct).
    Output: {"events": [typed Micro for append], "rule":.., "next_shield_variant": .., "quantized":..}
    Matches prior broadcast_failure contract exactly for surgical compat.
    Quantize + cluster via clustering; shield update via shield_policy.
    Events are state events (advance accepted_head per events.ACCEPTED..).
    """
    if not isinstance(failure, dict):
        failure = {"reason": str(failure)}

    qkey, cluster, capsule_id = failure_to_quantized_cluster(failure)
    reason = (
        failure.get("reason")
        or failure.get("payload", {}).get("reason")
        or "unspecified-failure"
    )

    rule = {
        "type": "failure_memory_broadcast",
        "from_failure": reason[:128],
        "quantized": qkey,
        "cluster": cluster,
        "capsule_id": capsule_id,
        "next_variant": f"shield-min-via-broadcast-{qkey}",
        "rule": f"on {cluster} failure in {capsule_id}, tighten shield for next (hide amplified priors; reduce context)",
    }

    # Base + policy apply (lazy to match existing style, prevent cycles)
    # Use capsule for base compile_shield (known_failures path) + variants for full
    try:
        from ..capsule.shield import compile_shield as _compile_shield
        base_shield = _compile_shield(known_failures=[reason, cluster])
    except Exception:
        base_shield = compile_shield_fallback()

    try:
        from ..capsule.variants import get_shield_variant as _get_variant
        next_variant = _get_variant(rule, base_shield)
    except Exception:
        next_variant = apply_broadcast_rule_to_shield(rule, base_shield)

    # Typed events (FC-A01, per charter 7.2; append via wtool for pred gate)
    br_event = make_event(
        BROADCAST_RULE_UPDATED,
        {
            "rule": rule,
            "capsule_id": capsule_id,
            "quantized_failure": qkey,
        },
    )
    sr_event = make_event(
        SHIELD_RULE_UPDATED,
        {
            "shield": next_variant,
            "rule_ref": qkey,
            "capsule_id": capsule_id,
            "applied_to_next": True,
        },
    )

    return {
        "events": [br_event, sr_event],
        "rule": rule,
        "next_shield_variant": next_variant,
        "quantized": qkey,
    }
