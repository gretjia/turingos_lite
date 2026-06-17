"""fake.py (moved from cli._fake_worker, focus first per task + README 'Fake Worker first for E2E').
Implements the exact P1/P2/P3/P4 E2E sequence to keep test_cli_fake_e2e_and_no_zombies + dispatch identical.
Uses existing append_work_capsule_built_after_order (capsule compiler+shield+private+macro_contract per FC-A08).
Then Worker* + receipt + MacroObs (not accepted) + FailureNode (append only) + broadcast for loop.
All appends go through wtool -> predicate kernel (Micro gate). No zombies.
"""
from ..micro.wtool import append as wtool_append, append_work_capsule_built_after_order
from ..capsule.broadcast import broadcast_failure
from ..events import (
    make_event,
    WORK_ORDER_PROPOSED,
    WORKER_DISPATCH_PREPARED,
    WORKER_RUN_STARTED,
    WORKER_RUN_RECEIPT_IMPORTED,
    MACRO_OBSERVATION_IMPORTED,
    FAILURE_NODE,
)
from .base import WorkerBase


class FakeWorker(WorkerBase):
    """Fake command worker. Simulates external bundle run for E2E harness validation.
    Per charter 1.5: blackbox boundary, TuringOS does typed receipts + predicate.
    """

    name = "fake_command"

    def run(self, pid: str, capsule_id: str, worker_name: str = "fake_command") -> dict:
        # Simulate contract before (FC-A08/09) + order
        wtool_append(
            pid,
            make_event(WORK_ORDER_PROPOSED, {"capsule_id": capsule_id, "worker": worker_name}),
        )
        # P4: capsule built (visible+private CAS, shield, macro_completion_contract) AFTER order
        append_work_capsule_built_after_order(
            pid,
            capsule_id,
            mission="Create src/hello.txt with hello from turingos per captured intent.",
            atom="P4-capsule-atom",
            law="Micro Predicate is gate; visible never contains hidden; use μ:/macro: scale names.",
            allowed=["src/", "tests/", ".turingos/capsules/"],
            forbidden=[".git/", "private_*/", "~/.ssh/"],
            known_failures=["prior-timeout-on-long-run", "missing-macro-contract-in-capsule"],
            output_contract="produce receipt + artifacts + exit0; Macro actions via observer only",
            macro_completion_contract="macro:git:demo_app:abc123:success on hello.txt",
        )
        wtool_append(pid, make_event(WORKER_DISPATCH_PREPARED, {"capsule_id": capsule_id}))

        # "run" fake + started (use base + direct for WorkerRunStarted)
        self._append_run_started(pid, capsule_id)
        receipt = {"status": "done", "artifacts": ["src/hello.txt"], "exit": 0}
        wtool_append(
            pid,
            make_event(WORKER_RUN_RECEIPT_IMPORTED, {"capsule_id": capsule_id, "worker": worker_name}),
            receipts={"run.json": receipt},
        )

        # P5: observation via observer (after dispatch, P4 integration; imports diff/branch/PR as MacroObservationImported with scale)
        # (replaces direct; exercises macro/ + wtool/predicate/anchors/contract + acc unchanged per FC-A)
        from turingos.macro.observer import import_macro_observation
        import_macro_observation(
            pid,
            capsule_id,
            macro_path=".",
            diff="+hello from turingos",
            macro_ref="macro:git:demo_app:fake123",
        )

        # exercise failure path (advances tape, NOT accepted per FC-A03/04)
        wtool_append(
            pid,
            make_event(FAILURE_NODE, {"reason": "simulated for test", "capsule_id": capsule_id}),
        )

        # P4: after failure in loop, broadcast reducer -> SHIELD/BROADCAST_RULE_UPDATED (for next variant + shield)
        br = broadcast_failure({"reason": "simulated for test", "capsule_id": capsule_id}, pid=pid)
        for ev in br.get("events", []):
            wtool_append(pid, ev)

        return receipt
