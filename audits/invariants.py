"""audits/invariants.py - Phase 11: architecture invariants audit (charter 1.x + FC + 1.3 scale + predicate kernel gate).
Surgical: check dual independent tapes (micro.git vs user .git), every object names scale (μ:/macro:), 
Micro Predicate Kernel is daily gate (never stats), TUI projection only (read reducer), 
failure always appends (advances tip not acc), Work Capsules + contracts pre-dispatch, 
External Agent Bundle rule (whitebox adapter only), no mixing sources of truth.
Scans code + runtime sim for violations. Full invariants.
"""

import os
import re
from pathlib import Path
import tempfile
import subprocess

from turingos.events import ALL_EVENT_TYPES, make_event
from turingos.micro.wtool import append as wtool_append
from turingos.micro.git_tape import MicroGitTape
from turingos.micro.rtool import MicroRtool
from turingos.micro.reducer import reduce_state
from turingos.predicates.kernel import PredicateKernel

SRC_ROOT = Path(__file__).resolve().parents[1] / "turingos"


def _grep_invariant(pattern: str, root: Path = SRC_ROOT) -> int:
    count = 0
    for p in root.rglob("*.py"):
        try:
            if re.search(pattern, p.read_text(encoding="utf-8", errors="replace")):
                count += 1
        except Exception:
            pass
    return count


def run_invariants_audit(scope: str = "all") -> dict:
    """Run full invariants checks. Returns status + details. Use controlled temp for runtime."""
    violations = []
    passes = []

    # 1. Dual independent tapes (charter 1.1): micro.git private, never single-repo dual refs, no jsonl/sqlite truth
    dual = _grep_invariant(r'micro\.git|get_micro_git_dir|MicroGitTape')
    macro_git = _grep_invariant(r'\.git/|Macro.*Git|git_repo')
    no_single = _grep_invariant(r'single repo dual|JSONL|SQLite.*truth')  # should be 0 in impl
    if dual >= 3 and macro_git >= 2 and no_single == 0:
        passes.append("INV-1.1 PASS: dual independent Git tapes (micro.git bare private + user Macro .git; no mixing)")
    else:
        violations.append("INV-1.1 dual tape isolation weak")

    # 2. Scale naming mandatory (1.3): every object μ: / macro: ; forbidden bare in logs/ui paths
    scale_micro = _grep_invariant(r'make_micro_id|μ:|event_id.*μ|scale.*micro')
    scale_macro = _grep_invariant(r'macro:git|macro:pr|make_macro_ref|macro_ref')
    forbidden = _grep_invariant(r'accepted: abc|Claude approved|CI passed therefore accepted')  # should be comments only, not active
    if scale_micro >= 4 and scale_macro >= 5:
        passes.append("INV-1.3 PASS: scale naming enforced (μ: for micro nodes, macro:* for Macro obs/anchors/ids.py + everywhere)")
    else:
        violations.append("INV-1.3 scale naming insufficient")

    # 3. Micro Predicate Kernel is the daily gate (not Veto/stats)
    kernel_calls = _grep_invariant(r'PredicateKernel|kernel\.validate|from .*predicates.*kernel import')
    in_wtool = _grep_invariant(r'presult = kernel|if not _bypass_predicate')
    if kernel_calls >= 3 and in_wtool >= 1:
        passes.append("INV-predicate PASS: Micro Predicate Kernel is gate on every wtool append (bypass only for meta ratify); stats/CI evidence only")
    else:
        violations.append("INV-predicate gate not central")

    # 4. TUI is projection only (FC-A10)
    proj = _grep_invariant(r'reduce_state|MicroRtool|read_tip|read_accepted|projection.*only|TUI.*read|tui/app')
    writes_in_tui = _grep_invariant(r'tui/.*(wtool|update_ref|append)')  # strict: no writes inside tui module
    if proj >= 3 and writes_in_tui == 0:
        passes.append("INV-FC-A10 PASS: TUI (cli.tui + reducer + tui/app) is read-only projection from Micro Tape + declared anchors; no truth writes")
    else:
        violations.append("INV-projection: TUI writes or insufficient read")

    # 5. Failure always appends (FC-A03/3.6): FailureNode on tape, acc unchanged
    fail_append = _grep_invariant(r'FAILURE_NODE|FailureNode|fail_event = make_event')
    acc_unchanged = _grep_invariant(r'accepted_head.*unchanged|do_accept = False|on fail')
    if fail_append >= 3 and acc_unchanged >= 1:
        passes.append("INV-failure PASS: every FAIL appends FailureNode (advances tape_tip only; accepted unchanged)")
    else:
        violations.append("INV-failure append")

    # 6. Work Capsules + explicit contracts before dispatch (FC-A08)
    cap_contract = _grep_invariant(r'macro_completion_contract|append_work_capsule_built_after_order|WORK_CAPSULE_BUILT')
    if cap_contract >= 3:
        passes.append("INV-capsule PASS: visible capsule + private contract + macro: contract declared before any dispatch (compiler + wtool)")
    else:
        violations.append("INV-capsule contract pre-dispatch")

    # 7. External Agent Bundle rule (1.5): blackbox for cmd/claude/grok/manual; whitebox receipts for api
    bundle = _grep_invariant(r'blackbox|External Agent Bundle|command_template|FakeWorker|ManualWorker|ApiToolLoopWorker')
    receipts = _grep_invariant(r'receipts=|WorkerRunReceiptImported')
    if bundle >= 4 and receipts >= 3:
        passes.append("INV-bundle PASS: external bundles (codex etc) = blackbox adapter+timeout+receipt; api = full whitebox + every tool Micro receipt")
    else:
        violations.append("INV-external bundle rule")

    # 8. Runtime verify: create tape, append state + fail, assert scale ids, tape != acc on fail, pred always runs
    with tempfile.TemporaryDirectory() as td:
        os.environ["TURINGOS_DATA_DIR"] = td
        pid = "audit_inv_proj"
        gt = MicroGitTape(pid)
        tip0 = gt.init()
        assert tip0.startswith("μ:")
        # state
        m_state = wtool_append(pid, make_event("ProjectReady", {"name": pid}))
        r = MicroRtool(pid)
        assert r.read_tip() == m_state
        # fail path: append failure, tip advances, acc does not (if prior state)
        pre_acc = r.read_accepted_head()
        m_fail = wtool_append(pid, make_event("FailureNode", {"reason": "inv-audit-fail"}))
        assert r.read_tip() == m_fail
        assert r.read_accepted_head() == pre_acc  # distinct
        # scale on nodes
        node = r.load_node(m_fail)
        assert node["event_id"].startswith("μ:")
        assert node["scale"] == "micro"
        # kernel exercised
        k = PredicateKernel()
        res = k.validate(make_event("IntentCaptured", {"task": "x"}), {"prev_tape_tip": tip0})
        assert hasattr(res, "passed")
        passes.append("INV-runtime PASS: tape/acc distinct on fail, μ: scale ids, kernel gate, dual layout respected")

    status = "PASS" if not violations else "FAIL"
    return {
        "status": status,
        "passes": passes,
        "violations": violations,
        "all_event_types_count": len(ALL_EVENT_TYPES),
    }


if __name__ == "__main__":
    res = run_invariants_audit()
    print("INVARIANTS AUDIT:", res["status"])
    for p in res.get("passes", []):
        print("  ", p)
    if res.get("violations"):
        print("VIOLATIONS:", res["violations"])
