"""
tessara.handling.tree
=====================

Traversal and mutation helpers for ParameterSet trees.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

from tessara.core.errors.handling import UnknownParameterError
from tessara.core.parameters import Param, ParamGrid, ParameterSet, resolve_path

ParameterNode = Param | ParamGrid | ParameterSet


@dataclass(frozen=True)
class ParameterTree:
    """Facade for parameter-tree traversal and replacement operations."""

    root: ParameterSet

    def get_node(self, path: str) -> ParameterNode:
        if "." not in path:
            if path not in self.root.data:
                raise UnknownParameterError(f"No parameter '{path}' in the ParameterSet.")
            return self.root.data[path]
        node = resolve_path(self.root, path)
        if not isinstance(node, (Param, ParamGrid, ParameterSet)):
            raise UnknownParameterError(f"No parameter '{path}' in the ParameterSet.")
        return node

    def get_value(self, path: str) -> Any:
        node = self.get_node(path)
        if isinstance(node, Param):
            return node.get()
        if isinstance(node, ParamGrid):
            return list(node.iter_values())
        raise UnknownParameterError(f"'{path}' does not resolve to a parameter value.")

    def iter_leaf_nodes(
        self,
        params: ParameterSet | None = None,
        prefix: tuple[str, ...] = (),
    ) -> Iterator[tuple[str, ParameterNode]]:
        current = params or self.root
        for key in sorted(current.data.keys()):
            node = current.data[key]
            path = ".".join(prefix + (key,))
            if isinstance(node, ParameterSet):
                yield from self.iter_leaf_nodes(node, prefix + (key,))
            else:
                yield path, node

    def replace_node(self, path: str, node: ParameterNode) -> None:
        parts = path.split(".")
        if len(parts) == 1:
            self.root.data[parts[0]] = node
            return
        parent = resolve_path(self.root, ".".join(parts[:-1]))
        if not isinstance(parent, ParameterSet):
            raise UnknownParameterError(f"No parameter '{path}' in the ParameterSet.")
        parent.data[parts[-1]] = node

    @staticmethod
    def merge(original: ParameterSet, other: ParameterSet, override: bool = False) -> ParameterSet:
        merged = original.copy()
        for name, node in other.data.items():
            if name not in merged.data or override:
                merged.data[name] = node
        for rule, targets in other.relation_rules:
            merged.relation_rules.append((rule, targets))
        return merged
