"""Phase 0 smoke test per charter atom P0-M0-A01."""

from typer.testing import CliRunner
from turingos.cli import app

runner = CliRunner()


def test_help_exits_cleanly():
    """Basic smoke: --help should succeed (per charter acceptance)."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "TuringOS Lite" in result.output or "turing" in result.output.lower()
