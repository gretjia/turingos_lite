"""Payload hashing (sha256, canonical json) for envelope.payload_hash."""

import hashlib
import json
from typing import Any

def canonical_json(obj: Any) -> bytes:
    """Deterministic json bytes for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def payload_hash(payload: dict) -> str:
    data = canonical_json(payload)
    return hashlib.sha256(data).hexdigest()
