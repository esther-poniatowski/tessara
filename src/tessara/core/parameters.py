"""
tessara.core.parameters
=======================

Core parameter management classes for defining, validating, and organizing parameters.

Classes
-------
Param
    Define a parameter with properties and constraints for runtime validation.
ParamGrid
    Define a parameter representing a sweep over multiple values.
ParameterSet
    Manage a collection of parameters with dot notation access.

Functions
---------
resolve_path
    Traverse a nested ParameterSet structure using a dot-separated path.

Notes
-----
- Parameters support validation rules via the `rules` attribute
- Nested ParameterSets can be accessed using dot notation (e.g., ``params.model.lr``)
- Values can be set with optional strict validation via ``param.set(value, strict=True)``
- Use ``param.is_set`` to distinguish between "not set" and "explicitly set to None"
"""
from collections import UserDict
from collections.abc import Iterable
from copy import deepcopy
from typing import Any, Optional, Self, Dict, List

from tessara.core.errors.handling import (
    OverrideParameterError,
    UnknownParameterError,
)
from tessara.core.types import (
    RuleProtocol,
    MultiValueRuleProtocol,
    RuleRegistryProtocol,
    Targets,
    RelationRule,
)


class _Unset:
    """Sentinel class to distinguish 'not set' from 'explicitly set to None'."""
    _instance = None

    def __new__(cls):
        # Singleton pattern - same instance survives deepcopy type checks
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "<UNSET>"

    def __bool__(self) -> bool:
        return False

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        # Return the same singleton instance on deepcopy
        return self

    def __reduce__(self):
        return (self.__class__, ())


_UNSET = _Unset()


# --- Path Resolution Utility ---------------------------------------------------------------------

def resolve_path(
    params: "ParameterSet",
    path: str,
) -> "Param | ParameterSet":
    """
    Traverse a nested ParameterSet structure using a dot-separated path.

    Parameters
    ----------
    params : ParameterSet
        Root parameter set to start traversal from.
    path : str
        Dot-separated path to the target parameter or nested set
        (e.g., ``"model.layers.hidden"``).

    Returns
    -------
    Param | ParameterSet
        The resolved object at the end of the path.

    Raises
    ------
    UnknownParameterError
        If any segment of the path does not exist in the structure.
    """
    parts = path.split(".")
    obj: Any = params
    for part in parts:
        if isinstance(obj, ParameterSet) and part in obj.data:
            obj = obj.data[part]
        else:
            raise UnknownParameterError(f"No parameter '{path}' in the ParameterSet.")
    return obj


# --- Param Class ----------------------------------------------------------------------------------

class Param:
    """
    Define a parameter with properties and constraints for runtime validation.

    Each instance of this class represents a parameter with constraints (type, value range, regular
    expression...) and an optional default value.
    The actual value of the parameter has to be set at runtime, and it will be validated against the
    rules defined in the instance (if the strict mode is enabled).

    Attributes
    ----------
    value : Any
        Value set at runtime.
    default : Any
        Default value for the parameter.
    rules : List[RuleProtocol]
        Rules (constraints) to validate the parameter value.

    Methods
    -------
    set(value: Any)
        Set parameter value at runtime with optional validation.
    get() -> Any
        Retrieve the set value or default.
    register_rule(rule: RuleProtocol)
        Register a rule to validate the parameter.

    Examples
    --------
    Define a parameter with a default value, type constraint and boundaries:

    >>> param = Param(
    ...     default=5,
    ...     rules=[
    ...         TypeRule(int),
    ...         RangeRule(gt=0, le=10),
    ...     ]
    ... )
    >>> param.get()
    5

    Define a parameter with no default value and a pattern matching constraint:

    >>> param = Param(rules=[PatternRule(r'^[A-Z]{3}$')])
    >>> param.set('ABC')
    >>> param.get()
    'ABC'

    Set a runtime value for the parameter:

    >>> param.set(6)
    >>> param.get()
    6

    Notes
    -----
    The ``Param`` class serves as a static representation of a parameter with constraints. It does
    not perform validation itself.

    See Also
    --------
    RuleProtocol
        Protocol for validation rules.
    """
    def __init__(
        self,
        default: Optional[Any] = None,
        rules: Optional[Iterable[RuleProtocol]] = None,
    ) -> None:
        self._value = _UNSET  # sentinel to distinguish "not set" from "set to None"
        self.default = default
        self.rules: List[RuleProtocol] = []  # Initialize first
        if rules:
            for rule in rules:
                self.register_rule(rule)

    def set(self, value: Any, strict: bool = False) -> "Param":
        """
        Set the parameter value at runtime.

        Parameters
        ----------
        value : Any
            Value to set.
        strict : bool, default False
            If True, validate the value against all registered rules before setting.
            Raises ValidationError if any rule fails.

        Returns
        -------
        Param
            Self, for method chaining.

        Raises
        ------
        ValidationError
            If strict=True and validation fails.
        """
        if strict:
            self.validate_value(value)
        self._value = value
        return self

    def validate_value(self, value: Any) -> None:
        """
        Validate a value against all registered rules.

        Raises ValidationError on the first failing rule.
        """
        if not self.rules:
            return
        for rule in self.rules:
            error = rule.get_error(value)
            if error is not None:
                raise error

    @property
    def value(self) -> Any:
        """
        The explicitly set value, or None if not set.

        Note: Use ``is_set`` to distinguish between "set to None" and "not set".
        """
        return None if self._value is _UNSET else self._value

    @property
    def is_set(self) -> bool:
        """Return True if the value has been explicitly set (even to None)."""
        return self._value is not _UNSET

    def get(self) -> Any:
        """
        Retrieve the current value or default.

        Returns the runtime value if explicitly set (even if None),
        otherwise returns the default value.
        """
        return self._value if self._value is not _UNSET else self.default

    def register_rule(self, rule: RuleProtocol) -> None:
        """
        Add a rule to validate the parameter.

        Parameters
        ----------
        rule : RuleProtocol
            Any object implementing ``check(value) -> bool`` and
            ``get_error(value) -> Exception | None``.

        Raises
        ------
        TypeError
            If *rule* does not satisfy the RuleProtocol.
        """
        if not isinstance(rule, RuleProtocol):
            raise TypeError(
                f"Rule '{rule.__class__.__name__}' does not satisfy RuleProtocol "
                f"(must implement check() and get_error())."
            )
        self.rules.append(rule)

    def copy(self) -> Self:
        """Create a deep copy of the parameter, namely all the rules. Used to set a new value."""
        return deepcopy(self)

    def to_dict(self, registry: Optional[RuleRegistryProtocol] = None) -> Dict[str, Any]:
        """
        Serialize the parameter to a dictionary.

        Parameters
        ----------
        registry : RuleRegistryProtocol, optional
            Registry used to serialize rules. If not provided, rules are serialized
            as class names only (for documentation purposes).

        Returns
        -------
        Dict[str, Any]
            Dictionary representation of the parameter containing:
            - 'value': Current runtime value (if set)
            - 'default': Default value (if set)
            - 'rules': List of serialized rules

        Example
        -------
        >>> param = Param(default=10, rules=[TypeRule(int), RangeRule(gt=0)])
        >>> param.to_dict()
        {'value': None, 'default': 10, 'rules': [{'type': 'TypeRule'}, ...]}
        """
        if registry is not None:
            serialized_rules = [registry.serialize(rule) for rule in self.rules]
        else:
            # Lazy import to avoid circular dependency; only needed for default serialization
            from tessara.validation.rules import DEFAULT_RULE_REGISTRY
            serialized_rules = [DEFAULT_RULE_REGISTRY.serialize(rule) for rule in self.rules]
        return {
            "value": None if self._value is _UNSET else self._value,
            "default": self.default,
            "rules": serialized_rules,
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        registry: Optional[RuleRegistryProtocol] = None,
    ) -> "Param":
        """
        Create a Param instance from a dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary containing 'value' and/or 'default' keys.
        registry : RuleRegistryProtocol, optional
            Registry used to deserialize rules. If not provided, the default registry is used.

        Returns
        -------
        Param
            New parameter instance with the specified values.

        Example
        -------
        >>> data = {'value': 5, 'default': 10}
        >>> param = Param.from_dict(data)
        >>> param.get()
        5
        """
        if registry is None:
            from tessara.validation.rules import DEFAULT_RULE_REGISTRY
            registry = DEFAULT_RULE_REGISTRY
        rules_data = data.get("rules", [])
        rules = [registry.deserialize(rule_data) for rule_data in rules_data]
        param = cls(default=data.get("default"), rules=rules)
        if "value" in data and data["value"] is not None:
            param.set(data["value"])
        return param


# --- ParameterSet Class ---------------------------------------------------------------------------

class ParameterSet(UserDict[str, Param]):
    """
    Manage a collection of parameters.

    Attributes
    ----------
    data : Dict[str, Param]
        Underlying dictionary of parameters, inherited from UserDict.

    Methods
    -------
    get(name) -> Any
        Retrieve the *value* (not the Param object) of a parameter by name.
    get_value(name) -> Any
        Retrieve a parameter value by name, supporting dot notation.
    set(name, value)
        Set the value of an existing parameter by name (supports dot notation).

    Examples
    --------
    Create a parameter set with two parameters:

    >>> params = ParameterSet(
    ...     param1=Param(default=42, rules=RangeRule(gt=0)),
    ...     param2=Param(rules=TypeRule(str))
    ... )

    Retrieve a parameter value:

    >>> params.get('param1')
    42

    Access nested Param or ParameterSet objects via dot notation:

    >>> params.model.lr        # returns the Param object
    >>> params.model.lr.get()  # returns its value

    Notes
    -----
    Instances of ``ParameterSet`` behave like dictionaries. All the methods of the UserDict class
    are available for this object, and by extension all the dict methods. The main difference is
    that the values are ``Param`` objects, which provide additional validation and constraints.

    Dot notation access (e.g. ``params.model``) returns ``Param`` or ``ParameterSet`` objects,
    never raw values. Use ``get()`` or ``get_value()`` to retrieve values directly.

    The ``add``, ``remove`` and ``set`` methods provide flexibility for hierarchical construction
    of parameter sets that can mirror a hierarchy of workflows, from the most general to the most
    specific.

    See Also
    --------
    Param
        Custom parameter class with validation constraints.
    collections.UserDict
        Inherit from this class to create a dictionary-like object.
    """

    # Attributes that belong to the object itself, not to be treated as parameter keys
    _RESERVED_ATTRS = frozenset({"data", "relation_rules", "_RESERVED_ATTRS"})

    def __init__(self, *args, relation_rules: Optional[List[RelationRule]] = None, **kwargs):
        """
        Initialize parameters from a dictionary or keyword arguments.

        Arguments
        ---------
        *args : Tuple
            Positional arguments to initialize the parameter set.
            Used to pass a dictionary as the first argument.
        relation_rules : List[RelationRule]
            Relation rules to apply to the parameters. Each element is a tuple (rule, targets).
            ``rule``: MultiValueRuleProtocol instance to apply to the parameters.
            ``targets``: Specification of the parameters targeted by the rule. Possibilities:
            - List of parameter names (strings).
            - Dictionary with parameter names as keys and corresponding variable names as values (in
              the signature of the rule function).
        **kwargs : Dict[str, Param]
            Keyword arguments to initialize the parameter set.
            Used to pass parameters directly as keyword arguments.
            If the values are not Param objects, they will be converted to Param objects and the
            provided value will serve as the 'default' attribute of the Param object.

        Examples
        --------
        Initialize parameters from a dictionary:

        >>> params = ParameterSet({'param1': Param(default=42), 'param2': Param(default='foo')})

        Initialize parameters from keyword arguments:

        >>> params = ParameterSet(param1=Param(default=42), param2=Param(default='foo'))
        """
        super().__init__()  # initialize with the parent class constructor (UserDict)
        candidates = args[0] if args and isinstance(args[0], dict) else kwargs
        for param in candidates:
            self.add(param, candidates[param])
        self.relation_rules: List[RelationRule] = []
        if relation_rules is not None:
            if isinstance(relation_rules, Iterable):
                for rule, targets in relation_rules:
                    self.register_relation_rule(rule, targets)
            else:
                raise TypeError("Pass rules in an iterable")

    def add(self, name: str, param: Any):
        """
        Add a new parameter in the set with a unique name.

        Arguments
        ---------
        param : Any
            If ``param`` is already a Param or ParameterSet, it will be added directly.
            Otherwise, a new Param object will be created with the provided value as the default.
        """
        if name in self.data:
            raise OverrideParameterError(f"Parameter '{name}' already exists in the ParameterSet.")
        if isinstance(param, (Param, ParameterSet, ParamGrid)):
            self.data[name] = param
        else:  # convert to Param object with the provided value as the default
            self.data[name] = Param(default=param)

    def remove(self, name: str):
        """Remove a parameter from the set by its name."""
        self.data.pop(name, None)

    def __setitem__(self, name: str, param: Any) -> None:
        """Set a full Param instance (from a Param instance or a single value).
        Override the ``__setitem__`` method to ensure that the value is a valid Param object.

        This method is triggered with the following syntax: ``params['key'] = value``.
        """
        self.add(name, param)

    def __getattr__(self, name: str) -> Any:
        """
        Access parameters or nested ParameterSets using dot notation.

        Always returns the ``Param`` or ``ParameterSet`` object itself, never its raw value.
        Use ``.get()`` on the returned Param to obtain the value.

        Parameters
        ----------
        name : str
            Single-segment attribute name (e.g. ``"lr"``). Multi-segment dot paths are not
            expected here because Python dispatches each segment individually.

        Returns
        -------
        Param | ParameterSet
            The parameter or nested set registered under *name*.

        Raises
        ------
        AttributeError
            If *name* is not found in the ParameterSet.

        Example
        -------
        >>> params = ParameterSet(model=ParameterSet(lr=Param(default=0.01)))
        >>> params.model.lr.get()
        0.01
        """
        # Handle special attributes (dunder methods, private attrs) - delegate to parent
        # This prevents recursion during deepcopy and pickle operations
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        # Ensure 'data' attribute exists before accessing it
        if "data" not in self.__dict__:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        if name in self.data:
            return self.data[name]

        raise AttributeError(f"No parameter '{name}' in the ParameterSet.")

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set parameter values using dot notation (e.g. ``params.lr = 0.01``).

        Supports assignment to both direct parameters and nested ParameterSets.
        Reserved attributes (like 'data', 'relation_rules') are set normally.

        Parameters
        ----------
        name : str
            Attribute name to set.
        value : Any
            Value to assign. If the target is a Param, sets its value via ``Param.set()``.
            If the target is a ParameterSet, replaces it.

        Raises
        ------
        AttributeError
            If the specified parameter is not found in the ParameterSet.

        Example
        -------
        >>> params = ParameterSet(model=ParameterSet(lr=Param(default=0.01)))
        >>> params.model.lr = 0.001  # Sets the value of the 'lr' parameter
        """
        # Handle reserved attributes (object's own attributes)
        if name in ParameterSet._RESERVED_ATTRS or name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        # During initialization, 'data' might not exist yet
        if not hasattr(self, "data"):
            object.__setattr__(self, name, value)
            return

        # Try to find and set the parameter
        if name in self.data:
            target = self.data[name]
            if isinstance(target, Param):
                target.set(value)
            elif isinstance(target, ParameterSet):
                # Replace nested ParameterSet or assign value to it
                if isinstance(value, ParameterSet):
                    self.data[name] = value
                elif isinstance(value, dict):
                    self.data[name] = ParameterSet.from_dict(value, values_only=True)
                else:
                    raise TypeError(
                        f"Cannot assign non-ParameterSet value to nested ParameterSet '{name}'"
                    )
            else:
                self.data[name] = value
        else:
            # Parameter doesn't exist - raise an error (don't silently create)
            raise AttributeError(
                f"No parameter '{name}' in the ParameterSet. "
                f"Use add() to create new parameters."
            )

    def get(self, name: str) -> Any:
        """
        Retrieve the *value* of a parameter by its name.

        Parameters
        ----------
        name : str
            Parameter name (single segment, no dot notation).

        Returns
        -------
        Any
            The current value if set, otherwise the default.
        """
        return self[name].get()

    def get_value(self, name: str) -> Any:
        """
        Retrieve a parameter value by name, supporting dot notation.

        Parameters
        ----------
        name : str
            Parameter name, possibly dot-separated (e.g. ``"model.lr"``).

        Returns
        -------
        Any
            The current value if set, otherwise the default.

        Raises
        ------
        UnknownParameterError
            If the path cannot be resolved or does not end at a Param.
        """
        if "." not in name:
            return self.get(name)
        obj = resolve_path(self, name)
        if isinstance(obj, Param):
            return obj.get()
        raise UnknownParameterError(f"No parameter '{name}' in the ParameterSet.")

    def set(self, name: str, value: Any) -> None:
        """
        Set the value of an existing parameter by name.

        Supports dot notation for nested parameters (e.g. ``"model.lr"``).

        Parameters
        ----------
        name : str
            Parameter name, possibly dot-separated.
        value : Any
            Value to assign.

        Raises
        ------
        UnknownParameterError
            If the parameter does not exist.
        """
        if "." not in name:
            if name not in self.data:
                raise UnknownParameterError(f"No parameter '{name}' in the ParameterSet.")
            target = self.data[name]
            if isinstance(target, Param):
                target.set(value)
            else:
                self.data[name] = value
            return

        parts = name.split(".")
        parent = resolve_path(self, ".".join(parts[:-1]))
        if not isinstance(parent, ParameterSet):
            raise UnknownParameterError(f"'{'.'.join(parts[:-1])}' is not a nested ParameterSet.")
        final_name = parts[-1]
        if final_name not in parent.data:
            raise UnknownParameterError(f"No parameter '{final_name}' in the ParameterSet.")
        target = parent.data[final_name]
        if isinstance(target, Param):
            target.set(value)
        else:
            parent.data[final_name] = value

    def register_rule(self, target: str, rule: RuleProtocol) -> None:
        """
        Register a rule for a specific parameter already present in the set.

        Arguments
        ---------
        target : str
            Name of the parameter targeted by the rule.
        rule : RuleProtocol
            Validation rule to apply to the parameter.

        Examples
        --------
        Add a custom rule to a parameter:

        >>> params = ParameterSet(param1=Param(rules=[TypeRule(int)]))
        >>> def is_even(value: Any) -> bool:
        ...     return value % 2 == 0
        >>> params.register_rule('param1', CustomRule(is_even))
        """
        if target in self.data:
            self.data[target].register_rule(rule)
        else:
            raise UnknownParameterError(f"No parameter '{target}' in the ParameterSet.")

    def register_relation_rule(self, rule: MultiValueRuleProtocol, targets: Targets) -> None:
        """
        Register a relation rule between multiple parameters, for cross-parameter dependencies.

        Arguments
        ---------
        rule : MultiValueRuleProtocol
            Relational validation rule to apply to the parameters.
        targets : Targets
            Names of the parameters targeted by the rule (list or mapping).

        Examples
        --------
        >>> params = ParameterSet(param1=Param(default=1), param2=Param(default=2))
        >>> def is_greater_than(x: int, y: int) -> bool:
        ...     return x > y
        >>> from tessara.validation.rules import MultiValueRule
        >>> greater_than_rule = MultiValueRule(is_greater_than)
        >>> params.register_relation_rule(greater_than_rule, ['param1', 'param2'])

        Notes
        -----
        The format of the targets determines the internal call to the rule function.
        If the targets are provided as a list, the parameters are passed as positional arguments.
        If the targets are provided as a dictionary, the parameters are passed as keyword arguments.
        """
        if not isinstance(rule, MultiValueRuleProtocol):
            raise TypeError(
                f"Rule '{rule.__class__.__name__}' does not satisfy MultiValueRuleProtocol."
            )
        for target in targets:
            if target not in self.data:
                raise UnknownParameterError(f"No parameter '{target}' in the ParameterSet.")
        self.relation_rules.append((rule, targets))

    def copy(self) -> Self:
        """Create a deep copy of the parameter set, including all nested ParameterSets and Params."""
        return deepcopy(self)

    def to_dict(self, values_only: bool = False) -> Dict[str, Any]:
        """
        Serialize the parameter set to a dictionary.

        Parameters
        ----------
        values_only : bool, default False
            If True, return only the current values (or defaults) of parameters.
            If False, return the full serialization including Param metadata.

        Returns
        -------
        Dict[str, Any]
            Dictionary representation of the parameter set.

        Examples
        --------
        Get values only (useful for configuration export):

        >>> params = ParameterSet(lr=Param(default=0.01), epochs=Param(default=100))
        >>> params.to_dict(values_only=True)
        {'lr': 0.01, 'epochs': 100}

        Get full serialization:

        >>> params.to_dict()
        {'lr': {'value': None, 'default': 0.01, 'rules': []}, ...}

        Nested parameter sets are recursively serialized:

        >>> params = ParameterSet(model=ParameterSet(lr=Param(default=0.01)))
        >>> params.to_dict(values_only=True)
        {'model': {'lr': 0.01}}
        """
        result: Dict[str, Any] = {}
        for name, param in self.data.items():
            if isinstance(param, ParameterSet):
                result[name] = param.to_dict(values_only=values_only)
            elif isinstance(param, Param):
                if values_only:
                    # Return the current value if set, otherwise the default
                    result[name] = param.get()
                else:
                    result[name] = param.to_dict()
            else:
                result[name] = param
        return result

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], values_only: bool = False
    ) -> "ParameterSet":
        """
        Create a ParameterSet from a dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary to convert. Structure depends on ``values_only``.
        values_only : bool, default False
            If True, treats values as parameter values/defaults directly.
            If False, expects full Param serialization format.

        Returns
        -------
        ParameterSet
            New parameter set instance.

        Examples
        --------
        From values (configuration-style):

        >>> data = {'lr': 0.01, 'epochs': 100}
        >>> params = ParameterSet.from_dict(data, values_only=True)

        Nested dictionaries become nested ParameterSets:

        >>> data = {'model': {'lr': 0.01}}
        >>> params = ParameterSet.from_dict(data, values_only=True)
        >>> params.model.lr.get()
        0.01
        """
        params = cls()
        for name, value in data.items():
            if isinstance(value, dict):
                # Check if it's a nested ParameterSet or a Param serialization
                if values_only or not any(k in value for k in ("value", "default", "rules")):
                    # Nested dictionary -> nested ParameterSet
                    params.data[name] = cls.from_dict(value, values_only=values_only)
                else:
                    # Param serialization format
                    params.data[name] = Param.from_dict(value)
            else:
                if values_only:
                    param = Param(default=None)
                    param.set(value)
                    params.data[name] = param
                else:
                    # Direct value -> Param with that default
                    params.data[name] = Param(default=value)
        return params


# --- ParamGrid Class ------------------------------------------------------------------------------

class ParamGrid:
    """
    Wrapper encapsulating a parameter intended for sweeping over multiple values.

    To represent all parameters uniformly in the ParameterSet, this wrapper behaves like a basic
    parameter for rule related behavior, except that:

    - It also stores a list of values that need to be traversed during a parameter sweep.
    - It does not store a value, as it is intended to be used as a template for generating multiple
      ``Param`` instances.

    The sweep values can be set either at the moment of defining the ParamGrid instance, or
    at runtime, for instance to define sweep values from a configuration object.

    Attributes
    ----------
    param : Param
        Underlying parameter that defines validation rules.
    sweep_values : List[Any]
        Values over which the parameter should be swept.

    Methods
    -------
    generate_params() -> Iterable[Param]
        Generate individual ``Param`` instances for each sweep value.
    register_rule(rule: RuleProtocol)
        Delegate rule registration to the underlying ``Param`` instance.

    Examples
    --------
    Define a parameter sweep:

    >>> param = ParamGrid(Param(rules=TypeRule(int)), sweep_values=[1, 2, 3])
    """

    def __init__(self, param: Param, sweep_values: Optional[List[Any]] = None) -> None:
        if not isinstance(param, Param):
            raise TypeError("`param` must be an instance of `Param`.")
        self.param = param
        self.sweep_values = sweep_values or []

    def register_rule(self, rule: RuleProtocol) -> None:
        """Delegate rule registration to the underlying ``Param`` instance."""
        self.param.register_rule(rule)

    def iter_values(self) -> Iterable[Any]:
        """Iterate over sweep values."""
        return iter(self.sweep_values)

    def make_param(self, value: Any) -> Param:
        """Create a Param instance with a specific sweep value."""
        param = self.param.copy()
        param.set(value)
        return param

    def generate_params(self) -> Iterable[Param]:
        """
        Generate ``Param`` instances for each sweep value while keeping validation rules.

        Returns
        -------
        params : Iterable[Param]
            ``Param`` instances with the values to sweep over. Each instance has the same rules and
            constraints as the base ``Param`` object in the ParamGrid, but with a single value set.
        """
        for value in self.iter_values():
            yield self.make_param(value)
