#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialization logic and public interface for the `tessara` package.

Variables
---------
__version__ : str, default "0.0.0+unknown"
    Version of the package (PEP 440 compliant). If the package is not installed via a package
    manager, a default fallback value is used (e.g. for development environments, where the package
    is run directly from the source code).
__all__ : list
    Public objects exposed by this package.

Modules
-------
None declared at the top level.

Functions
---------
info() -> str
    Format diagnostic information about the package and platform.

Examples
--------
To run a minimal diagnostic after installation from the command line:

    $ python -m tessara
    tessara, version: 0.1.0
    Platform: Linux - 3.11.5

To programmatically retrieve the package version:

    >>> import tessara
    >>> tessara.__version__
    '0.1.0'

See Also
--------
importlib.metadata.version
    Function to retrieve the version of a package.
PackageNotFoundError
    Exception raised when the package is not found in the environment.
"""
from importlib.metadata import version, PackageNotFoundError
import platform

try:
    __version__ = version(__package__)
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = []


def info() -> str:
    """Format diagnostic information on package and platform."""
    return f"{__package__}, version: {__version__}\n" \
           f"Platform: {platform.system()} - {platform.python_version()}"


if __name__ == "__main__":
    print(info())
