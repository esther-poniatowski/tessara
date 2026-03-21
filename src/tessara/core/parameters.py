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

Notes
-----
- Parameters support validation rules via the `rules` attribute
- Nested ParameterSets can be accessed using dot notation (e.g., `params.model.lr`)
- Values can be set with optional strict validation via `param.set(value, strict=True)`
- Use `param.is_set` to distinguish between "not set" and "explicitly set to None"
"""
from collections import UserDict
from collections.abc import Iterable
from copy import deepcopy
from typing import Any, Optional, Self, Dict, List, TypeAlias, Tuple

from tessara.core.errors.handling import (
    OverrideParameterError,
    UnknownParameterError,
)

from tessara.validation.rules import SingleValueRule, MultiValueRule, RuleRegistry, DEFAULT_RULE_REGISTRY


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
    rules : List[Rule]
        Rules (constraints) to validate the parameter value.

    Methods
    -------
    set(value: Any)
        Set parameter value at runtime with optional validation.
    get() -> Any
        Retrieve the set value or default.
    register_rule(rule: Rule)
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
    The `Param` class serves as a static representation of a parameter with constraints. It does not
    perform validation itself.

    See Also
    --------
    Rule
        Base class for all validation rules.
    """
    def __init__(
        self,
        default: Optional[Any] = None,
        rules: Optional[Iterable[SingleValueRule]] = None,
    ) -> None:
        self._value = _UNSET  # sentinel to distinguish "not set" from "set to None"
        self.default = default
        self.rules = []  # Initialize first
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

        Note: Use `is_set` to distinguish between "set to None" and "not set".
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

    def register_rule(self, rule: SingleValueRule) -> None:
        """Add a rule to validate the parameter."""
        if not isinstance(rule, SingleValueRule):
            raise TypeError(f"Rule '{rule.__class__.__name__}' is not '{SingleValueRule.__name__}'.")
        self.rules.append(rule)

    def copy(self) -> Self:
        """Create a deep copy of the parameter, namely all the rules. Used to set a new value."""
        return deepcopy(self)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the parameter to a dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary representation of the parameter containing:
            - 'value': Current runtime value (if set)
            - 'default': Default value (if set)
            - 'rules': List of rule class names (for documentation, not reconstruction)

        Notes
        -----
        Rules are serialized as class names only for documentation purposes.
        Full rule reconstruction requires additional logic or custom serializers.

        Example
        -------
        >>> param = Param(default=10, rules=[TypeRule(int), RangeRule(gt=0)])
        >>> param.to_dict()
        {'value': None, 'default': 10, 'rules': ['TypeRule', 'RangeRule']}
        """
        return {
            "value": None if self._value is _UNSET else self._value,
            "default": self.default,
            "rules": [DEFAULT_RULE_REGISTRY.serialize(rule) for rule in self.rules],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry | None = None) -> "Param":
        """
        Create a Param instance from a dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary containing 'value' and/or 'default' keys.
            Note: Rules are not reconstructed (would require a rule registry).

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
        registry = registry or DEFAULT_RULE_REGISTRY
        rules_data = data.get("rules", [])
        rules = [registry.deserialize(rule_data) for rule_data in rules_data]
        param = cls(default=data.get("default"), rules=rules)
        if "value" in data and data["value"] is not None:
            param.set(data["value"])
        return param


# --------------------------------------------------------------------------------------------------

Targets : TypeAlias = List[str] | Dict[str, str]
"""Type alias for target specifications in relation rules: list of strings or dictionary of strings."""

RelationRule : TypeAlias = Tuple[MultiValueRule, Targets]
"""Type alias for relation rule specifications: tuple of a rule instance and targets."""

class ParameterSet(UserDict[str, Param]):
    """
    Manage a collection of parameters.

    Attributes
    ----------
    data : Dict[str, Param]
        Underlying dictionary of parameters, inherited from UserDict.

    Methods
    -------
    get(key: str) -> Param
        Retrieve a parameter by name.
    override(**overrides) -> ParameterSet
        Create a new parameter set with modifications.
    apply_config(config: Dict[str, Any])
        Apply runtime configuration values to the parameters.

    Examples
    --------
    Create a parameter set with two parameters:

    >>> params = ParameterSet(
    ...     param1=Param(default=42, rules=RangeRule(gt=0)),
    ...     param2=Param(rules=TypeRule(str))
    ... )

    Retrieve a parameter by name:

    >>> params.get('param1')
    Param(default=42)

    Override a parameter:

    >>> new_params = params.override(param1=Param(default=7))
    >>> new_params.get('param1')

    Apply a configuration to the parameters:

    >>> config = {'param1': 7, 'param2': 'bar'}
    >>> params.apply_config(config)
    >>> params.get('param1')
    7

    Use dot notation for nested access and assignment:

    >>> params.model.lr = 0.01  # Sets value of nested parameter
    >>> print(params.model.lr)  # Gets value: 0.01

    Notes
    -----
    Instances of `ParameterSet` behave like dictionaries. All the methods of the UserDict class are
    available for this object, and by extension all the dict methods. The main difference is that
    the values are `Param` objects, which provide additional validation and constraints.

    Dot notation access returns `Param` or `ParameterSet` objects. Use `get_value()` to retrieve
    values directly when needed.

    The `add`, `remove` and `override` methods provide flexibility for hierarchical construction of
    parameter sets that can mirror a hierarchy of workflows, from the most general to the most
    specific. This behavior also aligns with the hierarchical configurations of the YAML files.

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
            `rule`: MultiValueRule instance to apply to the parameters.
            `targets`: Specification of the parameters targeted by the rule. Possibilities:
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

        Implementation
        --------------
        Choice of the candidate set to pass to the constructor:

        - If the first argument is a dictionary, use it as the candidate set.
        - If the first argument is not a dictionary, use the keyword arguments.

        The `relation_rules` attribute is type hinted as a list of tuples, where each tuple
        contains a rule instance and a target specification. This type is preferred to a dictionary
        with rule instances as keys, in order to facilitate serialization.
        """
        super().__init__() # initialize with the parent class constructor (UserDict)
        candidates = args[0] if args and isinstance(args[0], dict) else kwargs
        for param in candidates:
            self.add(param, candidates[param])
        self.relation_rules = []
        if relation_rules is not None:
            if isinstance(relation_rules, Iterable):
                for rule, targets in relation_rules:
                    self.register_relation_rule(rule, targets)
            else:
                raise TypeError(f"Pass rules in an iterable")

    def add(self, name: str, param: Any):
        """
        Add a new parameter in the set with a unique name.

        Arguments
        ---------
        param : Any
            If `param` is already a Param or ParameterSet, it will be added directly.
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
        Override the `__setitem__` method to ensure that the value is a valid Param object.

        This method is triggered with the following syntax: `params['key'] = value`.
        """
        self.add(name, param)

    def __getattr__(self, name: str) -> Any:
        """
        Access nested parameters using the dot notation (e.g. 'params.level.sublevel').

        Overrides the `__getattr__` method to access nested parameters as attributes. It supports
        arbitrary levels of nesting and works with both direct parameters and nested ParameterSets.

        Parameters
        ----------
        name : str
            Attribute name to access, which may include dots for nested access (e.g.
            'params.level.sublevel').

        Returns
        -------
        Any
            Param or ParameterSet object, if found.

        Raises
        ------
        AttributeError
            If the specified parameter is not found in the ParameterSet.

        Implementation
        --------------
        1. Split the attribute name by dots to obtain a list of keys.
        2. Iteratively traverse the nested structure using these keys.
        3. If a Param object is encountered, return it.
        4. If a nested ParameterSet is encountered, continue traversing.
        5. If the traversal completes without finding a Param, return the final object (since the
           query might be for a nested ParameterSet).
        6. If any key is not found during traversal, fall back to standard attribute access.

        Example
        -------
        Define a nested parameter set and access its values using dot notation:

        >>> nested_params = ParameterSet(
        ...     model=ParameterSet(
        ...         learning_rate=Param(default=0.01),
        ...         layers=ParameterSet(
        ...             hidden_units=Param(default=128)
        ...         )
        ...     )
        ... )
        >>> print(nested_params.model.learning_rate.get())
        0.01
        >>> print(nested_params.model.layers.hidden_units.get())
        128
        >>> print(nested_params.non_existent)
        AttributeError: No parameter 'non_existent' in the ParameterSet.

        Note
        ----
        The standard __getattr__ method (overridden here) is typically triggered with the following
        syntax: `params.name`.
        TODO: If multiple dots were used with the standard method, what would happen ? I do not get
        how, with the new method, the name can be interpreted as the full sequence after the first
        dot. I was expecting that only the first "level" would enter the current method, retrieve
        the corresponding object, and the next names would be passed to the original __getattr__
        method of the retrieved object.
        """
        # Handle special attributes (dunder methods, private attrs) - delegate to parent
        # This prevents recursion during deepcopy and pickle operations
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        # Ensure 'data' attribute exists before accessing it
        if "data" not in self.__dict__:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        keys = name.split(".") # split the attribute name by dots
        obj: Any = self # start traversal from the current object
        try:
            for key in keys:
                if isinstance(obj, ParameterSet) and key in obj.data:
                    obj = obj.data[key] # update the object to the nested ParameterSet
                else: # delegate to parent class
                    raise AttributeError(f"No parameter '{name}' in the ParameterSet.")
            return obj # end of traversal without error -> query for the final object
        except (AttributeError, KeyError):
            raise AttributeError(f"No parameter '{name}' in the ParameterSet.")

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set parameter values using dot notation (e.g. 'params.learning_rate = 0.01').

        Supports assignment to both direct parameters and nested ParameterSets.
        Reserved attributes (like 'data', 'relation_rules') are set normally.

        Parameters
        ----------
        name : str
            Attribute name to set.
        value : Any
            Value to assign. If the target is a Param, sets its value.
            If the target is a ParameterSet, replaces it.

        Raises
        ------
        AttributeError
            If the specified parameter is not found in the ParameterSet.

        Example
        -------
        >>> params = ParameterSet(
        ...     model=ParameterSet(
        ...         lr=Param(default=0.01),
        ...     )
        ... )
        >>> params.model.lr = 0.001  # Sets the value of the 'lr' parameter
        >>> print(params.model.lr)
        0.001

        Note
        ----
        This method differentiates between:
        1. Reserved attributes of the ParameterSet object itself (stored normally)
        2. Parameter keys in the underlying data dictionary (set via Param.set())
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
        """Retrieve the value of a parameter by its name."""
        return self[name].get()

    def get_value(self, name: str) -> Any:
        """
        Retrieve a parameter value by name, supporting dot notation.

        Returns the current value if set, otherwise the default.
        """
        if "." not in name:
            return self.get(name)
        parts = name.split(".")
        obj: Any = self
        for part in parts:
            if isinstance(obj, ParameterSet) and part in obj.data:
                obj = obj.data[part]
            else:
                raise UnknownParameterError(f"No parameter '{name}' in the ParameterSet.")
        if isinstance(obj, Param):
            return obj.get()
        raise UnknownParameterError(f"No parameter '{name}' in the ParameterSet.")

    def register_rule(self, target: str, rule: SingleValueRule) -> None:
        """
        Register a rule for a specific parameter already present in the set.

        Arguments
        ---------
        target : str
            Name of the parameter targeted by the rule.
        rule : SingleValueRule
            Validation rule to apply to the parameter.

        Examples
        --------
        Add a custom rule to a parameter:

        >>> params = ParameterSet(param1=Param(rules=[TypeRule(int)]))
        >>> def is_even(value: Any) -> bool:
        ...     return value % 2 == 0
        >>> params.register_rule('param1', CustomRule(is_even))
        >>> print(params.param1.rules)
        [TypeRule(int), CustomRule(is_even)]
        """
        if target in self.data:
            self.data[target].register_rule(rule)
        else:
            raise UnknownParameterError(f"No parameter '{target}' in the ParameterSet.")

    def register_relation_rule(self, rule: MultiValueRule, targets: Targets) -> None:
        """
        Register a relation rule between multiple parameters, for cross-parameter dependencies.

        Arguments
        ---------
        rule : RelationalRule
            Relational validation rule to apply to the parameters.
        targets : List[str] | Dict[str, str]
            Names of the parameters targeted by the rule.

        Examples
        --------
        Define a relation rule that checks if one parameter is greater than another:

        >>> params = ParameterSet(param1=Param(default=1), param2=Param(default=2))
        >>> def is_greater_than(x: int, y: int) -> bool:
        ...     return x > y
        >>> greater_than_rule = RelationalRule(is_greater_than)

        Register the rule by specifying the targets as a list:

        >>> params.register_relation_rule(greater_than_rule, ['param1', 'param2'])

        Register the rule by specifying the targets as a dictionary:

        >>> params.register_global_rule(greater_than_rule, targets={'x': 'param1', 'y': 'param2'})

        Notes
        -----
        The format of the targets determines the internal call to the rule function.

        If the targets are provided as a list, then the parameters are passed as positional
        arguments:

        >>> is_greater_than(params.param1, params.param2)

        If the targets are provided as a dictionary, then the parameters are passed as keyword
        arguments:

        >>> is_greater_than(x=params.param1, y=params.param2)
        """
        if not isinstance(rule, MultiValueRule):
            raise TypeError(f"Rule '{rule.__class__.__name__}' is not '{MultiValueRule.__name__}'.")
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
            Dictionary to convert. Structure depends on `values_only`.
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
        >>> params.lr
        0.01

        From full serialization:

        >>> data = {'lr': {'value': 0.01, 'default': 0.001}}
        >>> params = ParameterSet.from_dict(data)

        Nested dictionaries become nested ParameterSets:

        >>> data = {'model': {'lr': 0.01}}
        >>> params = ParameterSet.from_dict(data, values_only=True)
        >>> params.model.lr
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


# -------------------------------------------------------------------------------------------------

class ParamGrid:
    """
    Wrapper encapsulating a parameter intended for sweeping over multiple values.

    To represent all parameters uniformly in the ParameterSet, this wrapper behaves like a basic
    parameter for rule related behavior, except that:

    - It also stores a list of values that need to be traversed during a parameter sweep.
    - It does not store a value, as it is intended to be used as a template for generating multiple
      `Param` instances.

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
    generate_params() -> List[Param]
        Generate individual `Param` instances for each sweep value.
    register_rule(rule: SingleValueRule)
        Delegate rule registration to the underlying `Param` instance.

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

    def register_rule(self, rule: SingleValueRule) -> None:
        """Delegate rule registration to the underlying `Param` instance."""
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
        Generate `Param` instances for each sweep value while keeping validation rules.

        Returns
        -------
        params : List[Param]
            `Param` instances with the values to sweep over. Each instance has the same rules and
            constraints as the base `Param` object in the ParamGrid, but with a single value set.
        """
        for value in self.iter_values():
            yield self.make_param(value)
