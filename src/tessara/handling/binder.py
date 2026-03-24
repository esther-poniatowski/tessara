"""
tessara.handling.binder
=======================

Parameter binding to function signatures.

Classes
-------
ParamBinder
    Bind parameters to a function signature.
"""
import inspect
from typing import Any, Callable

from tessara.core.parameters import ParameterSet


class ParamBinder:
    """
    Bind parameters to a function signature.

    Attributes
    ----------
    params : ParameterSet
        Parameters to bind to a function signature.

    Methods
    -------
    query(func: Callable) -> inspect.BoundArguments
        Query the parameters based on a function signature.
    call(func: Callable) -> Any
        Call a function with the parameters matching its signature.
    """
    def __init__(self, params: ParameterSet) -> None:
        self.params = params

    def query(self, func: Callable) -> inspect.BoundArguments:
        """
        Query the parameters based on a function signature.

        Arguments
        ---------
        func : Callable
            Function to inspect.

        Returns
        -------
        bound_args : inspect.BoundArguments
            Bound arguments of the function.

        Notes
        -----
        The query is performed by filtering the parameters based on the function signature. Only the
        parameters that match the function signature will be included in the bound arguments.

        Examples
        --------
        >>> def foo(a, b, c=42):
        ...     pass
        >>> params = ParameterSet(a=Param(default=1), b=Param(default=2))
        >>> binder = ParamBinder(params)
        >>> bound_args = binder.query(foo)
        >>> bound_args.arguments
        {'a': 1, 'b': 2}

        See Also
        --------
        inspect.signature
            Get the signature of a callable object.
        inspect.BoundArguments
            Object representing the bound arguments of a function.
        """
        sig = inspect.signature(func)
        # Extract values (not Param objects) for parameters matching the function signature
        filtered_params = {
            k: self.params.get(k)
            for k in self.params.data
            if k in sig.parameters
        }
        bound_args = sig.bind_partial(**filtered_params)
        return bound_args

    def call(self, func: Callable) -> Any:
        """
        Call a function with the parameters matching its signature.

        Arguments
        ---------
        func : Callable
            Function to call.

        Returns
        -------
        result : Any
            Result of the function call.

        Examples
        --------
        >>> def foo(a, b, c=42):
        ...     return a + b + c
        >>> params = ParameterSet(a=Param(default=1), b=Param(default=2))
        >>> binder = ParamBinder(params)
        >>> result = binder.call(foo)
        >>> result
        45
        """
        bound_args = self.query(func)
        return func(*bound_args.args, **bound_args.kwargs)
