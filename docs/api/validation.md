<a id="validation-module"></a>

# Validation Module

Validation rules and the parameter validator.

<a id="module-tessara.validation.rules"></a>

<a id="rules"></a>

## Rules

Validation rules for the parameters.

Rules can be applied to single values or to multiple values, depending on the
rule type. Each rule generates an appropriate error when validation fails. New
rule types can be added by subclassing the base rule classes.

<a id="tessara.validation.rules.E"></a>

### *class* tessara.validation.rules.E

Type variable for the error type associated with a rule.

alias of TypeVar(‘E’, bound=[`ValidationError`](core.md#tessara.core.errors.validation.ValidationError))

<a id="tessara.validation.rules.Rule"></a>

### *class* tessara.validation.rules.Rule

Bases: [`ABC`](https://docs.python.org/3/library/abc.html#abc.ABC), [`Generic`](https://docs.python.org/3/library/typing.html#typing.Generic)[[`E`](#tessara.validation.rules.E)]

Base class for all validation rules.

Subclasses should implement the \_\_call_\_ method to perform the validation check.

> **See also**
>
> [`SingleValueRule`](#tessara.validation.rules.SingleValueRule), [`MultiValueRule`](#tessara.validation.rules.MultiValueRule)
>
> `ValidationError`
> : Custom exception base class to indicate validation errors.

### Examples

Template code to define a rule and check the validity of input values:

```pycon
>>> rule = Rule(constraint='example')
>>> rule.check(correct_value)
True
>>> outcome_valid = rule.get_error(correct_value)
None
>>> outcome_invalid = rule.get_error(wrong_value)
ValidationError('Invalid value')
>>> print(outcome_invalid.message)
ValidationError: "Error message with dynamic placeholders: 'wrong_value'."
```

<a id="tessara.validation.rules.Rule.check"></a>

#### *abstract* check(\*args, \*\*kwargs)

Check the validity of input values.

* **Parameters:**
  * **\*args** – Input values to check (number and types of arguments depend on the rule subclass).
  * **\*\*kwargs** – Input values to check (number and types of arguments depend on the rule subclass).

<a id="tessara.validation.rules.Rule.get_error"></a>

#### get_error(\*args, \*\*kwargs)

Create error only if validation fails.

* **Parameters:**
  * **\*args** – Positional values forwarded to `check` and `create_error`.
  * **\*\*kwargs** – Keyword values forwarded to `check` and `create_error`.
* **Returns:**
  A validation error when the check fails, `None` otherwise.
* **Return type:**
  [E](#tessara.validation.rules.E) | None

<a id="tessara.validation.rules.Rule.create_error"></a>

#### *abstract* create_error(\*args, \*\*kwargs)

Create a specific error associated with a rule’s failure.

* **Parameters:**
  * **\*args** – Positional values describing the failed input.
  * **\*\*kwargs** – Keyword values describing the failed input.

<a id="tessara.validation.rules.Rule.to_dict"></a>

#### to_dict()

Serialize a rule to a dictionary.

* **Returns:**
  Dictionary representation of the rule.
* **Return type:**
  Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]
* **Raises:**
  [**NotImplementedError**](https://docs.python.org/3/library/exceptions.html#NotImplementedError) – If the subclass does not implement serialization.

<a id="tessara.validation.rules.Rule.from_dict"></a>

#### *classmethod* from_dict(data, registry)

Deserialize a rule from a dictionary.

* **Parameters:**
  * **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Serialized rule payload.
  * **registry** ([*RuleRegistry*](#tessara.validation.rules.RuleRegistry)) – Registry used for resolving nested rule types.
* **Returns:**
  Reconstructed rule instance.
* **Return type:**
  [Rule](#tessara.validation.rules.Rule)
* **Raises:**
  [**NotImplementedError**](https://docs.python.org/3/library/exceptions.html#NotImplementedError) – If the subclass does not implement deserialization.

<a id="tessara.validation.rules.UnknownRule"></a>

### *class* tessara.validation.rules.UnknownRule(payload)

Bases: [`Rule`](#tessara.validation.rules.Rule)[[`ValidationError`](core.md#tessara.core.errors.validation.ValidationError)]

Fallback rule for unknown or unsupported serialized rules.

* **Parameters:**
  **payload** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Original serialized data that could not be resolved.

<a id="tessara.validation.rules.UnknownRule.check"></a>

#### check(\*args, \*\*kwargs)

Return `False` unconditionally.

* **Parameters:**
  * **\*args** – Ignored positional arguments.
  * **\*\*kwargs** – Ignored keyword arguments.
* **Returns:**
  Always `False`.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="tessara.validation.rules.UnknownRule.create_error"></a>

#### create_error(\*args, \*\*kwargs)

Return a deserialization error wrapping the original payload.

* **Parameters:**
  * **\*args** – Ignored positional arguments.
  * **\*\*kwargs** – Ignored keyword arguments.
* **Returns:**
  Error containing the unresolved payload.
* **Return type:**
  [RuleDeserializationError](core.md#tessara.core.errors.validation.RuleDeserializationError)

<a id="tessara.validation.rules.UnknownRule.to_dict"></a>

#### to_dict()

Serialize the unknown rule back to its original payload.

* **Returns:**
  Dictionary containing the original payload.
* **Return type:**
  Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]

<a id="tessara.validation.rules.UnknownRule.from_dict"></a>

#### *classmethod* from_dict(data, registry)

Reconstruct from the raw payload dictionary.

* **Parameters:**
  * **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Serialized rule payload.
  * **registry** ([*RuleRegistry*](#tessara.validation.rules.RuleRegistry)) – Rule registry (unused).
* **Returns:**
  Reconstructed instance.
* **Return type:**
  [UnknownRule](#tessara.validation.rules.UnknownRule)

<a id="tessara.validation.rules.RuleRegistry"></a>

### *class* tessara.validation.rules.RuleRegistry

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Registry for rule serialization and deserialization.

Provides a central mapping from rule type names to rule classes.

<a id="tessara.validation.rules.RuleRegistry.register"></a>

#### register(rule_cls, name=None)

Register a rule class.

* **Parameters:**
  * **rule_cls** (*Type* *[*[*Rule*](#tessara.validation.rules.Rule) *]*) – Rule class to register.
  * **name** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None*) – Key under which to store the class. Defaults to `rule_cls.__name__`.

<a id="tessara.validation.rules.RuleRegistry.serialize"></a>

#### serialize(rule)

Serialize a rule to a dictionary.

* **Parameters:**
  **rule** ([*Rule*](#tessara.validation.rules.Rule)) – Rule instance to serialize.
* **Returns:**
  Dictionary representation including a `"type"` key.
* **Return type:**
  Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]

<a id="tessara.validation.rules.RuleRegistry.deserialize"></a>

#### deserialize(data)

Deserialize a rule from a dictionary.

* **Parameters:**
  **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Serialized rule payload containing at least a `"type"` key.
* **Returns:**
  Reconstructed rule instance.
* **Return type:**
  [Rule](#tessara.validation.rules.Rule)
* **Raises:**
  [**RuleDeserializationError**](core.md#tessara.core.errors.validation.RuleDeserializationError) – If the rule type is missing or unknown.

<a id="tessara.validation.rules.SingleValueRule"></a>

### *class* tessara.validation.rules.SingleValueRule

Bases: [`Rule`](#tessara.validation.rules.Rule)[[`E`](#tessara.validation.rules.E)]

Parameter-specific rule, checking the validity of a single value.

### Notes

Compared to the base Rule class, this class specializes its methods’ signatures to
handle a single value.

Its nature is checked in the Validator class to trigger the appropriate logic for passing a
*single* value.

<a id="tessara.validation.rules.SingleValueRule.check"></a>

#### *abstract* check(value)

Check the validity of a single value.

* **Parameters:**
  **value** – Value to validate.
* **Returns:**
  `True` if the value is valid.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="tessara.validation.rules.SingleValueRule.create_error"></a>

#### *abstract* create_error(value)

Create the error for a single failed value.

* **Parameters:**
  **value** – Value that failed validation.
* **Returns:**
  Specific validation error for the failure.
* **Return type:**
  [E](#tessara.validation.rules.E) | None

<a id="tessara.validation.rules.TypeRule"></a>

### *class* tessara.validation.rules.TypeRule(expected_type)

Bases: [`SingleValueRule`](#tessara.validation.rules.SingleValueRule)[[`TypeValidationError`](core.md#tessara.core.errors.validation.TypeValidationError)]

Rule checking if a value is a specific type.

* **Parameters:**
  **expected_type** ([*type*](https://docs.python.org/3/library/functions.html#type) *|* [*tuple*](https://docs.python.org/3/library/stdtypes.html#tuple) *[*[*type*](https://docs.python.org/3/library/functions.html#type) *]*) – Required type(s) for the value.
* **Raises:**
  [**TypeError**](https://docs.python.org/3/library/exceptions.html#TypeError) – If the expected type is not a type or a tuple of types.

> **See also**
>
> `TypeValidationError`
> : Custom exception raised when a parameter has an invalid type.
>
> [`isinstance`](https://docs.python.org/3/library/functions.html#isinstance), `class_or_tuple`

### Examples

For a unique expected type:

```pycon
>>> rule = TypeRule(int)
>>> rule.check('abc')
False
```

For several allowed types:

```pycon
>>> rule = TypeRule((str, float))
>>> rule.check(1)
False
```

<a id="tessara.validation.rules.TypeRule.check"></a>

#### check(value)

Return `True` if *value* is an instance of the expected type.

* **Parameters:**
  **value** – Value to type-check.
* **Returns:**
  `True` if *value* matches the expected type.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="tessara.validation.rules.TypeRule.create_error"></a>

#### create_error(value)

Create a type-validation error for *value*.

* **Parameters:**
  **value** – Value that failed the type check.
* **Returns:**
  Error describing the type mismatch.
* **Return type:**
  [TypeValidationError](core.md#tessara.core.errors.validation.TypeValidationError)

<a id="tessara.validation.rules.TypeRule.to_dict"></a>

#### to_dict()

Serialize the rule to a dictionary.

* **Returns:**
  Dictionary containing the expected type specification.
* **Return type:**
  Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]

<a id="tessara.validation.rules.TypeRule.from_dict"></a>

#### *classmethod* from_dict(data, registry)

Reconstruct from a serialized dictionary.

* **Parameters:**
  * **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Serialized rule payload.
  * **registry** ([*RuleRegistry*](#tessara.validation.rules.RuleRegistry)) – Registry used for type resolution.
* **Returns:**
  Reconstructed instance.
* **Return type:**
  [TypeRule](#tessara.validation.rules.TypeRule)

<a id="tessara.validation.rules.RangeRule"></a>

### *class* tessara.validation.rules.RangeRule(ge=None, gt=None, le=None, lt=None)

Bases: [`SingleValueRule`](#tessara.validation.rules.SingleValueRule)[[`RangeValidationError`](core.md#tessara.core.errors.validation.RangeValidationError)]

Rule checking if a value is within a range.

* **Parameters:**
  * **ge** ([*float*](https://docs.python.org/3/library/functions.html#float) *,* *optional*) – Minimum value (inclusive).
  * **gt** ([*float*](https://docs.python.org/3/library/functions.html#float) *,* *optional*) – Minimum value (exclusive).
  * **le** ([*float*](https://docs.python.org/3/library/functions.html#float) *,* *optional*) – Maximum value (inclusive).
  * **lt** ([*float*](https://docs.python.org/3/library/functions.html#float) *,* *optional*) – Maximum value (exclusive).

> **See also**
>
> `RangeValidationError`
> : Custom exception raised when a parameter is out of bounds.

### Examples

```pycon
>>> rule = RangeRule(ge=0, lt=10)
>>> rule.check(-1)
False
```

<a id="tessara.validation.rules.RangeRule.check"></a>

#### check(value)

Return `True` if *value* falls within the configured bounds.

* **Parameters:**
  **value** – Value to check against the range boundaries.
* **Returns:**
  `True` if *value* satisfies all configured bounds.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="tessara.validation.rules.RangeRule.create_error"></a>

#### create_error(value)

Create a range-validation error for *value*.

* **Parameters:**
  **value** – Value that fell outside the range.
* **Returns:**
  Error describing which bounds were violated.
* **Return type:**
  [RangeValidationError](core.md#tessara.core.errors.validation.RangeValidationError)

<a id="tessara.validation.rules.RangeRule.to_dict"></a>

#### to_dict()

Serialize the rule to a dictionary.

* **Returns:**
  Dictionary containing the range boundaries.
* **Return type:**
  Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]

<a id="tessara.validation.rules.RangeRule.from_dict"></a>

#### *classmethod* from_dict(data, registry)

Reconstruct from a serialized dictionary.

* **Parameters:**
  * **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Serialized rule payload.
  * **registry** ([*RuleRegistry*](#tessara.validation.rules.RuleRegistry)) – Rule registry (unused).
* **Returns:**
  Reconstructed instance.
* **Return type:**
  [RangeRule](#tessara.validation.rules.RangeRule)

<a id="tessara.validation.rules.PatternRule"></a>

### *class* tessara.validation.rules.PatternRule(pattern)

Bases: [`SingleValueRule`](#tessara.validation.rules.SingleValueRule)[[`PatternValidationError`](core.md#tessara.core.errors.validation.PatternValidationError)]

Rule checking if a value matches a regular expression pattern.

* **Parameters:**
  **pattern** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Regular expression pattern to match, if the parameter value is a string.
* **Raises:**
  [**ValueError**](https://docs.python.org/3/library/exceptions.html#ValueError) – If the pattern is not a valid regular expression.

> **See also**
>
> `PatternValidationError`
> : Custom exception raised when a parameter does not match a regular expression pattern.

### Examples

Match one or more digits:

```pycon
>>> rule = PatternRule(r"\d+")
>>> rule.check("abc")
False
```

<a id="tessara.validation.rules.PatternRule.check"></a>

#### check(value)

Return `True` if *value* matches the compiled pattern.

* **Parameters:**
  **value** – Value to match against the pattern.
* **Returns:**
  `True` if the string representation of *value* matches.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="tessara.validation.rules.PatternRule.create_error"></a>

#### create_error(value)

Create a pattern-validation error for *value*.

* **Parameters:**
  **value** – Value that did not match the pattern.
* **Returns:**
  Error describing the pattern mismatch.
* **Return type:**
  [PatternValidationError](core.md#tessara.core.errors.validation.PatternValidationError)

<a id="tessara.validation.rules.PatternRule.to_dict"></a>

#### to_dict()

Serialize the rule to a dictionary.

* **Returns:**
  Dictionary containing the pattern string.
* **Return type:**
  Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]

<a id="tessara.validation.rules.PatternRule.from_dict"></a>

#### *classmethod* from_dict(data, registry)

Reconstruct from a serialized dictionary.

* **Parameters:**
  * **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Serialized rule payload.
  * **registry** ([*RuleRegistry*](#tessara.validation.rules.RuleRegistry)) – Rule registry (unused).
* **Returns:**
  Reconstructed instance.
* **Return type:**
  [PatternRule](#tessara.validation.rules.PatternRule)

<a id="tessara.validation.rules.OptionRule"></a>

### *class* tessara.validation.rules.OptionRule(options)

Bases: [`SingleValueRule`](#tessara.validation.rules.SingleValueRule)[[`OptionValidationError`](core.md#tessara.core.errors.validation.OptionValidationError)]

Rule checking if a value is in a set of allowed options.

* **Parameters:**
  **options** (*Iterable*) – Allowed values for the parameter.

> **See also**
>
> `OptionValidationError`
> : Custom exception raised when a parameter’s value does not belong to the allowed options.

### Examples

```pycon
>>> rule = OptionRule([1, 2, 3])
>>> rule.check(4)
False
```

<a id="tessara.validation.rules.OptionRule.check"></a>

#### check(value)

Return `True` if *value* belongs to the allowed options.

* **Parameters:**
  **value** – Value to look up in the allowed set.
* **Returns:**
  `True` if *value* is in the options.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="tessara.validation.rules.OptionRule.create_error"></a>

#### create_error(value)

Create an option-validation error for *value*.

* **Parameters:**
  **value** – Value that was not among the allowed options.
* **Returns:**
  Error listing the allowed options.
* **Return type:**
  [OptionValidationError](core.md#tessara.core.errors.validation.OptionValidationError)

<a id="tessara.validation.rules.OptionRule.to_dict"></a>

#### to_dict()

Serialize the rule to a dictionary.

* **Returns:**
  Dictionary containing the allowed options.
* **Return type:**
  Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]

<a id="tessara.validation.rules.OptionRule.from_dict"></a>

#### *classmethod* from_dict(data, registry)

Reconstruct from a serialized dictionary.

* **Parameters:**
  * **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Serialized rule payload.
  * **registry** ([*RuleRegistry*](#tessara.validation.rules.RuleRegistry)) – Rule registry (unused).
* **Returns:**
  Reconstructed instance.
* **Return type:**
  [OptionRule](#tessara.validation.rules.OptionRule)

<a id="tessara.validation.rules.CustomRule"></a>

### *class* tessara.validation.rules.CustomRule(func)

Bases: [`SingleValueRule`](#tessara.validation.rules.SingleValueRule)[[`CustomValidationError`](core.md#tessara.core.errors.validation.CustomValidationError)]

Rule checking if a value passes a custom validation function.

* **Parameters:**
  **func** (*Callable* *[* *[**Any* *]* *,* [*bool*](https://docs.python.org/3/library/functions.html#bool) *]*) – Custom validation function. It should take a single argument (value) and return a boolean.

> **See also**
>
> `CustomValidationError`
> : Custom exception raised when a custom validation rule fails.

### Examples

```pycon
>>> def is_even(x):
...     return x % 2 == 0
>>> rule = CustomRule(is_even)
>>> rule.check(5)
False
```

<a id="tessara.validation.rules.CustomRule.check"></a>

#### check(value)

Return `True` if the custom function accepts *value*.

* **Parameters:**
  **value** – Value to pass to the custom function.
* **Returns:**
  Result of the custom validation function.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="tessara.validation.rules.CustomRule.create_error"></a>

#### create_error(value)

Create a custom-validation error for *value*.

* **Parameters:**
  **value** – Value that failed the custom validation.
* **Returns:**
  Error referencing the custom function.
* **Return type:**
  [CustomValidationError](core.md#tessara.core.errors.validation.CustomValidationError)

<a id="tessara.validation.rules.CustomRule.to_dict"></a>

#### to_dict()

Serialize the rule to a dictionary.

* **Returns:**
  Dictionary with function metadata (not re-importable).
* **Return type:**
  Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]

<a id="tessara.validation.rules.CustomRule.from_dict"></a>

#### *classmethod* from_dict(data, registry)

Reconstruct from a serialized dictionary.

* **Parameters:**
  * **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Serialized rule payload.
  * **registry** ([*RuleRegistry*](#tessara.validation.rules.RuleRegistry)) – Rule registry (unused).
* **Returns:**
  Never returned; always raises.
* **Return type:**
  [CustomRule](#tessara.validation.rules.CustomRule)
* **Raises:**
  [**ValueError**](https://docs.python.org/3/library/exceptions.html#ValueError) – Always, because callables cannot be deserialized.

<a id="tessara.validation.rules.AndRule"></a>

### *class* tessara.validation.rules.AndRule(\*rules)

Bases: [`SingleValueRule`](#tessara.validation.rules.SingleValueRule)[[`CompositeValidationError`](core.md#tessara.core.errors.validation.CompositeValidationError)]

Composite rule that requires ALL sub-rules to pass (logical AND).

All sub-rules must be satisfied for the value to be valid.

* **Parameters:**
  **\*rules** ([*SingleValueRule*](#tessara.validation.rules.SingleValueRule)) – Sub-rules that must all pass.

### Examples

Combine type and range validation:

```pycon
>>> rule = AndRule(
...     TypeRule(int),
...     RangeRule(gt=0, lt=100),
... )
>>> rule.check(50)
True
>>> rule.check(-5)
False
```

Nested composite rules:

```pycon
>>> rule = AndRule(
...     TypeRule(int),
...     OrRule(RangeRule(lt=0), RangeRule(gt=100)),
... )
>>> rule.check(-5)  # int AND (negative OR > 100)
True
```

<a id="tessara.validation.rules.AndRule.check"></a>

#### check(value)

Return `True` if all sub-rules accept *value*.

* **Parameters:**
  **value** – Value to validate against every sub-rule.
* **Returns:**
  `True` if all sub-rules pass.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="tessara.validation.rules.AndRule.create_error"></a>

#### create_error(value)

Collect errors from all failing sub-rules.

* **Parameters:**
  **value** – Value that failed at least one sub-rule.
* **Returns:**
  Composite error aggregating individual failures.
* **Return type:**
  [CompositeValidationError](core.md#tessara.core.errors.validation.CompositeValidationError)

<a id="tessara.validation.rules.AndRule.to_dict"></a>

#### to_dict()

Serialize the rule and its sub-rules to a dictionary.

* **Returns:**
  Dictionary containing serialized sub-rules.
* **Return type:**
  Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]

<a id="tessara.validation.rules.AndRule.from_dict"></a>

#### *classmethod* from_dict(data, registry)

Reconstruct from a serialized dictionary.

* **Parameters:**
  * **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Serialized rule payload.
  * **registry** ([*RuleRegistry*](#tessara.validation.rules.RuleRegistry)) – Registry used to deserialize sub-rules.
* **Returns:**
  Reconstructed instance.
* **Return type:**
  [AndRule](#tessara.validation.rules.AndRule)

<a id="tessara.validation.rules.OrRule"></a>

### *class* tessara.validation.rules.OrRule(\*rules)

Bases: [`SingleValueRule`](#tessara.validation.rules.SingleValueRule)[[`CompositeValidationError`](core.md#tessara.core.errors.validation.CompositeValidationError)]

Composite rule that requires AT LEAST ONE sub-rule to pass (logical OR).

At least one sub-rule must be satisfied for the value to be valid.

* **Parameters:**
  **\*rules** ([*SingleValueRule*](#tessara.validation.rules.SingleValueRule)) – Sub-rules where at least one must pass.

### Examples

Accept either string or integer:

```pycon
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
```

Complex condition - value is either small or large (not medium):

```pycon
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
```

<a id="tessara.validation.rules.OrRule.check"></a>

#### check(value)

Return `True` if at least one sub-rule accepts *value*.

* **Parameters:**
  **value** – Value to validate against the sub-rules.
* **Returns:**
  `True` if any sub-rule passes.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="tessara.validation.rules.OrRule.create_error"></a>

#### create_error(value)

Collect errors from all failing sub-rules.

* **Parameters:**
  **value** – Value that failed all sub-rules.
* **Returns:**
  Composite error aggregating individual failures.
* **Return type:**
  [CompositeValidationError](core.md#tessara.core.errors.validation.CompositeValidationError)

<a id="tessara.validation.rules.OrRule.to_dict"></a>

#### to_dict()

Serialize the rule and its sub-rules to a dictionary.

* **Returns:**
  Dictionary containing serialized sub-rules.
* **Return type:**
  Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]

<a id="tessara.validation.rules.OrRule.from_dict"></a>

#### *classmethod* from_dict(data, registry)

Reconstruct from a serialized dictionary.

* **Parameters:**
  * **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Serialized rule payload.
  * **registry** ([*RuleRegistry*](#tessara.validation.rules.RuleRegistry)) – Registry used to deserialize sub-rules.
* **Returns:**
  Reconstructed instance.
* **Return type:**
  [OrRule](#tessara.validation.rules.OrRule)

<a id="tessara.validation.rules.MultiValueRule"></a>

### *class* tessara.validation.rules.MultiValueRule(func)

Bases: [`Rule`](#tessara.validation.rules.Rule)[[`RelationValidationError`](core.md#tessara.core.errors.validation.RelationValidationError)]

Rule checking a relationship or dependency between multiple parameters.

* **Parameters:**
  **func** (*Callable* *[* *...* *,* [*bool*](https://docs.python.org/3/library/functions.html#bool) *]*) – Function which takes several values, checks a relationship between them, and returns a
  boolean.

### Notes

Compared to the base Rule class, this class specializes the signatures of its methods to
handle a variable number of values. Contrary to the SingleValueRule class, there is no need to
override the check method, as the parent class already handles multiple values.

This type is checked in the Validator class to trigger the appropriate logic for passing
multiple values.

### Examples

Define a rule that checks if one parameter is greater than another:

```pycon
>>> def is_greater_than(x, y):
...     return x > y
>>> rule = RelationalRule(is_greater_than)
```

Pass values as positional arguments:

```pycon
>>> rule.check(1, 2)
False
```

Pass values as keyword arguments:

```pycon
>>> rule.check(x=1, y=2)
False
```

<a id="tessara.validation.rules.MultiValueRule.check"></a>

#### check(\*args, \*\*kwargs)

Delegate to the wrapped function.

* **Parameters:**
  * **\*args** – Positional values forwarded to the wrapped function.
  * **\*\*kwargs** – Keyword values forwarded to the wrapped function.
* **Returns:**
  Result of the wrapped function.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="tessara.validation.rules.MultiValueRule.create_error"></a>

#### create_error(\*args, \*\*kwargs)

Create a relation-validation error for the given values.

* **Parameters:**
  * **\*args** – Positional values that failed the relation check.
  * **\*\*kwargs** – Keyword values that failed the relation check.
* **Returns:**
  Error referencing the wrapped function and its inputs.
* **Return type:**
  [RelationValidationError](core.md#tessara.core.errors.validation.RelationValidationError)

<a id="module-tessara.validation.validator"></a>

<a id="validator"></a>

## Validator

Validation of parameters and parameter sets.

Individual rules can validate values in isolation. The `Validator` class is a
higher-level component that aggregates the outcomes of multiple rules.

<a id="tessara.validation.validator.Values"></a>

### tessara.validation.validator.Values

Type alias for values to validate against a rule, retrieved from the target names.

alias of [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`Any`](https://docs.python.org/3/library/typing.html#typing.Any)] | [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/library/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

<a id="tessara.validation.validator.ReportEntry"></a>

### *class* tessara.validation.validator.ReportEntry(rule, targets, success=None, message='')

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Representation of a single validation report entry.

<a id="tessara.validation.validator.ReportEntry.rule"></a>

#### rule *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

Name of the rule that was checked.

<a id="tessara.validation.validator.ReportEntry.targets"></a>

#### targets *: [Iterable](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[str](https://docs.python.org/3/library/stdtypes.html#str)] | [Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[str](https://docs.python.org/3/library/stdtypes.html#str), [str](https://docs.python.org/3/library/stdtypes.html#str)]*

Specification of the parameter(s) to validate, by their names in the ParameterSet instance.

<a id="tessara.validation.validator.ReportEntry.success"></a>

#### success *: [bool](https://docs.python.org/3/library/functions.html#bool) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

Outcome of the validation process. `True` if the check passed,
`False` if it failed, `None` if it could not complete.

<a id="tessara.validation.validator.ReportEntry.message"></a>

#### message *: [str](https://docs.python.org/3/library/stdtypes.html#str)* *= ''*

Error message if the validation failed.

<a id="tessara.validation.validator.ValidationRecorder"></a>

### *class* tessara.validation.validator.ValidationRecorder

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Handle validation reports and error aggregation separately from validation execution.

> **See also**
>
> [`ReportEntry`](#tessara.validation.validator.ReportEntry)
> : Representation of a single validation report entry.
>
> `ValidationError`
> : Base class for all validation errors.
>
> `Rule.get_error`
> : Method to generate the output of a rule check.

<a id="tessara.validation.validator.ValidationRecorder.SUCCESS_FLAG"></a>

#### SUCCESS_FLAG *= 'PASSED'*

<a id="tessara.validation.validator.ValidationRecorder.record"></a>

#### record(rule, targets, error=None)

Register a validation check in the report.

* **Parameters:**
  * **rule** ([*Rule*](#tessara.validation.rules.Rule)) – Rule instance that was checked.
  * **targets** (*Targets*) – Parameter names involved in the check.
  * **error** ([*ValidationError*](core.md#tessara.core.errors.validation.ValidationError) *|* [*CheckError*](core.md#tessara.core.errors.validation.CheckError) *|* *None*) – Error object if the validation check failed.
    If None, the check passed successfully.

<a id="tessara.validation.validator.ValidationRecorder.get_report"></a>

#### get_report()

Retrieve the complete validation report.

* **Returns:**
  All recorded report entries.
* **Return type:**
  List[[ReportEntry](#tessara.validation.validator.ReportEntry)]

<a id="tessara.validation.validator.ValidationRecorder.get_errors"></a>

#### get_errors()

Retrieve only errors.

* **Returns:**
  All collected validation errors.
* **Return type:**
  List[[ValidationError](core.md#tessara.core.errors.validation.ValidationError)]

<a id="tessara.validation.validator.ValidationRecorder.has_errors"></a>

#### has_errors()

Signal if any errors occurred.

* **Returns:**
  `True` if at least one error was recorded.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="tessara.validation.validator.Checker"></a>

### *class* tessara.validation.validator.Checker(rule, targets)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Specifies and performs a single validation check on a ParameterSet.

This layer serves to standardize the inputs and outputs of the validation process, so that they
do not depend on the type of rule being checked (parameter-specific or relational).

* **Parameters:**
  * **rule** ([*Rule*](#tessara.validation.rules.Rule)) – Rule to apply.
  * **targets** (*Targets*) – Parameter names involved in the check.

<a id="tessara.validation.validator.Checker.ARGS_MODE"></a>

#### ARGS_MODE *= 'args'*

<a id="tessara.validation.validator.Checker.KWARGS_MODE"></a>

#### KWARGS_MODE *= 'kwargs'*

<a id="tessara.validation.validator.Checker.bind_targets"></a>

#### bind_targets(params)

Retrieve target values from the ParameterSet instance.

* **Parameters:**
  **params** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet)) – Set of parameters to validate, containing Param instances named as the targets.
* **Returns:**
  Values of the parameters to validate, depending on the type of the targets.
  If the target are specified in a list of parameter names, the method returns a list of
  values in the same order.
  If the targets are specified in a dictionary, the method returns a dictionary of values
  with the same keys.
* **Return type:**
  Values

<a id="tessara.validation.validator.Checker.check"></a>

#### check(params)

Perform a single check of input values against a rule.

* **Parameters:**
  **params** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet)) – Set of parameters to validate, containing Param instances named as the targets.
* **Returns:**
  **error** – If the check fails, it provides an error summarizing the failure.
  If the check passes, it returns None.
* **Return type:**
  [ValidationError](core.md#tessara.core.errors.validation.ValidationError) | None

> **See also**
>
> `Rule.get_error`
> : Method to generate the output of a rule check.

<a id="tessara.validation.validator.Validator"></a>

### *class* tessara.validation.validator.Validator(params, strict=False)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Validate input values against a set of rules.

Input values are fixed while several rules can be checked against them.

* **Parameters:**
  * **params** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet)) – Set of parameters to validate.
  * **strict** ([*bool*](https://docs.python.org/3/library/functions.html#bool) *,* *default False*) – When `True`, raise `GlobalValidationError` on any failure.

> **See also**
>
> `ParameterSet`
> : Set of parameters to validate, with individual rules and relationships.
>
> `Param`
> : Single parameter to validate, nested in a ParameterSet instance.
>
> `Rule`
> : Base class for validation rules to apply.
>
> `ValidationError`
> : Base class for all validation errors.
>
> [`Checker`](#tessara.validation.validator.Checker)
> : Specification and executor for a single validation check.

<a id="tessara.validation.validator.Validator.init_checks"></a>

#### init_checks()

Determine all the checks to perform on the parameters during a new validation process.

Checks are dynamically generated based on the rules associated with the parameters:

1. Check type and constraints of individual parameters (parameter-specific rules).
2. Check relationships between parameters (global rules).

* **Returns:**
  Checks to perform on the parameters, before any filtering.
* **Return type:**
  List[[Checker](#tessara.validation.validator.Checker)]

<a id="tessara.validation.validator.Validator.filter"></a>

#### *static* filter(checks, include_only=None, exclude=None)

Filter the checks to perform on the parameters based on the rule type.

* **Parameters:**
  * **checks** (*List* *[*[*Checker*](#tessara.validation.validator.Checker) *]*) – Checks to filter based on the rule type.
  * **include_only** (*Iterable* *[*[*Rule*](#tessara.validation.rules.Rule) *]*) – Rule types to include exclusively in the checks. It takes precedence over the `exclude`
    argument if both are provided.
  * **exclude** (*Iterable* *[*[*Rule*](#tessara.validation.rules.Rule) *]*) – Rule types to exclude from the checks, if the `only` argument is not provided.
* **Returns:**
  Filtered checks.
* **Return type:**
  List[[Checker](#tessara.validation.validator.Checker)]

<a id="tessara.validation.validator.Validator.validate"></a>

#### validate(include_only=None, exclude=None)

Execute the full validation process over a set of parameters and rules.

1. Reset the report to start a new validation process on new values.
2. Iterate over the checks to perform.
3. Retrieve the target values from the ParameterSet instance.
4. Execute the rule on the target values and catch the outcome.
5. Aggregate the outcomes of the rules in the report and the error stack.
6. Determine the global validation status (True if all rules passed).

* **Parameters:**
  * **include_only** (*Iterable* *[*[*Rule*](#tessara.validation.rules.Rule) *]* *,* *optional*) – Rule types to include exclusively.
  * **exclude** (*Iterable* *[*[*Rule*](#tessara.validation.rules.Rule) *]* *,* *optional*) – Rule types to exclude.
* **Returns:**
  True if all rules pass, False otherwise.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)
* **Raises:**
  [**GlobalValidationError**](core.md#tessara.core.errors.validation.GlobalValidationError) – If strict mode is enabled and any rule fails.
