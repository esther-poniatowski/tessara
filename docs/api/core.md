<a id="core-module"></a>

# Core Module

Parameter definitions, shared types, and custom errors.

<a id="top-level-package"></a>

## Top-Level Package

<a id="tessara.info"></a>

### tessara.info()

Format diagnostic information on package and platform.

* **Returns:**
  One-line summary of package name, version, OS, and Python version.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="module-tessara.core.parameters"></a>

<a id="parameters"></a>

## Parameters

Core parameter management classes for defining, validating, and organizing parameters.

Parameters support validation rules via the `rules` attribute. Nested
`ParameterSet` objects can be accessed using dot notation (e.g.
`params.model.lr`). Values can be set with optional strict validation via
`param.set(value, strict=True)`. Use `param.is_set` to distinguish between
“not set” and “explicitly set to None”.

<a id="tessara.core.parameters.SweepMaterializationPolicy"></a>

### *class* tessara.core.parameters.SweepMaterializationPolicy(strict=True)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Policy controlling how sweep candidates become concrete Param objects.

<a id="tessara.core.parameters.SweepMaterializationPolicy.strict"></a>

#### strict *: [bool](https://docs.python.org/3/library/functions.html#bool)* *= True*

Whether to validate values during materialization.

<a id="tessara.core.parameters.resolve_path"></a>

### tessara.core.parameters.resolve_path(params, path)

Traverse a nested ParameterSet structure using a dot-separated path.

* **Parameters:**
  * **params** ([*ParameterSet*](#tessara.core.parameters.ParameterSet)) – Root parameter set to start traversal from.
  * **path** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Dot-separated path to the target parameter or nested set
    (e.g., `"model.layers.hidden"`).
* **Returns:**
  The resolved object at the end of the path.
* **Return type:**
  [Param](#tessara.core.parameters.Param) | [ParameterSet](#tessara.core.parameters.ParameterSet)
* **Raises:**
  [**UnknownParameterError**](#tessara.core.errors.handling.UnknownParameterError) – If any segment of the path does not exist in the structure.

<a id="tessara.core.parameters.Param"></a>

### *class* tessara.core.parameters.Param(default=None, rules=None)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Define a parameter with properties and constraints for runtime validation.

Each instance of this class represents a parameter with constraints (type, value range, regular
expression…) and an optional default value.
The actual value of the parameter has to be set at runtime, and it will be validated against the
rules defined in the instance (if the strict mode is enabled).

* **Parameters:**
  * **default** (*Any* *,* *optional*) – Default value for the parameter.
  * **rules** (*Iterable* *[*[*RuleProtocol*](#tessara.core.types.RuleProtocol) *]* *,* *optional*) – Initial validation rules.

### Notes

The `Param` class serves as a static representation of a parameter with constraints. It does
not perform validation itself.

> **See also**
>
> `RuleProtocol`
> : Protocol for validation rules.

### Examples

Define a parameter with a default value, type constraint and boundaries:

```pycon
>>> param = Param(
...     default=5,
...     rules=[
...         TypeRule(int),
...         RangeRule(gt=0, le=10),
...     ]
... )
>>> param.get()
5
```

Define a parameter with no default value and a pattern matching constraint:

```pycon
>>> param = Param(rules=[PatternRule(r'^[A-Z]{3}$')])
>>> param.set('ABC')
>>> param.get()
'ABC'
```

Set a runtime value for the parameter:

```pycon
>>> param.set(6)
>>> param.get()
6
```

<a id="tessara.core.parameters.Param.set"></a>

#### set(value, strict=False)

Set the parameter value at runtime.

* **Parameters:**
  * **value** (*Any*) – Value to set.
  * **strict** ([*bool*](https://docs.python.org/3/library/functions.html#bool) *,* *default False*) – If True, validate the value against all registered rules before setting.
    Raises ValidationError if any rule fails.
* **Returns:**
  Self, for method chaining.
* **Return type:**
  [Param](#tessara.core.parameters.Param)
* **Raises:**
  [**ValidationError**](#tessara.core.errors.validation.ValidationError) – If strict=True and validation fails.

<a id="tessara.core.parameters.Param.validate_value"></a>

#### validate_value(value)

Validate a value against all registered rules.

* **Parameters:**
  **value** (*Any*) – Value to validate.
* **Raises:**
  [**ValidationError**](#tessara.core.errors.validation.ValidationError) – On the first failing rule.

<a id="tessara.core.parameters.Param.value"></a>

#### *property* value *: [Any](https://docs.python.org/3/library/typing.html#typing.Any)*

Return the explicitly set value, or None if not set.

* **Returns:**
  The runtime value, or `None` when unset.
  Use `is_set` to distinguish between “set to None” and “not set”.
* **Return type:**
  Any

<a id="tessara.core.parameters.Param.is_set"></a>

#### *property* is_set *: [bool](https://docs.python.org/3/library/functions.html#bool)*

Return `True` if the value has been explicitly set (even to `None`).

* **Returns:**
  Whether a runtime value has been assigned.
* **Return type:**
  [bool](https://docs.python.org/3/library/functions.html#bool)

<a id="tessara.core.parameters.Param.get"></a>

#### get()

Retrieve the current value or default.

* **Returns:**
  The runtime value if explicitly set (even if `None`),
  otherwise the default value.
* **Return type:**
  Any

<a id="tessara.core.parameters.Param.register_rule"></a>

#### register_rule(rule)

Add a rule to validate the parameter.

* **Parameters:**
  **rule** ([*RuleProtocol*](#tessara.core.types.RuleProtocol)) – Any object implementing `check(value) -> bool` and
  `get_error(value) -> Exception | None`.
* **Raises:**
  [**TypeError**](https://docs.python.org/3/library/exceptions.html#TypeError) – If *rule* does not satisfy the RuleProtocol.

<a id="tessara.core.parameters.Param.copy"></a>

#### copy()

Create a deep copy of the parameter, namely all the rules. Used to set a new value.

* **Returns:**
  Independent copy of this parameter.
* **Return type:**
  Self

<a id="tessara.core.parameters.Param.to_dict"></a>

#### to_dict(registry=None)

Serialize the parameter to a dictionary.

* **Parameters:**
  **registry** ([*RuleRegistryProtocol*](#tessara.core.types.RuleRegistryProtocol) *,* *optional*) – Registry used to serialize rules. If not provided, rules are serialized
  as class names only (for documentation purposes).
* **Returns:**
  Dictionary representation of the parameter containing:
  - ‘value’: Current runtime value (if set)
  - ‘default’: Default value (if set)
  - ‘rules’: List of serialized rules
* **Return type:**
  Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]

### Example

```pycon
>>> param = Param(default=10, rules=[TypeRule(int), RangeRule(gt=0)])
>>> param.to_dict()
{'value': None, 'default': 10, 'rules': [{'type': 'TypeRule'}, ...]}
```

<a id="tessara.core.parameters.Param.from_dict"></a>

#### *classmethod* from_dict(data, registry=None)

Create a Param instance from a dictionary.

* **Parameters:**
  * **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Dictionary containing ‘value’ and/or ‘default’ keys.
  * **registry** ([*RuleRegistryProtocol*](#tessara.core.types.RuleRegistryProtocol) *,* *optional*) – Registry used to deserialize rules. If not provided, the default registry is used.
* **Returns:**
  New parameter instance with the specified values.
* **Return type:**
  [Param](#tessara.core.parameters.Param)

### Example

```pycon
>>> data = {'value': 5, 'default': 10}
>>> param = Param.from_dict(data)
>>> param.get()
5
```

<a id="tessara.core.parameters.ParameterSet"></a>

### *class* tessara.core.parameters.ParameterSet(\*args, relation_rules=None, \*\*kwargs)

Bases: [`UserDict`](https://docs.python.org/3/library/collections.html#collections.UserDict)[[`str`](https://docs.python.org/3/library/stdtypes.html#str), [`Param`](#tessara.core.parameters.Param)]

Manage a collection of parameters.

* **Parameters:**
  * **\*args** ([*dict*](https://docs.python.org/3/library/stdtypes.html#dict)) – Positional arguments to initialize the parameter set.
    Used to pass a dictionary as the first argument.
  * **relation_rules** (*List* *[**RelationRule* *]* *,* *optional*) – Relation rules to apply to the parameters. Each element is a tuple (rule, targets).
  * **\*\*kwargs** ([*Param*](#tessara.core.parameters.Param)) – Keyword arguments to initialize the parameter set.
    If the values are not Param objects, they will be converted to Param objects and the
    provided value will serve as the ‘default’ attribute of the Param object.

### Notes

Instances of `ParameterSet` behave like dictionaries. All the methods of the UserDict class
are available for this object, and by extension all the dict methods. The main difference is
that the values are `Param` objects, which provide additional validation and constraints.

Dot notation access (e.g. `params.model`) returns `Param` or `ParameterSet` objects,
never raw values. Use `get()` or `get_value()` to retrieve values directly.

The `add`, `remove` and `set` methods provide flexibility for hierarchical construction
of parameter sets that can mirror a hierarchy of workflows, from the most general to the most
specific.

> **See also**
>
> [`Param`](#tessara.core.parameters.Param)
> : Custom parameter class with validation constraints.
>
> [`collections.UserDict`](https://docs.python.org/3/library/collections.html#collections.UserDict)
> : Inherit from this class to create a dictionary-like object.

### Examples

Create a parameter set with two parameters:

```pycon
>>> params = ParameterSet(
...     param1=Param(default=42, rules=RangeRule(gt=0)),
...     param2=Param(rules=TypeRule(str))
... )
```

Retrieve a parameter value:

```pycon
>>> params.get('param1')
42
```

Access nested Param or ParameterSet objects via dot notation:

```pycon
>>> params.model.lr        # returns the Param object
>>> params.model.lr.get()  # returns its value
```

<a id="tessara.core.parameters.ParameterSet.add"></a>

#### add(name, param)

Add a new parameter in the set with a unique name.

* **Parameters:**
  * **name** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Unique key for the parameter.
  * **param** (*Any*) – If `param` is already a Param or ParameterSet, it will be added directly.
    Otherwise, a new Param object will be created with the provided value as the default.

<a id="tessara.core.parameters.ParameterSet.remove"></a>

#### remove(name)

Remove a parameter from the set by its name.

* **Parameters:**
  **name** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Key of the parameter to remove.

<a id="tessara.core.parameters.ParameterSet.get"></a>

#### get(name)

Retrieve the *value* of a parameter by its name.

* **Parameters:**
  **name** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Parameter name (single segment, no dot notation).
* **Returns:**
  The current value if set, otherwise the default.
* **Return type:**
  Any

<a id="tessara.core.parameters.ParameterSet.get_value"></a>

#### get_value(name)

Retrieve a parameter value by name, supporting dot notation.

* **Parameters:**
  **name** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Parameter name, possibly dot-separated (e.g. `"model.lr"`).
* **Returns:**
  The current value if set, otherwise the default.
* **Return type:**
  Any
* **Raises:**
  [**UnknownParameterError**](#tessara.core.errors.handling.UnknownParameterError) – If the path cannot be resolved or does not end at a Param.

<a id="tessara.core.parameters.ParameterSet.set"></a>

#### set(name, value)

Set the value of an existing parameter by name.

Supports dot notation for nested parameters (e.g. `"model.lr"`).

* **Parameters:**
  * **name** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Parameter name, possibly dot-separated.
  * **value** (*Any*) – Value to assign.
* **Raises:**
  [**UnknownParameterError**](#tessara.core.errors.handling.UnknownParameterError) – If the parameter does not exist.

<a id="tessara.core.parameters.ParameterSet.register_rule"></a>

#### register_rule(target, rule)

Register a rule for a specific parameter already present in the set.

* **Parameters:**
  * **target** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Name of the parameter targeted by the rule.
  * **rule** ([*RuleProtocol*](#tessara.core.types.RuleProtocol)) – Validation rule to apply to the parameter.

### Examples

Add a custom rule to a parameter:

```pycon
>>> params = ParameterSet(param1=Param(rules=[TypeRule(int)]))
>>> def is_even(value: Any) -> bool:
...     return value % 2 == 0
>>> params.register_rule('param1', CustomRule(is_even))
```

<a id="tessara.core.parameters.ParameterSet.register_relation_rule"></a>

#### register_relation_rule(rule, targets)

Register a relation rule between multiple parameters, for cross-parameter dependencies.

* **Parameters:**
  * **rule** ([*MultiValueRuleProtocol*](#tessara.core.types.MultiValueRuleProtocol)) – Relational validation rule to apply to the parameters.
  * **targets** (*Targets*) – Names of the parameters targeted by the rule (list or mapping).

### Notes

The format of the targets determines the internal call to the rule function.
If the targets are provided as a list, the parameters are passed as positional arguments.
If the targets are provided as a dictionary, the parameters are passed as keyword arguments.

### Examples

```pycon
>>> params = ParameterSet(param1=Param(default=1), param2=Param(default=2))
>>> def is_greater_than(x: int, y: int) -> bool:
...     return x > y
>>> from tessara.validation.rules import MultiValueRule
>>> greater_than_rule = MultiValueRule(is_greater_than)
>>> params.register_relation_rule(greater_than_rule, ['param1', 'param2'])
```

<a id="tessara.core.parameters.ParameterSet.copy"></a>

#### copy()

Create a deep copy of the parameter set, including all nested ParameterSets and Params.

* **Returns:**
  Independent copy of this parameter set.
* **Return type:**
  Self

<a id="tessara.core.parameters.ParameterSet.to_dict"></a>

#### to_dict(values_only=False)

Serialize the parameter set to a dictionary.

* **Parameters:**
  **values_only** ([*bool*](https://docs.python.org/3/library/functions.html#bool) *,* *default False*) – If True, return only the current values (or defaults) of parameters.
  If False, return the full serialization including Param metadata.
* **Returns:**
  Dictionary representation of the parameter set.
* **Return type:**
  Dict[[str](https://docs.python.org/3/library/stdtypes.html#str), Any]

### Examples

Get values only (useful for configuration export):

```pycon
>>> params = ParameterSet(lr=Param(default=0.01), epochs=Param(default=100))
>>> params.to_dict(values_only=True)
{'lr': 0.01, 'epochs': 100}
```

Get full serialization:

```pycon
>>> params.to_dict()
{'lr': {'value': None, 'default': 0.01, 'rules': []}, ...}
```

Nested parameter sets are recursively serialized:

```pycon
>>> params = ParameterSet(model=ParameterSet(lr=Param(default=0.01)))
>>> params.to_dict(values_only=True)
{'model': {'lr': 0.01}}
```

<a id="tessara.core.parameters.ParameterSet.from_dict"></a>

#### *classmethod* from_dict(data, values_only=False)

Create a ParameterSet from a dictionary.

* **Parameters:**
  * **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Dictionary to convert. Structure depends on `values_only`.
  * **values_only** ([*bool*](https://docs.python.org/3/library/functions.html#bool) *,* *default False*) – If True, treats values as parameter values/defaults directly.
    If False, expects full Param serialization format.
* **Returns:**
  New parameter set instance.
* **Return type:**
  [ParameterSet](#tessara.core.parameters.ParameterSet)

### Examples

From values (configuration-style):

```pycon
>>> data = {'lr': 0.01, 'epochs': 100}
>>> params = ParameterSet.from_dict(data, values_only=True)
```

Nested dictionaries become nested ParameterSets:

```pycon
>>> data = {'model': {'lr': 0.01}}
>>> params = ParameterSet.from_dict(data, values_only=True)
>>> params.model.lr.get()
0.01
```

<a id="tessara.core.parameters.ParamGrid"></a>

### *class* tessara.core.parameters.ParamGrid(param, sweep_values=None, \*, policy=None)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Wrapper encapsulating a parameter intended for sweeping over multiple values.

To represent all parameters uniformly in the ParameterSet, this wrapper behaves like a basic
parameter for rule related behavior, except that:

- It also stores a list of values that need to be traversed during a parameter sweep.
- It does not store a value, as it is intended to be used as a template for generating multiple
  `Param` instances.

The sweep values can be set either at the moment of defining the ParamGrid instance, or
at runtime, for instance to define sweep values from a configuration object.

* **Parameters:**
  * **param** ([*Param*](#tessara.core.parameters.Param)) – Underlying parameter that defines validation rules.
  * **sweep_values** (*List* *[**Any* *]* *,* *optional*) – Values over which the parameter should be swept.
  * **policy** ([*SweepMaterializationPolicy*](#tessara.core.parameters.SweepMaterializationPolicy) *,* *optional*) – Policy controlling how sweep candidates become concrete Param objects.

### Examples

Define a parameter sweep:

```pycon
>>> param = ParamGrid(Param(rules=TypeRule(int)), sweep_values=[1, 2, 3])
```

<a id="tessara.core.parameters.ParamGrid.register_rule"></a>

#### register_rule(rule)

Delegate rule registration to the underlying `Param` instance.

* **Parameters:**
  **rule** ([*RuleProtocol*](#tessara.core.types.RuleProtocol)) – Validation rule to add.

<a id="tessara.core.parameters.ParamGrid.iter_values"></a>

#### iter_values()

Iterate over sweep values.

* **Returns:**
  Iterator over the configured sweep values.
* **Return type:**
  Iterable[Any]

<a id="tessara.core.parameters.ParamGrid.make_param"></a>

#### make_param(value)

Create a Param instance with a specific sweep value.

* **Parameters:**
  **value** (*Any*) – Concrete value drawn from the sweep grid.
* **Returns:**
  Deep copy of the base parameter with *value* set.
* **Return type:**
  [Param](#tessara.core.parameters.Param)

<a id="tessara.core.parameters.ParamGrid.generate_params"></a>

#### generate_params()

Generate `Param` instances for each sweep value while keeping validation rules.

* **Yields:**
  *Param* – `Param` instances with the values to sweep over. Each instance has the same rules and
  constraints as the base `Param` object in the ParamGrid, but with a single value set.

<a id="module-tessara.core.types"></a>

<a id="types"></a>

## Types

Shared type definitions for the tessara framework.

<a id="tessara.core.types.Targets"></a>

### tessara.core.types.Targets *: [TypeAlias](https://docs.python.org/3/library/typing.html#typing.TypeAlias)* *= collections.abc.Iterable[str] | collections.abc.Mapping[str, str]*

Specification of target parameters by name, as either a list of strings or a mapping of strings.

<a id="tessara.core.types.RuleProtocol"></a>

### *class* tessara.core.types.RuleProtocol(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Structural protocol for single-value validation rules.

Any object implementing `check` and `get_error` can serve as a rule
for `Param` validation, without requiring inheritance from a specific base class.

<a id="tessara.core.types.RuleProtocol.check"></a>

#### check(value)

Return `True` if *value* satisfies the rule.

* **Parameters:**
  **value** (*Any*) – Value to validate.

<a id="tessara.core.types.RuleProtocol.get_error"></a>

#### get_error(value)

Return an error if *value* fails, otherwise `None`.

* **Parameters:**
  **value** (*Any*) – Value to validate.

<a id="tessara.core.types.MultiValueRuleProtocol"></a>

### *class* tessara.core.types.MultiValueRuleProtocol(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Structural protocol for multi-value (relational) validation rules.

<a id="tessara.core.types.MultiValueRuleProtocol.check"></a>

#### check(\*args, \*\*kwargs)

Return `True` if the relational constraint holds.

* **Parameters:**
  * **\*args** (*Any*) – Positional values to check.
  * **\*\*kwargs** (*Any*) – Keyword values to check.

<a id="tessara.core.types.MultiValueRuleProtocol.get_error"></a>

#### get_error(\*args, \*\*kwargs)

Return an error if the relation fails, otherwise `None`.

* **Parameters:**
  * **\*args** (*Any*) – Positional values to check.
  * **\*\*kwargs** (*Any*) – Keyword values to check.

<a id="tessara.core.types.RuleRegistryProtocol"></a>

### *class* tessara.core.types.RuleRegistryProtocol(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Structural protocol for rule registries used in serialization.

<a id="tessara.core.types.RuleRegistryProtocol.serialize"></a>

#### serialize(rule)

Serialize a rule instance to a dictionary.

* **Parameters:**
  **rule** (*Any*) – Rule instance to serialize.

<a id="tessara.core.types.RuleRegistryProtocol.deserialize"></a>

#### deserialize(data)

Reconstruct a rule instance from a dictionary.

* **Parameters:**
  **data** (*Dict* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Serialized rule payload.

<a id="tessara.core.types.RelationRule"></a>

### tessara.core.types.RelationRule

Tuple of a multi-value rule instance and its target specification.

alias of `Tuple`[[`MultiValueRuleProtocol`](#tessara.core.types.MultiValueRuleProtocol), [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable)[[`str`](https://docs.python.org/3/library/stdtypes.html#str)] | [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[`str`](https://docs.python.org/3/library/stdtypes.html#str), [`str`](https://docs.python.org/3/library/stdtypes.html#str)]]

<a id="module-tessara.core.errors.handling"></a>

<a id="errors-handling"></a>

## Errors — Handling

Custom exceptions raised during parameter manipulation.

<a id="tessara.core.errors.handling.MissingValueError"></a>

### *exception* tessara.core.errors.handling.MissingValueError(message=None)

Bases: [`ValidationError`](#tessara.core.errors.validation.ValidationError)

Exception raised when a parameter is missing.

<a id="tessara.core.errors.handling.OverrideParameterError"></a>

### *exception* tessara.core.errors.handling.OverrideParameterError

Bases: [`Exception`](https://docs.python.org/3/library/exceptions.html#Exception)

Exception raised when a parameter is overridden in a ParameterSet.

<a id="tessara.core.errors.handling.UnknownParameterError"></a>

### *exception* tessara.core.errors.handling.UnknownParameterError

Bases: [`KeyError`](https://docs.python.org/3/library/exceptions.html#KeyError)

Exception raised when a parameter name is not found in a ParameterSet.

<a id="module-tessara.core.errors.validation"></a>

<a id="errors-validation"></a>

## Errors — Validation

Custom exceptions raised during the validation of parameters.

<a id="tessara.core.errors.validation.ValidationError"></a>

### *exception* tessara.core.errors.validation.ValidationError(message=None)

Bases: [`Exception`](https://docs.python.org/3/library/exceptions.html#Exception)

Base class for all validation errors, raised when a parameter is invalid.

* **Parameters:**
  **message** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *optional*) – Explicit error message. When `None`, `format_message` is called.

> **See also**
>
> [`Exception`](https://docs.python.org/3/library/exceptions.html#Exception)
> : Base class for all exceptions in Python.

<a id="tessara.core.errors.validation.ValidationError.format_message"></a>

#### format_message()

Format an error message to provide more context if the rule fails.

Override in subclasses to introduce dynamic placeholders to fill with runtime value(s) for
custom default messages.

Default implementation: Static message.

* **Returns:**
  Human-readable error message.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="tessara.core.errors.validation.TypeValidationError"></a>

### *exception* tessara.core.errors.validation.TypeValidationError(value, expected_type)

Bases: [`ValidationError`](#tessara.core.errors.validation.ValidationError)

Exception raised when a parameter has an invalid type.

* **Parameters:**
  * **value** (*Any*) – The value that failed type validation.
  * **expected_type** ([*type*](https://docs.python.org/3/library/functions.html#type) *|* [*tuple*](https://docs.python.org/3/library/stdtypes.html#tuple) *[*[*type*](https://docs.python.org/3/library/functions.html#type) *]*) – The required type(s).

### Examples

For a unique expected type:

```pycon
>>> raise TypeValidationError(1, str)
Traceback (most recent call last):
...
TypeValidationError: Type 'int' for value 1, required 'str'.
```

For several allowed types:

```pycon
>>> raise TypeValidationError(1, (str, float))
Traceback (most recent call last):
...
TypeValidationError: Type 'int' for value 1, required 'str' or 'float'.
```

<a id="tessara.core.errors.validation.TypeValidationError.format_message"></a>

#### format_message()

Format a message describing the type mismatch.

* **Returns:**
  Human-readable error message.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="tessara.core.errors.validation.RangeValidationError"></a>

### *exception* tessara.core.errors.validation.RangeValidationError(value, ge=None, gt=None, le=None, lt=None)

Bases: [`ValidationError`](#tessara.core.errors.validation.ValidationError)

Exception raised when a parameter is out of bounds.

* **Parameters:**
  * **value** (*Any*) – The value that fell outside the allowed range.
  * **ge** ([*float*](https://docs.python.org/3/library/functions.html#float) *,* *optional*) – Minimum value (inclusive).
  * **gt** ([*float*](https://docs.python.org/3/library/functions.html#float) *,* *optional*) – Minimum value (exclusive).
  * **le** ([*float*](https://docs.python.org/3/library/functions.html#float) *,* *optional*) – Maximum value (inclusive).
  * **lt** ([*float*](https://docs.python.org/3/library/functions.html#float) *,* *optional*) – Maximum value (exclusive).

### Examples

```pycon
>>> raise RangeValidationError(5, ge=10)
Traceback (most recent call last):
...
RangeValidationError: Value 5 out of bounds: required >= 10.
```

<a id="tessara.core.errors.validation.RangeValidationError.format_message"></a>

#### format_message()

Format a message listing the violated boundary constraints.

* **Returns:**
  Human-readable error message.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="tessara.core.errors.validation.PatternValidationError"></a>

### *exception* tessara.core.errors.validation.PatternValidationError(value, pattern)

Bases: [`ValidationError`](#tessara.core.errors.validation.ValidationError)

Exception raised when a parameter does not match a regular expression.

* **Parameters:**
  * **value** (*Any*) – The value that did not match the pattern.
  * **pattern** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Regular expression pattern that was expected.

### Examples

```pycon
>>> raise PatternValidationError("abc", r"\d+")
Traceback (most recent call last):
...
PatternValidationError: Value 'abc' does not match regex pattern '\d+'.
```

<a id="tessara.core.errors.validation.PatternValidationError.format_message"></a>

#### format_message()

Format a message showing the value and expected pattern.

* **Returns:**
  Human-readable error message.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="tessara.core.errors.validation.OptionValidationError"></a>

### *exception* tessara.core.errors.validation.OptionValidationError(value, options)

Bases: [`ValidationError`](#tessara.core.errors.validation.ValidationError)

Exception raised when a parameter’s value does not belong the allowed options.

* **Parameters:**
  * **value** (*Any*) – The value that was not among the allowed options.
  * **options** (*Set* *[**Any* *]*) – The allowed values.

### Examples

```pycon
>>> raise OptionValidationError("A", ["B", "C"])
Traceback (most recent call last):
...
OptionValidationError: Value 'A' not among allowed options: ['B', 'C'].
```

<a id="tessara.core.errors.validation.OptionValidationError.format_message"></a>

#### format_message()

Format a message listing the allowed options.

* **Returns:**
  Human-readable error message.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="tessara.core.errors.validation.CustomValidationError"></a>

### *exception* tessara.core.errors.validation.CustomValidationError(value, func)

Bases: [`ValidationError`](#tessara.core.errors.validation.ValidationError)

Exception raised when a custom validation rule fails.

* **Parameters:**
  * **value** (*Any*) – The value that did not pass the custom check.
  * **func** (*Callable* *[* *[**Any* *]* *,* [*bool*](https://docs.python.org/3/library/functions.html#bool) *]*) – The validation function that rejected the value.

### Examples

```pycon
>>> def is_even(value):
...     return value % 2 == 0
>>> raise CustomValidationError(3, is_even)
Traceback (most recent call last):
...
CustomValidationError: Value 3 does not satisfy the custom validation function 'is_even'.
```

<a id="tessara.core.errors.validation.CustomValidationError.format_message"></a>

#### format_message()

Format a message naming the custom function that failed.

* **Returns:**
  Human-readable error message.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="tessara.core.errors.validation.RelationValidationError"></a>

### *exception* tessara.core.errors.validation.RelationValidationError(func, args=None, kwargs=None)

Bases: [`ValidationError`](#tessara.core.errors.validation.ValidationError)

Exception raised when a relational validation rule fails (targets multiple parameters).

* **Parameters:**
  * **func** (*Callable* *[* *...* *,* [*bool*](https://docs.python.org/3/library/functions.html#bool) *]*) – Relational validation function that was not satisfied.
  * **args** (*Iterable* *[**Any* *]* *,* *optional*) – Positional arguments passed to the function.
  * **kwargs** (*Mapping* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]* *,* *optional*) – Keyword arguments passed to the function.

### Notes

When possible, the function signature is retrieved to format the error message.
Otherwise, a fallback message is displayed.

Fallback message occurs when:

- Function parameters are positional-only but passed as keywords
- Function uses `*args` / `**kwargs`
- Signature inspection fails (e.g., built-in functions, `len`, `max`…)
- Provided arguments count or names mismatch the function signature

The function’s name is inferred from the \_\_name_\_ attribute if available, otherwise it uses
the repr() of the function. This is useful for lambda functions or functions without a name.

### Examples

```pycon
>>> def is_greater_than(x, y):
...     return x > y
```

Pass values as positional arguments:

```pycon
>>> raise RelationValidationError(is_greater_than, args=[1, 2])
Traceback (most recent call last):
...
RelationValidationError: Values do not satisfy the relation when calling `is_greater_than(x=1, y=2)`.
```

Pass values as keyword arguments:

```pycon
>>> raise RelationValidationError(is_greater_than, kwargs={'x': 1, 'y': 2})
Traceback (most recent call last):
...
RelationValidationError: Values do not satisfy the relation when calling `is_greater_than(x=1, y=2)`.
```

<a id="tessara.core.errors.validation.RelationValidationError.format_message"></a>

#### format_message()

Format a message binding the arguments to the function signature.

* **Returns:**
  Human-readable error message.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="tessara.core.errors.validation.bind_function_arguments"></a>

### tessara.core.errors.validation.bind_function_arguments(func, \*args, \*\*kwargs)

Bind arguments to a function signature.

* **Parameters:**
  * **func** (*Callable* *[* *...* *,* [*bool*](https://docs.python.org/3/library/functions.html#bool) *]*) – Function to bind arguments to.
  * **args** (*Iterable* *[**Any* *]*) – Positional arguments to bind.
  * **kwargs** (*Mapping* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*) – Keyword arguments to bind.
* **Returns:**
  Bound arguments to the function signature, exposing `args`,
  `kwargs`, `arguments`, and `signature`.
* **Return type:**
  [inspect.BoundArguments](https://docs.python.org/3/library/inspect.html#inspect.BoundArguments)

<a id="tessara.core.errors.validation.CheckError"></a>

### *exception* tessara.core.errors.validation.CheckError(exception)

Bases: [`ValidationError`](#tessara.core.errors.validation.ValidationError)

Exception raised when a validation check fails to execute, i.e. no outcome can be determined.

* **Parameters:**
  **exception** ([*Exception*](https://docs.python.org/3/library/exceptions.html#Exception)) – Original exception raised during the check execution.

<a id="tessara.core.errors.validation.CheckError.format_message"></a>

#### format_message()

Format a message wrapping the original exception.

* **Returns:**
  Human-readable error message.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="tessara.core.errors.validation.CompositeValidationError"></a>

### *exception* tessara.core.errors.validation.CompositeValidationError(errors, operator, value=None, rule_ids=None)

Bases: [`ValidationError`](#tessara.core.errors.validation.ValidationError)

Exception raised when a composite validation rule (AndRule or OrRule) fails.

* **Parameters:**
  * **errors** ([*list*](https://docs.python.org/3/library/stdtypes.html#list)) – Individual errors from the sub-rules that failed.
  * **operator** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – The logical operator (‘AND’ or ‘OR’).
  * **value** (*Any* *,* *optional*) – The value that failed validation.
  * **rule_ids** ([*list*](https://docs.python.org/3/library/stdtypes.html#list) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *]* *,* *optional*) – Names of the rules that failed.

<a id="tessara.core.errors.validation.CompositeValidationError.format_message"></a>

#### format_message()

Format a message aggregating sub-rule failures.

* **Returns:**
  Human-readable error message.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="tessara.core.errors.validation.CompositeValidationError.to_dict"></a>

#### to_dict()

Serialize the composite error to a dictionary.

* **Returns:**
  Dictionary representation of the error.
* **Return type:**
  [dict](https://docs.python.org/3/library/stdtypes.html#dict)

<a id="tessara.core.errors.validation.GlobalValidationError"></a>

### *exception* tessara.core.errors.validation.GlobalValidationError(errors)

Bases: [`ValidationError`](#tessara.core.errors.validation.ValidationError)

Exception raised when at least one error occurred during the validation of multiple parameters.

* **Parameters:**
  **errors** (*Iterable* *[*[*ValidationError*](#tessara.core.errors.validation.ValidationError) *]*) – Collection of individual validation errors.

### Notes

The global message is a concatenation of all individual error messages.

<a id="tessara.core.errors.validation.GlobalValidationError.format_message"></a>

#### format_message()

Format a combined message from all individual errors.

* **Returns:**
  Human-readable error message.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)

<a id="tessara.core.errors.validation.RuleDeserializationError"></a>

### *exception* tessara.core.errors.validation.RuleDeserializationError(reason, rule_type=None, payload=None)

Bases: [`ValidationError`](#tessara.core.errors.validation.ValidationError)

Exception raised when serialized validation policy cannot be materialized safely.

* **Parameters:**
  * **reason** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Description of why deserialization failed.
  * **rule_type** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *optional*) – Serialized rule type name, if available.
  * **payload** (*Mapping* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]* *,* *optional*) – Serialized data that could not be deserialized.

<a id="tessara.core.errors.validation.RuleDeserializationError.format_message"></a>

#### format_message()

Format a message identifying the rule type and failure reason.

* **Returns:**
  Human-readable error message.
* **Return type:**
  [str](https://docs.python.org/3/library/stdtypes.html#str)
