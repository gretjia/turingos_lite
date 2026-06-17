"""Phase 8 failure/clustering.py (per charter section 12, 3.8 Failure Memory Feedback Loop).

Quantization + Cluster Reducer for FailureNode -> broadcast rule.
Min impl (simplicity): hash-bucket quant, token prefix cluster.
Pure; no side effects. Called by memory for loop (FailureNode input).
Integrates with broadcast_failure (via delegation) + wtool appends.
"""

from typing import Any


def quantize_failure(reason: str) -> str:
    """Min quantization per charter/research: stable bucket key for failure class."""
    r = reason or "unspecified"
    return f"q:{abs(hash(r)) % 97}"


def cluster_reason(reason: str) -> str:
    """Cluster reducer: group by leading token (e.g. error type prefix)."""
    r = (reason or "").strip()
    if not r:
        return "unknown"
    return r.split()[0]


def failure_to_quantized_cluster(failure: dict) -> tuple[str, str, str]:
    """Extract reason, return (qkey, cluster, capsule_id)."""
    if not isinstance(failure, dict):
        failure = {"reason": str(failure)}
    capsule_id = (
        failure.get("capsule_id")
        or failure.get("payload", {}).get("capsule_id")
        or "wc_unknown"
    )
    reason = (
        failure.get("reason")
        or failure.get("payload", {}).get("reason")
        or "unspecified-failure"
    )
    qkey = quantize_failure(reason)
    cluster = cluster_reason(reason)
    return qkey, cluster, capsule_id
