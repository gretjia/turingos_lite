#!/usr/bin/env bash
# TuringLoop IPQC interval calculator
# Usage: calc-ipqc-interval.sh <eta_steps> <failure_rate>
set -euo pipefail
eta="${1:-300}"
rate="${2:-0}"
python3 -c "
import math
eta = float('$eta')
rate = float('$rate')
interval = max(3, round(eta * 0.12 / (1 + rate)))
print(interval)
"