#!/usr/bin/env bash
# Human UX audit — strict Pilot journeys (no _facilitator_run / post_message bypass).
# Run on Linux server CI or before release. Same event pump as real `turing` TUI.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"

echo "=== Human TUI Journey Matrix (strict Pilot) ==="
python3 -m pytest tests/tui_e2e/test_human_journey_matrix.py \
  tests/tui_e2e/test_human_simulator_guards.py \
  -v --tb=short "$@"

echo ""
echo "=== Optional: real terminal smoke (requires TTY) ==="
if [[ -t 1 ]] && command -v script &>/dev/null; then
  echo "TTY detected. Run manual checklist:"
  echo "  cd <your-project> && turing"
  echo "  Follow tests/tui_e2e/HUMAN_SIMULATOR.md § Staging on SSH"
else
  echo "No TTY — skipped live terminal smoke (CI uses Textual Pilot headless)."
fi

echo "=== Human UX audit passed ==="