# TUI UX Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make TuringOS Lite's Textual TUI usable as a real mouse-and-keyboard product in Terminal, from first boot through API setup, project cognition, proposal approval, and verification.

**Architecture:** Keep the TUI projection-only: reads stay on reducer/rtool, writes stay on daemon/wtool/predicate. The UX change is presentation and interaction routing only: center task flow first, left/right evidence secondary, and automatic layout modes for small, regular, and wide terminals.

**Tech Stack:** Python 3.11+, Textual, Typer console script, pytest, Textual Pilot human journeys, macOS Terminal visual staging.

---

### Task 1: Make Installed Audit And Turing Entrypoints Reliable

**Files:**
- Modify: `pyproject.toml`
- Create: `audits/__init__.py`
- Test: `tests/unit/test_cli_smoke.py`

- [x] **Step 1: Write the packaging expectation**

Installed `turing audit all` must import `audits.flowcharts`, `audits.invariants`, `audits.e2e`, and `audits.global_zombie_check` without requiring `PYTHONPATH=.`.

- [x] **Step 2: Run command to verify the baseline failure**

Run:

```bash
.venv/bin/turing audit all
```

Expected before fix: `No module named 'audits'` notes for audit modules.

- [x] **Step 3: Add audits to package discovery**

```toml
[tool.setuptools.packages.find]
include = ["turingos*", "audits*"]
```

- [x] **Step 4: Add package marker**

```python
"""Audit command modules for TuringOS Lite."""
```

- [x] **Step 5: Verify installed path**

Run:

```bash
.venv/bin/python -m pip install -e .
.venv/bin/turing audit all
```

Expected: `PHASE11 AUDITS IMPLEMENTED + AUDIT PASS - ALL NODES ACTIVE, NO ZOMBIES`.

### Task 2: Fix Terminal Layout Modes Around Real Sizes

**Files:**
- Modify: `turingos/tui/app.py`
- Test: `tests/unit/test_vibe_tui.py`

- [x] **Step 1: Write failing layout mode tests**

Add tests that assert:

```python
def test_layout_mode_for_regular_terminal(data_dir):
    app = TuiApp(project_id="layout_regular", data_dir=data_dir, force_mock_facilitator=True)
    async with app.run_test(size=(122, 30)) as pilot:
        await pilot.pause(0.2)
        assert app.has_class("focus")

def test_layout_mode_for_wide_terminal(data_dir):
    app = TuiApp(project_id="layout_wide", data_dir=data_dir, force_mock_facilitator=True)
    async with app.run_test(size=(287, 66)) as pilot:
        await pilot.pause(0.2)
        assert app.has_class("wide")
```

- [x] **Step 2: Run tests to verify red**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_vibe_tui.py -q -k "layout_mode" --tb=short
```

Expected: tests fail because `focus` and `wide` modes do not exist.

- [x] **Step 3: Implement mode thresholds**

Use three modes:

```python
if height <= 28 or width <= 100:
    mode = "compact"
elif height <= 36 or width <= 140:
    mode = "focus"
else:
    mode = "wide"
```

Only one mode class may be active at a time.

- [x] **Step 4: Add CSS for focus mode**

Focus mode keeps center task flow primary and hides the low-value side panes:

```css
.focus #left-pane, .focus #right-col, .focus #autonomy-row { display: none; }
.focus #center-pane { width: 1fr; border-right: none; }
.focus #chat-thread { height: 5; }
.focus #composer-body { min-height: 16; }
```

- [x] **Step 5: Verify green**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_vibe_tui.py -q -k "layout_mode" --tb=short
```

Expected: all layout mode tests pass.

### Task 3: Make Evidence Useful Instead Of Duplicative

**Files:**
- Modify: `turingos/tui/app.py`
- Test: `tests/unit/test_vibe_tui.py`

- [x] **Step 1: Write evidence summary test**

Add a test that seeds a project, mounts `TuiApp`, calls `refresh_projection()`, and asserts the evidence pane contains compact sections:

```python
assert "Project" in evidence_text
assert "Micro events" in evidence_text
assert "README:" not in evidence_text
```

- [x] **Step 2: Run test to verify red**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_vibe_tui.py -q -k "evidence_summary" --tb=short
```

Expected: failure because current evidence repeats full project cognition.

- [x] **Step 3: Implement compact evidence formatter**

Create `_format_evidence_lines(q, ev_lines)` inside `TuiApp` that returns only:

```text
Project: <project_id>
Status: <project_status>
Tip: <short μ>
Micro events
- <event_id>:<event_type>
```

- [x] **Step 4: Keep detailed cognition in center**

Do not remove center project cognition; only stop duplicating it in right-side Evidence.

- [x] **Step 5: Verify green**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_vibe_tui.py -q -k "evidence_summary" --tb=short
```

Expected: pass.

### Task 4: Add Real-Terminal Human QA Harness

**Files:**
- Modify: `scripts/run_human_tui_audit.sh`
- Create: `scripts/stage_tui_terminal.sh`
- Test: `tests/tui_e2e/test_human_journey_matrix.py`

- [x] **Step 1: Add staging script**

Script behavior:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export TURINGOS_DATA_DIR="${TURINGOS_DATA_DIR:-$HOME/.local/share/turingos}"
".venv/bin/turing" boot
exec ".venv/bin/turing" tui
```

- [x] **Step 2: Make executable**

Run:

```bash
chmod +x scripts/stage_tui_terminal.sh
```

- [x] **Step 3: Verify real terminal launch**

Run via macOS Terminal:

```bash
osascript -e 'tell application "Terminal" to do script "cd /Users/zephryj/Documents/turingos_lite/.turingos/worktrees/tui-ux-overhaul && ./scripts/stage_tui_terminal.sh"'
```

Expected: TUI opens with first screen visible.

- [x] **Step 4: Capture screenshot evidence**

Run:

```bash
screencapture -x /tmp/turingos-lite-tui-qa.png
```

Expected: screenshot shows full-screen TUI with readable center flow.

### Task 5: Real API And Real Project Journey

**Files:**
- Modify: `turingos/config.py`, `turingos/facilitator/provider_registry.py`, `turingos/facilitator/provider_setup.py`
- Test: `tests/real_llm_test.py`, `tests/unit/test_config_env.py`, `tests/unit/test_provider_setup.py`

- [x] **Step 1: Configure real DeepSeek API details**

Use the user-provided API key only in env/keyring paths. Do not write secrets to files, logs, screenshots, commits, or Micro Tape.

- [x] **Step 2: Select a real local project**

Primary project selected for E2E:

```text
/Users/zephryj/Documents/turingos_lite
```

- [x] **Step 3: Run adopt/config/task journey**

Use mouse and keyboard path:

```text
Boot -> project cognition -> AI setup -> API provider -> API key panel -> save -> ask project question -> submit -> approve -> verify replay/audit
```

Verified through Textual Pilot human journeys plus real macOS Terminal screenshots.

- [x] **Step 4: Verify no secret leakage**

Run:

```bash
grep -R "sk-" -n . ~/.local/share/turingos 2>/dev/null | head
```

Expected: no real API key in repo or Micro runtime files. Fake `sk-test` and `sk-fake` fixtures are allowed in tests.

- [x] **Step 5: Verify PR-ready project gates**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/unit tests/tui_e2e tests/real_llm_test.py -q --tb=short
./turing audit all
git diff --check
```

Expected: all tests/audits pass before opening the PR.

---

## Self-Review

Spec coverage: covers local setup, isolated worktree, TUI UX, Terminal staging, real project/API journey, and handoff quality.

Placeholder scan: no TBD/TODO/later placeholders; Task 5 explicitly waits for user API because secret input is intentionally external.

Type consistency: class names and selectors match `TuiApp`, `VibeComposerPane`, `#center-pane`, `#left-pane`, `#right-col`, and `#evidence-pane`.
