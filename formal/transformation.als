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

assert UnknownIsNotExplicitDisappearance {
    all
        t: Transformation,
        src: t.source.rels
    |
        continuityUnknown[
            t,
            src
        ]
        implies
            not explicitlyDisappears[
                t,
                src
            ]
}


pred UnknownAndDisappearanceCanCoexist {
    some t: Transformation {
        t.source != t.destination

        some disj
            unknownSource,
            disappearingSource:
                t.source.rels
        {
            continuityUnknown[
                t,
                unknownSource
            ]

            explicitlyDisappears[
                t,
                disappearingSource
            ]
        }
    }
}


/* -------------------------------------------------------------------------
 * Continuity cardinality witnesses
 * ---------------------------------------------------------------------- */

pred ExplicitDisappearanceExists {
    some t: Transformation {
        t.source != t.destination

        some src: t.source.rels {
            explicitlyDisappears[
                t,
                src
            ]
        }
    }
}


pred UniqueContinuationExists {
    some t: Transformation {
        t.source != t.destination

        some
            src: t.source.rels,
            dst: t.destination.rels
        {
            hasUniqueContinuation[
                t,
                src
            ]

            continuesTo[
                t,
                src,
                dst
            ]
        }
    }
}


pred SplitExists {
    some t: Transformation {
        t.source != t.destination

        some src: t.source.rels {
            splits[
                t,
                src
            ]
        }
    }
}


pred MergeExists {
    some t: Transformation {
        t.source != t.destination

        some disj
            firstSource,
            secondSource:
                t.source.rels
        {
            some dst: t.destination.rels {
                hasUniqueContinuation[
                    t,
                    firstSource
                ]

                hasUniqueContinuation[
                    t,
                    secondSource
                ]

                continuesTo[
                    t,
                    firstSource,
                    dst
                ]

                continuesTo[
                    t,
                    secondSource,
                    dst
                ]
            }
        }
    }
}


/* -------------------------------------------------------------------------
 * Representation invariants
 * ---------------------------------------------------------------------- */

assert ClaimPerSourceIsFunctional {
    all
        t: Transformation,
        src: t.source.rels
    |
        lone {
            claim: ContinuityClaim |
                claim.transformation = t
                and
                claim.sourceOccurrence = src
        }
}


assert ClaimsStayInsideTheirTransformation {
    all claim: ContinuityClaim {
        claim.sourceOccurrence
            in claim.transformation.source.rels

        claim.destinations
            in claim.transformation.destination.rels
    }
}


pred IndependentClaimsCanCoexist {
    some t: Transformation {
        t.source != t.destination

        some disj
            firstSource,
            secondSource:
                t.source.rels
        {
            continuityKnown[
                t,
                firstSource
            ]

            continuityKnown[
                t,
                secondSource
            ]
        }
    }
}


/* -------------------------------------------------------------------------
 * Structural equality is not continuity
 * ---------------------------------------------------------------------- */

pred EqualValuesWithoutContinuity {
    some t: Transformation {
        t.source != t.destination

        some
            src: t.source.rels,
            dst: t.destination.rels,
            value: Atom
        {
            src.atom = value
            dst.atom = value

            valueEqual[
                t.source,
                src,
                t.destination,
                dst
            ]

            continuityUnknown[
                t,
                src
            ]
        }
    }
}


/* -------------------------------------------------------------------------
 * Bounded verification commands
 * ---------------------------------------------------------------------- */

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
