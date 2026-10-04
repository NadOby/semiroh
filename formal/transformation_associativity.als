module formal/transformation_associativity

open formal/transformation_model

/*
 * SHEAR continuity-composition associativity verification.
 *
 * Candidate binary composition semantics are defined in:
 *
 *     formal/transformation_model.als
 *
 * This module introduces verification scaffolding for comparing:
 *
 *     (first ; second) ; third
 *
 * with:
 *
 *     first ; (second ; third)
 *
 * No new semantic Transformation object is introduced for either
 * intermediate composition.
 */


/* -------------------------------------------------------------------------
 * Left-associated composition
 *
 * (first ; second) ; third
 * ---------------------------------------------------------------------- */

pred leftAssociatedKnown[
    first: Transformation,
    second: Transformation,
    third: Transformation,
    src: Rel
] {
    transformationsCompatible[first, second]
    transformationsCompatible[second, third]

    composedContinuityKnown[
        first,
        second,
        src
    ]

    all mid:
        composedContinuityTargets[
            first,
            second,
            src
        ]
    |
        continuityKnown[
            third,
            mid
        ]
}


fun leftAssociatedTargets[
    first: Transformation,
    second: Transformation,
    third: Transformation,
    src: Rel
]: set Rel {
    {
        dst: third.destination.rels |
            some mid:
                composedContinuityTargets[
                    first,
                    second,
                    src
                ]
            |
                continuesTo[
                    third,
                    mid,
                    dst
                ]
    }
}


pred leftAssociatedUnknown[
    first: Transformation,
    second: Transformation,
    third: Transformation,
    src: Rel
] {
    transformationsCompatible[first, second]
    transformationsCompatible[second, third]

    not leftAssociatedKnown[
        first,
        second,
        third,
        src
    ]
}


/* -------------------------------------------------------------------------
 * Right-associated composition
 *
 * first ; (second ; third)
 * ---------------------------------------------------------------------- */

pred rightAssociatedKnown[
    first: Transformation,
    second: Transformation,
    third: Transformation,
    src: Rel
] {
    transformationsCompatible[first, second]
    transformationsCompatible[second, third]

    continuityKnown[
        first,
        src
    ]

    all mid:
        continuityTargets[
            first,
            src
        ]
    |
        composedContinuityKnown[
            second,
            third,
            mid
        ]
}


fun rightAssociatedTargets[
    first: Transformation,
    second: Transformation,
    third: Transformation,
    src: Rel
]: set Rel {
    {
        dst: third.destination.rels |
            some mid:
                continuityTargets[
                    first,
                    src
                ]
            |
                composedContinuesTo[
                    second,
                    third,
                    mid,
                    dst
                ]
    }
}


pred rightAssociatedUnknown[
    first: Transformation,
    second: Transformation,
    third: Transformation,
    src: Rel
] {
    transformationsCompatible[first, second]
    transformationsCompatible[second, third]

    not rightAssociatedKnown[
        first,
        second,
        third,
        src
    ]
}


/* -------------------------------------------------------------------------
 * Associativity property
 * ---------------------------------------------------------------------- */

/*
 * Candidate associativity.
 *
 * Under compatible state boundaries, both parenthesizations must agree:
 *
 *     1. whether complete continuity information is known;
 *     2. if known, on the complete destination set.
 *
 * This is a semantic hypothesis under bounded verification.
 */
assert ContinuityCompositionIsAssociative {
    all
        first, second, third: Transformation,
        src: first.source.rels
    |
        transformationsCompatible[first, second]
        and
        transformationsCompatible[second, third]
        implies {
            leftAssociatedKnown[
                first,
                second,
                third,
                src
            ]
            iff
            rightAssociatedKnown[
                first,
                second,
                third,
                src
            ]

            leftAssociatedKnown[
                first,
                second,
                third,
                src
            ]
            implies
                leftAssociatedTargets[
                    first,
                    second,
                    third,
                    src
                ]
                =
                rightAssociatedTargets[
                    first,
                    second,
                    third,
                    src
                ]
        }
}


/* -------------------------------------------------------------------------
 * Non-vacuity witnesses
 * ---------------------------------------------------------------------- */

/*
 * Fully known three-step chain:
 *
 *     src -> mid1 -> mid2 -> dst
 *
 * Both parenthesizations are known and produce dst.
 */
pred KnownChainExists {
    some disj
        first,
        second,
        third:
            Transformation
    {
        transformationsCompatible[first, second]
        transformationsCompatible[second, third]

        some
            src: first.source.rels,
            mid1: first.destination.rels,
            mid2: second.destination.rels,
            dst: third.destination.rels
        {
            continuityKnown[first, src]
            continuityTargets[first, src] = mid1

            continuityKnown[second, mid1]
            continuityTargets[second, mid1] = mid2

            continuityKnown[third, mid2]
            continuityTargets[third, mid2] = dst

            leftAssociatedKnown[
                first,
                second,
                third,
                src
            ]

            rightAssociatedKnown[
                first,
                second,
                third,
                src
            ]

            leftAssociatedTargets[
                first,
                second,
                third,
                src
            ] = dst

            rightAssociatedTargets[
                first,
                second,
                third,
                src
            ] = dst
        }
    }
}


/*
 * Unknown at the first step propagates through both parenthesizations.
 */
pred FirstStepUnknownChainExists {
    some disj
        first,
        second,
        third:
            Transformation
    {
        transformationsCompatible[first, second]
        transformationsCompatible[second, third]

        some src: first.source.rels {
            continuityUnknown[first, src]

            leftAssociatedUnknown[
                first,
                second,
                third,
                src
            ]

            rightAssociatedUnknown[
                first,
                second,
                third,
                src
            ]
        }
    }
}


/*
 * Unknown at the second step propagates through both parenthesizations.
 */
pred SecondStepUnknownChainExists {
    some disj
        first,
        second,
        third:
            Transformation
    {
        transformationsCompatible[first, second]
        transformationsCompatible[second, third]

        some
            src: first.source.rels,
            mid: first.destination.rels
        {
            continuityKnown[first, src]
            continuityTargets[first, src] = mid

            continuityUnknown[second, mid]

            leftAssociatedUnknown[
                first,
                second,
                third,
                src
            ]

            rightAssociatedUnknown[
                first,
                second,
                third,
                src
            ]
        }
    }
}


/*
 * Unknown at the third step propagates through both parenthesizations.
 */
pred ThirdStepUnknownChainExists {
    some disj
        first,
        second,
        third:
            Transformation
    {
        transformationsCompatible[first, second]
        transformationsCompatible[second, third]

        some
            src: first.source.rels,
            mid1: first.destination.rels,
            mid2: second.destination.rels
        {
            continuityKnown[first, src]
            continuityTargets[first, src] = mid1

            continuityKnown[second, mid1]
            continuityTargets[second, mid1] = mid2

            continuityUnknown[third, mid2]

            leftAssociatedUnknown[
                first,
                second,
                third,
                src
            ]

            rightAssociatedUnknown[
                first,
                second,
                third,
                src
            ]
        }
    }
}


/*
 * Split followed by independent known branches and then a merge.
 *
 * This exercises associativity beyond a simple linear chain.
 */
pred SplitMergeChainExists {
    some disj
        first,
        second,
        third:
            Transformation
    {
        transformationsCompatible[first, second]
        transformationsCompatible[second, third]

        some src: first.source.rels {
            some disj
                left1,
                right1:
                    first.destination.rels
            {
                some disj
                    left2,
                    right2:
                        second.destination.rels
                {
                    some dst: third.destination.rels {
                        continuityKnown[first, src]
                        continuityTargets[first, src]
                            = left1 + right1

                        continuityKnown[second, left1]
                        continuityTargets[second, left1] = left2

                        continuityKnown[second, right1]
                        continuityTargets[second, right1] = right2

                        continuityKnown[third, left2]
                        continuityTargets[third, left2] = dst

                        continuityKnown[third, right2]
                        continuityTargets[third, right2] = dst

                        leftAssociatedKnown[
                            first,
                            second,
                            third,
                            src
                        ]

                        rightAssociatedKnown[
                            first,
                            second,
                            third,
                            src
                        ]

                        leftAssociatedTargets[
                            first,
                            second,
                            third,
                            src
                        ] = dst

                        rightAssociatedTargets[
                            first,
                            second,
                            third,
                            src
                        ] = dst
                    }
                }
            }
        }
    }
}


/*
 * Partial information in a split:
 *
 *     src -> {knownBranch, unknownBranch}
 *
 * The known branch continues, but the unknown branch prevents either
 * parenthesization from becoming complete.
 */
pred PartialSplitUnknownChainExists {
    some disj
        first,
        second,
        third:
            Transformation
    {
        transformationsCompatible[first, second]
        transformationsCompatible[second, third]

        some src: first.source.rels {
            some disj
                knownMid,
                unknownMid:
                    first.destination.rels
            {
                some
                    next: second.destination.rels,
                    dst: third.destination.rels
                {
                    continuityKnown[first, src]
                    continuityTargets[first, src]
                        = knownMid + unknownMid

                    continuityKnown[second, knownMid]
                    continuityTargets[second, knownMid] = next

                    continuityUnknown[second, unknownMid]

                    continuityKnown[third, next]
                    continuityTargets[third, next] = dst

                    leftAssociatedUnknown[
                        first,
                        second,
                        third,
                        src
                    ]

                    rightAssociatedUnknown[
                        first,
                        second,
                        third,
                        src
                    ]
                }
            }
        }
    }
}


/* -------------------------------------------------------------------------
 * Classification sanity
 * ---------------------------------------------------------------------- */

assert AssociatedClassificationAgrees {
    all
        first, second, third: Transformation,
        src: first.source.rels
    |
        transformationsCompatible[first, second]
        and
        transformationsCompatible[second, third]
        implies
            (
                leftAssociatedUnknown[
                    first,
                    second,
                    third,
                    src
                ]
                iff
                rightAssociatedUnknown[
                    first,
                    second,
                    third,
                    src
                ]
            )
}


/* -------------------------------------------------------------------------
 * Bounded commands
 * ---------------------------------------------------------------------- */

/*
 * Command 0
 *
 * Main associativity check.
 */
check ContinuityCompositionIsAssociative
    for 6
    but exactly 4 State,
        6 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 3 Transformation,
        5 ContinuityClaim
    expect 0


/*
 * Command 1
 *
 * Non-vacuity – fully known linear chain.
 */
run KnownChainExists
    for 5
    but exactly 4 State,
        exactly 4 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 3 Transformation,
        exactly 3 ContinuityClaim
    expect 1


/*
 * Command 2
 *
 * Non-vacuity – first-step unknown.
 */
run FirstStepUnknownChainExists
    for 5
    but exactly 4 State,
        exactly 1 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 3 Transformation,
        0 ContinuityClaim
    expect 1


/*
 * Command 3
 *
 * Non-vacuity – second-step unknown.
 */
run SecondStepUnknownChainExists
    for 5
    but exactly 4 State,
        exactly 2 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 3 Transformation,
        exactly 1 ContinuityClaim
    expect 1


/*
 * Command 4
 *
 * Non-vacuity – third-step unknown.
 */
run ThirdStepUnknownChainExists
    for 5
    but exactly 4 State,
        exactly 3 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 3 Transformation,
        exactly 2 ContinuityClaim
    expect 1


/*
 * Command 5
 *
 * Non-vacuity – split followed by merge.
 */
run SplitMergeChainExists
    for 6
    but exactly 4 State,
        exactly 6 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 3 Transformation,
        exactly 5 ContinuityClaim
    expect 1


/*
 * Command 6
 *
 * Non-vacuity – partial split remains unknown.
 */
run PartialSplitUnknownChainExists
    for 6
    but exactly 4 State,
        exactly 5 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 3 Transformation,
        exactly 4 ContinuityClaim
    expect 1


/*
 * Command 7
 *
 * Classification sanity. This substantially overlaps the main associativity
 * assertion and is not independent semantic evidence.
 */
check AssociatedClassificationAgrees
    for 6
    but exactly 4 State,
        6 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 3 Transformation,
        5 ContinuityClaim
    expect 0
