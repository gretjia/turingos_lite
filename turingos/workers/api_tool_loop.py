"""API Worker: whitebox tool loop with real file I/O (charter §1.5 / FC-A07)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..events import (
    make_event,
    WORKER_DISPATCH_PREPARED,
    WORKER_RUN_RECEIPT_IMPORTED,
    TOOL_CALL_REQUESTED,
    TOOL_CALL_DENIED,
    TOOL_CALL_RECEIPT,
)
from ..micro.wtool import append as wtool_append
from ..predicates.kernel import PredicateKernel
from ..tools.whitebox import WhiteboxScope, run_tool
from .base import WorkerBase


class ApiToolLoopWorker(WorkerBase):
    """Whitebox API worker — every tool call → ToolCall* Micro receipt."""

    name = "api"
    ALLOWED_TOOLS = {"read_file", "list_dir", "grep", "apply_patch", "write_file", "run_command"}

    def run(
        self,
        pid: str,
        capsule_id: str,
        worker_name: str = "api",
        max_tool_steps: int = 8,
        tool_plan: list[dict[str, Any]] | None = None,
        macro_root: str | None = None,
        data_dir: Path | None = None,
        **_: Any,
    ) -> dict:
        root = Path(macro_root or os.getcwd())
        scope = WhiteboxScope(root)
        plan = tool_plan or [
            {"tool": "list_dir", "args": {"path": "."}},
            {"tool": "read_file", "args": {"path": "README.md"}},
        ]

        wtool_append(
            pid,
            make_event(WORKER_DISPATCH_PREPARED, {"capsule_id": capsule_id, "worker": worker_name}),
            data_dir=data_dir,
        )
        self._append_run_started(pid, capsule_id)

        k = PredicateKernel()
        tool_results: list[dict] = []

        for step, item in enumerate(plan[:max_tool_steps]):
            tool = item.get("tool", "")
            args = item.get("args") or {}
            if tool not in self.ALLOWED_TOOLS:
                wtool_append(
                    pid,
                    make_event(TOOL_CALL_DENIED, {"capsule_id": capsule_id, "tool": tool, "reason": "not_allowed"}),
                    data_dir=data_dir,
                )
                continue

            req = {"tool": tool, "step": step, "args": args}
            wtool_append(
                pid,
                make_event(TOOL_CALL_REQUESTED, {"capsule_id": capsule_id, "tool_call": req}),
                data_dir=data_dir,
            )
            try:
                _ = k.validate({"event_type": "ToolCallRequested", "payload": req}, {"prev_tape_tip": "μ:sim"})
            except Exception:
                pass

            result = run_tool(scope, tool, args)
            wtool_append(
                pid,
                make_event(TOOL_CALL_RECEIPT, {"capsule_id": capsule_id, "tool": tool, "result": result}),
                receipts={f"tool_{tool}_{step}.json": result},
                data_dir=data_dir,
            )
            tool_results.append(result)

        final = {
            "status": "api_tool_loop_done",
            "worker": worker_name,
            "tools_executed": len(tool_results),
            "mutated": any(r.get("mutated") for r in tool_results),
            "exit": 0,
        }
        wtool_append(
            pid,
            make_event(WORKER_RUN_RECEIPT_IMPORTED, {"capsule_id": capsule_id, "worker": worker_name}),
            receipts={"api_run.json": final},
            data_dir=data_dir,
        )
        return final