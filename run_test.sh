#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
echo "=== TuringOS Vibe TUI test suite ==="
python3 -m pytest \
  tests/unit/test_facilitator_v2.py \
  tests/unit/test_config_wizard_nav.py \
  tests/unit/test_vibe_tui.py \
  tests/unit/test_tui_replay.py \
  tests/agent_sim.py \
  tests/unit/test_cli_smoke.py \
  -q --tb=short
echo "=== Real LLM tests (skip if no endpoint) ==="
python3 -m pytest tests/real_llm_test.py -q --tb=short || true
echo "=== All mock tests passed ==="