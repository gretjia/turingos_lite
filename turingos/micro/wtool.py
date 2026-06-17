"""wtool.append(event) per A02: builds via commit-builder, always advances tape, conditionally accepted per state machine (FC-A03/04)."""

from datetime import datetime, timezone
from pathlib import Path

from ..core.ids import make_micro_id, strip_micro_id
from ..core.errors import MicroGitError
from .git_tape import MicroGitTape, get_micro_git_dir
from .refs import get_ref, update_ref
from .commit_builder import append_commit
from ..events import ACCEPTED_STATE_EVENTS, FAILURE_NODE, MICRO_PREDICATE_RESULT, make_event
from ..predicates.kernel import PredicateKernel

# P4 integration (surgical): capsule compiler call after WorkOrder for WorkCapsuleBuilt
# (visible + private_contract per charter 3.3/3.7/FC-A08; caller supplies macro contract + data)
from ..capsule.compiler import compile_work_capsule


def append_work_capsule_built_after_order(
    project_id: str,
    capsule_id: str,
    data_dir: Path | None = None,
    mission: str | None = None,
    atom: str | None = None,
    law: str | None = None,
    allowed: list[str] | None = None,
    forbidden: list[str] | None = None,
    known_failures: list[str] | None = None,
    output_contract: str | None = None,
    macro_completion_contract: str | None = None,
) -> str:
    """P4: Call site AFTER WorkOrderProposed (per 3.3 Intent flow, FC-A08).
    Uses compiler to build visible capsule (shield applied, no hidden) + private in CAS.
    Returns the μ: of the appended WORK_CAPSULE_BUILT (which includes macro_completion_contract).
    Used by cli dispatch and E2E to replace hardcoded; keeps wtool as single append path.
    """
    cap = compile_work_capsule(
        project_id,
        capsule_id,
        mission=mission,
        atom=atom,
        law=law,
        allowed=allowed,
        forbidden=forbidden,
        known_failures=known_failures,
        output_contract=output_contract,
        macro_completion_contract=macro_completion_contract,
        data_dir=data_dir,
    )
    payload = {
        "capsule_id": capsule_id,
        "contract": cap["macro_completion_contract"],
        "capsule_hash": cap.get("capsule_hash"),
        "visible_ref": cap.get("visible_path"),
    }
    ev = make_event("WorkCapsuleBuilt", payload)
    return append(
        project_id,
        ev,
        data_dir=data_dir,
        source="turingos:capsule",
        issuer="compiler",
    )


def append(
    project_id: str,
    event: dict,
    data_dir: Path | None = None,
    source: str | None = None,
    issuer: str | None = None,
    receipts: dict | None = None,
    anchors: dict | None = None,
    _bypass_predicate: bool = False,
) -> str:
    """
    Main append entrypoint. event must have 'event_type' + 'payload' (use events.make_event).
    - Always: create commit, update refs/heads/tape .
    - Accepted update IFF event_type in ACCEPTED_STATE_EVENTS (failures + MacroObservationImported do not; per charter 3.6 / FC-A04).
    Returns μ:<oid> of the new tape tip.
    """
    if not isinstance(event, dict) or "event_type" not in event:
        raise MicroGitError("wtool.append requires dict event with event_type")

    gt = MicroGitTape(project_id, data_dir=data_dir)
    # ensure initialized (safe, creates genesis if needed)
    gt.init()

    git_dir = gt.git_dir
    tape_ref = "refs/heads/tape"
    accepted_ref = "refs/heads/accepted"

    prev_tip = get_ref(git_dir, tape_ref)
    prev_accepted = get_ref(git_dir, accepted_ref)

    # Phase 2: PredicateKernel gate (before enrich). Compute for non-meta; used for FAIL->FailureNode + MicroPredicateResult appends.
    # Context carries receipts/anchors (separate in append) for receipt/anchor preds.
    presult = None
    context = None
    if not _bypass_predicate and event.get("event_type") != MICRO_PREDICATE_RESULT:
        kernel = PredicateKernel()
        context = {
            "project_id": project_id,
            "prev_tape_tip": make_micro_id(prev_tip) if prev_tip else None,
            "prev_accepted_head": make_micro_id(prev_accepted) if prev_accepted else None,
            "git_dir": str(git_dir),
        }
        if receipts is not None:
            context["receipts"] = receipts
        if anchors is not None:
            context["anchors"] = anchors
        presult = kernel.validate(event, context)
        # Note: meta appends of result/failure done *after* main (see below) to keep parent correct for business event.

    # enrich event with before snapshot (for envelope)
    event = dict(event)  # copy
    event["prev_tape_tip"] = make_micro_id(prev_tip) if prev_tip else None
    event["accepted_head_before"] = make_micro_id(prev_accepted) if prev_accepted else None
    event["parent_hashes"] = [make_micro_id(prev_tip)] if prev_tip else []

    new_oid = append_commit(
        git_dir,
        parent=prev_tip,
        event=event,
        source=source or "turingos:cli",
        issuer=issuer or "user",
        receipts=receipts,
        anchors=anchors,
    )

    # ALWAYS advance tape_tip (A02)
    update_ref(git_dir, tape_ref, new_oid)

    # Conditionally advance accepted_head ONLY for permitted state events.
    # Gate: if presult for this, !pass => no advance (FC-A04).
    # Special for MicroPredicateResult: advance accepted IFF it passed *and* its target_event_type is an ACCEPTED_STATE_EVENT (so failure/obs ratifications do not advance).
    event_type = event["event_type"]
    do_accept = event_type in ACCEPTED_STATE_EVENTS
    if presult is not None and event_type != MICRO_PREDICATE_RESULT:
        if not presult.passed:
            do_accept = False
    if event_type == MICRO_PREDICATE_RESULT:
        pl = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        target_et = pl.get("target_event_type")
        if not (pl.get("passed", False) and target_et in ACCEPTED_STATE_EVENTS):
            do_accept = False
    if do_accept:
        update_ref(git_dir, accepted_ref, new_oid)

    # Failures and observation-only explicitly leave accepted unchanged (FC-A03/04)
    # (no else needed)

    # Phase 2 integration continued: AFTER main, append MicroPredicateResult (always for this path) + FailureNode on !pass.
    # Use bypass=True to avoid infinite predicate generation on the meta events themselves.
    if presult is not None:
        pred_event = make_event(
            MICRO_PREDICATE_RESULT,
            {
                "target_event_type": event_type,
                "passed": presult.passed,
                "failed": presult.failed,
                "prev_tape_tip": context.get("prev_tape_tip") if presult is not None else None,
            },
        )
        append(
            project_id,
            pred_event,
            data_dir=data_dir,
            source=source or "turingos:predicate",
            issuer="kernel",
            receipts=None,
            anchors=None,
            _bypass_predicate=True,
        )
        if not presult.passed:
            fail_event = make_event(
                FAILURE_NODE,
                {
                    "reason": "Micro predicate gate rejected",
                    "failed": presult.failed,
                    "target_event_type": event_type,
                },
            )
            append(
                project_id,
                fail_event,
                data_dir=data_dir,
                source=source or "turingos:predicate",
                issuer="kernel",
                receipts=None,
                anchors=None,
                _bypass_predicate=True,
            )

    # return current tape tip (post any metas); per docstring "new tape tip". Callers/tests updated for P2 reality (interleaved results).
    final_tip = get_ref(git_dir, tape_ref)
    return make_micro_id(final_tip)
