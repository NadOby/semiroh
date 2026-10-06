# Task contract

Plan for #68, with issues #77 (contract and verifier) and #78 (CLAUDE.md
principle and trim). Everything here is **Provisional** until the owner
answers the decisions in section 5; section 1 is **Decided** (issue #68).

## 1. Principle (Decided)

What Review must verify mechanically is a repository check, printed in
ordinary CI step output with its reasons. Review keeps judgement: whether a
contract change is justified, whether a plan is right.

Today the mechanical checks are the lanes, the golden check (#72) and the
mutation catalog. Still manual in the roadmap: "the acceptance tests are
unchanged" (Publish) and "protected paths". This document mechanizes those.

## 2. The contract

One file per issue, written by Plan in `tests/contracts/GH-<n>.toml`:

    [protected]
    "tests/test_example.py" = "<git blob id>"
    "docs/example.md" = "<git blob id>"

- `protected` lists the acceptance tests and the specification Execute must
  not change, each pinned by git blob id (content, not commit), as
  `git rev-parse <commit>:<path>` gives it.
- Golden declarations stay where they are, `tests/golden_changes/GH-<n>.txt`.
  The verifier treats both directories alike: new files are the branch's
  contract, files in the base are history and cannot change or disappear.
  Names must match `GH-[0-9]+` plus the extension.
- Unknown tables or keys fail (fail closed). TOML is read with `tomllib`.

## 3. What the verifier checks

For every contract file added in the branch (absent from the merge base):

1. each protected path exists at HEAD with exactly its pinned blob; a
   changed or deleted path fails, printing pinned and actual blob;
2. each pin was true in the commit that added the contract (a wrong pin
   fails);
3. every commit in `base..HEAD` that touches `tests/contracts/` touches
   nothing else; a mixed commit fails;
4. every such commit after the one that added the file is an amendment and is
   listed (commit, file, path, old and new blob). Amendments pass; Review
   justifies them. This is how Execute legitimately re-pins a test, in a
   commit of its own, visible to the owner.

Contract files in the base are history: changing or deleting one fails.
With no new contract file the verifier only enforces history immutability.

## 4. Where it runs

- `tests/contract.py`, a CI step next to the golden check, also run locally
  (`python3 -m tests.contract --against main`). Base resolution (merge base,
  `--base` with `github.event.before` on a push to `main`) is shared with the
  golden check in one small module instead of copied.
- The check that judges a branch runs from the merge base's copy of
  `tests/contract.py` and `tests/golden_check.py`, in a worktree, against
  the head tree. A branch cannot weaken the checker that judges it; a checker
  change takes effect after it merges. When the base has no checker yet (the
  first merge), the head's runs.
- The golden check splits: the recorder stays in `tests/golden.py`; the
  comparison moves to `tests/golden_check.py`. A checker-only change then
  needs no `*`, and the recorder's `*` rule is unchanged. This resolves the
  limitation Review recorded on #72 (recorder and verifier shared a file).
- Ordinary tests (`tests/test_contract.py`, lane `cross-boundary`) cover the
  rules on planted values and on small temporary git repositories; the CI
  step covers the real history. The history-dependent checks are never
  ordinary tests, because they need a base.

## 5. Decisions for the owner

- **D-A. Contract format.** Recommended: separate files, `contracts/` for
  pins and `golden_changes/` for golden, as above (golden shipped and its
  history is immutable). Alternative: one TOML per issue holding both, which
  needs a migration of `golden_changes`.
- **D-B. Checker from the base.** Recommended: yes, section 4. Cost: a
  checker fix lands one merge late. Alternative: judge with the head's copy
  and rely on Review (the status quo).
- **D-C. Amendments.** Recommended: pass and list, as above. Alternative:
  fail unless the owner adds a label or an approval, which needs CI to read
  GitHub state and is not planned.

## 6. Acceptance for Execute (#77)

Each rule is shown failing on a planted violation, and each test fails on the
code without the rule:

- a protected file edited; deleted; a wrong pin; a mixed commit touching the
  contract; an amendment listed but passing; a base contract changed or
  deleted; a badly named or unknown-keyed file;
- the base's checker is the one executed (a head checker that always passes
  does not rescue a violating branch), shown on a temporary repository;
- the golden check passes unchanged on `main` (55 records) after the split,
  and `tests/golden.py` still needs `*` when the recorder changes.

Out of scope: binding the number in the name to the real issue (needs
GitHub state), the mutation carry-over check (#49), readable golden diffs
(#73).
