"""git_repo.py (P5): Min Macro Git repo adapter (read-only for observe; whitebox boundary).
Uses subprocess git plumbing. Returns scale-named refs only. Never mutates user's main branch.
Per charter: Macro Tape = existing .git ; observer imports diff/branch/PR as MacroObservationImported.
"""

import subprocess
from pathlib import Path


def get_macro_head(macro_path: str | Path) -> str:
    """Return raw HEAD oid or 'unknown'. Min, matches adopt.py style."""
    mpath = Path(macro_path).resolve()
    try:
        cp = subprocess.run(
            ["git", "-C", str(mpath), "rev-parse", "--verify", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return cp.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def get_diff(macro_path: str | Path, ref: str = "HEAD") -> str:
    """Min diff for observation (post-dispatch evidence)."""
    mpath = Path(macro_path).resolve()
    try:
        cp = subprocess.run(
            ["git", "-C", str(mpath), "diff", "--no-color", f"{ref}~1..{ref}" if ref != "HEAD" else "HEAD~1..HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        d = cp.stdout.strip()
        return d or "+ (no prior commit diff; simulated post-dispatch change)"
    except Exception:
        return "+ (diff unavailable; external Macro evidence)"


def get_branch(macro_path: str | Path) -> str:
    """Current branch name or 'main'."""
    mpath = Path(macro_path).resolve()
    try:
        cp = subprocess.run(
            ["git", "-C", str(mpath), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        b = cp.stdout.strip()
        return b if b and b != "HEAD" else "main"
    except Exception:
        return "main"


def make_macro_ref(project_id: str, oid: str, kind: str = "git") -> str:
    """Canonical scale name per charter 1.3. Never bare oid."""
    if not project_id:
        project_id = "demo_app"
    oid = oid or "HEAD"
    if kind == "git":
        return f"macro:git:{project_id}:{oid}"
    if kind == "pr":
        return f"macro:pr:local/{project_id}#{oid}"
    return f"macro:{kind}:{project_id}:{oid}"
