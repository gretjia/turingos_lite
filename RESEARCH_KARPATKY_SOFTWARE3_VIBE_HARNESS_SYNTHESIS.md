# Research Synthesis: Karpathy Software 3.0 + Vibe Coding + Harness Best Practices
## For TuringOS Lite (as of 2026-06-16)

**Sources**:
- Subagent 1 (Karpathy focus, ID 019ed207-0a23-7023-b873-35addf9ca553): Completed, 78s, 5 tool calls.
- Subagent 2 (Harness architectures survey, ID 019ed207-0a23-7023-b873-35b64d6ec785): Completed, 104s, 10 tool calls.
- Parallel web/X searches, page browses (latent.space transcript, etc.), sequential-thinking at depth (multiple high-total thoughts with revisions).
- Direct charter reading (full prompt_2.txt + saved TURINGOS_LITE_v1.0_PROJECT_CHARTER.md).

**Directive followed**: Research best practices of the most up-to-date harnesses *before* making any plan. Used max thinking level + multi-agents (parallel spawns). Charter saved for recursive audit.

---

## 1. Karpathy Software 3.0 + Vibe Coding + Coding Principles (from Subagent 1 + corroborating sources)

**Software 3.0**:
- Prompts as programs that program the LLM. Natural language (English) as the programming interface.
- Context window = RAM (the program/state you pack and manipulate).
- Model weights = CPU (the interpreter/substrate).
- Software 3.0 is eating 1.0 (explicit rules) and 2.0 (learned weights). Patchwork coexistence, but massive rewriting ahead.
- LLMs as utilities/fabs/OSes (or time-shared mainframes). Tool calls ≈ syscalls. "Build for agents" (new consumer of digital information alongside humans + APIs).
- LLM "psychology" to design for: jagged intelligence + anterograde amnesia (no persistent consolidation beyond context; needs external scratchpads, system-prompt learning, durable memory).

**Vibe coding** (coined Feb 2025 by Karpathy; now memetic with Wikipedia entry; evolved to "agentic engineering"):
- "Fully give in to the vibes, embrace exponentials, and forget that the code even exists."
- See stuff, say stuff (declarative), run stuff, copy-paste errors raw, Accept All, let it loop.
- Human role: manifestor/orchestrator/curator/verifier (not line-by-line coder).
- Expansion (do more previously uneconomical things) often > pure speedup.
- Real example (MenuGen): exhilarating locally; painful for production infra not designed for agents.
- 2026 evolution: Professional work = agentic engineering with oversight, better loops, partial autonomy. "Give it success criteria and watch it go."

**Karpathy coding/arch style + 4 principles** (from his 2026 notes on heavy agent use; viral in CLAUDE.md files):
1. Think Before Coding: Don't assume. Don't hide confusion. Surface tradeoffs. (State assumptions, present pros/cons, push back.)
2. Simplicity First: Minimum code that solves the problem. Nothing speculative.
3. Surgical Changes: Touch only what you must. Match existing style. No orthogonal "improvements."
4. Goal-Driven Execution: Define success criteria. Loop until verified. (This is where the leverage/"feel the AGI" magic lives — tenacity via loops.)

**Harness implications** (synthesized):
- Treat durable external memory (Git tapes, playbooks, event logs) as the "context/RAM" that survives amnesia.
- Projection-only views + declarative intent over chat walls.
- Explicit contracts/predicates as success criteria.
- Loops as the central engineering work (failure memory, broadcast, replay, grind until predicate).
- Blackbox workers + whitebox control plane for safe "forget the code" while retaining sovereignty.
- Role-specialized multi-agents orchestrated by task type.
- Surgical, goal-driven atoms with acceptance commands.

---

## 2. Latest Agent Harness Architectures (2025-2026) — from Subagent 2

**Core insight across harnesses**: "Agent = Model + Harness". The harness (constraints, loops, context architecture, persistent memory, role specialization, projection, typed contracts, behavioral rules, isolation) often matters *more* than the base model for reliability at scale. "Harness engineering" and "loop engineering" are explicit disciplines.

**Leading examples and convergent patterns** (Grok Build, Claude Code/Anthropic, Cursor, Aider, OpenDevin/SWE-agent/OpenHands, etc.):

- **Master loops + feedback**:
  - ReAct base extended with Plan-Execute-Verify (PEV), reflexion, self-critique.
  - Hooks (lifecycle events: Pre/PostToolUse, SessionStart, etc.) for deterministic control/quality gates (auto-lint, test injection, doom-loop detection).
  - Long-running "grind" loops via skills/hooks (iterate until "tests pass" or scratchpad DONE predicate).
  - Failure append + broadcast + reflexion (quantize failures, update memory/playbook, feed back to next capsule/iteration).

- **Multi-agent specialization + orchestration**:
  - Role-based sub-agents (explorer/read-only/fast, planner, builder, reviewer, security-expert, debugger, SRE).
  - Parallel execution in one turn (worktrees, isolated envs/VMs, context firewalls).
  - Parent orchestrator delegates + compresses results (1-msg summary back).
  - Teams/workflows/hierarchical; cross-verification/synthesis.
  - Cheap/fast models for exploration; strong models for planning/verification.
  - Coordinator/supervisor patterns.

- **Projection / read-only views of truth**:
  - Plan mode (read-only research + numbered editable plan MD before any edits).
  - Sidebars, Agents Windows, panes for parallel sessions/capsules/state.
  - Derived views (memory files, event logs, task trackers, beads) preferred over internal writes.
  - TUI/projection reads derived state; never mutates core truth.

- **Git (or tape/chain) as memory/audit/SoT for agency**:
  - Every significant change → atomic commit.
  - Git worktrees for parallel/isolated speculative work (prevents context contamination; clean separation).
  - Event logs / session streams / durable append-only logs outside pure context window (recoverable, sliceable, auditable).
  - Dual-memory patterns: code world (user Git) vs. agency world (persistent logs/tapes/playbooks).
  - Replay from logs/tapes + external state (progress.txt, PRDs, scratchpads) for recovery/resume.
  - Aider: git-native everything. OpenHands/SWE: event-stream + sandbox + git snapshots.

- **Blackbox external agents vs. whitebox adapters/tool servers**:
  - External bundles (Claude CLI, Codex Exec, Grok Build, manual) treated as compound blackbox (model + internal tools opaque; provenance PARTIAL/OUTSIDE by default).
  - Sovereignty via whitebox adapter layer: workspace sandbox, env/credential scope, timeout/process control, receipt normalizer, observer.
  - Native/API workers get full whitebox tools (read/grep/patch/run) with *mandatory* receipts on every call.
  - MCP as standardized (often proxied) tool server interface.
  - "Managed agents" meta-pattern: decouple brain (orchestrator + loop) from hands (sandboxes); cattle not pets.

- **Typed events/contracts on boundaries + context minimization**:
  - Typed Micro events / event streams / receipts on every boundary (no naked "then system updates state").
  - Work capsules / visible summaries + private contracts / shields (limits what worker sees; progressive disclosure).
  - On-demand skills (vs. always-on rules/CLAUDE.md).
  - Context architecture: tiered/progressive, repo maps (tree-sitter + ranking for LM-friendly structural view, not full files), ACI (Agent-Computer Interface: LM-centric commands with summaries/guards instead of human UIs).
  - Compaction with recoverability; context firewalls between sub-agents.

- **Behavioral constraints + reusable behaviors**:
  - CLAUDE.md / AGENTS.md / rules (always-on, hierarchical, git-checkin friendly; loaded at session start; conventions, style, expectations, "from now on always X").
  - Skills (SKILL.md bundles: description always visible; content on-demand; encode repeatable workflows/loops).
  - Hooks for deterministic law (not model-dependent).

**Evidence alignment**: Official docs, engineering posts (Anthropic managed agents, Cursor best practices, Aider repomap), papers (SWE-agent ACI), 2026 comparisons, X/community discourse on "harness engineering."

**Anti-patterns** (recurring warnings):
- Chat walls / long polluted sessions (noise, repeated mistakes, context anxiety) → use clean restarts + external durable state.
- Single source of truth (mixing code + agency in one repo/chat/SQLite/JSONL) → dual tapes or explicit separation.
- Statistical "approved" or external signals as gate ("Claude approved", "CI green therefore accepted") → verifiable predicates/contracts + human/Micro approval separate from evidence.
- Hidden state / lack of projection/audit → explicit logs, projection views, append-only truth.
- Overstuffing context, doom loops without detection, irreversible compaction, tight model coupling.

---

## 3. Consolidated Alignment with TuringOS Lite Charter

The charter is already a **near-ideal, forward-aligned sovereign realization** of 2026 harness engineering + Karpathy Software 3.0 principles:

- **Micro Git ChainTape** = durable agency memory / typed event log / "context window as program" (best practice for audit, replay, determinism, countering amnesia). Independent of Macro code Git. "Same Git technology. Two independent tapes. Macro remembers code. Micro remembers agency."
- **Projection-only TUI** = visibility layer without mutating truth (panes for state/capsules/evidence/failures/next sovereign action + hotkeys; "ugly, fast, and calm"; no chat walls, no magic "verified").
- **Micro Predicate Kernel + Failure Memory + Broadcast + Shield** = master control loop + feedback + context minimization + verifiable gates (not statistical signals).
- **Work Capsules + macro completion contracts + Tool Predicate** = explicit typed contracts on boundaries; success criteria declared *before* dispatch.
- **Blackbox external bundles + whitebox adapters/toolserver/observer + mandatory receipts** = safe use of compound middle blackboxes while retaining sovereignty and provenance tracking.
- **Typed Micro events on every cross-boundary** (FC-A01–FC-A10 audit checklist) + scale language + tape_tip vs. accepted_head distinction = explicit events/contracts + constraints layer.
- **Replay from tape + derived projection only** = recoverability and audit from source of truth.
- **Atom/phase/module cascade with worker-friendly contracts** (allowed/forbidden files, acceptance commands like pytest, output format with status/changed/risks/next atom) = surgical, goal-driven units for low-thinking Worker AI execution.
- **Multi-agent orchestration by task type**: Clear roles (Meta proposer, Shield compiler, Predicate kernel, Broadcast reducer, specialized adapters, Human approver, Macro Observer) + worktree isolation. Matches sub-agent specialization + parallel + compression patterns.
- **Loops as the central work**: Failure feedback, predicate verification, broadcast, replay ritual, grind via hooks/skills equivalents. Directly embodies "embrace loops" and "tenacity via success criteria."

Non-negotiables in the charter (no single-repo dual refs, no JSONL/SQLite as truth, no hidden predicates in capsules, no Macro as Micro, explicit failure appends, contracts before irreversible actions, etc.) are exactly the stable invariants that leading harnesses converge on for reliability and sovereignty.

**High alignment verdict**: The charter reads like distilled best-practice harness engineering applied to *agency sovereignty* rather than just code generation. It turns Karpathy's "vibes + agentic engineering" + 2026 patterns (loops, multi-agents, projection, Git-memory, typed boundaries, context min) into a local, auditable, replayable system.

---

## 4. Concrete Recommendations (Integrated from Both Subagents)

- **For atoms/phases**: Design as role-specialized, capsule-isolated units with embedded loops (explorer → planner → executor → verifier). Use sequential-thinking MCP inside kernel/Meta/Broadcast for explicit "think before" depth (structured thoughts, revisions, hypothesis verification — Karpathy-style thoroughness).
- **Projection TUI**: Strictly read-only per FC-A10. Add parallel capsule views, typed event timelines, replay sliders/diffs, predicate status. Hotkeys dispatch to daemon (which runs predicates + wtool appends).
- **Micro Predicate as the sovereign kernel**: Validates *agency* transitions (contracts, receipts, shields, authorizations, failure handling). Integrates hooks (deterministic) + receipts on every boundary. For external blackboxes: adapter layer enforces receipts + partial provenance.
- **Adopt proven primitives** (without violating charter):
  - Hierarchical AGENTS.md / behavioral constraints (always-on + git-checkin).
  - Skills for reusable atom/phase loop bundles (on-demand).
  - Hooks for control/quality at dispatch/observe/approve boundaries.
  - Git worktrees (already planned for Macro) + repo-map/ACI-style minimization for whitebox tools.
  - MCP for standardized external tool servers.
  - Context minimization via capsules (visible + private/shield) + sub-agent compression + recoverable compaction.
  - Persistent memory: Micro Tape (primary agency chain) + derived playbooks/files (reflect/curate failures).
- **Multi-agent orchestration for phases**: Parent orchestrator manages delegation (sub-capsules in isolated worktrees), result compression, cross-verification. Specialized roles per atom type. "Cattle not pets" — restartable via replay + external state.
- **Loops emphasis**: Failure append + broadcast + shield update as core reflexion loop. Predicate gates at every transition. Replay for recovery. Long-running grind via deterministic mechanisms until verifiable predicates met.
- **Implementation hygiene**: Python per charter (Typer/Textual/Pydantic/Git plumbing). Start with P0 atoms for boot/new/adopt/intent/capsule/dispatch/observe/approve/reject/replay/tui. Test every diagram/code against FC-A checklist and charter audit prompts.

---

## 5. Anti-Patterns to Strictly Avoid (Charter + Research Convergence)

- Chat walls / long polluted sessions.
- Single source of truth (code + agency mixed).
- Statistical "approved" or external signals as Micro gates.
- Hidden state / lack of projection/audit.
- Overstuffing context, unrecoverable compaction, doom loops without detection, irreversible actions without prior authorization/contracts.
- Treating external agents as fully sovereign without whitebox adapter + receipts.

---

**Conclusion**:
Both subagents confirm that TuringOS Lite's architecture (as chartered) is already one of the cleanest, most forward-aligned expressions of Software 3.0 + 2026 harness engineering for a *sovereign, local, agency-focused* system. The dual-tape + Micro Predicate + projection TUI + capsules/shields + typed events + failure loops + atom cascade provide a stable foundation on top of (or orchestrating) blackbox execution engines.

Research phase is now fully complete (two subagents + sequential synthesis + external sources). Charter and this integrated research file are saved locally for recursive audit.

No implementation plan has been created yet.

**Next steps (user decision)**:
- Review the two research files + charter.
- Ready to move to high-level plan / strategy phase (using your module/phase/atom 3-cascade + multi-agent orchestration to finish phases/atoms in one go, with solid role design, management, and loops designed per this research)?
- Or continue research (e.g., resume a subagent for deeper dive on a specific harness, more sequential-thinking, specific atom prototyping via multi-agents)?
- Specific question or focus area?

All findings emphasize staying true to the charter's non-negotiables while layering proven patterns for loops, multi-agents, and projection.

(Full raw subagent outputs retrievable via resume_from on the IDs above.)