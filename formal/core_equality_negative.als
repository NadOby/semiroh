module formal/core_equality_negative

open formal/core_model

/*
 * SHEAR negative structural-equality verification.
 *
 * These are bounded anti-witnesses for distinctions that the current
 * candidate value-equality semantics is intended to preserve.
 *
 * Each predicate constructs two occurrences differing in exactly the
 * relevant structural dimension and requires valueEqual to reject them.
 *
 * These are verification scenarios, not additional semantic primitives.
 */


/* -------------------------------------------------------------------------
 * Different atomic values
 * ---------------------------------------------------------------------- */

pred DifferentAtomsAreNotEqual {
    some
        s: State,
        disj left, right: s.rels,
        disj leftAtom, rightAtom: Atom
    {
        left.atom = leftAtom
        right.atom = rightAtom

        no roleNames[left]
        no roleNames[right]

        not valueEqual[
            s,
            left,
            s,
            right
        ]
    }
}


/* -------------------------------------------------------------------------
 * Different role sets
 * ---------------------------------------------------------------------- */

pred DifferentRoleSetsAreNotEqual {
    some
        s: State,
        disj left, right: s.rels,
        role: Role,
        use: RoleUse
    {
        no left.atom
        no right.atom

        use.owner = left
        use.name = role

        roleNames[left] = role
        no roleNames[right]

        no slotsOf[left, role]

        not valueEqual[
            s,
            left,
            s,
            right
        ]
    }
}


/* -------------------------------------------------------------------------
 * Different target order
 * ---------------------------------------------------------------------- */

pred DifferentTargetOrderIsNotEqual {
    some
        s: State,
        disj left, right, first, second: s.rels,
        role: Role,
        leftUse, rightUse: RoleUse,
        left0, left1, right0, right1: Slot,
        disj firstAtom, secondAtom: Atom
    {
        no left.atom
        no right.atom

        first.atom = firstAtom
        second.atom = secondAtom

        no roleNames[first]
        no roleNames[second]

        leftUse.owner = left
        leftUse.name = role

        rightUse.owner = right
        rightUse.name = role

        roleNames[left] = role
        roleNames[right] = role

        left0.use = leftUse
        left0.index = 0
        left0.target = first

        left1.use = leftUse
        left1.index = 1
        left1.target = second

        right0.use = rightUse
        right0.index = 0
        right0.target = second

        right1.use = rightUse
        right1.index = 1
        right1.target = first

        slotsOf[left, role] = left0 + left1
        slotsOf[right, role] = right0 + right1

        not valueEqual[
            s,
            left,
            s,
            right
        ]
    }
}


/* -------------------------------------------------------------------------
 * Different target multiplicity
 * ---------------------------------------------------------------------- */

pred DifferentTargetMultiplicityIsNotEqual {
    some
        s: State,
        disj left, right, target: s.rels,
        role: Role,
        leftUse, rightUse: RoleUse,
        left0, left1, right0: Slot
    {
        no left.atom
        no right.atom

        no roleNames[target]

        leftUse.owner = left
        leftUse.name = role

        rightUse.owner = right
        rightUse.name = role

        roleNames[left] = role
        roleNames[right] = role

        left0.use = leftUse
        left0.index = 0
        left0.target = target

        left1.use = leftUse
        left1.index = 1
        left1.target = target

        right0.use = rightUse
        right0.index = 0
        right0.target = target

        slotsOf[left, role] = left0 + left1
        slotsOf[right, role] = right0

        not valueEqual[
            s,
            left,
            s,
            right
        ]
    }
}


/* -------------------------------------------------------------------------
 * Present empty role versus absent role
 * ---------------------------------------------------------------------- */

pred PresentEmptyRoleDiffersFromAbsentRole {
    some
        s: State,
        disj present, absent: s.rels,
        role: Role,
        use: RoleUse
    {
        no present.atom
        no absent.atom

        use.owner = present
        use.name = role

        roleNames[present] = role
        no roleNames[absent]

        no slotsOf[present, role]

        not valueEqual[
            s,
            present,
            s,
            absent
        ]
    }
}


/* -------------------------------------------------------------------------
 * Bounded commands
 * ---------------------------------------------------------------------- */

/*
 * These are SAT witnesses demonstrating that the bounded model admits each
 * intended inequality scenario and that valueEqual rejects the pair.
 *
 * A SAT result is bounded evidence for the scenario, not an unbounded proof
 * that all such structurally different values are unequal.
 */

run DifferentAtomsAreNotEqual
    for 3
    but exactly 1 State,
        exactly 2 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        exactly 2 Atom,
        0 EntityID,
        0 View
    expect 1


run DifferentRoleSetsAreNotEqual
    for 3
    but exactly 1 State,
        exactly 2 Rel,
        exactly 1 Role,
        exactly 1 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View
    expect 1


run DifferentTargetOrderIsNotEqual
    for 4
    but exactly 1 State,
        exactly 4 Rel,
        exactly 1 Role,
        exactly 2 RoleUse,
        exactly 4 Slot,
        exactly 2 Atom,
        0 EntityID,
        0 View
    expect 1


run DifferentTargetMultiplicityIsNotEqual
    for 3
    but exactly 1 State,
        exactly 3 Rel,
        exactly 1 Role,
        exactly 2 RoleUse,
        exactly 3 Slot,
        0 Atom,
        0 EntityID,
        0 View
    expect 1


run PresentEmptyRoleDiffersFromAbsentRole
    for 3
    but exactly 1 State,
        exactly 2 Rel,
        exactly 1 Role,
        exactly 1 RoleUse,
        0 Slot,
        0 Atom,
        0 EntityID,
        0 View
    expect 1
