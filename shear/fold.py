"""Constant folding as a graph transformation (docs/constant_folding.md).

``fold_constants(state)`` finds the code of a graph-form state that can be
computed without running it and returns a ``TransformResult`` that replaces
it, declaring what it did as continuity:

- a constant subtree such as ``add(lit 1, mul(lit 2, lit 3))`` becomes one
  ``lit`` node. The subtree's root keeps its ``EntityID`` and takes the new
  content, and every node below it is *merged* into it: the mapping sends
  each of them, and the root, to the root;
- ``if`` with a constant condition is replaced by the branch it chooses:
  the ``if`` node and the nodes of the condition are merged into the
  branch's root, and the other branch disappears.

Nothing else moves. Every entity that the pass leaves alone maps to itself,
so its ``EntityID`` and ``VersionID`` stay, and the parents of a replaced
node follow by endpoint continuity. The mapping stays in the result, so a
node of the optimised code can be traced to the nodes it came from
(:func:`sources_of`).

The pass folds only what cannot fail and cannot be observed: ``add``,
``sub``, ``mul`` on ints, ``lt`` on ints, ``eq`` on constants, and ``if`` on
a constant bool. Anything that would raise when run stays as it is, so the
optimised code raises what the original raised.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import canonical_serialize, canonicalize
from .identity import EntityID
from .lang import _decode, _definition_of
from .relations import Relation, relation_of
from .state import State
from .transforms import TransformResult, transform_with_mapping

_UNKNOWN = object()
_ARITHMETIC = {
    "add": lambda left, right: left + right,
    "sub": lambda left, right: left - right,
    "mul": lambda left, right: left * right,
}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


@dataclass(frozen=True)
class _Constant:
    """A subtree that is a constant: its value, the nodes that fold into
    its root, and the nodes that disappear (an ``if``'s other branch).
    """

    value: Any
    merged: frozenset[EntityID]
    dropped: frozenset[EntityID]


class _Function:
    def __init__(self, state: State, function: EntityID) -> None:
        definition = _definition_of(state.values[function])

        self.state = state
        self.owned = state.owned_subtree(function)
        self.root = definition.body
        self.labelled = frozenset(definition.labels.values())
        self.constants: dict[EntityID, _Constant | None] = {}
        self.changes: dict[EntityID, Any] = {}
        self.mappings: dict[EntityID, tuple[EntityID, ...]] = {}

    def node(self, entity: EntityID) -> Relation:
        return relation_of(self.state.values[entity])

    def children(self, entity: EntityID) -> list[EntityID]:
        """The nodes an expression node is made of. A ``call`` or ``read``
        also has an endpoint to a function or a cell; those are not owned by
        the function and are not code below the node.
        """

        return [
            child
            for role in self.node(entity).roles.values()
            for child in (role if isinstance(role, tuple) else (role,))
            if child in self.owned
        ]

    def subtree(self, entity: EntityID) -> frozenset[EntityID]:
        """The node and every node below it."""

        found = {entity}

        for child in self.children(entity):
            found |= self.subtree(child)

        return frozenset(found)

    def constant(self, entity: EntityID) -> _Constant | None:
        if entity not in self.constants:
            self.constants[entity] = self._constant(entity)

        return self.constants[entity]

    def _constant(self, entity: EntityID) -> _Constant | None:
        node = self.node(entity)
        kind = node.kind
        roles = node.roles

        if kind == "lit":
            return _Constant(_decode(node.payload), frozenset(), frozenset())

        if kind in _ARITHMETIC or kind in ("lt", "eq"):
            left = self.constant(roles["left"])
            right = self.constant(roles["right"])

            if left is None or right is None:
                return None

            if kind == "eq":
                value = canonical_serialize(
                    canonicalize(left.value)
                ) == canonical_serialize(canonicalize(right.value))
            elif not (_is_int(left.value) and _is_int(right.value)):
                return None
            elif kind == "lt":
                value = left.value < right.value
            else:
                value = _ARITHMETIC[kind](left.value, right.value)

            return _Constant(
                value,
                left.merged | right.merged
                | {roles["left"], roles["right"]},
                left.dropped | right.dropped,
            )

        if kind == "if":
            chosen = self.chosen(entity)

            if chosen is None:
                return None

            cond, taken, other = chosen
            branch = self.constant(taken)

            if branch is None:
                return None

            return _Constant(
                branch.value,
                cond.merged | branch.merged | {roles["cond"], taken},
                cond.dropped | branch.dropped | self.subtree(other),
            )

        return None

    def chosen(
        self, entity: EntityID
    ) -> tuple[_Constant, EntityID, EntityID] | None:
        """For an ``if`` with a constant bool condition: the condition, the
        branch it takes and the branch it does not.
        """

        roles = self.node(entity).roles
        cond = self.constant(roles["cond"])

        if cond is None or not isinstance(cond.value, bool):
            return None

        if cond.value:
            return cond, roles["then"], roles["else"]

        return cond, roles["else"], roles["then"]

    def merge(self, sources: frozenset[EntityID], into: EntityID) -> None:
        for source in sources:
            self.mappings[source] = (into,)

    def drop(self, dropped: frozenset[EntityID]) -> None:
        for entity in dropped:
            self.mappings[entity] = ()

    def visit(self, entity: EntityID) -> EntityID:
        """Fold what is below ``entity``, and return the node that takes its
        place: itself, or the branch an ``if`` was replaced by (which may
        itself have been replaced), so that no mapping points at a node that
        disappears.
        """

        node = self.node(entity)
        constant = self.constant(entity)

        if constant is not None and node.kind != "lit":
            if not self.labelled & constant.dropped:
                self.changes[entity] = Relation("lit", {}, constant.value)
                self.merge(constant.merged, entity)
                self.drop(constant.dropped)
                return entity

            # A label would disappear; keep the code and look inside.
        elif node.kind == "if":
            chosen = self.chosen(entity)

            if chosen is not None:
                cond, taken, other = chosen
                dropped = self.subtree(other) | cond.dropped

                if not self.labelled & dropped:
                    final = self.visit(taken)
                    self.merge(
                        cond.merged | {entity, node.roles["cond"]}, final
                    )
                    self.drop(dropped)
                    return final

        self.visit_children(entity)
        return entity

    def visit_children(self, entity: EntityID) -> None:
        for child in self.children(entity):
            self.visit(child)


def fold_constants(state: State) -> TransformResult:
    """The transformation that folds the constants of every function of a
    graph-form ``state`` (docs/constant_folding.md). Activate the result as
    any other; it changes nothing when there is nothing to fold.
    """

    changes: dict[EntityID, Any] = {}
    mappings: dict[EntityID, tuple[EntityID, ...]] = {}

    for entity in sorted(state.values, key=lambda item: item.value):
        value = state.values[entity]

        if _definition_of(value) is None:
            continue

        function = _Function(state, entity)
        function.visit(function.root)
        changes.update(function.changes)
        mappings.update(function.mappings)

    for entity in state.values:
        mappings.setdefault(entity, (entity,))

    return transform_with_mapping(state, changes, mappings)


def sources_of(result: TransformResult, entity: EntityID) -> tuple[EntityID, ...]:
    """The nodes of the source state that continue into ``entity``: the node
    itself if it was there, and every node folded into it.
    """

    return tuple(sorted(
        (
            mapping.source_entity
            for mapping in result.mappings
            if entity in mapping.destination_entities
        ),
        key=lambda item: item.value,
    ))
