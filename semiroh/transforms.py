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


@dataclass(frozen=True)
class TransformationDefinition:
    """Immutable semantic definition of a state transformation."""

    changes: tuple[EntityChange, ...]
    mappings: tuple[TransformationMapping, ...]

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

    @staticmethod
    def create(
        changes: Mapping[EntityID, Any] | None = None,
        mappings: Mapping[
            EntityID,
            EntityID | tuple[EntityID, ...],
        ] | None = None,
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
        )

    def apply(
        self,
        state: State,
        provenance: Any = None,
        ownership: Mapping[EntityID, Any] | None = None,
    ) -> "TransformResult":
        """Apply the definition and produce an immutable transformation result."""

        values = dict(state.values)

        for change in self.changes:
            values[change.entity] = change.value

        explicitly_mapped: set[EntityID] = set()
        declared_disappearances: set[EntityID] = set()
        mapped_destinations: set[EntityID] = set()

        for mapping in self.mappings:
            source_entity = mapping.source_entity

            if source_entity not in state.values:
                raise KeyError(
                    f"{source_entity.value} is absent from "
                    f"{state.id.value}"
                )

            explicitly_mapped.add(source_entity)
            mapped_destinations.update(mapping.destination_entities)

            if not mapping.destination_entities:
                declared_disappearances.add(source_entity)

        # Presence of an explicitly mapped source is decided by the mappings
        # alone:
        #
        # - a source mapped to zero destinations disappears;
        # - otherwise a source is absent unless it is itself a destination of
        #   some mapping (A -> A, or a swap / shift chain such as A -> B,
        #   B -> A).
        #
        # A value change for a source that the mappings remove has no effect;
        # this generalizes the rule that explicit disappearance takes
        # precedence over a value change.
        removed = (
            explicitly_mapped - mapped_destinations
        ) | declared_disappearances

        for entity in removed:
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

        destination_ownership: Mapping[EntityID, Any]

        if ownership is None:
            # Mappings do not modify ownership. Only edges involving entities
            # absent from the destination are removed.
            destination_ownership = {
                owner: tuple(
                    child
                    for child in children
                    if child in values
                )
                for owner, children in state.ownership.items()
                if owner in values
            }
        else:
            destination_ownership = ownership

        destination = State.create(
            values,
            destination_ownership,
        )

        return TransformResult(
            source=state,
            destination=destination,
            mappings=tuple(normalized_mappings),
            provenance=provenance,
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

    def __post_init__(self) -> None:
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
) -> TransformResult:
    """Produce a state transition with an explicit continuity mapping."""

    definition = TransformationDefinition.create(
        changes=changes,
        mappings=entity_mappings,
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
