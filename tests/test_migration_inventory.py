"""Keep the migrated resource inventory reproducible against original provenance."""
import hashlib
import json
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]


class MigrationInventory(unittest.TestCase):
    def test_original_files_and_executable_bits(self):
        manifest = json.loads((REPO / 'docs/migration-provenance.json').read_text())
        expected = manifest['files']
        skill_roots = {Path(name).parts[1] for name in expected}
        actual = {p.relative_to(REPO).as_posix(): p for name in skill_roots
                  for p in (REPO / 'skills' / name).rglob('*') if p.is_file()}
        self.assertEqual(set(actual), set(expected))
        for name, entry in expected.items():
            with self.subTest(resource=name):
                self.assertEqual(hashlib.sha256(actual[name].read_bytes()).hexdigest(), entry['sha256'])
                self.assertEqual(bool(actual[name].stat().st_mode & 0o111), entry['executable'])
