"""Main Typer application: assembles all commands into the CLI."""

from __future__ import annotations

from typing import Optional

import typer

from podifyr import __version__
from podifyr.cli.commands.cache_cmd import cache_clear, cache_stats
from podifyr.cli.commands.config_cmd import config_init, config_show
from podifyr.cli.commands.generate import generate
from podifyr.cli.display import console


# ─── Main App ────────────────────────────────────────────────────────────────

app = typer.Typer(
    name="podifyr-ai",
    help="Generate podcast-style audio walkthroughs of Python codebases.",
    no_args_is_help=True,
    add_completion=True,
    rich_markup_mode="rich",
)

# ─── Sub-command Groups ──────────────────────────────────────────────────────

config_app = typer.Typer(
    name="config",
    help="Manage podifyr configuration.",
    no_args_is_help=True,
)

cache_app = typer.Typer(
    name="cache",
    help="Manage the podifyr cache.",
    no_args_is_help=True,
)


# ─── Version Callback ────────────────────────────────────────────────────────


def _version_callback(value: bool) -> None:
    """Print version information and exit."""
    if value:
        console.print(f"[bold blue]podifyr-ai[/bold blue] v{__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(  # noqa: UP007
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Podifyr: Automated developer onboarding via AI-powered podcast walkthroughs."""


# ─── Register Commands ───────────────────────────────────────────────────────

# Main generate command
app.command(name="generate", help="Generate a podcast walkthrough of a Python repository.")(
    generate
)

# Config sub-commands
config_app.command(name="init", help="Initialize a .env configuration file.")(config_init)
config_app.command(name="show", help="Display current resolved configuration.")(config_show)
app.add_typer(config_app)

# Cache sub-commands
cache_app.command(name="clear", help="Clear all cached data.")(cache_clear)
cache_app.command(name="stats", help="Show cache usage statistics.")(cache_stats)
app.add_typer(cache_app)


if __name__ == "__main__":
    app()
