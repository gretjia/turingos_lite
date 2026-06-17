# Project Skills — TuringOS Lite

Executable agent workflows scoped to this repository. **Registry of record:** [`HARNESS_INDEX.md`](../../HARNESS_INDEX.md).

Read `AGENTS.md` first, then pick a skill below.

| skill | slash | path | one-liner |
|-------|-------|------|-----------|
| **turing-loop** | `/TuringLoop` | [`turing-loop/SKILL.md`](turing-loop/SKILL.md) | AgenticForgeLoop v1.2: long-horizon atoms, IPQC, Mini-Recovery, tier-3 autonomy |

## Add a skill

1. Create `turing-loop/` sibling: `<name>/SKILL.md` (+ optional `references/`, `scripts/`).
2. Frontmatter: `name`, `description` (triggers), `metadata.slash-command` if applicable.
3. Update `HARNESS_INDEX.md` and this table.
4. HANDOFF must set `index_updated: true`.

## Not here

- **Global skills** (`~/.grok/skills/`): check-work, docx, pptx, … — listed in `HARNESS_INDEX.md`.
- **Bundled Grok** (`~/.grok/bundled/skills/`): implement, review, design, … — listed in `HARNESS_INDEX.md`.
- **Design history** (`architecture/`): why we built X — not executable skills.