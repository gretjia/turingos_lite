#!/usr/bin/env bash
# E2E demo: 4 vibes → deliver → artifact + tape verification (headless/mock).
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
DEMO_DIR="${TURINGOS_DATA_DIR:-/tmp/turingos_vibe_demo}"
export TURINGOS_DATA_DIR="$DEMO_DIR"
PID="vibe_demo_e2e"
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"

python3 << 'PY'
import os
from pathlib import Path

from turingos.events import make_event, SYSTEM_BOOTSTRAPPED, PROJECT_READY
from turingos.micro.git_tape import MicroGitTape
from turingos.micro.rtool import MicroRtool
from turingos.micro.wtool import append as wtool_append
from turingos.tui.app import TuiApp

data_dir = Path(os.environ["TURINGOS_DATA_DIR"])
pid = "vibe_demo_e2e"
gt = MicroGitTape(pid, data_dir=data_dir)
gt.init()
wtool_append(pid, make_event(SYSTEM_BOOTSTRAPPED, {"boot": "demo"}), data_dir=data_dir)
wtool_append(pid, make_event(PROJECT_READY, {"name": pid}), data_dir=data_dir)

app = TuiApp(project_id=pid, data_dir=data_dir, force_mock_facilitator=True)
app.autonomy = 40

vibes = [
    "vibe: create a todo app with persistence",
    "vibe: use sqlite + React frontend",
    "vibe: add user authentication",
    "vibe: complete and deliver",
]
for vibe in vibes:
    from turingos.facilitator.transcribe import mock_transcribe
    app.pending_proposals = mock_transcribe(vibe, {"project_id": pid})
    app._approve_proposals()

r = MicroRtool(pid, data_dir=data_dir)
artifact = data_dir / "projects" / pid / "delivered.json"
assert r.read_tip().startswith("μ:"), "tape must be non-empty"
assert artifact.exists(), f"artifact missing: {artifact}"
assert app.delivered or "wc_delivered" in str(r.iter_commits())
print("E2E PASS: Project Delivered")
print(f"  tape_tip: {r.read_tip()}")
print(f"  artifact: {artifact}")
print(f"  commits: {len(list(r.iter_commits()))}")
PY

echo "=== demo_e2e.sh SUCCESS ==="