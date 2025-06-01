#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import re
from typing import Optional, Any, Callable, Generic, TypeVar

from tessara.errors.validation import (
    ValidationError,
    TypeValidationError,
    RangeValidationError,
    PatternValidationError,
    OptionValidationError,
    CustomValidationError,
    RelationValidationError
)


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
        return all(func(value, constraint) for constraint, func in constraints if constraint is not None)

    def create_error(self, value) -> RangeValidationError:
        return RangeValidationError(value, ge=self.ge, gt=self.gt, le=self.le, lt=self.lt)


class PatternRule(SingleValueRule[PatternValidationError]):
    """
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
