"""Basic CLI entrypoint for TuringOS Lite (Phase 0 scaffold)."""

import typer

app = typer.Typer(
    name="turing",
    help="TuringOS Lite - Dual Git Tape Agentic Workbench (Software 3.0)",
    add_completion=False,
)


@app.command()
def boot():
    """Bootstrap local config and Micro project registry."""
    typer.echo("Bootstrapping TuringOS Lite harness...")


@app.command()
def new(name: str):
    """Create a new project (Meta AI proposes InitSpec + MicroPredicate)."""
    typer.echo(f"Creating new project: {name}")


@app.command()
def adopt(path: str = "."):
    """Adopt existing repo (observe Macro, propose BackfilledSpec)."""
    typer.echo(f"Adopting project at: {path}")


@app.command()
def intent(task: str):
    """Capture user intent (appends IntentCaptured to Micro Tape)."""
    typer.echo(f"Capturing intent: {task}")


@app.command()
def tui():
    """Launch the projection-only TUI."""
    typer.echo("Launching TuringOS Lite TUI (projection mode)...")


@app.command()
def audit(scope: str = "all"):
    """Run architecture audits (flowcharts, invariants, e2e)."""
    typer.echo(f"Running audits: {scope}")


if __name__ == "__main__":
    app()
