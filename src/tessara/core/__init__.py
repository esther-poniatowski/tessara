"""
tessara.core
============

Establishes the core API for constructing and composing parameters in the tessara framework.

The `core` module provides the foundational base classes for defining custom parameters: single
parameters and parameter sets.

The design prioritizes:
- Structured, modular, and extensible parameter definitions
- Consistent interaction across parameter types
- Seamless integration with parameter handling and processing


Modules
-------


Usage
-----
To create a parameter set:

1. Declare individual parameters using the `Parameter` class, specifying optional properties such as
   validation rules (types, ranges, etc.) and default values.
2. Group parameters into a `ParameterSet` object, which can be nested within other parameter sets.
3. Specify the structure of the parameter set, including the relationships between parameters and
   sweeps.

See Also
--------
test_core
    Tests for the core module.
"""
