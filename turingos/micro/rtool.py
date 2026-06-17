"""rtool reads + load per A03. Projection only (FC-A10)."""

import json
import subprocess
from pathlib import Path

from ..core.ids import make_micro_id, strip_micro_id
from ..core.errors import MicroGitError
from .git_tape import MicroGitTape, get_micro_git_dir
from .refs import get_ref
from ..predicates.kernel import PredicateKernel  # Phase2 integrate: rtool reads nodes incl MicroPredicateResult (projection of kernel results)


def _git_show(git_dir: Path, rev_path: str) -> str:
    """git show <rev>:<path> for bare repo content."""
    try:
        cp = subprocess.run(
            ["git", "--git-dir", str(git_dir), "show", rev_path],
            capture_output=True,
            text=True,
            check=True,
        )
        return cp.stdout
    except subprocess.CalledProcessError as e:
        raise MicroGitError(f"git show {rev_path} failed: {e.stderr or e}") from e


class MicroRtool:
    """A03: read_tip, read_accepted_head, iter_commits, load_node(oid) reading the json files."""

    def __init__(self, project_id: str, data_dir: Path | None = None):
        self.project_id = project_id
        self.git_dir = get_micro_git_dir(project_id, data_dir)

    def read_tip(self) -> str | None:
        oid = get_ref(self.git_dir, "refs/heads/tape")
        return make_micro_id(oid) if oid else None

    def read_accepted_head(self) -> str | None:
        oid = get_ref(self.git_dir, "refs/heads/accepted")
        return make_micro_id(oid) if oid else None

    def iter_commits(self, ref: str = "refs/heads/tape") -> list[str]:
        """Return list of oids oldest->newest (chronological)."""
        try:
            cp = subprocess.run(
                ["git", "--git-dir", str(self.git_dir), "rev-list", "--reverse", ref],
                capture_output=True,
                text=True,
                check=True,
            )
            oids = [line.strip() for line in cp.stdout.splitlines() if line.strip()]
            return oids
        except subprocess.CalledProcessError:
            return []

    def load_node(self, oid: str) -> dict:
        """Read node.json + payload.json from the commit tree. Inject canonical event_id=μ:oid . (MicroPredicateResult nodes from kernel are loaded here for TUI/replay)."""
        _ = PredicateKernel  # referenced for integration (no-op; kernel used in append paths)
        raw_oid = strip_micro_id(oid)
        try:
            node_txt = _git_show(self.git_dir, f"{raw_oid}:node.json")
            node = json.loads(node_txt)
            payload_txt = _git_show(self.git_dir, f"{raw_oid}:payload.json")
            payload = json.loads(payload_txt)
        except Exception as e:
            raise MicroGitError(f"load_node({oid}) failed reading json files: {e}") from e

        # Always authoritative event_id from the commit oid itself (scale correct, resolves pending)
        node["event_id"] = make_micro_id(raw_oid)
        node["payload"] = payload  # embed for convenience in reducer/audit
        return node
