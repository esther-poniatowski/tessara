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
    Sweep over a grid of parameters with iterator/generator support.
Config
    Protocol for configuration objects used to pass runtime values to the parameters.

"""
import inspect
from itertools import product
from pathlib import Path
from typing import Any, List, Protocol, Callable, Union

from tessara.core.parameters import ParameterSet, ParamGrid, Param
from tessara.core.errors.handling import UnknownParameterError
from tessara.handling.config_io import load_yaml


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

    Supports loading configuration from YAML files, OmegaConf objects, or dictionaries.

    Attributes
    ----------
    params : ParameterSet
        Parameters to bind to a configuration.

    Methods
    -------
    set(name: str, value: Any)
        Set the value of an existing parameter by its name.
    apply_config(config: Config)
        Apply runtime configuration values to the parameters.
    from_yaml(path: str | Path) -> ParamAssigner
        Load configuration from a YAML file.
    from_dict(data: dict) -> ParamAssigner
        Apply configuration from a dictionary.

    Examples
    --------
    Basic usage:

    >>> params = ParameterSet(lr=Param(default=0.01), epochs=Param(default=100))
    >>> assigner = ParamAssigner(params)
    >>> assigner.set('lr', 0.001)
    >>> params.lr
    0.001

    Load from YAML file:

    >>> assigner = ParamAssigner(params).from_yaml('config.yaml')

    Load from dictionary:

    >>> assigner = ParamAssigner(params).from_dict({'lr': 0.001, 'epochs': 50})
    """

    def __init__(self, params: ParameterSet) -> None:
        self.params = params

    def set(self, name: str, value: Any) -> "ParamAssigner":
        """
        Set the value of an existing parameter by its name.

        Parameters
        ----------
        name : str
            Parameter name (supports dot notation for nested parameters).
        value : Any
            Value to set.

        Returns
        -------
        ParamAssigner
            Self, for method chaining.

        Raises
        ------
        UnknownParameterError
            If the parameter does not exist.

        Warning
        -------
        If a value is already set, the initial value will be overridden.
        """
        # Handle dot notation for nested parameters
        if "." in name:
            parts = name.split(".")
            obj = self.params
            for part in parts[:-1]:
                if part not in obj.data:
                    raise UnknownParameterError(f"No parameter '{part}' in path '{name}'.")
                obj = obj.data[part]
                if not isinstance(obj, ParameterSet):
                    raise UnknownParameterError(f"'{part}' is not a nested ParameterSet in '{name}'.")
            final_name = parts[-1]
            if final_name not in obj.data:
                raise UnknownParameterError(f"No parameter '{final_name}' in the ParameterSet.")
            obj.data[final_name].set(value)
        elif name in self.params:
            self.params[name].set(value)
        else:
            raise UnknownParameterError(f"No parameter '{name}' in the ParameterSet.")
        return self

    def apply_config(
        self,
        config: Config,
        recursive: bool = True,
        strict: bool = False,
    ) -> "ParamAssigner":
        """
        Apply runtime configuration values to the parameters.

        Parameters
        ----------
        config : Config
            Configuration values to apply (dict-like object).
        recursive : bool, default True
            If True, recursively apply nested dictionaries to nested ParameterSets.

        Returns
        -------
        ParamAssigner
            Self, for method chaining.

        Notes
        -----
        Parameters are set by querying the configuration object and retrieving the values for the
        relevant keys which match the parameter names.
        """
        self._apply_config_recursive(self.params, config, recursive, strict, path="")
        return self

    def _apply_config_recursive(
        self,
        params: ParameterSet,
        config: Config,
        recursive: bool,
        strict: bool,
        path: str,
    ) -> None:
        """Recursively apply configuration to nested ParameterSets."""
        param_keys = set(params.keys())
        config_keys = set(config.keys())
        if strict:
            unknown = config_keys - param_keys
            if unknown:
                paths = [
                    f"{path}.{key}" if path else key
                    for key in sorted(unknown)
                ]
                raise UnknownParameterError(
                    f"Unknown parameter(s) in config: {', '.join(paths)}"
                )

        matching_keys = param_keys & config_keys
        for key in matching_keys:
            target = params.data[key]
            value = config[key]
            if recursive and isinstance(target, ParameterSet) and isinstance(value, dict):
                # Recursively apply to nested ParameterSet
                next_path = f"{path}.{key}" if path else key
                self._apply_config_recursive(target, value, recursive, strict, next_path)
            elif hasattr(target, "set"):
                target.set(value)
            else:
                params.data[key] = value

    def from_yaml(
        self,
        path: Union[str, Path],
        prefer_omegaconf: bool = True,
        strict: bool = False,
    ) -> "ParamAssigner":
        """
        Load configuration from a YAML file and apply to parameters.

        Parameters
        ----------
        path : str or Path
            Path to the YAML configuration file.

        Returns
        -------
        ParamAssigner
            Self, for method chaining.

        Raises
        ------
        ImportError
            If PyYAML is not installed.
        FileNotFoundError
            If the YAML file does not exist.

        Examples
        --------
        >>> assigner = ParamAssigner(params).from_yaml('config.yaml')

        With OmegaConf (if installed):

        >>> assigner = ParamAssigner(params).from_yaml('config.yaml')
        # Automatically uses OmegaConf if available for variable interpolation

        Notes
        -----
        If OmegaConf is installed, it will be used for loading (supports variable
        interpolation and merging). Otherwise, falls back to PyYAML.
        """
        config = load_yaml(path, prefer_omegaconf=prefer_omegaconf)
        return self.from_dict(config, strict=strict)

    def from_dict(self, data: dict, strict: bool = False) -> "ParamAssigner":
        """
        Apply configuration from a dictionary.

        Parameters
        ----------
        data : dict
            Dictionary of parameter names to values.

        Returns
        -------
        ParamAssigner
            Self, for method chaining.

        Examples
        --------
        >>> assigner = ParamAssigner(params).from_dict({
        ...     'lr': 0.001,
        ...     'model': {'hidden_size': 256}
        ... })
        """
        return self.apply_config(data, strict=strict)


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

from typing import Iterator, Generator


class ParamSweeper:
    """
    Sweep over a grid of parameters with iterator/generator support.

    Generates all combinations of parameter values from ParamGrid objects
    using cartesian product. Supports both eager (list) and lazy (generator)
    evaluation.

    Attributes
    ----------
    params : ParameterSet
        Parameter set containing both static Params and ParamGrid objects.

    Methods
    -------
    generate() -> Generator[ParameterSet, None, None]
        Lazily generate parameter combinations one at a time.
    generate_all() -> List[ParameterSet]
        Eagerly generate all parameter combinations as a list.
    __iter__() -> Iterator[ParameterSet]
        Make the sweeper iterable (uses generate()).
    __len__() -> int
        Return the total number of combinations.

    Examples
    --------
    Basic usage with a ParameterSet:

    >>> params = ParameterSet(
    ...     lr=ParamGrid(Param(), sweep_values=[0.01, 0.001]),
    ...     epochs=Param(default=100),
    ... )
    >>> sweeper = ParamSweeper(params)
    >>> for combo in sweeper:
    ...     print(combo.to_dict(values_only=True))
    {'lr': 0.01, 'epochs': 100}
    {'lr': 0.001, 'epochs': 100}

    Multiple sweep parameters (cartesian product):

    >>> params = ParameterSet(
    ...     lr=ParamGrid(Param(), sweep_values=[0.01, 0.001]),
    ...     batch_size=ParamGrid(Param(), sweep_values=[32, 64]),
    ... )
    >>> sweeper = ParamSweeper(params)
    >>> len(sweeper)  # 2 * 2 = 4 combinations
    4

    Notes
    -----
    - Parameter names are sorted for deterministic ordering across runs.
    - The generator pattern allows memory-efficient iteration over large sweeps.
    - Each generated ParameterSet is a deep copy with the sweep values applied.
    """

    def __init__(self, params: ParameterSet) -> None:
        self.params = params

    def _collect_sweep_params(
        self,
        params: ParameterSet,
        prefix: tuple[str, ...] = (),
    ) -> List[tuple[str, ParamGrid]]:
        """Collect ParamGrid objects with deterministic ordering."""
        items: List[tuple[str, ParamGrid]] = []
        for key in sorted(params.data.keys()):
            value = params.data[key]
            if isinstance(value, ParameterSet):
                items.extend(self._collect_sweep_params(value, prefix + (key,)))
            elif isinstance(value, ParamGrid):
                path = ".".join(prefix + (key,))
                items.append((path, value))
        return items

    def _set_param_by_path(self, params: ParameterSet, path: str, param: Param) -> None:
        """Set a Param at a dotted path in a nested ParameterSet."""
        parts = path.split(".")
        obj: Any = params
        for part in parts[:-1]:
            if isinstance(obj, ParameterSet) and part in obj.data:
                obj = obj.data[part]
            else:
                raise UnknownParameterError(f"No parameter '{path}' in the ParameterSet.")
        if not isinstance(obj, ParameterSet):
            raise UnknownParameterError(f"No parameter '{path}' in the ParameterSet.")
        obj.data[parts[-1]] = param

    def generate(self) -> Generator[ParameterSet, None, None]:
        """
        Lazily generate parameter combinations one at a time.

        Yields
        ------
        ParameterSet
            A parameter set with one specific combination of sweep values.
            Static parameters retain their original values.

        Notes
        -----
        This is memory-efficient for large sweeps as it generates
        combinations on-demand rather than storing them all in memory.
        """
        sweep_items = self._collect_sweep_params(self.params)
        if not sweep_items:
            # No sweep parameters -> yield the original set
            yield self.params.copy()
            return

        names = [name for name, _ in sweep_items]
        grids = [grid for _, grid in sweep_items]
        value_lists = [list(grid.iter_values()) for grid in grids]

        for combination in product(*value_lists):
            new_set = self.params.copy()
            for name, value, grid in zip(names, combination, grids):
                param = grid.make_param(value)
                self._set_param_by_path(new_set, name, param)
            yield new_set

    def generate_all(self) -> List[ParameterSet]:
        """
        Eagerly generate all parameter combinations as a list.

        Returns
        -------
        List[ParameterSet]
            All parameter combinations. Equivalent to list(self.generate()).

        Notes
        -----
        For large sweeps, prefer using generate() or iteration directly
        to avoid memory issues.
        """
        return list(self.generate())

    def __iter__(self) -> Iterator[ParameterSet]:
        """Make the sweeper iterable."""
        return self.generate()

    def __len__(self) -> int:
        """
        Return the total number of combinations.

        Uses multiplication to avoid generating all combinations.
        """
        sweep_items = self._collect_sweep_params(self.params)
        if not sweep_items:
            return 1
        count = 1
        for _, grid in sweep_items:
            count *= len(grid.sweep_values)
        return count
