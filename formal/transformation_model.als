module formal/transformation_model

open formal/core_model

/*
 * SHEAR candidate transformation / continuity layer.
 *
 * This is experimental and is not a normative language specification.
 *
 * This module models an applied transition:
 *
 *     source State
 *         ->
 *     destination State
 *
 * together with explicitly asserted continuity information.
 *
 * It also defines candidate composition of continuity information across two
 * compatible concrete transitions.
 *
 * It does NOT yet model:
 *
 *     reusable transformation definitions
 *     changes / state construction
 *     transformation application
 *     ownership propagation
 *     reference transfer
 *     provenance
 *     transformation composition
 *
 * Those mechanisms must be derived or added separately rather than being
 * silently implied by this representation.
 */


/* -------------------------------------------------------------------------
 * Transformation
 * ---------------------------------------------------------------------- */

/*
 * Candidate representation of one concrete transition.
 *
 * No intrinsic identity relation between source and destination occurrences
 * is inferred from:
 *
 *     structural equality
 *     position
 *     Atom equality
 *     EntityID bindings
 *
 * Continuity is represented only by explicit ContinuityClaim atoms below.
 *
 * We deliberately do not yet require:
 *
 *     source != destination
 *
 * because equality / identity of complete State values has not yet been
 * formalized in the candidate model. A later state-identity decision may
 * strengthen this.
 */
sig Transformation {
    source: one State,
    destination: one State
}


/* -------------------------------------------------------------------------
 * Explicit continuity
 * ---------------------------------------------------------------------- */

/*
 * Continuity has three semantically distinct states for a source occurrence:
 *
 *     no ContinuityClaim
 *         unknown / no continuity assertion
 *
 *     ContinuityClaim with no destinations
 *         explicit disappearance
 *
 *     ContinuityClaim with one or more destinations
 *         declared continuity
 *
 * A plain Alloy relation:
 *
 *     Rel -> set Rel
 *
 * cannot represent this distinction because both:
 *
 *     no mapping
 *
 * and:
 *
 *     explicit mapping to the empty set
 *
 * would be represented by the absence of tuples.
 *
 * ContinuityClaim therefore exists as representation scaffolding for:
 *
 *     Option(Set DestinationOccurrence)
 *
 * It is not currently proposed as an independent SHEAR semantic primitive.
 *
 * Destination order is intentionally not represented here. Current SHEAR
 * transformation semantics use canonical destination ordering for
 * deterministic representation, but that ordering does not itself denote
 * an additional continuity relationship.
 */
sig ContinuityClaim {
    transformation: one Transformation,
    sourceOccurrence: one Rel,
    destinations: set Rel
}


/*
 * A continuity claim always connects occurrences belonging to the states of
 * its transformation.
 */
fact ContinuityClaimsStayWithinTransformation {
    all claim: ContinuityClaim {
        claim.sourceOccurrence
            in claim.transformation.source.rels

        claim.destinations
            in claim.transformation.destination.rels
    }
}


/*
 * One source occurrence can have at most one explicit continuity claim in a
 * transformation.
 *
 * Cardinality of `destinations` then carries:
 *
 *     0     disappearance
 *     1     unique continuation
 *     >1    split / non-unique continuation
 *
 * Multiple different source occurrences may still name the same destination,
 * so merges and general many-to-one continuity remain representable.
 */
fact AtMostOneClaimPerSource {
    all disj first, second: ContinuityClaim |
        first.transformation = second.transformation
        implies
            first.sourceOccurrence != second.sourceOccurrence
}


/* -------------------------------------------------------------------------
 * Continuity helpers
 * ---------------------------------------------------------------------- */

fun claimFor[
    tx: Transformation,
    occurrence: Rel
]: lone ContinuityClaim {
    {
        claim: ContinuityClaim |
            claim.transformation = tx
            and
            claim.sourceOccurrence = occurrence
    }
}


/*
 * The source has an explicit continuity assertion.
 *
 * This includes explicit disappearance.
 */
pred continuityKnown[
    tx: Transformation,
    occurrence: Rel
] {
    occurrence in tx.source.rels
    one claimFor[tx, occurrence]
}


/*
 * No continuity assertion exists for this source occurrence.
 *
 * Unknown continuity does NOT mean disappearance.
 */
pred continuityUnknown[
    tx: Transformation,
    occurrence: Rel
] {
    occurrence in tx.source.rels
    no claimFor[tx, occurrence]
}


/*
 * Returns explicit destinations.
 *
 * IMPORTANT:
 *
 * An empty result alone does not distinguish:
 *
 *     unknown
 *
 * from:
 *
 *     explicit disappearance
 *
 * Callers must also inspect continuityKnown / continuityUnknown.
 */
fun continuityTargets[
    tx: Transformation,
    occurrence: Rel
]: set Rel {
    claimFor[tx, occurrence].destinations
}


/*
 * Explicitly asserted disappearance:
 *
 *     source -> {}
 */
pred explicitlyDisappears[
    tx: Transformation,
    occurrence: Rel
] {
    continuityKnown[tx, occurrence]

    no continuityTargets[
        tx,
        occurrence
    ]
}


/*
 * One explicitly declared destination.
 */
pred hasUniqueContinuation[
    tx: Transformation,
    occurrence: Rel
] {
    continuityKnown[tx, occurrence]

    one continuityTargets[
        tx,
        occurrence
    ]
}


/*
 * More than one explicitly declared destination.
 */
pred splits[
    tx: Transformation,
    occurrence: Rel
] {
    continuityKnown[tx, occurrence]

    #continuityTargets[
        tx,
        occurrence
    ] > 1
}


/*
 * Explicit pairwise continuity relation.
 */
pred continuesTo[
    tx: Transformation,
    sourceOccurrence: Rel,
    destinationOccurrence: Rel
] {
    sourceOccurrence
        in tx.source.rels

    destinationOccurrence
        in tx.destination.rels

    continuityKnown[
        tx,
        sourceOccurrence
    ]

    destinationOccurrence
        in continuityTargets[
            tx,
            sourceOccurrence
        ]
}


/* -------------------------------------------------------------------------
 * Destination-side helpers
 * ---------------------------------------------------------------------- */

/*
 * All source occurrences explicitly declared as predecessors of a
 * destination occurrence.
 *
 * Multiple predecessors are allowed.
 */
fun declaredPredecessors[
    tx: Transformation,
    destinationOccurrence: Rel
]: set Rel {
    {
        sourceOccurrence: tx.source.rels |
            continuesTo[
                tx,
                sourceOccurrence,
                destinationOccurrence
            ]
    }
}


/*
 * Whether a destination has at least one explicitly declared predecessor.
 *
 * Absence of a declared predecessor does not by itself infer why the
 * destination exists. Creation semantics will be considered when
 * transformation application is modeled.
 */
pred hasDeclaredPredecessor[
    tx: Transformation,
    destinationOccurrence: Rel
] {
    destinationOccurrence
        in tx.destination.rels

    some declaredPredecessors[
        tx,
        destinationOccurrence
    ]
}


/* -------------------------------------------------------------------------
 * Candidate continuity composition
 * ---------------------------------------------------------------------- */

/*
 * Two concrete transitions are directly composable when the destination state
 * of the first is exactly the source state of the second.
 *
 * No structural rebinding or state-equivalence inference is performed here.
 */
pred transformationsCompatible[
    first: Transformation,
    second: Transformation
] {
    first.destination = second.source
}


/*
 * Candidate semantics for whether composed continuity is completely known.
 *
 * For a source occurrence:
 *
 *     first step unknown
 *         -> composed continuity unknown
 *
 *     first step known empty
 *         -> composed continuity known empty
 *
 *     first step known nonempty
 *         -> composed continuity is known only if every intermediate
 *            occurrence has known second-step continuity
 *
 * The universal condition is intentionally vacuous for a known-empty first
 * step, preserving explicit disappearance.
 */
pred composedContinuityKnown[
    first: Transformation,
    second: Transformation,
    src: Rel
] {
    transformationsCompatible[
        first,
        second
    ]

    src in first.source.rels

    continuityKnown[
        first,
        src
    ]

    all mid: continuityTargets[
        first,
        src
    ] |
        continuityKnown[
            second,
            mid
        ]
}


/*
 * Candidate complete destination set after two compatible transitions.
 *
 * This is the union of explicitly known second-step destinations of all
 * first-step destinations.
 *
 * IMPORTANT:
 *
 * This function may return some destinations even when composed continuity is
 * unknown, for example when one split branch is known and another is unknown.
 *
 * Therefore callers must inspect composedContinuityKnown before interpreting
 * this set as complete.
 */
fun composedContinuityTargets[
    first: Transformation,
    second: Transformation,
    src: Rel
]: set Rel {
    {
        dst: second.destination.rels |
            some mid: continuityTargets[
                first,
                src
            ] |
                continuesTo[
                    second,
                    mid,
                    dst
                ]
    }
}


/*
 * Composed continuity is unknown whenever compatible composition exists for
 * the source occurrence but the complete result cannot be established.
 *
 * This includes:
 *
 *     unknown first-step continuity
 *
 * and:
 *
 *     any known first-step destination whose second-step continuity is unknown
 */
pred composedContinuityUnknown[
    first: Transformation,
    second: Transformation,
    src: Rel
] {
    transformationsCompatible[
        first,
        second
    ]

    src in first.source.rels

    not composedContinuityKnown[
        first,
        second,
        src
    ]
}


/*
 * Explicit disappearance after composition.
 *
 * Examples:
 *
 *     A -> {}
 *
 * or:
 *
 *     A -> {B, C}
 *     B -> {}
 *     C -> {}
 *
 * both produce a known empty composed destination set.
 */
pred composedExplicitlyDisappears[
    first: Transformation,
    second: Transformation,
    src: Rel
] {
    composedContinuityKnown[
        first,
        second,
        src
    ]

    no composedContinuityTargets[
        first,
        second,
        src
    ]
}


/*
 * Pairwise composed continuity.
 *
 * This predicate is true only when the complete composed continuity result is
 * known. A destination discovered through one known branch of an otherwise
 * partially unknown split is therefore not exposed as a composed continuation.
 */
pred composedContinuesTo[
    first: Transformation,
    second: Transformation,
    src: Rel,
    dst: Rel
] {
    composedContinuityKnown[
        first,
        second,
        src
    ]

    dst in composedContinuityTargets[
        first,
        second,
        src
    ]
}
