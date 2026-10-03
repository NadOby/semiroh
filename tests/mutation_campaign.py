"""Mutation campaign work selection, sharding and exact replay."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from tests import mutation
from tests import mutation_oracle


def build_work_set(
    root: Path,
    targets: tuple[str, ...],
    count: int,
    seed: int,
    batch: int = 0,
) -> tuple[mutation.Mutant, ...]:
    """Build the exact selected mutation work set.

    Selection retains the Task 18 semantics: each target independently uses
    mutation.sample() with the requested count, seed and batch. Only after that
    complete unsharded set exists is it shuffled for mutant-level sharding.
    """

    selected: list[mutation.Mutant] = []

    for target in targets:
        source = (root / target).read_text()
        descriptions = mutation.site_descriptions(
            source,
            target,
        )
        indexes = mutation.sample(
            source,
            count,
            seed,
            batch=batch,
        )

        selected.extend(
            descriptions[index]
            for index in indexes
        )

    keys = [
        mutant.key
        for mutant in selected
    ]

    if len(keys) != len(set(keys)):
        raise RuntimeError(
            "selected mutation work set contains duplicate keys"
        )

    shuffled = list(selected)
    random.Random(seed).shuffle(shuffled)

    return tuple(shuffled)


def shard_work(
    work: tuple[mutation.Mutant, ...],
    shards: int,
    shard: int,
) -> tuple[mutation.Mutant, ...]:
    """Return one balanced deterministic mutant shard.

    ``work`` is already deterministically shuffled. Round-robin assignment
    therefore changes only ownership of mutants, never the selected set.
    """

    if shards < 1:
        raise ValueError(
            "SEMIROH_MUTATE_SHARDS must be a positive integer"
        )

    if shard < 0 or shard >= shards:
        raise ValueError(
            "SEMIROH_MUTATE_SHARD must be between 0 and "
            "SEMIROH_MUTATE_SHARDS - 1"
        )

    return tuple(
        mutant
        for index, mutant in enumerate(work)
        if index % shards == shard
    )


def work_for_shard(
    root: Path,
    targets: tuple[str, ...],
    count: int,
    seed: int,
    batch: int,
    shards: int,
    shard: int,
) -> tuple[mutation.Mutant, ...]:
    """Build the unsharded selection, then return one mutant-level shard."""

    return shard_work(
        build_work_set(
            root,
            targets,
            count,
            seed,
            batch,
        ),
        shards,
        shard,
    )


def resolve_exact_key(
    root: Path,
    key: mutation.MutationKey,
    source_blob: str,
    engine_blob: str,
) -> mutation.Mutant:
    """Resolve one exact mutation key under pinned source and engine versions."""

    engine_path = root / "tests" / "mutation.py"

    if not engine_path.is_file():
        raise ValueError(
            "reviewed mutation engine is missing: tests/mutation.py"
        )

    current_engine = mutation.git_blob_id(
        engine_path.read_bytes()
    )

    if current_engine != engine_blob:
        raise ValueError(
            "mutation engine version mismatch: "
            f"expected {engine_blob}, got {current_engine}"
        )

    target = key[0]
    target_path = root / target

    if not target_path.is_file():
        raise ValueError(
            f"mutation target is missing: {target}"
        )

    current_source = mutation.git_blob_id(
        target_path.read_bytes()
    )

    if current_source != source_blob:
        raise ValueError(
            f"{target}: source version mismatch: "
            f"expected {source_blob}, got {current_source}"
        )

    source = target_path.read_text()
    matches = [
        mutant
        for mutant in mutation.site_descriptions(
            source,
            target,
        )
        if mutant.key == key
    ]

    if len(matches) != 1:
        raise ValueError(
            f"{target}: exact mutation key resolved to "
            f"{len(matches)} sites, expected exactly one"
        )

    return matches[0]


def replay_exact(
    root: Path,
    key: mutation.MutationKey,
    source_blob: str,
    engine_blob: str,
    command: list[str] | None = None,
) -> tuple[mutation.Mutant, bool]:
    """Run one exact pinned mutation and return its killed/survived outcome."""

    selected = resolve_exact_key(
        root,
        key,
        source_blob,
        engine_blob,
    )
    oracle = (
        mutation_oracle.command()
        if command is None
        else command
    )

    executed, dead = mutation.killed(
        root,
        selected.target,
        selected.index,
        oracle,
    )

    if executed.key != selected.key:
        raise RuntimeError(
            "resolved mutation key changed during replay"
        )

    return executed, dead


def _parse_key(raw: str) -> mutation.MutationKey:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "mutation key must be valid JSON"
        ) from exc

    if (
        not isinstance(value, list)
        or len(value) != 4
        or not isinstance(value[0], str)
        or not isinstance(value[1], str)
        or not isinstance(value[2], str)
        or not isinstance(value[3], int)
        or isinstance(value[3], bool)
        or value[3] < 0
    ):
        raise ValueError(
            "mutation key must be "
            '[target, kind, source, occurrence]'
        )

    return (
        value[0],
        value[1],
        value[2],
        value[3],
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mutation campaign utilities",
    )
    subparsers = parser.add_subparsers(
        dest="action",
        required=True,
    )

    replay = subparsers.add_parser(
        "replay",
        help="replay one exact pinned mutation key",
    )
    replay.add_argument(
        "--key-json",
        required=True,
        help=(
            "JSON mutation key: "
            '[target, kind, source, occurrence]'
        ),
    )
    replay.add_argument(
        "--source-blob",
        required=True,
        help="expected Git blob id of the mutation target",
    )
    replay.add_argument(
        "--engine-blob",
        required=True,
        help="expected Git blob id of tests/mutation.py",
    )
    replay.add_argument(
        "--root",
        default=str(mutation.ROOT),
        help="repository root; defaults to the current repository",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.action != "replay":
        parser.error(
            f"unsupported action: {args.action}"
        )

    try:
        key = _parse_key(args.key_json)
        mutant, dead = replay_exact(
            Path(args.root),
            key,
            args.source_blob,
            args.engine_blob,
        )
    except (ValueError, RuntimeError) as exc:
        print(
            f"mutation replay failed: {exc}",
            file=sys.stderr,
        )
        return 2

    outcome = "killed" if dead else "survived"

    print(
        f"{outcome}: "
        f"{mutant.target}:site-{mutant.index}:"
        f"line-{mutant.line} "
        f"{mutant.kind}[{mutant.occurrence}]: "
        f"{mutant.text}",
        flush=True,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
