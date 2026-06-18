# PlanLoop Changelog & Agent Guide

**For future agents:** read this before modifying PlanLoop or its references. Registry of record remains [`HARNESS_INDEX.md`](../../../HARNESS_INDEX.md).

---

## v1.3 — 2026-06-18 (current)

### What changed (v1.2 → v1.3)

| Area | v1.2 | v1.3 |
|------|------|------|
| **Step 1** | Grill Me (intent only) | **Grill-with-docs** — grilling + inline domain modeling |
| **PlanCapsule field** | `grill_me` | `grill_with_docs` (+ `context_path`, `adrs`) |
| **Artifacts** | Proposal only | `plans/<plan_id>/CONTEXT.md` + `plans/<plan_id>/adr/*.md` |
| **External alignment** | Socratic checklist | Matt Pocock `/grilling` + `/domain-modeling` (via `.agents/skills/`) |
| **Handoff** | `proposal_path` | + `context_path`, `adrs` for `/TuringLoop` |

### Six-step flow (locked)

```text
0 用户初始输入
1 Grill-with-docs     ← mandatory start; one question at a time
2 调研 (agent self-managed)
3 思辨对抗 (Advocate / Skeptic / Minimalist)
4 汇总 → Canonical Proposal Format v1.0
5 用户批准 (+ re-Grill on rejection → back to Step 2)
6 Handoff → /TuringLoop
```

### New / updated files

| File | Role |
|------|------|
| `SKILL.md` | v1.3 orchestrator spec |
| `references/grill-with-docs.md` | **Canonical Step 1** — grilling rules, CONTEXT/ADR layout, machine exit |
| `references/grill-me-checklist.md` | Step 1 exit criteria (`grill_with_docs.complete`) |
| `references/plan-capsule-template.yaml` | PlanCapsule v1.3 |
| `references/adversarial-roles.md` | Step 3 (renumbered from Step 4) |
| `references/canonical-proposal-format.md` | Step 4 output (renumbered from Step 5) |

### Plan artifact layout (default)

```text
plans/PL-YYYYMMDD-slug.md          # Canonical Proposal
plans/PL-YYYYMMDD-slug/
├── CONTEXT.md                     # plan-scoped ubiquitous language (glossary only)
└── adr/
    └── 0001-<slug>.md             # major trade-offs during grill
```

On **approval**, promote cross-cutting terms/ADRs to `docs/adr/` or `architecture/` only if user agrees.

### External skills (optional, same behavior)

Installed via `npx skills@latest add mattpocock/skills` → `.agents/skills/` (see `skills-lock.json`):

| Skill | PlanLoop use |
|-------|----------------|
| `grill-with-docs` | Router → grilling + domain-modeling |
| `grilling` | One-question interview; recommended answers |
| `domain-modeling` | CONTEXT.md + ADR formats |

**Rule:** PlanLoop Step 1 follows **this repo's** `references/grill-with-docs.md`, not the 7-line router in `.agents/skills/grill-with-docs/SKILL.md`.

### Machine exit gates (Step 1)

Set `grill_with_docs.complete: true` only when ALL hold:

- Falsifiable `problem_statement`, concrete `desired_final_state`
- Non-empty `out_of_scope`, measurable `success_metrics`
- User constraints acknowledged; `open_questions` empty
- `CONTEXT.md` exists under `plan_dir`; ambiguous terms defined there
- Charter invariants acknowledged (dual tapes, predicate gate, projection TUI, capsules)

### Adversarial verification (2026-06-18)

Dry-run in isolated worktree `.turingos/worktrees/planloop-adversarial-test` (cleaned up after test).

**Result:** 35/35 PASS — structural integrity, happy-path Steps 0–6, failure gates, mermaid order.

**Re-run anytime:**

```bash
python3 audits/planloop_adversarial.py
```

**Gates tested:**

- Skip grill / empty problem / open questions → block advance past Step 1
- Handoff without `context_path` → invalid
- Rejection fields (`user_objections`, `re_grill_rounds`) present in template
- SKILL forbids implementation code before user approval

### Migration notes for agents

- Do **not** reintroduce `grill_me` in PlanCapsule — use `grill_with_docs`
- Do **not** renumber steps without updating all six reference files + `HARNESS_INDEX.md`
- Greenfield planning: `/PlanLoop` before `/TuringLoop`; TuringLoop consumes `CONTEXT.md` terminology
- Updating PlanLoop → update `HARNESS_INDEX.md`, `.grok/skills/README.md`, and this CHANGELOG

---

## v1.2 — 2026-06-17

- Grill Me (Step 2), research, adversarial debate, Canonical Proposal Format
- Handoff to AgenticForgeLoop / TuringLoop
- PlanCapsule `grill_me` field (superseded in v1.3)