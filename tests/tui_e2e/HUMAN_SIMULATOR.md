# Human User Simulator — TUI UX Testing on Linux

## Problem

Kernel/unit tests call `_facilitator_run()`, `post_message()`, or set `widget.value` directly.
That **bypasses** the same guards, scroll regions, and `_choices_ready` gates a human hits.
UX bugs (silent no-ops, off-screen MCQ, missing config panel) slip through.

## Two layers (both required)

| Layer | Where | What it simulates |
|-------|--------|-------------------|
| **A. Strict Pilot (CI)** | `tests/tui_e2e/test_human_journey_matrix.py` | Mouse click + keyboard via Textual `Pilot` in `run_test()` headless |
| **B. Staging TTY (SSH)** | `turing` in tmux + checklist below | Real terminal rendering on your Linux server |

Textual docs: [`run_test()` + Pilot](https://textual.textualize.io/guide/testing/) uses the **same message pump** as production; headless only skips drawing to stdout.

## Run strict human audit

```bash
./scripts/run_human_tui_audit.sh
# or
pytest tests/tui_e2e/test_human_journey_matrix.py -v
```

## Journey matrix coverage

| ID | Journey |
|----|---------|
| J01 | Boot → project cognition visible |
| J02 | Type question → chat thread reply |
| J03 | Paste DeepSeek token → auto setup feedback |
| J04 | explore → submit → **click Approve** → enrich → skip |
| J10 | Config menu: Facilitator / Meta / Worker |
| J11–J12 | Meta wizard preset + API key panel via click |
| J13–J14 | Facilitator NVIDIA + paste snippet |
| J20 | **Every** Worker API provider MCQ clickable |
| J21 | Worker bundles (Codex / Claude / Grok) |
| J22 | Worker DeepSeek full wizard → save |
| J30 | **80×24 SSH** terminal — scroll + click Worker API |

## Strict rules (enforced by `test_human_simulator_source_has_no_bypass`)

- ✅ `pilot.click`, `pilot.press`, `pilot.pause`, scroll before click
- ❌ `_facilitator_run`, `_approve_proposals`, `post_message(ChoiceSelected)`
- ❌ `inp.value = ...` (typing must use `pilot.press` per key)

## Staging on SSH (real human)

```bash
tmux new -s turing-ux
cd ~/projects/your-app
export TURINGOS_DATA_DIR=~/.local/share/turingos/projects/your-app
turing
```

Checklist (15 min):

1. Boot shows 项目认知
2. 配置 → Worker → scroll ↓ → click **API · DeepSeek** → wizard step 1
3. Click **输入 API Key** → blue panel appears below MCQ
4. Paste NVIDIA sample in top composer → Send → chat feedback with extracted fields
5. explore → 我理解对了 → Approve button → enrich
6. Resize tmux small (`Ctrl+B` then drag) — all Worker API options still reachable via scroll

## When a human journey fails

The error includes a **journal** of clicks/presses — reproduce exactly in tmux.

## Legacy tests

`test_pilot_journeys.py` — allows `post_message` fallback (technical debt).
**UX gate = human journey matrix only.**