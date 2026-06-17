"""new.py (P3 atom per charter sec12 + 3.2 Boot/New/Adopt): Meta proposes InitSpec; wtool + predicate; append ProjectDiscovered + ProjectReady (or Failure via kernel)."""

from pathlib import Path

from ..micro.wtool import append as wtool_append
from ..events import make_event, PROJECT_DISCOVERED, PROJECT_READY
from ..micro.rtool import MicroRtool
from .registry import register_project


def create_new_project(name: str, data_dir: Path | None = None) -> dict:
    """New project (pid from name, independent of Macro cwd). InitSpec in Discovered payload. Predicate on schema/budget/law via wtool. Ready state advances accepted."""
    pid = (name or "unnamed").replace("/", "_").replace(" ", "_")
    if not pid:
        pid = "unnamed"
    reg = register_project(pid, macro_path=None, data_dir=data_dir)
    # Meta proposes InitSpec (budget/law included for predicate checks)
    init_spec = {
        "name": pid,
        "budget": {"tokens": 100000, "steps": 50},
        "law": {"version": "default-v1", "confirm_mode": "auto_for_new"},
    }
    disc_ev = make_event(PROJECT_DISCOVERED, {"init_spec": init_spec, "proposed_by": "meta"})
    disc_mid = wtool_append(pid, disc_ev, data_dir=data_dir)
    ready_ev = make_event(PROJECT_READY, {"name": pid, "init_spec": init_spec})
    ready_mid = wtool_append(pid, ready_ev, data_dir=data_dir)
    # use rtool for read per integration req (proj read of new state)
    r = MicroRtool(pid, data_dir=data_dir)
    _ = r.read_accepted_head()
    return {
        "project_id": pid,
        "discovered": disc_mid,
        "ready": ready_mid,
        "registry": reg,
    }
