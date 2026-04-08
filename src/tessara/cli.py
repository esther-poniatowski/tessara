"""
Command-line interface for the `tessara` package.

Defines commands available via `python -m tessara` or `tessara` if installed as a script.

See Also
--------
typer.Typer
    Library for building CLI applications: https://typer.tiangolo.com/

Functions
---------
cli_info
    Display version and platform diagnostics.
main_callback
    Root command for the package command-line interface.
"""

import typer
from . import info, __version__

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command("info")
def cli_info() -> None:
    """Display version and platform diagnostics."""
    typer.echo(info())


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show the package version and exit."
    )
) -> None:
    """Root command for the package command-line interface.

    Parameters
    ----------
    version : bool
        Print the version string and exit.
    """
    if version:
        typer.echo(__version__)
        raise typer.Exit()
