"""Agent event bus: headless/agent-driven TUI without human clicks."""
from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentBus:
    """Simple in-process queue for agent → TUI events."""

    _queue: deque[dict[str, Any]] = field(default_factory=deque)

    def post(self, event: dict[str, Any]) -> None:
        self._queue.append(event)

    def post_json(self, raw: str) -> None:
        self.post(json.loads(raw))

    def drain(self) -> list[dict[str, Any]]:
        out = list(self._queue)
        self._queue.clear()
        return out

    def pending(self) -> int:
        return len(self._queue)


# Module-level bus for headless/agent scripts
GLOBAL_BUS = AgentBus()