import typer

app = typer.Typer(
    help="b2gx — Blast2GO-style functional annotation pipeline.",
    no_args_is_help=True,
    add_completion=True,
)


@app.command("version")
def version() -> None:
    """Print the b2gx version."""
    from b2gx import __version__

    typer.echo(__version__)


# Placeholder so Typer keeps the multi-command layout even before other
# subcommands are wired in (prevents Typer from collapsing to a single-command
# app and swallowing the subcommand name).
@app.command("info", hidden=True)
def _info() -> None:
    """Show build info (placeholder)."""
    typer.echo("b2gx info — not yet implemented.")


if __name__ == "__main__":
    app()
