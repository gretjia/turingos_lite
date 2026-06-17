"""adopt.py (P3 atom per charter sec12 + 3.2): observe Macro (named scale anchor), BackfilledSpec in Discovered; human law confirm; wtool+pred; ProjectDiscovered + ProjectReady (Failure on reject)."""

import subprocess
from pathlib import Path

from ..micro.wtool import append as wtool_append
from ..events import make_event, PROJECT_DISCOVERED, PROJECT_READY, FAILURE_NODE
from ..micro.rtool import MicroRtool
from .registry import register_project
from .law import confirm_law


def adopt_project(path: str = ".", data_dir: Path | None = None) -> dict:
    """Adopt at path: Macro observe (git head -> macro:git:PID:OID anchor), BackfilledSpec; law confirm gate; Discovered/Ready via wtool (predicate on schema etc)."""
    mpath = Path(path).resolve()
    pid = (mpath.name or "adopted").replace("/", "_").replace(" ", "_")
    if not pid:
        pid = "adopted"
    reg = register_project(pid, macro_path=str(mpath), data_dir=data_dir)
    # Observe Macro (FC-A02: only via named macro ref in payload/anchor, not as Micro id)
    macro_oid = "unknown"
    try:
        cp = subprocess.run(
            ["git", "-C", str(mpath), "rev-parse", "--verify", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        macro_oid = cp.stdout.strip() or "unknown"
    except Exception:
        pass
    macro_ref = f"macro:git:{pid}:{macro_oid}"
    back_spec = {
        "path": str(mpath),
        "macro_head": macro_oid,
        "observed": macro_oid != "unknown",
    }
    disc_payload = {"path": str(mpath), "backfilled_spec": back_spec, "macro_ref": macro_ref}
    disc_ev = make_event(PROJECT_DISCOVERED, disc_payload)
    disc_mid = wtool_append(pid, disc_ev, data_dir=data_dir, anchors={"macro.json": {"macro_ref": macro_ref}})
    # human confirm law (charter 3.2 for adopt)
    if not confirm_law(pid, str(mpath)):
        fail_mid = wtool_append(pid, make_event(FAILURE_NODE, {"reason": "law not confirmed for adopt", "path": str(mpath)}), data_dir=data_dir)
        return {"project_id": pid, "discovered": disc_mid, "failure": fail_mid, "registry": reg, "adopted": False}
    ready_ev = make_event(PROJECT_READY, {"name": pid, "path": str(mpath), "backfilled_spec": back_spec})
    ready_mid = wtool_append(pid, ready_ev, data_dir=data_dir)
    # use rtool read (P3 integration)
    r = MicroRtool(pid, data_dir=data_dir)
    _ = r.read_accepted_head()
    return {
        "project_id": pid,
        "discovered": disc_mid,
        "ready": ready_mid,
        "registry": reg,
        "adopted": True,
        "macro_ref": macro_ref,
    }
