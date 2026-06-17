# Original Charter and Vision (2026-06-16)

This captures the starting point: the full TuringOS Lite v1.0 开发项目计划书 provided by the user.

Key elements from the charter (summarized for reference; full text in TURINGOS_LITE_v1.0_PROJECT_CHARTER.md):

- **Core Definition**: Linux local TUI + Daemon. Macro Tape (user Git for code), Micro Tape (private bare Git ChainTape for agency: Intent, Capsule, Dispatch, Receipt, Failure, Approval, Broadcast, Replay).

- **Slogans**:
  - Same Git technology.
  - Two independent tapes.
  - Macro remembers code.
  - Micro remembers agency.
  - External agents generate candidates.
  - TuringOS keeps sovereignty.

- **Non-negotiable Architecture**:
  - Dual independent tapes (no single-repo dual refs, no JSONL/SQLite as truth).
  - Physical layout: user project + ~/.local/share/turingos/...
  - Strict scale language (μ: for Micro, macro:git: etc.).
  - VetoAI not in daily Lite flow.
  - External Agent Bundle rules (blackbox for bundles like Codex/Claude/Grok; whitebox tools + receipts for API workers).

- **Flowcharts and Audits**: Detailed flows (Dual-Tape Anti-Oreo, Boot/New/Adopt, Intent to Candidate, etc.) with FC-A01 to FC-A10 audit checklist that all diagrams must pass. Micro Predicate validates agency transitions, not code correctness.

- **P0 Scope**: Linux local daemon + CLI + TUI, dual tapes, specific commands, Meta AI as configurable OpenAI-compatible control model, fake workers first, Work Capsule compiler, Macro observer, Micro Predicate Kernel, Failure Memory, TUI Software 3.0 projection, audits.

- **Phases**: 0 (scaffold) to 11 (audits). Strict order: Micro append/replay before TUI; fake before real externals.

- **Atoms**: Detailed per phase/module with input/output contracts, forbidden behaviors, acceptance commands. Worker AI format for implementation.

- **Testing & Validation**: First demo script, recursive audits, no zombie nodes, E2E with simulated human in TUI.

- **Final Boundary**: "ugly, fast, and calm" — no chat walls, no IDE clone, no magic "verified", only law/capsule/receipt/failure/evidence/next sovereign action. User manages agency.

This charter was the immutable source. All later design (Software 3.0 alignment, keyring, loops/multi-agents, TUI as projection, global `turing` entrypoint, first-run Meta AI setup) derives from and must pass its invariants and FC-A audits.

See also the initial user query containing the full plan.