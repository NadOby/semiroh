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
        and
        first.sourceOccurrence = second.sourceOccurrence
        implies
            false
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
