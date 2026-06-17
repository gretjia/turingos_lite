"""manual.py: Manual copy-paste Worker (charter P0 scope, 1.5 blackbox bundle).
Visible capsule shown; user pastes result -> receipt appended via wtool (predicate).
Min surgical stub: no interactive (TUI later), just simulate paste for dispatch compat.
"""
from ..events import make_event, WORKER_DISPATCH_PREPARED, WORKER_RUN_RECEIPT_IMPORTED
from ..micro.wtool import append as wtool_append
from .base import WorkerBase


class ManualWorker(WorkerBase):
    """Manual worker. Per charter: copy-paste path for sovereignty when no exec.
    Visible .turingos/capsules/<id>.md (already compiled pre-dispatch).
    """

    name = "manual"

    def run(self, pid: str, capsule_id: str, worker_name: str = "manual") -> dict:
        # Dispatch prepared (caller may have done order/capsule)
        wtool_append(
            pid,
            make_event(WORKER_DISPATCH_PREPARED, {"capsule_id": capsule_id, "worker": worker_name}),
        )
        self._append_run_started(pid, capsule_id)
        # Simulate user having read visible capsule and pasted result back
        receipt = {
            "status": "manual_paste",
            "note": "user-pasted for " + capsule_id + " (visible capsule in .turingos/capsules/)",
            "artifacts": [],
            "exit": 0,
        }
        wtool_append(
            pid,
            make_event(WORKER_RUN_RECEIPT_IMPORTED, {"capsule_id": capsule_id, "worker": worker_name}),
            receipts={"manual.json": receipt},
        )
        return receipt
