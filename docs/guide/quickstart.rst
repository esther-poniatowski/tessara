Quickstart
==========

Installation
------------

.. code-block:: bash

   pip install tessara

Basic Usage
-----------

Define parameters with defaults:

.. code-block:: python

   from tessara import ParameterSet, Param

   params = ParameterSet(
       learning_rate=Param(default=0.01),
       epochs=Param(default=100),
       model_name=Param(default="resnet"),
   )

   # Access parameter values
   print(params.learning_rate.get())  # 0.01

   # Modify values
   params.learning_rate = 0.001
   print(params.learning_rate.get())  # 0.001

Loading from YAML
-----------------

.. code-block:: python

   from tessara import ParameterSet, Param, ParamAssigner

   params = ParameterSet(
       learning_rate=Param(default=0.01),
       epochs=Param(default=100),
   )

   # Load from config file
   assigner = ParamAssigner(params)
   assigner.from_yaml("config.yaml")

Parameter Sweeps
----------------

.. code-block:: python

   from tessara import ParameterSet, Param, ParamGrid, ParamSweeper

   params = ParameterSet(
       lr=ParamGrid(Param(), sweep_values=[0.01, 0.001, 0.0001]),
       batch_size=ParamGrid(Param(), sweep_values=[32, 64]),
   )

   sweeper = ParamSweeper(params)
   print(f"Total combinations: {len(sweeper)}")  # 6

   for combo in sweeper:
       print(combo.to_dict(values_only=True))
