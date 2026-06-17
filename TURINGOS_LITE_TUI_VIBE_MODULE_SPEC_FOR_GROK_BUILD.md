# TuringOS Lite - Vibe TUI Redesign Module
**Build Specification v1.0** | Worktree: `.turingos/worktrees/tui-vibe-redesign`

See also: [TUI_SOFTWARE_3_VIBE_DESIGN.md](./TUI_SOFTWARE_3_VIBE_DESIGN.md)

## Status: IMPLEMENTED (2026-06-17)

### Delivered
- `turingos/tui/app.py` — 5-pane Vibe TUI (TopBar + Capsules | Composer | Next+Evidence)
- `turingos/tui/widgets.py` — VibeComposer, CapsulesPane, EvidencePane, etc.
- `turingos/facilitator/transcribe.py` — mock + OpenAI-compatible LLM transcription
- `turingos/tui/agent_bus.py` — agent event bus + headless API
- Tests: `tests/unit/test_vibe_tui.py`, `tests/agent_sim.py`, `tests/real_llm_test.py`
- Scripts: `run_test.sh`, `demo_e2e.sh`

### Launch
```bash
cd .turingos/worktrees/tui-vibe-redesign
export TURINGOS_DATA_DIR=/tmp/turingos_demo
python3 -m turingos.tui
# or: python3 -m turingos.cli tui
```

### LLM config
```toml
# env or turing config --meta
TURINGOS_META_BASE_URL=http://localhost:11434/v1
TURINGOS_META_API_KEY=ollama
TURINGOS_META_MODEL=llama3.2:3b
```

### Acceptance
- [x] Vibe → Proposal Card (mock <3s; real LLM optional)
- [x] Approve → dispatch + Evidence + Capsules update
- [x] Autonomy 0/50/100% behavior
- [x] Agent drives full flow (agent_bus + headless)
- [x] ≤5 visual blocks, reactive projections
- [x] E2E demo: `demo_e2e.sh` → Delivered + artifact