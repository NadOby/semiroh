module formal/transformation_composition

open formal/transformation_model

/*
 * SHEAR binary continuity-composition verification.
 *
 * Candidate composition semantics are defined in:
 *
 *     formal/transformation_model.als
 *
 * This module adds only bounded verification scenarios and properties.
 */


/* -------------------------------------------------------------------------
 * Base composition witnesses
 * ---------------------------------------------------------------------- */

pred KnownThenKnownExists {
    some disj first, second: Transformation {
        transformationsCompatible[first, second]

        some
            src: first.source.rels,
            mid: first.destination.rels,
            dst: second.destination.rels
        {
            continuityTargets[first, src] = mid
            continuityKnown[first, src]

            continuityTargets[second, mid] = dst
            continuityKnown[second, mid]

            composedContinuityKnown[first, second, src]
            composedContinuityTargets[first, second, src] = dst
        }
    }
}


pred KnownThenDisappearanceExists {
    some disj first, second: Transformation {
        transformationsCompatible[first, second]

        some
            src: first.source.rels,
            mid: first.destination.rels
        {
            continuityTargets[first, src] = mid
            continuityKnown[first, src]

            explicitlyDisappears[second, mid]

            composedExplicitlyDisappears[first, second, src]
        }
    }
}


pred KnownThenUnknownExists {
    some disj first, second: Transformation {
        transformationsCompatible[first, second]

        some
            src: first.source.rels,
            mid: first.destination.rels
        {
            continuityTargets[first, src] = mid
            continuityKnown[first, src]

            continuityUnknown[second, mid]

            composedContinuityUnknown[first, second, src]
        }
    }
}


pred FirstStepDisappearanceExists {
    some disj first, second: Transformation {
        transformationsCompatible[first, second]

        some src: first.source.rels {
            explicitlyDisappears[first, src]
            composedExplicitlyDisappears[first, second, src]
        }
    }
}


pred FirstStepUnknownExists {
    some disj first, second: Transformation {
        transformationsCompatible[first, second]

        some src: first.source.rels {
            continuityUnknown[first, src]
            composedContinuityUnknown[first, second, src]
        }
    }
}


/* -------------------------------------------------------------------------
 * Split and merge witnesses
 * ---------------------------------------------------------------------- */

pred CompleteSplitCompositionExists {
    some disj first, second: Transformation {
        transformationsCompatible[first, second]

        some src: first.source.rels {
            some disj
                leftMid,
                rightMid:
                    first.destination.rels
            {
                some disj
                    leftDst,
                    rightDst:
                        second.destination.rels
                {
                    continuityKnown[first, src]

                    continuityTargets[first, src]
                        = leftMid + rightMid

                    continuityKnown[second, leftMid]
                    continuityTargets[second, leftMid] = leftDst

                    continuityKnown[second, rightMid]
                    continuityTargets[second, rightMid] = rightDst

                    composedContinuityKnown[
                        first,
                        second,
                        src
                    ]

                    composedContinuityTargets[
                        first,
                        second,
                        src
                    ] = leftDst + rightDst
                }
            }
        }
    }
}


pred SplitWithDisappearingBranchExists {
    some disj first, second: Transformation {
        transformationsCompatible[first, second]

        some src: first.source.rels {
            some disj
                survivingMid,
                disappearingMid:
                    first.destination.rels
            {
                some dst: second.destination.rels {
                    continuityKnown[first, src]

                    continuityTargets[first, src]
                        = survivingMid + disappearingMid

                    continuityKnown[second, survivingMid]
                    continuityTargets[second, survivingMid] = dst

                    explicitlyDisappears[
                        second,
                        disappearingMid
                    ]

                    composedContinuityKnown[
                        first,
                        second,
                        src
                    ]

                    composedContinuityTargets[
                        first,
                        second,
                        src
                    ] = dst
                }
            }
        }
    }
}


pred AllSplitBranchesDisappearExists {
    some disj first, second: Transformation {
        transformationsCompatible[first, second]

        some src: first.source.rels {
            some disj
                leftMid,
                rightMid:
                    first.destination.rels
            {
                continuityKnown[first, src]

                continuityTargets[first, src]
                    = leftMid + rightMid

                explicitlyDisappears[second, leftMid]
                explicitlyDisappears[second, rightMid]

                composedExplicitlyDisappears[
                    first,
                    second,
                    src
                ]
            }
        }
    }
}


pred SplitWithUnknownBranchExists {
    some disj first, second: Transformation {
        transformationsCompatible[first, second]

        some src: first.source.rels {
            some disj
                knownMid,
                unknownMid:
                    first.destination.rels
            {
                some dst: second.destination.rels {
                    continuityKnown[first, src]

                    continuityTargets[first, src]
                        = knownMid + unknownMid

                    continuityKnown[second, knownMid]
                    continuityTargets[second, knownMid] = dst

                    continuityUnknown[second, unknownMid]

                    composedContinuityUnknown[
                        first,
                        second,
                        src
                    ]

                    /*
                     * Partial information is observable through the raw
                     * helper, but not exposed as complete continuity.
                     */
                    composedContinuityTargets[
                        first,
                        second,
                        src
                    ] = dst

                    not composedContinuesTo[
                        first,
                        second,
                        src,
                        dst
                    ]
                }
            }
        }
    }
}


pred MergeAfterSplitExists {
    some disj first, second: Transformation {
        transformationsCompatible[first, second]

        some src: first.source.rels {
            some disj
                leftMid,
                rightMid:
                    first.destination.rels
            {
                some dst: second.destination.rels {
                    continuityKnown[first, src]

                    continuityTargets[first, src]
                        = leftMid + rightMid

                    continuityKnown[second, leftMid]
                    continuityTargets[second, leftMid] = dst

                    continuityKnown[second, rightMid]
                    continuityTargets[second, rightMid] = dst

                    composedContinuityKnown[
                        first,
                        second,
                        src
                    ]

                    composedContinuityTargets[
                        first,
                        second,
                        src
                    ] = dst
                }
            }
        }
    }
}


/* -------------------------------------------------------------------------
 * Negative properties
 * ---------------------------------------------------------------------- */

assert PartialSplitCannotBecomeKnown {
    all
        first, second: Transformation,
        src: first.source.rels
    |
        transformationsCompatible[first, second]
        and
        continuityKnown[first, src]
        and
        some continuityTargets[first, src]
        and
        (
            some mid: continuityTargets[first, src] |
                continuityUnknown[second, mid]
        )
        implies
            not composedContinuityKnown[
                first,
                second,
                src
            ]
}


assert ComposedUnknownIsNotDisappearance {
    all
        first, second: Transformation,
        src: first.source.rels
    |
        composedContinuityUnknown[first, second, src]
        implies
            not composedExplicitlyDisappears[
                first,
                second,
                src
            ]
}


assert IncompatibleTransformationsDoNotCompose {
    all
        first, second: Transformation,
        src: first.source.rels
    |
        not transformationsCompatible[first, second]
        implies {
            not composedContinuityKnown[
                first,
                second,
                src
            ]

            not composedContinuityUnknown[
                first,
                second,
                src
            ]
        }
}


pred IncompatibleTransformationsExist {
    some disj first, second: Transformation {
        not transformationsCompatible[first, second]
        some first.source.rels
    }
}


/* -------------------------------------------------------------------------
 * Model-sanity properties
 * ---------------------------------------------------------------------- */

assert ComposedClassificationIsTotalAndExclusive {
    all
        first, second: Transformation,
        src: first.source.rels
    |
        transformationsCompatible[first, second]
        implies
            (
                composedContinuityKnown[first, second, src]
                iff
                not composedContinuityUnknown[
                    first,
                    second,
                    src
                ]
            )
}


assert KnownComposedTargetsStayInDestination {
    all
        first, second: Transformation,
        src: first.source.rels
    |
        composedContinuityKnown[first, second, src]
        implies
            composedContinuityTargets[
                first,
                second,
                src
            ] in second.destination.rels
}


/* -------------------------------------------------------------------------
 * Equality independence
 * ---------------------------------------------------------------------- */

pred EqualValueDoesNotManufactureComposition {
    some disj first, second: Transformation {
        transformationsCompatible[first, second]

        some
            src: first.source.rels,
            mid: first.destination.rels,
            dst: second.destination.rels,
            value: Atom
        {
            continuityKnown[first, src]
            continuityTargets[first, src] = mid

            mid.atom = value
            dst.atom = value

            valueEqual[
                second.source,
                mid,
                second.destination,
                dst
            ]

            continuityUnknown[second, mid]

            composedContinuityUnknown[
                first,
                second,
                src
            ]

            not composedContinuesTo[
                first,
                second,
                src,
                dst
            ]
        }
    }
}


/* -------------------------------------------------------------------------
 * Bounded commands
 * ---------------------------------------------------------------------- */

run KnownThenKnownExists
    for 4
    but exactly 3 State, exactly 3 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        exactly 2 ContinuityClaim
    expect 1

run KnownThenDisappearanceExists
    for 4
    but exactly 3 State, exactly 2 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        exactly 2 ContinuityClaim
    expect 1

run KnownThenUnknownExists
    for 4
    but exactly 3 State, exactly 2 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        exactly 1 ContinuityClaim
    expect 1

run FirstStepDisappearanceExists
    for 4
    but exactly 3 State, exactly 1 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        exactly 1 ContinuityClaim
    expect 1

run FirstStepUnknownExists
    for 4
    but exactly 3 State, exactly 1 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        0 ContinuityClaim
    expect 1

run CompleteSplitCompositionExists
    for 5
    but exactly 3 State, exactly 5 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        exactly 3 ContinuityClaim
    expect 1

run SplitWithDisappearingBranchExists
    for 5
    but exactly 3 State, exactly 4 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        exactly 3 ContinuityClaim
    expect 1

run AllSplitBranchesDisappearExists
    for 5
    but exactly 3 State, exactly 3 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        exactly 3 ContinuityClaim
    expect 1

run SplitWithUnknownBranchExists
    for 5
    but exactly 3 State, exactly 4 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        exactly 2 ContinuityClaim
    expect 1

run MergeAfterSplitExists
    for 5
    but exactly 3 State, exactly 4 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        exactly 3 ContinuityClaim
    expect 1

check PartialSplitCannotBecomeKnown
    for 5
    but exactly 3 State, 5 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        3 ContinuityClaim
    expect 0

check ComposedUnknownIsNotDisappearance
    for 5
    but exactly 3 State, 5 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        3 ContinuityClaim
    expect 0

check IncompatibleTransformationsDoNotCompose
    for 5
    but exactly 3 State, 4 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        2 ContinuityClaim
    expect 0

run IncompatibleTransformationsExist
    for 4
    but exactly 3 State, exactly 1 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        0 ContinuityClaim
    expect 1

check ComposedClassificationIsTotalAndExclusive
    for 5
    but exactly 3 State, 5 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        3 ContinuityClaim
    expect 0

check KnownComposedTargetsStayInDestination
    for 5
    but exactly 3 State, 5 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        3 ContinuityClaim
    expect 0

run EqualValueDoesNotManufactureComposition
    for 4
    but exactly 3 State, exactly 3 Rel,
        0 Role, 0 RoleUse, 0 Slot,
        exactly 1 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        exactly 1 ContinuityClaim
    expect 1
