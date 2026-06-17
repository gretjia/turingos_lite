"""registry.py (P3 atom): Micro project registry. Boot/new/adopt use; convenience locator only (truth = micro tapes)."""

import os
from pathlib import Path

from ..micro.git_tape import MicroGitTape, DEFAULT_DATA_DIR


def _get_data_dir(data_dir: Path | None = None) -> Path:
    if data_dir is None:
        env = os.environ.get("TURINGOS_DATA_DIR")
        return Path(env) if env else DEFAULT_DATA_DIR
    return data_dir


def register_project(project_id: str, macro_path: str | None = None, data_dir: Path | None = None) -> dict:
    """Ensure micro tape for project_id (registry entry). Optional macro locator note (not truth)."""
    if not project_id or not isinstance(project_id, str):
        raise ValueError("project_id must be non-empty str")
    gt = MicroGitTape(project_id, data_dir=_get_data_dir(data_dir))
    tip = gt.init()
    rec = {
        "project_id": project_id,
        "micro_tip": tip,
        "micro_git": str(gt.git_dir),
    }
    if macro_path:
        rec["macro_path"] = str(Path(macro_path).resolve())
    return rec


def list_projects(data_dir: Path | None = None) -> list[str]:
    """Scan data/projects/*/micro.git for registered project_ids."""
    ddir = _get_data_dir(data_dir)
    pbase = ddir / "projects"
    if not pbase.exists():
        return []
    return sorted([p.name for p in pbase.iterdir() if (p / "micro.git").exists()])
