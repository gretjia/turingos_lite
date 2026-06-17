"""base.py: Min WorkerBase for Phase 6.
All workers: dispatch -> run(pid, capsule_id) does started + work + receipt(s) via wtool (loops, predicate on every append per kernel).
Failure appends. Visible capsule + macro contract pre-declared (caller or inside for fake).
"""
from abc import ABC, abstractmethod
from ..events import make_event, WORKER_RUN_STARTED
from ..micro.wtool import append as wtool_append


class WorkerBase(ABC):
    """Abstract base. name identifies; run returns top receipt dict.
    Subclasses implement specific exec (fake sim, manual paste, cmd template blackbox, api whitebox tool loop).
    """

    name: str = "base"

    def __init__(self, name: str | None = None):
        if name:
            self.name = name

    def _append_run_started(self, pid: str, capsule_id: str) -> str:
        """Common: emit WorkerRunStarted (non-accept advancing). Always via wtool for predicate + scale."""
        return wtool_append(
            pid,
            make_event(WORKER_RUN_STARTED, {"capsule_id": capsule_id, "worker": self.name}),
        )

    @abstractmethod
    def run(self, pid: str, capsule_id: str, worker_name: str | None = None) -> dict:
        """Execute worker for the capsule (after order/capsule built/dispatch prepared by caller or inside).
        Must append WorkerRunStarted + WORKER_RUN_RECEIPT_IMPORTED (with receipts=) + Worker* .
        For api: inner loop appends ToolCall* (each through predicate per 3.5/FC-A07).
        Return final receipt for projection. Never bypass micro tape.
        """
        raise NotImplementedError
