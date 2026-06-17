"""Minimal reducer per A03: Q_t = tape_tip, accepted_head, project status, open capsules (from tape scan)."""

from pathlib import Path

from .rtool import MicroRtool
from ..events import ACCEPTED_STATE_EVENTS


def reduce_state(project_id: str, data_dir: Path | None = None) -> dict:
    """Return current Q_t projection. Uses rtool reads + light scan. Not source of truth."""
    r = MicroRtool(project_id, data_dir=data_dir)
    tip = r.read_tip()
    accepted = r.read_accepted_head()

    # Scan for status: last state event type seen (or 'bootstrapped')
    status = "unknown"
    open_capsules: list[str] = []
    last_state = None

    for coid in r.iter_commits():
        try:
            node = r.load_node(coid)
            et = node.get("event_type")
            if et in ACCEPTED_STATE_EVENTS:
                last_state = et
            if et == "WorkCapsuleBuilt":
                cap_id = node.get("payload", {}).get("capsule_id") or node.get("payload", {}).get("id")
                if cap_id and cap_id not in open_capsules:
                    open_capsules.append(cap_id)
            # naive: could remove on close events, but min for P1
        except Exception:
            pass  # ignore corrupt in reducer

    if last_state:
        status = last_state  # keep original event name clean, no mangling
    elif tip:
        status = "bootstrapped"

    return {
        "tape_tip": tip,
        "accepted_head": accepted,
        "project_status": status,
        "open_capsules": open_capsules,
        "project_id": project_id,
    }
