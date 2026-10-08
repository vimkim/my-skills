"""Keep the migrated resource inventory reproducible against original provenance."""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
MIGRATION_REVISION = '8a2fe861b7cba354684eb3e3095f1ad83961af24'


class MigrationInventory(unittest.TestCase):
    repo = REPO
    migration_revision = MIGRATION_REVISION
    skill_roots = tuple('skills/' + name for name in (
        'gh-pr-comments-all', 'resolve-greptile-comments', 'markdown-write',
        'question-socratically', 'track-work'))

    def expected_files(self):
        manifest = json.loads((self.repo / 'docs/migration-provenance.json').read_text())
        return manifest['files']

    def git(self, *args):
        try:
            return subprocess.check_output(['git', '-C', str(self.repo), *args],
                                           stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            self.fail(
                f'Cannot read migration snapshot {self.migration_revision}. '
                'Use a Git checkout containing the import commit; for a shallow '
                'clone, run git fetch --unshallow. Source archives do not contain '
                f'this evidence. Git reported: {error.output.decode().strip()}')

    def test_original_files_and_executable_bits(self):
        expected = self.expected_files()
        records = self.git('ls-tree', '-rz', self.migration_revision, '--', *self.skill_roots)
        actual = {}
        for record in filter(None, records.split(b'\0')):
            metadata, name = record.split(b'\t', 1)
            mode, kind, oid = metadata.decode().split()
            actual[name.decode()] = (mode, kind, oid)
        self.assertEqual(set(actual), set(expected), 'Historical resource inventory')
        for name, entry in expected.items():
            with self.subTest(resource=name):
                mode, kind, oid = actual[name]
                self.assertEqual(kind, 'blob', f'{name}: regular file')
                self.assertIn(mode, ('100644', '100755'), f'{name}: regular file mode')
                content = self.git('cat-file', 'blob', oid)
                self.assertEqual(hashlib.sha256(content).hexdigest(), entry['sha256'],
                                 f'{name}: sha256')
                self.assertEqual(mode == '100755', entry['executable'],
                                 f'{name}: executable')

    def test_current_files_and_executable_bits(self):
        expected = self.expected_files()
        actual = {p.relative_to(self.repo).as_posix(): p for root in self.skill_roots
                  for p in (self.repo / root).rglob('*') if p.is_file()}
        self.assertEqual(set(actual), set(expected), 'Current resource inventory')
        for name, entry in expected.items():
            with self.subTest(resource=name):
                self.assertEqual(bool(actual[name].stat().st_mode & 0o111), entry['executable'],
                                 f'{name}: executable')


class MigrationInventoryRegressions(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='test-migration-inventory-')
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name) / 'collection'
        self.repo.mkdir()
        self.git('init', '-q')
        self.resources = {
            'skills/example/SKILL.md': (b'Original instructions\n', False),
            'skills/example/scripts/check.py': (b'#!/usr/bin/env python3\n', True),
            'skills/other/SKILL.md': (b'Second migrated skill\n', False),
        }
        self.manifest = {'files': {}}
        for name, (content, executable) in self.resources.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(0o755 if executable else 0o644)
            self.manifest['files'][name] = {
                'sha256': hashlib.sha256(content).hexdigest(),
                'executable': executable,
            }
        (self.repo / 'docs').mkdir()
        self.write_manifest()
        self.original_revision = self.commit()

    def git(self, *args):
        return subprocess.check_output([
            'git', '-C', str(self.repo), '-c', 'user.name=Migration test',
            '-c', 'user.email=migration-test@example.invalid',
            '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null',
            *args,
        ], stderr=subprocess.STDOUT).decode().strip()

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'Fixture revision')
        return self.git('rev-parse', 'HEAD')

    def write_manifest(self):
        (self.repo / 'docs/migration-provenance.json').write_text(
            json.dumps(self.manifest))

    def run_inventory(self, method='test_original_files_and_executable_bits',
                      revision=None, repo=None):
        case = MigrationInventory(method)
        case.repo = repo or self.repo
        case.migration_revision = revision or self.original_revision
        case.skill_roots = ('skills/example', 'skills/other')
        result = unittest.TestResult()
        case.run(result)
        return result

    def assert_passes(self, result):
        self.assertTrue(result.wasSuccessful(), str(result.errors + result.failures))

    def assert_rejected(self, result, message):
        self.assertFalse(result.errors, str(result.errors))
        self.assertTrue(result.failures, 'Damaged evidence unexpectedly passed')
        self.assertIn(message, '\n'.join(detail for _, detail in result.failures))

    def test_later_content_edit_preserves_original_fingerprints(self):
        path = self.repo / 'skills/example/SKILL.md'
        path.write_bytes(b'Intentionally maintained instructions\n')
        maintained_revision = self.commit()
        self.assertNotEqual(maintained_revision, self.original_revision)
        self.assert_passes(self.run_inventory())
        self.assert_passes(self.run_inventory('test_current_files_and_executable_bits'))

    def test_changed_historical_content_is_rejected(self):
        (self.repo / 'skills/example/SKILL.md').write_bytes(b'Damaged import\n')
        self.assert_rejected(self.run_inventory(revision=self.commit()), 'sha256')

    def test_changed_provenance_checksum_is_rejected(self):
        self.manifest['files']['skills/example/SKILL.md']['sha256'] = '0' * 64
        self.write_manifest()
        self.assert_rejected(self.run_inventory(), 'sha256')

    def test_omitted_skill_in_provenance_is_rejected(self):
        self.manifest['files'] = {
            name: entry for name, entry in self.manifest['files'].items()
            if not name.startswith('skills/example/')}
        self.write_manifest()
        self.assert_rejected(self.run_inventory(), 'inventory')
        self.assert_rejected(
            self.run_inventory('test_current_files_and_executable_bits'), 'inventory')

    def test_missing_or_extra_historical_resource_is_rejected(self):
        script = self.repo / 'skills/example/scripts/check.py'
        script.unlink()
        self.assert_rejected(self.run_inventory(revision=self.commit()), 'inventory')
        content, executable = self.resources['skills/example/scripts/check.py']
        script.write_bytes(content)
        script.chmod(0o755 if executable else 0o644)
        (self.repo / 'skills/example/extra.txt').write_bytes(b'Unexpected resource\n')
        self.assert_rejected(self.run_inventory(revision=self.commit()), 'inventory')

    def test_changed_historical_executable_bit_is_rejected(self):
        (self.repo / 'skills/example/scripts/check.py').chmod(0o644)
        self.assert_rejected(self.run_inventory(revision=self.commit()), 'executable')

    def test_missing_or_extra_current_resource_is_rejected(self):
        method = 'test_current_files_and_executable_bits'
        script = self.repo / 'skills/example/scripts/check.py'
        script.unlink()
        self.assert_rejected(self.run_inventory(method), 'inventory')
        content, executable = self.resources['skills/example/scripts/check.py']
        script.write_bytes(content)
        script.chmod(0o755 if executable else 0o644)
        (self.repo / 'skills/example/extra.txt').write_bytes(b'Unexpected resource\n')
        self.assert_rejected(self.run_inventory(method), 'inventory')

    def test_changed_current_executable_bit_is_rejected(self):
        for name, (_, executable) in self.resources.items():
            with self.subTest(resource=name):
                path = self.repo / name
                path.chmod(0o644 if executable else 0o755)
                self.assert_rejected(
                    self.run_inventory('test_current_files_and_executable_bits'), 'executable')
                path.chmod(0o755 if executable else 0o644)

    def test_shallow_checkout_reports_missing_import_history(self):
        (self.repo / 'skills/example/SKILL.md').write_bytes(b'Maintained instructions\n')
        self.commit()
        shallow = self.repo.parent / 'shallow'
        subprocess.run(['git', 'clone', '-q', '--depth', '1', self.repo.as_uri(),
                        str(shallow)], check=True, capture_output=True)
        self.assert_rejected(self.run_inventory(repo=shallow), 'git fetch --unshallow')
        subprocess.run(['git', '-C', str(shallow), 'fetch', '-q', '--unshallow'],
                       check=True, capture_output=True)
        self.assert_passes(self.run_inventory(repo=shallow))
