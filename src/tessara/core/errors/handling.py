"""
tessara.errors.handling
=======================

Custom exceptions raised during parameter manipulation.

Classes
-------
MissingValueError
OverrideParameterError
UnknownParameterError
"""

from tessara.core.errors.validation import ValidationError


# --- ParameterSet Errors --------------------------------------------------------------------------

class MissingValueError(ValidationError):
    """
    Exception raised when a parameter is missing.
    """
    pass

class OverrideParameterError(Exception):
    """
    Exception raised when a parameter is overridden in a ParameterSet.
    """
    pass

class UnknownParameterError(KeyError):
    """
    Exception raised when a parameter name is not found in a ParameterSet.
    """
    pass
