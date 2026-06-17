"""worktree.py (P5): Macro worktree manager (charter 1.2: <macro>/.turingos/worktrees/<capsule_id>).
Git worktree for parallel/isolated Macro work per AGENTS + research (context firewall).
Min surgical: create on demand; detach to avoid branch pollution. Fallback mkdir if git worktree unavailable.
"""

import subprocess
from pathlib import Path


def ensure_worktree(macro_path: str | Path, capsule_id: str) -> str:
    """Ensure worktree dir for capsule. Return absolute path str.
    Uses git worktree add --detach (isolated HEAD). Safe for tests with temp macro git.
    """
    mpath = Path(macro_path).resolve()
    if not capsule_id:
        capsule_id = "wc_unknown"
    wt_root = mpath / ".turingos" / "worktrees"
    wt_root.mkdir(parents=True, exist_ok=True)
    wt_path = wt_root / capsule_id
    if wt_path.exists():
        return str(wt_path)
    try:
        # --detach + force to create clean isolated tree from current HEAD (no main side effects)
        subprocess.run(
            ["git", "-C", str(mpath), "worktree", "add", "--detach", "--force", str(wt_path), "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        # min fallback (e.g. shallow test git or no worktree support): just ensure dir for capsule isolation
        wt_path.mkdir(parents=True, exist_ok=True)
    return str(wt_path)
