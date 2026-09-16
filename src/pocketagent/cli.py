"""PocketAgent's environment-only command line interface."""

import logging
import platform
from typing import cast

import typer
from pydantic import ValidationError

from pocketagent import __version__
from pocketagent.config import Settings
from pocketagent.logging import configure_logging

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="PocketAgent environment bootstrap.",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_enable=False,
)


@app.callback()
def main(ctx: typer.Context) -> None:
    """Load and validate configuration before running a command."""
    try:
        settings = Settings()
    except ValidationError as exc:
        typer.echo(f"Invalid configuration: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    ctx.obj = settings
    configure_logging(settings.log_level)
    logger.debug("Loaded configuration for environment %s", settings.env)


@app.command()
def version() -> None:
    """Show the installed package version."""
    typer.echo(__version__)


@app.command()
def doctor(ctx: typer.Context) -> None:
    """Check that the package and application configuration load."""
    settings = cast(Settings, ctx.obj)
    typer.echo("PocketAgent Environment")
    typer.echo(f"Python:        {platform.python_version()}")
    typer.echo(f"Package:       OK ({__version__})")
    typer.echo(f"Configuration: OK ({settings.env})")
    typer.echo("Status:        READY")
