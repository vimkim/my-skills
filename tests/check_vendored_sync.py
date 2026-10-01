"""Verify the standalone old entry point in a disposable checkout/home.

Usage: python3 tests/check_vendored_sync.py /path/to/my-cubrid-skills
Reads that checkout; performs all synchronization in temporary fixtures.
"""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import unittest

from test_pruning import PruningCommands
from test_sync import REPO

OLD = Path(sys.argv.pop(1)).resolve()


class VendoredCommands(PruningCommands):
    # Restrict this smoke to its one scenario; inherited cases already cover shared engine.
    pass


for name in dir(VendoredCommands):
    if name.startswith('test_'):
        setattr(VendoredCommands, name, None)


def smoke(self):
    self.assertEqual((REPO / 'scripts/sync_skills.py').read_bytes(),
                     (OLD / 'tools/sync_skills.py').read_bytes())
    shutil.copy2(OLD / 'justfile', self.root / 'justfile')
    (self.root / 'tools').mkdir()
    for name in ('sync-skills.sh', 'sync_skills.py'):
        shutil.copy2(OLD / 'tools' / name, self.root / 'tools' / name)
    cfg = json.loads((self.root / 'collection-sync.json').read_text())
    cfg['skill_root'] = '.'
    (self.root / 'collection-sync.json').write_text(json.dumps(cfg))
    self.skill()
    shutil.move(str(self.root / 'skills/alpha'), self.root / 'alpha')
    self.run_sync()
    self.assertTrue(self.installed().is_dir())
    shutil.rmtree(self.root / 'alpha')
    before = self.snapshot()
    self.run_sync(dry=True)
    self.assertEqual(before, self.snapshot())
    self.run_sync()
    folder, = self.recovery()
    self.restore(folder)
    self.assertTrue((self.home / '.claude/skills/alpha/SKILL.md').is_file())


VendoredCommands.test_standalone_old_interface = smoke
if __name__ == '__main__':
    spec = importlib.util.spec_from_file_location('sync_engine', REPO / 'scripts/sync_skills.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    current = module.scan_collection(OLD)
    print(f'Old source scan: {len(current)} valid skill directories (read-only).')
    suite = unittest.TestSuite([VendoredCommands('test_standalone_old_interface')])
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
