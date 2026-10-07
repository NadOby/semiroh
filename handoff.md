# Handoff

Current checkpoint. Read CLAUDE.md and docs/roadmap.md first.

## State

- Task 27 / #63 merged through PR #82 as `532b68b`.
- Its implementation, measurements and changelog are complete.
- Current work: #81 on `fix/81-let-inline-if-render`.
- The implementation is complete. Next role: Publish after CI verification.

## Task 27 review

No blocking code defect found.

Independent checks verified:
- generations 1–3 match host-bytecode expansion;
- retained source stays unchanged;
- each rebuild uses one atomic activation;
- installed chunks match the generation record;
- failure during final compilation leaves state and generation unchanged;
- an injected host-run compiler bypass fails the unchanged acceptance
  test for generations 2 and 3.

Plan-owned acceptance tests and the golden declaration were preserved.
Only `programs/bootstrap` changed in the golden comparison.

The provenance test is specific to the current architecture. The manually
maintained source-dependency map is correct but can drift.

## Issue #81

The same printer mutant survived Task 27 run `37673486710` and main
control run `37682687438`. It was not introduced by Task 27.

The mutant changes the minimum precedence requested for an ordinary `let`
value from 0 to 1. Its only observable effect is redundant parentheses around
a precedence-0 expression such as an inline `if`; parsing and behaviour are
unchanged.

`docs/syntax.md` marks exact rendering layout as Provisional. The mutation
catalog already classifies analogous redundant-parenthesization changes as
`unspecified`.

The final resolution therefore classifies this survivor as `unspecified`
rather than pinning one exact rendering layout with a regression test.
Production code is unchanged.

## Verification

Before the final classification decision:
- ordinary push CI `37690789201` passed;
- exhaustive run `37692632581` passed ordinary tests and all 16 mutation
  shards with the temporary exact-layout regression test.

The temporary regression test was subsequently removed and the survivor was
added to `tests/mutation_catalog_data/shear/syntax/printer.toml`.

Final branch CI must be green before publication.

## Next

- Correct the #81 changelog entry to describe the final classification.
- Verify ordinary CI on the final branch head.
- Publish the separate fix PR with `Closes #81`.
- Keep the issue open until the fix merges.
