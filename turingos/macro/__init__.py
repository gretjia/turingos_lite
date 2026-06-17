"""P5 Macro (git_repo + worktree + observer + anchors + completion_contract) per charter sec12 + 3.10 Macro Completion Contract + 3.5 + 5.macro/.
Surgical: min adapters. Dual independent tapes. Every macro id names scale (macro:git:..., macro:pr:...).
Observer imports to Micro as MacroObservationImported ONLY (FC-A02). Uses wtool (predicate gate), rtool.
TUI projection reads only. No direct Macro main writes; worktree for isolation.
"""

from .git_repo import get_macro_head, get_diff, get_branch, make_macro_ref
from .worktree import ensure_worktree
from .observer import import_macro_observation
from .anchors import make_macro_anchor
from .completion_contract import (
    validate_macro_completion_contract,
    parse_macro_completion_contract,
    make_completion_contract,
)

__all__ = [
    "get_macro_head",
    "get_diff",
    "get_branch",
    "make_macro_ref",
    "ensure_worktree",
    "import_macro_observation",
    "make_macro_anchor",
    "validate_macro_completion_contract",
    "parse_macro_completion_contract",
    "make_completion_contract",
]
