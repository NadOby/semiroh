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

sig BisimWitness {
    left: one State,
    right: one State,
    pairs: Rel -> Rel
}

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
 * Algebraic properties
 * ---------------------------------------------------------------------- */

assert IdentityIsBisimulation {
    all s: State |
        bisimulation[
            s,
            s,
            (s.rels <: iden :> s.rels)
        ]
}

assert ReverseIsBisimulation {
    all witness: BisimWitness |
        bisimulation[
            witness.right,
            witness.left,
            ~(witness.pairs)
        ]
}

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
 * Negative equality scenarios
 * ---------------------------------------------------------------------- */

pred DifferentAtomsScenario[
    s: State,
    left: Rel,
    right: Rel
] {
    left != right
    left + right in s.rels

    some left.atom
    some right.atom
    left.atom != right.atom

    no roleNames[left]
    no roleNames[right]
}

assert DifferentAtomsAreNotEqual {
    all s: State, disj left, right: s.rels |
        DifferentAtomsScenario[s, left, right]
        implies
        not valueEqual[s, left, s, right]
}

pred DifferentAtomsScenarioExists {
    some s: State, disj left, right: s.rels |
        DifferentAtomsScenario[s, left, right]
}


pred DifferentRoleSetsScenario[
    s: State,
    left: Rel,
    right: Rel
] {
    left != right
    left + right in s.rels

    left.atom = right.atom
    roleNames[left] != roleNames[right]
}

assert DifferentRoleSetsAreNotEqual {
    all s: State, disj left, right: s.rels |
        DifferentRoleSetsScenario[s, left, right]
        implies
        not valueEqual[s, left, s, right]
}

pred DifferentRoleSetsScenarioExists {
    some s: State, disj left, right: s.rels |
        DifferentRoleSetsScenario[s, left, right]
}


pred DifferentTargetOrderScenario[
    s: State,
    left: Rel,
    right: Rel
] {
    left != right
    left + right in s.rels

    left.atom = right.atom
    roleNames[left] = roleNames[right]

    some role: roleNames[left] {
        indicesOf[left, role] = 0 + 1
        indicesOf[right, role] = 0 + 1

        let left0 = targetAt[left, role, 0],
            left1 = targetAt[left, role, 1],
            right0 = targetAt[right, role, 0],
            right1 = targetAt[right, role, 1] |
        {
            left0 != left1
            right0 = left1
            right1 = left0

            some left0.atom
            some left1.atom
            left0.atom != left1.atom

            no roleNames[left0]
            no roleNames[left1]
        }
    }
}

assert DifferentTargetOrderIsNotEqual {
    all s: State, disj left, right: s.rels |
        DifferentTargetOrderScenario[s, left, right]
        implies
        not valueEqual[s, left, s, right]
}

pred DifferentTargetOrderScenarioExists {
    some s: State, disj left, right: s.rels |
        DifferentTargetOrderScenario[s, left, right]
}


pred DifferentTargetMultiplicityScenario[
    s: State,
    left: Rel,
    right: Rel
] {
    left != right
    left + right in s.rels

    left.atom = right.atom
    roleNames[left] = roleNames[right]

    some role: roleNames[left] {
        indicesOf[left, role] != indicesOf[right, role]
    }
}

assert DifferentTargetMultiplicityIsNotEqual {
    all s: State, disj left, right: s.rels |
        DifferentTargetMultiplicityScenario[s, left, right]
        implies
        not valueEqual[s, left, s, right]
}

pred DifferentTargetMultiplicityScenarioExists {
    some s: State, disj left, right: s.rels |
        DifferentTargetMultiplicityScenario[s, left, right]
}


pred PresentEmptyRoleVsAbsentScenario[
    s: State,
    present: Rel,
    absent: Rel
] {
    present != absent
    present + absent in s.rels

    present.atom = absent.atom

    one roleNames[present]
    no roleNames[absent]

    all role: roleNames[present] |
        no slotsOf[present, role]
}

assert PresentEmptyRoleDiffersFromAbsentRole {
    all s: State, disj present, absent: s.rels |
        PresentEmptyRoleVsAbsentScenario[s, present, absent]
        implies
        not valueEqual[s, present, s, absent]
}

pred PresentEmptyRoleVsAbsentScenarioExists {
    some s: State, disj present, absent: s.rels |
        PresentEmptyRoleVsAbsentScenario[s, present, absent]
}


/* -------------------------------------------------------------------------
 * Non-vacuity witnesses
 * ---------------------------------------------------------------------- */

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


/* -------------------------------------------------------------------------
 * Negative equality checks and non-vacuity witnesses
 * ---------------------------------------------------------------------- */

check DifferentAtomsAreNotEqual
    for 3
    but exactly 1 State,
        exactly 2 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        exactly 2 Atom,
        0 EntityID,
        0 View,
        0 BisimWitness,
        0 CompositionCase
    expect 0

run DifferentAtomsScenarioExists
    for 3
    but exactly 1 State,
        exactly 2 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        exactly 2 Atom,
        0 EntityID,
        0 View,
        0 BisimWitness,
        0 CompositionCase
    expect 1


check DifferentRoleSetsAreNotEqual
    for 3
    but exactly 1 State,
        exactly 2 Rel,
        exactly 1 Role,
        exactly 1 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        0 BisimWitness,
        0 CompositionCase
    expect 0

run DifferentRoleSetsScenarioExists
    for 3
    but exactly 1 State,
        exactly 2 Rel,
        exactly 1 Role,
        exactly 1 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        0 BisimWitness,
        0 CompositionCase
    expect 1


check DifferentTargetOrderIsNotEqual
    for 5
    but exactly 1 State,
        exactly 4 Rel,
        exactly 1 Role,
        exactly 2 RoleUse,
        exactly 4 Slot,
        exactly 2 Atom,
        0 EntityID,
        0 View,
        0 BisimWitness,
        0 CompositionCase
    expect 0

run DifferentTargetOrderScenarioExists
    for 5
    but exactly 1 State,
        exactly 4 Rel,
        exactly 1 Role,
        exactly 2 RoleUse,
        exactly 4 Slot,
        exactly 2 Atom,
        0 EntityID,
        0 View,
        0 BisimWitness,
        0 CompositionCase
    expect 1


check DifferentTargetMultiplicityIsNotEqual
    for 4
    but exactly 1 State,
        exactly 3 Rel,
        exactly 1 Role,
        exactly 2 RoleUse,
        exactly 3 Slot,
        exactly 1 Atom,
        0 EntityID,
        0 View,
        0 BisimWitness,
        0 CompositionCase
    expect 0

run DifferentTargetMultiplicityScenarioExists
    for 4
    but exactly 1 State,
        exactly 3 Rel,
        exactly 1 Role,
        exactly 2 RoleUse,
        exactly 3 Slot,
        exactly 1 Atom,
        0 EntityID,
        0 View,
        0 BisimWitness,
        0 CompositionCase
    expect 1


check PresentEmptyRoleDiffersFromAbsentRole
    for 3
    but exactly 1 State,
        exactly 2 Rel,
        exactly 1 Role,
        exactly 1 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        0 BisimWitness,
        0 CompositionCase
    expect 0

run PresentEmptyRoleVsAbsentScenarioExists
    for 3
    but exactly 1 State,
        exactly 2 Rel,
        exactly 1 Role,
        exactly 1 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View,
        0 BisimWitness,
        0 CompositionCase
    expect 1
