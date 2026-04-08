"""
tessara.core.types
==================

Shared type definitions for the tessara framework.

Type Aliases
------------
Targets
    Specification of target parameters by name (list or mapping).
RelationRule
    Tuple of a multi-value rule and its targets.

Classes
-------
RuleProtocol
    Structural protocol for validation rules used by core parameter classes.
MultiValueRuleProtocol
    Structural protocol for multi-value validation rules.
RuleRegistryProtocol
    Structural protocol for rule registries used for serialization.
"""
from collections.abc import Iterable, Mapping
from typing import Any, Dict, List, Protocol, Tuple, TypeAlias, runtime_checkable


# --- Type Aliases ---------------------------------------------------------------------------------

Targets: TypeAlias = Iterable[str] | Mapping[str, str]
"""Specification of target parameters by name: list of strings or mapping of strings."""


# --- Protocols ------------------------------------------------------------------------------------

@runtime_checkable
class RuleProtocol(Protocol):
    """
    Structural protocol for single-value validation rules.

    Any object implementing ``check`` and ``get_error`` can serve as a rule
    for ``Param`` validation, without requiring inheritance from a specific base class.
    """

    def check(self, value: Any) -> bool:
        """Return ``True`` if *value* satisfies the rule.

        Parameters
        ----------
        value : Any
            Value to validate.
        """
        ...

    def get_error(self, value: Any) -> Exception | None:
        """Return an error if *value* fails, otherwise ``None``.

        Parameters
        ----------
        value : Any
            Value to validate.
        """
        ...


@runtime_checkable
class MultiValueRuleProtocol(Protocol):
    """Structural protocol for multi-value (relational) validation rules."""

    def check(self, *args: Any, **kwargs: Any) -> bool:
        """Return ``True`` if the relational constraint holds.

        Parameters
        ----------
        *args : Any
            Positional values to check.
        **kwargs : Any
            Keyword values to check.
        """
        ...

    def get_error(self, *args: Any, **kwargs: Any) -> Exception | None:
        """Return an error if the relation fails, otherwise ``None``.

        Parameters
        ----------
        *args : Any
            Positional values to check.
        **kwargs : Any
            Keyword values to check.
        """
        ...


@runtime_checkable
class RuleRegistryProtocol(Protocol):
    """Structural protocol for rule registries used in serialization."""

    def serialize(self, rule: Any) -> Dict[str, Any]:
        """Serialize a rule instance to a dictionary.

        Parameters
        ----------
        rule : Any
            Rule instance to serialize.
        """
        ...

    def deserialize(self, data: Dict[str, Any]) -> Any:
        """Reconstruct a rule instance from a dictionary.

        Parameters
        ----------
        data : Dict[str, Any]
            Serialized rule payload.
        """
        ...


# Derived type alias using protocols
RelationRule: TypeAlias = Tuple[MultiValueRuleProtocol, Targets]
"""Tuple of a multi-value rule instance and its target specification."""
