"""workers/ (Phase 6 per charter sec12 workers/, 3.4, 3.5, 6.).
Registry + base + impls: fake (focus first per order), manual, command_template (codex/claude/grok), api_tool_loop (Tool Predicate inner loop).
Surgical adapter layer only: dispatch calls worker; workers emit Worker*/Tool* via wtool (predicate gate, receipts, failure appends).
External bundles blackbox (1.5); api whitebox tools every call -> receipt.
No files outside workers/ + cli dispatch + tests touched.
"""
from .registry import get_worker, register_worker
from .base import WorkerBase
from .fake import FakeWorker
from .manual import ManualWorker
from .command_template import CommandTemplateWorker
from .api_tool_loop import ApiToolLoopWorker

__all__ = [
    "get_worker",
    "register_worker",
    "WorkerBase",
    "FakeWorker",
    "ManualWorker",
    "CommandTemplateWorker",
    "ApiToolLoopWorker",
]
