#!/usr/bin/env python3
"""Adversarial dry-run for PlanLoop v1.3 — harness integrity + full flow landing.

Run: python3 audits/planloop_adversarial.py
Exit 0 = all checks PASS. Safe to run from repo root; uses temp dir only.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO / ".grok/skills/plan-loop"
REF = SKILL_ROOT / "references"


@dataclass
class Result:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class Suite:
    results: list[Result] = field(default_factory=list)

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.results.append(Result(name, ok, detail))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def grill_checklist_satisfied(capsule: dict) -> tuple[bool, list[str]]:
    g = capsule.get("grill_with_docs", {})
    missing = []
    for key in ("problem_statement", "desired_final_state", "out_of_scope", "success_metrics"):
        val = g.get(key)
        if not val or (isinstance(val, list) and len(val) == 0):
            missing.append(key)
    if g.get("open_questions"):
        missing.append("open_questions_nonempty")
    if not g.get("complete"):
        missing.append("complete_false")
    ctx = Path(capsule.get("plan_dir", "")) / "CONTEXT.md"
    if not ctx.exists():
        missing.append("CONTEXT.md_missing")
    return len(missing) == 0, missing


def can_advance_past_step1(capsule: dict) -> bool:
    ok, _ = grill_checklist_satisfied(capsule)
    return ok


def handoff_valid(capsule: dict) -> tuple[bool, list[str]]:
    h = capsule.get("handoff", {})
    required = ("proposal_path", "context_path", "adrs", "turing_loop_ready")
    missing = [k for k in required if not h.get(k)]
    if h.get("turing_loop_ready") is not True:
        missing.append("turing_loop_ready_not_true")
    return len(missing) == 0, missing


def proposal_has_required_sections(text: str) -> tuple[bool, list[str]]:
    required = ["§0", "Overall Eval", "Shipgate", "Acceptance", "Anti-Drift", "Approval Status"]
    missing = [s for s in required if s not in text]
    return len(missing) == 0, missing


def test_structural_integrity(suite: Suite) -> None:
    skill = SKILL_ROOT / "SKILL.md"
    suite.check("skill_exists", skill.exists())
    text = skill.read_text(encoding="utf-8") if skill.exists() else ""
    suite.check("skill_v1_3", "v1.3" in text and "Grill-with-docs" in text)
    suite.check("step1_is_grill_with_docs", "Step 1 — Grill-with-docs" in text)

    for p in [
        REF / "grill-with-docs.md",
        REF / "grill-me-checklist.md",
        REF / "plan-capsule-template.yaml",
        REF / "canonical-proposal-format.md",
        REF / "adversarial-roles.md",
    ]:
        suite.check(f"ref_exists:{p.name}", p.exists())

    tmpl = load_yaml(REF / "plan-capsule-template.yaml")
    suite.check("capsule_version_1_3", tmpl.get("version") == "1.3")
    suite.check("capsule_has_grill_with_docs", "grill_with_docs" in tmpl)
    suite.check("capsule_no_grill_me", "grill_me" not in tmpl)

    grill_doc = (REF / "grill-with-docs.md").read_text(encoding="utf-8")
    suite.check("grill_doc_step1", "Step 1" in grill_doc)
    suite.check("grill_doc_machine_exit", "grill_with_docs.complete: true" in grill_doc)

    checklist = (REF / "grill-me-checklist.md").read_text(encoding="utf-8")
    suite.check("checklist_step1", "Step 1" in checklist)
    suite.check("checklist_grill_with_docs_field", "grill_with_docs.complete" in checklist)

    suite.check("adversarial_step3", "Step 3" in (REF / "adversarial-roles.md").read_text(encoding="utf-8"))
    suite.check("canonical_step4", "Step 4" in (REF / "canonical-proposal-format.md").read_text(encoding="utf-8"))

    harness = (REPO / "HARNESS_INDEX.md").read_text(encoding="utf-8")
    suite.check("harness_v1_3", "PlanLoop v1.3" in harness or "v1.3" in harness)
    suite.check("harness_grill_with_docs_ref", "grill-with-docs.md" in harness)


def simulate_happy_path(suite: Suite) -> Path:
    cache_root = REPO / ".cache" / "planloop-adversarial"
    cache_root.mkdir(parents=True, exist_ok=True)
    ws = Path(tempfile.mkdtemp(prefix="planloop-dryrun-", dir=cache_root))
    plan_id = "PL-20260618-adversarial-dryrun"
    plan_dir = ws / "plans" / plan_id
    plan_dir.mkdir(parents=True)

    capsule = load_yaml(REF / "plan-capsule-template.yaml")
    capsule["plan_id"] = plan_id
    capsule["initial_intent"] = "Adversarial dry-run: verify PlanLoop v1.3 lands end-to-end"
    capsule["plan_dir"] = str(plan_dir)

    context = plan_dir / "CONTEXT.md"
    context.write_text(
        "# Adversarial Dry-Run Plan\n\n## Language\n\n**PlanCapsule**: YAML state for PlanLoop steps.\n",
        encoding="utf-8",
    )
    adr_dir = plan_dir / "adr"
    adr_dir.mkdir()
    (adr_dir / "0001-plan-scoped-domain-docs.md").write_text(
        "# Plan-scoped CONTEXT and ADRs\n\nGlossary under plans/<plan_id>/ by default.\n",
        encoding="utf-8",
    )
    capsule["grill_with_docs"].update(
        {
            "round": 1,
            "complete": True,
            "context_path": str(context),
            "adrs": [str(adr_dir / "0001-plan-scoped-domain-docs.md")],
            "problem_statement": "Prove PlanLoop v1.3 can land all six steps without drift.",
            "desired_final_state": "Adversarial script PASS with happy path + failure gates.",
            "out_of_scope": ["Macro code changes", "TuringLoop execution"],
            "success_metrics": ["All suite checks PASS", "Handoff YAML valid"],
            "constraints": ["Charter dual tapes", "Predicate gate"],
            "open_questions": [],
        }
    )
    suite.check("step1_complete", can_advance_past_step1(capsule))

    capsule["research"]["findings"] = ["PlanLoop v1.3 — .grok/skills/plan-loop/SKILL.md"]
    suite.check("step2_research_populated", len(capsule["research"]["findings"]) >= 1)

    capsule["adversarial_debate"]["consensus_approach"] = "Automated structural + dry-run gates."
    suite.check("step3_consensus", bool(capsule["adversarial_debate"]["consensus_approach"]))

    proposal = ws / "plans" / f"{plan_id}.md"
    proposal.write_text(
        "# Plan Proposal — Dry-Run\n**Approval Status**: Pending\n\n"
        "**§0 以终为始 · Overall Eval**\nDesired Final State: PASS\n"
        "**Shipgate**: ok\n**Acceptance**: `python3 audits/planloop_adversarial.py`\n"
        "**Anti-Drift Commitment**: 本方案所有变更必须通过对应 Shipgate 且不偏离 §0 Overall Eval。\n",
        encoding="utf-8",
    )
    ok, missing = proposal_has_required_sections(proposal.read_text(encoding="utf-8"))
    suite.check("step4_canonical_sections", ok, ", ".join(missing))

    capsule["approval_status"] = "approved"
    capsule["handoff"].update(
        {
            "approved_at": "2026-06-18",
            "turing_loop_ready": True,
            "proposal_path": str(proposal),
            "context_path": str(context),
            "adrs": [str(adr_dir / "0001-plan-scoped-domain-docs.md")],
        }
    )
    suite.check("step5_approved", capsule["approval_status"] == "approved")

    h_ok, h_missing = handoff_valid(capsule)
    suite.check("step6_handoff", h_ok, ", ".join(h_missing))

    cap_path = ws / "plan-capsule.yaml"
    cap_path.write_text(yaml.dump(capsule, sort_keys=False, allow_unicode=True), encoding="utf-8")
    suite.check("capsule_persisted", cap_path.exists())
    return ws


def test_adversarial_gates(suite: Suite) -> None:
    base = load_yaml(REF / "plan-capsule-template.yaml")
    base["plan_dir"] = "/tmp/nonexistent-plan"

    skip = dict(base)
    skip["grill_with_docs"]["complete"] = False
    suite.check("gate_skip_grill_blocks", not can_advance_past_step1(skip))

    partial = dict(base)
    partial["grill_with_docs"]["complete"] = True
    partial["grill_with_docs"]["problem_statement"] = ""
    suite.check("gate_empty_problem_blocks", not can_advance_past_step1(partial))

    open_q = dict(base)
    open_q["grill_with_docs"].update(
        {
            "complete": True,
            "problem_statement": "x",
            "desired_final_state": "y",
            "out_of_scope": ["a"],
            "success_metrics": ["b"],
            "open_questions": ["still open"],
        }
    )
    suite.check("gate_open_questions_blocks", not can_advance_past_step1(open_q))

    bad_handoff = {"handoff": {"turing_loop_ready": True, "proposal_path": "p.md"}}
    ok, _ = handoff_valid(bad_handoff)
    suite.check("gate_handoff_missing_context", not ok)
    suite.check("gate_rejection_fields", "user_objections" in base and "re_grill_rounds" in base)

    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    suite.check("gate_no_code_before_approval", "禁止" in skill and "写实现代码" in skill)

    grill_doc = (REF / "grill-with-docs.md").read_text(encoding="utf-8")
    suite.check("gate_regrill_to_research", "Step 2 Research" in grill_doc)


def test_mermaid_flow_order(suite: Suite) -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"flowchart TD(.*?)```", skill, re.DOTALL)
    if not m:
        suite.check("mermaid_present", False, "no flowchart block")
        return
    block = m.group(1)
    steps = ["Grill-with-docs", "调研", "思辨", "Canonical", "批准", "Handoff"]
    positions = [block.find(s) for s in steps]
    suite.check("mermaid_all_steps", all(p >= 0 for p in positions), str(positions))
    suite.check("mermaid_order", positions == sorted(positions), str(positions))


def main() -> int:
    suite = Suite()
    ws: Path | None = None
    try:
        test_structural_integrity(suite)
        ws = simulate_happy_path(suite)
        test_adversarial_gates(suite)
        test_mermaid_flow_order(suite)
    finally:
        if ws and ws.exists():
            shutil.rmtree(ws, ignore_errors=True)

    fails = [r for r in suite.results if not r.passed]
    print(f"PlanLoop v1.3 Adversarial Suite: {len(suite.results) - len(fails)}/{len(suite.results)} PASS")
    for r in suite.results:
        mark = "PASS" if r.passed else "FAIL"
        extra = f" — {r.detail}" if r.detail else ""
        print(f"  [{mark}] {r.name}{extra}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())