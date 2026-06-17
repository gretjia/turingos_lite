"""Launch Vibe TUI: python -m turingos.tui"""
import os
from pathlib import Path

from turingos.tui.app import TuiApp


def main() -> None:
    data_dir = (
        Path(os.environ["TURINGOS_DATA_DIR"])
        if os.environ.get("TURINGOS_DATA_DIR")
        else None
    )
    TuiApp(data_dir=data_dir).run()


if __name__ == "__main__":
    main()