# Usage

## Define Parameters

`Param` holds a default value and optional validation rules. `ParameterSet`
groups named parameters with dot-notation access.

```python
from tessara.core.parameters import Param, ParameterSet
from tessara.validation.rules import TypeRule, RangeRule

params = ParameterSet(
    learning_rate=Param(default=0.01, rules=[TypeRule(float), RangeRule(gt=0, le=1.0)]),
    epochs=Param(default=100, rules=[TypeRule(int), RangeRule(gt=0)]),
    model_name=Param(default="resnet"),
)
```

`Param` accepts two keyword arguments:

| Argument  | Type                      | Description                      |
|-----------|---------------------------|----------------------------------|
| `default` | `Any` (default `None`)    | Default value                    |
| `rules`   | `Iterable[RuleProtocol]`  | Validation rules (default `None`)|

Plain values passed to `ParameterSet` are auto-wrapped as `Param(default=value)`:

```python
params = ParameterSet(learning_rate=0.01, epochs=100)
```

## Get and Set Values

`Param.get()` returns the runtime value if set, otherwise the default.
Dot notation on a `ParameterSet` returns the `Param` object, not the value.

```python
params.learning_rate.get()   # 0.01
params.learning_rate.set(0.001)
params.learning_rate.get()   # 0.001
```

`ParameterSet.get(name)` retrieves the value directly:

```python
params.get("learning_rate")  # 0.001
```

Dot-notation assignment delegates to `Param.set()` with `strict=False`
(no validation):

```python
params.learning_rate = 0.005
params.learning_rate.get()   # 0.005
```

To validate on assignment, call `Param.set()` with `strict=True`:

```python
params.learning_rate.set(5.0, strict=True)  # raises RangeValidationError
```

`Param.is_set` distinguishes between "not yet set" and "explicitly set to
None":

```python
p = Param(default=10)
p.is_set   # False
p.set(None)
p.is_set   # True
p.get()    # None  (runtime value takes precedence over default)
```

## Nest Parameter Sets

`ParameterSet` values can be other `ParameterSet` instances, forming a tree:

```python
params = ParameterSet(
    model=ParameterSet(
        hidden_size=Param(default=256, rules=[TypeRule(int)]),
        dropout=Param(default=0.1),
    ),
    training=ParameterSet(
        lr=Param(default=0.01),
        epochs=Param(default=100),
    ),
)

params.model.hidden_size.get()  # 256
```

`ParameterSet.get_value(name)` supports dot-separated paths:

```python
params.get_value("model.hidden_size")  # 256
```

`ParameterSet.set(name, value)` sets a value by dot-separated path:

```python
params.set("model.hidden_size", 512)
```

`ParameterSet.add(name, param)` adds a new parameter. Duplicate names
raise `OverrideParameterError`:

```python
params.add("optimizer", Param(default="adam"))
```

`ParameterSet.remove(name)` removes a parameter by name:

```python
params.remove("optimizer")
```

## Validate with Rules

Every rule implements `check(value) -> bool` and
`get_error(value) -> ValidationError | None`.

### Built-in Single-Value Rules

All single-value rules live in `tessara.validation.rules`.

```python
from tessara.validation.rules import (
    TypeRule,
    RangeRule,
    PatternRule,
    OptionRule,
    CustomRule,
)
```

**TypeRule** -- enforce a type or union of types:

```python
TypeRule(int)
TypeRule((int, float))
```

**RangeRule** -- enforce numeric bounds (`gt`, `ge`, `lt`, `le`):

```python
RangeRule(gt=0, le=100)
RangeRule(ge=-1.0, lt=1.0)
```

**PatternRule** -- match a regular expression:

```python
PatternRule(r"^[A-Z]{3}$")
```

**OptionRule** -- restrict to an explicit set of allowed values:

```python
OptionRule(["adam", "sgd", "rmsprop"])
```

**CustomRule** -- pass any `Callable[[Any], bool]`:

```python
def is_even(x):
    return x % 2 == 0

CustomRule(is_even)
```

### Composite Rules

`AndRule` requires all sub-rules to pass. `OrRule` requires at least one.

```python
from tessara.validation.rules import AndRule, OrRule

# Integer between 0 and 100
strict_int = AndRule(TypeRule(int), RangeRule(ge=0, le=100))

# Accept either string or integer
flexible = OrRule(TypeRule(str), TypeRule(int))

# Nested composites: int AND (negative OR > 100)
extreme_int = AndRule(
    TypeRule(int),
    OrRule(RangeRule(lt=0), RangeRule(gt=100)),
)
```

### Register Rules after Construction

`Param.register_rule()` and `ParameterSet.register_rule()` add rules
after the parameter already exists:

```python
params = ParameterSet(count=Param(default=10))
params.register_rule("count", RangeRule(gt=0))
```

### Relation Rules (Cross-Parameter Constraints)

`MultiValueRule` validates a relationship between multiple parameters.
Register relation rules on a `ParameterSet`:

```python
from tessara.validation.rules import MultiValueRule

def lr_below_dropout(lr, dropout):
    return lr < dropout

params = ParameterSet(
    lr=Param(default=0.01),
    dropout=Param(default=0.5),
)
params.register_relation_rule(
    MultiValueRule(lr_below_dropout),
    ["lr", "dropout"],
)
```

Targets can be a list (positional arguments) or a dict mapping parameter
names to function argument names (keyword arguments):

```python
params.register_relation_rule(
    MultiValueRule(lr_below_dropout),
    {"lr": "lr", "dropout": "dropout"},
)
```

Relation rules can also be passed at construction via the `relation_rules`
keyword:

```python
params = ParameterSet(
    lr=Param(default=0.01),
    dropout=Param(default=0.5),
    relation_rules=[(MultiValueRule(lr_below_dropout), ["lr", "dropout"])],
)
```

## Run Validation

The `Validator` class aggregates all rules (per-parameter and relational)
and runs them in one pass.

```python
from tessara.validation.validator import Validator

valid = Validator(params).validate()  # returns True or False
```

In strict mode, `validate()` raises `GlobalValidationError` on failure:

```python
from tessara.core.errors.validation import GlobalValidationError

validator = Validator(params, strict=True)
try:
    validator.validate()
except GlobalValidationError as exc:
    print(exc.errors)  # list of individual ValidationError instances
```

The validation recorder lists every check performed:

```python
validator = Validator(params)
validator.validate()

for entry in validator.recorder.get_report():
    print(entry.rule, entry.targets, entry.success, entry.message)
```

Filter checks by rule type with `include_only` or `exclude`:

```python
validator.validate(include_only=[TypeRule])
validator.validate(exclude=[PatternRule])
```

## Compose Parameter Sets

`ParamComposer` merges multiple `ParameterSet` instances into one.
`ParameterSet` does not support the `+` operator.

```python
from tessara.handling.composer import ParamComposer

model_params = ParameterSet(
    hidden_size=Param(default=256),
    dropout=Param(default=0.1),
)
training_params = ParameterSet(
    lr=Param(default=0.01),
    epochs=Param(default=100),
)

composer = ParamComposer(model=model_params, training=training_params)
full_config = composer.compose()  # single ParameterSet with all parameters
```

`ParamComposer.merge()` merges two sets directly:

```python
merged = ParamComposer.merge(model_params, training_params)
```

Override existing parameters by passing `override=True`:

```python
merged = ParamComposer.merge(original, updated, override=True)
```

Control merge order with `set_precedence()` -- later entries override
earlier ones:

```python
composer = ParamComposer(defaults=defaults, overrides=overrides)
composer.set_precedence(["defaults", "overrides"])
full_config = composer.compose()
```

## Assign Values from Configuration

`ParamAssigner` loads runtime values from YAML files, OmegaConf objects, or
plain dictionaries.

```python
from tessara.handling.assigner import ParamAssigner

params = ParameterSet(
    lr=Param(default=0.01),
    epochs=Param(default=100),
    model=ParameterSet(hidden_size=Param(default=256)),
)

assigner = ParamAssigner(params)
```

### From a Dictionary

```python
assigner.from_dict({"lr": 0.001, "model": {"hidden_size": 512}})
params.lr.get()               # 0.001
params.model.hidden_size.get() # 512
```

### From YAML

```python
assigner.from_yaml("config.yaml")
```

The YAML file mirrors the parameter structure:

```yaml
lr: 0.001
epochs: 200
model:
  hidden_size: 512
```

OmegaConf loads by default when installed (supports variable interpolation).
Disable with `prefer_omegaconf=False` to force PyYAML:

```python
assigner.from_yaml("config.yaml", prefer_omegaconf=False)
```

### Set Individual Values

```python
assigner.set("lr", 0.005)
assigner.set("model.hidden_size", 1024)
```

### Strict Mode

Pass `strict=True` to reject unknown keys in the configuration:

```python
assigner.from_dict({"lr": 0.001, "unknown_key": 42}, strict=True)
# raises UnknownParameterError
```

## Bind Parameters to Functions

`ParamBinder` matches parameter names to a function's signature and calls
the function with those values.

```python
from tessara.handling.binder import ParamBinder

def train(lr, epochs, hidden_size=256):
    return f"lr={lr}, epochs={epochs}, hidden={hidden_size}"

params = ParameterSet(lr=Param(default=0.01), epochs=Param(default=100))
binder = ParamBinder(params)

result = binder.call(train)  # "lr=0.01, epochs=100, hidden=256"
```

`ParamBinder.query()` returns `inspect.BoundArguments` without calling the
function:

```python
bound = binder.query(train)
bound.arguments  # {'lr': 0.01, 'epochs': 100}
```

Only parameters whose names match the function signature are passed;
extra parameters are ignored.

## Sweep Parameter Grids

`ParamGrid` wraps a `Param` with a list of sweep values.
`ParamSweeper` generates all combinations via cartesian product.

```python
from tessara.core.parameters import ParamGrid
from tessara.handling.sweeper import ParamSweeper

params = ParameterSet(
    lr=ParamGrid(Param(rules=[TypeRule(float)]), sweep_values=[0.01, 0.001, 0.0001]),
    batch_size=ParamGrid(Param(rules=[TypeRule(int)]), sweep_values=[32, 64]),
    epochs=Param(default=100),
)

sweeper = ParamSweeper(params)
len(sweeper)  # 6

for combo in sweeper:
    print(combo.to_dict(values_only=True))
# {'batch_size': 32, 'epochs': 100, 'lr': 0.01}
# {'batch_size': 32, 'epochs': 100, 'lr': 0.001}
# ...
```

Each combination is a deep-copied `ParameterSet` with the sweep value set
on the underlying `Param`. Static parameters retain their originals.

`generate()` returns a lazy generator. `generate_all()` returns a list.

Sweep values can also be assigned at runtime via `ParamAssigner`:

```python
assigner = ParamAssigner(params)
assigner.from_dict({"lr": [0.1, 0.01], "batch_size": [16, 32, 64]})
```

## Serialize and Deserialize

`Param.to_dict()` and `ParameterSet.to_dict()` convert to plain
dictionaries. `from_dict()` reconstructs the objects.

```python
data = params.to_dict()
# {'lr': {'value': None, 'default': 0.01, 'rules': [...]}, ...}

restored = ParameterSet.from_dict(data)
```

Export values only (for saving configuration):

```python
values = params.to_dict(values_only=True)
# {'lr': 0.01, 'epochs': 100}
```

Reconstruct from value-only dictionaries:

```python
restored = ParameterSet.from_dict({"lr": 0.01, "epochs": 100}, values_only=True)
```

Rule serialization uses a `RuleRegistry`. The default registry handles
`TypeRule`, `RangeRule`, `PatternRule`, `OptionRule`, `CustomRule`, `AndRule`,
and `OrRule`. Custom rule classes can be registered:

```python
from tessara.validation.rules import RuleRegistry

registry = RuleRegistry()
registry.register(MyCustomRule)
```

## Next Steps

- [Concepts](concepts.md) -- Core abstractions and design.
- [API Reference](../api/index.md) -- Python API documentation.
