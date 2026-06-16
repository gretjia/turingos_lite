# AGENTS.md - TuringOS Lite Development Harness

**Core Principles (Karpathy Software 3.0 + 4 Principles from research)**

1. **Think Before Coding**  
   Don't assume. Don't hide confusion. Surface tradeoffs explicitly before any implementation. For any atom or change, first state assumptions, present pros/cons or alternative approaches.

2. **Simplicity First**  
   Minimum that solves the problem. No speculative features, abstractions, or "flexibility". If it can be 50 lines instead of 200, it must be.

3. **Surgical Changes**  
   Touch *only* what the request/atom requires. Match existing style. No orthogonal refactors, comment "improvements", or touching unrelated code. Every changed line must trace directly to the atom/task.

4. **Goal-Driven Execution**  
   Define success criteria *first* (acceptance commands, predicates, tests). Loop until verified. Prefer "write the predicate/test that reproduces the requirement, then make it pass."

**TuringOS Lite Specific Invariants (from charter - non-negotiable, recursive audit)**

- **Dual independent tapes, same Git technology**:
  - Macro Tape = user's project `.git` (code/world).
  - Micro Tape = private `~/.local/share/turingos/projects/<id>/micro.git` (agency: Intent/Capsule/Receipt/Failure/Approval/Broadcast/Replay as first-class Git objects).
  - Never mix: no single-repo dual refs, no JSONL/SQLite as source of truth, no Macro commit/PR/CI as Micro acceptance.

- **Every object MUST name its scale**:
  - Micro: `μ:<micro_commit_oid>`
  - Macro commit: `macro:git:<project_id>:<commit_oid>`
  - Macro PR: `macro:pr:<provider>/<repo>#<number>`
  - etc. (see charter 1.3)
  - Forbidden in logs/UI: "accepted: abc123", "Claude approved", "CI passed therefore accepted".

- **Micro Predicate Kernel is the daily gate** (not VetoAI, not stats):
  - Validates Micro state transitions, contracts, receipts, shields, authorizations, failure handling.
  - Statistical signals (CI green, LLM judge, embedding sim) are *evidence only*, never gates.
  - "Micro anchor predicate PASS", "Macro CI green: external evidence only".

- **TUI is projection only** (FC-A10):
  - Reads Micro Tape + declared Macro observations/anchors.
  - Never writes truth directly. Hotkeys dispatch to daemon which goes through Predicate + wtool.

- **Work Capsules + explicit contracts before dispatch** (FC-A08, FC-A09):
  - Visible capsule for worker + private micro contract (hidden predicates, budget).
  - Macro completion contract declared *before* any worker run or irreversible Macro action.
  - No PR/push/merge without prior `MacroActionAuthorization`.

- **External Agent Bundle rule** (1.5):
  - Bundles (Codex, Claude CLI, Grok Build, manual) = compound middle blackbox.
  - TuringOS bottom whitebox = adapter + sandbox + timeout + receipts + observer.
  - API workers get full whitebox tools with *every* tool call producing a Micro receipt.

- **Failure always appends** (FC-A03, 3.6):
  - Every FAIL/reject/timeout writes FailureNode (advances tape_tip, *never* accepted_head).
  - accepted_head only advances on accepted state events.

- **Implementation process (module/phase/atom cascade + multi-agents)**:
  - Follow the 11 phases and atom contracts exactly (see CHARTER).
  - Each Atom is written for *low-thinking Worker AI*: explicit allowed/forbidden files, context, acceptance_commands.
  - Worker output format required: atom_id, status, changed_files, commands_run (with exit+stdout_hash), known_risks, next_recommended_atom.
  - For complex phases/atoms: use multi-agent orchestration (roles: explorer/plan/implementer/verifier/reviewer). One parent orchestrates, delegates in parallel where independent, compresses results.
  - Loops are first-class: Failure Memory feedback (quantize → cluster → broadcast rule → shield update), predicate verification at every boundary, replay from Micro Tape.
  - Before any code: run flowchart audit (FC-A01-10) + code audit prompt from charter section 15.
  - Tests + audit commands must pass for the atom.

**Harness Practices (synthesized from 2025-2026 leading harnesses: Grok, Claude Code, Cursor, Aider, SWE-agent etc. + Karpathy research)**

- Use Git worktrees for parallel/isolated Macro work (per charter .turingos/worktrees).
- Context minimization for workers (capsules + shields; repo-map style structural views; on-demand skills).
- Persistent memory outside ephemeral context: Micro Tape is primary; derived playbooks/files for curated failure knowledge.
- Typed events/contracts + provenance on boundaries.
- Behavioral constraints (this file) + reusable "skills" for common atom/loop patterns.
- Projection views for state (avoid chat walls / long polluted sessions).
- Always prefer declarative success criteria + loops over imperative step lists.
- When stuck: surface assumptions (Think Before), keep surgical, restart clean via replay + external state.

**Quick Commands for Agents/Developers**

- `python -m turingos.cli --help`
- Implement one atom at a time. Run its acceptance_commands.
- For a full phase: orchestrate multiple specialized sub-agents (one per atom or role).
- Audit: `python -m turingos.cli audit all` (or the standalone audit scripts in audits/).
- Replay: use Micro Tape + anchors to reconstruct.

**References (for recursive audit)**

- Full Charter/Plan: `TURINGOS_LITE_v1.0_PROJECT_CHARTER.md`
- Research & Best Practices: `RESEARCH_KARPATKY_SOFTWARE3_VIBE_HARNESS_SYNTHESIS.md`
- Canonical flowcharts, schemas, predicates, atom contracts: in the Charter.
- First demo script: in Charter section 17.

This AGENTS.md + the two reference files constitute the local development harness for TuringOS Lite. All work must pass the charter's architecture invariants.

---

*Generated from research into Software 3.0, vibe/agentic engineering, and 2026 harness engineering (loops as primary work, multi-agent role orchestration, projection, Git as durable agency memory, explicit typed boundaries).* 
