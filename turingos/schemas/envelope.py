"""MicroEnvelope schema (Pydantic) per A02 node.json structure."""

from pydantic import BaseModel
from typing import Optional, List

class MicroEnvelope(BaseModel):
    """Envelope stored in node.json inside each Micro commit tree."""
    event_id: str
    schema_version: str = "micro_envelope_v1"
    event_type: str
    scale: str = "micro"
    prev_tape_tip: Optional[str] = None
    accepted_head_before: Optional[str] = None
    parent_hashes: List[str] = []
    payload_hash: str
    source: str
    issuer: str
    issued_at: str
    signature_route: str = "unsigned"
    replay_rule: str = "append_only"
