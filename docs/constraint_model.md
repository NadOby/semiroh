# Constraint Model

This document defines the current semantic model for constraints in SEMIROH.

The constraint system is not yet fully implemented. This document records the
current semantic design rather than claiming a completed implementation.

## 1. Constraints as semantic values

A constraint is an immutable semantic value representing a proposition about
one or more semantic values.

Conceptually:

    Constraint(subject) -> result

The constraint itself does not contain evaluation state.

Types are also semantic values and may participate in constraint-based
reasoning.

Constraints may therefore describe properties of:

- values;
- entities;
- states;
- types;
- relations;
- transformations;
- other semantic values.

A constraint describes validity or knowledge about its subject. It does not
describe an operation that changes the subject.

## 2. Constraint evaluation

Constraint evaluation is an operation that applies a constraint to a subject
under some evaluation context.

Conceptually:

    Constraint
        +
    subject
        +
    evaluation context
        +
    applicable resources
        ->
    ConstraintResult

Evaluation is separate from the constraint itself.

Evaluating a constraint does not mutate the constraint or the subject.

The exact representation of evaluation context remains unspecified.

## 3. Three-valued evaluation

Constraint evaluation has three semantic outcomes:

    Satisfied
    Violated
    Unknown

`Unknown` is a first-class result.

It does not mean that the constraint is false.

It means that the system has not established either satisfaction or violation
under the applicable evaluation conditions.

The three outcomes are semantically distinct:

    Satisfied
        satisfaction has been established

    Violated
        violation has been established

    Unknown
        neither has been established

Unknown must not be silently converted into either of the definitive
outcomes.

## 4. Why Unknown exists

Semantic computation may be:

- expensive;
- incomplete;
- externally dependent;
- resource-bounded;
- dependent on unavailable information;
- dependent on unresolved semantic relationships.

The system must therefore distinguish:

    proven satisfied
    proven violated
    not established

Treating the third case as either success or failure would lose information
about the limits of available knowledge.

Unknown therefore represents an epistemic state, not a third truth value
equivalent to false.

## 5. Evaluation conditions and budgets

Constraint evaluation may depend on explicit evaluation conditions.

Potentially expensive semantic computation may also be subject to explicit
budgets.

Possible budget dimensions include:

- computation steps;
- memory;
- recursion depth;
- graph expansion;
- transformation count;
- optional wall-clock time.

The exact budget mechanism is not yet specified. The current reference model
implements only a computation-step budget: each evaluated constraint node
consumes one step.

Where an applicable evaluation condition or budget prevents a definitive
constraint result from being established, the result is `Unknown`.

A budget does not itself establish violation.

For example:

    evaluation exhausted budget
        ->
    Unknown

not:

    evaluation exhausted budget
        ->
    Violated

## 6. Evidence

Constraint evaluation may rely on evidence such as:

- structural facts;
- computed results;
- previously established constraints;
- metaprogram-generated evidence;
- certificates;
- analysis results;
- transformation references.

Evidence is information used to establish a result.

Evidence is distinct from the result it supports.

Conceptually:

    evidence
        +
    evaluation rules
        ->
    ConstraintResult

The current model does not yet define a canonical evidence representation.

A future evidence model must not make evidence indistinguishable from the
truth or knowledge claim that it supports.

## 7. Constraint identity

A constraint is a semantic value and therefore participates in the SEMIROH
identity model.

Constraint identity must be independent of mutable evaluation state.

Evaluation results, caches, resource consumption, and runtime evaluation state
must not change the identity of the constraint.

In the current reference model, a semantic constraint has a tagged canonical
representation. Its identity follows from canonical serialization, like any
other semantic value, so constraints can appear in program state.

## 8. Constraint immutability

Constraints are immutable.

Creating a different constraint produces a different semantic value.

Evaluating a constraint does not modify it.

Updating information relevant to a constraint therefore produces another
semantic object rather than mutating the existing constraint.

This is consistent with the general SEMIROH rule that semantic state and
semantic values are immutable by default.

Physical implementations may use:

- structural sharing;
- interning;
- caching;
- lazy evaluation;
- compact representations;

provided that observable semantic behaviour remains equivalent to the
immutable model.

## 9. Constraint composition

Constraints may be composed into larger constraints.

The composition itself is a new immutable semantic value.

At minimum, the model is expected to support logical composition such as:

    AND
    OR
    NOT

Composition must preserve the distinction between:

    Satisfied
    Violated
    Unknown

In particular, an implementation must not collapse an unresolved component
into a definitive result merely because a definitive result would be
convenient.

The composition rules are those of strong Kleene logic. A composed result is
definitive only when it holds for every possible resolution of its `Unknown`
components:

    AND (all of)
        Violated   if any component is Violated
        Satisfied  if every component is Satisfied
        Unknown    otherwise

    OR (any of)
        Satisfied  if any component is Satisfied
        Violated   if every component is Violated
        Unknown    otherwise

    NOT
        Satisfied  ↔  Violated
        Unknown    →  Unknown

For example, `Violated AND Unknown` is `Violated`: whatever the unknown
component turns out to be, the conjunction cannot be satisfied. `Satisfied
AND Unknown` stays `Unknown`.

An empty AND is `Satisfied`; an empty OR is `Violated`.

AND and OR are commutative and idempotent, so their components have set
semantics: the order and repetition of components do not affect constraint
identity.

## 10. Constraint dependencies

A constraint may depend on other constraints.

For example:

    ValidOwnership
        depends on
    AcyclicOwnership
    UniqueOwner

Dependencies are semantic relationships.

They must not be confused with evaluation history.

A dependency may be evaluated independently and its result may be used as
evidence for another constraint.

The exact dependency and evaluation model remains unresolved.

## 11. Constraints and types

Types are semantic values.

A type relationship may therefore be expressed through constraints rather than
requiring every type-system rule to be an unrelated primitive mechanism.

Conceptually:

    value
      |
      v
    constraint
      |
      v
    Satisfied / Violated / Unknown

The final type and constraint language remains under development.

This does not imply that every type-system operation must be implemented as an
ordinary runtime constraint evaluation. The eventual language may provide
specialized mechanisms where they are semantically or operationally justified.

## 12. Constraints and contracts

Contracts may contain requirements and guarantees.

Conceptually:

    Contract
       |
       +--> requirements -> Constraint
       |
       +--> guarantees  -> Constraint

A requirement and a guarantee are contextual roles for constraints. They do
not require two unrelated predicate systems.

A constraint may exist independently of any contract.

Contracts therefore build on the constraint model rather than replacing it.

The complete contract model is specified separately.

## 13. Constraints and transformations

Transformations may provide information relevant to constraints.

For example, a transformation may establish structural relationships between
entities that a later constraint evaluation can use as evidence.

Transformation mappings are not themselves automatically truth values.

The semantic meaning of information obtained from a transformation must be
defined by the relevant constraint.

A transformation does not automatically prove that a constraint is preserved.

For example:

    constraint holds in S₀
        +
    transformation S₀ -> S₁
        !=
    constraint holds in S₁

Preservation must be established explicitly by the applicable semantic rules
or analysis.

## 14. Constraint preservation across transformations

A constraint may be evaluated before and after a transformation.

Possible knowledge about preservation includes:

    Preserved
    Broken
    Unknown

These are statements about knowledge of the relationship between the
constraint and the transformation.

They are not replacements for the ordinary constraint results:

    Satisfied
    Violated
    Unknown

The exact preservation relation remains to be specified.

In particular, the current transformation model must not be extended with
implicit constraint-preservation semantics until those semantics are defined.

## 15. Constraint composition versus transformation composition

Constraint composition and transformation composition are different operations.

Constraint composition combines propositions.

Transformation composition combines explicit continuity information.

For example:

    Constraint A
    AND
    Constraint B

produces a constraint describing both propositions.

Whereas:

    A -> B
    B -> C

produces composed transformation continuity information:

    A -> C

The two forms of composition must not be conflated.

## 16. Constraints and semantic state

A constraint may describe a property of a semantic state.

For example:

    ValidState(S)

may establish that the values and ownership relation of `S` satisfy a
specified invariant.

Evaluation of the constraint does not alter `S`.

A state may satisfy a constraint independently of whether the state is
currently active.

State identity remains determined by semantic state content rather than by
constraint evaluation history.

## 17. Constraints and references

A constraint may describe properties involving references.

Reference validity itself is defined by the reference model.

A constraint may use that validity as a semantic fact, but constraint
evaluation must not silently alter reference semantics.

In particular:

    EntityID reuse
    state adjacency
    structural similarity

must not manufacture continuity merely because a constraint refers to related
entities.

Reference transfer remains an explicit transformation operation.

## 18. Constraint evaluation and ordinary computation

Not every semantic computation necessarily produces a three-valued result.

An ordinary semantic computation may produce:

- a semantic value;
- an explicitly defined error;
- another operation-specific result.

The three-valued constraint model is primarily relevant when the semantic
question is whether a proposition has been established.

Therefore:

    ordinary computation failure
        != automatically Unknown

and:

    constraint evaluation Unknown
        != ordinary execution failure

The semantics of ordinary computation errors belong to the relevant future
error and effect models.

## 19. Soundness principle

A system must not report `Satisfied` or `Violated` merely because an answer
could theoretically be obtained with unlimited computation.

A definitive result must be supported by the applicable evaluation rules and
available evidence.

The implementation may be incomplete while remaining semantically sound.

In particular:

    insufficient evidence
        ->
    Unknown

must be preferred to an unsupported definitive result.

## 20. Current implementation status

The Python reference model currently provides:

    ConstraintResult
        Satisfied, Violated, Unknown, and whether a result is decisive
        (is_known)

    Constraint
        base of all constraints, which are semantic values:
        IsKind, IntRange, Length, OneOf       primitive constraints
        AllOf, AnyOf, Not                     composition (section 9)
        External                              a named constraint evaluated
                                              by an Evaluator

    EvaluationContext
        registered evaluators for External constraints and an optional
        computation-step budget

    Evaluator
        an executable evaluator wrapping a Python predicate; it is not a
        semantic value and is referenced by name through External

Constraints are semantic values with canonical identity and can appear in
program state. An External constraint without a registered
evaluator evaluates to Unknown, as does evaluation that exhausts its budget.

Every subject is canonicalized before evaluation. Executable evaluators
therefore always receive canonical content, the same form as `Value.content`,
whether they are called directly or through External.

The following remain future work:

- constraints relating several entities (naturally hyperedges of the semantic
  graph);
- evidence representation;
- evaluation conditions beyond registered evaluators;
- budget dimensions beyond computation steps;
- dependency evaluation;
- preservation analysis.

The absence of implementation must not be interpreted as an absence of the
semantic concept.

## 21. Unresolved areas

Open questions include:

- exact constraint representation;
- constraint identity;
- predicate representation;
- evidence representation;
- evaluation context;
- constraint composition;
- three-valued composition rules;
- implication and dependency;
- incremental constraint evaluation;
- constraint caching;
- resource-budget semantics;
- interaction with equality;
- interaction with contracts;
- interaction with effects and capabilities;
- interaction with transformation preservation;
- formal soundness rules.

The constraint model does not currently require a separate first-class
predicate object. Whether predicates eventually become independently
represented semantic values remains open.

## 22. Design principles

The constraint system represents knowledge explicitly.

In particular:

    Unknown != Violated
    Unknown != Satisfied

A constraint is an immutable semantic value.

Constraint evaluation is separate from the constraint.

Evaluation state and cached results do not become part of constraint identity.

Evidence is distinct from the result established from that evidence.

Constraints may be reused by contracts and other semantic mechanisms.

Constraints do not automatically establish properties of future states or
transformations.

The language should preserve these distinctions rather than silently
converting lack of knowledge into a definitive semantic result.
