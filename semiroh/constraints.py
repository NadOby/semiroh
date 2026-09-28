"""Constraint results, semantic constraints, and executable evaluators."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Mapping

from .canonical import (
    CanonicalNode,
    SemanticRecord,
    _node,
    canonical_serialize,
    canonicalize,
)


class ConstraintResult(Enum):
    """Three-valued result of constraint evaluation."""

    SATISFIED = "satisfied"
    VIOLATED = "violated"
    UNKNOWN = "unknown"

    @property
    def is_known(self) -> bool:
        """Return whether the result is decisive."""

        return self is not ConstraintResult.UNKNOWN


ConstraintPredicate = Callable[[Any], ConstraintResult]


@dataclass(frozen=True)
class Evaluator:
    """Executable constraint evaluator.

    The predicate is an executable evaluation mechanism. It is not a semantic
    value: its identity is intentionally not inferred from Python callable
    identity, and it cannot appear in program state. Semantic constraints
    refer to evaluators by name through ``External``.
    """

    predicate: ConstraintPredicate
    description: str = ""

    def __post_init__(self) -> None:
        if not callable(self.predicate):
            raise TypeError(
                "constraint predicate must be callable"
            )

        if not isinstance(self.description, str):
            raise TypeError(
                "constraint description must be a string"
            )

    def evaluate(self, subject: Any) -> ConstraintResult:
        """Evaluate the constraint against a subject.

        The predicate always receives canonical content, the same form as
        ``Value.content``, whether it is called directly or through
        ``External``. A subject that cannot be canonicalized is rejected.
        """

        result = self.predicate(canonicalize(subject))

        if not isinstance(result, ConstraintResult):
            raise TypeError(
                "constraint predicate must return ConstraintResult"
            )

        return result


# ---------------------------------------------------------------------------
# Semantic constraints
# ---------------------------------------------------------------------------

KINDS = frozenset({
    "none",
    "bool",
    "int",
    "str",
    "bytes",
    "entity_id",
    "version_id",
    "state_id",
    "tuple",
    "list",
    "map",
    "cell",
    "constraint",
})


def kind_of(content: Any) -> str:
    """Return the semantic kind of a value's canonical content."""

    content = canonicalize(content)

    if content is None:
        return "none"

    if isinstance(content, bool):
        return "bool"

    if isinstance(content, int):
        return "int"

    if isinstance(content, str):
        return "str"

    if isinstance(content, CanonicalNode):
        return str(content[1])

    raise TypeError(
        f"unsupported canonical content: {type(content).__name__}"
    )


@dataclass(frozen=True)
class EvaluationContext:
    """Conditions under which semantic constraints are evaluated.

    ``externals`` maps ``External`` names to executable evaluators.
    ``budget`` limits the number of constraint nodes evaluated; when it is
    exhausted, the remaining evaluation yields ``UNKNOWN``.
    """

    externals: Mapping[str, Evaluator] = field(default_factory=dict)
    budget: int | None = None

    def __post_init__(self) -> None:
        for name, evaluator in self.externals.items():
            if not isinstance(name, str) or not isinstance(
                evaluator,
                Evaluator,
            ):
                raise TypeError(
                    "externals must map names to Evaluator instances"
                )

        if self.budget is not None and (
            isinstance(self.budget, bool)
            or not isinstance(self.budget, int)
            or self.budget < 0
        ):
            raise ValueError("budget must be a non-negative integer")

        object.__setattr__(
            self,
            "externals",
            MappingProxyType(dict(self.externals)),
        )


class _Evaluation:
    def __init__(self, context: EvaluationContext) -> None:
        self.context = context
        self.remaining = context.budget

    def step(self) -> bool:
        if self.remaining is None:
            return True

        if self.remaining == 0:
            return False

        self.remaining -= 1
        return True


class Constraint(SemanticRecord):
    """A constraint represented as a semantic value.

    Semantic constraints have canonical identity, so they can appear in
    program state. Equality and hashing use canonical serialization.
    """

    _name = ""

    def evaluate(
        self,
        subject: Any,
        context: EvaluationContext | None = None,
    ) -> ConstraintResult:
        """Evaluate against a subject, which is canonicalized first."""

        return self._evaluate(
            canonicalize(subject),
            _Evaluation(context or EvaluationContext()),
        )

    def _evaluate(
        self,
        subject: Any,
        evaluation: _Evaluation,
    ) -> ConstraintResult:
        if not evaluation.step():
            return ConstraintResult.UNKNOWN

        return self._check(subject, evaluation)

    def _check(
        self,
        subject: Any,
        evaluation: _Evaluation,
    ) -> ConstraintResult:
        raise NotImplementedError

    def _payload(self) -> tuple[Any, ...]:
        raise NotImplementedError

    def canonical_node(self) -> CanonicalNode:
        return _node("constraint", (self._name, *self._payload()))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Constraint):
            return NotImplemented

        return canonical_serialize(self) == canonical_serialize(other)

    def __hash__(self) -> int:
        return hash(canonical_serialize(self))

    @staticmethod
    def from_content(content: Any) -> "Constraint":
        """Rebuild a semantic constraint from its canonical content."""

        if not (
            isinstance(content, CanonicalNode)
            and content[1] == "constraint"
        ):
            raise ValueError("content is not a semantic constraint")

        name, *payload = content[2]

        if name == "is_kind":
            return IsKind(*payload)

        if name == "int_range":
            return IntRange(*payload)

        if name == "length":
            return Length(*payload)

        if name == "one_of":
            return OneOf(*payload[0])

        if name == "all_of":
            return AllOf(
                *(Constraint.from_content(part) for part in payload[0])
            )

        if name == "any_of":
            return AnyOf(
                *(Constraint.from_content(part) for part in payload[0])
            )

        if name == "not":
            return Not(Constraint.from_content(payload[0]))

        if name == "external":
            return External(*payload)

        raise ValueError(f"unknown semantic constraint: {name}")


def _result(condition: bool) -> ConstraintResult:
    return (
        ConstraintResult.SATISFIED
        if condition
        else ConstraintResult.VIOLATED
    )


def _check_bound(value: Any, name: str) -> None:
    if value is not None and (
        isinstance(value, bool) or not isinstance(value, int)
    ):
        raise TypeError(f"{name} must be an integer or None")


@dataclass(frozen=True, eq=False)
class IsKind(Constraint):
    """The subject has the given semantic kind (``bool`` is not ``int``)."""

    kind: str
    _name = "is_kind"

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown kind: {self.kind!r}")

    def _payload(self) -> tuple[Any, ...]:
        return (self.kind,)

    def _check(self, subject: Any, evaluation: _Evaluation) -> ConstraintResult:
        return _result(kind_of(subject) == self.kind)


@dataclass(frozen=True, eq=False)
class IntRange(Constraint):
    """The subject is an integer within inclusive bounds."""

    min: int | None = None
    max: int | None = None
    _name = "int_range"

    def __post_init__(self) -> None:
        _check_bound(self.min, "min")
        _check_bound(self.max, "max")

        if (
            self.min is not None
            and self.max is not None
            and self.min > self.max
        ):
            raise ValueError("min must not exceed max")

    def _payload(self) -> tuple[Any, ...]:
        return (self.min, self.max)

    def _check(self, subject: Any, evaluation: _Evaluation) -> ConstraintResult:
        if kind_of(subject) != "int":
            return ConstraintResult.VIOLATED

        return _result(
            (self.min is None or subject >= self.min)
            and (self.max is None or subject <= self.max)
        )


@dataclass(frozen=True, eq=False)
class Length(Constraint):
    """The subject's length is within inclusive bounds.

    Length applies to text (code points), bytes, tuples, lists, and maps
    (entries). Other kinds violate the constraint.
    """

    min: int = 0
    max: int | None = None
    _name = "length"

    def __post_init__(self) -> None:
        _check_bound(self.min, "min")
        _check_bound(self.max, "max")

        if self.min is None or self.min < 0:
            raise ValueError("min must be a non-negative integer")

        if self.max is not None and self.min > self.max:
            raise ValueError("min must not exceed max")

    def _payload(self) -> tuple[Any, ...]:
        return (self.min, self.max)

    def _check(self, subject: Any, evaluation: _Evaluation) -> ConstraintResult:
        kind = kind_of(subject)

        if kind == "str":
            length = len(subject)
        elif kind == "bytes":
            length = len(subject[2]) // 2
        elif kind in ("tuple", "list", "map"):
            length = len(subject[2])
        else:
            return ConstraintResult.VIOLATED

        return _result(
            length >= self.min
            and (self.max is None or length <= self.max)
        )


def _set_of_contents(values: tuple[Any, ...]) -> tuple[Any, ...]:
    unique = {
        canonical_serialize(canonical): canonical
        for canonical in (canonicalize(value) for value in values)
    }

    return tuple(unique[key] for key in sorted(unique))


@dataclass(frozen=True, eq=False, init=False)
class OneOf(Constraint):
    """The subject is semantically equal to one of the given values."""

    values: tuple[Any, ...]
    _name = "one_of"

    def __init__(self, *values: Any) -> None:
        object.__setattr__(self, "values", _set_of_contents(values))

    def _payload(self) -> tuple[Any, ...]:
        return (self.values,)

    def _check(self, subject: Any, evaluation: _Evaluation) -> ConstraintResult:
        encoded = canonical_serialize(subject)

        return _result(
            any(canonical_serialize(value) == encoded for value in self.values)
        )


def _set_of_constraints(
    parts: tuple[Constraint, ...],
) -> tuple[Constraint, ...]:
    for part in parts:
        if not isinstance(part, Constraint):
            raise TypeError("components must be semantic constraints")

    unique = {canonical_serialize(part): part for part in parts}

    return tuple(unique[key] for key in sorted(unique))


@dataclass(frozen=True, eq=False, init=False)
class AllOf(Constraint):
    """Conjunction under strong Kleene logic (constraint_model.md §9)."""

    parts: tuple[Constraint, ...]
    _name = "all_of"

    def __init__(self, *parts: Constraint) -> None:
        object.__setattr__(self, "parts", _set_of_constraints(parts))

    def _payload(self) -> tuple[Any, ...]:
        return (tuple(part.canonical_node() for part in self.parts),)

    def _check(self, subject: Any, evaluation: _Evaluation) -> ConstraintResult:
        unknown = False

        for part in self.parts:
            result = part._evaluate(subject, evaluation)

            if result is ConstraintResult.VIOLATED:
                return result

            if result is ConstraintResult.UNKNOWN:
                unknown = True

        return (
            ConstraintResult.UNKNOWN
            if unknown
            else ConstraintResult.SATISFIED
        )


@dataclass(frozen=True, eq=False, init=False)
class AnyOf(Constraint):
    """Disjunction under strong Kleene logic (constraint_model.md §9)."""

    parts: tuple[Constraint, ...]
    _name = "any_of"

    def __init__(self, *parts: Constraint) -> None:
        object.__setattr__(self, "parts", _set_of_constraints(parts))

    def _payload(self) -> tuple[Any, ...]:
        return (tuple(part.canonical_node() for part in self.parts),)

    def _check(self, subject: Any, evaluation: _Evaluation) -> ConstraintResult:
        unknown = False

        for part in self.parts:
            result = part._evaluate(subject, evaluation)

            if result is ConstraintResult.SATISFIED:
                return result

            if result is ConstraintResult.UNKNOWN:
                unknown = True

        return (
            ConstraintResult.UNKNOWN
            if unknown
            else ConstraintResult.VIOLATED
        )


@dataclass(frozen=True, eq=False)
class Not(Constraint):
    """Negation: swaps Satisfied and Violated; Unknown stays Unknown."""

    part: Constraint
    _name = "not"

    def __post_init__(self) -> None:
        if not isinstance(self.part, Constraint):
            raise TypeError("component must be a semantic constraint")

    def _payload(self) -> tuple[Any, ...]:
        return (self.part.canonical_node(),)

    def _check(self, subject: Any, evaluation: _Evaluation) -> ConstraintResult:
        result = self.part._evaluate(subject, evaluation)

        if result is ConstraintResult.SATISFIED:
            return ConstraintResult.VIOLATED

        if result is ConstraintResult.VIOLATED:
            return ConstraintResult.SATISFIED

        return result


@dataclass(frozen=True, eq=False)
class External(Constraint):
    """A named constraint evaluated by an executable evaluator.

    The evaluator is looked up in the evaluation context and receives the
    canonical subject. Without a registered evaluator the result is
    ``UNKNOWN``: the constraint is meaningful, but nothing available can
    establish it.
    """

    name: str
    _name = "external"

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise TypeError("external constraint name must be a non-empty string")

    def _payload(self) -> tuple[Any, ...]:
        return (self.name,)

    def _check(self, subject: Any, evaluation: _Evaluation) -> ConstraintResult:
        evaluator = evaluation.context.externals.get(self.name)

        if evaluator is None:
            return ConstraintResult.UNKNOWN

        return evaluator.evaluate(subject)
