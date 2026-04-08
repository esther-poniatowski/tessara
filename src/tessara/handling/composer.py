"""
tessara.handling.composer
=========================

Parameter set composition and merging.

Classes
-------
ParamComposer
    Merge a set of ParameterSets into a single ParameterSet.
"""
from typing import List

from tessara.core.parameters import ParameterSet
from tessara.handling.tree import ParameterTree


class ParamComposer:
    """
    Merge a set of ParameterSets into a single ParameterSet.

    Parameters
    ----------
    *args : ParameterSet
        ParameterSets to compose, in the order of precedence. Since no name is provided, the
        default names will be the indices of the sets in the list.
    **kwargs : ParameterSet
        ParameterSets to compose, identified by a unique name.

    Raises
    ------
    TypeError
        If the values are not ParameterSet instances.
    ValueError
        If the names of the parameter sets are not unique.

    Attributes
    ----------
    params : Dict[str, ParameterSet]
        ParameterSets to compose, each identified by a unique name.
    precedence : List[str]
        Order of precedence for the parameters (by name), which determines the overriding order.
        If A occurs *after* B in the list, then the parameters in A will *override* the ones in B.

    Methods
    -------
    set_precedence(precedence: List[str])
        Set the order of precedence for the parameters.
    merge(original, other, override=False) -> ParameterSet
        (Static method) Merge two parameter sets.
    compose() -> ParameterSet
        Compose the parameter sets into a single set.
    """
    def __init__(self, *args: ParameterSet, **kwargs: ParameterSet) -> None:
        if not all(isinstance(p, ParameterSet) for p in args) or not all(
            isinstance(p, ParameterSet) for p in kwargs.values()
        ):
            raise TypeError("All values must be ParameterSet instances.")
        names_args = [str(i) for i in range(len(args))]
        if len(set(names_args) | set(kwargs.keys())) != len(args) + len(kwargs):
            raise ValueError("Duplicate names in the parameter sets.")
        self.params = {**dict(zip(names_args, args)), **kwargs}
        self.precedence = list(self.params.keys())

    def set_precedence(self, precedence: List[str]) -> None:
        """
        Set the order of precedence for the parameters.

        Arguments
        ---------
        precedence : List[str]
            Order of precedence for the parameters (by name).

        Raises
        ------
        ValueError
            If the precedence list does not include all the names of the parameter sets.
        """
        missing = set(self.params.keys()) - set(precedence)
        if missing:
            raise ValueError(
                "Include all the names of the parameter sets in the precedence order. "
                f"Missing: {missing}"
            )
        self.precedence = precedence

    @staticmethod
    def merge(original: ParameterSet, other: ParameterSet, override: bool = False) -> ParameterSet:
        """
        Merge two parameter sets.

        Arguments
        ---------
        original : ParameterSet
            Original parameter set.
        other : ParameterSet
            Parameter set to merge with.
        override : bool
            If True, override existing parameters with new values.

        Returns
        -------
        merged : ParameterSet
            Merged parameter set (new object).

        Examples
        --------
        >>> params1 = ParameterSet(param1=Param(default=42))
        >>> params2 = ParameterSet(param2=Param(default='foo'))
        >>> merged = ParamComposer.merge(params1, params2)
        """
        return ParameterTree.merge(original, other, override=override)

    def compose(self) -> ParameterSet:
        """
        Compose the parameter sets into a single set.

        Returns
        -------
        composed : ParameterSet
            Composed parameter set.

        Notes
        -----
        The ``compose`` method merges the parameter sets in the order of precedence, from the first
        one to the last one. The parameters in the last set will override the ones in the previous
        sets.

        Examples
        --------
        >>> params1 = ParameterSet(param1=Param(default=42))
        >>> params2 = ParameterSet(param2=Param(default='foo'))
        >>> composer = ParamComposer(params1, params2)
        >>> composed = composer.compose()
        """
        composed = ParameterSet()
        for name in self.precedence:
            composed = self.merge(composed, self.params[name], override=True)
        return composed
