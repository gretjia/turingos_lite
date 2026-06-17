# Index and Conversation Map (2026-06-17)

This is the entry point for the architecture history.

## Quick Map of Conversations → Current Code
- **00-original-charter-and-vision.md** → The immutable source. Everything must pass its FC-A audits, invariants (dual tapes, scale, Micro Predicate as gate, projection TUI, failure appends, etc.), and phase/atom order.
- **01-software-3.0-vision-and-karpathy-design.md** → The "think like Karpathy" synthesis that shaped the overall harness philosophy (loops as central work, harness as OS, Micro Tape as durable agency memory, projection UX, multi-agent roles, whitebox boundaries, behavioral constraints). Directly influenced keyring design, event recording of config changes, TUI first-run as guided loop, etc.
- **02-api-key-secret-management-and-keyring-decision.md** → The specific research + 3.0 design exercise that produced the keyring improvement. Compares OpenCode/Aider/Continue patterns and justifies env-primary + keyring + XDG metadata + Micro events (no secrets in tape).
- **03-loops-multi-agents-cascade-design.md** → The full-auto execution plan (subagent roles + recursive audits + no-zombie requirement) and the runtime loop designs (directly implementing charter 3.1–3.10 flowcharts as first-class code: append semantics, failure feedback, capsule lifecycle, Tool Predicate inner loop, TUI projection, etc.).
- **04-cli-tui-global-entry-and-first-run-meta-setup.md** → The conversation that produced the bare `turing` → TUI behavior (via callback + ~/.local/bin launcher) + the Meta AI first-run guidance in the TUI (term verified from charter as "Meta AI").
- **05-testing-protocols-e2e-simulation-and-no-zombie-verification.md** → The testing design (simulator for human-in-TUI hotkeys, 10+ real cases, monitor/debug subagents, global zombie gate, acceptance criteria) that allowed the final "HALT CONDITIONS MET".
- **06-keyring-implementation-and-3.0-credential-design.md** → The actual surgical code (config.py, events additions, cli config command, tui updates) + the Karpathy 3.0 rationale that preceded it.

## Current State Snapshot (as of end of 2026-06-17 conversations)
- Full dual-tape implementation (micro/ + macro/ + project/ + capsule/ + workers/ + failure/ + predicates/ + daemon/ + tui/).
- Projection-only TUI with all charter hotkeys.
- Global `turing` entry point (launcher + pyproject script + bare-command callback).
- Secure Meta AI config (env primary + keyring + XDG metadata + Micro events).
- Complete E2E harness with TUI simulation, monitors, no-zombie verification, and recursive audits (audits/ + `turing audit all`).
- All 22+ nodes from charter 7.2 + flowcharts are active (verified by final monitor run).
- AGENTS.md, RESEARCH_..., TESTING_MANUAL.md, and this architecture/ folder committed for ongoing reference.

## How to Use This Folder Going Forward
- When wondering "why did we do X this way?": start here.
- Before changing core invariants (dual tapes, predicate as gate, projection-only, etc.): re-read the relevant file + the original charter.
- The conversations here (especially the Software 3.0 / Karpathy thinking and the keyring 3.0 design exercise) are the "root" of the current program.

This archive was created at the user's request on 2026-06-17 so that "in future we have a reference to check where this idea comes from, and we know the root."

All files are plain Markdown for easy reading and future git history.