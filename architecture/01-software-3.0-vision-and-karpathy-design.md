# Software 3.0 Vision and Karpathy-Style Design Thinking (2026-06-17)

Captured from the explicit "think about future Software 3.0... If you are Karpathy, what would you design this process" discussion before the keyring implementation.

## Core Karpathy Software 3.0 Principles (as synthesized in the session)
- Prompts as programs; natural language (English) is the new programming language.
- LLMs as new computers: utilities/fabs/OSes. Context window = RAM (volatile program state); model weights = CPU (interpreter/substrate).
- Software 3.0 eats 1.0 (explicit code) and 2.0 (neural weights). Massive rewriting ahead.
- LLMs have "jagged intelligence" and "anterograde amnesia" → need external durable memory (scratchpads, system prompt learning, Git as SoT), feedback loops, verification.
- Vibe coding → agentic engineering: embrace exponentials, forget the code exists, declarative (intent + success criteria) over imperative. Human role = manifestor/orchestrator/curator/verifier. Let agents loop with tenacity.
- The 4 principles (viral CLAUDE.md influence): Think Before Coding (surface assumptions/tradeoffs), Simplicity First, Surgical Changes, Goal-Driven Execution (criteria first, loop until verified).
- Harnesses matter more than models: context engineering, persistent memory (Git/tapes for replay/audit), multi-agent orchestration with roles + isolation, projection views, typed events/contracts, behavioral constraints (AGENTS.md), skills for reusable loops.
- Build for agents (new consumer of digital info). Partial autonomy with human verification loops. "The Decade of Agents."

## Application to TuringOS Lite Design (Karpathy Lens)
TuringOS Lite is positioned as a **sovereign local agentic harness** embodying 3.0:

- **Dual Tapes as 3.0 Memory Architecture**: Macro Tape = code world (user Git). Micro Tape (private Git ChainTape) = agency world (intents/capsules/receipts/failures as first-class objects). This is the "durable external memory" / "system prompt learning" scratchpad that counters LLM amnesia. Everything is replayable, auditable, sovereign. User manages *agency* (not model sessions).

- **Harness over Raw Model**: The system is the harness (wtool as typed event bus, rtool/reducer as projection, Predicate Kernel as daily law/gate enforcing FC-A invariants, Shield/Broadcast/Variants for context min + failure feedback loops, adapters for blackbox externals). External agents (Codex, Claude, Grok, API) are blackboxes; TuringOS owns the whitebox boundary + mandatory receipts. This matches "harnesses matter" and "build for agents."

- **Loops as Central Work**: 
  - Micro Append Semantics (state machine: tape_tip always, accepted_head only on state events post-predicate).
  - Failure Memory Feedback (FailureNode → Quantization → Cluster → Broadcast rule + Shield update → next capsule variant).
  - Capsule Lifecycle, Intent-to-Candidate (with inner Tool Predicate loop for API workers), Macro Completion Contract.
  - TUI Projection + hotkey dispatch → predicate → wtool (never direct mutation).
  - Replay from Micro Tape + anchors (projection rebuildable if sqlite deleted).

- **Multi-Agents by Task Type + Module/Phase/Atom Cascade**: 
  - Runtime: Meta AI (proposer), Shield (compiler), Predicate (kernel), Broadcast (reducer), specialized Worker adapters, Human approver. Orchestrated via daemon + typed events.
  - Development: Use multi-agent orchestration (explorer, planner, implementer, verifier, auditor, monitor/debugger subs) to execute the 11 phases / atoms in parallel where independent. Atoms are surgical/goal-driven contracts for low-thinking workers. Follow AGENTS.md (the 4 principles baked in).

- **Projection-Only UX (No Chat Walls)**: TUI is pure read-only view of law + evidence + next sovereign action (4 panes). Hotkeys dispatch through harness. "Ugly, fast, and calm." User manages agency via capsules/receipts/failures/evidence. Aligns with "no chat wall", "build for agents", partial autonomy.

- **First-Run / Onboarding as Guided Loop**: TUI on first launch surfaces assumptions/tradeoffs and guides high-level declaration of the Meta AI (Facilitator). This is the "intent capture + verification" loop.

- **Credential / Secret Management (the specific process discussed)**:
  - User manifests at high level ("declare my Meta AI capability").
  - Harness manages details: env vars primary (for 3.0 fluidity, CI, overrides — the "English program").
  - Persisted secrets ONLY in OS keychain (secure substrate, like password managers in the agent OS).
  - Non-secrets (base_url, model) in XDG JSON.
  - Declarations as first-class Micro events (MetaAIConfigured/Revoked with metadata/hash — sovereign, replayable, auditable; **never the raw secret** in tape/logs/capsules/projection).
  - Whitebox adapter boundary: key loaded at last moment for runtime use only.
  - Feedback: verification on load/use; failures as FailureNodes.
  - This is "harness as OS" + "build for agents" + "durable memory" + "never hide confusion."

- **Sovereignty & Scale Language**: Strict typing of everything (μ: vs macro:). External bundles blackbox; TuringOS whitebox. VetoAI out of P0 (daily gate = Micro Predicate only). User no longer manages model sessions — manages agency.

- **Overall 3.0 UX**: The harness turns ephemeral vibes/agent loops into durable, sovereign, explicit, replayable agency. User programs the *system* declaratively; the harness enforces law (predicates), provides memory (tapes), orchestrates agents, projects state cleanly, and handles low-level secrets (keyring) securely.

This conversation directly shaped the keyring improvement, the config.py central module (with event recording), the TUI first-run guidance, the `turing config --meta` CLI, the emphasis on env-primary + secure persistence, and the overall alignment of all harness primitives to 3.0 principles.

See also RESEARCH_KARPATKY_SOFTWARE3_VIBE_HARNESS_SYNTHESIS.md for the full synthesis that informed this design.