"""turingos.tui: projection-only TUI per charter FC-A10, section 12/9. Exports app."""
from .app import TuiApp  # re-export for cli import and tests

__all__ = ["TuiApp"]
