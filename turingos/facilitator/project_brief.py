"""Deterministic project background for Facilitator on TUI mount."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from turingos.config import load_facilitator_config, load_meta_config
from turingos.micro.reducer import reduce_state


def _read_excerpt(path: Path, max_lines: int = 40) -> str:
    if not path.is_file():
        return ""
    try:
        lines = path.read_text(errors="replace").splitlines()[:max_lines]
        return "\n".join(lines)
    except Exception:
        return ""


def _git(args: list[str], cwd: Path) -> str:
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return (r.stdout or "").strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def format_project_cognition(brief: dict[str, Any]) -> str:
    """Human-readable project snapshot for TUI + Facilitator summaries."""
    if not brief:
        return "（暂无项目背景）"
    lines: list[str] = []
    pid = brief.get("project_id", "?")
    lines.append(f"- **项目**: {pid}")
    cwd = brief.get("cwd")
    if cwd:
        lines.append(f"- **路径**: `{cwd}`")
    if brief.get("has_git"):
        lines.append("- **Git**: 已连接")
        remote = brief.get("github_remote")
        if remote:
            lines.append(f"- **Remote**: `{remote}`")
        head = brief.get("macro_head")
        if head:
            lines.append(f"- **Macro head**: `{head}`")
        commits = brief.get("recent_commits") or []
        if commits:
            lines.append("- **最近 commit**:")
            for c in commits[:5]:
                lines.append(f"  - `{c}`")
    else:
        lines.append("- **Git**: 未检测到")
    dirs = brief.get("top_level_dirs") or []
    if dirs:
        lines.append(f"- **顶层目录**: {', '.join(dirs)}")
    readme = (brief.get("readme_excerpt") or "").strip()
    if readme:
        one_line = " ".join(readme.split())[:360]
        lines.append(f"- **README**: {one_line}…")
    cfg = brief.get("config_status") or {}
    lines.append(
        f"- **AI 配置**: Facilitator={cfg.get('facilitator', '?')}, "
        f"Meta={cfg.get('meta_ai', '?')}, model={cfg.get('facilitator_model', '?')}"
    )
    tip = brief.get("micro_tape_tip")
    if tip:
        lines.append(f"- **Micro tape tip**: `{tip}`")
    caps = brief.get("open_capsules") or []
    if caps:
        lines.append(f"- **Open capsules**: {', '.join(caps)}")
    return "\n".join(lines)


def build_project_brief(
    project_id: str,
    cwd: Path | None = None,
    data_dir: Path | None = None,
) -> dict[str, Any]:
    """Whitebox project snapshot (no secrets). Fed to Facilitator user context."""
    cwd = cwd or Path.cwd()
    projection = reduce_state(project_id, data_dir=data_dir)
    has_git = (cwd / ".git").exists()
    has_turingos = (cwd / ".turingos").exists()
    remote = _git(["remote", "get-url", "origin"], cwd) if has_git else ""
    head = _git(["rev-parse", "HEAD"], cwd) if has_git else ""
    log = _git(["log", "-5", "--oneline"], cwd) if has_git else ""
    top_dirs = []
    try:
        top_dirs = sorted(
            p.name for p in cwd.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        )[:12]
    except Exception:
        pass

    fac_cfg = load_facilitator_config()
    meta_cfg = load_meta_config()
    return {
        "project_id": project_id,
        "cwd": str(cwd),
        "has_git": has_git,
        "has_turingos": has_turingos,
        "github_remote": remote,
        "macro_head": f"macro:git:{project_id}:{head[:12]}" if head else "",
        "readme_excerpt": _read_excerpt(cwd / "README.md"),
        "pyproject_excerpt": _read_excerpt(cwd / "pyproject.toml", 30),
        "top_level_dirs": top_dirs,
        "recent_commits": log.splitlines() if log else [],
        "micro_tape_tip": projection.get("tape_tip"),
        "open_capsules": projection.get("open_capsules", []),
        "project_status": projection.get("project_status"),
        "config_status": {
            "facilitator": "ok" if fac_cfg.get("api_key") else "missing",
            "meta_ai": "ok" if meta_cfg.get("api_key") else "missing",
            "facilitator_model": fac_cfg.get("model", "mock"),
        },
    }