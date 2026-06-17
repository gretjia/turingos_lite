"""Build temp tree + commit-tree using ONLY git CLI plumbing (subprocess). Per A02."""

import json
import subprocess
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from ..core.hashing import payload_hash, canonical_json
from ..core.ids import make_micro_id
from ..core.errors import MicroGitError
from ..events import make_event


def _git_env() -> dict:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "TuringOS"
    env["GIT_AUTHOR_EMAIL"] = "turingos@localhost"
    env["GIT_COMMITTER_NAME"] = "TuringOS"
    env["GIT_COMMITTER_EMAIL"] = "turingos@localhost"
    return env


def _run_plumbing(git_dir: Path, args: list[str], input_data: bytes | None = None) -> str:
    """Run git --git-dir ... ; return stdout stripped. Raise on fail with clear msg."""
    cmd = ["git", "--git-dir", str(git_dir)] + args
    try:
        cp = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            env=_git_env(),
            check=True,
        )
        return cp.stdout.decode("utf-8", errors="replace").strip()
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"").decode("utf-8", errors="replace").strip()
        raise MicroGitError(f"git {' '.join(args)} failed: {err}") from e


def _hash_blob(git_dir: Path, content: str | bytes) -> str:
    data = content if isinstance(content, bytes) else content.encode("utf-8")
    return _run_plumbing(git_dir, ["hash-object", "-w", "--stdin"], input_data=data)


def _mktree(git_dir: Path, tree_lines: str) -> str:
    """tree_lines: '100644 blob SHA\tname\n040000 tree SHA\tsubdir\n' """
    return _run_plumbing(git_dir, ["mktree"], input_data=tree_lines.encode("utf-8"))


def append_commit(
    git_dir: Path,
    parent: str | None,
    event: dict,
    source: str = "turingos:cli",
    issuer: str = "system",
    receipts: dict | None = None,
    anchors: dict | None = None,
) -> str:
    """
    Core A02 impl: build temp tree containing node.json + payload.json + optional receipts/* anchors/* .
    git commit-tree (with parent if any). Return the new commit oid (caller does ref updates).
    node.json envelope populated with knowns + placeholder event_id resolved by rtool on load.
    """
    if not git_dir.exists():
        raise MicroGitError(f"micro.git not found at {git_dir}")

    event_type = event["event_type"]
    payload = event.get("payload", {})

    phash = payload_hash(payload)
    now = datetime.now(timezone.utc).isoformat()

    # Build envelope without final self event_id (circular with commit oid); rtool injects event_id=μ:oid on load.
    # This keeps pure immutable git commits, satisfies read json + scale naming (id from commit itself).
    # All other required fields present.
    envelope = {
        "event_id": "μ:PENDING",  # resolved at load to μ:<this-oid>
        "schema_version": "micro_envelope_v1",
        "event_type": event_type,
        "scale": "micro",
        "prev_tape_tip": event.get("prev_tape_tip"),
        "accepted_head_before": event.get("accepted_head_before"),
        "parent_hashes": event.get("parent_hashes", []),
        "payload_hash": phash,
        "source": source,
        "issuer": issuer,
        "issued_at": now,
        "signature_route": event.get("signature_route", "unsigned"),
        "replay_rule": event.get("replay_rule", "append_only"),
    }

    with TemporaryDirectory(prefix="turingos-micro-tree-") as td:
        tdir = Path(td)
        # Write node.json and payload.json at root of tree
        (tdir / "node.json").write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
        (tdir / "payload.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

        # Optional receipts/ dir (multiple .json)
        if receipts:
            rdir = tdir / "receipts"
            rdir.mkdir()
            for fname, rcontent in receipts.items():
                if not fname.endswith(".json"):
                    fname += ".json"
                (rdir / fname).write_text(json.dumps(rcontent, indent=2, sort_keys=True) + "\n")

        # Optional anchors/ dir
        if anchors:
            adir = tdir / "anchors"
            adir.mkdir()
            for fname, acontent in anchors.items():
                if not fname.endswith(".json"):
                    fname += ".json"
                (adir / fname).write_text(json.dumps(acontent, indent=2, sort_keys=True) + "\n")

        # Build tree objects via plumbing: first hash all blobs, build subtrees, top mktree
        # node.json
        node_blob = _hash_blob(git_dir, (tdir / "node.json").read_bytes())
        # payload.json
        payload_blob = _hash_blob(git_dir, (tdir / "payload.json").read_bytes())

        tree_spec = f"100644 blob {node_blob}\tnode.json\n100644 blob {payload_blob}\tpayload.json\n"

        # receipts subtree if present
        if receipts:
            rec_lines = ""
            for f in (tdir / "receipts").iterdir():
                if f.is_file():
                    bsha = _hash_blob(git_dir, f.read_bytes())
                    rec_lines += f"100644 blob {bsha}\t{f.name}\n"
            rec_tree = _mktree(git_dir, rec_lines)
            tree_spec += f"040000 tree {rec_tree}\treceipts\n"

        # anchors subtree
        if anchors:
            anc_lines = ""
            for f in (tdir / "anchors").iterdir():
                if f.is_file():
                    bsha = _hash_blob(git_dir, f.read_bytes())
                    anc_lines += f"100644 blob {bsha}\t{f.name}\n"
            anc_tree = _mktree(git_dir, anc_lines)
            tree_spec += f"040000 tree {anc_tree}\tanchors\n"

        tree_sha = _mktree(git_dir, tree_spec)

        # commit-tree
        commit_args = ["commit-tree", tree_sha]
        if parent:
            commit_args += ["-p", parent]
        # message uses event_type for human readability in git log
        commit_args += ["-m", f"micro:{event_type}"]

        new_oid = _run_plumbing(git_dir, commit_args)

    return new_oid
