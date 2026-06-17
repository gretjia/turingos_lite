#!/usr/bin/env bash
# Install `turing` globally to ~/.local/bin (editable, any directory).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"

echo "Installing turingos-lite from: $ROOT"
pip3 install -e "$ROOT" --user --break-system-packages

if command -v turing >/dev/null 2>&1; then
  echo "OK: $(which turing)"
  turing --help | head -3
else
  echo "WARN: turing not on PATH. Add to ~/.bashrc:"
  echo '  export PATH="$HOME/.local/bin:$PATH"'
fi