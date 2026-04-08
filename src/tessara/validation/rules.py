"""
tessara.validation.rules
========================

Validation rules for the parameters.

Key Features:

- Flexible Validation: Rules can be applied to single values or multiple values, depending on the
  rule type.
- Custom Error Messages: Each rule generates appropriate error messages when validation fails.
- Extensibility: New rule types can be added by subclassing the base rule classes.

Usage
-----
1. Define a specific constraint by instantiating the appropriate rule class:

>>> type_rule = TypeRule(int)
>>> range_rule = RangeRule(gt=0, lt=10)

2. Apply the rule to a value by calling the `check` method with the value as an argument:

>>> type_rule('abc')
False
>>> range_rule(5)
True

3. If necessary, retrieve the corresponding error indicating the status og the validation:

>>> error = type_rule.get_error('abc')
>>> print(error.message)
"Type 'str' for value 'abc', required 'int'."

Notes
-----
TODO: Are the method names well chosen ?

TODO: Implement composite validation, use logical operators to combine rules::

    composite_rule = AndRule(
        RangeRule(0, 100),
        TypeRule(float),
        OrRule(EvenNumberRule(), PrimeNumberRule())
    )

Classes
-------
Rule
    Base class for all validation rules.
SingleValueRule
    Base class for rules checking the validity of a single value.
TypeRule
    Rule checking if a value is of a specific type.
RangeRule
    Rule checking if a value is within a range.
PatternRule
    Rule checking if a value matches a regular expression pattern.
OptionRule
    Rule checking if a value is in a set of allowed options.
CustomRule
    Rule checking if a value passes a custom validation function.
MultiValueRule
    Rule checking a relationship between multiple parameters.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
import importlib
import logging
import inspect
import re
from typing import Optional, Any, Callable, Generic, TypeVar, Dict, Type

from tessara.core.errors.validation import (
    ValidationError,
    TypeValidationError,
    RangeValidationError,
    PatternValidationError,
    OptionValidationError,
    CustomValidationError,
    RelationValidationError,
    CompositeValidationError,
    RuleDeserializationError,
)

logger = logging.getLogger(__name__)

# --- Base Rule Class ------------------------------------------------------------------------------

E = TypeVar('E', bound=ValidationError)
"""Type variable for the error type associated with a rule."""


class Rule(ABC, Generic[E]):
    """
    Base class for all validation rules.

    Subclasses should implement the `__call__` method to perform the validation check.

    Attributes
    ----------

    Methods
    -------
    check(*values) -> bool
        (Abstract) Check the validity of input values. To be implemented in subclasses.
    get_error(value) -> ValidationError | None
        Generate the output of a rule check for specific value(s).
        If the rule is satisfied, the error remains None.
        Otherwise, it provides context about the failure (input values, constraints, etc.)
        encapsulated in the specific error class associated with this rule.

    See Also
    --------
    SingleValueRule, MultiValueRule
        Specific base classes to distinguish between single and multiple value rules respectively.
    ValidationError
        Custom exception base class to indicate validation errors.

    Examples
    --------
    Template code to define a rule and check the validity of input values:

    >>> rule = Rule(constraint='example')
    >>> rule.check(correct_value)
    True
    >>> outcome_valid = rule.get_error(correct_value)
    None
    >>> outcome_invalid = rule.get_error(wrong_value)
    ValidationError('Invalid value')
    >>> print(outcome_invalid.message)
    ValidationError: "Error message with dynamic placeholders: 'wrong_value'."
    """

    @abstractmethod
    def check(self, *args, **kwargs) -> bool:
        """Check the validity of input values.

        Arguments
        ---------
        *args, **kwargs
            Input values to check (number and types of arguments depend on the rule subclass).
        """
        pass

    def get_error(self, *args, **kwargs) -> E | None:
        """Create error only if validation fails.

        Parameters
        ----------
        *args
            Positional values forwarded to ``check`` and ``create_error``.
        **kwargs
            Keyword values forwarded to ``check`` and ``create_error``.

        Returns
        -------
        E | None
            A validation error when the check fails, ``None`` otherwise.
        """
        if self.check(*args, **kwargs): # call subclass method
            return None
        return self.create_error(*args, **kwargs) # call subclass method

    @abstractmethod
    def create_error(self, *args, **kwargs) -> E :
        """Create a specific error associated with a rule's failure.

        Parameters
        ----------
        *args
            Positional values describing the failed input.
        **kwargs
            Keyword values describing the failed input.
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize a rule to a dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary representation of the rule.

        Raises
        ------
        NotImplementedError
            If the subclass does not implement serialization.
        """
        raise NotImplementedError("Rule serialization is not implemented for this rule.")

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: "RuleRegistry") -> "Rule":
        """Deserialize a rule from a dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Serialized rule payload.
        registry : RuleRegistry
            Registry used for resolving nested rule types.

        Returns
        -------
        Rule
            Reconstructed rule instance.

        Raises
        ------
        NotImplementedError
            If the subclass does not implement deserialization.
        """
        raise NotImplementedError("Rule deserialization is not implemented for this rule.")


class UnknownRule(Rule[ValidationError]):
    """
    Fallback rule for unknown or unsupported serialized rules.

    Parameters
    ----------
    payload : Dict[str, Any]
        Original serialized data that could not be resolved.

    Attributes
    ----------
    payload : Dict[str, Any]
        Stored serialized data for round-tripping.
    """

    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload

    def check(self, *args, **kwargs) -> bool:
        """Return ``False`` unconditionally.

        Parameters
        ----------
        *args
            Ignored positional arguments.
        **kwargs
            Ignored keyword arguments.

        Returns
        -------
        bool
            Always ``False``.
        """
        return False

    def create_error(self, *args, **kwargs) -> RuleDeserializationError:
        """Return a deserialization error wrapping the original payload.

        Parameters
        ----------
        *args
            Ignored positional arguments.
        **kwargs
            Ignored keyword arguments.

        Returns
        -------
        RuleDeserializationError
            Error containing the unresolved payload.
        """
        return RuleDeserializationError(
            "unknown or unsupported rule payload",
            rule_type=self.payload.get("type"),
            payload=self.payload,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the unknown rule back to its original payload.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing the original payload.
        """
        return {"type": "UnknownRule", "payload": self.payload}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: "RuleRegistry") -> "UnknownRule":
        """Reconstruct from the raw payload dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Serialized rule payload.
        registry : RuleRegistry
            Rule registry (unused).

        Returns
        -------
        UnknownRule
            Reconstructed instance.
        """
        return cls(payload=data)


class RuleRegistry:
    """
    Registry for rule serialization and deserialization.

    Provides a central mapping from rule type names to rule classes.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Type[Rule]] = {}

    def register(self, rule_cls: Type[Rule], name: str | None = None) -> None:
        """Register a rule class.

        Parameters
        ----------
        rule_cls : Type[Rule]
            Rule class to register.
        name : str | None
            Key under which to store the class. Defaults to ``rule_cls.__name__``.
        """
        key = name or rule_cls.__name__
        self._registry[key] = rule_cls

    def serialize(self, rule: Rule) -> Dict[str, Any]:
        """Serialize a rule to a dictionary.

        Parameters
        ----------
        rule : Rule
            Rule instance to serialize.

        Returns
        -------
        Dict[str, Any]
            Dictionary representation including a ``"type"`` key.
        """
        data = rule.to_dict()
        if "type" not in data:
            data["type"] = rule.__class__.__name__
        return data

    def deserialize(self, data: Dict[str, Any]) -> Rule:
        """Deserialize a rule from a dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Serialized rule payload containing at least a ``"type"`` key.

        Returns
        -------
        Rule
            Reconstructed rule instance.

        Raises
        ------
        RuleDeserializationError
            If the rule type is missing or unknown.
        """
        rule_type = data.get("type")
        if not rule_type:
            raise RuleDeserializationError("missing rule type", payload=data)
        rule_cls = self._registry.get(rule_type)
        if rule_cls is None:
            raise RuleDeserializationError(
                "unknown rule type",
                rule_type=rule_type,
                payload=data,
            )
        try:
            return rule_cls.from_dict(data, registry=self)
        except Exception as exc:
            raise RuleDeserializationError(
                str(exc),
                rule_type=rule_type,
                payload=data,
            ) from exc

    @staticmethod
    def _type_to_spec(expected_type: type | tuple[type]) -> list[dict]:
        if isinstance(expected_type, tuple):
            types = expected_type
        else:
            types = (expected_type,)
        return [
            {"module": t.__module__, "qualname": t.__qualname__}
            for t in types
        ]

    @staticmethod
    def _spec_to_type(specs: list[dict]) -> type | tuple[type]:
        types = []
        for spec in specs:
            module = importlib.import_module(spec["module"])
            current = module
            for part in spec["qualname"].split("."):
                current = getattr(current, part)
            types.append(current)
        if len(types) == 1:
            return types[0]
        return tuple(types)


# --- Single Value Rules ---------------------------------------------------------------------------

class SingleValueRule(Rule[E]):
    """
    Parameter-specific rule, checking the validity of a single value.

    Notes
    -----
    Compared to the base `Rule` class, this class specializes its methods' signatures to
    handle a single value.

    Its nature is checked in the Validator class to trigger the appropriate logic for passing a
    *single* value.
    """
    @abstractmethod
    def check(self, value) -> bool:
        """Check the validity of a single value.

        Parameters
        ----------
        value
            Value to validate.

        Returns
        -------
        bool
            ``True`` if the value is valid.
        """
        pass

    @abstractmethod
    def create_error(self, value) -> E | None:
        """Create the error for a single failed value.

        Parameters
        ----------
        value
            Value that failed validation.

        Returns
        -------
        E | None
            Specific validation error for the failure.
        """
        pass


class TypeRule(SingleValueRule[TypeValidationError]):
    """
    Rule checking if a value is a specific type.

    Parameters
    ----------
    expected_type : type | tuple[type]
        Required type(s) for the value.

    Raises
    ------
    TypeError
        If the expected type is not a type or a tuple of types.

    Attributes
    ----------
    expected_type : type | tuple[type]
        Required type(s) for the value.
        If a tuple is provided, the value must be one of the types in the tuple.
        Each type can be a built-in Python type or a custom class.

    See Also
    --------
    TypeValidationError
        Custom exception raised when a parameter has an invalid type.
    isinstance(obj, class_or_tuple)
        Built-in Python function to check if an object is an instance of a class or of a subclass
        thereof.
        If a tuple is provided, the type check is performed against each element in the tuple (OR
        logic).

    Examples
    --------
    For a unique expected type:

    >>> rule = TypeRule(int)
    >>> rule.check('abc')
    False

    For several allowed types:

    >>> rule = TypeRule((str, float))
    >>> rule.check(1)
    False
    """
    def __init__(self, expected_type: type | tuple[type]):
        if not isinstance(expected_type, (type, tuple)):
            raise TypeError(f"Expected a type or a tuple of types, got {type(expected_type)}")
        self.expected_type = expected_type

    def check(self, value) -> bool:
        """Return ``True`` if *value* is an instance of the expected type.

        Parameters
        ----------
        value
            Value to type-check.

        Returns
        -------
        bool
            ``True`` if *value* matches the expected type.
        """
        return isinstance(value, self.expected_type)

    def create_error(self, value) -> TypeValidationError:
        """Create a type-validation error for *value*.

        Parameters
        ----------
        value
            Value that failed the type check.

        Returns
        -------
        TypeValidationError
            Error describing the type mismatch.
        """
        return TypeValidationError(value, self.expected_type)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the rule to a dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing the expected type specification.
        """
        return {
            "type": "TypeRule",
            "expected_type": RuleRegistry._type_to_spec(self.expected_type),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "TypeRule":
        """Reconstruct from a serialized dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Serialized rule payload.
        registry : RuleRegistry
            Registry used for type resolution.

        Returns
        -------
        TypeRule
            Reconstructed instance.
        """
        expected_type = registry._spec_to_type(data["expected_type"])
        return cls(expected_type)


class RangeRule(SingleValueRule[RangeValidationError]):
    """
    Rule checking if a value is within a range.

    Parameters
    ----------
    ge : float, optional
        Minimum value (inclusive).
    gt : float, optional
        Minimum value (exclusive).
    le : float, optional
        Maximum value (inclusive).
    lt : float, optional
        Maximum value (exclusive).

    Attributes
    ----------
    ge, lt, le, gt : Optional[float]
        Range boundaries for the parameter value (greater or equal, less than, less or equal,
        greater).

    See Also
    --------
    RangeValidationError
        Custom exception raised when a parameter is out of bounds.

    Examples
    --------
    >>> rule = RangeRule(ge=0, lt=10)
    >>> rule.check(-1)
    False
    """
    def __init__(self,
                 ge: Optional[float]=None,
                 gt: Optional[float]=None,
                 le: Optional[float]=None,
                 lt: Optional[float]=None
                ):
        self.ge = ge
        self.gt = gt
        self.le = le
        self.lt = lt

    def check(self, value) -> bool:
        """Return ``True`` if *value* falls within the configured bounds.

        Parameters
        ----------
        value
            Value to check against the range boundaries.

        Returns
        -------
        bool
            ``True`` if *value* satisfies all configured bounds.
        """
        constraints = [
            (self.gt, lambda v, c: v > c),
            (self.ge, lambda v, c: v >= c),
            (self.lt, lambda v, c: v < c),
            (self.le, lambda v, c: v <= c)
        ]
        try:
            return all(func(value, constraint) for constraint, func in constraints if constraint is not None)
        except TypeError:
            # Comparison not supported between value type and constraint type
            return False

    def create_error(self, value) -> RangeValidationError:
        """Create a range-validation error for *value*.

        Parameters
        ----------
        value
            Value that fell outside the range.

        Returns
        -------
        RangeValidationError
            Error describing which bounds were violated.
        """
        return RangeValidationError(value, ge=self.ge, gt=self.gt, le=self.le, lt=self.lt)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the rule to a dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing the range boundaries.
        """
        return {
            "type": "RangeRule",
            "ge": self.ge,
            "gt": self.gt,
            "le": self.le,
            "lt": self.lt,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "RangeRule":
        """Reconstruct from a serialized dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Serialized rule payload.
        registry : RuleRegistry
            Rule registry (unused).

        Returns
        -------
        RangeRule
            Reconstructed instance.
        """
        return cls(ge=data.get("ge"), gt=data.get("gt"), le=data.get("le"), lt=data.get("lt"))


class PatternRule(SingleValueRule[PatternValidationError]):
    r"""
    Rule checking if a value matches a regular expression pattern.

    Parameters
    ----------
    pattern : str
        Regular expression pattern to match, if the parameter value is a string.

    Raises
    ------
    ValueError
        If the pattern is not a valid regular expression.

    Attributes
    ----------
    pattern : str
        Regular expression pattern to match, if the parameter value is a string.

    See Also
    --------
    PatternValidationError
        Custom exception raised when a parameter does not match a regular expression pattern.

    Examples
    --------
    Match one or more digits:

    >>> rule = PatternRule(r"\d+")
    >>> rule.check("abc")
    False
    """
    def __init__(self, pattern: str):
        try:
            self.pattern = re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {pattern}") from exc

    def check(self, value) -> bool:
        """Return ``True`` if *value* matches the compiled pattern.

        Parameters
        ----------
        value
            Value to match against the pattern.

        Returns
        -------
        bool
            ``True`` if the string representation of *value* matches.
        """
        return bool(self.pattern.match(str(value)))

    def create_error(self, value) -> PatternValidationError:
        """Create a pattern-validation error for *value*.

        Parameters
        ----------
        value
            Value that did not match the pattern.

        Returns
        -------
        PatternValidationError
            Error describing the pattern mismatch.
        """
        return PatternValidationError(value, self.pattern)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the rule to a dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing the pattern string.
        """
        return {"type": "PatternRule", "pattern": self.pattern.pattern}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "PatternRule":
        """Reconstruct from a serialized dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Serialized rule payload.
        registry : RuleRegistry
            Rule registry (unused).

        Returns
        -------
        PatternRule
            Reconstructed instance.
        """
        return cls(pattern=data["pattern"])


class OptionRule(SingleValueRule[OptionValidationError]):
    """
    Rule checking if a value is in a set of allowed options.

    Parameters
    ----------
    options : Iterable
        Allowed values for the parameter.

    Attributes
    ----------
    options : Set[Any]
        Allowed values for the parameter.

    See Also
    --------
    OptionValidationError
        Custom exception raised when a parameter's value does not belong to the allowed options.

    Examples
    --------
    >>> rule = OptionRule([1, 2, 3])
    >>> rule.check(4)
    False
    """
    def __init__(self, options: Iterable):
        self.options = set(options) # convert to set for faster lookup

    def check(self, value) -> bool:
        """Return ``True`` if *value* belongs to the allowed options.

        Parameters
        ----------
        value
            Value to look up in the allowed set.

        Returns
        -------
        bool
            ``True`` if *value* is in the options.
        """
        return value in self.options

    def create_error(self, value) -> OptionValidationError:
        """Create an option-validation error for *value*.

        Parameters
        ----------
        value
            Value that was not among the allowed options.

        Returns
        -------
        OptionValidationError
            Error listing the allowed options.
        """
        return OptionValidationError(value, self.options)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the rule to a dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing the allowed options.
        """
        return {"type": "OptionRule", "options": list(self.options)}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "OptionRule":
        """Reconstruct from a serialized dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Serialized rule payload.
        registry : RuleRegistry
            Rule registry (unused).

        Returns
        -------
        OptionRule
            Reconstructed instance.
        """
        return cls(options=data["options"])


class CustomRule(SingleValueRule[CustomValidationError]):
    """
    Rule checking if a value passes a custom validation function.

    Parameters
    ----------
    func : Callable[[Any], bool]
        Custom validation function. It should take a single argument (value) and return a boolean.

    Attributes
    ----------
    func : Callable[[Any], bool]
        Custom validation function. It should take a single argument (value) and return a boolean.

    See Also
    --------
    CustomValidationError
        Custom exception raised when a custom validation rule fails.

    Examples
    --------
    >>> def is_even(x):
    ...     return x % 2 == 0
    >>> rule = CustomRule(is_even)
    >>> rule.check(5)
    False
    """
    def __init__(self, func: Callable[[Any], bool]):
        self.func = func

    def check(self, value) -> bool:
        """Return ``True`` if the custom function accepts *value*.

        Parameters
        ----------
        value
            Value to pass to the custom function.

        Returns
        -------
        bool
            Result of the custom validation function.
        """
        return self.func(value)

    def create_error(self, value) -> CustomValidationError:
        """Create a custom-validation error for *value*.

        Parameters
        ----------
        value
            Value that failed the custom validation.

        Returns
        -------
        CustomValidationError
            Error referencing the custom function.
        """
        return CustomValidationError(value, self.func)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the rule to a dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary with function metadata (not re-importable).
        """
        func = self.func
        qualname = getattr(func, "__qualname__", None)
        module = getattr(func, "__module__", None)
        return {
            "type": "CustomRule",
            "serializable": False,
            "module": module,
            "qualname": qualname,
            "repr": repr(func),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "CustomRule":
        """Reconstruct from a serialized dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Serialized rule payload.
        registry : RuleRegistry
            Rule registry (unused).

        Returns
        -------
        CustomRule
            Never returned; always raises.

        Raises
        ------
        ValueError
            Always, because callables cannot be deserialized.
        """
        raise ValueError("CustomRule cannot be deserialized without a callable.")


# --- Composite Rules ------------------------------------------------------------------------------

class AndRule(SingleValueRule[CompositeValidationError]):
    """
    Composite rule that requires ALL sub-rules to pass (logical AND).

    All sub-rules must be satisfied for the value to be valid.

    Parameters
    ----------
    *rules : SingleValueRule
        Sub-rules that must all pass.

    Attributes
    ----------
    rules : List[SingleValueRule]
        Sub-rules that must all pass.

    Examples
    --------
    Combine type and range validation:

    >>> rule = AndRule(
    ...     TypeRule(int),
    ...     RangeRule(gt=0, lt=100),
    ... )
    >>> rule.check(50)
    True
    >>> rule.check(-5)
    False

    Nested composite rules:

    >>> rule = AndRule(
    ...     TypeRule(int),
    ...     OrRule(RangeRule(lt=0), RangeRule(gt=100)),
    ... )
    >>> rule.check(-5)  # int AND (negative OR > 100)
    True
    """
    def __init__(self, *rules: SingleValueRule):
        if not rules:
            raise ValueError("AndRule requires at least one sub-rule.")
        for rule in rules:
            if not isinstance(rule, SingleValueRule):
                raise TypeError(f"All rules must be SingleValueRule instances, got {type(rule)}")
        self.rules = list(rules)

    def check(self, value) -> bool:
        """Return ``True`` if all sub-rules accept *value*.

        Parameters
        ----------
        value
            Value to validate against every sub-rule.

        Returns
        -------
        bool
            ``True`` if all sub-rules pass.
        """
        return all(rule.check(value) for rule in self.rules)

    def create_error(self, value) -> CompositeValidationError:
        """Collect errors from all failing sub-rules.

        Parameters
        ----------
        value
            Value that failed at least one sub-rule.

        Returns
        -------
        CompositeValidationError
            Composite error aggregating individual failures.
        """
        errors = []
        rule_ids: list[str] = []
        for rule in self.rules:
            error = rule.get_error(value)
            if error is not None:
                errors.append(error)
                rule_ids.append(rule.__class__.__name__)
        return CompositeValidationError(errors, "AND", value=value, rule_ids=rule_ids)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the rule and its sub-rules to a dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing serialized sub-rules.
        """
        return {
            "type": "AndRule",
            "rules": [rule.to_dict() for rule in self.rules],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "AndRule":
        """Reconstruct from a serialized dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Serialized rule payload.
        registry : RuleRegistry
            Registry used to deserialize sub-rules.

        Returns
        -------
        AndRule
            Reconstructed instance.
        """
        rules = [registry.deserialize(rule_data) for rule_data in data.get("rules", [])]
        return cls(*rules)


class OrRule(SingleValueRule[CompositeValidationError]):
    """
    Composite rule that requires AT LEAST ONE sub-rule to pass (logical OR).

    At least one sub-rule must be satisfied for the value to be valid.

    Parameters
    ----------
    *rules : SingleValueRule
        Sub-rules where at least one must pass.

    Attributes
    ----------
    rules : List[SingleValueRule]
        Sub-rules where at least one must pass.

    Examples
    --------
    Accept either string or integer:

    >>> rule = OrRule(
    ...     TypeRule(str),
    ...     TypeRule(int),
    ... )
    >>> rule.check("hello")
    True
    >>> rule.check(42)
    True
    >>> rule.check(3.14)
    False

    Complex condition - value is either small or large (not medium):

    >>> rule = OrRule(
    ...     RangeRule(lt=10),
    ...     RangeRule(gt=100),
    ... )
    >>> rule.check(5)   # Small: passes
    True
    >>> rule.check(50)  # Medium: fails
    False
    >>> rule.check(200) # Large: passes
    True
    """
    def __init__(self, *rules: SingleValueRule):
        if not rules:
            raise ValueError("OrRule requires at least one sub-rule.")
        for rule in rules:
            if not isinstance(rule, SingleValueRule):
                raise TypeError(f"All rules must be SingleValueRule instances, got {type(rule)}")
        self.rules = list(rules)

    def check(self, value) -> bool:
        """Return ``True`` if at least one sub-rule accepts *value*.

        Parameters
        ----------
        value
            Value to validate against the sub-rules.

        Returns
        -------
        bool
            ``True`` if any sub-rule passes.
        """
        return any(rule.check(value) for rule in self.rules)

    def create_error(self, value) -> CompositeValidationError:
        """Collect errors from all failing sub-rules.

        Parameters
        ----------
        value
            Value that failed all sub-rules.

        Returns
        -------
        CompositeValidationError
            Composite error aggregating individual failures.
        """
        errors = []
        rule_ids: list[str] = []
        for rule in self.rules:
            error = rule.get_error(value)
            if error is not None:
                errors.append(error)
                rule_ids.append(rule.__class__.__name__)
        return CompositeValidationError(errors, "OR", value=value, rule_ids=rule_ids)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the rule and its sub-rules to a dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing serialized sub-rules.
        """
        return {
            "type": "OrRule",
            "rules": [rule.to_dict() for rule in self.rules],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "OrRule":
        """Reconstruct from a serialized dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Serialized rule payload.
        registry : RuleRegistry
            Registry used to deserialize sub-rules.

        Returns
        -------
        OrRule
            Reconstructed instance.
        """
        rules = [registry.deserialize(rule_data) for rule_data in data.get("rules", [])]
        return cls(*rules)


# --- Multi Value Rules ----------------------------------------------------------------------------

class MultiValueRule(Rule[RelationValidationError]):
    """
    Rule checking a relationship or dependency between multiple parameters.

    Parameters
    ----------
    func : Callable[..., bool]
        Function which takes several values, checks a relationship between them, and returns a
        boolean.

    Attributes
    ----------
    func : Callable
        Function which takes several values, checks a relationship between them, and returns a
        boolean.

    Notes
    -----
    Compared to the base `Rule` class, this class specializes the signatures of its methods to
    handle a variable number of values. Contrary to the `SingleValueRule` class, there is no need to
    override the `check` method, as the parent class already handles multiple values.

    This type is checked in the Validator class to trigger the appropriate logic for passing
    multiple values.

    Examples
    --------
    Define a rule that checks if one parameter is greater than another:

    >>> def is_greater_than(x, y):
    ...     return x > y
    >>> rule = RelationalRule(is_greater_than)

    Pass values as positional arguments:

    >>> rule.check(1, 2)
    False

    Pass values as keyword arguments:

    >>> rule.check(x=1, y=2)
    False
    """
    def __init__(self, func: Callable[..., bool]):
        self.func = func

    def check(self, *args, **kwargs) -> bool:
        """Delegate to the wrapped function.

        Parameters
        ----------
        *args
            Positional values forwarded to the wrapped function.
        **kwargs
            Keyword values forwarded to the wrapped function.

        Returns
        -------
        bool
            Result of the wrapped function.
        """
        return self.func(*args, **kwargs)

    def create_error(self, *args, **kwargs) -> RelationValidationError:
        """Create a relation-validation error for the given values.

        Parameters
        ----------
        *args
            Positional values that failed the relation check.
        **kwargs
            Keyword values that failed the relation check.

        Returns
        -------
        RelationValidationError
            Error referencing the wrapped function and its inputs.
        """
        return RelationValidationError(self.func, args=args, kwargs=kwargs)


DEFAULT_RULE_REGISTRY = RuleRegistry()
DEFAULT_RULE_REGISTRY.register(TypeRule)
DEFAULT_RULE_REGISTRY.register(RangeRule)
DEFAULT_RULE_REGISTRY.register(PatternRule)
DEFAULT_RULE_REGISTRY.register(OptionRule)
DEFAULT_RULE_REGISTRY.register(CustomRule)
DEFAULT_RULE_REGISTRY.register(AndRule)
DEFAULT_RULE_REGISTRY.register(OrRule)
DEFAULT_RULE_REGISTRY.register(UnknownRule)
