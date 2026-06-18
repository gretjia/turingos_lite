# Project Skills — TuringOS Lite

Executable agent workflows scoped to this repository. **Registry of record:** [`HARNESS_INDEX.md`](../../HARNESS_INDEX.md).

Read `AGENTS.md` first, then pick a skill below.

| skill | slash | path | one-liner |
|-------|-------|------|-----------|
| **plan-loop** | `/PlanLoop` | [`plan-loop/SKILL.md`](plan-loop/SKILL.md) | PlanLoop v1.3: Grill-with-docs → research → debate → Canonical Proposal → approve → handoff ([CHANGELOG](plan-loop/CHANGELOG.md)) |
| **turing-loop** | `/TuringLoop` | [`turing-loop/SKILL.md`](turing-loop/SKILL.md) | AgenticForgeLoop v1.4: 8-step loop, TestForge, `fresh_bp`, IPQC, Reflect, Mini-Recovery, tier-3 |

**Pipeline:** `/PlanLoop` (plan + §0 sign-off) → `/TuringLoop` (execute atoms).

**PlanLoop v1.3 (2026-06-18):** Step 1 is mandatory Grill-with-docs — interview + `plans/<id>/CONTEXT.md` + `adr/`. Optional external skills in `.agents/skills/` (`grilling`, `domain-modeling`, `grill-with-docs`); canonical spec is `plan-loop/references/grill-with-docs.md`. Verify harness: `python3 audits/planloop_adversarial.py`.

## Add a skill

1. Create `turing-loop/` sibling: `<name>/SKILL.md` (+ optional `references/`, `scripts/`).
2. Frontmatter: `name`, `description` (triggers), `metadata.slash-command` if applicable.
3. Update `HARNESS_INDEX.md` and this table.
4. HANDOFF must set `index_updated: true`.

## Not here

- **Global skills** (`~/.grok/skills/`): check-work, docx, pptx, … — listed in `HARNESS_INDEX.md`.
- **Bundled Grok** (`~/.grok/bundled/skills/`): implement, review, design, … — listed in `HARNESS_INDEX.md`.
- **Design history** (`architecture/`): why we built X — not executable skills.