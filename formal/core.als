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
 * BisimWitness and CompositionCase are Alloy verification scaffolding,
 * not proposed SHEAR semantic primitives.
 */


/* -------------------------------------------------------------------------
 * Bisimulation verification scaffolding
 * ---------------------------------------------------------------------- */

/*
 * A first-order container for an explicit bisimulation witness.
 *
 * The underlying bisimulation predicate is part of the candidate model.
 * This container exists only so Alloy can quantify over explicit witnesses
 * while checking properties such as reversal.
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


/*
 * Verification-specific representation of two compatible bisimulations:
 *
 *     left --firstPairs--> middle --secondPairs--> right
 *
 * This replaces the earlier composition check over two arbitrary
 * BisimWitness atoms plus:
 *
 *     first.right = second.left
 *
 * The earlier representation introduced irrelevant witness-object symmetry
 * and required the solver to search both compatible and incompatible witness
 * pairs.
 *
 * CompositionCase encodes compatibility directly.
 *
 * It does not weaken the property being checked:
 *
 *   - left, middle and right may still be equal or distinct;
 *   - firstPairs and secondPairs are independently arbitrary;
 *   - the pair relations may be equal;
 *   - each relation need only be a nonempty valid bisimulation.
 *
 * Therefore every compatible pair admitted by the previous representation
 * can be represented by a CompositionCase.
 */
sig CompositionCase {
    left: one State,
    middle: one State,
    right: one State,
    firstPairs: Rel -> Rel,
    secondPairs: Rel -> Rel
}


/*
 * The two relations carried by a CompositionCase are valid nonempty
 * bisimulations with their common middle State encoded directly.
 */
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
 * relational composition of two compatible bisimulations is again a
 * bisimulation.
 *
 * Compatibility and validity are supplied by CompositionCasesAreValid.
 *
 * The check therefore searches directly for a counterexample consisting of:
 *
 *     valid first bisimulation
 *     valid second bisimulation
 *     invalid relational composition
 *
 * rather than also searching irrelevant incompatible witness pairs.
 */
assert CompositionIsBisimulation {
    all c: CompositionCase |
        bisimulation[
            c.left,
            c.right,
            (c.firstPairs).(c.secondPairs)
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
 * Non-vacuity witness for the composition search surface.
 *
 * Require a genuine three-state chain and a nonempty relational composition
 * containing a source relation with actual role structure.
 *
 * This directly exercises the same CompositionCase representation used by
 * CompositionIsBisimulation.
 */
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
 * Verification-only signatures that are irrelevant to a command are
 * explicitly scoped to zero.
 *
 * This reduces the SAT search surface without reducing the bounds of the
 * semantic structures actually involved in that property.
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
        2 Atom,
        0 EntityID,
        0 View,
        0 BisimWitness,
        0 CompositionCase
    expect 0


check ReverseIsBisimulation
    for 4
    but 2 State,
        4 Rel,
        2 Role,
        4 RoleUse,
        4 Slot,
        2 Atom,
        0 EntityID,
        0 View,
        exactly 1 BisimWitness,
        0 CompositionCase
    expect 0


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
        0 BisimWitness,
        exactly 1 CompositionCase
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
        exactly 1 View,
        0 BisimWitness,
        0 CompositionCase
    expect 1


run SharingDoesNotForceInequality
    for 5
    but exactly 1 State,
        exactly 5 Rel,
        exactly 1 Role,
        exactly 2 RoleUse,
        exactly 4 Slot,
        exactly 1 Atom,
        0 EntityID,
        0 View,
        0 BisimWitness,
        0 CompositionCase
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
        exactly 1 BisimWitness,
        0 CompositionCase
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
        0 BisimWitness,
        exactly 1 CompositionCase
    expect 1
