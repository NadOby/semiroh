# Contract Model

This document defines the current semantic model for contracts in SHEAR.

The contract system is not yet fully implemented. This document records the
current semantic design rather than claiming a completed implementation.

## 1. Contracts as semantic values

A contract is an immutable semantic value describing requirements and
guarantees associated with another semantic value or semantic operation.

Conceptually:

    Contract(subject)
        |
        +--> requirements
        |
        +--> guarantees

Requirements describe conditions that must be satisfied for the contracted
use or operation.

Guarantees describe properties that the contract establishes when its stated
conditions are satisfied.

A contract does not itself perform the operation it describes.

## 2. Contracts use constraints

Requirements and guarantees are expressed using constraints.

Conceptually:

    Contract
        |
        +--> Requirement -> Constraint
        |
        +--> Guarantee  -> Constraint

A contract therefore does not introduce a second predicate system.

The same constraint model is used independently of whether a constraint is
attached to a contract.

A constraint may participate in multiple contracts or exist without any
contract.

## 3. Contract immutability

Contracts are immutable semantic values.

Changing a requirement or guarantee produces a different contract value.

Evaluation of a contract does not mutate the contract.

Runtime state, evaluation caches, consumed resources, and temporary evidence
must not become part of the contract's semantic identity.

Physical implementations may use structural sharing, interning, caching, or
lazy evaluation provided that observable semantic behaviour remains
consistent with the immutable model.

## 4. Requirements

A requirement is a constraint that describes a condition under which a
contract is applicable or valid.

For example:

    Requirement:
        argument satisfies type constraint

or:

    Requirement:
        resource satisfies capability constraint

Requirements may concern:

- semantic values;
- entities;
- types;
- states;
- references;
- resources;
- capabilities;
- transformations;
- representations;
- other contracts.

The exact interpretation of a requirement depends on the contract context.

A requirement being unknown is not equivalent to the requirement being
violated.

The underlying constraint model therefore retains:

    Satisfied
    Violated
    Unknown

## 5. Guarantees

A guarantee is a constraint describing a property established by the contract
when its applicable requirements and semantic conditions hold.

For example:

    Requirement:
        input satisfies condition A

    Guarantee:
        result satisfies condition B

A guarantee is a semantic claim, not merely documentation.

Whether a guarantee has actually been established is determined by the
applicable contract semantics and evidence.

A contract must not silently treat an unverified guarantee as established.

## 6. Preconditions and postconditions

Requirements and guarantees can express the familiar distinction between
preconditions and postconditions.

Conceptually:

    precondition
        =
    requirement on the applicable input/context

    postcondition
        =
    guarantee about the resulting semantic state/value/context

The contract model is not restricted to this pattern.

Contracts may describe properties that are neither naturally preconditions nor
postconditions.

The terms "requirement" and "guarantee" are therefore the more general
semantic concepts.

## 7. Contract subject

A contract may be associated with different kinds of semantic values.

Possible subjects include:

- callable values;
- transformations;
- types;
- modules;
- data values;
- resources;
- representations;
- semantic states;
- other semantic values.

The contract model must not assume that every contract describes a function
call.

For a callable value, a contract may describe argument requirements and
result guarantees.

For a transformation, a contract may describe requirements on the source
state and guarantees about the destination state.

For a resource, a contract may describe conditions for valid use and
properties guaranteed by that use.

## 8. Contract evaluation

Contract evaluation applies a contract to its relevant subject and semantic
context.

Conceptually:

    Contract
        +
    subject
        +
    context
        ->
    contract evaluation result

Evaluation may require evaluation of the contract's constraints.

The contract itself remains immutable.

The exact representation of the contract evaluation result is not yet
specified.

The result must preserve the distinction between:

    established
    violated
    unknown

where those distinctions are applicable to the contract semantics.

## 9. Requirement failure

A violated requirement means that the stated condition for the contract is
not satisfied.

This is distinct from an unknown requirement.

For example:

    requirement evaluation -> Unknown

does not establish:

    requirement evaluation -> Violated

Consequently, a contract evaluator must not silently execute or validate a
contract merely because it cannot establish that a requirement is violated.

The precise operational response to unknown requirements remains dependent on
the contract's execution and effect semantics.

## 10. Guarantee establishment

A guarantee may be established through:

- direct semantic evaluation;
- execution under the contract;
- constraint evaluation;
- a transformation result;
- a proof or certificate;
- analysis;
- explicitly supplied evidence.

Evidence must be interpreted according to the relevant semantic rules.

The existence of a contract does not by itself prove that its guarantees hold
for an arbitrary subject or execution.

## 11. Contract composition

Contracts may eventually be composed.

Composition must combine requirements and guarantees according to explicit
semantic rules.

The exact composition algebra is not yet specified.

In particular, the implementation must not assume that contract composition
can be reduced to simple concatenation of constraint lists.

Composition may require reasoning about dependencies between:

    requirements
    guarantees
    subject transformations
    intermediate states

Any such rules must be defined before a normative contract-composition API is
introduced.

## 12. Contract refinement

A contract may be refined by replacing it with another contract that imposes
different requirements or establishes different guarantees.

The semantic relation between two contracts must be explicitly defined before
contract refinement is treated as a formal operation.

In particular, stronger and weaker contracts must not be inferred merely from
structural similarity.

A future refinement relation may use constraint implication or another
explicit semantic relation.

Until that relation is defined:

    similar contract structure
        !=
    proven contract refinement

## 13. Contracts and transformations

A transformation may be subject to a contract.

Conceptually:

    Contract
       |
       v
    Transformation
       |
       v
    destination state

A transformation contract may contain:

    requirements on source state/context
    guarantees about destination state/context

Transformation mappings may provide evidence relevant to those constraints.

However, an explicit transformation mapping does not automatically establish
arbitrary guarantees.

For example:

    entity A maps to entity B

does not by itself prove:

    property(A) -> property(B)

Such preservation must be established by the applicable constraint or
contract semantics.

## 14. Contracts and state

A contract may refer to semantic state.

For example, a transformation contract may express:

    Requirement:
        source state satisfies constraint C

    Guarantee:
        destination state satisfies constraint D

State identity remains determined by state content.

Contract evaluation does not change state identity.

Activation of a state is also separate from contract evaluation.

## 15. Contracts and references

Contracts may impose requirements on references or guarantee properties about
references.

Reference validity itself remains defined by the reference model.

A contract must not manufacture reference continuity.

In particular:

    same EntityID
    structural similarity
    matching values

do not establish reference transfer between states.

Where a contract concerns continuity, it must rely on the explicit
transformation mapping semantics.

## 16. Contracts and types

Types are semantic values and may participate in constraints.

A contract may therefore express requirements and guarantees involving types.

For example:

    Requirement:
        value satisfies type constraint

    Guarantee:
        returned value satisfies type constraint

The contract model does not require a separate type-contract mechanism.

The eventual type system may provide specialized semantics where necessary,
but those semantics remain compatible with the general constraint model.

## 17. Contracts and equality

Contract requirements or guarantees may involve semantic equality.

Equality and constraint satisfaction remain separate concepts.

For example:

    equality establishes that two semantic values are equal

while:

    a constraint evaluates whether some proposition holds.

A contract may use equality as part of a constraint without changing the
meaning of either system.

## 18. Contracts and effects

Contracts may eventually describe effects associated with an operation.

Examples may include:

- mutation;
- program modification;
- logging;
- resource consumption;
- other explicitly modelled effects.

The current contract model does not define the effect system.

Effect semantics therefore must not be invented implicitly through contract
fields.

When effects become formally specified, contracts may reference the resulting
effect model through constraints or dedicated semantic relations.

## 19. Contracts and capabilities

Capabilities may participate in contract requirements or guarantees.

For example:

    Requirement:
        caller possesses capability C

or:

    Guarantee:
        resulting resource provides capability D

The capability model remains separate from the contract model.

A contract does not itself grant authority merely by mentioning a capability.

Authority semantics belong to the capability and ownership models.

## 20. Contracts and resources

Contracts may describe use of external resources.

A resource-related contract may specify:

    requirements for access
    guarantees about the resulting operation

Resource availability, authority, lifetime, and external side effects remain
properties of the relevant semantic systems.

A contract does not make an external resource immutable or internal merely by
referring to it.

## 21. Contracts and representations

A representation is not necessarily the semantic value represented by it.

Contracts may concern representations when the contract explicitly describes
representation-level properties.

For example:

    Requirement:
        representation uses encoding X

or:

    Guarantee:
        produced representation satisfies format constraint Y

Representation-level guarantees must not be confused with guarantees about
the underlying semantic value.

A representation satisfying a contract does not automatically imply that
every semantic property of the represented value has been established.

## 22. Contracts and metaprogramming

Contracts are semantic values and may therefore be inspected or manipulated
by metaprograms.

A metaprogram may:

- construct contracts;
- inspect requirements;
- inspect guarantees;
- generate constraints;
- analyse contracts;
- transform contract values.

Such operations produce new semantic values where appropriate.

Metaprogramming does not grant implicit authority to violate the semantic
rules of the values being manipulated.

## 23. Contract identity

A contract has semantic identity according to the general SHEAR identity
model.

Its identity must be determined by its canonical semantic content.

Evaluation history must not affect contract identity.

In particular, the following must not change contract identity:

- evaluation results;
- evaluation caches;
- runtime state;
- temporary evidence;
- resource consumption;
- provenance metadata unless explicitly defined as semantic content.

The exact canonical contract representation remains implementation work.

## 24. Contract provenance

Contract evaluation or construction may produce provenance metadata.

Provenance may record information such as:

- how a contract was constructed;
- which analysis produced evidence;
- which transformation was evaluated;
- which external source supplied evidence.

Provenance is metadata unless explicitly defined as part of the semantic
contract value.

Consequently, two semantically identical contracts must not become different
contract values merely because they were derived through different histories.

## 25. Contract validity versus contract satisfaction

The existence of a contract and satisfaction of a contract are distinct.

A contract may be semantically well-formed while its requirements are not
satisfied for a particular subject.

Likewise, a contract may contain guarantees that have not yet been
established for a particular execution.

Therefore:

    valid contract
        !=
    contract satisfied for subject

The exact notion of contract well-formedness remains part of future contract
validation semantics.

## 26. Contract violation

A contract violation occurs when a required contractual condition is
established to be false, or when a guarantee that must hold is established to
be false, according to the applicable contract semantics.

A lack of evidence is not automatically a violation.

Conceptually:

    insufficient evidence
        ->
    Unknown

not:

    insufficient evidence
        ->
    ContractViolation

The eventual runtime and tooling semantics may distinguish contract
violation from ordinary constraint violation.

That distinction is not yet formally specified.

## 27. Contract checking and execution

Contract checking and execution are separate semantic operations.

A system may:

- check requirements before execution;
- establish guarantees after execution;
- analyse both statically;
- evaluate only selected constraints;
- defer checking;
- use certificates or other evidence.

The contract model does not mandate one execution strategy.

An implementation may optimize or reorder checking where the observable
semantic result remains valid.

## 28. Soundness principle

A contract evaluator must not claim that a guarantee has been established
without sufficient semantic basis.

Likewise, a requirement must not be treated as violated merely because its
satisfaction could not be established.

The system should preserve the distinction between:

    satisfied
    violated
    unknown

throughout contract evaluation where those outcomes apply.

This is inherited from the constraint model rather than being a separate
three-valued logic invented by contracts.

## 29. Contracts as reusable semantic specifications

A contract may be attached to multiple compatible semantic uses.

For example, the same constraint can participate in contracts for:

- multiple callable values;
- multiple transformations;
- multiple representations;
- multiple resources.

The contract itself remains a reusable semantic value.

Binding a contract to a particular subject or execution context is separate
from defining the contract.

## 30. Current implementation status

The current Python reference model does not yet implement a complete contract
system.

The following remain future work:

- concrete contract representation;
- contract identity;
- requirement representation;
- guarantee representation;
- contract evaluation;
- contract result representation;
- contract validation;
- contract composition;
- contract refinement;
- contract-to-transformation interaction;
- contract evidence;
- contract provenance;
- contract interaction with effects;
- contract interaction with capabilities;
- contract execution semantics.

This document therefore defines architecture and semantic boundaries rather
than an implementation API.

## 31. Unresolved areas

Open questions include:

- exact contract representation;
- canonical contract serialization;
- formal contract equality;
- requirement/guarantee ordering;
- contract evaluation result;
- contract composition;
- contract refinement;
- implication between constraints;
- static versus dynamic checking;
- evidence and certificates;
- guarantee establishment;
- contract violation semantics;
- interaction with effects;
- interaction with capabilities;
- interaction with ownership;
- interaction with transformations;
- interaction with representations;
- contract inheritance or reuse mechanisms;
- contract versioning;
- contract persistence.

These questions must be resolved explicitly before the corresponding
mechanisms become normative.

## 32. Design principles

Contracts are immutable semantic values.

Contracts use the existing constraint model rather than introducing a second
predicate system.

Requirements describe conditions for contractual applicability or validity.

Guarantees describe properties established under the contract's semantic
conditions.

Unknown constraint results remain distinct from violations.

A contract does not automatically prove its own guarantees.

A transformation mapping does not automatically establish arbitrary
property preservation.

Authority remains separate from contractual description.

Effects remain separate from contractual description until an effect model is
defined.

Contract identity is independent of evaluation history and runtime state.

Contract semantics must remain general enough to describe callable values,
transformations, types, modules, data, resources, representations, and other
semantic values.

The contract model should add a reusable semantic specification layer without
duplicating the underlying systems for constraints, identity, state,
ownership, references, transformations, effects, or capabilities.
