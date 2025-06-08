# Tessara

[![Conda](https://img.shields.io/badge/conda-eresthanaconda--channel-blue)](#installation)
[![Maintenance](https://img.shields.io/maintenance/yes/2025)]()
[![Last Commit](https://img.shields.io/github/last-commit/esther-poniatowski/tessara)](https://github.com/esther-poniatowski/tessara/commits/main)
[![Python](https://img.shields.io/badge/python-supported-blue)](https://www.python.org/)
[![License: GPL](https://img.shields.io/badge/License-GPL-yellow.svg)](https://opensource.org/licenses/GPL-3.0)

Parameter management system for declarative definition, constraint enforcement, and modular composition.

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

Tessara introduces a parameter management framework for manipulating
parameters sets as structured objects with validation rules and modular compositions.

---

## Features

- [ ] **Structured declarative specifications**: Define parameters as typed objects with validation
  constraints, using predefined and custom rules.
- [ ] **Direct Parameter Access**: Retrieve parameters and nested fields using dot notation for
  clarity and uniformity.
- [ ] **Modular composition of parameter sets**: Organize parameters into reusable and composable
  collections that can be merged or overridden.
- [ ] **Flexible Value Setting**: Define default values at the definition time or runtime values.
- [ ] **Schema Validation**: Enforce constraints on single parameters, levering type hints for
  compact and readable definitions.
- [ ] **Relational Validation**: Enforce consistency across parameters by defining relational rules.
- [ ] **Sweeping exploration**: Define parameter sweeps for systematic experimentation and
  controlled variability.

---

## Installation

To install the package and its dependencies, use one of the following methods:

### Using Pip Installs Packages

Install the package from the GitHub repository URL via `pip`:

```bash
pip install git+https://github.com/esther-poniatowski/tessara.git
```

### Using Conda

Install the package from the private channel eresthanaconda:

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

To display the list of available commands and options:

```sh
tessara --help
```

### Programmatic Usage

To use the package programmatically in Python:

```python
import tessara
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
