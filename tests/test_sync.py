import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


class SyncCommands(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='test-collection-sync-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'collection'
        self.root.mkdir()
        (self.root / 'skills').mkdir()
        shutil.copy2(REPO / 'justfile', self.root)
        shutil.copytree(REPO / 'scripts', self.root / 'scripts')
        (self.root / 'collection-sync.json').write_text(json.dumps({'version': 1, 'collection': 'example/collection', 'collections': {'example/collection': '.'}}))
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.home = self.base / 'home'
        self.home.mkdir()
        self.env = dict(os.environ)
        self.env['SKILLS_SYNC_PYTHON'] = sys.executable
        for key, value in {'HOME': self.home, 'CODEX_HOME': self.home / '.codex',
                           'CLAUDE_CONFIG_DIR': self.home / '.claude',
                           'XDG_STATE_HOME': self.home / '.local/state',
                           'XDG_CONFIG_HOME': self.home / '.config',
                           'XDG_CACHE_HOME': self.home / '.cache',
                           'XDG_DATA_HOME': self.home / '.local/share',
                           'npm_config_cache': self.home / '.npm', 'TMPDIR': self.base,
                           'GIT_CONFIG_GLOBAL': '/dev/null'}.items():
            self.env[key] = str(value)
        self.env['SKILLS_SYNC_INSTALLER'] = json.dumps([sys.executable, str(REPO / 'tests/fake_installer.py')])
        self.state = self.home / '.local/state/skill-collections/state.json'
        self.lock = self.home / '.agents/.skill-lock.json'

    def skill(self, name='alpha', body='Original'):
        folder = self.root / 'skills' / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Fixture skill.\n---\n{body}\n')
        (folder / 'resources').mkdir(exist_ok=True)
        (folder / 'resources/data.txt').write_text(body)
        script = folder / 'resources/run.sh'
        script.write_text('#!/bin/sh\nexit 0\n')
        script.chmod(0o755)
        return folder

    def run_sync(self, dry=False, code=0):
        run = subprocess.run(['just', '--justfile', str(self.root / 'justfile'), 'sync-dry-run' if dry else 'sync'], cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertEqual(run.returncode, code, run.stdout + run.stderr)
        return run.stdout + run.stderr

    def snapshot(self):
        return {str(p.relative_to(self.base)): ('link', os.readlink(p)) if p.is_symlink() else ('dir',) if p.is_dir() else ('file', p.read_bytes(), p.stat().st_mode) for p in self.base.rglob('*')}

    def installed(self, name='alpha'):
        return self.home / '.agents/skills' / name

    def test_first_update_new_and_idempotent(self):
        self.skill()
        self.run_sync()
        self.assertEqual((self.installed() / 'resources/data.txt').read_text(), 'Original')
        self.assertEqual((self.home / '.claude/skills/alpha').resolve(), self.installed())
        before = self.snapshot()
        self.assertIn('unchanged: alpha', self.run_sync())
        self.assertEqual(before, self.snapshot())
        self.skill(body='Changed')
        self.skill('beta')
        self.run_sync()
        self.assertEqual((self.installed() / 'resources/data.txt').read_text(), 'Changed')
        self.assertTrue(self.installed('beta').is_dir())

    def test_dry_run_and_empty_and_removal(self):
        self.assertIn('empty collection', self.run_sync(dry=True))
        self.skill()
        before = self.snapshot()
        self.assertIn('add: alpha', self.run_sync(dry=True))
        self.assertEqual(before, self.snapshot())
        self.run_sync()
        shutil.rmtree(self.root / 'skills/alpha')
        before = self.snapshot()
        self.assertIn('remove: alpha', self.run_sync(dry=True))
        self.assertEqual(before, self.snapshot())
        self.run_sync()
        self.assertFalse(self.installed().exists())

    def test_edited_and_independent(self):
        self.skill()
        self.run_sync()
        target = self.installed() / 'resources/data.txt'
        target.write_text('Local edit')
        self.skill('beta')
        self.assertIn('installed files were edited', self.run_sync(code=2))
        self.assertEqual(target.read_text(), 'Local edit')
        self.assertTrue(self.installed('beta').is_dir())

    def test_untracked_same_bytes_still_conflict(self):
        self.skill()
        self.run_sync()
        self.state.unlink()
        before = self.snapshot()
        self.assertIn('untracked/manual', self.run_sync(code=2))
        self.assertEqual(before, self.snapshot())

    def test_github_and_local_metadata_adoption(self):
        for source_type, source in [('github', 'example/collection'), ('local', str(self.root))]:
            with self.subTest(source_type=source_type):
                self.skill()
                self.run_sync()
                self.state.unlink()
                self.lock.write_text(json.dumps({'version': 3, 'skills': {'alpha': {'sourceType': source_type, 'source': source}}}))
                self.assertIn('adopt: alpha', self.run_sync())
                self.assertEqual(json.loads(self.state.read_text())['skills']['alpha']['owner'], 'example/collection')
                self.assertNotIn('alpha', json.loads(self.lock.read_text())['skills'])

    def test_other_github_source_conflicts(self):
        self.skill()
        self.run_sync()
        self.lock.write_text(json.dumps({'version': 3, 'skills': {'alpha': {'sourceType': 'github', 'source': 'other/repository'}}}))
        before = self.snapshot()
        self.run_sync(code=2)
        self.assertEqual(before, self.snapshot())

    def test_old_github_copy_cannot_prove_no_edits(self):
        self.skill()
        self.run_sync()
        self.state.unlink()
        self.lock.write_text(json.dumps({'version': 3, 'skills': {'alpha': {'sourceType': 'github', 'source': 'example/collection'}}}))
        self.skill(body='New source')
        before = self.snapshot()
        self.run_sync(code=2)
        self.assertEqual(before, self.snapshot())

    def test_installer_failures_leave_previous_files_and_ownership(self):
        self.skill()
        self.run_sync()
        self.skill(body='Changed')
        self.skill('beta')
        for failure in ('partial', 'verification', 'link'):
            with self.subTest(failure=failure):
                self.env['TEST_INSTALLER_FAILURE'] = failure
                before = self.snapshot()
                self.run_sync(code=1)
                self.assertEqual(before, self.snapshot())

    def test_incomplete_scan_and_malformed_state_leave_all_unchanged(self):
        self.skill()
        self.run_sync()
        (self.root / 'skills/broken').mkdir()
        before = self.snapshot()
        self.run_sync(code=1)
        self.assertEqual(before, self.snapshot())
        (self.root / 'skills/broken').rmdir()
        self.state.write_text('{broken json')
        before = self.snapshot()
        self.run_sync(code=1)
        self.assertEqual(before, self.snapshot())

    def test_malformed_installer_metadata_and_symlink_parent(self):
        self.skill()
        self.run_sync()
        self.lock.write_text('{"version": 99, "skills": {}}')
        before = self.snapshot()
        self.run_sync(code=1)
        self.assertEqual(before, self.snapshot())
        self.lock.unlink()
        original = self.home / '.agents'
        moved = self.home / 'moved-agents'
        original.rename(moved)
        original.symlink_to(moved)
        before = self.snapshot()
        self.run_sync(code=1)
        self.assertEqual(before, self.snapshot())

    def test_missing_container_and_missing_git_fail_closed(self):
        shutil.rmtree(self.root / 'skills')
        before = self.snapshot()
        self.run_sync(code=1)
        self.assertEqual(before, self.snapshot())
        (self.root / 'skills').mkdir()
        shutil.rmtree(self.root / '.git')
        before = self.snapshot()
        self.run_sync(code=1)
        self.assertEqual(before, self.snapshot())

    def test_link_escape_and_legacy_shadow_are_preserved(self):
        self.skill()
        self.run_sync()
        link = self.home / '.claude/skills/alpha'
        link.unlink()
        link.symlink_to(self.root / 'skills/alpha')
        before = self.snapshot()
        self.run_sync(code=2)
        self.assertEqual(before, self.snapshot())
        link.unlink()
        link.symlink_to(self.installed())
        shadow = self.home / '.codex/skills/alpha'
        shadow.mkdir(parents=True)
        (shadow / 'SKILL.md').write_text('User skill')
        before = self.snapshot()
        self.run_sync(code=2)
        self.assertEqual(before, self.snapshot())

    def test_source_symlink_rejected(self):
        folder = self.skill()
        (folder / 'escape').symlink_to('/etc/passwd')
        before = self.snapshot()
        self.run_sync(code=1)
        self.assertEqual(before, self.snapshot())


if __name__ == '__main__':
    unittest.main()
