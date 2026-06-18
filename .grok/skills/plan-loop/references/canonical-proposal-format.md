# Canonical Proposal Format v1.0

**Mandatory output** of PlanLoop Step 4 (汇总). Copy this skeleton; fill every section.

```markdown
# Plan Proposal — [Task Name] v1.2
**Approval Status**: Pending

**§0 以终为始 · Overall Eval（必须先定义，用户必须确认）**
Desired Final State: ...
Success Metrics: ...
Global Verification Plan:
- E2E Certification: ...
- Shipgates Summary: ...
- Audit Gates: ...
**User Sign-off**: I approve the End State [ ] Yes / [ ] No + comments

## Module [1] — [Name]
**Shipgate**: ...

### Phase [X] — [Name]
**Shipgate**: ...

#### Atom [X-Y-Z] — [Name]
**Shipgate**: ...
**Acceptance**: ...

## Module [2] — [Name]
...

**Anti-Drift Commitment**: 本方案所有变更必须通过对应 Shipgate 且不偏离 §0 Overall Eval。
**Next Action**: 等待用户批准或具体异议。
```

## Field rules

| Field | Rule |
|-------|------|
| **§0 Overall Eval** | Written **before** modules/phases/atoms. User must sign off before execution. |
| **Shipgate** | Per-level gate: predicate or command that must PASS before proceeding deeper or shipping. |
| **Acceptance** | Atom-level only: concrete `acceptance_commands` (shell-ready). |
| **Approval Status** | `Pending` → `Approved` (with date) or `Rejected` (with objections). |

## TuringOS Lite bindings (when plan targets this repo)

- Atom acceptance should reference `./run_test.sh`, `./scripts/run_human_tui_audit.sh` (TUI), `python -m turingos.cli audit all` (invariants) as appropriate.
- Scale language in shipgates: μ:, macro:git:, macro:pr: — never vague "accepted".
- TUI work: human journey matrix is UX shipgate (no bypass).
- Execution handoff: approved plan → `/TuringLoop` with TaskCapsule derived from atoms.

## Approval block (after user says Yes)

```markdown
**Approval Status**: Approved — [YYYY-MM-DD]
**User Sign-off**: I approve the End State [x] Yes
**Handoff**: Activate AgenticForgeLoop v1.4 / TuringLoop with atoms from this proposal.
```