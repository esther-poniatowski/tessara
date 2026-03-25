"""
tessara.handling.sweeper
========================

Parameter sweep generation over grids.

Classes
-------
ParamSweeper
    Sweep over a grid of parameters with iterator/generator support.
"""
from itertools import product
from typing import Any, List, Iterator, Generator

from tessara.core.parameters import ParameterSet, ParamGrid, Param
from tessara.handling.tree import ParameterTree


class ParamSweeper:
    """
    Sweep over a grid of parameters with iterator/generator support.

    Generates all combinations of parameter values from ParamGrid objects
    using cartesian product. Supports both eager (list) and lazy (generator)
    evaluation.

    Attributes
    ----------
    params : ParameterSet
        Parameter set containing both static Params and ParamGrid objects.

    Methods
    -------
    generate() -> Generator[ParameterSet, None, None]
        Lazily generate parameter combinations one at a time.
    generate_all() -> List[ParameterSet]
        Eagerly generate all parameter combinations as a list.
    __iter__() -> Iterator[ParameterSet]
        Make the sweeper iterable (uses generate()).
    __len__() -> int
        Return the total number of combinations.

    Examples
    --------
    >>> params = ParameterSet(
    ...     lr=ParamGrid(Param(), sweep_values=[0.01, 0.001]),
    ...     epochs=Param(default=100),
    ... )
    >>> sweeper = ParamSweeper(params)
    >>> for combo in sweeper:
    ...     print(combo.to_dict(values_only=True))
    {'lr': 0.01, 'epochs': 100}
    {'lr': 0.001, 'epochs': 100}

    Notes
    -----
    - Parameter names are sorted for deterministic ordering across runs.
    - The generator pattern allows memory-efficient iteration over large sweeps.
    - Each generated ParameterSet is a deep copy with the sweep values applied.
    """

    def __init__(self, params: ParameterSet) -> None:
        self.params = params
        self._tree = ParameterTree(params)

    def _collect_sweep_params(
        self,
        params: ParameterSet,
        prefix: tuple[str, ...] = (),
    ) -> List[tuple[str, ParamGrid]]:
        """Collect ParamGrid objects with deterministic ordering."""
        items: List[tuple[str, ParamGrid]] = []
        for path, value in self._tree.iter_leaf_nodes(params, prefix):
            if isinstance(value, ParamGrid):
                items.append((path, value))
        return items

    def _set_param_by_path(self, params: ParameterSet, path: str, param: Param) -> None:
        """Set a Param at a dotted path in a nested ParameterSet."""
        ParameterTree(params).replace_node(path, param)

    def generate(self) -> Generator[ParameterSet, None, None]:
        """
        Lazily generate parameter combinations one at a time.

        Yields
        ------
        ParameterSet
            A parameter set with one specific combination of sweep values.
            Static parameters retain their original values.

        Notes
        -----
        This is memory-efficient for large sweeps as it generates
        combinations on-demand rather than storing them all in memory.
        """
        sweep_items = self._collect_sweep_params(self.params)
        if not sweep_items:
            # No sweep parameters -> yield the original set
            yield self.params.copy()
            return

        names = [name for name, _ in sweep_items]
        grids = [grid for _, grid in sweep_items]
        value_lists = [list(grid.iter_values()) for grid in grids]

        for combination in product(*value_lists):
            new_set = self.params.copy()
            for name, value, grid in zip(names, combination, grids):
                param = grid.make_param(value)
                self._set_param_by_path(new_set, name, param)
            yield new_set

    def generate_all(self) -> List[ParameterSet]:
        """
        Eagerly generate all parameter combinations as a list.

        Returns
        -------
        List[ParameterSet]
            All parameter combinations. Equivalent to ``list(self.generate())``.
        """
        return list(self.generate())

    def __iter__(self) -> Iterator[ParameterSet]:
        """Make the sweeper iterable."""
        return self.generate()

    def __len__(self) -> int:
        """
        Return the total number of combinations.

        Uses multiplication to avoid generating all combinations.
        """
        sweep_items = self._collect_sweep_params(self.params)
        if not sweep_items:
            return 1
        count = 1
        for _, grid in sweep_items:
            count *= len(grid.sweep_values)
        return count
