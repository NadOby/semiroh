module formal/core_deep

open formal/core_model

/*
 * SHEAR semantic-core deep verification entrypoint.
 *
 * Holds bounded checks that are too expensive for the routine per-push lane.
 * They run in .github/workflows/alloy-deep-verification.yml when the candidate
 * model or this file changes, and on manual dispatch. Scopes are unchanged
 * from the routine lane they came from.
 *
 * CompositionIsBisimulation restates a textbook lemma (bisimulations compose)
 * for the candidate predicate. It is kept as regression protection for
 * core_model.als, not as new semantic evidence.
 *
 * CompositionCase is Alloy verification scaffolding, not a proposed SHEAR
 * semantic primitive.
 */


/* -------------------------------------------------------------------------
 * Verification scaffolding
 * ---------------------------------------------------------------------- */

sig CompositionCase {
    left: one State,
    middle: one State,
    right: one State,
    firstPairs: Rel -> Rel,
    secondPairs: Rel -> Rel
}

fact CompositionCasesAreValid {
    all c: CompositionCase {
        some c.firstPairs
        some c.secondPairs

        bisimulation[
            c.left,
            c.middle,
            c.firstPairs
        ]

        bisimulation[
            c.middle,
            c.right,
            c.secondPairs
        ]
    }
}


/* -------------------------------------------------------------------------
 * Algebraic property
 * ---------------------------------------------------------------------- */

assert CompositionIsBisimulation {
    all c: CompositionCase |
        bisimulation[
            c.left,
            c.right,
            (c.firstPairs).(c.secondPairs)
        ]
}


/* -------------------------------------------------------------------------
 * Non-vacuity witness
 * ---------------------------------------------------------------------- */

pred CompositionWitnessesExist {
    some c: CompositionCase {
        c.left != c.middle
        c.middle != c.right
        c.left != c.right

        some
            source: c.left.rels,
            destination: c.right.rels
        {
            (source -> destination)
                in (c.firstPairs).(c.secondPairs)

            some roleNames[source]
        }
    }
}


/* -------------------------------------------------------------------------
 * Bounded commands
 * ---------------------------------------------------------------------- */

check CompositionIsBisimulation
    for 4
    but 3 State,
        6 Rel,
        2 Role,
        6 RoleUse,
        6 Slot,
        3 Atom,
        0 EntityID,
        0 View,
        exactly 1 CompositionCase
    expect 0

run CompositionWitnessesExist
    for 6
    but exactly 3 State,
        exactly 6 Rel,
        exactly 1 Role,
        exactly 3 RoleUse,
        exactly 3 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 1 CompositionCase
    expect 1
