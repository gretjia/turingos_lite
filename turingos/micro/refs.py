"""Ref helpers for tape and accepted (used by git_tape, wtool, rtool). Pure git plumbing."""

import subprocess
from pathlib import Path

from ..core.errors import MicroGitError


def get_ref(git_dir: Path, ref: str) -> str | None:
    """Return raw oid for ref or None if absent."""
    try:
        cp = subprocess.run(
            ["git", "--git-dir", str(git_dir), "rev-parse", "--verify", ref],
            capture_output=True,
            text=True,
            check=True,
        )
        return cp.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def update_ref(git_dir: Path, ref: str, oid: str) -> None:
    """Update (create) the ref to point at oid. Creates ref if absent."""
    try:
        subprocess.run(
            ["git", "--git-dir", str(git_dir), "update-ref", ref, oid],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise MicroGitError(f"update-ref {ref} failed: {e.stderr or e}") from e
