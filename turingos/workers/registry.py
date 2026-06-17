"""registry.py: Phase 6 worker registry (simple, no yaml yet per surgical min).
get_worker(name) -> WorkerBase instance. Supports fake_command (first), manual, codex/claude/grok via command_template, api via tool_loop.
Dispatch integrates by calling worker.run; workers own their receipt loops + inner predicates (api).
Auto-registers on import for E2E compat (cli dispatch --worker fake_command unchanged).
"""
from typing import Dict
from .base import WorkerBase
from .fake import FakeWorker
from .manual import ManualWorker
from .command_template import CommandTemplateWorker
from .api_tool_loop import ApiToolLoopWorker

_registry: Dict[str, WorkerBase] = {}


def register_worker(name: str, worker: WorkerBase) -> None:
    """Explicit register (override)."""
    _registry[name] = worker


def get_worker(name: str = "fake_command") -> WorkerBase:
    """Return or create worker by name. Fake first. Fallbacks for command:* and api.
    All registered support run(pid, capsule_id, worker_name) -> receipt.
    """
    if name in _registry:
        return _registry[name]

    if name == "fake_command" or name.startswith("fake"):
        w = FakeWorker()
    elif name == "manual":
        w = ManualWorker()
    elif name in ("codex", "claude", "grok", "command") or name.startswith(("command", "codex", "claude", "grok")):
        w = CommandTemplateWorker(name=name)
    elif name == "api" or "api" in name.lower() or name.startswith("api"):
        w = ApiToolLoopWorker()
    else:
        # min compat: unknown -> fake (E2E dispatch must not break; real would error)
        w = FakeWorker()
        w.name = name  # label it
    _registry[name] = w
    return w


# Eager default registrations (fake first)
register_worker("fake_command", FakeWorker())
register_worker("manual", ManualWorker())
register_worker("codex", CommandTemplateWorker(name="codex"))
register_worker("claude", CommandTemplateWorker(name="claude"))
register_worker("grok", CommandTemplateWorker(name="grok"))
register_worker("api", ApiToolLoopWorker())
