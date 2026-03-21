# Tessara Documentation

**Tessara** is a parameter management library for scientific computing workflows.
It provides type-safe parameter definitions, validation rules, and sweep generation.

```{toctree}
:maxdepth: 2
:caption: Contents:

guide/quickstart
guide/concepts
api/index
```

## Features

- **Type-safe parameters**: Define parameters with types, defaults, and constraints
- **Validation rules**: Built-in and custom validation with composite rules (And/Or)
- **Parameter sweeps**: Generator-based iteration over parameter grids
- **YAML configuration**: Load parameters from configuration files
- **Serialization**: Convert parameter sets to/from dictionaries

## Quick Example

```python
from tessara import ParameterSet, Param, ParamGrid, ParamSweeper

# Define parameters with validation
params = ParameterSet(
    learning_rate=Param(default=0.01),
    epochs=Param(default=100),
    batch_size=ParamGrid(Param(), sweep_values=[32, 64, 128]),
)

# Sweep over parameter combinations
for combo in ParamSweeper(params):
    print(combo.to_dict(values_only=True))
```

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
