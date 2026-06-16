# TuringOS Lite

**Dual independent Git Tape local Agentic operation workbench.**

Linux-first TUI + Daemon.  
Macro Tape manages your project's code world (existing Git/CI).  
Micro Tape (private Git ChainTape) manages *agency* (intents, capsules, receipts, failures, approvals, broadcasts, replay) with full sovereignty.

> Same Git technology.  
> Two independent tapes.  
> Macro remembers code.  
> Micro remembers agency.  
> External agents generate candidates.  
> TuringOS keeps sovereignty.

## Software 3.0 Foundation & Research Harness

This project is built on Andrej Karpathy's Software 3.0 principles (prompts as programs, natural language + agents as the new interface, context as RAM, models as CPU; Software 3.0 eating 1.0/2.0) and "vibe coding" / agentic engineering (declarative intent + success criteria, embrace loops and exponentials, manifest/orchestrate rather than direct coding, forget the code exists while retaining sovereignty).

Development harness (local best practices synthesized from 2025-2026 leading systems — Grok Build, Claude Code, Cursor, Aider, SWE-agent/OpenHands etc.):

- **Loops as the most important work**: Failure Memory feedback loops, Micro Predicate verification at every boundary, broadcast reducers, replay from tape, PEV-style (plan → capsule/contract → execute → verify).
- **Multi-agents by task type**: Role-specialized orchestration (explorer, planner, implementer, verifier, reviewer, orchestrator). Parallel where independent, with context firewalls + worktree isolation. One parent manages delegation + synthesis.
- **Module/Phase/Atom 3-cascade**: Follow the exact cascade in the Charter. Atoms are *surgical, goal-driven units* written for low-thinking Worker AI (explicit contracts: allowed/forbidden files, acceptance commands, output format with hashes + risks + next atom). Use multi-agents to complete phases/atoms in one go.
- **Projection-only interfaces**: TUI and views are read-only projections of law + evidence + next sovereign action. No chat walls, no direct mutation of truth.
- **Karpathy 4 principles baked in** (see AGENTS.md): Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution.
- **Sovereign boundaries**: Blackbox external workers (Codex, Claude CLI, Grok, APIs, manual) vs. TuringOS whitebox adapters + mandatory typed receipts + scale language. No hidden predicates in worker-visible capsules.

Full research synthesis (including specific recommendations and anti-patterns from real harnesses):

**`RESEARCH_KARPATKY_SOFTWARE3_VIBE_HARNESS_SYNTHESIS.md`**

## The Plan (Charter)

Complete v1.0 development project plan book (non-negotiable architecture decisions, flowcharts with FC-A audit checklist, schemas, predicate kernel, TUI spec, CLI contract, worker config, 11 phases + detailed atom contracts with input/output/forbidden/acceptance, audit prompts, first working demo script, final product boundary):

**`TURINGOS_LITE_v1.0_PROJECT_CHARTER.md`**

Key non-negotiables (excerpt):
- Dual independent tapes (Macro = user code Git, Micro = private agency Git ChainTape as source of truth).
- Every object names its scale; forbidden "magic accepted" language.
- Micro Predicate (not stats or CI) is the daily gate.
- TUI is pure projection.
- Explicit Macro completion contracts + Micro authorization before any irreversible action.
- Failure *always* appends FailureNode (advances tape_tip, never accepted_head).
- External bundles are blackboxes; TuringOS owns whitebox boundary + receipts.
- VetoAI / constitutional evolution is out of P0 scope.

Implementation order: Phase 0 scaffold → Phase 1 Micro Git ChainTape → ... → Phase 11 audits. Do not start TUI before Micro append/replay works. Fake Worker first for E2E.

First working demo (from charter):
```bash
python -m turingos.cli boot
python -m turingos.cli new demo_app
cd demo_app
python -m turingos.cli intent "create src/hello.txt with hello from turingos"
python -m turingos.cli dispatch wc_000001 --worker fake_command
python -m turingos.cli observe wc_000001
python -m turingos.cli approve candidate_000001 --route staging
python -m turingos.cli replay latest
python -m turingos.cli tui
python -m turingos.cli audit all
```
PASS requires specific Micro events on tape, Macro changes in worktree, projection rebuildable, no main merge.

## Local Setup (this repo)

This checkout is the harness bootstrap + skeleton per the charter (Phase 0 atoms + research best practices).

```bash
# Install (uv or pip)
pip install -e .

# Smoke
turing --help
python -m pytest tests/unit/test_cli_smoke.py -q
```

Key files:
- `pyproject.toml` — minimal deps + entrypoint (typer + pydantic + textual per charter)
- `turingos/cli.py` — Phase 0 skeleton (boot/new/adopt/intent/tui/audit placeholders)
- `tests/unit/test_cli_smoke.py` — acceptance per charter atom
- `AGENTS.md` — the active development harness (Karpathy 4 + TuringOS invariants + atom/multi-agent/loop process + references to research & charter)
- `.turingos/` — runtime (capsules, worktrees) — gitignored for source
- The full Charter and Research md files are committed for auditability.

## Development Process (Harness-Enforced)

1. Pick next atom from the Charter (e.g. P0-M0-A01...).
2. Read relevant charter sections + research recommendations.
3. For complex work: use multi-agent orchestration (roles per research: explorer, plan, implement, verify).
4. Implement *surgically* + goal-driven (acceptance commands first).
5. Run acceptance + full audits (FC-A checklist + code audit prompt from charter §15).
6. Append FailureNodes on any deviation; use broadcast/replay loops.
7. Commit with clear Micro-scale thinking.

See `AGENTS.md` for the complete harness rules that all agents (human or AI) must follow on this codebase.

## Status

Initial harness + skeleton setup (research-driven, charter-aligned).  
Repo: public on GitHub (turingos_lite).  
Next: follow Phase 0/1 atoms to flesh out Micro Git ChainTape kernel etc.

---

*Built with the explicit goal of a completely AGI-towards (Software 3.0) product UX while maintaining strict sovereignty via dual tapes, predicates, and projection.* 
