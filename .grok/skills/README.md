# Project Skills — TuringOS Lite

Executable agent workflows scoped to this repository. **Registry of record:** [`HARNESS_INDEX.md`](../../HARNESS_INDEX.md).

Read `AGENTS.md` first, then pick a skill below.

| skill | slash | path | one-liner |
|-------|-------|------|-----------|
| **plan-loop** | `/PlanLoop` | [`plan-loop/SKILL.md`](plan-loop/SKILL.md) | PlanLoop v1.2: Grill Me → research → debate → Canonical Proposal → approve → handoff |
| **turing-loop** | `/TuringLoop` | [`turing-loop/SKILL.md`](turing-loop/SKILL.md) | AgenticForgeLoop v1.3: 8-step loop, `fresh_bp` alignment, IPQC, Reflect, Mini-Recovery, tier-3 |

**Pipeline:** `/PlanLoop` (plan + §0 sign-off) → `/TuringLoop` (execute atoms).

## Add a skill

1. Create `turing-loop/` sibling: `<name>/SKILL.md` (+ optional `references/`, `scripts/`).
2. Frontmatter: `name`, `description` (triggers), `metadata.slash-command` if applicable.
3. Update `HARNESS_INDEX.md` and this table.
4. HANDOFF must set `index_updated: true`.

## Not here

- **Global skills** (`~/.grok/skills/`): check-work, docx, pptx, … — listed in `HARNESS_INDEX.md`.
- **Bundled Grok** (`~/.grok/bundled/skills/`): implement, review, design, … — listed in `HARNESS_INDEX.md`.
- **Design history** (`architecture/`): why we built X — not executable skills.