#!/usr/bin/env python3
"""Verify actual five-skill migration in disposable repositories and homes.

Usage: python3 tests/check_migration.py OLD_CHECKOUT [--real]
The old checkout may still contain the five original sources or already have
removed them. Reconstruct the pre-migration sources from the destination.
--real uses pinned skills CLI (SKILLS_REAL_INSTALLER may select inspected CLI).
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from test_sync import REPO, SyncCommands

NAMES = ('gh-pr-comments-all', 'resolve-greptile-comments', 'markdown-write',
         'question-socratically', 'track-work')
OLD = Path(sys.argv[1]).resolve()
REAL = '--real' in sys.argv[2:]


def files(root):
    return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mode & 0o111)
            for p in root.rglob('*') if p.is_file()}


class Migration(unittest.TestCase):
    setUp = SyncCommands.setUp
    run_sync = SyncCommands.run_sync
    snapshot = SyncCommands.snapshot
    installed = SyncCommands.installed

    def prepare(self):
        self.old = self.base / 'old'
        self.old.mkdir()
        tracked = subprocess.check_output(['git', '-C', str(OLD), 'ls-files', '-z']).decode().split('\0')
        for relative in filter(None, tracked):
            source = OLD / relative
            if relative.split('/')[0] in NAMES or not source.exists():
                continue
            target = self.old / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target, follow_symlinks=False)
        subprocess.run(['git', 'init', '-q', str(self.old)], check=True)
        self.assertEqual((REPO / 'scripts/sync_skills.py').read_bytes(),
                         (self.old / 'tools/sync_skills.py').read_bytes())
        config = json.loads((REPO / 'collection-sync.json').read_text())
        config['collections'] = {'vimkim/my-skills': str(self.root),
                                 'vimkim/my-cubrid-skills': str(self.old)}
        for path, owner, container in ((self.root, 'vimkim/my-skills', 'skills'),
                                       (self.old, 'vimkim/my-cubrid-skills', '.')):
            config.update(collection=owner, skill_root=container)
            (path / 'collection-sync.json').write_text(json.dumps(config))
        for name in NAMES:
            shutil.copytree(REPO / 'skills' / name, self.old / name)
        self.assertTrue((self.old / 'daily-schedule/SKILL.md').is_file())
        self.assertTrue((self.old / 'my-cubrid-skills-create/SKILL.md').is_file())
        if REAL:
            self.env['SKILLS_SYNC_INSTALLER'] = os.environ.get('SKILLS_REAL_INSTALLER',
                json.dumps(['npx', '--yes', 'skills@1.7.0']))

    def run_old(self, **kwargs):
        new = self.root
        self.root = self.old
        try:
            return self.run_sync(**kwargs)
        finally:
            self.root = new

    def verify(self, transferred=True):
        state = json.loads(self.state.read_text())
        for name in NAMES:
            self.assertEqual(files(REPO / 'skills' / name), files(self.installed(name)))
            self.assertEqual((self.home / '.claude/skills' / name).resolve(), self.installed(name))
            if transferred:
                self.assertEqual(state['skills'][name]['owner'], 'vimkim/my-skills')
        for name in ('daily-schedule', 'my-cubrid-skills-create'):
            self.assertEqual(files(self.old / name), files(self.installed(name)))
            self.assertEqual(state['skills'][name]['owner'], 'vimkim/my-cubrid-skills')

    def test_conflicts_before_transfer(self):
        self.prepare()
        self.run_old()
        for name in NAMES:
            shutil.copytree(self.old / name, self.root / 'skills' / name)
        target = self.installed('markdown-write') / 'scripts/check_copyparty_markdown.py'
        target.write_text(target.read_text() + '\n# User edit before transfer\n')
        edited = files(self.installed('markdown-write'))
        self.lock.write_text(json.dumps({'version': 3, 'skills': {
            'track-work': {'sourceType': 'github', 'source': 'other/owner'}}}))
        conflict = files(self.installed('track-work'))
        before = self.snapshot()
        self.run_sync(dry=True, code=2)
        self.assertEqual(before, self.snapshot())
        self.run_sync(code=2)
        self.run_old()
        self.assertEqual(edited, files(self.installed('markdown-write')))
        self.assertEqual(conflict, files(self.installed('track-work')))
        state = json.loads(self.state.read_text())['skills']
        for name in NAMES:
            self.assertEqual(state[name]['owner'], 'vimkim/my-cubrid-skills'
                if name in ('markdown-write', 'track-work') else 'vimkim/my-skills')

    def scenario(self, order, ownership):
        self.prepare()
        self.run_old()
        self.verify(transferred=False)
        for name in NAMES:
            shutil.copytree(self.old / name, self.root / 'skills' / name)
        if ownership != 'state':
            state = json.loads(self.state.read_text())
            for name in NAMES:
                del state['skills'][name]
            self.state.write_text(json.dumps(state))
            self.lock.write_text(json.dumps({'version': 3, 'skills': {
                n: {'sourceType': ownership, 'source': 'vimkim/my-cubrid-skills'
                    if ownership == 'github' else str(self.old)} for n in NAMES}}))
        before = self.snapshot()
        self.run_sync(dry=True)
        self.run_old(dry=True)
        self.assertEqual(before, self.snapshot())
        if order == 'old-first':
            self.run_old()
        self.run_sync()
        self.verify()
        # Original sources remain available until destination installation is proven.
        for name in NAMES:
            shutil.rmtree(self.old / name)
        self.run_old()
        self.verify()
        before = self.snapshot()
        self.run_sync()
        self.run_old()
        self.run_sync(dry=True)
        self.run_old(dry=True)
        self.assertEqual(before, self.snapshot())
        # Post-transfer edits and third-party ownership are preserved on both interfaces.
        target = self.installed('markdown-write') / 'scripts/check_copyparty_markdown.py'
        target.write_text(target.read_text() + '\n# Installed user edit\n')
        lock = {'version': 3, 'skills': {'track-work': {'sourceType': 'github', 'source': 'other/owner'}}}
        self.lock.write_text(json.dumps(lock))
        before = self.snapshot()
        self.run_sync(dry=True, code=2)
        self.run_sync(code=2)
        self.run_old()
        self.assertEqual(before, self.snapshot())


for order in ('old-first', 'new-first'):
    for ownership in (('state',) if REAL else ('state', 'github', 'local')):
        def case(self, order=order, ownership=ownership):
            self.scenario(order, ownership)
        setattr(Migration, 'test_' + order.replace('-', '_') + '_' + ownership, case)

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Migration)
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
