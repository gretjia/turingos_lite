"""Scoped whitebox file tools — every call returns a typed receipt dict."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any


class WhiteboxScope:
    """Restrict tool I/O to a macro repo root."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _resolve(self, rel: str) -> Path:
        p = (self.root / (rel or ".")).resolve()
        if self.root not in p.parents and p != self.root:
            raise PermissionError(f"path outside repo: {rel}")
        return p


def read_file(scope: WhiteboxScope, path: str, *, max_bytes: int = 64_000) -> dict[str, Any]:
    p = scope._resolve(path)
    if not p.is_file():
        return {"ok": False, "error": f"not a file: {path}"}
    data = p.read_bytes()[:max_bytes]
    return {"ok": True, "path": str(p.relative_to(scope.root)), "content": data.decode(errors="replace")}


def list_dir(scope: WhiteboxScope, path: str = ".", *, max_entries: int = 40) -> dict[str, Any]:
    p = scope._resolve(path)
    if not p.is_dir():
        return {"ok": False, "error": f"not a directory: {path}"}
    entries = sorted(x.name for x in p.iterdir())[:max_entries]
    return {"ok": True, "path": str(p.relative_to(scope.root)), "entries": entries}


def grep(scope: WhiteboxScope, pattern: str, path: str = ".", *, max_matches: int = 20) -> dict[str, Any]:
    root = scope._resolve(path)
    try:
        r = subprocess.run(
            ["rg", "-n", "--max-count", str(max_matches), pattern, str(root)],
            capture_output=True,
            text=True,
            timeout=8,
            cwd=scope.root,
        )
        out = (r.stdout or "").strip()
        return {"ok": True, "matches": out.splitlines() if out else [], "exit": r.returncode}
    except FileNotFoundError:
        return {"ok": False, "error": "rg not installed"}


def write_file(scope: WhiteboxScope, path: str, content: str, *, append: bool = False) -> dict[str, Any]:
    p = scope._resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with open(p, mode, encoding="utf-8") as f:
        f.write(content)
    return {"ok": True, "path": str(p.relative_to(scope.root)), "bytes": len(content.encode()), "mutated": True}


def apply_patch(scope: WhiteboxScope, path: str, old: str, new: str) -> dict[str, Any]:
    p = scope._resolve(path)
    if not p.is_file():
        return {"ok": False, "error": f"not a file: {path}"}
    text = p.read_text(encoding="utf-8", errors="replace")
    if old not in text:
        return {"ok": False, "error": "old snippet not found", "path": path}
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    return {"ok": True, "path": str(p.relative_to(scope.root)), "mutated": True}


def run_tool(scope: WhiteboxScope, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool == "read_file":
        return read_file(scope, args.get("path", "README.md"))
    if tool == "list_dir":
        return list_dir(scope, args.get("path", "."))
    if tool == "grep":
        return grep(scope, args.get("pattern", "."), path=args.get("path", "."))
    if tool == "write_file":
        return write_file(
            scope,
            args["path"],
            args.get("content", ""),
            append=bool(args.get("append")),
        )
    if tool == "apply_patch":
        return apply_patch(scope, args["path"], args.get("old", ""), args.get("new", ""))
    if tool == "run_command":
        cmd = args.get("command", "")
        if not cmd:
            return {"ok": False, "error": "empty command"}
        try:
            r = subprocess.run(
                cmd,
                shell=True,
                cwd=scope.root,
                capture_output=True,
                text=True,
                timeout=int(args.get("timeout", 30)),
            )
            return {
                "ok": r.returncode == 0,
                "exit": r.returncode,
                "stdout": (r.stdout or "")[:2000],
                "stderr": (r.stderr or "")[:1000],
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
    return {"ok": False, "error": f"unknown tool: {tool}"}


def infer_target_path(task: str, root: Path) -> str | None:
    """Best-effort path guess from natural language."""
    m = re.search(r"([\w./-]+\.py)\b", task)
    if m:
        rel = m.group(1)
        if (root / rel).is_file():
            return rel
    for name in ("turingos/cli.py", "turingos/config.py", "README.md"):
        if (root / name).is_file():
            return name
    return None