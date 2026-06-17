# CLI/TUI Global Entry Point and First-Run Meta AI Setup (2026-06-17)

This captures the conversation about making `turing` a global command that directly enters the TUI, plus the first-launch guidance for setting the Meta AI (Facilitator) API.

## Requirements
- "set up a command line entry point as turing, and also set the global path. So, in any working folders, I just need to type turing, and then I'll enter the TUI."
- "I assume in the TUI, it should designed to guide me to set my first API for Facilitator AI. Or Meta AI, I forgot what's written in the plan. you need to check it for me"

From charter check (performed in session):
- Term is **Meta AI** (see header "目标读者：Meta AI...", section 0 "Meta AI as one configurable OpenAI-compatible control model.", flowcharts with META[Meta AI proposal only], P0 scope).
- It is the OpenAI-compatible control/proposer model that turns user intent into WorkOrders (the "Facilitator" role in the user's mental model).

## What Was Implemented
- **Entry point**: pyproject.toml already had `[project.scripts] turing = "turingos.cli:app"`. This generates the console script on `pip install -e .`.
- **Global launcher**: Created `~/.local/bin/turing` (simple exec python3 -m turingos.cli "$@") so the command works from any directory even before/without full pipx-style install. User adds `export PATH="$HOME/.local/bin:$PATH"` to shell rc (standard for user tools on Linux).
- **Bare `turing` launches TUI**: Added `@app.callback(invoke_without_command=True)` in cli.py. If no subcommand, calls tui(). `turing` (bare) now directly enters the projection TUI from any folder. Subcommands (`turing intent ...`, `turing audit all`, etc.) still work.
- **First-run guidance in TUI**: In tui/app.py `on_mount` → `_check_first_time_meta_setup()`:
  - Checks `~/.local/share/turingos/config/meta_ai.json` (or falls back to env).
  - If no key: sets prominent message in the NEXT ACTION pane (visible immediately) explaining "FIRST SETUP: Set your Meta AI (Facilitator AI / control model). This is the OpenAI-compatible model that proposes WorkOrders (see charter)." Gives exact env var examples (TURINGOS_META_BASE_URL, _API_KEY, _MODEL).
  - If envs present: auto-persists metadata (key handling moved to keyring in later improvement).
  - Message updated in the keyring improvement conversation to strongly recommend the secure `turing config --meta` path (CLI getpass → keyring) while keeping env as primary for 3.0 fluidity.
- **Config command** (added as part of keyring improvement, but tied to this request): `turing config --meta` for interactive secure management (set/clear/show; key only to keyring; metadata to JSON; records MetaAIConfigured/Revoked events in Micro Tape).
- **Terminology**: Always "Meta AI" per plan, with parenthetical "Facilitator" when user used that language, plus explanation that it is the proposer in the charter flows.

This directly fulfills the request: type `turing` anywhere → TUI → immediate guidance on setting the first Meta AI API (the exact thing from the plan).

See cli.py (callback + tui() + config command), tui/app.py (first-run logic), the global launcher script, README.md (updated instructions), and TESTING_MANUAL.md for usage.

This change was part of making the harness feel like a real Software 3.0 personal agentic OS (bare command drops you into the projection of your agency, with onboarding for the brain).