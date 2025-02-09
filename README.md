# Tessara

**Tessara** is a Python package for defining and managing parameters as structured objects with constraints, rules, and modular compositions. It provides a flexible framework for parameter validation, ensuring correctness, consistency, and composability in complex configurations.

## Key Features

- **Structured Parameters**: Define parameters as objects with validation constraints, through predefined and custom rules.
- **Parameter Sets**: Group parameters into modular, composable collections.
- **Sweeping Mechanism**: Define parameter sweeps for systematic exploration of configurations.
- **Hierarchical and MOdular Composition**: Merge and override parameter sets for flexibility.
- **Flexible Value Setting**: Define default values at the definition time or runtime values, possibly from configuration files.
- **Validation**: Enforce constraints on sigle parameters and across parameters, to ensure consistency and relations.

## Installation

```sh
pip install tessara
```

## Usage

### Defining Parameters

```python
from tessara.core.parameters import Param
from tessara.validation.rules import TypeRule, RangeRule

param = Param(
    default=5,
    rules=[
        TypeRule(int),
        RangeRule(gt=0, le=10)
    ]
)

print(param.get_value())  # Output: 5
param.set_value(7)        # Valid assignment
```

### Defining Parameter Sweeps

```python
from tessara.core.parameters import SweepParam

sweep_param = SweepParam(sweep_values=[1, 2, 3, 4])
print(sweep_param.get_sweep_values())  # Output: [1, 2, 3, 4]
```

### Managing Parameter Sets

```python
from tessara.core.structures import ParameterSet

params = ParameterSet(
    learning_rate=Param(default=0.01),
    batch_size=Param(default=32)
)

print(params.get_value("learning_rate"))  # Output: 0.01
```

### Applying Validation Rules

```python
from tessara.validation.validator import Validator

validator = Validator(params)
if validator.validate():
    print("Validation passed.")
else:
    print("Validation failed.")
```

## Key Components

### `parameters`

- **`Param`**: Defines an individual parameter with validation constraints.
- **`SweepParam`**: Defines a parameter representing a sweep over multiple values.

### `structures`

- **`ParameterSet`**: Manages a collection of parameters.

### `validation.rules`
- **`Rule`**: Base class for validation rules.
- **`TypeRule`**: Ensures a value matches a required type.
- **`RangeRule`**: Ensures a value is within a specified range.
- **`PatternRule`**: Checks if a value matches a regex pattern.
- **`OptionRule`**: Validates against a set of allowed options.
- **`CustomRule`**: Allows custom validation functions.
- **`MultiValueRule`**: Validates relations between multiple parameters.

### `validation.validator`
- **`Validator`**: Applies validation rules to parameters and parameter sets.
- **`Checker`**: Encapsulates a single validation process.
- **`ValidationRecorder`**: Tracks validation reports and errors.


## License

This project is licensed under the GNU License.


