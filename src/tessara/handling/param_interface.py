#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tessara.core.param_interface
============================

High-level interface for parameter assignment, binding, composition, sweeping...

Classes
-------
ParamAssigner
    Assign specific values to a set of parameters.
ParamBinder
    Bind parameters to a function signature.
ParamComposer
    Merge a set of ParameterSets into a single ParameterSet.
ParamSweeper
    Sweep over a grid of parameters. FIXME: To be refined. See below.
Config
    Protocol for configuration objects used to pass runtime values to the parameters.

"""
import inspect
from itertools import product
from typing import Any, List, Protocol, Callable

from tessara.core.parameters import ParameterSet, ParamGrid
from tessara.errors.validation import UnknownParameterError


# --- Parameter Binding ----------------------------------------------------------------------------

class Config(Protocol):
    """
    Protocol for configuration objects used to pass runtime values to the parameters.

    Provide a dictionary-like interface to access configuration values.

    Methods
    -------
    keys() -> List[str]
        Return the keys of the configuration object.
    __getitem__(key: str) -> Any
        Get the value of a configuration key.
    __contains__(key: str) -> bool
        Check if a key is present in the configuration object.
    """
    def keys(self) -> List[str]:
        ...

    def __getitem__(self, key: str) -> Any:
        ...

    def __contains__(self, key: str) -> bool:
        ...


class ParamAssigner:
    """
    Assign specific values to a set of parameters.

    Attributes
    ----------
    params : ParameterSet
        Parameters to bind to a configuration.
    config : Config
        Configuration values to apply to the parameters.

    Methods
    -------
    set(name: str, value: Any)
        Set the value of an existing parameter by its name.
    apply_config(config: Config)
        Apply runtime configuration values to the parameters.

    """
    def __init__(self, params: ParameterSet) -> None:
        self.params = params

    def set(self, name: str, value: Any):
        """
        Set the value of an existing parameter by its name.

        Warning
        -------
        If a value is already set, the initial value will be overridden.
        """
        if name in self.params:
            self.params[name].value = value
        else:
            raise UnknownParameterError(f"No parameter '{name}' in the ParameterSet.")

    def apply_config(self, config: Config) -> None:
        """
        Apply runtime configuration values to the parameters.

        Arguments
        ---------
        config : Config
            Configuration values to apply.

        Notes
        -----
        Parameters are set by querying the configuration object and retrieving the values for the
        relevant keys which match the parameter names.

        When a parameter is matched, its value is set in the Param object using the `set`
        method, which performs broadcast validation on the value.
        """
        matching_keys = self.params.keys() & config.keys()
        for key in matching_keys:
            self.params[key].value = config[key]


# --- Filtering ------------------------------------------------------------------------------------

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

        The returned object is an instance of `inspect.BoundArguments`, which has the advantage of
        separating the arguments into positional and keyword arguments if needed.

        Examples
        --------
        Query the parameters for a function:

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
            Relevant attributes:
                - `arguments` (dict): All bound arguments.
                - `args` (tuple): Positional arguments.
                - `kwargs` (dict): Keyword arguments.
        """
        sig = inspect.signature(func)
        filtered_params = {k: v for k, v in self.params if k in sig.parameters}
        # FIXME: Ensure the ParameterSet can be traversed as a dictionary returning raw values
        # rather than Param objects
        bound_args = sig.bind(**filtered_params)
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
        Call a function with the parameters:

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


# --- Composition ----------------------------------------------------------------------------------

class ParamComposer:
    """
    Merge a set of ParameterSets into a single ParameterSet.

    Attributes
    ----------
    params : Dict[ParameterSet]
        ParameterSets to compose, each identified by a unique name.
    precedence : List[str]
        Order of precedence for the parameters (by name), which determines the overriding order.
        If a A occurs *after* B in the list, then the parameters in A will *override* the ones in B.
        Thus, if a parameter is present in multiple input sets, its final value in the composed set
        will be the one from the set with the highest precedence, i.e. the last one in the list.

    Methods
    -------
    set_precedence(precedence: List[str])
        Set the order of precedence for the parameters.
    merge(original: ParameterSet, other: ParameterSet, override: bool = False) -> ParameterSet
        (Static method) Merge two parameter sets. Utility method in addition to the instance method.
    compose() -> ParameterSet
        Compose the parameter sets into a single set.
    """
    def __init__(self, *args: ParameterSet, **kwargs: ParameterSet) -> None:
        """
        Initialize the composer with a set of parameter sets.

        Arguments
        ---------
        args : ParameterSet
            ParameterSets to compose, in the order of precedence. Since no name is provided, the
            default names will be the indices of the sets in the list.
        kwargs : ParameterSet
            ParameterSets to compose, identified by a unique name. The names will be used to
            determine the order of precedence.

        Raises
        ------
        TypeError
            If the values are not ParameterSet instances or if there are duplicate names.
        ValueError
            If the names of the parameter sets are not unique.
        """
        if not all(isinstance(p, ParameterSet) for p in args) or not all(isinstance(p, ParameterSet) for p in kwargs.values()):
            raise TypeError("All values must be ParameterSet instances.")
        names_args = [str(i) for i in range(len(args))]
        if len(set(names_args) | set(kwargs.keys())) != len(args) + len(kwargs):
            raise ValueError("Duplicate names in the parameter sets.")
        self.params = {**dict(zip(names_args, args)), **kwargs} # merge both dictionaries
        self.precedence = list(self.params.keys()) # default order of precedence

    def set_precedence(self, precedence: List[str]) -> None:
        """
        Set the order of precedence for the parameters.

        Arguments
        ---------
        precedence : List[str]
            Order of precedence for the parameters (by name). The names must match the names of the
            parameter sets provided at initialization.

        Raises
        ------
        ValueError
            If the precedence list does not include all the names of the parameter sets.
        """
        missing = set(self.params.keys()) - set(precedence)
        if missing:
            raise ValueError(
                "Include all the names of the parameter sets in the precedence order. "
                f"Missing: {missing}"
            )
        self.precedence = precedence

    @staticmethod
    def merge(original: ParameterSet, other: ParameterSet, override: bool = False) -> ParameterSet:
        """
        Merge two parameter sets.

        Arguments
        ---------
        original : ParameterSet
            Original parameter set.
        other : ParameterSet
            Parameter set to merge with.
        override : bool
            If True, override existing parameters with new values.

        Returns
        -------
        merged : ParameterSet
            Merged parameter set (new object).

        Notes
        -----
        Merging one set in the other one consists in transferring all its parameters (`Param`
        instances) and the relation rules.

        Conventions:

        - If a parameter is absent in the recipient set (based on the name), it will be added.
        - If it is already present, it will be overridden only if the `override` flag is set to
          True.

        The goal of the `merge` method is to compose modular schemas of parameters, mirroring the
        hierarchical structure of the workflows.

        Examples
        --------
        Merge two parameter sets:

        >>> params1 = ParameterSet(param1=Param(default=42))
        >>> params2 = ParameterSet(param2=Param(default='foo'))
        >>> merged_params = ParamComposer.merge(params1, params2)
        >>> merged_params['param1'].get_value()
        42
        >>> merged_params['param2'].get_value()
        'foo'

        With overriding (two parameters with the same name):

        >>> params1 = ParameterSet(param1=Param(default=42))
        >>> params2 = ParameterSet(param1=Param(default=7))
        >>> merged_params = ParamComposer.merge(params1, params2, override=True)
        >>> merged_params['param1'].get_value()
        7
        """
        merged = original.copy()
        for name, param in other.data.items(): # param: Param instance
            if name not in merged.data or override:
                merged.data[name] = param
        for rule, targets in other.relation_rules:
            merged.relation_rules.append((rule, targets))
        return merged

    def compose(self) -> ParameterSet:
        """
        Compose the parameter sets into a single set.

        Returns
        -------
        composed : ParameterSet
            Composed parameter set.

        Notes
        -----
        The `compose` method merges the parameter sets in the order of precedence, from the first
        one to the last one. The parameters in the last set will override the ones in the previous
        sets.

        The order of precedence is determined by the `precedence` attribute, which can be set using
        the `set_precedence` method.

        Examples
        --------
        Compose a set of parameter sets:

        >>> params1 = ParameterSet(param1=Param(default=42))
        >>> params2 = ParameterSet(param2=Param(default='foo'))
        >>> composer = ParamComposer(params1, params2)
        >>> composed_params = composer.compose()
        >>> composed_params['param1'].get_value()
        42
        >>> composed_params['param2'].get_value()
        'foo'
        """
        composed = ParameterSet()
        for name in self.precedence:
            composed = self.merge(composed, self.params[name], override=True)
        return composed


# --- Sweeping -------------------------------------------------------------------------------------

"""
Separation of Sweep Functionality:
TODO: In generate_sweep_params, instead of returning a list, should it return a generator /
iterator? What would be the functional difference and the benefits or drawbacks ?
TODO: (In the future, not a priority) Here, the default combinations of sweeping values is a
cartesian product. Add support for more refined combinations, where only certain associations are
relevant.
TODO: Modify the generate_params method to filter out sweep-specific or internal attributes before
passing the remaining attributes to the base parameter constructor. This can be achieved by
explicitly constructing a dictionary of attributes to forward (e.g. using a whitelist of attribute
names or by excluding known keys such as sweep_values and _value).
TODO: Determine whether the sweeping functionality should be included in the Grid class.
"""

class ParamSweeper:
    """
    Sweep over a grid of parameters.

    Methods
    -------
    generate_sweep_grid() -> List[ParameterSet]
        Generate the combinations of parameters to sweep over.
    """
    def generate_sweep_grid(self) -> List[ParameterSet]:
        """
        Generate the combinations of parameters to sweep over, from all the combinations of
        ParamGrid values.

        Returns
        -------
        grid : List[ParameterSet]
            ParameterSets to sweep over. Each item represents a combination of parameters where:

            - For static parameters, the value is set to the current value (default or set).
            - For sweeping parameters, the value is set to one the list of values to sweep over.

        Notes
        -----
        All the combinations are generated from the cartesian product of the values in the
        ParamGrid objects. The static parameters remain fixed across the sweep.
        """
        sweep_params = {k: p.generate_params() for k, p in self.items() if isinstance(p, ParamGrid)}
        if not sweep_params: # no sweep parameters -> return a single ParameterSet
            return [self.copy()]
        grid = []
        names, params = zip(*sweep_params.items()) # params: list of lists (of Param instances)
        for combination in product(*params): # cartesian product of Param instances
            new_set = self.copy() # copy all parameters to override with new params
            for k, p in zip(names, combination):
                new_set[k] = p # replace Param instance (keep all attributes + new value)
            grid.append(new_set)
        return grid
