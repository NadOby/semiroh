"""Semantic state transformations and explicit identity mappings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .identity import EntityID, StateID
from .references import (
    AmbiguousEntityMapping,
    CrossStateReference,
    MissingEntityMapping,
    Reference,
    StaleReference,
)
from .ownership import OwnershipError, follow_ownership
from .relations import DanglingRelation, relation_of
from .state import State
from .values import Value, version_id_for


@dataclass(frozen=True)
class EntityChange:
    """Immutable replacement of one entity's semantic value."""

    entity: EntityID
    value: Value

    def __post_init__(self) -> None:
        if self.value.entity != self.entity:
            raise ValueError(
                f"value entity {self.value.entity.value} does not match "
                f"change entity {self.entity.value}"
            )


@dataclass(frozen=True)
class TransformationMapping:
    """Immutable continuity mapping used by a transformation definition."""

    source_entity: EntityID
    destination_entities: tuple[EntityID, ...]

    def __post_init__(self) -> None:
        if len(self.destination_entities) != len(
            set(self.destination_entities)
        ):
            raise ValueError(
                f"duplicate destination entities in mapping from "
                f"{self.source_entity.value}"
            )

        if tuple(sorted(self.destination_entities)) != (
            self.destination_entities
        ):
            raise ValueError(
                f"destination entities for {self.source_entity.value} "
                f"are not canonically ordered"
            )


Conversions = tuple[tuple[EntityID, str], ...]


def _validate_conversions(conversions: Conversions) -> None:
    destinations = tuple(
        destination
        for destination, _ in conversions
    )

    if len(destinations) != len(set(destinations)):
        raise ValueError(
            "multiple conversions for the same destination entity"
        )

    if destinations != tuple(sorted(destinations)):
        raise ValueError(
            "conversions are not canonically ordered"
        )

    for destination, name in conversions:
        if not isinstance(destination, EntityID):
            raise TypeError(
                "conversion destination must be an EntityID"
            )

        if not isinstance(name, str) or not name:
            raise TypeError(
                "conversion name must be a non-empty string"
            )


Placements = tuple[tuple[EntityID, EntityID], ...]


def _validate_placements(placements: Placements) -> None:
    placed_entities = tuple(
        placed
        for placed, _ in placements
    )

    if len(placed_entities) != len(set(placed_entities)):
        raise ValueError(
            "multiple placements for the same entity"
        )

    if placed_entities != tuple(sorted(placed_entities)):
        raise ValueError(
            "placements are not canonically ordered"
        )

    for placed, owner in placements:
        if not isinstance(placed, EntityID):
            raise TypeError(
                "placement entity must be an EntityID"
            )

        if not isinstance(owner, EntityID):
            raise TypeError(
                "placement owner must be an EntityID"
            )


def _cascaded_disappearances(
    ownership: Mapping[EntityID, tuple[EntityID, ...]],
    mappings: Mapping[EntityID, tuple[EntityID, ...]],
) -> frozenset[EntityID]:
    """Entities that disappear because an ended owner's subtree ends with it.

    ownership_model.md section 7 / transformation_model.md section 13: when
    a mapping ends an owner (maps it to zero destinations), every entity in
    its owned subtree, computed from the source ownership, that the
    mappings do not name as a source or a destination disappears too,
    recursively. The cascade does not descend past a named entity: a named
    descendant keeps what its own mapping says (section 9/10 there).
    """

    named: set[EntityID] = set(mappings)

    for destinations in mappings.values():
        named.update(destinations)

    stack = [
        child
        for source, destinations in mappings.items()
        if not destinations
        for child in ownership.get(source, ())
    ]

    cascaded: set[EntityID] = set()

    while stack:
        entity = stack.pop()

        if entity in named or entity in cascaded:
            continue

        cascaded.add(entity)
        stack.extend(ownership.get(entity, ()))

    return frozenset(cascaded)


@dataclass(frozen=True)
class TransformationDefinition:
    """Immutable semantic definition of a state transformation.

    ``conversions`` name, per destination cell, the converter that produces
    that cell's content from the content of the cells mapped into it when the
    result is activated. They are provisional (activation_model.md section 4)
    and refer to executable converters by name, so the definition stays pure
    data.

    ``placements`` declare, per created entity, the owner it is placed under
    (ownership_model.md section 10): ``created entity -> owner``. A placed
    entity must not be a mapping destination; the rest of what makes it
    "created" (absent from the source, present in the destination) can only
    be checked once a source state is known, so `apply` checks it.
    """

    changes: tuple[EntityChange, ...]
    mappings: tuple[TransformationMapping, ...]
    conversions: Conversions = ()
    placements: Placements = ()

    def __post_init__(self) -> None:
        change_entities = tuple(
            change.entity
            for change in self.changes
        )

        if len(change_entities) != len(set(change_entities)):
            raise ValueError(
                "multiple changes for the same entity"
            )

        if change_entities != tuple(sorted(change_entities)):
            raise ValueError(
                "changes are not canonically ordered"
            )

        mapping_entities = tuple(
            mapping.source_entity
            for mapping in self.mappings
        )

        if len(mapping_entities) != len(set(mapping_entities)):
            raise ValueError(
                "multiple mappings for the same source entity"
            )

        if mapping_entities != tuple(sorted(mapping_entities)):
            raise ValueError(
                "mappings are not canonically ordered"
            )

        _validate_conversions(self.conversions)
        _validate_placements(self.placements)

        mapped_destinations = {
            destination
            for mapping in self.mappings
            for destination in mapping.destination_entities
        }

        placed_destinations = sorted(
            placed
            for placed, _ in self.placements
            if placed in mapped_destinations
        )

        if placed_destinations:
            raise OwnershipError(
                f"placement target(s) "
                f"{', '.join(entity.value for entity in placed_destinations)} "
                f"are mapping destinations, not created entities"
            )

        contradictory = sorted(
            set(change_entities) & self.removed_entities
        )

        if contradictory:
            raise ValueError(
                f"definition changes "
                f"{', '.join(entity.value for entity in contradictory)} "
                f"and also removes it through its mappings"
            )

    @property
    def removed_entities(self) -> frozenset[EntityID]:
        """Source entities the mappings remove from the destination.

        A source mapped to zero destinations disappears. Any other mapped
        source is absent unless it is itself a destination of some mapping
        (``A -> A``, or a swap or shift such as ``A -> B``, ``B -> A``).
        """

        mapped = {
            mapping.source_entity
            for mapping in self.mappings
        }
        destinations = {
            destination
            for mapping in self.mappings
            for destination in mapping.destination_entities
        }
        disappearing = {
            mapping.source_entity
            for mapping in self.mappings
            if not mapping.destination_entities
        }

        return frozenset((mapped - destinations) | disappearing)

    @staticmethod
    def create(
        changes: Mapping[EntityID, Any] | None = None,
        mappings: Mapping[
            EntityID,
            EntityID | tuple[EntityID, ...],
        ] | None = None,
        conversions: Mapping[EntityID, str] | None = None,
        placements: Mapping[EntityID, EntityID] | None = None,
    ) -> "TransformationDefinition":
        """Create an immutable transformation definition."""

        normalized_changes = tuple(
            sorted(
                (
                    EntityChange(
                        entity=entity,
                        value=Value(entity, content),
                    )
                    for entity, content in (changes or {}).items()
                ),
                key=lambda change: change.entity,
            )
        )

        normalized_mappings = tuple(
            sorted(
                (
                    TransformationMapping(
                        source_entity=source_entity,
                        destination_entities=tuple(
                            sorted(
                                (
                                    (destination_spec,)
                                    if isinstance(
                                        destination_spec,
                                        EntityID,
                                    )
                                    else tuple(destination_spec)
                                )
                            )
                        ),
                    )
                    for source_entity, destination_spec in (
                        mappings or {}
                    ).items()
                ),
                key=lambda mapping: mapping.source_entity,
            )
        )

        return TransformationDefinition(
            changes=normalized_changes,
            mappings=normalized_mappings,
            conversions=tuple(
                sorted(
                    (conversions or {}).items(),
                    key=lambda item: item[0],
                )
            ),
            placements=tuple(
                sorted(
                    (placements or {}).items(),
                    key=lambda item: item[0],
                )
            ),
        )

    def _follow_relation_endpoints(
        self,
        values: dict[EntityID, Value],
    ) -> tuple["RelationRewrite", ...]:
        """Rewrite endpoints of unchanged relations along declared continuity.

        An endpoint whose entity the definition maps follows that mapping,
        even when the entity is still present (a swap or shift). A mapped
        endpoint that disappears or splits cannot be followed; the relation
        must then be changed or removed explicitly. Unmapped endpoints stay
        unchanged. See relation_model.md section 5.
        """

        changed = {change.entity for change in self.changes}
        declared = {
            mapping.source_entity: mapping.destination_entities
            for mapping in self.mappings
        }
        rewrites: list[RelationRewrite] = []

        for entity in sorted(values):
            if entity in changed:
                continue

            relation = relation_of(values[entity])

            if relation is None:
                continue

            replacement: dict[EntityID, EntityID] = {}

            for endpoint in sorted(relation.endpoints):
                if endpoint not in declared:
                    continue

                destinations = declared[endpoint]

                if len(destinations) != 1:
                    outcome = "disappears" if not destinations else "splits"
                    raise DanglingRelation(
                        f"relation {entity.value} points to "
                        f"{endpoint.value}, which {outcome}; change or "
                        f"remove the relation explicitly"
                    )

                replacement[endpoint] = destinations[0]

            moved = tuple(
                (source, target)
                for source, target in sorted(replacement.items())
                if source != target
            )

            if moved:
                values[entity] = Value(
                    entity,
                    relation.with_endpoints(replacement),
                )
                rewrites.append(RelationRewrite(entity, moved))

        return tuple(rewrites)

    def apply(
        self,
        state: State,
        provenance: Any = None,
        ownership: Mapping[EntityID, Any] | None = None,
    ) -> "TransformResult":
        """Apply the definition and produce an immutable transformation result."""

        if self.placements and ownership is not None:
            raise ValueError(
                "placements cannot be combined with explicit destination "
                "ownership, which already states the whole relation"
            )

        values = dict(state.values)

        for change in self.changes:
            values[change.entity] = change.value

        mapped_destinations: set[EntityID] = set()
        declared_mappings: dict[EntityID, tuple[EntityID, ...]] = {}

        for mapping in self.mappings:
            if mapping.source_entity not in state.values:
                raise KeyError(
                    f"{mapping.source_entity.value} is absent from "
                    f"{state.id.value}"
                )

            mapped_destinations.update(mapping.destination_entities)
            declared_mappings[mapping.source_entity] = mapping.destination_entities

        # An owner mapped to zero destinations ends its owned subtree: every
        # entity in it that the mappings do not name disappears too, and the
        # cascade does not descend past a named entity (ownership_model.md
        # section 7, transformation_model.md section 13).
        cascaded = _cascaded_disappearances(state.ownership, declared_mappings)

        changed_cascaded = sorted(
            {change.entity for change in self.changes} & cascaded
        )

        if changed_cascaded:
            raise ValueError(
                f"definition changes "
                f"{', '.join(entity.value for entity in changed_cascaded)}, "
                f"which disappears because its owner's subtree ended"
            )

        # Presence of an explicitly mapped source is decided by the mappings
        # alone (removed_entities). A definition that also changes a removed
        # entity is contradictory and was rejected at construction. Cascaded
        # entities disappear the same way.
        for entity in self.removed_entities:
            values.pop(entity, None)

        for entity in cascaded:
            values.pop(entity, None)

        normalized_mappings: list[EntityMapping] = []

        for mapping in self.mappings:
            for destination_entity in mapping.destination_entities:
                if destination_entity not in values:
                    raise KeyError(
                        f"{destination_entity.value} is absent from "
                        f"destination state"
                    )

            normalized_mappings.append(
                EntityMapping(
                    source_state=state.id,
                    source_entity=mapping.source_entity,
                    destination_entities=mapping.destination_entities,
                )
            )

        for entity in cascaded:
            normalized_mappings.append(
                EntityMapping(
                    source_state=state.id,
                    source_entity=entity,
                    destination_entities=(),
                )
            )

        normalized_mappings.sort(key=lambda mapping: mapping.source_entity)

        for destination_entity, _ in self.conversions:
            if destination_entity not in mapped_destinations:
                raise ValueError(
                    f"conversion for {destination_entity.value} does not "
                    f"target a mapping destination"
                )

        relation_rewrites = self._follow_relation_endpoints(values)

        destination_ownership: Mapping[EntityID, Any]

        if ownership is None:
            # Ownership follows declared continuity; no remaining entity
            # changes owner implicitly (transformation_model.md section 13).
            # Cascaded entities are folded in as disappearances so their
            # ownership edges are dropped like any other declared one.
            ownership_mapping = dict(declared_mappings)

            for entity in cascaded:
                ownership_mapping[entity] = ()

            destination_ownership = follow_ownership(
                state.ownership,
                ownership_mapping,
            )
        else:
            destination_ownership = ownership

        if self.placements:
            # ownership is None here (checked above), so destination_ownership
            # is the dict of lists follow_ownership produced; placed edges
            # are appended after the owner's existing children.
            for placed_entity, owner in self.placements:
                if placed_entity in state.values:
                    raise OwnershipError(
                        f"placement target {placed_entity.value} exists in "
                        f"the source state; it is a reparenting, not a "
                        f"creation"
                    )

                if placed_entity not in values:
                    raise OwnershipError(
                        f"placement target {placed_entity.value} is absent "
                        f"from the destination state"
                    )

                if owner not in values:
                    raise OwnershipError(
                        f"owner {owner.value} of placement target "
                        f"{placed_entity.value} is absent from the "
                        f"destination state"
                    )

                destination_ownership.setdefault(owner, []).append(
                    placed_entity
                )

        destination = State.create(
            values,
            destination_ownership,
        )

        return TransformResult(
            source=state,
            destination=destination,
            mappings=tuple(normalized_mappings),
            provenance=provenance,
            conversions=self.conversions,
            relation_rewrites=relation_rewrites,
        )


@dataclass(frozen=True)
class CompositionResult:
    """Immutable result of composing two transformation relations."""

    mappings: tuple[TransformationMapping, ...]
    unknown_sources: frozenset[EntityID]

    def __post_init__(self) -> None:
        mapping_entities = tuple(
            mapping.source_entity
            for mapping in self.mappings
        )

        if len(mapping_entities) != len(set(mapping_entities)):
            raise ValueError(
                "multiple composed mappings for the same source entity"
            )

        if mapping_entities != tuple(sorted(mapping_entities)):
            raise ValueError(
                "composed mappings are not canonically ordered"
            )

        if any(
            mapping.source_entity in self.unknown_sources
            for mapping in self.mappings
        ):
            raise ValueError(
                "a source cannot be both mapped and unknown"
            )

    def mapping_for(
        self,
        source_entity: EntityID,
    ) -> TransformationMapping | None:
        """Return the composed mapping for a source, if one exists."""

        for mapping in self.mappings:
            if mapping.source_entity == source_entity:
                return mapping

        return None

    @property
    def known_sources(self) -> frozenset[EntityID]:
        """Return sources for which composition established a result."""

        return frozenset(
            mapping.source_entity
            for mapping in self.mappings
        )


@dataclass(frozen=True)
class RelationRewrite:
    """Endpoints of one relation rewritten along declared continuity.

    ``endpoints`` lists each rewritten endpoint as ``(before, after)`` in
    canonical order. Recording rewrites makes the relation changes that a
    transformation derives from its mappings explicit in its result
    (relation_model.md section 5).
    """

    relation: EntityID
    endpoints: tuple[tuple[EntityID, EntityID], ...]

    def __post_init__(self) -> None:
        if not self.endpoints:
            raise ValueError("a relation rewrite needs at least one endpoint")

        befores = tuple(before for before, _ in self.endpoints)

        if befores != tuple(sorted(set(befores))):
            raise ValueError(
                "rewritten endpoints must be unique and canonically ordered"
            )

        if any(before == after for before, after in self.endpoints):
            raise ValueError("a rewritten endpoint must change")


@dataclass(frozen=True)
class EntityMapping:
    """Explicit continuity relation from one source entity to destinations."""

    source_state: StateID
    source_entity: EntityID
    destination_entities: tuple[EntityID, ...]


@dataclass(frozen=True)
class TransformResult:
    """Immutable result of a state transformation."""

    source: State
    destination: State
    mappings: tuple[EntityMapping, ...]
    provenance: Any = None
    conversions: Conversions = ()
    relation_rewrites: tuple[RelationRewrite, ...] = ()

    def __post_init__(self) -> None:
        _validate_conversions(self.conversions)
        self._validate_relation_rewrites()

        mapped_destinations = {
            destination
            for mapping in self.mappings
            for destination in mapping.destination_entities
        }

        for destination, _ in self.conversions:
            if destination not in mapped_destinations:
                raise ValueError(
                    f"conversion for {destination.value} does not target a "
                    f"mapping destination"
                )

        seen_sources: set[EntityID] = set()

        for mapping in self.mappings:
            if mapping.source_state != self.source.id:
                raise ValueError(
                    f"mapping source state {mapping.source_state.value} "
                    f"does not match source state {self.source.id.value}"
                )

            if mapping.source_entity not in self.source.values:
                raise ValueError(
                    f"mapping source entity {mapping.source_entity.value} "
                    f"is absent from source state"
                )

            if mapping.source_entity in seen_sources:
                raise ValueError(
                    f"multiple mapping records for "
                    f"{mapping.source_entity.value}"
                )

            seen_sources.add(mapping.source_entity)

            if len(mapping.destination_entities) != len(
                set(mapping.destination_entities)
            ):
                raise ValueError(
                    f"duplicate destination entities in mapping from "
                    f"{mapping.source_entity.value}"
                )

            if tuple(sorted(mapping.destination_entities)) != (
                mapping.destination_entities
            ):
                raise ValueError(
                    f"destination entities for {mapping.source_entity.value} "
                    f"are not canonically ordered"
                )

            for destination_entity in mapping.destination_entities:
                if destination_entity not in self.destination.values:
                    raise ValueError(
                        f"mapping destination entity "
                        f"{destination_entity.value} is absent from "
                        f"destination state"
                    )

        if tuple(
            sorted(
                self.mappings,
                key=lambda mapping: mapping.source_entity,
            )
        ) != self.mappings:
            raise ValueError(
                "entity mappings are not canonically ordered"
            )

    def _validate_relation_rewrites(self) -> None:
        relations = tuple(rewrite.relation for rewrite in self.relation_rewrites)

        if relations != tuple(sorted(set(relations))):
            raise ValueError(
                "relation rewrites must be unique and canonically ordered"
            )

        for rewrite in self.relation_rewrites:
            relation = rewrite.relation

            if not (
                self.source.contains(relation)
                and self.destination.contains(relation)
            ):
                raise ValueError(
                    f"rewritten relation {relation.value} must be present "
                    f"in the source and destination states"
                )

            before = relation_of(self.source.values[relation])
            after = relation_of(self.destination.values[relation])

            if (
                before is None
                or after is None
                or before.with_endpoints(dict(rewrite.endpoints)) != after
            ):
                raise ValueError(
                    f"relation rewrite for {relation.value} does not match "
                    f"the source and destination states"
                )

    def conversion_for(self, destination: EntityID) -> str | None:
        """Return the converter name declared for a destination, if any."""

        for converted, name in self.conversions:
            if converted == destination:
                return name

        return None

    def mapping_for(self, source: EntityID) -> EntityMapping | None:
        """Return the mapping record for a source entity, if any."""

        for mapping in self.mappings:
            if mapping.source_entity == source:
                return mapping

        return None

    def mapped_entities(
        self,
        reference: Reference,
    ) -> tuple[EntityID, ...]:
        """Return all explicit destination entities for a reference."""

        matches = [
            mapping.destination_entities
            for mapping in self.mappings
            if (
                mapping.source_state == reference.state
                and mapping.source_entity == reference.entity
            )
        ]

        if not matches:
            raise MissingEntityMapping(
                f"no explicit mapping from "
                f"{reference.entity.value}@{reference.state.value} "
                f"to {self.destination.id.value}"
            )

        if len(matches) > 1:
            raise ValueError(
                f"multiple mapping records for "
                f"{reference.entity.value}@{reference.state.value}"
            )

        return matches[0]

    def mapped_entity(
        self,
        reference: Reference,
    ) -> EntityID:
        """Return the unique destination entity."""

        destinations = self.mapped_entities(reference)

        if not destinations:
            raise MissingEntityMapping(
                f"entity {reference.entity.value}@{reference.state.value} "
                f"has no destination in {self.destination.id.value}"
            )

        if len(destinations) > 1:
            raise AmbiguousEntityMapping(
                f"entity {reference.entity.value}@{reference.state.value} "
                f"maps to multiple destination entities"
            )

        return destinations[0]


TransformationRelation = TransformationDefinition | CompositionResult


def compose(
    first: TransformationRelation,
    second: TransformationRelation,
) -> CompositionResult:
    """Compose explicit continuity mappings from two transformation relations.

    Only explicit mappings compose. If a destination of the first mapping
    has no explicit mapping in the second relation, continuity becomes
    unknown rather than being inferred from preservation.

    An already-unknown source remains unknown through later composition.
    Unknown sources of the second relation are considered only when they
    correspond to intermediate entities reached by the first relation.

    Destination entities use set semantics, so duplicate endpoints collapse.

    Only transformation definitions and composition results can be composed.
    Transformation results are rejected: references move through results one
    step at a time (transformation_composition_api.md).
    """

    for relation in (first, second):
        if not isinstance(
            relation,
            (TransformationDefinition, CompositionResult),
        ):
            raise TypeError(
                "compose accepts TransformationDefinition or "
                f"CompositionResult, not {type(relation).__name__}"
            )

    second_mappings = {
        mapping.source_entity: mapping.destination_entities
        for mapping in second.mappings
    }

    second_unknown_sources = (
        second.unknown_sources
        if isinstance(second, CompositionResult)
        else frozenset()
    )

    composed: list[TransformationMapping] = []
    unknown_sources: set[EntityID] = set()

    if isinstance(first, CompositionResult):
        unknown_sources.update(first.unknown_sources)

    for first_mapping in first.mappings:
        source_entity = first_mapping.source_entity
        intermediate_entities = first_mapping.destination_entities

        if not intermediate_entities:
            composed.append(
                TransformationMapping(
                    source_entity=source_entity,
                    destination_entities=(),
                )
            )
            continue

        final_entities: set[EntityID] = set()
        unknown = False

        for intermediate_entity in intermediate_entities:
            if intermediate_entity in second_unknown_sources:
                unknown = True
                continue

            second_destinations = second_mappings.get(
                intermediate_entity
            )

            if second_destinations is None:
                unknown = True
                continue

            final_entities.update(second_destinations)

        if unknown:
            unknown_sources.add(source_entity)
            continue

        composed.append(
            TransformationMapping(
                source_entity=source_entity,
                destination_entities=tuple(
                    sorted(final_entities)
                ),
            )
        )

    return CompositionResult(
        mappings=tuple(
            sorted(
                composed,
                key=lambda mapping: mapping.source_entity,
            )
        ),
        unknown_sources=frozenset(unknown_sources),
    )


def transform(
    state: State,
    changes: Mapping[EntityID, Any],
) -> State:
    """Produce a new immutable state without a transition mapping."""

    return state.with_changes(changes)


def transform_with_mapping(
    state: State,
    changes: Mapping[EntityID, Any],
    entity_mappings: Mapping[
        EntityID,
        EntityID | tuple[EntityID, ...],
    ],
    provenance: Any = None,
    ownership: Mapping[EntityID, Any] | None = None,
    conversions: Mapping[EntityID, str] | None = None,
    placements: Mapping[EntityID, EntityID] | None = None,
) -> TransformResult:
    """Produce a state transition with an explicit continuity mapping."""

    definition = TransformationDefinition.create(
        changes=changes,
        mappings=entity_mappings,
        conversions=conversions,
        placements=placements,
    )

    return definition.apply(
        state,
        provenance=provenance,
        ownership=ownership,
    )


def transfer_reference(
    reference: Reference,
    result: TransformResult,
) -> Reference:
    """Transfer a valid source reference through a uniquely resolving mapping."""

    if reference.state != result.source.id:
        raise CrossStateReference(
            f"reference belongs to {reference.state.value}, "
            f"not {result.source.id.value}"
        )

    try:
        source_value = result.source.values[reference.entity]
    except KeyError as exc:
        raise KeyError(
            f"{reference.entity.value} is absent from "
            f"{result.source.id.value}"
        ) from exc

    actual_source_version = version_id_for(source_value)

    if actual_source_version != reference.version:
        raise StaleReference(
            f"reference expects version {reference.version.value}, "
            f"but source state contains {actual_source_version.value}"
        )

    destination_entity = result.mapped_entity(reference)

    destination = result.destination

    if destination_entity not in destination.values:
        raise KeyError(
            f"{destination_entity.value} is absent from "
            f"{destination.id.value}"
        )

    destination_value = destination.values[destination_entity]

    return Reference(
        state=destination.id,
        entity=destination_entity,
        version=version_id_for(destination_value),
    )


def rebind_reference(
    reference: Reference,
    destination: State,
    destination_entity: EntityID,
) -> Reference:
    """Explicitly bind to a chosen destination entity.

    Rebinding does not preserve conceptual identity and asserts no relation
    to the original reference. The original reference is therefore neither
    validated nor consulted: a stale, cross-state, or untransferable
    reference can be rebound, which is usually why rebinding is needed. It
    is still a parameter so that call sites state what is being replaced.
    """

    if not isinstance(reference, Reference):
        raise TypeError(
            "rebind_reference expects the Reference being replaced, "
            f"not {type(reference).__name__}"
        )

    return destination.reference(destination_entity)


class TransformationConflict(ValueError):
    """Two transformations of one state cannot be combined: they touch a
    common entity, or their combination fails a structural check
    (continuity_inference.md section 5).
    """


def _parents(state: State) -> dict[EntityID, EntityID]:
    return {
        child: owner
        for owner, children in state.ownership.items()
        for child in children
    }


def touched(result: TransformResult) -> frozenset[EntityID]:
    """The entities a result touches (continuity_inference.md section 5):
    those of its source whose value or owner changes, that disappear or that
    map to anything but themselves, and those it creates.
    """

    source, destination = result.source, result.destination
    before, after = _parents(source), _parents(destination)
    found = {
        entity
        for entity, value in source.values.items()
        if destination.values.get(entity) != value
        or before.get(entity) != after.get(entity)
    }
    found.update(
        mapping.source_entity
        for mapping in result.mappings
        if mapping.destination_entities != (mapping.source_entity,)
    )
    found.update(set(destination.values) - set(source.values))

    return frozenset(found)


def _node_name(entity: EntityID, owner: EntityID | None) -> tuple[int, str] | None:
    """``(generation, index)`` of a node named ``<owner>/<generation>.<index>``."""

    if owner is None or not entity.value.startswith(owner.value + "/"):
        return None

    generation, dot, index = entity.value[len(owner.value) + 1:].partition(".")

    if not (dot and generation.isdigit() and index.isdigit()):
        return None

    return int(generation), index


def _renames(result: TransformResult, base: State) -> dict[EntityID, EntityID]:
    """New names for what ``result`` creates under names ``base`` has.

    A node ``<f>/<g>.<i>`` moves, with every node ``result`` created in
    generation ``g`` of ``f``, to the first later generation of ``f`` whose
    names are all free. Any other created entity whose name is taken is a
    conflict.
    """

    created = set(result.destination.values) - set(result.source.values)
    owners = _parents(result.destination)
    groups: dict[tuple[EntityID, int], dict[EntityID, str]] = {}

    for entity in sorted(created & set(base.values)):
        owner = owners.get(entity)
        name = _node_name(entity, owner)

        if owner is None or name is None:
            raise TransformationConflict(
                f"both transformations create {entity.value}"
            )

        groups[(owner, name[0])] = {}

    for entity in sorted(created):
        owner = owners.get(entity)
        name = _node_name(entity, owner)

        if owner is not None and name is not None and (owner, name[0]) in groups:
            groups[(owner, name[0])][entity] = name[1]

    taken = set(base.values) | set(result.destination.values)
    renames: dict[EntityID, EntityID] = {}

    for (owner, generation), members in sorted(groups.items()):
        while True:
            generation += 1
            names = {
                entity: EntityID(f"{owner.value}/{generation}.{index}")
                for entity, index in members.items()
            }

            if taken.isdisjoint(names.values()):
                break

        renames.update(names)
        taken.update(names.values())

    return renames


def rebase(result: TransformResult, onto: TransformResult) -> TransformResult:
    """Re-base ``result`` to start from ``onto.destination``.

    Both must start from the same state, else ``ValueError``. They combine
    only when the entities they touch (:func:`touched`) are disjoint;
    otherwise, or when the combined state fails a structural check (an
    endpoint or an owner that is gone), ``TransformationConflict``. What
    ``result`` creates under a name ``onto`` already created is renamed
    (``_renames``). Constraints are left to activation, as for any result.
    """

    if result.source.id != onto.source.id:
        raise ValueError(
            f"rebase needs two results from one state, not from "
            f"{result.source.id.value} and {onto.source.id.value}"
        )

    source, base = result.source, onto.destination
    renames = _renames(result, base)

    def rename(entity: EntityID) -> EntityID:
        return renames.get(entity, entity)

    overlap = sorted({rename(entity) for entity in touched(result)} & touched(onto))

    if overlap:
        raise TransformationConflict(
            f"both transformations touch "
            f"{', '.join(entity.value for entity in overlap)}"
        )

    changes: dict[EntityID, Any] = {}

    for entity, value in result.destination.values.items():
        if source.values.get(entity) != value:
            relation = relation_of(value)
            changes[rename(entity)] = (
                value.content if relation is None
                else relation.with_endpoints(renames)
            )

    mappings: dict[EntityID, tuple[EntityID, ...]] = {
        entity: (entity,) for entity in base.values if entity not in source.values
    }

    for mapping in result.mappings:
        entity = mapping.source_entity

        if mapping.destination_entities != (entity,) or entity in base.values:
            mappings[entity] = tuple(sorted(map(rename, mapping.destination_entities)))

    parents = _parents(base)
    before, after = _parents(source), _parents(result.destination)

    for entity in set(source.values) | set(result.destination.values):
        if before.get(entity) != after.get(entity):
            parents.pop(entity, None)

            if entity in after:
                parents[rename(entity)] = rename(after[entity])

    ownership: dict[EntityID, list[EntityID]] = {}

    for child, owner in parents.items():
        ownership.setdefault(owner, []).append(child)

    try:
        return TransformationDefinition.create(
            changes,
            mappings,
            {rename(entity): name for entity, name in result.conversions},
        ).apply(base, result.provenance, ownership)
    except (KeyError, ValueError) as exc:
        raise TransformationConflict(
            f"the two transformations do not combine: {exc}"
        ) from exc
