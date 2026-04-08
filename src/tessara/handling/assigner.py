"""
tessara.handling.assigner
=========================

Parameter assignment from configuration sources.

Classes
-------
Config
    Protocol for configuration objects used to pass runtime values to the parameters.
ParamAssigner
    Assign specific values to a set of parameters.
"""
from pathlib import Path
from typing import Any, List, Protocol, Union

from tessara.core.parameters import ParameterSet, Param, ParamGrid
from tessara.core.errors.handling import UnknownParameterError
from tessara.handling.config_io import load_yaml
from tessara.handling.tree import ParameterTree


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
        """Return the configuration keys."""
        ...

    def __getitem__(self, key: str) -> Any:
        ...

    def __contains__(self, key: str) -> bool:
        ...


class _AssignmentStrategy(Protocol):
    def supports(self, target: object) -> bool:
        """Return ``True`` if this strategy can handle *target*.

        Parameters
        ----------
        target : object
            Parameter node to test.

        Returns
        -------
        bool
            Whether this strategy can handle *target*.
        """
        ...

    def apply(
        self,
        assigner: "ParamAssigner",
        target: object,
        value: Any,
        recursive: bool,
        strict: bool,
        path: str,
    ) -> None:
        """Apply *value* to *target* using the assigner context.

        Parameters
        ----------
        assigner : ParamAssigner
            Owning assigner (provides recursive application).
        target : object
            Parameter node to assign to.
        value : Any
            Configuration value to apply.
        recursive : bool
            Whether to recurse into nested parameter sets.
        strict : bool
            Whether to validate values and reject unknown keys.
        path : str
            Dot-separated path for error messages.
        """
        ...


class _ParamStrategy:
    def supports(self, target: object) -> bool:
        """Return ``True`` for Param targets.

        Parameters
        ----------
        target : object
            Parameter node to test.

        Returns
        -------
        bool
            Whether *target* is a ``Param``.
        """
        return isinstance(target, Param)

    def apply(
        self,
        assigner: "ParamAssigner",
        target: object,
        value: Any,
        recursive: bool,
        strict: bool,
        path: str,
    ) -> None:
        """Set *value* directly on the Param.

        Parameters
        ----------
        assigner : ParamAssigner
            Owning assigner (unused for leaf assignment).
        target : object
            ``Param`` instance to update.
        value : Any
            Scalar value to assign.
        recursive : bool
            Ignored for leaf parameters.
        strict : bool
            Whether to validate the value against the parameter constraints.
        path : str
            Dot-separated path for error messages.
        """
        assert isinstance(target, Param)
        target.set(value, strict=strict)


class _ParamGridStrategy:
    def supports(self, target: object) -> bool:
        """Return ``True`` for ParamGrid targets.

        Parameters
        ----------
        target : object
            Parameter node to test.

        Returns
        -------
        bool
            Whether *target* is a ``ParamGrid``.
        """
        return isinstance(target, ParamGrid)

    def apply(
        self,
        assigner: "ParamAssigner",
        target: object,
        value: Any,
        recursive: bool,
        strict: bool,
        path: str,
    ) -> None:
        """Replace sweep values on the ParamGrid.

        Parameters
        ----------
        assigner : ParamAssigner
            Owning assigner (unused for grid assignment).
        target : object
            ``ParamGrid`` instance to update.
        value : Any
            List or tuple of sweep values to assign.
        recursive : bool
            Ignored for grid parameters.
        strict : bool
            Whether to validate each candidate value.
        path : str
            Dot-separated path for error messages.
        """
        assert isinstance(target, ParamGrid)
        if not isinstance(value, (list, tuple)):
            raise TypeError(
                f"Config value for sweep parameter '{path}' must be a list or tuple, "
                f"got {type(value).__name__}."
            )
        sweep_values = list(value)
        if strict:
            for candidate in sweep_values:
                target.make_param(candidate)
        target.sweep_values = sweep_values


class _ParameterSetStrategy:
    def supports(self, target: object) -> bool:
        """Return ``True`` for ParameterSet targets.

        Parameters
        ----------
        target : object
            Parameter node to test.

        Returns
        -------
        bool
            Whether *target* is a ``ParameterSet``.
        """
        return isinstance(target, ParameterSet)

    def apply(
        self,
        assigner: "ParamAssigner",
        target: object,
        value: Any,
        recursive: bool,
        strict: bool,
        path: str,
    ) -> None:
        """Recurse into the nested ParameterSet with *value* as sub-config.

        Parameters
        ----------
        assigner : ParamAssigner
            Owning assigner (used to recurse into children).
        target : object
            ``ParameterSet`` instance to recurse into.
        value : Any
            Mapping-like sub-configuration for the nested set.
        recursive : bool
            Whether to continue recursing into deeper levels.
        strict : bool
            Whether to reject unknown keys and validate values.
        path : str
            Dot-separated path for error messages.
        """
        assert isinstance(target, ParameterSet)
        config = _as_config(value, path)
        assigner._apply_config_recursive(target, config, recursive, strict, path=path)


def _as_config(value: Any, path: str) -> Config:
    if isinstance(value, dict):
        return value
    if hasattr(value, "keys") and hasattr(value, "__getitem__"):
        return value
    raise TypeError(
        f"Config value for nested ParameterSet '{path or '<root>'}' must be a mapping-like object, "
        f"got {type(value).__name__}."
    )


class ParamAssigner:
    """
    Assign specific values to a set of parameters.

    Supports loading configuration from YAML files, OmegaConf objects, or dictionaries.

    Parameters
    ----------
    params : ParameterSet
        Parameters to bind to a configuration.

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
        self._tree = ParameterTree(params)
        self._strategies: tuple[_AssignmentStrategy, ...] = (
            _ParameterSetStrategy(),
            _ParamGridStrategy(),
            _ParamStrategy(),
        )

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
        target = self._tree.get_node(name)
        self._apply_target(target, value, recursive=True, strict=False, path=name)
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
        strict : bool, default False
            If True, raise on unknown config keys and validate values.

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
        """Recursively apply configuration to nested ParameterSets.

        Parameters
        ----------
        params : ParameterSet
            Target parameter set.
        config : Config
            Configuration mapping to apply.
        recursive : bool
            Whether to recurse into nested sets.
        strict : bool
            Whether to reject unknown keys.
        path : str
            Dot-separated path prefix for error messages.
        """
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
            next_path = f"{path}.{key}" if path else key
            self._apply_target(target, value, recursive, strict, next_path)

    def _apply_target(
        self,
        target: object,
        value: Any,
        recursive: bool,
        strict: bool,
        path: str,
    ) -> None:
        for strategy in self._strategies:
            if strategy.supports(target):
                strategy.apply(self, target, value, recursive, strict, path)
                return
        raise TypeError(f"Unsupported parameter node at '{path}': {type(target).__name__}")

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
        prefer_omegaconf : bool, default True
            Use OmegaConf for loading if available.
        strict : bool, default False
            If True, raise on unknown config keys.

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

        Notes
        -----
        If OmegaConf is installed, it will be used for loading (supports variable
        interpolation and merging). Otherwise, falls back to PyYAML.

        Examples
        --------
        >>> assigner = ParamAssigner(params).from_yaml('config.yaml')
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
        strict : bool, default False
            If True, raise on unknown config keys.

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
