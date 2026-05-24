<a id="handling-module"></a>

# Handling Module

Parameter assignment, binding, composition, sweeping, tree traversal, and
configuration I/O.

<a id="module-tessara.handling.assigner"></a>

<a id="assigner"></a>

## Assigner

Parameter assignment from configuration sources.

<a id="tessara.handling.assigner.Config"></a>

### *class* tessara.handling.assigner.Config(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Protocol for configuration objects used to pass runtime values to the parameters.

Provide a dictionary-like interface to access configuration values.

<a id="tessara.handling.assigner.Config.keys"></a>

#### keys()

Return the configuration keys.

<a id="tessara.handling.assigner.ParamAssigner"></a>

### *class* tessara.handling.assigner.ParamAssigner(params)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Assign specific values to a set of parameters.

Supports loading configuration from YAML files, OmegaConf objects, or dictionaries.

* **Parameters:**
  **params** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet)) – Parameters to bind to a configuration.

### Examples

Basic usage:

```pycon
>>> params = ParameterSet(lr=Param(default=0.01), epochs=Param(default=100))
>>> assigner = ParamAssigner(params)
>>> assigner.set('lr', 0.001)
>>> params.lr
0.001
```

Load from YAML file:

```pycon
>>> assigner = ParamAssigner(params).from_yaml('config.yaml')
```

Load from dictionary:

```pycon
>>> assigner = ParamAssigner(params).from_dict({'lr': 0.001, 'epochs': 50})
```

<a id="tessara.handling.assigner.ParamAssigner.set"></a>

#### set(name, value)

Set the value of an existing parameter by its name.

* **Parameters:**
  * **name** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Parameter name (supports dot notation for nested parameters).
  * **value** (*Any*) – Value to set.
* **Returns:**
  Self, for method chaining.
* **Return type:**
  [ParamAssigner](#tessara.handling.assigner.ParamAssigner)
* **Raises:**
  [**UnknownParameterError**](core.md#tessara.core.errors.handling.UnknownParameterError) – If the parameter does not exist.

#### WARNING
If a value is already set, the initial value will be overridden.

<a id="tessara.handling.assigner.ParamAssigner.apply_config"></a>

#### apply_config(config, recursive=True, strict=False)

Apply runtime configuration values to the parameters.

* **Parameters:**
  * **config** ([*Config*](#tessara.handling.assigner.Config)) – Configuration values to apply (dict-like object).
  * **recursive** ([*bool*](https://docs.python.org/3/library/functions.html#bool) *,* *default True*) – If True, recursively apply nested dictionaries to nested ParameterSets.
  * **strict** ([*bool*](https://docs.python.org/3/library/functions.html#bool) *,* *default False*) – If True, raise on unknown config keys and validate values.
* **Returns:**
  Self, for method chaining.
* **Return type:**
  [ParamAssigner](#tessara.handling.assigner.ParamAssigner)

### Notes

Parameters are set by querying the configuration object and retrieving the values for the
relevant keys which match the parameter names.

<a id="tessara.handling.assigner.ParamAssigner.from_yaml"></a>

#### from_yaml(path, prefer_omegaconf=True, strict=False)

Load configuration from a YAML file and apply to parameters.

* **Parameters:**
  * **path** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *or* *Path*) – Path to the YAML configuration file.
  * **prefer_omegaconf** ([*bool*](https://docs.python.org/3/library/functions.html#bool) *,* *default True*) – Use OmegaConf for loading if available.
  * **strict** ([*bool*](https://docs.python.org/3/library/functions.html#bool) *,* *default False*) – If True, raise on unknown config keys.
* **Returns:**
  Self, for method chaining.
* **Return type:**
  [ParamAssigner](#tessara.handling.assigner.ParamAssigner)
* **Raises:**
  * [**ImportError**](https://docs.python.org/3/library/exceptions.html#ImportError) – If PyYAML is not installed.
  * [**FileNotFoundError**](https://docs.python.org/3/library/exceptions.html#FileNotFoundError) – If the YAML file does not exist.

### Notes

If OmegaConf is installed, it will be used for loading (supports variable
interpolation and merging). Otherwise, falls back to PyYAML.

### Examples

```pycon
>>> assigner = ParamAssigner(params).from_yaml('config.yaml')
```

<a id="tessara.handling.assigner.ParamAssigner.from_dict"></a>

#### from_dict(data, strict=False)

Apply configuration from a dictionary.

* **Parameters:**
  * **data** ([*dict*](https://docs.python.org/3/library/stdtypes.html#dict)) – Dictionary of parameter names to values.
  * **strict** ([*bool*](https://docs.python.org/3/library/functions.html#bool) *,* *default False*) – If True, raise on unknown config keys.
* **Returns:**
  Self, for method chaining.
* **Return type:**
  [ParamAssigner](#tessara.handling.assigner.ParamAssigner)

### Examples

```pycon
>>> assigner = ParamAssigner(params).from_dict({
...     'lr': 0.001,
...     'model': {'hidden_size': 256}
... })
```

<a id="module-tessara.handling.binder"></a>

<a id="binder"></a>

## Binder

Parameter binding to function signatures.

<a id="tessara.handling.binder.ParamBinder"></a>

### *class* tessara.handling.binder.ParamBinder(params)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Bind parameters to a function signature.

* **Parameters:**
  **params** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet)) – Parameters to bind to a function signature.

<a id="tessara.handling.binder.ParamBinder.query"></a>

#### query(func)

Query the parameters based on a function signature.

* **Parameters:**
  **func** (*Callable*) – Function to inspect.
* **Returns:**
  **bound_args** – Bound arguments of the function.
* **Return type:**
  [inspect.BoundArguments](https://docs.python.org/3/library/inspect.html#inspect.BoundArguments)

### Notes

The query is performed by filtering the parameters based on the function signature. Only the
parameters that match the function signature will be included in the bound arguments.

> **See also**
>
> [`inspect.signature`](https://docs.python.org/3/library/inspect.html#inspect.signature)
> : Get the signature of a callable object.
>
> [`inspect.BoundArguments`](https://docs.python.org/3/library/inspect.html#inspect.BoundArguments)
> : Object representing the bound arguments of a function.

### Examples

```pycon
>>> def foo(a, b, c=42):
...     pass
>>> params = ParameterSet(a=Param(default=1), b=Param(default=2))
>>> binder = ParamBinder(params)
>>> bound_args = binder.query(foo)
>>> bound_args.arguments
{'a': 1, 'b': 2}
```

<a id="tessara.handling.binder.ParamBinder.call"></a>

#### call(func)

Call a function with the parameters matching its signature.

* **Parameters:**
  **func** (*Callable*) – Function to call.
* **Returns:**
  **result** – Result of the function call.
* **Return type:**
  Any

### Examples

```pycon
>>> def foo(a, b, c=42):
...     return a + b + c
>>> params = ParameterSet(a=Param(default=1), b=Param(default=2))
>>> binder = ParamBinder(params)
>>> result = binder.call(foo)
>>> result
45
```

<a id="module-tessara.handling.composer"></a>

<a id="composer"></a>

## Composer

Parameter set composition and merging.

<a id="tessara.handling.composer.ParamComposer"></a>

### *class* tessara.handling.composer.ParamComposer(\*args, \*\*kwargs)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Merge a set of ParameterSets into a single ParameterSet.

* **Parameters:**
  * **\*args** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet)) – ParameterSets to compose, in the order of precedence. Since no name is provided, the
    default names will be the indices of the sets in the list.
  * **\*\*kwargs** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet)) – ParameterSets to compose, identified by a unique name.
* **Raises:**
  * [**TypeError**](https://docs.python.org/3/library/exceptions.html#TypeError) – If the values are not ParameterSet instances.
  * [**ValueError**](https://docs.python.org/3/library/exceptions.html#ValueError) – If the names of the parameter sets are not unique.

<a id="tessara.handling.composer.ParamComposer.set_precedence"></a>

#### set_precedence(precedence)

Set the order of precedence for the parameters.

* **Parameters:**
  **precedence** (*List* *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *]*) – Order of precedence for the parameters (by name).
* **Raises:**
  [**ValueError**](https://docs.python.org/3/library/exceptions.html#ValueError) – If the precedence list does not include all the names of the parameter sets.

<a id="tessara.handling.composer.ParamComposer.merge"></a>

#### *static* merge(original, other, override=False)

Merge two parameter sets.

* **Parameters:**
  * **original** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet)) – Original parameter set.
  * **other** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet)) – Parameter set to merge with.
  * **override** ([*bool*](https://docs.python.org/3/library/functions.html#bool)) – If True, override existing parameters with new values.
* **Returns:**
  **merged** – Merged parameter set (new object).
* **Return type:**
  [ParameterSet](core.md#tessara.core.parameters.ParameterSet)

### Examples

```pycon
>>> params1 = ParameterSet(param1=Param(default=42))
>>> params2 = ParameterSet(param2=Param(default='foo'))
>>> merged = ParamComposer.merge(params1, params2)
```

<a id="tessara.handling.composer.ParamComposer.compose"></a>

#### compose()

Compose the parameter sets into a single set.

* **Returns:**
  **composed** – Composed parameter set.
* **Return type:**
  [ParameterSet](core.md#tessara.core.parameters.ParameterSet)

### Notes

The `compose` method merges the parameter sets in the order of precedence, from the first
one to the last one. The parameters in the last set will override the ones in the previous
sets.

### Examples

```pycon
>>> params1 = ParameterSet(param1=Param(default=42))
>>> params2 = ParameterSet(param2=Param(default='foo'))
>>> composer = ParamComposer(params1, params2)
>>> composed = composer.compose()
```

<a id="module-tessara.handling.sweeper"></a>

<a id="sweeper"></a>

## Sweeper

Parameter sweep generation over grids.

<a id="tessara.handling.sweeper.ParamSweeper"></a>

### *class* tessara.handling.sweeper.ParamSweeper(params)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Sweep over a grid of parameters with iterator/generator support.

Generates all combinations of parameter values from ParamGrid objects
using cartesian product. Supports both eager (list) and lazy (generator)
evaluation.

* **Parameters:**
  **params** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet)) – Parameter set containing both static Params and ParamGrid objects.

### Notes

- Parameter names are sorted for deterministic ordering across runs.
- The generator pattern allows memory-efficient iteration over large sweeps.
- Each generated ParameterSet is a deep copy with the sweep values applied.

### Examples

```pycon
>>> params = ParameterSet(
...     lr=ParamGrid(Param(), sweep_values=[0.01, 0.001]),
...     epochs=Param(default=100),
... )
>>> sweeper = ParamSweeper(params)
>>> for combo in sweeper:
...     print(combo.to_dict(values_only=True))
{'lr': 0.01, 'epochs': 100}
{'lr': 0.001, 'epochs': 100}
```

<a id="tessara.handling.sweeper.ParamSweeper.generate"></a>

#### generate()

Lazily generate parameter combinations one at a time.

* **Yields:**
  *ParameterSet* – A parameter set with one specific combination of sweep values.
  Static parameters retain their original values.

### Notes

This is memory-efficient for large sweeps as it generates
combinations on-demand rather than storing them all in memory.

<a id="tessara.handling.sweeper.ParamSweeper.generate_all"></a>

#### generate_all()

Eagerly generate all parameter combinations as a list.

* **Returns:**
  All parameter combinations. Equivalent to `list(self.generate())`.
* **Return type:**
  List[[ParameterSet](core.md#tessara.core.parameters.ParameterSet)]

<a id="module-tessara.handling.tree"></a>

<a id="tree"></a>

## Tree

<a id="tessara-handling-tree"></a>

### tessara.handling.tree

Traversal and mutation helpers for ParameterSet trees.

<a id="tessara.handling.tree.ParameterTree"></a>

### *class* tessara.handling.tree.ParameterTree(root)

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Facade for parameter-tree traversal and replacement operations.

<a id="tessara.handling.tree.ParameterTree.root"></a>

#### root *: [ParameterSet](core.md#tessara.core.parameters.ParameterSet)*

Top-level parameter set this tree wraps.

<a id="tessara.handling.tree.ParameterTree.get_node"></a>

#### get_node(path)

Return the node at *path*, raising on missing segments.

* **Parameters:**
  **path** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Dot-separated path to the target node.
* **Returns:**
  The node found at the given path.
* **Return type:**
  ParameterNode
* **Raises:**
  [**UnknownParameterError**](core.md#tessara.core.errors.handling.UnknownParameterError) – If *path* does not resolve to a known parameter.

<a id="tessara.handling.tree.ParameterTree.get_value"></a>

#### get_value(path)

Return the concrete value at *path*.

* **Parameters:**
  **path** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Dot-separated path to the target parameter.
* **Returns:**
  The resolved value of the parameter.
* **Return type:**
  Any
* **Raises:**
  [**UnknownParameterError**](core.md#tessara.core.errors.handling.UnknownParameterError) – If *path* does not resolve to a parameter value.

<a id="tessara.handling.tree.ParameterTree.iter_leaf_nodes"></a>

#### iter_leaf_nodes(params=None, prefix=())

Yield `(dotted_path, node)` pairs for every leaf in the tree.

* **Parameters:**
  * **params** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet) *or* *None* *,* *optional*) – Subtree to iterate. Defaults to `self.root`.
  * **prefix** ([*tuple*](https://docs.python.org/3/library/stdtypes.html#tuple) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,*  *...* *]* *,* *optional*) – Path segments accumulated so far.
* **Yields:**
  *tuple[str, ParameterNode]* – Dotted path and corresponding leaf node.

<a id="tessara.handling.tree.ParameterTree.replace_node"></a>

#### replace_node(path, node)

Replace the node at *path* with *node*.

* **Parameters:**
  * **path** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Dot-separated path to the node to replace.
  * **node** (*ParameterNode*) – New node to insert at the given path.

<a id="tessara.handling.tree.ParameterTree.merge"></a>

#### *static* merge(original, other, override=False)

Merge *other* into a copy of *original*, optionally overriding existing entries.

* **Parameters:**
  * **original** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet)) – Base parameter set to copy.
  * **other** ([*ParameterSet*](core.md#tessara.core.parameters.ParameterSet)) – Parameter set whose entries are merged in.
  * **override** ([*bool*](https://docs.python.org/3/library/functions.html#bool) *,* *optional*) – If `True`, entries in *other* overwrite existing keys. Default is `False`.
* **Returns:**
  A new parameter set containing the merged data.
* **Return type:**
  [ParameterSet](core.md#tessara.core.parameters.ParameterSet)

<a id="module-tessara.handling.config_io"></a>

<a id="configuration-i-o"></a>

## Configuration I/O

<a id="tessara-handling-config-io"></a>

### tessara.handling.config_io

Configuration loading utilities.

<a id="tessara.handling.config_io.load_yaml"></a>

### tessara.handling.config_io.load_yaml(path, prefer_omegaconf=True)

Load configuration from YAML with optional OmegaConf resolution.

* **Parameters:**
  * **path** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *Path*) – Path to the YAML file.
  * **prefer_omegaconf** ([*bool*](https://docs.python.org/3/library/functions.html#bool) *,* *default True*) – If True, try OmegaConf before PyYAML. If False, try PyYAML first.
* **Returns:**
  Loaded configuration.
* **Return type:**
  [dict](https://docs.python.org/3/library/stdtypes.html#dict)
* **Raises:**
  * [**FileNotFoundError**](https://docs.python.org/3/library/exceptions.html#FileNotFoundError) – If the YAML file does not exist at *path*.
  * [**ImportError**](https://docs.python.org/3/library/exceptions.html#ImportError) – If neither `omegaconf` nor `pyyaml` is installed.
