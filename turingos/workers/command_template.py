"""command_template.py: Command-template Workers for codex exec, Claude CLI, Grok Build (charter 4.1, 1.5).
Blackbox external bundles: TuringOS adapter only (timeout, receipt, observer boundary).
Templates map --worker codex|claude|grok|command:* -> subprocess (simulated for harness; real cmd would exec outside).
Every dispatch produces WORKER_* receipt. No internal tools (partial provenance).
"""
import shlex
import subprocess
from ..events import make_event, WORKER_DISPATCH_PREPARED, WORKER_RUN_RECEIPT_IMPORTED
from ..micro.wtool import append as wtool_append
from .base import WorkerBase


class CommandTemplateWorker(WorkerBase):
    """Templated command worker impls for external agent CLIs.
    Simplicity: echo-sim for E2E; production would use real binaries + sandbox.
    """

    name = "command"
    TEMPLATES = {
        "codex": "echo 'CODEX-EXEC simulated for capsule={capsule}'",
        "claude": "echo 'CLAUDE-CLI simulated --capsule {capsule}'",
        "grok": "echo 'GROK-BUILD simulated --from {capsule}'",
        "command": "echo 'GENERIC-COMMAND simulated {capsule}'",
    }

    def __init__(self, name: str | None = None):
        super().__init__(name=name)
        key = (name or "codex").split(":")[-1] if name else "codex"
        self.template = self.TEMPLATES.get(key, self.TEMPLATES["codex"])
        if name:
            self.name = name

    def run(self, pid: str, capsule_id: str, worker_name: str | None = None) -> dict:
        wname = worker_name or self.name
        wtool_append(
            pid,
            make_event(WORKER_DISPATCH_PREPARED, {"capsule_id": capsule_id, "worker": wname}),
        )
        self._append_run_started(pid, capsule_id)

        cap_path = f".turingos/capsules/{capsule_id}.md"
        cmd_str = self.template.format(capsule=cap_path)
        try:
            cmd = shlex.split(cmd_str)
            cp = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            out = (cp.stdout or cp.stderr or "ok").strip()[:256]
            exit_code = cp.returncode
        except Exception as e:  # pragma: no cover (sim)
            out = f"template-err:{type(e).__name__}"
            exit_code = 1

        receipt = {
            "status": "command_template_done" if exit_code == 0 else "command_template_fail",
            "worker": wname,
            "output": out,
            "exit": exit_code,
            "template": self.template[:64],
        }
        wtool_append(
            pid,
            make_event(WORKER_RUN_RECEIPT_IMPORTED, {"capsule_id": capsule_id, "worker": wname}),
            receipts={"command.json": receipt},
        )
        return receipt
