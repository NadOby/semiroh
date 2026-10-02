"""Fail-closed tests for serialized mutation-catalog loading."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests import mutation
from tests.mutation_catalog import (
    CatalogError,
    load_catalog,
)


ENGINE_BLOB = "a" * 40
SOURCE_BLOB = "b" * 40
TARGET = "semiroh/bytecode.py"

VALID_CATALOG = f'''source_blob = "{SOURCE_BLOB}"

[[survivor]]
kind = "constant"
source = "may_activate: bool = False,"
occurrence = 0
classification = "unspecified"
reason = "fixture classification"
'''

SURVIVOR_BLOCK = '''
[[survivor]]
kind = "constant"
source = "may_activate: bool = False,"
occurrence = 0
classification = "unspecified"
reason = "duplicate fixture classification"
'''


def manifest(
    *targets: str,
    schema_version: int = 1,
    engine_blob: str = ENGINE_BLOB,
) -> str:
    target_lines = "".join(
        f'    "{target}",\n'
        for target in targets
    )

    return (
        f"schema_version = {schema_version}\n"
        f'engine_blob = "{engine_blob}"\n'
        "\n"
        "catalog_targets = [\n"
        f"{target_lines}"
        "]\n"
    )


@unittest.skipIf(
    mutation.in_mutation_subprocess(),
    "mutation catalog loading is harness metadata, not a semantic kill oracle",
)
class MutationCatalogLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(
        self,
        relative: str,
        text: str,
    ) -> None:
        path = self.root / relative
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_text(
            text,
            encoding="utf-8",
        )

    def write_manifest(
        self,
        *targets: str,
        schema_version: int = 1,
        engine_blob: str = ENGINE_BLOB,
    ) -> None:
        self.write(
            "manifest.toml",
            manifest(
                *targets,
                schema_version=schema_version,
                engine_blob=engine_blob,
            ),
        )

    def write_valid_catalog(self) -> None:
        self.write(
            "semiroh/bytecode.toml",
            VALID_CATALOG,
        )

    def test_valid_minimal_catalog_loads(self) -> None:
        self.write_manifest(TARGET)
        self.write_valid_catalog()

        engine_blob, source_blobs, survivors = load_catalog(
            self.root
        )

        self.assertEqual(
            engine_blob,
            ENGINE_BLOB,
        )
        self.assertEqual(
            source_blobs,
            {
                TARGET: SOURCE_BLOB,
            },
        )
        self.assertEqual(
            survivors,
            {
                (
                    TARGET,
                    "constant",
                    "may_activate: bool = False,",
                    0,
                ): (
                    "unspecified",
                    "fixture classification",
                ),
            },
        )

    def test_missing_manifest_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            CatalogError,
            "missing mutation catalog file",
        ):
            load_catalog(self.root)

    def test_unsupported_schema_version_is_rejected(
        self,
    ) -> None:
        self.write_manifest(
            schema_version=2,
        )

        with self.assertRaisesRegex(
            CatalogError,
            "unsupported schema_version 2",
        ):
            load_catalog(self.root)

    def test_missing_catalog_is_rejected(self) -> None:
        self.write_manifest(TARGET)

        with self.assertRaisesRegex(
            CatalogError,
            "missing catalogs: semiroh/bytecode.py",
        ):
            load_catalog(self.root)

    def test_unlisted_catalog_is_rejected(self) -> None:
        self.write_manifest()
        self.write_valid_catalog()

        with self.assertRaisesRegex(
            CatalogError,
            "unlisted catalogs: semiroh/bytecode.py",
        ):
            load_catalog(self.root)

    def test_unknown_manifest_target_is_rejected(
        self,
    ) -> None:
        self.write_manifest(
            "semiroh/not_a_target.py",
        )

        with self.assertRaisesRegex(
            CatalogError,
            "catalog_targets contains non-targets",
        ):
            load_catalog(self.root)

    def test_manifest_targets_must_be_sorted(self) -> None:
        self.write_manifest(
            "semiroh/canonical.py",
            "semiroh/bytecode.py",
        )

        with self.assertRaisesRegex(
            CatalogError,
            "catalog_targets must be sorted",
        ):
            load_catalog(self.root)

    def test_invalid_mirrored_path_is_rejected(self) -> None:
        self.write_manifest()
        self.write(
            "other/bytecode.toml",
            VALID_CATALOG,
        )

        with self.assertRaisesRegex(
            CatalogError,
            "catalog data must mirror a target path below semiroh/",
        ):
            load_catalog(self.root)

    def test_invalid_source_blob_is_rejected(self) -> None:
        self.write_manifest(TARGET)
        self.write(
            "semiroh/bytecode.toml",
            VALID_CATALOG.replace(
                SOURCE_BLOB,
                "not-a-blob",
            ),
        )

        with self.assertRaisesRegex(
            CatalogError,
            "source_blob must be a lowercase 40-character Git blob ID",
        ):
            load_catalog(self.root)

    def test_unexpected_catalog_field_is_rejected(
        self,
    ) -> None:
        self.write_manifest(TARGET)
        self.write(
            "semiroh/bytecode.toml",
            VALID_CATALOG.replace(
                "\n\n[[survivor]]",
                "\nunexpected = true\n\n[[survivor]]",
            ),
        )

        with self.assertRaisesRegex(
            CatalogError,
            "unexpected fields: unexpected",
        ):
            load_catalog(self.root)

    def test_boolean_occurrence_is_rejected(self) -> None:
        self.write_manifest(TARGET)
        self.write(
            "semiroh/bytecode.toml",
            VALID_CATALOG.replace(
                "occurrence = 0",
                "occurrence = true",
            ),
        )

        with self.assertRaisesRegex(
            CatalogError,
            "occurrence must be an integer",
        ):
            load_catalog(self.root)

    def test_invalid_classification_is_rejected(
        self,
    ) -> None:
        self.write_manifest(TARGET)
        self.write(
            "semiroh/bytecode.toml",
            VALID_CATALOG.replace(
                'classification = "unspecified"',
                'classification = "probably-fine"',
            ),
        )

        with self.assertRaisesRegex(
            CatalogError,
            "unknown classification",
        ):
            load_catalog(self.root)

    def test_duplicate_survivor_key_is_rejected(
        self,
    ) -> None:
        self.write_manifest(TARGET)
        self.write(
            "semiroh/bytecode.toml",
            VALID_CATALOG + SURVIVOR_BLOCK,
        )

        with self.assertRaisesRegex(
            CatalogError,
            "duplicate survivor key",
        ):
            load_catalog(self.root)

    def test_malformed_toml_is_rejected(self) -> None:
        self.write_manifest(TARGET)
        self.write(
            "semiroh/bytecode.toml",
            'source_blob = "unterminated\n',
        )

        with self.assertRaisesRegex(
            CatalogError,
            "invalid TOML",
        ):
            load_catalog(self.root)


if __name__ == "__main__":
    unittest.main()
