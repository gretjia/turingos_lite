"""project/ (P3): registry, new, adopt, law atoms. Integrates wtool (for Discovered/Ready/InitSpec+Backfilled), rtool reads, kernel preds via appends, per 3.2 flowchart + charter sec12. TUI-projection friendly; dual-tape; scale named."""

from .registry import register_project, list_projects
from .new import create_new_project
from .adopt import adopt_project
from .law import confirm_law

__all__ = ["register_project", "list_projects", "create_new_project", "adopt_project", "confirm_law"]
