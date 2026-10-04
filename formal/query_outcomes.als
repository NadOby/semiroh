module formal/query_outcomes

open formal/core_model

/*
 * Experimental bounded query-outcome model.
 *
 * Goals:
 *
 *   - keep core_model.als unchanged;
 *   - compare a privileged/scaffolding outcome representation with an
 *     ordinary graph-native representation;
 *   - exercise both value equality and occurrence identity;
 *   - keep semantic result separate from evaluator status;
 *   - bound structural comparison to at most four examined relation pairs.
 *
 * This is verification scaffolding, not proposed SHEAR ontology.
 *
 * The current core model contains only fully specified finite graph
 * structures. Therefore this experiment does not yet manufacture a semantic
 * Unknown case. Unknown is reserved for a later experiment where represented
 * information itself can be incomplete.
 */


/* -------------------------------------------------------------------------
 * Direct/scaffolding outcome representation
 * ---------------------------------------------------------------------- */

abstract sig DirectResult {}

one sig DirectYes, DirectNo, DirectUnknown extends DirectResult {}


/*
 * Evaluator status is deliberately separate from semantic result.
 *
 * BudgetExhausted means that evaluation stopped for a known operational
 * reason. It is not semantic Unknown.
 */
abstract sig EvaluationStatus {}

one sig Complete, BudgetExhausted extends EvaluationStatus {}


/* -------------------------------------------------------------------------
 * Graph-native outcome representation
 * ---------------------------------------------------------------------- */

/*
 * These atoms are experimental payload labels only.
 *
 * The result itself is an ordinary Rel carrying one of these Atom values.
 * No result-specific primitive is added to core_model.als.
 */
one sig YesAtom, NoAtom, UnknownAtom extends Atom {}


pred GraphYes[result: Rel] {
    result.atom = YesAtom
    no roleNames[result]
}

pred GraphNo[result: Rel] {
    result.atom = NoAtom
    no roleNames[result]
}

pred GraphUnknown[result: Rel] {
    result.atom = UnknownAtom
    no roleNames[result]
}


/* -------------------------------------------------------------------------
 * Bounded structural comparison scaffolding
 * ---------------------------------------------------------------------- */

/*
 * A Comparison records the finite set of relation pairs actually examined.
 *
 * `frontier` contains corresponding child pairs that still require
 * examination.
 *
 * `rank` is Alloy-only traversal scaffolding. Each examined pair receives one
 * integer rank. The root pair has rank 0, and every other examined pair must
 * be a required child of a compatible examined pair with a lower rank.
 *
 * Thus every examined pair is justified by a finite path from the root.
 *
 * The experiment bounds:
 *
 *     #examined <= 4
 *
 * The Alloy instance itself remains finite, but the comparison is explicitly
 * prevented from silently expanding to every relation pair in the instance.
 */
sig Comparison {
    leftState: one State,
    rightState: one State,

    leftRoot: one Rel,
    rightRoot: one Rel,

    examined: Rel -> Rel,
    frontier: Rel -> Rel,

    rank: Rel -> Rel -> lone Int
}

fact ComparisonEndpointsStayInStates {
    all c: Comparison {
        c.leftRoot in c.leftState.rels
        c.rightRoot in c.rightState.rels

        c.examined in c.leftState.rels -> c.rightState.rels
        c.frontier in c.leftState.rels -> c.rightState.rels

        no c.examined & c.frontier

        (c.leftRoot -> c.rightRoot) in c.examined
    }
}


/*
 * Explicit comparison budget.
 */
fact FourPairComparisonBudget {
    all c: Comparison |
        #c.examined <= 4
}


/* -------------------------------------------------------------------------
 * Pair observations
 * ---------------------------------------------------------------------- */

pred PairLocallyCompatible[a: Rel, b: Rel] {
    a.atom = b.atom
    roleNames[a] = roleNames[b]

    all role: roleNames[a] |
        indicesOf[a, role] = indicesOf[b, role]
}


pred PairLocallyContradictory[a: Rel, b: Rel] {
    not PairLocallyCompatible[a, b]
}


/*
 * Child pairs demanded by one locally compatible pair.
 */
fun RequiredChildren[a: Rel, b: Rel]: Rel -> Rel {
    {
        childA: Rel,
        childB: Rel |
            some role: roleNames[a],
                 index: indicesOf[a, role] {
                childA = targetAt[a, role, index]
                childB = targetAt[b, role, index]
            }
    }
}


/*
 * Every examined pair has exactly one traversal rank, and no unexamined pair
 * has one.
 *
 * The root is rank 0. Every non-root examined pair has positive rank and must
 * be a required child of a compatible examined pair with a lower rank.
 *
 * Because ranks strictly decrease toward the root, disconnected examined
 * cycles cannot justify themselves.
 */
fact ExaminedPairsAreRootReachable {
    all c: Comparison {
        c.rank.Int = c.examined

        c.rank[c.leftRoot][c.rightRoot] = 0

        all a: c.leftState.rels, b: c.rightState.rels |
            (a -> b) in
                c.examined - (c.leftRoot -> c.rightRoot)
            implies
            {
                c.rank[a][b] > 0

                some parentA: c.leftState.rels,
                     parentB: c.rightState.rels |
                    (parentA -> parentB) in c.examined
                    and PairLocallyCompatible[parentA, parentB]
                    and
                    (a -> b) in
                        RequiredChildren[parentA, parentB]
                    and
                    c.rank[parentA][parentB] < c.rank[a][b]
            }
    }
}


/*
 * Child pairs demanded by all examined locally compatible pairs.
 */
fun RequiredByExamined[c: Comparison]: Rel -> Rel {
    {
        childA: c.leftState.rels,
        childB: c.rightState.rels |
            some a: c.leftState.rels,
                 b: c.rightState.rels |
                (a -> b) in c.examined
                and PairLocallyCompatible[a, b]
                and
                (childA -> childB) in RequiredChildren[a, b]
    }
}


/*
 * The frontier is exactly the required child pairs that have not yet been
 * examined.
 */
pred ComparisonIsExpanded[c: Comparison] {
    c.frontier = RequiredByExamined[c] - c.examined
}


/* -------------------------------------------------------------------------
 * Bounded equality result
 * ---------------------------------------------------------------------- */

/*
 * Yes:
 *
 *   - all examined pairs are locally compatible;
 *   - every required child pair has been examined;
 *   - the frontier is empty.
 *
 * Thus the finite relation in `examined` is closed and is a bisimulation
 * witness for the compared roots.
 */
pred EqualityYes[c: Comparison] {
    ComparisonIsExpanded[c]

    all a: c.leftState.rels, b: c.rightState.rels |
        (a -> b) in c.examined implies
            PairLocallyCompatible[a, b]

    no c.frontier
}


/*
 * No:
 *
 * A structural contradiction has actually been reached and examined.
 */
pred EqualityNo[c: Comparison] {
    some a: c.leftState.rels, b: c.rightState.rels |
        (a -> b) in c.examined
        and PairLocallyContradictory[a, b]
}


/*
 * Budget exhaustion:
 *
 *   - no examined contradiction exists;
 *   - unresolved required child pairs remain;
 *   - all four permitted examined pairs have been consumed.
 *
 * This is evaluator status, not semantic Unknown.
 */
pred EqualityBudgetExhausted[c: Comparison] {
    ComparisonIsExpanded[c]

    no a: c.leftState.rels, b: c.rightState.rels |
        (a -> b) in c.examined
        and PairLocallyContradictory[a, b]

    some c.frontier
    #c.examined = 4
}


/* -------------------------------------------------------------------------
 * Direct result interpretation
 * ---------------------------------------------------------------------- */

pred DirectEqualityResult[
    c: Comparison,
    result: DirectResult,
    status: EvaluationStatus
] {
    (
        EqualityYes[c]
        and result = DirectYes
        and status = Complete
    )
    or
    (
        EqualityNo[c]
        and result = DirectNo
        and status = Complete
    )
    or
    (
        EqualityBudgetExhausted[c]
        and status = BudgetExhausted
    )
}


/* -------------------------------------------------------------------------
 * Graph-native result interpretation
 * ---------------------------------------------------------------------- */

pred GraphEqualityResult[
    c: Comparison,
    result: Rel,
    status: EvaluationStatus
] {
    (
        EqualityYes[c]
        and GraphYes[result]
        and status = Complete
    )
    or
    (
        EqualityNo[c]
        and GraphNo[result]
        and status = Complete
    )
    or
    (
        EqualityBudgetExhausted[c]
        and status = BudgetExhausted
    )
}


/* -------------------------------------------------------------------------
 * Identity comparison
 * ---------------------------------------------------------------------- */

/*
 * Identity is occurrence identity, not value equality.
 *
 * It requires no structural traversal and therefore cannot exhaust the
 * structural comparison budget.
 */
pred DirectIdentityResult[
    left: Rel,
    right: Rel,
    result: DirectResult,
    status: EvaluationStatus
] {
    status = Complete

    (
        left = right
        and result = DirectYes
    )
    or
    (
        left != right
        and result = DirectNo
    )
}


pred GraphIdentityResult[
    left: Rel,
    right: Rel,
    result: Rel,
    status: EvaluationStatus
] {
    status = Complete

    (
        left = right
        and GraphYes[result]
    )
    or
    (
        left != right
        and GraphNo[result]
    )
}


/* -------------------------------------------------------------------------
 * Representation correspondence
 * ---------------------------------------------------------------------- */

pred DirectAndGraphEqualityAgree[
    c: Comparison,
    direct: DirectResult,
    graph: Rel,
    status: EvaluationStatus
] {
    DirectEqualityResult[c, direct, status]
    GraphEqualityResult[c, graph, status]

    direct = DirectYes implies GraphYes[graph]
    direct = DirectNo implies GraphNo[graph]
    direct = DirectUnknown implies GraphUnknown[graph]
}


pred DirectAndGraphIdentityAgree[
    left: Rel,
    right: Rel,
    direct: DirectResult,
    graph: Rel,
    status: EvaluationStatus
] {
    DirectIdentityResult[left, right, direct, status]
    GraphIdentityResult[left, right, graph, status]

    direct = DirectYes implies GraphYes[graph]
    direct = DirectNo implies GraphNo[graph]
}


/* -------------------------------------------------------------------------
 * Witness scenarios
 * ---------------------------------------------------------------------- */

pred EqualLeafComparisonExists {
    some
        c: Comparison,
        direct: DirectResult,
        graph: Rel,
        status: EvaluationStatus
    {
        c.leftRoot != c.rightRoot

        no c.leftRoot.atom
        no c.rightRoot.atom

        no roleNames[c.leftRoot]
        no roleNames[c.rightRoot]

        DirectAndGraphEqualityAgree[
            c,
            direct,
            graph,
            status
        ]

        direct = DirectYes
        status = Complete
    }
}


pred UnequalLeafComparisonExists {
    some
        c: Comparison,
        direct: DirectResult,
        graph: Rel,
        status: EvaluationStatus
    {
        some c.leftRoot.atom
        some c.rightRoot.atom
        c.leftRoot.atom != c.rightRoot.atom

        DirectAndGraphEqualityAgree[
            c,
            direct,
            graph,
            status
        ]

        direct = DirectNo
        status = Complete
    }
}


/*
 * Reuses the important cyclic case:
 *
 *     self -> self
 *
 * versus:
 *
 *     first -> second -> first
 *
 * The finite comparison closes with two distinct examined pairs.
 */
pred CyclicEqualityClosesWithinBudget {
    some
        c: Comparison,
        disj self, first, second: Rel,
        role: Role,
        selfUse, firstUse, secondUse: RoleUse,
        selfSlot, firstSlot, secondSlot: Slot,
        direct: DirectResult,
        graph: Rel,
        status: EvaluationStatus
    {
        c.leftState = c.rightState
        self + first + second in c.leftState.rels

        c.leftRoot = self
        c.rightRoot = first

        no self.atom
        no first.atom
        no second.atom

        selfUse.owner = self
        selfUse.name = role

        firstUse.owner = first
        firstUse.name = role

        secondUse.owner = second
        secondUse.name = role

        selfSlot.use = selfUse
        selfSlot.index = 0
        selfSlot.target = self

        firstSlot.use = firstUse
        firstSlot.index = 0
        firstSlot.target = second

        secondSlot.use = secondUse
        secondSlot.index = 0
        secondSlot.target = first

        c.examined =
            (self -> first)
            + (self -> second)

        no c.frontier

        DirectAndGraphEqualityAgree[
            c,
            direct,
            graph,
            status
        ]

        direct = DirectYes
        status = Complete
    }
}


/*
 * Five corresponding pairs are required, but only four may be examined.
 *
 * No contradiction has been discovered. The fifth pair remains on the
 * frontier, so evaluation ends with BudgetExhausted rather than Unknown.
 */
pred EqualityBudgetExhaustionExists {
    some
        c: Comparison,
        disj l0, l1, l2, l3, l4: c.leftState.rels,
        disj r0, r1, r2, r3, r4: c.rightState.rels,
        role: Role
    {
        c.leftRoot = l0
        c.rightRoot = r0

        no (l0 + l1 + l2 + l3 + l4).atom
        no (r0 + r1 + r2 + r3 + r4).atom

        all l: l0 + l1 + l2 + l3 |
            roleNames[l] = role

        all r: r0 + r1 + r2 + r3 |
            roleNames[r] = role

        no roleNames[l4]
        no roleNames[r4]

        targetAt[l0, role, 0] = l1
        targetAt[l1, role, 0] = l2
        targetAt[l2, role, 0] = l3
        targetAt[l3, role, 0] = l4

        targetAt[r0, role, 0] = r1
        targetAt[r1, role, 0] = r2
        targetAt[r2, role, 0] = r3
        targetAt[r3, role, 0] = r4

        indicesOf[l0, role] = 0
        indicesOf[l1, role] = 0
        indicesOf[l2, role] = 0
        indicesOf[l3, role] = 0

        indicesOf[r0, role] = 0
        indicesOf[r1, role] = 0
        indicesOf[r2, role] = 0
        indicesOf[r3, role] = 0

        c.examined =
            (l0 -> r0)
            + (l1 -> r1)
            + (l2 -> r2)
            + (l3 -> r3)

        c.frontier = l4 -> r4

        EqualityBudgetExhausted[c]
    }
}


pred SameIdentityExists {
    some
        s: State,
        value: s.rels,
        direct: DirectResult,
        graph: Rel,
        status: EvaluationStatus
    {
        DirectAndGraphIdentityAgree[
            value,
            value,
            direct,
            graph,
            status
        ]

        direct = DirectYes
    }
}


pred EqualValueDistinctIdentityExists {
    some
        s: State,
        disj left, right: s.rels,
        direct: DirectResult,
        graph: Rel,
        status: EvaluationStatus
    {
        no left.atom
        no right.atom
        no roleNames[left]
        no roleNames[right]

        valueEqual[s, left, s, right]

        DirectAndGraphIdentityAgree[
            left,
            right,
            direct,
            graph,
            status
        ]

        direct = DirectNo
    }
}


/* -------------------------------------------------------------------------
 * Assertions
 * ---------------------------------------------------------------------- */

/*
 * A completed Yes comparison provides an explicit bisimulation witness:
 *
 *   - `examined` lies inside leftState.rels -> rightState.rels by fact;
 *   - the root pair is in `examined` by fact;
 *   - EqualityYes requires every examined pair to be locally compatible;
 *   - an empty exact frontier means every required corresponding child pair
 *     is already in `examined`.
 *
 * Together this is the concrete witness required by valueEqual. Checking the
 * existential valueEqual formulation directly here requires higher-order
 * quantification that Alloy cannot always skolemize, so this assertion checks
 * the witness property itself.
 */
assert ClosedBoundedComparisonIsBisimulation {
    all c: Comparison |
        EqualityYes[c]
        implies
        bisimulation[
            c.leftState,
            c.rightState,
            c.examined
        ]
}


assert IdentityNeverExhaustsStructuralBudget {
    all
        left, right: Rel,
        result: DirectResult,
        status: EvaluationStatus
    |
        DirectIdentityResult[
            left,
            right,
            result,
            status
        ]
        implies
        status = Complete
}


/* -------------------------------------------------------------------------
 * Bounded commands
 * ---------------------------------------------------------------------- */

run EqualLeafComparisonExists
    for 4
    but 2 State,
        4 Rel,
        1 Role,
        2 RoleUse,
        2 Slot,
        exactly 3 Atom,
        0 EntityID,
        0 View,
        exactly 1 Comparison
    expect 1

run UnequalLeafComparisonExists
    for 4
    but 2 State,
        4 Rel,
        1 Role,
        2 RoleUse,
        2 Slot,
        exactly 5 Atom,
        0 EntityID,
        0 View,
        exactly 1 Comparison
    expect 1

run CyclicEqualityClosesWithinBudget
    for 5
    but exactly 1 State,
        4 Rel,
        exactly 1 Role,
        exactly 3 RoleUse,
        exactly 3 Slot,
        exactly 3 Atom,
        0 EntityID,
        0 View,
        exactly 1 Comparison
    expect 1

run EqualityBudgetExhaustionExists
    for 10
    but exactly 2 State,
        exactly 10 Rel,
        exactly 1 Role,
        exactly 8 RoleUse,
        exactly 8 Slot,
        exactly 3 Atom,
        0 EntityID,
        0 View,
        exactly 1 Comparison
    expect 1

run SameIdentityExists
    for 3
    but exactly 1 State,
        2 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        exactly 3 Atom,
        0 EntityID,
        0 View,
        0 Comparison
    expect 1

run EqualValueDistinctIdentityExists
    for 3
    but exactly 1 State,
        exactly 3 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        exactly 3 Atom,
        0 EntityID,
        0 View,
        0 Comparison
    expect 1

check ClosedBoundedComparisonIsBisimulation
    for 4
    but 2 State,
        4 Rel,
        1 Role,
        3 RoleUse,
        3 Slot,
        exactly 3 Atom,
        0 EntityID,
        0 View,
        exactly 1 Comparison
    expect 0

check IdentityNeverExhaustsStructuralBudget
    for 3
    but 1 State,
        3 Rel,
        0 Role,
        0 RoleUse,
        0 Slot,
        exactly 3 Atom,
        0 EntityID,
        0 View,
        0 Comparison
    expect 0
