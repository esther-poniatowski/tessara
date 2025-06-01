#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tessara.errors.validation
=========================

Custom exceptions raised during the validation of parameters.

Classes
-------
ValidationError
TypeValidationError
RangeValidationError
PatternValidationError
OptionValidationError
CustomValidationError
RelationValidationError
CheckError
GlobalValidationError
"""
from collections.abc import Mapping, Iterable, Set
import inspect
from typing import Optional, Any, Callable


# --- Base Validation Error ------------------------------------------------------------------------

class ValidationError(Exception):
    """
    Base class for all validation errors, raised when a parameter is invalid.

    Attributes
    ----------
    message : str
        Error message to display if the rule fails. Default: empty string.
    args : tuple
        Arguments passed to the constructor of the base Exception class.

    Methods
    -------
    format_message() -> str
        Formats an error message to display if the rule fails.

    See Also
    --------
    Exception
        Base class for all exceptions in Python.
    """
    def __init__(self, message: Optional[str] = None):
        self.message = message or self.format_message() # subclass method or default implementation
        super().__init__(self.message) # base Exception constructor

    def format_message(self) -> str:
        """
        Formats an error message to provide more context if the rule fails.

        Override in subclasses to introduce dynamic placeholders to fill with runtime value(s) for
        custom default messages.

        Default implementation: Static message.
        """
        return "Invalid value(s)"


# --- Single Value Validation Errors ---------------------------------------------------------------

class TypeValidationError(ValidationError):
    """
    Exception raised when a parameter has an invalid type.

    Examples
    --------
    For a unique expected type:

    >>> raise TypeValidationError(1, str)
    Traceback (most recent call last):
    ...
    TypeValidationError: Type 'int' for value 1, required 'str'.

    For several allowed types:

    >>> raise TypeValidationError(1, (str, float))
    Traceback (most recent call last):
    ...
    TypeValidationError: Type 'int' for value 1, required 'str' or 'float'.
    """
    def __init__(self, value: Any, expected_type: type | tuple[type]):
        self.value = value
        self.expected_type = expected_type
        super().__init__() # call ValidationError constructor

    def format_message(self) -> str:
        expected = "' or '".join(t.__name__ for t in (self.expected_type if isinstance(self.expected_type, tuple) else (self.expected_type,)))
        return f"Type '{type(self.value).__name__}' for value {self.value}, required '{expected}'."


class RangeValidationError(ValidationError):
    """
    Exception raised when a parameter is out of bounds (greater, less, greater or equal, less or
    equal).

    Examples
    --------
    >>> raise RangeValidationError(5, ge=10)
    Traceback (most recent call last):
    ...
    RangeValidationError: Value 5 out of bounds: required >= 10.
    """
    def __init__(self, value: Any, ge: Optional[float]=None, gt: Optional[float]=None, le: Optional[float]=None, lt: Optional[float]=None):
        self.value = value
        self.ge = ge
        self.gt = gt
        self.le = le
        self.lt = lt
        super().__init__() # call ValidationError constructor

    def format_message(self) -> str:
        constraints = [
            f"> {self.gt}" if self.gt is not None else None,
            f">= {self.ge}" if self.ge is not None else None,
            f"< {self.lt}" if self.lt is not None else None,
            f"<= {self.le}" if self.le is not None else None
        ]
        constraints = [c for c in constraints if c]
        return f"Value {self.value} out of bounds: required {' and '.join(constraints)}."


class PatternValidationError(ValidationError):
    """
    Exception raised when a parameter does not match a regular expression.

    Examples
    --------
    >>> raise PatternValidationError("abc", r"\d+")
    Traceback (most recent call last):
    ...
    PatternValidationError: Value 'abc' does not match regex pattern '\d+'.
    """
    def __init__(self, value: Any, pattern: str):
        self.value = value
        self.pattern = pattern
        super().__init__() # call ValidationError constructor

    def format_message(self) -> str:
        return f"Value '{self.value}' does not match regex pattern '{self.pattern}'."


class OptionValidationError(ValidationError):
    """
    Exception raised when a parameter's value does not belong the allowed options.

    Examples
    --------
    >>> raise OptionValidationError("A", ["B", "C"])
    Traceback (most recent call last):
    ...
    OptionValidationError: Value 'A' not among allowed options: ['B', 'C'].
    """
    def __init__(self, value: Any, options: Set[Any]):
        self.value = value
        self.options = set(options)
        super().__init__() # call ValidationError constructor

    def format_message(self) -> str:
        return f"Value '{self.value}' not among allowed options: {self.options}."


class CustomValidationError(ValidationError):
    """
    Exception raised when a custom validation rule fails.

    Examples
    --------
    >>> def is_even(value):
    ...     return value % 2 == 0
    >>> raise CustomValidationError(3, is_even)
    Traceback (most recent call last):
    ...
    CustomValidationError: Value 3 does not satisfy the custom validation function 'is_even'.
    """
    def __init__(self, value: Any, func: Callable[[Any], bool]):
        self.value = value
        self.func = func
        super().__init__() # call ValidationError constructor

    def format_message(self) -> str:
        func_name = self.func.__name__ if hasattr(self.func, "__name__") else repr(self.func)
        return f"Value {self.value} does not satisfy the custom validation function '{func_name}'."


# --- Multiple Value Validation Errors -------------------------------------------------------------

class RelationValidationError(ValidationError):
    """
    Exception raised when a relational validation rule fails (targets multiple parameters).

    Examples
    --------
    >>> def is_greater_than(x, y):
    ...     return x > y

    Pass values as positional arguments:

    >>> raise RelationValidationError(is_greater_than, args=[1, 2])
    Traceback (most recent call last):
    ...
    RelationValidationError: Values do not satisfy the relation when calling `is_greater_than(x=1, y=2)`.

    Pass values as keyword arguments:

    >>> raise RelationValidationError(is_greater_than, kwargs={'x': 1, 'y': 2})
    Traceback (most recent call last):
    ...
    RelationValidationError: Values do not satisfy the relation when calling `is_greater_than(x=1, y=2)`.

    Notes
    -----
    When possible, the function signature is retrieved to format the error message.
    Otherwise, a fallback message is displayed.

    Fallback message occurs when:

    - Function parameters are positional-only but passed as keywords
    - Function uses `*args`/`**kwargs`
    - Signature inspection fails (e.g., built-in functions:, `len`, `max`...)
    - Provided arguments count/names mismatch the function signature

    The function's name is inferred from the `__name__` attribute if available, otherwise it uses
    the `repr()` of the function. This is useful for lambda functions or functions without a name.
    """
    def __init__(self, func: Callable[..., bool],
                 args: Optional[Iterable[Any]] = None,
                 kwargs: Optional[Mapping[str, Any]] = None):
        self.func = func
        self.args = tuple(args) if args else ()
        self.kwargs = dict(kwargs) if kwargs else {}
        super().__init__() # call ValidationError constructor

    def format_message(self) -> str:
        func_name = self.func.__name__ if hasattr(self.func, "__name__") else repr(self.func)
        try: # bind values to function signature

            formatted_args = ", ".join(f"{k}={v!r}" for k, v in bound_args.arguments.items())
            return f"Values do not satisfy the relation when calling `{func_name}({formatted_args})`."
        except (TypeError, ValueError,  AttributeError):  # fallback if binding fails
            return f"Values {self.args or self.kwargs} do not satisfy the relational validation function '{func_name}'."


def bind_function_arguments(func: Callable[..., bool], *args, **kwargs) -> inspect.BoundArguments:
    """
    Bind arguments to a function signature.

    Arguments
    ---------
    func : Callable[..., bool]
        Function to bind arguments to.
    args : Iterable[Any]
        Positional arguments to bind.
    kwargs : Mapping[str, Any]
        Keyword arguments to bind.

    Returns
    -------
    inspect.BoundArguments
        Bound arguments to the function signature.
        Attributes:
            - `args` (tuple): Positional arguments
            - `kwargs` (dict): Keyword arguments.
            - `arguments` (dict): Combined arguments (positional and keyword).
            - `signature` (inspect.Signature): Function signature.
    """
    sig = inspect.signature(func)
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()  # include default parameters for missing arguments
    return bound_args


# --- Aggregate Validation Errors ------------------------------------------------------------------

class CheckError(ValidationError):
    """
    Exception raised when a validation check fails to execute, i.e. no outcome can be determined.

    Attributes
    ----------
    exc : Exception
        Original exception raised during the check execution.
    """
    def __init__(self, exception: Exception):
        self.exception = exception
        super().__init__()

    def format_message(self) -> str:
        return f"Execution failed for validation check: {str(self.exception)}"


class GlobalValidationError(ValidationError):
    """
    Exception raised when at least one error occurred during the validation of multiple parameters.

    Attributes
    ----------
    errors : Iterable[ValidationError]
        Collection of individual validation errors.

    Notes
    -----
    The global message is a concatenation of all individual error messages.
    """
    def __init__(self, errors: Iterable[ValidationError]):
        self.errors = list(errors)
        super().__init__()

    def format_message(self) -> str:
        if not self.errors:
            return "No errors occurred."
        return "\n".join(str(error) for error in self.errors)
