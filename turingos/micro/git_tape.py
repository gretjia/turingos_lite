"""MicroGitTape per A01: init bare, refs, genesis SystemBootstrapped using git plumbing only. Controlled env, clear errors."""

import os
import subprocess
from pathlib import Path

from ..core.errors import MicroGitError
from ..core.ids import make_micro_id
from .refs import get_ref, update_ref
from .commit_builder import append_commit
from ..events import make_event, SYSTEM_BOOTSTRAPPED


DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "turingos"


def get_micro_git_dir(project_id: str, data_dir: Path | None = None) -> Path:
    """Compute location per charter 1.2 physical layout. Override via TURINGOS_DATA_DIR for tests/controlled."""
    if data_dir is None:
        env_dir = os.environ.get("TURINGOS_DATA_DIR")
        data_dir = Path(env_dir) if env_dir else DEFAULT_DATA_DIR
    return data_dir / "projects" / project_id / "micro.git"


class MicroGitTape:
    """A01 impl. git init --bare + tape/accepted + genesis commit if new."""

    def __init__(self, project_id: str, data_dir: Path | None = None):
        if not project_id or not isinstance(project_id, str):
            raise MicroGitError("project_id must be non-empty str")
        self.project_id = project_id
        self.git_dir = get_micro_git_dir(project_id, data_dir)

    def init(self) -> str:
        """Ensure bare repo, tape/accepted refs, genesis SystemBootstrapped commit if tape absent. Return current μ:tape_tip."""
        git_dir = self.git_dir
        try:
            if not git_dir.exists():
                git_dir.mkdir(parents=True, exist_ok=True)
                # git init --bare
                subprocess.run(
                    ["git", "init", "--bare", str(git_dir)],
                    capture_output=True,
                    text=True,
                    check=True,
                    env={"GIT_AUTHOR_NAME": "TuringOS", "GIT_AUTHOR_EMAIL": "turingos@localhost"},
                )
                # user config (plumbing)
                subprocess.run(
                    ["git", "--git-dir", str(git_dir), "config", "user.name", "TuringOS"],
                    capture_output=True, check=True
                )
                subprocess.run(
                    ["git", "--git-dir", str(git_dir), "config", "user.email", "turingos@localhost"],
                    capture_output=True, check=True
                )

            tape_ref = "refs/heads/tape"
            accepted_ref = "refs/heads/accepted"

            tape_tip = get_ref(git_dir, tape_ref)
            if not tape_tip:
                # genesis per A01
                genesis = make_event(
                    SYSTEM_BOOTSTRAPPED,
                    payload={
                        "project_id": self.project_id,
                        "turingos_version": "v1.0-lite",
                    },
                )
                # append_commit creates the commit; we set refs after
                oid = append_commit(
                    git_dir,
                    parent=None,
                    event=genesis,
                    source="turingos:system",
                    issuer="system",
                )
                update_ref(git_dir, tape_ref, oid)
                update_ref(git_dir, accepted_ref, oid)
                tape_tip = oid

            # ensure accepted ref exists (points at something)
            if not get_ref(git_dir, accepted_ref):
                update_ref(git_dir, accepted_ref, tape_tip)

            return make_micro_id(tape_tip)
        except Exception as e:
            if isinstance(e, MicroGitError):
                raise
            raise MicroGitError(f"MicroGitTape.init failed for {self.project_id}: {e}") from e

    def fsck(self) -> bool:
        """Helper for test acceptance: run git fsck --full , return True if clean."""
        import subprocess
        try:
            cp = subprocess.run(
                ["git", "--git-dir", str(self.git_dir), "fsck", "--full", "--strict"],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False
