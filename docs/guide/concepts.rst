Concepts
========

Parameters
----------

The ``Param`` class represents a single parameter with:

- **default**: Default value
- **dtype**: Expected data type
- **description**: Human-readable description

Parameters support validation through attached rules.

ParameterSet
------------

A ``ParameterSet`` groups related parameters together:

- Dot notation access (``params.learning_rate``)
- Dictionary-like interface (``params["learning_rate"]``)
- Serialization (``to_dict()``, ``from_dict()``)
- Iteration over parameter names and values

Validation Rules
----------------

Rules validate parameter values:

- **RangeRule**: Check numeric bounds
- **ChoiceRule**: Validate against allowed values
- **TypeRule**: Enforce type constraints
- **AndRule**: Combine rules with AND logic
- **OrRule**: Combine rules with OR logic

Example:

.. code-block:: python

   from tessara.validation import RangeRule, ChoiceRule, AndRule

   # Composite rule: value must be in range AND in choices
   rule = AndRule([
       RangeRule(min_val=0.0, max_val=1.0),
       ChoiceRule(choices=[0.1, 0.5, 1.0]),
   ])

ParamGrid and Sweeping
----------------------

``ParamGrid`` wraps a ``Param`` with multiple values to sweep:

.. code-block:: python

   grid = ParamGrid(
       Param(default=0.01),
       sweep_values=[0.01, 0.001, 0.0001]
   )

``ParamSweeper`` generates all combinations lazily:

.. code-block:: python

   sweeper = ParamSweeper(params)
   for combo in sweeper.generate():
       run_experiment(combo)
