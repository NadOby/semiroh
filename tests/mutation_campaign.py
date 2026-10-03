"""Mutation campaign work-set construction and mutant-level sharding."""

from __future__ import annotations

import random
from pathlib import Path

from tests import mutation


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
