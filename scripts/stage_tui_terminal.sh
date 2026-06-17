#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export TURINGOS_DATA_DIR="${TURINGOS_DATA_DIR:-$HOME/.local/share/turingos}"

"$ROOT/turing" boot
exec "$ROOT/turing" tui
