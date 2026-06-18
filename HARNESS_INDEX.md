# Harness & Skill Index — TuringOS Lite Agent Entry

**Purpose:** Single operational catalog for agents and humans. Answers: *what harness/skills exist, when to use each, what conflicts, and what acceptance gates apply.*

**Last verified:** 2026-06-18 — update date whenever entries change (`git log -1 --oneline HARNESS_INDEX.md`).

---

## Agent Entry (read in order)

```text
1. AGENTS.md              — Charter invariants + core principles (L0 constitution)
2. HARNESS_INDEX.md       — This file: pick harness, skill, script, test gate (L1 catalog)
3. Task-specific skill    — e.g. /PlanLoop (plan) or /TuringLoop (execute) (L2 executable flow)
4. Deep reference         — Charter, architecture/, HUMAN_SIMULATOR.md (L3 detail)
```

**Quick routing**

| You are doing… | Start here | Blocking acceptance |
|----------------|------------|---------------------|
| Any code change | `AGENTS.md` → `./run_test.sh` | Unit + e2e mock suite |
| TUI / Facilitator UX | + `./scripts/run_human_tui_audit.sh` | Human journey matrix (strict Pilot) |
| New feature / multi-phase work | `/PlanLoop` v1.3 (Grill-with-docs first) → user approval → `/TuringLoop` | `CONTEXT.md` + ADRs + Canonical Proposal §0 sign-off, then atom acceptance |
| Long-horizon atom/phase (approved plan) | `/TuringLoop` (`.grok/skills/turing-loop/`) | TaskCapsule acceptance_commands |
| Charter invariant change | `architecture/07-index-and-conversation-map.md` + FC-A audit | `python -m turingos.cli audit all` |
| Why was X designed this way? | `architecture/` (not this file) | — |

---

## Layer Model

| Layer | Path | Role |
|-------|------|------|
| **L0** | `AGENTS.md` | Non-negotiable invariants; thin pointer to this index |
| **L1** | `HARNESS_INDEX.md` | Full registry (this file) |
| **L2** | `.grok/skills/*/SKILL.md` | Project-scoped executable workflows |
| **L3** | Charter, `architecture/`, `tests/tui_e2e/HUMAN_SIMULATOR.md` | Rationale and deep specs |

**Related (not duplicate):** `architecture/07-index-and-conversation-map.md` maps *design conversations → code*; this file maps *agent actions → commands/skills*.

---

## Project Harness (tracked in repo)

| id | type | path | when_to_use | acceptance | conflicts_with |
|----|------|------|-------------|------------|----------------|
| `agents-md` | harness | `AGENTS.md` | Every session start; before any implementation | — | — |
| `charter` | harness | `TURINGOS_LITE_v1.0_PROJECT_CHARTER.md` | Atoms, phases, FC-A audits, schema | `python -m turingos.cli audit all` | — |
| `research` | harness | `RESEARCH_KARPATKY_SOFTWARE3_VIBE_HARNESS_SYNTHESIS.md` | Harness philosophy, loop patterns | — | — |
| `testing-manual` | harness | `TESTING_MANUAL.md` | Full system test playbook | per section | — |
| `architecture-index` | harness | `architecture/07-index-and-conversation-map.md` | Trace design rationale | — | — |
| `human-simulator` | harness | `tests/tui_e2e/HUMAN_SIMULATOR.md` | TUI UX testing rules; staging on SSH | human matrix tests | bypass patterns in tests |
| `tui-vibe-spec` | harness | `TURINGOS_LITE_TUI_VIBE_MODULE_SPEC_FOR_GROK_BUILD.md` | TUI module scope | `./scripts/run_human_tui_audit.sh` | — |

---

## Project Skills (repo: `.grok/skills/`)

| id | slash | path | triggers | when_to_use | when_not | acceptance | conflicts_with | owner |
|----|-------|------|----------|-------------|----------|------------|----------------|-------|
| `plan-loop` | `/PlanLoop` | `.grok/skills/plan-loop/SKILL.md` | `/PlanLoop`, `Activate PlanLoop v1.3`, `开始第一个 Plan`, `plan before execute` | Structured planning; Grill-with-docs (grilling + CONTEXT/ADRs); research; adversarial debate; Canonical Proposal | Single-file fix; plan already approved | User §0 sign-off + Canonical Proposal Format | `/design`, vibe planning without shipgates | project |
| `turing-loop` | `/TuringLoop` | `.grok/skills/turing-loop/SKILL.md` | `/TuringLoop`, `Activate AgenticForgeLoop v1.4`, `TuringLoop`, `loop engineering` | Long-horizon atoms/phases; TestForge (embedded); IPQC; `fresh_bp`; Reflect; Mini-Recovery | Single-file fix; no ETA; no approved plan for greenfield | TestForge shipgate + TaskCapsule acceptance (+ human audit if TUI) | `/implement` (generic), ad-hoc orchestration | project |

**References (plan-loop):**

| path | purpose |
|------|---------|
| `.grok/skills/plan-loop/CHANGELOG.md` | v1.2→v1.3 history, artifact layout, adversarial test — **read before editing PlanLoop** |
| `.grok/skills/plan-loop/references/grill-with-docs.md` | **Step 1 start** — grilling + domain modeling (`CONTEXT.md` + plan ADRs) |
| `.grok/skills/plan-loop/references/plan-capsule-template.yaml` | PlanCapsule v1.3 (`grill_with_docs`, not `grill_me`) |
| `.grok/skills/plan-loop/references/canonical-proposal-format.md` | **Mandatory** proposal output (v1.0) |
| `.grok/skills/plan-loop/references/grill-me-checklist.md` | Step 1 machine exit criteria (grill-with-docs) |
| `.grok/skills/plan-loop/references/adversarial-roles.md` | Step 3 multi-role debate |

**References (turing-loop):**

| path | purpose |
|------|---------|
| `.grok/skills/turing-loop/references/task-capsule-template.yaml` | TaskCapsule v1.4 (`test_mode`, `frontier_mode`) |
| `.grok/skills/turing-loop/references/test-forge.md` | `TestForge` embedded verification sub-tool |
| `.grok/skills/turing-loop/references/best-practice-alignment.md` | `fresh_bp` / `force_alignment` sub-tool |
| `.grok/skills/turing-loop/references/ipqc-checklist.md` | IPQC four-dimension scan |
| `.grok/skills/turing-loop/scripts/calc-ipqc-interval.sh` | IPQC interval from ETA |

See also: `.grok/skills/README.md` (per-skill one-liners).

---

## Project Agent Skills (repo: `.agents/skills/`)

Installed via `npx skills@latest add mattpocock/skills` (lockfile: `skills-lock.json`). Grok Build discovers these as project skills. **PlanLoop v1.3** inlines the relevant behavior into `.grok/skills/plan-loop/references/grill-with-docs.md`; use `.agents/` skills only when running standalone workflows outside PlanLoop.

| id | path | PlanLoop relationship |
|----|------|----------------------|
| `grill-with-docs` | `.agents/skills/grill-with-docs/SKILL.md` | Router only (7 lines); real spec = plan-loop `references/grill-with-docs.md` |
| `grilling` | `.agents/skills/grilling/SKILL.md` | Source behavior for Step 1 interview |
| `domain-modeling` | `.agents/skills/domain-modeling/SKILL.md` | Source behavior for Step 1 `CONTEXT.md` + ADRs |
| `review` | `.agents/skills/review/SKILL.md` | Standards + Spec dual-axis review (orthogonal to PlanLoop) |
| `tdd` | `.agents/skills/tdd/SKILL.md` | Test-first atoms (use with `/TuringLoop`) |

Full catalog: 34 skills under `.agents/skills/` — not all listed here; add row when a skill becomes harness-critical.

---

## Global Skills (`~/.grok/skills/` — user machine, not in repo)

Use when the task is **not** TuringOS-specific. Paths are on the developer machine.

| id | slash | triggers | when_to_use | conflicts_with |
|----|-------|----------|-------------|----------------|
| `check-work` | `/check-work` | `check work`, `verify changes`, `/check`, `/verify` | Post-implementation self-verify via subagent | TuringLoop Verifier step (pick one, not both) |
| `create-skill` | `/create-skill` | `create skill`, `/create-skill` | Author new SKILL.md | — |
| `help` | — | Grok setup, MCP, config | Platform help | — |
| `docx` / `pptx` / `xlsx` | — | `.docx`, `.pptx`, `.xlsx` tasks | Office document deliverables | — |
| `imagine` | — | image gen/edit in Grok Build | Visual assets | — |

---

## Bundled Grok Skills (`~/.grok/bundled/skills/`)

| id | slash | triggers | when_to_use | conflicts_with |
|----|-------|----------|-------------|----------------|
| `implement` | `/implement` | `implement`, `build`, `add feature`, `fix bug` | Generic implement→review→fix loop | `/TuringLoop` on turingoslite long tasks |
| `review` | `/review` | `review`, `code review`, `review PR` | Local/branch/PR review | TuringLoop Verifier; `/check-work` |
| `design` | `/design` | `design doc`, `system design`, `/design` | Design doc + PR plan DAG | Charter atom contracts (use atoms for in-repo work) |
| `execute-plan` | `/execute-plan` | `execute plan`, `run the plan` | Multi-PR DAG from design doc | `/TuringLoop` (overlapping orchestration) |
| `pr-babysit` | `/pr-babysit` | `/pr-babysit` | Monitor PR CI, reviews, merge | — |
| `remove-wall-of-text` | `/remove-wall-of-text` | `tl;dr`, `concise` | Condense prior reply | — |

---

## Oh-My-Claude Skills (`~/.claude/plugins/.../oh-my-claude/skills/`)

| id | triggers | when_to_use on turingoslite |
|----|----------|----------------------------|
| `git-commit-validator` | any commit workflow | Before `git commit` — conventional messages |
| `pr-creation` | `create PR`, `open PR` | Draft PR via `gh` (default branch: **master**) |
| `worktree` | `/worktree create` | Isolated branches → `.turingos/worktrees/<name>` |
| `verification` | `verify`, `is it done` | Pre-ship evidence check |
| `tdd` | `tdd`, `test first` | Test-first atoms |
| `debugger` | repeated failures | Systematic root-cause after 2+ failed fixes |

---

## Test Gates & Scripts

| id | type | path | when_to_use | notes |
|----|------|------|-------------|-------|
| `run-test` | test-gate | `./run_test.sh` | Every code change | 74 mock tests; includes human matrix |
| `human-tui-audit` | test-gate | `./scripts/run_human_tui_audit.sh` | TUI/Facilitator UX changes | **Blocking**; strict Pilot, no bypass |
| `cli-audit` | test-gate | `python -m turingos.cli audit all` | Invariant / flowchart checks | FC-A01–A10 |
| `audits-invariants` | script | `audits/invariants.py` | Standalone invariant audit | via CLI or direct |
| `audits-flowcharts` | script | `audits/flowcharts.py` | Flowchart coverage | via CLI or direct |
| `audits-e2e` | script | `audits/e2e.py` | E2E harness audit | via CLI or direct |
| `audits-zombie` | script | `audits/global_zombie_check.py` | No zombie nodes | charter 7.2 nodes |
| `planloop-adversarial` | test-gate | `audits/planloop_adversarial.py` | After PlanLoop skill/harness changes | 35 checks: refs, Steps 0–6 dry-run, failure gates; temp under `.cache/planloop-adversarial/` |

**Two-layer testing rule (TUI):** `./run_test.sh` green ≠ UX green. Human matrix is the UX gate. Forbidden in tests: `_facilitator_run`, `post_message(ChoiceSelected)`, direct `inp.value =` shortcuts.

---

## Trigger Conflict Matrix

| trigger family | prefer | avoid combining |
|----------------|--------|-----------------|
| Greenfield / multi-phase planning | `/PlanLoop` → approve → `/TuringLoop` | `/design`, vibe planning, direct `/TuringLoop` |
| Long turingoslite execution | `/TuringLoop` | `/implement`, `/execute-plan` |
| Post-change verify | TuringLoop Verifier **or** `/check-work` | both in same step |
| Code review | `/review` | duplicate reviewer subagent |
| Design doc only (no shipgates) | `/design` | `/PlanLoop` when TuringOS atoms needed |
| Commit | `git-commit-validator` skill | ad-hoc messages |

**Rule:** No two skills with the same primary slash command. New skills must register here before merge.

---

## Maintenance Rules

1. **New or changed project skill** → update this file + `.grok/skills/README.md` + `last_verified` commit/date.
2. **New test gate or script** → add row under Test Gates; link from relevant skill HANDOFF step.
3. **TuringLoop HANDOFF (step 8)** → include `index_updated: true|false` in TaskCapsule.
4. **Quarterly or end-of-phase** → reconcile `last_verified` against repo; run full acceptance column.
5. **Project vs global** → project skills live in `.grok/skills/` (git-tracked); global skills stay in `~/.grok/skills/` (document here, do not copy into repo).

### PR checklist (harness touch)

- [ ] `HARNESS_INDEX.md` row added/updated if skill, script, or gate changed
- [ ] `.grok/skills/README.md` synced for project skills
- [ ] `AGENTS.md` still points to this index (no duplicate long lists in AGENTS.md)
- [ ] `conflicts_with` reviewed for trigger overlap

---

## Changelog

| date | change |
|------|--------|
| 2026-06-17 | Initial index: turing-loop, test gates, global/bundled skill pointers, agent entry block |
| 2026-06-17 | turing-loop → AgenticForgeLoop v1.3: BestPractice Alignment Pass, Reflect step, TaskCapsule `frontier_mode` |
| 2026-06-17 | plan-loop v1.2: Grill Me, research, adversarial debate, Canonical Proposal Format; handoff to TuringLoop |
| 2026-06-18 | plan-loop v1.3: Grill-with-docs as mandatory Step 1 (grilling + plan CONTEXT/ADRs); PlanCapsule `grill_with_docs` |
| 2026-06-18 | `.agents/skills/` mattpocock bundle registered; `plan-loop/CHANGELOG.md`; `audits/planloop_adversarial.py` (35/35 PASS adversarial dry-run) |
| 2026-06-17 | turing-loop → v1.4: TestForge embedded in VERIFY/IPQC, Mini-Recovery, REFLECT; `test_mode` field |