# Tessara

[![Conda](https://img.shields.io/badge/conda-eresthanaconda--channel-blue)](#installation)
[![Maintenance](https://img.shields.io/maintenance/yes/2026)]()
[![Last Commit](https://img.shields.io/github/last-commit/esther-poniatowski/tessara)](https://github.com/esther-poniatowski/tessara/commits/main)
[![Python](https://img.shields.io/badge/python-supported-blue)](https://www.python.org/)
[![License: GPL](https://img.shields.io/badge/License-GPL-yellow.svg)](https://opensource.org/licenses/GPL-3.0)

Parameter management system for declaring, validating, and composing structured parameter sets.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Support](#support)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Overview

### Motivations

Complex workflows or models often rely on numerous interdependent parameters that must satisfy
structural, logical, and relational constraints. As configurations grow in size and complexity,
manual parameter handling becomes error-prone, difficult to validate, and hard to modularize across
components.

### Advantages

Tessara treats parameter sets as structured objects with validation rules and composable modules.

---

## Features

- [ ] **Declarative specifications**: Define parameters as typed objects with predefined and custom
  validation constraints.
- [ ] **Dot-notation access**: Retrieve parameters and nested fields through uniform dot notation.
- [ ] **Composable parameter sets**: Organize parameters into reusable collections that can be
  merged or overridden.
- [ ] **Flexible defaults**: Set default values at definition time or override them at runtime.
- [ ] **Schema validation**: Enforce constraints on individual parameters using type hints for
  compact definitions.
- [ ] **Relational validation**: Enforce consistency across parameters through relational rules.
- [ ] **Parameter sweeps**: Define systematic sweeps for controlled experimentation.

---

## Installation

### Using pip

Install from the GitHub repository:

```bash
pip install git+https://github.com/esther-poniatowski/tessara.git
```

### Using conda

Install from the eresthanaconda channel:

```bash
conda install tessara -c eresthanaconda
```

### From Source

1. Clone the repository:

      ```bash
      git clone https://github.com/esther-poniatowski/tessara.git
      ```

2. Create a dedicated virtual environment:

      ```bash
      cd tessara
      conda env create -f environment.yml
      ```

---

## Usage

### Command Line Interface (CLI)

Display version and platform diagnostics:

```sh
tessara info
```

### Programmatic Usage

Define parameters with validation rules:

```python
from tessara.core.parameters import Param, ParameterSet, ParamGrid
from tessara.validation.rules import TypeRule, RangeRule

# Single parameter with constraints
lr = Param(default=0.001, rules=[TypeRule(float), RangeRule(gt=0, lt=1)])

# Nested parameter set with dot-notation access
params = ParameterSet(
    model=ParameterSet(
        lr=Param(default=0.001),
        epochs=Param(default=100, rules=[TypeRule(int), RangeRule(ge=1)]),
    ),
    batch_size=ParamGrid(Param(), sweep_values=[32, 64, 128]),
)

# Set values and validate
params["model"]["lr"].set(0.01)
config = params.to_dict()
```

---

## Configuration

### Environment Variables

|Variable|Description|Default|Required|
|---|---|---|---|
|`VAR_1`|Description 1|None|Yes|
|`VAR_2`|Description 2|`false`|No|

### Configuration File

Configuration options are specified in YAML files located in the `config/` directory.

The canonical configuration schema is provided in [`config/default.yaml`](config/default.yaml).

```yaml
var_1: value1
var_2: value2
```

---

## Documentation

- [User Guide](https://esther-poniatowski.github.io/tessara/guide/)
- [API Documentation](https://esther-poniatowski.github.io/tessara/api/)

> [!NOTE]
> Documentation can also be browsed locally from the [`docs/`](docs/) directory.

## Support

**Issues**: [GitHub Issues](https://github.com/esther-poniatowski/tessara/issues)

**Email**: `{{ contact@example.com }}`

---

## Contributing

Please refer to the [contribution guidelines](CONTRIBUTING.md).

---

## Acknowledgments

### Authors & Contributors

**Author**: @esther-poniatowski

**Contact**: `{{ contact@example.com }}`

For academic use, please cite using the GitHub "Cite this repository" feature to
generate a citation in various formats.

Alternatively, refer to the [citation metadata](CITATION.cff).

### Third-Party Dependencies

- **[Library A](link)** - Purpose
- **[Library B](link)** - Purpose

---

## License

This project is licensed under the terms of the [GNU General Public License v3.0](LICENSE).
