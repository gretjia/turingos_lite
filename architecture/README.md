# Architecture, Design & Plan History for TuringOS Lite

This folder preserves the key conversations, decisions, and thinking that shaped the project.

It serves as the "root" reference:
- Trace where ideas originated.
- Understand why certain architectural choices were made (e.g., dual tapes, Micro Predicate, keyring for secrets, projection-only TUI).
- See the evolution from the original charter to the implemented system.
- Reference Karpathy's Software 3.0 principles and harness best practices as applied here.

**How the program looks today is a direct result of the conversations documented here (primarily from 2026-06-16 to 2026-06-17 sessions).**

Files in this folder capture:
- Original project charter and vision.
- Software 3.0 thinking (as if from Karpathy's perspective).
- Architecture decisions: loops, multi-agents, module/phase/atom cascade.
- Secret/API key management design and keyring improvement.
- CLI/TUI entry points, global command, first-run Meta AI setup.
- Testing protocols, E2E simulation (human-in-TUI simulation, monitors, no-zombie verification).
- Implementation of core harness (config, dual tapes, etc.).

See the main README.md and `TURINGOS_LITE_v1.0_PROJECT_CHARTER.md` for current state. Use this folder for historical context and rationale.

Last updated: 2026-06-17 (end of major architecture and implementation conversations).