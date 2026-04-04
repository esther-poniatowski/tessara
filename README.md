# Tessara

[![Conda](https://img.shields.io/badge/conda-eresthanaconda--channel-blue)](docs/guide/installation.md)
[![Maintenance](https://img.shields.io/maintenance/yes/2026)]()
[![Last Commit](https://img.shields.io/github/last-commit/esther-poniatowski/tessara)](https://github.com/esther-poniatowski/tessara/commits/main)
[![Python](https://img.shields.io/badge/python-%E2%89%A53.12-blue)](https://www.python.org/)
[![License: GPL](https://img.shields.io/badge/License-GPL-yellow.svg)](https://opensource.org/licenses/GPL-3.0)

Defines and validates structured parameter sets for complex configurations.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Overview

### Motivation

Scientific computing and data analysis workflows depend on large, structured parameter
sets. Managing parameters manually — tracking defaults, enforcing types, validating
constraints, and sweeping over combinations — introduces repetitive boilerplate and
subtle bugs.

### Advantages

- **Declarative parameter specifications** — define parameters with types, defaults,
  bounds, and validation rules in a single source of truth.
- **Composable parameter sets** — combine and inherit parameter groups for modular
  configuration.
- **Parameter sweeps** — generate parameter grids and sweep combinations for
  experiments.
- **YAML serialization** — load and save parameter sets from YAML files with schema
  validation.

---

## Features

- [ ] **Typed parameters**: Define parameters with type annotations, default values,
  and validation constraints.
- [ ] **Dot-notation access**: Read and modify parameters and nested fields through
  attribute-style access.
- [ ] **Composable sets**: Combine, inherit, and override parameter groups.
- [ ] **Flexible defaults**: Set default values at definition time or override them at
  runtime.
- [ ] **Schema validation**: Enforce constraints on individual parameters via type hints
  for compact definitions.
- [ ] **Relational validation**: Enforce consistency across parameters through
  relational rules.
- [ ] **Parameter sweeps**: Generate parameter grids and sweep combinations with
  `ParamGrid` and `ParamSweeper`.
- [ ] **YAML configuration**: Load and save parameter sets from structured YAML files.

---

## Quick Start

```python
from tessara import ParamSet, Param

class ModelParams(ParamSet):
    learning_rate = Param(default=0.01, bounds=(1e-5, 1.0))
    epochs = Param(default=100, type=int)
    hidden_size = Param(default=256, type=int)

params = ModelParams()
params.learning_rate = 0.001
```

---

## Documentation

| Guide | Content |
| ----- | ------- |
| [Installation](docs/guide/installation.md) | Prerequisites, pip/conda/source setup |
| [Usage](docs/guide/usage.md) | Parameter sets, YAML loading, composition, sweeps |
| [Concepts](docs/guide/concepts.md) | Core abstractions and design |

Full API documentation and rendered guides are also available at
[esther-poniatowski.github.io/tessara](https://esther-poniatowski.github.io/tessara/).

---

## Contributing

Contribution guidelines are described in [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Acknowledgments

### Authors

**Author**: @esther-poniatowski

For academic use, the GitHub "Cite this repository" feature generates citations in
various formats. The [citation metadata](CITATION.cff) file is also available.

---

## License

This project is licensed under the terms of the
[GNU General Public License v3.0](LICENSE).
