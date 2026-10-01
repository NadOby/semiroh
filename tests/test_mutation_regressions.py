"""Permanent regressions for semantic gaps found by mutation testing."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from semiroh import EntityID, State, Value, canonicalize
from semiroh.closures import Closure, closure_value


ENTITY = EntityID("entity")
OTHER = EntityID("other")
OWNER = EntityID("owner")
BODY = EntityID("body")


class SemanticRecordImmutabilityTests(unittest.TestCase):
    def test_public_pinned_semantic_records_are_immutable(self) -> None:
        value = Value.create(ENTITY, 1)
        state = State.create({
            ENTITY: value,
        })
        reference = state.reference(ENTITY)

        cases = (
            (value, "content", 2),
            (state, "values", {}),
            (reference, "entity", OTHER),
        )

        for record, field, replacement in cases:
            with self.subTest(record=type(record).__name__):
                with self.assertRaises(FrozenInstanceError):
                    setattr(record, field, replacement)


class ClosureCanonicalRegressionTests(unittest.TestCase):
    def test_canonical_closure_decodes_primitive_params_and_captures(
        self,
    ) -> None:
        original = Closure(
            OWNER,
            BODY,
            ("x",),
            (("n", 4),),
        )

        decoded = closure_value(canonicalize(original))

        self.assertEqual(decoded, original)


if __name__ == "__main__":
    unittest.main()
