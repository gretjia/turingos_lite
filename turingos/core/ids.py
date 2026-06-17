"""Scale naming for Micro objects. Every id names its scale: μ:<oid> per charter 1.3."""

def make_micro_id(oid: str) -> str:
    """Return μ: prefixed id. Idempotent."""
    if not oid:
        return oid
    if oid.startswith("μ:"):
        return oid
    return f"μ:{oid}"

def strip_micro_id(mid: str) -> str:
    """Strip μ: prefix to get raw git oid."""
    if mid and mid.startswith("μ:"):
        return mid[2:]
    return mid
