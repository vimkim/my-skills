#!/usr/bin/env python3
"""Reconcile collection skills through the skills CLI; Python standard library only."""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


class SyncError(Exception):
    pass


def command(argv, **kwargs):
    result = subprocess.run(argv, text=True, capture_output=True, **kwargs)
    if result.returncode:
        raise SyncError(f"command failed ({result.returncode}): {argv!r}\n{result.stderr or result.stdout}")
    return result.stdout


def load_json(path, default):
    if not path.exists():
        return copy.deepcopy(default)
    try:
        value = json.loads(path.read_text())
    except (ValueError, OSError) as exc:
        raise SyncError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SyncError(f"expected JSON object: {path}")
    return value


def config_for(root, path=None):
    cfg = load_json(path or root / 'collection-sync.json', {})
    if (cfg.get('version') != 1 or not isinstance(cfg.get('collection'), str)
            or not isinstance(cfg.get('collections'), dict)
            or cfg['collection'] not in cfg['collections']):
        raise SyncError(f"invalid collection configuration: {root}")
    return cfg


def digest_tree(root):
    """Hash names, executable bits and bytes; reject ambiguous/special resources."""
    if root.is_symlink() or not root.is_dir():
        raise SyncError(f"not a regular skill directory: {root}")
    digest = hashlib.sha256()
    for directory, dirs, files in os.walk(root, onerror=lambda exc: (_ for _ in ()).throw(exc)):
        for name in sorted(dirs + files):
            p = Path(directory) / name
            if p.is_symlink() or not (p.is_file() or p.is_dir()):
                raise SyncError(f"unsupported symlink or special resource: {p}")
        dirs.sort()
        for name in dirs:
            relative = (Path(directory) / name).relative_to(root).as_posix().encode()
            digest.update(b'd' + len(relative).to_bytes(8, 'big') + relative)
        for name in sorted(files):
            p = Path(directory) / name
            relative = p.relative_to(root).as_posix().encode()
            data = p.read_bytes()
            digest.update(b'f' + len(relative).to_bytes(8, 'big') + relative)
            digest.update(bytes([bool(p.stat().st_mode & 0o111)]))
            digest.update(len(data).to_bytes(8, 'big') + data)
    return digest.hexdigest()


def scan_collection(root, cfg=None):
    if not root.is_dir():
        raise SyncError(f"missing collection: {root}")
    git_root = Path(command(['git', '-C', str(root), 'rev-parse', '--show-toplevel']).strip()).resolve()
    if git_root != root.resolve():
        raise SyncError(f"collection must be a Git checkout root: {root}")
    cfg = cfg or config_for(root)
    relative = Path(cfg.get('skill_root', 'skills'))
    if relative.is_absolute() or '..' in relative.parts:
        raise SyncError('skill_root must stay inside the collection')
    source = root / relative
    if not source.is_dir() or source.is_symlink():
        raise SyncError(f"missing or unsafe skill container: {source}")
    result = {}
    # os.scandir and explicit reads propagate scan errors rather than treating them as deletion.
    for directory in sorted(source.iterdir()):
        if directory.name.startswith('.'):
            continue
        skill = directory / 'SKILL.md'
        if not skill.exists():
            if relative != Path('.') and directory.is_dir():
                raise SyncError(f"incomplete skill directory (missing SKILL.md): {directory}")
            continue
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', directory.name):
            raise SyncError(f"unsafe skill name: {directory.name}")
        text = skill.read_text()
        front = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
        if not front:
            raise SyncError(f"missing frontmatter: {skill}")
        name = re.search(r'^name:\s*[\"\']?([a-z0-9-]+)[\"\']?\s*$', front[1], re.M)
        description = re.search(r'^description:\s*\S', front[1], re.M)
        if not name or name[1] != directory.name or not description:
            raise SyncError(f"invalid name/description: {skill}")
        result[directory.name] = {'path': directory, 'digest': digest_tree(directory)}
    return result


def paths_for(home):
    # Codex reads the universal store. Honor Claude's supported home override.
    return {'store': home / '.agents/skills',
            'claude': Path(os.environ.get('CLAUDE_CONFIG_DIR', str(home / '.claude'))) / 'skills',
            'codex_legacy': Path(os.environ.get('CODEX_HOME', str(home / '.codex'))) / 'skills',
            'lock': home / '.agents/.skill-lock.json',
            'state': Path(os.environ.get('XDG_STATE_HOME', str(home / '.local/state'))) / 'skill-collections/state.json'}


def validate_state(state):
    if state.get('version') != 1 or not isinstance(state.get('skills'), dict):
        raise SyncError('malformed ownership state')
    for name, entry in state['skills'].items():
        if (not re.fullmatch(r'[a-z0-9][a-z0-9-]*', name) or not isinstance(entry, dict)
                or not isinstance(entry.get('owner'), str)
                or not re.fullmatch(r'[0-9a-f]{64}', entry.get('digest', ''))
                or not isinstance(entry.get('source'), str)):
            raise SyncError(f'malformed ownership record: {name}')


def lock_owner(entry, cfg, root):
    if not isinstance(entry, dict):
        return None
    if entry.get('sourceType') == 'github':
        return entry.get('source')
    if entry.get('sourceType') == 'local':
        source = entry.get('sourceUrl') or entry.get('source', '')
        if Path(source).is_absolute() and Path(source).resolve() == root.resolve():
            return cfg['collection']
    return None


def installation_digest(name, paths):
    canonical = paths['store'] / name
    claude = paths['claude'] / name
    legacy = paths['codex_legacy'] / name
    if os.path.lexists(legacy) and legacy.resolve() != canonical.resolve():
        raise SyncError('separate Codex skill shadows the universal installation')
    if not os.path.lexists(canonical):
        if os.path.lexists(claude):
            raise SyncError('Claude-only/manual installation')
        return None
    digest = digest_tree(canonical)
    if os.path.lexists(claude):
        if not claude.is_symlink() or claude.resolve() != canonical.resolve():
            raise SyncError('Claude installation is not the verified universal link')
    else:
        raise SyncError('Claude installation is missing')
    return digest


def inspect_skill(name, skill, cfg, root, paths, state, lock):
    try:
        existing = installation_digest(name, paths)
    except (SyncError, OSError) as exc:
        return 'conflict', str(exc)
    record = state['skills'].get(name)
    metadata = lock['skills'].get(name)
    if metadata is not None and lock_owner(metadata, cfg, root) != cfg['collection']:
        return 'conflict', 'installer metadata belongs to another or unknown source'
    if record and record['owner'] != cfg['collection']:
        return 'conflict', f"owned by {record['owner']}"
    if existing is None:
        return 'add', ''
    if record:
        if existing != record['digest']:
            return 'conflict', 'installed files were edited'
        return ('unchanged' if existing == skill['digest'] else 'update'), ''
    # GitHub/local metadata proves source identity, but cannot prove an old copy is unedited.
    # Bootstrap only when bytes already equal the authoritative checkout.
    if metadata and lock_owner(metadata, cfg, root) == cfg['collection'] and existing == skill['digest']:
        return 'adopt', 'verified installer source and exact current content'
    return 'conflict', 'untracked/manual installation or unverifiable older content'


def isolated_env(home):
    env = dict(os.environ)
    for key, relative in {'HOME': '.', 'CODEX_HOME': '.codex', 'CLAUDE_CONFIG_DIR': '.claude',
                          'XDG_CONFIG_HOME': '.config', 'XDG_CACHE_HOME': '.cache',
                          'XDG_DATA_HOME': '.local/share', 'XDG_STATE_HOME': '.local/state',
                          'npm_config_cache': '.npm', 'TMPDIR': 'tmp'}.items():
        env[key] = str(home / relative)
    (home / 'tmp').mkdir(parents=True, exist_ok=True)
    env.update(DISABLE_TELEMETRY='1', DO_NOT_TRACK='1', CI='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
    return env


def installer_command():
    # JSON argv allows deterministic test substitutes without invoking a shell.
    raw = os.environ.get('SKILLS_SYNC_INSTALLER')
    argv = json.loads(raw) if raw else ['npx', '--yes', 'skills@1.7.0']
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        raise SyncError('SKILLS_SYNC_INSTALLER must be a nonempty JSON argument list')
    return argv


def stage_install(root, names, skills, stage):
    env = isolated_env(stage)
    command(installer_command() + ['add', str(root), '--global', '--agent', 'claude-code', 'codex',
                                   '--skill', *names, '--yes'], env=env, cwd=stage)
    paths = {'store': stage / '.agents/skills', 'claude': stage / '.claude/skills', 'codex_legacy': stage / '.codex/skills'}
    for name in names:
        if installation_digest(name, paths) != skills[name]['digest']:
            raise SyncError(f'installer verification failed for {name}')
    return paths


def remove_path(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def copy_path(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        destination.symlink_to(os.readlink(source))
    elif source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.new')
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    os.replace(temporary, path)


def promote(names, stage_paths, paths, new_state, new_lock):
    """Rollback all targeted files and ownership metadata on ordinary I/O failure."""
    targets = [paths[key] / name for name in names for key in ('store', 'claude')]
    targets += [paths['state'], paths['lock']]
    with tempfile.TemporaryDirectory(prefix='skill-sync-rollback-') as temporary:
        backup = Path(temporary)
        existed = {}
        for index, target in enumerate(targets):
            existed[index] = os.path.lexists(target)
            if existed[index]:
                copy_path(target, backup / str(index))
        try:
            for name in names:
                for key in ('store', 'claude'):
                    target = paths[key] / name
                    remove_path(target)
                    if key == 'store':
                        copy_path(stage_paths[key] / name, target)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.symlink_to(os.path.relpath(paths['store'] / name, target.parent))
            write_json(paths['state'], new_state)
            if new_lock is not None:
                write_json(paths['lock'], new_lock)
        except BaseException:
            for index, target in enumerate(targets):
                remove_path(target)
                if existed[index]:
                    copy_path(backup / str(index), target)
            raise


def run_sync(args):
    root = args.collection.resolve()
    cfg = config_for(root, args.config)
    skills = scan_collection(root, cfg)
    paths = paths_for(Path.home())
    for path in paths.values():
        if any(parent.is_symlink() for parent in [path, *path.parents]):
            raise SyncError(f'unsafe symlink in managed path: {path}')
    state = load_json(paths['state'], {'version': 1, 'skills': {}})
    validate_state(state)
    lock = load_json(paths['lock'], {'version': 3, 'skills': {}})
    if lock.get('version') != 3 or not isinstance(lock.get('skills'), dict) or not all(isinstance(v, dict) for v in lock['skills'].values()):
        raise SyncError('malformed installer metadata')
    eligible, conflicts = [], []
    for name, skill in skills.items():
        action, reason = inspect_skill(name, skill, cfg, root, paths, state, lock)
        print(f'{action}: {name}' + (f' ({reason})' if reason else ''))
        if action == 'conflict':
            conflicts.append(name)
        elif action != 'unchanged':
            eligible.append(name)
    for name, record in state['skills'].items():
        if record['owner'] == cfg['collection'] and name not in skills:
            print(f'deferred stale: {name} (automatic removal is not enabled)')
    if not skills:
        print('empty collection: no current skills')
    if args.dry_run or not eligible:
        return 2 if conflicts else 0
    # All installer writes happen in a disposable home. A partial CLI failure cannot
    # overwrite live files or lock records, and verification precedes promotion.
    with tempfile.TemporaryDirectory(prefix='skill-sync-stage-') as temporary:
        staged = stage_install(root, eligible, skills, Path(temporary))
        # Recheck inputs after the external command, including complete source evidence.
        if scan_collection(root, cfg) != skills:
            raise SyncError('source changed during installation; retry')
        if load_json(paths['state'], {'version': 1, 'skills': {}}) != state or load_json(paths['lock'], {'version': 3, 'skills': {}}) != lock:
            raise SyncError('ownership metadata changed during installation; retry')
        for name in eligible:
            action, _ = inspect_skill(name, skills[name], cfg, root, paths, state, lock)
            if action == 'conflict':
                raise SyncError(f'installation changed during sync: {name}')
        updated = copy.deepcopy(state)
        for name in eligible:
            updated['skills'][name] = {'owner': cfg['collection'], 'digest': skills[name]['digest'], 'source': str(skills[name]['path'])}
        # Local CLI does not emit lock records. Remove superseded matching GitHub
        # entries only after verification; shared baseline now records ownership.
        updated_lock = copy.deepcopy(lock)
        for name in eligible:
            updated_lock['skills'].pop(name, None)
        promote(eligible, staged, paths, updated, updated_lock if updated_lock != lock else None)
    return 2 if conflicts else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--config', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        # An advisory lock on the existing home directory serializes cooperating
        # collection syncs without creating a file (including during dry runs).
        home_fd = os.open(Path.home(), os.O_RDONLY | os.O_DIRECTORY)
        try:
            fcntl.flock(home_fd, fcntl.LOCK_EX)
            return run_sync(args)
        finally:
            os.close(home_fd)
    except (SyncError, OSError, ValueError, TypeError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
