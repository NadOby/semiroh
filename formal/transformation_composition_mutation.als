module formal/transformation_composition_mutation

open formal/transformation_model

/*
 * SHEAR targeted mutation experiment for continuity composition.
 *
 * This file deliberately introduces an incorrect composition rule.
 * It is verification scaffolding only – not candidate semantics.
 *
 * Mutation:
 *
 *     Correct:
 *         every first-step destination must have known second-step
 *         continuity before the composed result is Known.
 *
 *     Mutated:
 *         for a nonempty first-step destination set, only one intermediate
 *         occurrence needs known second-step continuity.
 *
 * This incorrectly promotes partial information:
 *
 *     A -> {B, C}
 *     B -> D
 *     C -> Unknown
 *
 * into a Known composed result.
 *
 * The experiment succeeds only if Alloy finds a counterexample to the
 * safety property under the mutated rule.
 */


/* -------------------------------------------------------------------------
 * Deliberately incorrect composition rule
 * ---------------------------------------------------------------------- */

pred mutatedComposedContinuityKnown[
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

    (
        no continuityTargets[
            first,
            src
        ]

        or

        some mid: continuityTargets[
            first,
            src
        ] |
            continuityKnown[
                second,
                mid
            ]
    )
}


/* -------------------------------------------------------------------------
 * Mutation target
 * ---------------------------------------------------------------------- */

/*
 * This is the same semantic safety requirement exercised by
 * PartialSplitCannotBecomeKnown in transformation_composition.als,
 * evaluated against the deliberately weakened rule.
 *
 * We EXPECT this assertion to be false.
 *
 * Therefore:
 *
 *     SAT counterexample = mutation detected
 *     UNSAT              = mutation survived
 */
assert MutatedPartialSplitCannotBecomeKnown {
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
            not mutatedComposedContinuityKnown[
                first,
                second,
                src
            ]
}


/* -------------------------------------------------------------------------
 * Explicit non-vacuity witness
 * ---------------------------------------------------------------------- */

/*
 * Construct the intended killing scenario explicitly:
 *
 *     src -> {knownMid, unknownMid}
 *     knownMid -> dst
 *     unknownMid -> Unknown
 *
 * The correct rule classifies the composition Unknown.
 * The mutated rule classifies it Known.
 */
pred PartialSplitMutationIsObservable {
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
                    continuityTargets[second, knownMid]
                        = dst

                    continuityUnknown[
                        second,
                        unknownMid
                    ]

                    composedContinuityUnknown[
                        first,
                        second,
                        src
                    ]

                    not composedContinuityKnown[
                        first,
                        second,
                        src
                    ]

                    mutatedComposedContinuityKnown[
                        first,
                        second,
                        src
                    ]
                }
            }
        }
    }
}


/* -------------------------------------------------------------------------
 * Bounded mutation experiment
 * ---------------------------------------------------------------------- */

/*
 * expect 1 is intentional:
 *
 * we require Alloy to find a counterexample to the assertion.
 * That counterexample demonstrates that the verification property kills
 * this mutation.
 */
check MutatedPartialSplitCannotBecomeKnown
    for 5
    but exactly 3 State, exactly 4 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        exactly 2 ContinuityClaim
    expect 1

/*
 * Independent SAT witness that the exact mutated scenario is reachable.
 */
run PartialSplitMutationIsObservable
    for 5
    but exactly 3 State, exactly 4 Rel,
        0 Role, 0 RoleUse, 0 Slot, 0 Atom,
        0 EntityID, 0 View,
        exactly 2 Transformation,
        exactly 2 ContinuityClaim
    expect 1
