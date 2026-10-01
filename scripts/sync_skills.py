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


def promote(names, stage_paths, paths, new_state, new_lock, removals=()):
    """Rollback all targeted files and ownership metadata on ordinary I/O failure."""
    targets = [paths[key] / name for name in [*names, *removals] for key in ('store', 'claude')]
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
            for name in removals:
                for key in ('claude', 'store'):
                    remove_path(paths[key] / name)
            write_json(paths['state'], new_state)
            if new_lock is not None:
                write_json(paths['lock'], new_lock)
        except BaseException:
            for index, target in enumerate(targets):
                remove_path(target)
                if existed[index]:
                    copy_path(backup / str(index), target)
            raise


APPROVED_MIGRATIONS = frozenset({
    'gh-pr-comments-all', 'resolve-greptile-comments', 'markdown-write',
    'question-socratically', 'track-work'})


def peer_evidence(root, cfg):
    """An unavailable peer is unknown evidence, never an empty collection."""
    peers, errors = {}, []
    for owner, location in cfg['collections'].items():
        if owner == cfg['collection']:
            continue
        try:
            if not isinstance(location, str):
                raise SyncError('collection path must be a string')
            path = (root / location).resolve()
            peer_cfg = config_for(path)
            if peer_cfg['collection'] != owner:
                raise SyncError(f'collection identity mismatch: {path}')
            peers[owner] = (path, scan_collection(path, peer_cfg))
        except (SyncError, OSError) as exc:
            errors.append(f'{owner}: {exc}')
    return peers, errors


def approved_transfer(name, cfg):
    migrations = cfg.get('migrations', [])
    if not isinstance(migrations, list):
        raise SyncError('malformed migration configuration')
    for entry in migrations:
        if (not isinstance(entry, dict) or set(entry) != {'name', 'from', 'to'}
                or entry['name'] not in APPROVED_MIGRATIONS
                or entry['from'] != 'vimkim/my-cubrid-skills'
                or entry['to'] != 'vimkim/my-skills'):
            raise SyncError('migration must name an approved old-to-new skill transfer')
    return next((entry for entry in migrations if entry['name'] == name), None)


def inspect_current(name, skill, cfg, root, paths, state, lock, peers):
    transfer = approved_transfer(name, cfg)
    record = state['skills'].get(name)
    metadata = lock['skills'].get(name)
    if transfer and cfg['collection'] == transfer['from']:
        destination = peers.get(transfer['to'])
        if destination and name in destination[1]:
            return 'preserve', 'destination supplies approved migration; sync destination to transfer'
    action, reason = inspect_skill(name, skill, cfg, root, paths, state, lock)
    if not transfer or cfg['collection'] != transfer['to'] or transfer['from'] not in peers:
        return action, reason
    previous_root, previous_skills = peers[transfer['from']]
    previous_cfg = {'collection': transfer['from']}
    owner = lock_owner(metadata, previous_cfg, previous_root) if metadata else None
    if metadata and owner != transfer['from']:
        return action, reason
    if record and record['owner'] != transfer['from']:
        return action, reason
    if not record and owner != transfer['from']:
        return action, reason
    try:
        existing = installation_digest(name, paths)
    except (SyncError, OSError) as exc:
        return 'conflict', str(exc)
    expected = record['digest'] if record else previous_skills.get(name, skill)['digest']
    if existing != expected:
        return 'conflict', 'migration cannot verify unedited previous installation'
    return 'transfer', f"verified ownership from {transfer['from']}"


def prune_plan(root, cfg, skills, paths, state, lock, peers, errors):
    removals, conflicts = [], []
    for name, record in sorted(state['skills'].items()):
        if record['owner'] != cfg['collection'] or name in skills:
            continue
        reason = ''
        if errors:
            reason = 'incomplete collection evidence'
        elif any(name in peer_skills for _, peer_skills in peers.values()):
            print(f'preserve: {name} (supplied by another configured collection)')
            continue
        elif any(os.path.lexists(peer_root / config_for(peer_root).get('skill_root', 'skills') / name)
                 for peer_root, _ in peers.values()):
            reason = 'incomplete peer source directory remains'
        elif os.path.lexists(root / cfg.get('skill_root', 'skills') / name):
            reason = 'incomplete source directory remains'
        else:
            metadata = lock['skills'].get(name)
            if metadata is not None and lock_owner(metadata, cfg, root) != cfg['collection']:
                reason = 'installer metadata belongs to another or unknown source'
            else:
                try:
                    if installation_digest(name, paths) != record['digest']:
                        reason = 'installed files were edited or are missing'
                except (SyncError, OSError) as exc:
                    reason = str(exc)
        if reason:
            print(f'conflict: {name} ({reason}; removal skipped)')
            conflicts.append(name)
        else:
            print(f'remove: {name} (verified obsolete owned installation)')
            removals.append(name)
    return removals, conflicts


def recovery_snapshot(names, paths, state, lock):
    parent = paths['state'].parent / 'recovery'
    if any(p.is_symlink() for p in [parent, *parent.parents]):
        raise SyncError(f'unsafe symlink in recovery path: {parent}')
    parent.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='removed-', dir=parent))
    try:
        records = {}
        for name in names:
            copy_path(paths['store'] / name, folder / 'skills' / name)
            if digest_tree(folder / 'skills' / name) != state['skills'][name]['digest']:
                raise SyncError(f'recovery verification failed: {name}')
            records[name] = {'state': state['skills'][name], 'lock': lock['skills'].get(name)}
        write_json(folder / 'manifest.json', {'version': 1, 'skills': records})
    except BaseException:
        shutil.rmtree(folder)
        raise
    print(f'recovery: {folder}')
    return folder


def read_managed_state(paths):
    for path in paths.values():
        if any(parent.is_symlink() for parent in [path, *path.parents]):
            raise SyncError(f'unsafe symlink in managed path: {path}')
    state = load_json(paths['state'], {'version': 1, 'skills': {}})
    validate_state(state)
    lock = load_json(paths['lock'], {'version': 3, 'skills': {}})
    if lock.get('version') != 3 or not isinstance(lock.get('skills'), dict) or not all(isinstance(v, dict) for v in lock['skills'].values()):
        raise SyncError('malformed installer metadata')
    return state, lock


def restore_snapshot(args):
    paths = paths_for(Path.home())
    state, lock = read_managed_state(paths)
    folder = args.restore.resolve()
    manifest = load_json(folder / 'manifest.json', {})
    if manifest.get('version') != 1 or not isinstance(manifest.get('skills'), dict) or not manifest['skills']:
        raise SyncError('malformed recovery manifest')
    restored, updated_lock = copy.deepcopy(state), copy.deepcopy(lock)
    for name, entry in manifest['skills'].items():
        if not isinstance(entry, dict) or set(entry) != {'state', 'lock'}:
            raise SyncError('malformed recovery entry')
        validate_state({'version': 1, 'skills': {name: entry['state']}})
        if entry['lock'] is not None and not isinstance(entry['lock'], dict):
            raise SyncError('malformed recovery installer metadata')
        if (name in state['skills'] or name in lock['skills']
                or any(os.path.lexists(paths[key] / name) for key in ('store', 'claude', 'codex_legacy'))):
            raise SyncError(f'restore conflict: {name} already has installed files or ownership')
        if digest_tree(folder / 'skills' / name) != entry['state']['digest']:
            raise SyncError(f'recovery content changed: {name}')
        restored['skills'][name] = entry['state']
        if entry['lock'] is not None:
            updated_lock['skills'][name] = entry['lock']
        print(f'restore: {name}')
    if not args.dry_run:
        promote(list(manifest['skills']), {'store': folder / 'skills'}, paths, restored,
                updated_lock if updated_lock != lock else None)
    return 0


def run_sync(args):
    if args.restore:
        return restore_snapshot(args)
    root = args.collection.resolve()
    cfg = config_for(root, args.config)
    approved_transfer('', cfg)  # Validate the complete transfer policy before any mutation.
    skills = scan_collection(root, cfg)
    paths = paths_for(Path.home())
    state, lock = read_managed_state(paths)
    peers, errors = peer_evidence(root, cfg)
    for error in errors:
        print(f'skipped peer evidence: {error}')
    eligible, conflicts, observations = [], [], {}
    for name, skill in skills.items():
        action, reason = inspect_current(name, skill, cfg, root, paths, state, lock, peers)
        observations[name] = (action, reason)
        print(f'{action}: {name}' + (f' ({reason})' if reason else ''))
        if action == 'conflict':
            conflicts.append(name)
        elif action not in ('unchanged', 'preserve'):
            eligible.append(name)
    removals, prune_conflicts = prune_plan(root, cfg, skills, paths, state, lock, peers, errors)
    if conflicts and removals:
        print('skipped removals: current installation conflicts prevent collection pruning')
        removals = []
    conflicts.extend(prune_conflicts)
    if not skills:
        print('empty collection: no current skills')
    result = 2 if conflicts or errors else 0
    if args.dry_run or not (eligible or removals):
        return result
    with tempfile.TemporaryDirectory(prefix='skill-sync-stage-') as temporary:
        staged = stage_install(root, eligible, skills, Path(temporary)) if eligible else {}
        if scan_collection(root, cfg) != skills or peer_evidence(root, cfg) != (peers, errors):
            raise SyncError('source evidence changed during installation; retry')
        if read_managed_state(paths) != (state, lock):
            raise SyncError('ownership metadata changed during installation; retry')
        # Reverify unchanged current installations too before authorizing pruning.
        for name in skills:
            if inspect_current(name, skills[name], cfg, root, paths, state, lock, peers) != observations[name]:
                raise SyncError(f'installation changed during sync: {name}')
        checked_removals, _ = prune_plan(root, cfg, skills, paths, state, lock, peers, errors)
        if any(action == 'conflict' for action, _ in observations.values()):
            checked_removals = []
        if checked_removals != removals:
            raise SyncError('removal evidence changed during installation; retry')
        updated, updated_lock = copy.deepcopy(state), copy.deepcopy(lock)
        for name in eligible:
            updated['skills'][name] = {'owner': cfg['collection'], 'digest': skills[name]['digest'], 'source': str(skills[name]['path'])}
            updated_lock['skills'].pop(name, None)
        if removals:
            recovery_snapshot(removals, paths, state, lock)
        for name in removals:
            updated['skills'].pop(name)
            updated_lock['skills'].pop(name, None)
        promote(eligible, staged, paths, updated, updated_lock if updated_lock != lock else None, removals)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--config', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--restore', type=Path, help='restore a reported recovery directory without overwriting any skill')
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
