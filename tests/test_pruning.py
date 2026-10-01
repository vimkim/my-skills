import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
import test_sync


class PruningCommands(unittest.TestCase):
    setUp = test_sync.SyncCommands.setUp
    skill = test_sync.SyncCommands.skill
    run_sync = test_sync.SyncCommands.run_sync
    snapshot = test_sync.SyncCommands.snapshot
    installed = test_sync.SyncCommands.installed

    def recovery(self):
        return list((self.state.parent / 'recovery').glob('removed-*'))

    def restore(self, folder, dry=False, code=0):
        result = subprocess.run(['just', '--justfile', str(self.root / 'justfile'),
                                 'sync-dry-run' if dry else 'sync', '--restore', str(folder)],
                                cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def test_remove_restore_content_state_link_and_executable(self):
        self.skill()
        self.run_sync()
        baseline = json.loads(self.state.read_text())
        saved_lock = {'version': 3, 'skills': {
            'alpha': {'sourceType': 'github', 'source': 'example/collection'},
            'unrelated': {'sourceType': 'github', 'source': 'other/repo'}}}
        self.lock.write_text(json.dumps(saved_lock))
        shutil.rmtree(self.root / 'skills/alpha')
        output = self.run_sync()
        self.assertIn('recovery:', output)
        self.assertFalse(self.installed().exists())
        folder, = self.recovery()
        before = self.snapshot()
        self.restore(folder, dry=True)
        self.assertEqual(before, self.snapshot())
        self.restore(folder)
        self.assertEqual(json.loads(self.state.read_text()), baseline)
        self.assertEqual(json.loads(self.lock.read_text()), saved_lock)
        self.assertEqual((self.installed() / 'resources/data.txt').read_text(), 'Original')
        self.assertEqual((self.home / '.claude/skills/alpha').resolve(), self.installed())
        subprocess.run([str(self.installed() / 'resources/run.sh')], check=True)
        before = self.snapshot()
        self.restore(folder, code=1)
        self.assertEqual(before, self.snapshot())

    def test_rename_and_repeat_empty(self):
        self.skill()
        self.run_sync()
        shutil.rmtree(self.root / 'skills/alpha')
        self.skill('beta')
        self.run_sync()
        self.assertFalse(self.installed().exists())
        self.assertTrue(self.installed('beta').exists())
        shutil.rmtree(self.root / 'skills/beta')
        self.run_sync()
        before = self.snapshot()
        self.assertIn('empty collection', self.run_sync())
        self.assertEqual(before, self.snapshot())

    def test_install_or_verification_failure_prevents_any_prune(self):
        self.skill()
        self.run_sync()
        shutil.rmtree(self.root / 'skills/alpha')
        self.skill('beta')
        for failure in ('partial', 'verification', 'link'):
            with self.subTest(failure=failure):
                self.env['TEST_INSTALLER_FAILURE'] = failure
                before = self.snapshot()
                self.run_sync(code=1)
                self.assertEqual(before, self.snapshot())
                self.assertTrue(self.installed().exists())

    def test_edited_manual_and_third_party_not_pruned(self):
        self.skill()
        self.skill('manual')
        self.skill('third-party')
        self.run_sync()
        (self.installed() / 'resources/data.txt').write_text('User edit')
        state = json.loads(self.state.read_text())
        del state['skills']['manual']
        self.state.write_text(json.dumps(state))
        self.lock.write_text(json.dumps({'version': 3, 'skills': {'third-party': {'sourceType': 'github', 'source': 'another/owner'}}}))
        for name in ('alpha', 'manual', 'third-party'):
            shutil.rmtree(self.root / 'skills' / name)
        before = self.snapshot()
        output = self.run_sync(code=2)
        self.assertIn('removal skipped', output)
        self.assertEqual(before, self.snapshot())

    def peer(self):
        peer = self.base / 'peer'
        peer.mkdir()
        (peer / 'skills').mkdir()
        shutil.copy2(self.root / 'justfile', peer)
        shutil.copytree(self.root / 'scripts', peer / 'scripts')
        subprocess.run(['git', 'init', '-q', str(peer)], check=True)
        collections = {'vimkim/my-skills': str(self.root), 'vimkim/my-cubrid-skills': str(peer)}
        names = ['gh-pr-comments-all', 'resolve-greptile-comments', 'markdown-write', 'question-socratically', 'track-work']
        transfers = [{'name': n, 'from': 'vimkim/my-cubrid-skills', 'to': 'vimkim/my-skills'} for n in names]
        for root, owner in [(self.root, 'vimkim/my-skills'), (peer, 'vimkim/my-cubrid-skills')]:
            (root / 'collection-sync.json').write_text(json.dumps({'version': 1, 'collection': owner, 'collections': collections, 'migrations': transfers}))
        return peer, names

    def run_peer(self, peer, **kwargs):
        original = self.root
        self.root = peer
        try:
            return self.run_sync(**kwargs)
        finally:
            self.root = original

    def test_missing_peer_blocks_prune_but_independent_add_proceeds(self):
        peer, _ = self.peer()
        self.skill()
        self.run_sync()
        shutil.rmtree(self.root / 'skills/alpha')
        shutil.rmtree(peer)
        self.skill('beta')
        output = self.run_sync(code=2)
        self.assertIn('incomplete collection evidence', output)
        self.assertTrue(self.installed().exists())
        self.assertTrue(self.installed('beta').exists())
        self.assertFalse((self.state.parent / 'recovery').exists())

    def test_incomplete_peer_and_malformed_state_never_delete(self):
        peer, _ = self.peer()
        self.skill()
        self.run_sync()
        shutil.rmtree(self.root / 'skills/alpha')
        (peer / 'skills/broken').mkdir()
        before = self.snapshot()
        self.run_sync(code=2)
        self.assertEqual(before, self.snapshot())
        (peer / 'skills/broken').rmdir()
        self.state.write_text('{"version":1,"skills":{"alpha":{"owner":"vimkim/my-skills"}}}')
        before = self.snapshot()
        self.run_sync(code=1)
        self.assertEqual(before, self.snapshot())

    def test_all_five_transfers_both_orders_and_source_types(self):
        peer, names = self.peer()
        for order in ('old-first', 'new-first'):
            for ownership in ('state', 'github', 'local'):
                with self.subTest(order=order, ownership=ownership):
                    for root in (self.root, peer):
                        shutil.rmtree(root / 'skills')
                        (root / 'skills').mkdir()
                    shutil.rmtree(self.home)
                    self.home.mkdir()
                    for name in names:
                        self.skill(name)
                        shutil.copytree(self.root / 'skills' / name, peer / 'skills' / name)
                        shutil.rmtree(self.root / 'skills' / name)
                    self.run_peer(peer)
                    for name in names:
                        shutil.copytree(peer / 'skills' / name, self.root / 'skills' / name)
                    if ownership != 'state':
                        self.state.unlink()
                        self.lock.write_text(json.dumps({'version': 3, 'skills': {n: {'sourceType': ownership, 'source': 'vimkim/my-cubrid-skills' if ownership == 'github' else str(peer)} for n in names}}))
                    # Destination is verified before source removal. Old first must preserve.
                    if order == 'old-first':
                        self.assertIn('preserve:', self.run_peer(peer))
                    self.assertIn('transfer:', self.run_sync())
                    for name in names:
                        shutil.rmtree(peer / 'skills' / name)
                    self.run_peer(peer)
                    state = json.loads(self.state.read_text())
                    for name in names:
                        self.assertTrue(self.installed(name).exists())
                        self.assertEqual(state['skills'][name]['owner'], 'vimkim/my-skills')
                    before = self.snapshot()
                    self.run_sync()
                    self.run_peer(peer)
                    self.assertEqual(before, self.snapshot())

    def test_former_source_removed_first_and_edited_transfer(self):
        peer, names = self.peer()
        name = names[0]
        self.skill(name)
        shutil.copytree(self.root / 'skills' / name, peer / 'skills' / name)
        shutil.rmtree(self.root / 'skills' / name)
        self.run_peer(peer)
        shutil.move(str(peer / 'skills' / name), self.root / 'skills' / name)
        self.assertIn('preserve:', self.run_peer(peer))
        (self.installed(name) / 'resources/data.txt').write_text('Edited')
        before = self.snapshot()
        self.assertIn('cannot verify', self.run_sync(code=2))
        self.assertEqual(before, self.snapshot())
        (self.installed(name) / 'resources/data.txt').write_text('Original')
        self.run_sync()
        self.run_peer(peer)
        self.assertTrue(self.installed(name).exists())

    def test_top_level_incomplete_source_is_not_deletion(self):
        cfg = json.loads((self.root / 'collection-sync.json').read_text())
        cfg['skill_root'] = '.'
        (self.root / 'collection-sync.json').write_text(json.dumps(cfg))
        self.skill()
        shutil.move(str(self.root / 'skills/alpha'), self.root / 'alpha')
        self.run_sync()
        (self.root / 'alpha/SKILL.md').unlink()
        before = self.snapshot()
        self.assertIn('incomplete source', self.run_sync(code=2))
        self.assertEqual(before, self.snapshot())

    def test_unapproved_migration_and_corrupt_recovery_fail_closed(self):
        self.skill()
        self.run_sync()
        shutil.rmtree(self.root / 'skills/alpha')
        self.run_sync()
        folder, = self.recovery()
        (folder / 'skills/alpha/resources/data.txt').write_text('Corrupt')
        before = self.snapshot()
        self.restore(folder, code=1)
        self.assertEqual(before, self.snapshot())
        cfg = json.loads((self.root / 'collection-sync.json').read_text())
        cfg['migrations'] = [{'name': 'alpha', 'from': 'arbitrary', 'to': 'example/collection'}]
        (self.root / 'collection-sync.json').write_text(json.dumps(cfg))
        before = self.snapshot()
        self.run_sync(code=1)
        self.assertEqual(before, self.snapshot())

    def test_dangling_source_and_recovery_parent_symlink_fail_closed(self):
        self.skill()
        self.run_sync()
        shutil.rmtree(self.root / 'skills/alpha')
        (self.root / 'skills/alpha').symlink_to(self.base / 'missing-source')
        before = self.snapshot()
        self.run_sync(code=2)
        self.assertEqual(before, self.snapshot())
        (self.root / 'skills/alpha').unlink()
        external = self.base / 'external'
        external.mkdir()
        (self.state.parent / 'recovery').symlink_to(external)
        before = self.snapshot()
        self.run_sync(code=1)
        self.assertEqual(before, self.snapshot())

    def test_current_conflict_prevents_prune_allows_independent_install(self):
        self.skill()
        self.skill('stale')
        self.run_sync()
        shutil.rmtree(self.root / 'skills/stale')
        (self.home / '.claude/skills/alpha').unlink()
        self.skill('beta')
        output = self.run_sync(code=2)
        self.assertIn('skipped removals', output)
        self.assertTrue(self.installed('stale').exists())
        self.assertTrue(self.installed('beta').exists())
        self.assertFalse((self.state.parent / 'recovery').exists())

    def test_top_level_peer_candidate_without_metadata_protects_removal(self):
        peer, _ = self.peer()
        cfg = json.loads((peer / 'collection-sync.json').read_text())
        cfg['skill_root'] = '.'
        (peer / 'collection-sync.json').write_text(json.dumps(cfg))
        self.skill()
        self.run_sync()
        shutil.rmtree(self.root / 'skills/alpha')
        (peer / 'alpha').mkdir()
        (peer / 'alpha/resource.txt').write_text('Incomplete peer skill')
        before = self.snapshot()
        self.assertIn('incomplete peer source', self.run_sync(code=2))
        self.assertEqual(before, self.snapshot())
