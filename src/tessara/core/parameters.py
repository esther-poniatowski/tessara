"""
tessara.core.parameters
=======================

Error Handling:
TODO: How should the Validator interact with the parameter objects?
TODO: Implement logging for validation errors.



ParameterSet Class:
FIXME: Revisit the implementation of __getattr__ to ensure that nested parameter access (via dotted
attribute names) is robust. One approach is to perform recursive attribute lookups explicitly on the
nested Parameter Set objects rather than relying on a single pass that delegates to the superclass.
TODO: Given that the __getattr__ method is overridden to support dot notation for nested parameter
access, consider implementing a corresponding __setattr__ method. This would permit assignment using
dot notation, provided that care is taken to differentiate between attributes of the Parameter Set
object itself and keys in the underlying data dictionary.
TODO: Implement a dedicated method (for example, convert) within the Parameter Set class that
performs the conversion of arbitrary values into parameter instances. This method should encapsulate
the logic already present in the add method and should be invoked by both __setitem__ and the
constructor.
TODO: Consider implementing a ParamAssigner class that encapsulates the logic for binding a set
of parameters to a specific configuration. This class could be responsible for applying the values
of the configuration to the parameters, but maybe also validating the parameters, and generating
sweep grids.
TODO: Chose whether to access values via self.get(key) or self.data[key]. Encapsulate this logic in
a dedicated accessor method that documents the intended behavior.

Classes
-------
Param
    Define a parameter with properties and constraints for runtime validation.
ParamGrid
    Define a parameter representing a sweep over multiple values.
ParameterSet
    Manage a collection of parameters.
"""
from collections import UserDict
from collections.abc import Iterable
from copy import deepcopy
from typing import Any, Optional, Self, Dict, List, TypeAlias, Tuple

from tessara.errors.validation import (
    OverrideParameterError,
    UnknownParameterError,
)

from tessara.validation.rules import SingleValueRule, MultiValueRule


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
        self.value = None  # set at runtime
        self.default = default
        self.rules = [self.register_rule(rule) for rule in rules] if rules else []

    def set(self, value: Any) -> None:
        """Explicit setter method."""
        self.value = value # call the property setter

    def get(self) -> Any:
        """Explicit getter method."""
        return self.value # call the property getter

    def register_rule(self, rule: SingleValueRule) -> None:
        """Add a rule to validate the parameter."""
        if not isinstance(rule, SingleValueRule):
            raise TypeError(f"Rule '{rule.__class__.__name__}' is not '{SingleValueRule.__name__}'.")
        self.rules.append(rule)

    def copy(self) -> Self:
        """Create a deep copy of the parameter, namely all the rules. Used to set a new value."""
        return deepcopy(self)


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

    Notes
    -----
    Instances of `ParameterSet` behave like dictionaries. All the methods of the UserDict class are
    available for this object, and by extension all the dict methods. The main difference is that
    the values are `Param` objects, which provide additional validation and constraints.

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
            If `param` is already a Param object, it will be added directly and its mode will be
            adjusted to match the mode of the parent ParameterSet.
            Otherwise, a new Param object will be created with the provided value as the default.
            All the other attributes will not be specified, except the mode, which will match the
            mode of the parent ParameterSet.
        """
        if name in self.data:
            raise OverrideParameterError(f"Parameter '{name}' already exists in the ParameterSet.")
        if isinstance(param, Param):
            self.data[name] = param
        else: # convert to Param object with the provided value as the default
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

        Overrides the `__getattr__` method to access the nested value of the parameters as if they
        were attributes of the ParameterSet object. It supports arbitrary levels of nesting and
        works with both direct parameters and nested ParameterSets.

        Parameters
        ----------
        name : str
            Attribute name to access, which may include dots for nested access (e.g.
            'params.level.sublevel').

        Returns
        -------
        Any
            Value of the parameter, if found.

        Raises
        ------
        AttributeError
            If the specified parameter is not found in the ParameterSet.

        Implementation
        --------------
        1. Split the attribute name by dots to obtain a list of keys.
        2. Iteratively traverse the nested structure using these keys.
        3. If a Param object is encountered, return its value.
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
        >>> print(nested_params.model.learning_rate)
        0.01
        >>> print(nested_params.model.layers.hidden_units)
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
        keys = name.split(".") # split the attribute name by dots
        obj = self # start traversal from the current object
        try:
            for key in keys:
                if isinstance(obj, ParameterSet) and key in obj.data:
                    obj = obj.data[key] # update the object to the nested ParameterSet
                    if isinstance(obj, Param): # hit a Param object -> successful query
                        return obj.get()
                else: # delegate to parent class
                    return super().__getattr__(name)
            return obj # end of traversal without error -> query for the final object
        except AttributeError: # if AttributeError at any point, stop traversal
            return super().__getattr__(name) # delegate to parent class

    def get(self, name: str) -> Any:
        """Retrieve the value of a parameter by its name."""
        return self[name].get()

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

    def generate_params(self) -> List[Param]:
        """
        Generate `Param` instances for each sweep value while keeping validation rules.

        Returns
        -------
        params : List[Param]
            `Param` instances with the values to sweep over. Each instance has the same rules and
            constraints as the base `Param` object in the ParamGrid, but with a single value set.
        """
        return [self.param.copy().set(value) for value in self.sweep_values]
