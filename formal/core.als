module formal/core

/*
 * SHEAR candidate semantic core – bounded structural model.
 *
 * This is an experimental model, not a normative language specification.
 *
 * Ontological candidates:
 *
 *     Atom
 *     Role
 *     Rel
 *     State
 *     View
 *     EntityID
 *
 * RoleUse, Slot, and BisimWitness are Alloy encoding / verification
 * scaffolding. They are not proposed SHEAR semantic primitives.
 *
 * A Rel atom represents a state-local relation occurrence – effectively the
 * formal RelationRef used in the architectural notes. Rel atoms carry no
 * semantic identity field.
 */


/* -------------------------------------------------------------------------
 * Atomic content
 * ---------------------------------------------------------------------- */

/*
 * Atomic values are deliberately opaque here.
 *
 * The concrete Atom domain – Bool, Int, Text, Bytes, Symbol, sentinels, etc. –
 * is an open design question and is not needed for the structural experiment.
 *
 * Equality of Atom atoms represents equality of irreducible atomic values.
 */
sig Atom {}


/* -------------------------------------------------------------------------
 * Relations
 * ---------------------------------------------------------------------- */

sig Role {}

/*
 * The only candidate graph-semantic object.
 *
 * A relation may:
 *
 *   - have no atom;
 *   - have one atom;
 *   - have no roles;
 *   - have roles;
 *   - have both an atom and roles.
 *
 * Whether the last case should eventually be restricted is deliberately
 * not decided here.
 */
sig Rel {
    atom: lone Atom
}


/*
 * Alloy scaffolding for:
 *
 *     Role -> Sequence<Rel>
 *
 * RoleUse exists so that an explicitly present empty role can be
 * distinguished from an absent role.
 *
 * RoleUse is NOT a candidate semantic object.
 */
sig RoleUse {
    owner: one Rel,
    name: one Role
}

/*
 * Slot encodes one position in an ordered role target sequence.
 *
 * Slot is NOT a candidate semantic object.
 */
sig Slot {
    use: one RoleUse,
    index: one Int,
    target: one Rel
}


/*
 * A relation has at most one occurrence of a given role name.
 */
fact UniqueRoleNames {
    all disj a, b: RoleUse |
        a.owner = b.owner implies a.name != b.name
}


/*
 * Each role target collection is a finite sequence indexed:
 *
 *     0, 1, ..., n - 1
 *
 * There may be zero slots, representing an explicitly present empty role.
 */
fact RoleTargetsAreSequences {
    all disj a, b: Slot |
        a.use = b.use implies a.index != b.index

    all s: Slot {
        s.index >= 0

        s.index > 0 implies
            (one previous: Slot |
                previous.use = s.use and
                previous.index = minus[s.index, 1])
    }
}


/* -------------------------------------------------------------------------
 * State
 * ---------------------------------------------------------------------- */

/*
 * State is a finite collection of relation occurrences.
 *
 * Alloy instances are finite by construction.
 */
sig State {
    rels: set Rel
}


/*
 * Rel atoms are state-local occurrence handles.
 *
 * One occurrence belongs to exactly one State.
 *
 * This does NOT assert that equal relational values cannot occur in
 * multiple states or multiple times in one state.
 */
fact RelationOccurrencesAreStateLocal {
    all r: Rel |
        one s: State | r in s.rels
}


fun stateOf[r: Rel]: one State {
    { s: State | r in s.rels }
}


/*
 * Structural references are closed within a state.
 */
fact RoleTargetsRemainInState {
    all s: Slot |
        s.target in stateOf[s.use.owner].rels
}


/* -------------------------------------------------------------------------
 * Structural helpers
 * ---------------------------------------------------------------------- */

fun roleNames[r: Rel]: set Role {
    (r.~owner).name
}


fun roleUse[r: Rel, role: Role]: lone RoleUse {
    {
        use: RoleUse |
            use.owner = r and
            use.name = role
    }
}


fun slotsOf[r: Rel, role: Role]: set Slot {
    roleUse[r, role].~use
}


fun indicesOf[r: Rel, role: Role]: set Int {
    slotsOf[r, role].index
}


fun targetAt[r: Rel, role: Role, index: Int]: lone Rel {
    {
        slot: slotsOf[r, role] |
            slot.index = index
    }.target
}


/* -------------------------------------------------------------------------
 * Entry points and entity bindings
 * ---------------------------------------------------------------------- */

sig EntityID {}


/*
 * View is formal scaffolding for interpreting a State from an arbitrary
 * entry relation.
 *
 * `entities` represents the proposed entry-scoped finite mapping:
 *
 *     EntityID -> RelationOccurrence
 *
 * It is intentionally represented directly as an Alloy relation here.
 * This does not decide how the map is represented inside SHEAR itself.
 */
sig View {
    state: one State,
    entry: one Rel,
    entities: EntityID -> lone Rel
}


fact ViewsStayInsideTheirState {
    all v: View {
        v.entry in v.state.rels
        EntityID.(v.entities) in v.state.rels
    }
}


/* -------------------------------------------------------------------------
 * Structural equality
 * ---------------------------------------------------------------------- */

/*
 * Candidate structural/value equality is bisimilarity.
 *
 * `pairs` relates occurrences in `left` with occurrences in `right`.
 *
 * For every related pair:
 *
 *   - atomic content is equal;
 *   - the same role names are present;
 *   - each role has the same sequence positions;
 *   - corresponding targets are themselves related by `pairs`.
 *
 * Importantly, `pairs` need not be one-to-one.
 *
 * This permits equal values with different sharing topology. For example,
 * one source child may correspond to two equal destination children.
 */
pred bisimulation[
    left: State,
    right: State,
    pairs: Rel -> Rel
] {
    pairs in left.rels -> right.rels

    all a: left.rels, b: right.rels |
        (a -> b) in pairs implies {
            a.atom = b.atom
            roleNames[a] = roleNames[b]

            all role: roleNames[a] {
                indicesOf[a, role] = indicesOf[b, role]

                all index: indicesOf[a, role] |
                    (
                        targetAt[a, role, index]
                        ->
                        targetAt[b, role, index]
                    ) in pairs
            }
        }
}


/*
 * Mathematical candidate for structural value equality:
 *
 *     two occurrences are equal iff some bisimulation relates them.
 *
 * This uses existential higher-order quantification. Positive uses are
 * suitable for bounded witness searches; the first-order BisimWitness
 * scaffolding below is used for checking algebraic closure properties
 * without relying on higher-order assertions.
 */
pred valueEqual[
    left: State,
    a: Rel,
    right: State,
    b: Rel
] {
    a in left.rels
    b in right.rels

    some pairs: left.rels -> right.rels |
        (a -> b) in pairs and
        bisimulation[left, right, pairs]
}


/* -------------------------------------------------------------------------
 * Bisimulation verification scaffolding
 * ---------------------------------------------------------------------- */

/*
 * A first-order container for an explicit bisimulation witness.
 *
 * This is verification machinery, not part of the candidate SHEAR core.
 */
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
 * Intended witness scenarios
 * ---------------------------------------------------------------------- */

/*
 * Entity identity and structural value equality are independent.
 *
 * Two distinct EntityIDs may designate two distinct occurrences whose
 * relation values are structurally equal.
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
 * Bounded checks
 * ---------------------------------------------------------------------- */

check IdentityIsBisimulation
    for 6
    but 3 State,
        12 Rel,
        8 Role,
        16 RoleUse,
        24 Slot,
        8 Atom


check ReverseIsBisimulation
    for 6
    but 3 State,
        12 Rel,
        8 Role,
        16 RoleUse,
        24 Slot,
        8 Atom,
        3 BisimWitness


check CompositionIsBisimulation
    for 6
    but 4 State,
        12 Rel,
        8 Role,
        16 RoleUse,
        24 Slot,
        8 Atom,
        4 BisimWitness


/*
 * These are expected to be satisfiable.
 *
 * They establish that the bounded model admits the intended distinctions;
 * they are not proofs that the candidate semantics is correct.
 */
run DistinctEntitiesCanNameEqualValues
    for 6
    but 2 State,
        8 Rel,
        6 Role,
        10 RoleUse,
        16 Slot,
        6 Atom,
        4 EntityID,
        2 View


run SharingDoesNotForceInequality
    for 8
    but exactly 1 State,
        exactly 5 Rel,
        exactly 1 Role,
        exactly 2 RoleUse,
        exactly 4 Slot,
        exactly 1 Atom
