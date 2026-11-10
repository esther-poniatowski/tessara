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

Notes
-----
The options follow the command-line conventions of the workspace: `-v`, `--version` prints the
version, and a usage error exits with status 2.
"""

import typer
from . import info, __version__

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command("info")
def cli_info() -> None:
    """Display version and platform diagnostics."""
    typer.echo(info())


def _print_version(value: bool) -> None:
    """Print the version string and exit before any command is required.

    Parameters
    ----------
    value : bool
        Whether the option `-v`, `--version` is present.
    """
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=_print_version,
        is_eager=True,
        help="Show the package version and exit.",
    )
) -> None:
    """Root command for the package command-line interface.

    Parameters
    ----------
    version : bool
        Print the version string and exit; handled eagerly by `_print_version`.
    """
