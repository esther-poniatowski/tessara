"""
Entry point for the `tessara` package, invoked as a module.

Usage
-----
To launch the command-line interface, execute::

    python -m tessara


See Also
--------
tessara.cli: Module implementing the application's command-line interface.
"""
from .cli import app

app()
