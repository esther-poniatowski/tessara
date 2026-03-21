"""
tessara.validation.rules
========================

Validation rules for the parameters.

Key Features:

- Flexible Validation: Rules can be applied to single values or multiple values, depending on the
  rule type.
- Custom Error Messages: Each rule generates appropriate error messages when validation fails.
- Extensibility: New rule types can be added by subclassing the base rule classes.

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


TODO: Are the method names well chosen ?

TODO: Implement composite validation, use logical operators to combine rules:
```
composite_rule = AndRule(
    RangeRule(0, 100),
    TypeRule(float),
    OrRule(EvenNumberRule(), PrimeNumberRule())
)
```
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
    RelationValidationError
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

    See Also
    --------
    SingleValueRule, MultiValueRule
        Specific base classes to distinguish between single and multiple value rules respectively.
    ValidationError
        Custom exception base class to indicate validation errors.
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
        """Create error only if validation fails"""
        if self.check(*args, **kwargs): # call subclass method
            return None
        return self.create_error(*args, **kwargs) # call subclass method

    @abstractmethod
    def create_error(self, *args, **kwargs) -> E :
        """Factory method to create a specific error associated with a rule's failure."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize a rule to a dictionary."""
        raise NotImplementedError("Rule serialization is not implemented for this rule.")

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: "RuleRegistry") -> "Rule":
        """Deserialize a rule from a dictionary."""
        raise NotImplementedError("Rule deserialization is not implemented for this rule.")


class UnknownRule(Rule[ValidationError]):
    """Fallback rule for unknown or unsupported serialized rules."""

    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload

    def check(self, *args, **kwargs) -> bool:
        return True

    def create_error(self, *args, **kwargs) -> ValidationError:
        return ValidationError()

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "UnknownRule", "payload": self.payload}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: "RuleRegistry") -> "UnknownRule":
        return cls(payload=data)


class RuleRegistry:
    """
    Registry for rule serialization and deserialization.

    Provides a central mapping from rule type names to rule classes.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Type[Rule]] = {}

    def register(self, rule_cls: Type[Rule], name: str | None = None) -> None:
        """Register a rule class."""
        key = name or rule_cls.__name__
        self._registry[key] = rule_cls

    def serialize(self, rule: Rule) -> Dict[str, Any]:
        """Serialize a rule to a dictionary."""
        data = rule.to_dict()
        if "type" not in data:
            data["type"] = rule.__class__.__name__
        return data

    def deserialize(self, data: Dict[str, Any]) -> Rule:
        """Deserialize a rule from a dictionary."""
        rule_type = data.get("type")
        if not rule_type:
            logger.warning("Missing rule type in serialized rule data.")
            return UnknownRule(data)
        rule_cls = self._registry.get(rule_type)
        if rule_cls is None:
            logger.warning("Unknown rule type '%s'.", rule_type)
            return UnknownRule(data)
        try:
            return rule_cls.from_dict(data, registry=self)
        except Exception as exc:
            logger.warning("Failed to deserialize rule '%s': %s", rule_type, exc)
            return UnknownRule(data)

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
        pass

    @abstractmethod
    def create_error(self, value) -> E | None:
        pass


class TypeRule(SingleValueRule[TypeValidationError]):
    """
    Rule checking if a value is a specific type.

    Attributes
    ----------
    expected_type : type | tuple[type]
        Required type(s) for the value.
        If a tuple is provided, the value must be one of the types in the tuple.
        Each type can be a built-in Python type or a custom class.

    Raises
    ------
    TypeError
        If the expected type is not a type or a tuple of types.

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

    See Also
    --------
    TypeValidationError
        Custom exception raised when a parameter has an invalid type.
    isinstance(obj, class_or_tuple)
        Built-in Python function to check if an object is an instance of a class or of a subclass
        thereof.
        If a tuple is provided, the type check is performed against each element in the tuple (OR
        logic).
        """
    def __init__(self, expected_type: type | tuple[type]):
        if not isinstance(expected_type, (type, tuple)):
            raise TypeError(f"Expected a type or a tuple of types, got {type(expected_type)}")
        self.expected_type = expected_type

    def check(self, value) -> bool:
        return isinstance(value, self.expected_type)

    def create_error(self, value) -> TypeValidationError:
        return TypeValidationError(value, self.expected_type)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "TypeRule",
            "expected_type": RuleRegistry._type_to_spec(self.expected_type),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "TypeRule":
        expected_type = registry._spec_to_type(data["expected_type"])
        return cls(expected_type)


class RangeRule(SingleValueRule[RangeValidationError]):
    """
    Rule checking if a value is within a range.

    Attributes
    ----------
    ge, lt, le, gt : Optional[float]
        Range boundaries for the parameter value (greater or equal, less than, less or equal,
        greater).

    Examples
    --------
    >>> rule = RangeRule(ge=0, lt=10)
    >>> rule.check(-1)
    False

    See Also
    --------
    RangeValidationError
        Custom exception raised when a parameter is out of bounds.
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
        return RangeValidationError(value, ge=self.ge, gt=self.gt, le=self.le, lt=self.lt)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "RangeRule",
            "ge": self.ge,
            "gt": self.gt,
            "le": self.le,
            "lt": self.lt,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "RangeRule":
        return cls(ge=data.get("ge"), gt=data.get("gt"), le=data.get("le"), lt=data.get("lt"))


class PatternRule(SingleValueRule[PatternValidationError]):
    r"""
    Rule checking if a value matches a regular expression pattern.

    Attributes
    ----------
    pattern : str
        Regular expression pattern to match, if the parameter value is a string.

    Raises
    ------
    ValueError
        If the pattern is not a valid regular expression.

    Examples
    --------
    Match one or more digits:

    >>> rule = PatternRule(r"\d+")
    >>> rule.check("abc")
    False

    See Also
    --------
    PatternValidationError
        Custom exception raised when a parameter does not match a regular expression pattern.
    """
    def __init__(self, pattern: str):
        try:
            self.pattern = re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {pattern}") from exc

    def check(self, value) -> bool:
        return bool(self.pattern.match(str(value)))

    def create_error(self, value) -> PatternValidationError:
        return PatternValidationError(value, self.pattern)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "PatternRule", "pattern": self.pattern.pattern}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "PatternRule":
        return cls(pattern=data["pattern"])


class OptionRule(SingleValueRule[OptionValidationError]):
    """
    Rule checking if a value is in a set of allowed options.

    Attributes
    ----------
    options : Set[Any]
        Allowed values for the parameter.

    Examples
    --------
    >>> rule = OptionRule([1, 2, 3])
    >>> rule.check(4)
    False

    See Also
    --------
    OptionValidationError
        Custom exception raised when a parameter's value does not belong to the allowed options.
    """
    def __init__(self, options: Iterable):
        self.options = set(options) # convert to set for faster lookup

    def check(self, value) -> bool:
        return value in self.options

    def create_error(self, value) -> OptionValidationError:
        return OptionValidationError(value, self.options)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "OptionRule", "options": list(self.options)}

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "OptionRule":
        return cls(options=data["options"])


class CustomRule(SingleValueRule[CustomValidationError]):
    """
    Rule checking if a value passes a custom validation function.

    Attributes
    ----------
    func : Callable[[Any], bool]
        Custom validation function. It should take a single argument (value) and return a boolean.

    Examples
    --------
    >>> def is_even(x):
    ...     return x % 2 == 0
    >>> rule = CustomRule(is_even)
    >>> rule.check(5)
    False

    See Also
    --------
    CustomValidationError
        Custom exception raised when a custom validation rule fails.
    """
    def __init__(self, func: Callable[[Any], bool]):
        self.func = func

    def check(self, value) -> bool:
        return self.func(value)

    def create_error(self, value) -> CustomValidationError:
        return CustomValidationError(value, self.func)

    def to_dict(self) -> Dict[str, Any]:
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
        raise ValueError("CustomRule cannot be deserialized without a callable.")


# --- Composite Rules ------------------------------------------------------------------------------

class CompositeValidationError(ValidationError):
    """
    Exception raised when a composite validation rule (AndRule or OrRule) fails.

    Attributes
    ----------
    errors : List[ValidationError]
        Individual errors from the sub-rules that failed.
    operator : str
        The logical operator ('AND' or 'OR').
    value : Any
        The value that failed validation.
    rule_ids : List[str]
        Names of the rules that failed.
    """
    def __init__(
        self,
        errors: list,
        operator: str,
        value: Any = None,
        rule_ids: Optional[list[str]] = None,
    ):
        self.errors = errors
        self.operator = operator
        self.value = value
        self.rule_ids = rule_ids or []
        super().__init__()

    def format_message(self) -> str:
        value_repr = repr(self.value) if self.value is not None else "value"
        if not self.errors:
            return f"Composite {self.operator} rule failed for {value_repr} with no specific errors."
        messages = [str(e) for e in self.errors]
        failed_rules = ", ".join(self.rule_ids) if self.rule_ids else "unknown rules"
        return (
            f"Composite {self.operator} rule failed for {value_repr}. "
            f"Failed rules: [{failed_rules}]. Details: {'; '.join(messages)}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operator": self.operator,
            "value": repr(self.value),
            "errors": [str(e) for e in self.errors],
            "rule_ids": list(self.rule_ids),
        }


class AndRule(SingleValueRule[CompositeValidationError]):
    """
    Composite rule that requires ALL sub-rules to pass (logical AND).

    All sub-rules must be satisfied for the value to be valid.

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
        return all(rule.check(value) for rule in self.rules)

    def create_error(self, value) -> CompositeValidationError:
        errors = []
        rule_ids: list[str] = []
        for rule in self.rules:
            error = rule.get_error(value)
            if error is not None:
                errors.append(error)
                rule_ids.append(rule.__class__.__name__)
        return CompositeValidationError(errors, "AND", value=value, rule_ids=rule_ids)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "AndRule",
            "rules": [rule.to_dict() for rule in self.rules],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "AndRule":
        rules = [registry.deserialize(rule_data) for rule_data in data.get("rules", [])]
        return cls(*rules)


class OrRule(SingleValueRule[CompositeValidationError]):
    """
    Composite rule that requires AT LEAST ONE sub-rule to pass (logical OR).

    At least one sub-rule must be satisfied for the value to be valid.

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
        return any(rule.check(value) for rule in self.rules)

    def create_error(self, value) -> CompositeValidationError:
        errors = []
        rule_ids: list[str] = []
        for rule in self.rules:
            error = rule.get_error(value)
            if error is not None:
                errors.append(error)
                rule_ids.append(rule.__class__.__name__)
        return CompositeValidationError(errors, "OR", value=value, rule_ids=rule_ids)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "OrRule",
            "rules": [rule.to_dict() for rule in self.rules],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], registry: RuleRegistry) -> "OrRule":
        rules = [registry.deserialize(rule_data) for rule_data in data.get("rules", [])]
        return cls(*rules)


# --- Multi Value Rules ----------------------------------------------------------------------------

class MultiValueRule(Rule[RelationValidationError]):
    """
    Rule checking a relationship or dependency between multiple parameters.

    Attributes
    ----------
    func : Callable
        Function which takes several values, checks a relationship between them, and returns a
        boolean.

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

    Notes
    -----
    Compared to the base `Rule` class, this class specializes the signatures of its methods to
    handle a variable number of values. Contrary to the `SingleValueRule` class, there is no need to
    override the `check` method, as the parent class already handles multiple values.

    This type is checked in the Validator class to trigger the appropriate logic for passing
    multiple values.
    """
    def __init__(self, func: Callable[..., bool]):
        self.func = func

    def check(self, *args, **kwargs) -> bool:
        return self.func(*args, **kwargs)

    def create_error(self, *args, **kwargs) -> RelationValidationError:
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
