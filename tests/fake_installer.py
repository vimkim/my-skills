"""Controlled CLI substitute, invoked as an external process in disposable HOME."""
import json
import os
from pathlib import Path
import shutil
import sys

argv = sys.argv[1:]
root = Path(argv[argv.index('add') + 1])
names = argv[argv.index('--skill') + 1:argv.index('--yes')]
home = Path.home()
for name in names:
    source = root / 'skills' / name
    if not source.exists():
        source = root / name
    destination = home / '.agents/skills' / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    link = home / '.claude/skills' / name
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(os.path.relpath(destination, link.parent))
    if os.environ.get('TEST_INSTALLER_FAILURE') == 'partial':
        sys.exit(17)
    if os.environ.get('TEST_INSTALLER_FAILURE') == 'verification':
        (destination / 'SKILL.md').write_text('corrupt output')
    if os.environ.get('TEST_INSTALLER_FAILURE') == 'link':
        link.unlink()

lock_mode = os.environ.get('TEST_INSTALLER_LOCAL_LOCK')
if lock_mode:
    lock_path = (Path(os.environ['XDG_STATE_HOME']) / 'skills/.skill-lock.json'
                 if lock_mode == 'xdg' else home / '.agents/.skill-lock.json')
    source = str(root if lock_mode != 'wrong-source' else root / 'other')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps({'version': 3, 'skills': {
        name: {'sourceType': 'local', 'source': source, 'sourceUrl': source}
        for name in names}}))
