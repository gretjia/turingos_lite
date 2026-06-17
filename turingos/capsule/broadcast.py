"""P4 broadcast.py: Broadcast reducer for failure rules -> next variant (Failure Memory Feedback Loop 3.8).
Phase 8: thin delegation to turingos/failure/ (memory.py + clustering + shield_policy) per charter sec12/3.8.
Surgical: only this file + failure/ + min cli/tests. broadcast_failure contract unchanged for callers (wtool, fake, compiler).
"""

from typing import Any


def broadcast_failure(failure: dict, pid: str | None = None, data_dir: Any = None) -> dict:
    """Broadcast reducer.
    Input: FailureNode dict (or minimal {"reason":.., "capsule_id":..}).
    Output: {"events": [Micro events to append], "rule":.., "next_shield_variant": ..}
    Caller must append the events (ensures FC-A01 typed + wtool predicate gate + failure always appends).
    Phase 8: delegates to failure.memory.process_failure_memory (FailureNode->quantize(cluster)->rule->shield update).
    """
    from ..failure.memory import process_failure_memory
    return process_failure_memory(failure, pid=pid, data_dir=data_dir)
