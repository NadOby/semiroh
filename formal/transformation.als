module formal/transformation

open formal/transformation_model

/*
 * SHEAR transformation / continuity verification entrypoint.
 *
 * The candidate model is defined in:
 *
 *     formal/transformation_model.als
 *
 * This module contains only verification assertions, witness scenarios and
 * bounded commands.
 *
 * It does not add transformation semantics.
 *
 * In particular, this verification layer does NOT yet model:
 *
 *     continuity composition
 *     transformation application
 *     ownership propagation
 *     reference transfer
 *     provenance
 */


/* -------------------------------------------------------------------------
 * Unknown versus explicit disappearance
 * ---------------------------------------------------------------------- */

/*
 * Unknown continuity and explicit disappearance are distinct.
 *
 * Unknown:
 *
 *     no ContinuityClaim
 *
 * Explicit disappearance:
 *
 *     ContinuityClaim exists
 *     destinations = {}
 */
assert UnknownIsNotExplicitDisappearance {
    all
        transformation: Transformation,
        sourceOccurrence: transformation.source.rels
    |
        continuityUnknown[
            transformation,
            sourceOccurrence
        ]
        implies
            not explicitlyDisappears[
                transformation,
                sourceOccurrence
            ]
}


/*
 * Non-vacuity witness for the distinction.
 *
 * Require one transformation containing two source occurrences:
 *
 *     unknownSource
 *         has no continuity claim
 *
 *     disappearingSource
 *         has an explicit empty continuity claim
 *
 * Both states therefore coexist inside the same transition.
 */
pred UnknownAndDisappearanceCanCoexist {
    some transformation: Transformation {
        transformation.source != transformation.destination

        some disj
            unknownSource,
            disappearingSource:
                transformation.source.rels
        {
            continuityUnknown[
                transformation,
                unknownSource
            ]

            explicitlyDisappears[
                transformation,
                disappearingSource
            ]
        }
    }
}


/* -------------------------------------------------------------------------
 * Continuity cardinality witnesses
 * ---------------------------------------------------------------------- */

/*
 * One source occurrence may explicitly disappear:
 *
 *     1 -> 0
 */
pred ExplicitDisappearanceExists {
    some transformation: Transformation {
        transformation.source != transformation.destination

        some sourceOccurrence: transformation.source.rels {
            explicitlyDisappears[
                transformation,
                sourceOccurrence
            ]
        }
    }
}


/*
 * One source occurrence may have exactly one explicit continuation:
 *
 *     1 -> 1
 */
pred UniqueContinuationExists {
    some transformation: Transformation {
        transformation.source != transformation.destination

        some
            sourceOccurrence: transformation.source.rels,
            destinationOccurrence: transformation.destination.rels
        {
            hasUniqueContinuation[
                transformation,
                sourceOccurrence
            ]

            continuesTo[
                transformation,
                sourceOccurrence,
                destinationOccurrence
            ]
        }
    }
}


/*
 * One source occurrence may split into multiple explicit continuations:
 *
 *     1 -> many
 */
pred SplitExists {
    some transformation: Transformation {
        transformation.source != transformation.destination

        some sourceOccurrence: transformation.source.rels {
            splits[
                transformation,
                sourceOccurrence
            ]
        }
    }
}


/*
 * Multiple source occurrences may explicitly continue to the same
 * destination:
 *
 *     many -> 1
 *
 * Each source has exactly one continuation here so this witness isolates
 * many-to-one continuity rather than combining merge and split.
 */
pred MergeExists {
    some transformation: Transformation {
        transformation.source != transformation.destination

        some disj
            firstSource,
            secondSource:
                transformation.source.rels
        {
            some destinationOccurrence:
                transformation.destination.rels
            {
                hasUniqueContinuation[
                    transformation,
                    firstSource
                ]

                hasUniqueContinuation[
                    transformation,
                    secondSource
                ]

                continuesTo[
                    transformation,
                    firstSource,
                    destinationOccurrence
                ]

                continuesTo[
                    transformation,
                    secondSource,
                    destinationOccurrence
                ]
            }
        }
    }
}


/* -------------------------------------------------------------------------
 * Representation invariants
 * ---------------------------------------------------------------------- */

/*
 * A transformation may contain at most one explicit continuity claim for a
 * given source occurrence.
 *
 * This independently checks the externally observable consequence of
 * AtMostOneClaimPerSource.
 */
assert ClaimPerSourceIsFunctional {
    all
        transformation: Transformation,
        sourceOccurrence: transformation.source.rels
    |
        lone {
            claim: ContinuityClaim |
                claim.transformation = transformation
                and
                claim.sourceOccurrence = sourceOccurrence
        }
}


/*
 * Every claim is confined to the source and destination states named by its
 * transformation.
 *
 * This checks the externally visible consequence of
 * ContinuityClaimsStayWithinTransformation.
 */
assert ClaimsStayInsideTheirTransformation {
    all claim: ContinuityClaim {
        claim.sourceOccurrence
            in claim.transformation.source.rels

        claim.destinations
            in claim.transformation.destination.rels
    }
}


/*
 * Non-vacuity witness for multiple independent claims.
 *
 * This ensures the functional-per-source invariant is not checked only in
 * models containing zero or one ContinuityClaim.
 */
pred IndependentClaimsCanCoexist {
    some transformation: Transformation {
        transformation.source != transformation.destination

        some disj
            firstSource,
            secondSource:
                transformation.source.rels
        {
            continuityKnown[
                transformation,
                firstSource
            ]

            continuityKnown[
                transformation,
                secondSource
            ]
        }
    }
}


/* -------------------------------------------------------------------------
 * Structural equality is not continuity
 * ---------------------------------------------------------------------- */

/*
 * Structural/value equality does not create continuity.
 *
 * Require:
 *
 *     two distinct States
 *     one source occurrence
 *     one destination occurrence
 *     equal atomic values
 *     structural value equality
 *     no continuity assertion for the source
 *
 * This is a witness, rather than a universal theorem about inference,
 * because the current transformation model contains no inference mechanism
 * at all. The relevant question at this layer is whether equal values can
 * exist while continuity remains unknown.
 */
pred EqualValuesWithoutContinuity {
    some transformation: Transformation {
        transformation.source != transformation.destination

        some
            sourceOccurrence: transformation.source.rels,
            destinationOccurrence: transformation.destination.rels,
            value: Atom
        {
            sourceOccurrence.atom = value
            destinationOccurrence.atom = value

            valueEqual[
                transformation.source,
                sourceOccurrence,
                transformation.destination,
                destinationOccurrence
            ]

            continuityUnknown[
                transformation,
                sourceOccurrence
            ]
        }
    }
}


/* -------------------------------------------------------------------------
 * Bounded verification commands
 * ---------------------------------------------------------------------- */

/*
 * These scopes deliberately eliminate unrelated semantic structures.
 *
 * The purpose is to test the continuity representation itself before adding
 * continuity composition or transformation application.
 */


/*
 * Command 0
 *
 * Unknown continuity cannot simultaneously be explicit disappearance.
 */
check UnknownIsNotExplicitDisappearance
    for 3
    but exactly 2 State,
        2 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 1 Transformation,
        exactly 1 ContinuityClaim
    expect 0


/*
 * Command 1
 *
 * Unknown and explicit disappearance can coexist in one transformation.
 */
run UnknownAndDisappearanceCanCoexist
    for 3
    but exactly 2 State,
        exactly 2 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 1 Transformation,
        exactly 1 ContinuityClaim
    expect 1


/*
 * Command 2
 *
 * 1 -> 0
 */
run ExplicitDisappearanceExists
    for 3
    but exactly 2 State,
        exactly 1 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 1 Transformation,
        exactly 1 ContinuityClaim
    expect 1


/*
 * Command 3
 *
 * 1 -> 1
 */
run UniqueContinuationExists
    for 3
    but exactly 2 State,
        exactly 2 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 1 Transformation,
        exactly 1 ContinuityClaim
    expect 1


/*
 * Command 4
 *
 * 1 -> many
 */
run SplitExists
    for 4
    but exactly 2 State,
        exactly 3 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 1 Transformation,
        exactly 1 ContinuityClaim
    expect 1


/*
 * Command 5
 *
 * many -> 1
 */
run MergeExists
    for 4
    but exactly 2 State,
        exactly 3 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 1 Transformation,
        exactly 2 ContinuityClaim
    expect 1


/*
 * Command 6
 *
 * Functional claim lookup.
 *
 * Exactly two claims are required so the bounded check does not operate only
 * over a zero- or one-claim universe.
 */
check ClaimPerSourceIsFunctional
    for 4
    but exactly 2 State,
        exactly 3 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 1 Transformation,
        exactly 2 ContinuityClaim
    expect 0


/*
 * Command 7
 *
 * Claims cannot escape their transformation states.
 */
check ClaimsStayInsideTheirTransformation
    for 4
    but exactly 2 State,
        exactly 3 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 1 Transformation,
        exactly 2 ContinuityClaim
    expect 0


/*
 * Command 8
 *
 * Non-vacuity for multiple claims.
 */
run IndependentClaimsCanCoexist
    for 4
    but exactly 2 State,
        exactly 3 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 1 Transformation,
        exactly 2 ContinuityClaim
    expect 1


/*
 * Command 9
 *
 * Equal values can exist while continuity remains unknown.
 */
run EqualValuesWithoutContinuity
    for 3
    but exactly 2 State,
        exactly 2 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        exactly 1 Atom,
        0 EntityID,
        0 View,
        exactly 1 Transformation,
        0 ContinuityClaim
    expect 1
