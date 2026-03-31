# Usage

Tessara manages structured parameter sets for scientific computing and data
analysis workflows. Parameters define types, defaults, bounds, and validation
rules; parameter sets compose and inherit; sweeps generate experiment grids.

## Defining Parameters

A `ParameterSet` groups typed parameters with defaults:

```python
from tessara import ParameterSet, Param

params = ParameterSet(
    learning_rate=Param(default=0.01),
    epochs=Param(default=100),
    model_name=Param(default="resnet"),
)
```

## Accessing and Modifying Values

Parameters support dot-notation access:

```python
print(params.learning_rate.get())  # 0.01

params.learning_rate = 0.001
print(params.learning_rate.get())  # 0.001
```

## Loading from YAML

Configuration files map directly to parameter sets:

```python
from tessara import ParamAssigner

assigner = ParamAssigner(params)
assigner.from_yaml("config.yaml")
```

The YAML file mirrors the parameter structure:

```yaml
learning_rate: 0.001
epochs: 200
model_name: transformer
```

## Composing Parameter Sets

Parameter sets combine and inherit for modular configuration:

```python
model_params = ParameterSet(
    hidden_size=Param(default=256, type=int),
    dropout=Param(default=0.1),
)

training_params = ParameterSet(
    learning_rate=Param(default=0.01),
    epochs=Param(default=100),
)

# Compose into a single set
full_config = model_params + training_params
```

## Running Parameter Sweeps

`ParamGrid` and `ParamSweeper` generate all combinations for experiments:

```python
from tessara import ParamGrid, ParamSweeper

params = ParameterSet(
    lr=ParamGrid(Param(), sweep_values=[0.01, 0.001, 0.0001]),
    batch_size=ParamGrid(Param(), sweep_values=[32, 64]),
)

sweeper = ParamSweeper(params)
print(f"Total combinations: {len(sweeper)}")  # 6

for combo in sweeper:
    print(combo.to_dict(values_only=True))
```

Each combination is a fully resolved parameter set ready for use in an
experiment run.

## Validating Parameters

Constraints enforce bounds and types at assignment time:

```python
params = ParameterSet(
    learning_rate=Param(default=0.01, bounds=(1e-5, 1.0)),
    epochs=Param(default=100, type=int),
)

params.learning_rate = 5.0  # raises ValidationError: out of bounds
```

## Next Steps

- [Concepts](concepts.md) — Core abstractions and design.
- [API Reference](../api/index.md) — Python API documentation.
