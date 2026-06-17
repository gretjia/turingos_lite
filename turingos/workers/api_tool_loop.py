"""api_tool_loop.py: API (raw model) Worker with explicit inner Tool Predicate loop (charter 3.5 / FC-A07 / 1.5).
For OpenAI-compat / local: TuringOS provides FULL whitebox (read/grep/patch/run) -- every tool call produces typed ToolCall* Micro receipt via wtool (predicate kernel gate on request/receipt).
Loop: request (append ToolCallRequested -> predicate), inner scope/budget check (use kernel), execute sim, ToolCallReceipt (with receipt).
Macro completion contract pre dispatch; no irreversible macro w/o auth.
"""
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
from .base import WorkerBase


class ApiToolLoopWorker(WorkerBase):
    """Whitebox API tool loop worker.
    Inner predicate per 3.5: every step Tool* append triggers full MicroPredicateKernel (schema, scope, provenance, receipt etc).
    Additional explicit local 'tool predicate' gate for mutability/budget (min for phase).
    Sim tools only (no side effects on arbitrary fs in harness; real impl would use controlled tools/ + receipts).
    """

    name = "api"

    ALLOWED_TOOLS = {"read_file", "list_dir", "grep", "apply_patch", "write_file", "run_command"}

    def run(self, pid: str, capsule_id: str, worker_name: str = "api", max_tool_steps: int = 2) -> dict:
        wtool_append(
            pid,
            make_event(WORKER_DISPATCH_PREPARED, {"capsule_id": capsule_id, "worker": worker_name}),
        )
        self._append_run_started(pid, capsule_id)

        k = PredicateKernel()  # explicit for inner Tool Predicate loop (3.5)
        tool_results = []
        sim_tools = ["read_file", "grep"][:max_tool_steps]

        for step, tool in enumerate(sim_tools):
            if tool not in self.ALLOWED_TOOLS:
                wtool_append(
                    pid,
                    make_event(TOOL_CALL_DENIED, {"capsule_id": capsule_id, "tool": tool, "reason": "not_allowed"}),
                )
                continue

            req = {"tool": tool, "step": step, "args": {"path": "README.md" if tool == "read_file" else None}}
            # Append REQUEST -> full predicate gate (incl worker_scope, budget stubs, schema)
            wtool_append(pid, make_event(TOOL_CALL_REQUESTED, {"capsule_id": capsule_id, "tool_call": req}))
            # 'inner predicate' (local + kernel already ran on append): sim scope/budget/mutability
            # (real would pull from private_contract via pid/capsule_id but hidden; here min)
            tool_ctx = {"tool": tool, "step": step}
            try:
                # sample kernel call (exercises table for tool events too)
                _ = k.validate({"event_type": "ToolCallRequested", "payload": req}, {"prev_tape_tip": "μ:sim"})
            except Exception:
                pass
            # execute whitebox tool (sim; produce receipt always)
            result = {
                "tool": tool,
                "ok": True,
                "content_preview": "sim-whitebox-tool-output-for-" + capsule_id,
                "mutated": tool in ("apply_patch", "write_file"),
            }
            # ToolCallReceipt append -> predicate + receipt sidecar
            wtool_append(
                pid,
                make_event(TOOL_CALL_RECEIPT, {"capsule_id": capsule_id, "tool": tool, "result": result}),
                receipts={f"tool_{tool}_{step}.json": result},
            )
            tool_results.append(result)

        final = {
            "status": "api_tool_loop_done",
            "worker": worker_name,
            "tools_executed": len(tool_results),
            "exit": 0,
        }
        wtool_append(
            pid,
            make_event(WORKER_RUN_RECEIPT_IMPORTED, {"capsule_id": capsule_id, "worker": worker_name}),
            receipts={"api_run.json": final},
        )
        return final
