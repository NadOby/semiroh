module formal/core

open formal/core_model

/*
 * SHEAR semantic-core verification entrypoint.
 *
 * This module contains verification scaffolding, assertions, witness
 * scenarios and bounded commands for the candidate model defined in:
 *
 *     formal/core_model.als
 *
 * Neither this module nor core_model.als is a normative language
 * specification.
 *
 * BisimWitness is Alloy verification scaffolding, not a proposed SHEAR
 * semantic primitive.
 */


/* -------------------------------------------------------------------------
 * Bisimulation verification scaffolding
 * ---------------------------------------------------------------------- */

/*
 * A first-order container for an explicit bisimulation witness.
 *
 * The underlying bisimulation predicate is part of the candidate model.
 * This container exists only so Alloy can quantify over explicit witnesses
 * while checking algebraic closure properties.
 */
sig BisimWitness {
    left: one State,
    right: one State,
    pairs: Rel -> Rel
}


/*
 * Every BisimWitness atom denotes a nonempty valid bisimulation.
 */
fact BisimWitnessesAreValid {
    all witness: BisimWitness {
        some witness.pairs

        bisimulation[
            witness.left,
            witness.right,
            witness.pairs
        ]
    }
}


/* -------------------------------------------------------------------------
 * Algebraic properties
 * ---------------------------------------------------------------------- */

/*
 * Reflexivity basis:
 *
 * identity on the occurrences of any State is a bisimulation.
 */
assert IdentityIsBisimulation {
    all s: State |
        bisimulation[
            s,
            s,
            (s.rels <: iden :> s.rels)
        ]
}


/*
 * Symmetry basis:
 *
 * transposing a valid bisimulation produces a valid reverse bisimulation.
 */
assert ReverseIsBisimulation {
    all witness: BisimWitness |
        bisimulation[
            witness.right,
            witness.left,
            ~(witness.pairs)
        ]
}


/*
 * Transitivity basis:
 *
 * relational composition of compatible bisimulations is again a
 * bisimulation.
 */
assert CompositionIsBisimulation {
    all first, second: BisimWitness |
        first.right = second.left implies
            bisimulation[
                first.left,
                second.right,
                (first.pairs).(second.pairs)
            ]
}


/* -------------------------------------------------------------------------
 * Intended semantic witness scenarios
 * ---------------------------------------------------------------------- */

/*
 * Entity identity and structural value equality are independent.
 *
 * Two distinct EntityIDs may designate two distinct occurrences whose
 * relational values are structurally equal.
 */
pred DistinctEntitiesCanNameEqualValues {
    some
        v: View,
        disj firstID, secondID: EntityID,
        disj firstRel, secondRel: v.state.rels
    {
        firstID.(v.entities) = firstRel
        secondID.(v.entities) = secondRel

        valueEqual[
            v.state,
            firstRel,
            v.state,
            secondRel
        ]
    }
}


/*
 * Sharing topology alone does not force value inequality.
 *
 * Left:
 *
 *     pair -> [x, x]
 *
 * Right:
 *
 *     pair -> [y, z]
 *
 * where x, y and z are equal nullary values.
 *
 * The parents should be structurally value-equal even though one structure
 * shares a child occurrence and the other duplicates equal occurrences.
 */
pred SharingDoesNotForceInequality {
    some
        s: State,
        disj leftParent, rightParent, shared, copyA, copyB: s.rels,
        role: Role,
        leftUse, rightUse: RoleUse,
        left0, left1, right0, right1: Slot,
        value: Atom
    {
        leftUse.owner = leftParent
        leftUse.name = role

        rightUse.owner = rightParent
        rightUse.name = role

        roleNames[leftParent] = role
        roleNames[rightParent] = role

        left0.use = leftUse
        left0.index = 0
        left0.target = shared

        left1.use = leftUse
        left1.index = 1
        left1.target = shared

        right0.use = rightUse
        right0.index = 0
        right0.target = copyA

        right1.use = rightUse
        right1.index = 1
        right1.target = copyB

        slotsOf[leftParent, role] = left0 + left1
        slotsOf[rightParent, role] = right0 + right1

        shared.atom = value
        copyA.atom = value
        copyB.atom = value

        no roleNames[shared]
        no roleNames[copyA]
        no roleNames[copyB]

        valueEqual[
            s,
            leftParent,
            s,
            rightParent
        ]
    }
}


/* -------------------------------------------------------------------------
 * Non-vacuity witnesses
 * ---------------------------------------------------------------------- */

/*
 * Non-vacuity witness for reversal.
 *
 * This requires a valid BisimWitness between two distinct states and at
 * least one related source relation with an actual role.
 *
 * It therefore exercises structural bisimulation rather than merely
 * demonstrating that two roleless values can be related.
 */
pred ReverseWitnessExists {
    some
        witness: BisimWitness,
        source: witness.left.rels,
        destination: witness.right.rels
    {
        witness.left != witness.right

        (source -> destination) in witness.pairs

        some roleNames[source]
    }
}


/*
 * Non-vacuity witness for composition.
 *
 * The witnesses form a genuine three-state chain:
 *
 *     first.left
 *         ->
 *     first.right = second.left
 *         ->
 *     second.right
 *
 * Their relational composition must contain a pair whose source has an
 * actual role.
 *
 * This establishes that the antecedent used by
 * CompositionIsBisimulation is realizable by nonempty structural
 * bisimulations within the selected bounds.
 */
pred CompositionWitnessesExist {
    some disj first, second: BisimWitness {
        first.right = second.left

        first.left != first.right
        first.right != second.right
        first.left != second.right

        some
            source: first.left.rels,
            destination: second.right.rels
        {
            (source -> destination)
                in (first.pairs).(second.pairs)

            some roleNames[source]
        }
    }
}


/* -------------------------------------------------------------------------
 * Bounded checks
 * ---------------------------------------------------------------------- */

/*
 * Initial scopes are deliberately small.
 *
 * Their purpose is to validate the candidate model and obtain useful
 * bounded evidence before increasing search depth systematically.
 *
 * Large arbitrary scopes create very large SAT encodings without
 * automatically adding a correspondingly clear verification claim.
 *
 * `expect 0` means that no counterexample should exist.
 */

check IdentityIsBisimulation
    for 4
    but exactly 1 State,
        4 Rel,
        2 Role,
        4 RoleUse,
        4 Slot,
        2 Atom
    expect 0


check ReverseIsBisimulation
    for 4
    but 2 State,
        4 Rel,
        2 Role,
        4 RoleUse,
        4 Slot,
        2 Atom,
        exactly 1 BisimWitness
    expect 0


check CompositionIsBisimulation
    for 4
    but 3 State,
        6 Rel,
        2 Role,
        6 RoleUse,
        6 Slot,
        3 Atom,
        exactly 2 BisimWitness
    expect 0


/*
 * `expect 1` means that an intended witness should exist.
 *
 * These commands establish that the bounded model admits the intended
 * distinctions or non-vacuity conditions.
 *
 * They are not proofs of the candidate semantics.
 */

run DistinctEntitiesCanNameEqualValues
    for 3
    but exactly 1 State,
        exactly 2 Rel,
        1 Role,
        2 RoleUse,
        2 Slot,
        exactly 1 Atom,
        exactly 2 EntityID,
        exactly 1 View
    expect 1


run SharingDoesNotForceInequality
    for 5
    but exactly 1 State,
        exactly 5 Rel,
        exactly 1 Role,
        exactly 2 RoleUse,
        exactly 4 Slot,
        exactly 1 Atom
    expect 1


/*
 * Explicit non-vacuity checks.
 *
 * These remain after the original five commands so established command
 * indices remain stable:
 *
 *     0  IdentityIsBisimulation
 *     1  ReverseIsBisimulation
 *     2  CompositionIsBisimulation
 *     3  DistinctEntitiesCanNameEqualValues
 *     4  SharingDoesNotForceInequality
 *     5  ReverseWitnessExists
 *     6  CompositionWitnessesExist
 */

run ReverseWitnessExists
    for 4
    but exactly 2 State,
        exactly 4 Rel,
        exactly 1 Role,
        exactly 2 RoleUse,
        exactly 2 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        exactly 1 BisimWitness
    expect 1


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
        exactly 2 BisimWitness
    expect 1
