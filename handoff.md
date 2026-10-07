# Handoff

Current checkpoint. Read CLAUDE.md and docs/roadmap.md first.

## State

- Task 27 / #63 merged through PR #82 as `532b68b`.
- Its implementation, measurements and changelog are complete.
- Current work: #81 on `fix/81-let-inline-if-render`.
- Tested code head: `7654fe6be74a930abbd8cf1932ce93c67a4ab36e`.
- The fix is verified but not merged. Next role: Publish.

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

The previous exhaustive run `37441477077` killed this mutant through the
stored golden's bootstrap text hash. GH-72 moved golden comparison outside
the mutation oracle, exposing the missing direct rendering assertion.

The chosen resolution is an exact rendering regression test, not a
mutation-catalog classification:
`test_let_inline_if_value_is_not_parenthesized` requires
`let x = 1 if true else 0` without redundant parentheses.

Production code and the mutation catalog are unchanged.

## Verification

On code head `7654fe6`:
- ordinary push CI `37690789201` passed;
- exhaustive run `37692632581` passed ordinary tests and all 16 mutation
  shards.

These results precede this documentation update.

## Next

- Add the #81 changelog entry.
- Check ordinary CI after documentation updates.
- Publish the separate fix PR with `Closes #81`.
- Keep the issue open until the fix merges.
