#!/usr/bin/env python3
"""Real CLI consumer check. Default: published plain URL AND shorthand.

--local rehearses the same resource/ownership assertions against this checkout;
it NEVER satisfies the published-default-branch acceptance condition.
All command writes, caches, Git configuration and installations are disposable.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
URL = 'https://github.com/vimkim/my-skills'
NAMES = {'gh-pr-comments-all', 'resolve-greptile-comments', 'markdown-write',
         'question-socratically', 'track-work'}
ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def snapshot(root):
    return {str(p.relative_to(root)): ('link', os.readlink(p)) if p.is_symlink()
            else ('dir',) if p.is_dir() else
            ('file', hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mode & 0o111)
            for p in root.rglob('*')}


def resources(root):
    return {key: value for key, value in snapshot(root).items() if value[0] != 'dir'}


def environment(base):
    # Allow executables on PATH, never inherit agent, installer, Git, npm or auth
    # configuration. Node/npm are prerequisites and must work non-interactively.
    env = {'PATH': os.environ['PATH'], 'LANG': 'C.UTF-8', 'CI': '1',
           'DO_NOT_TRACK': '1', 'DISABLE_TELEMETRY': '1', 'BROWSER': 'none',
           'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
           'GIT_TERMINAL_PROMPT': '0', 'npm_config_userconfig': '/dev/null',
           'npm_config_globalconfig': '/dev/null', 'PYTHONDONTWRITEBYTECODE': '1',
           'SKILLS_SYNC_PYTHON': sys.executable}
    for key, relative in {'HOME': 'home', 'CODEX_HOME': 'home/.codex',
                          'CLAUDE_CONFIG_DIR': 'home/.claude',
                          'XDG_STATE_HOME': 'home/.local/state',
                          'XDG_CONFIG_HOME': 'home/.config',
                          'XDG_DATA_HOME': 'home/.local/share',
                          'XDG_CACHE_HOME': 'home/.cache',
                          'npm_config_cache': 'home/.npm', 'TMPDIR': 'tmp'}.items():
        path = base / relative
        path.mkdir(parents=True, exist_ok=True)
        env[key] = str(path)
    return env


def verify(case, source, local):
    with tempfile.TemporaryDirectory(prefix='published-skills-check-') as temporary:
        base = Path(temporary)
        env = environment(base)
        cli = json.loads(os.environ.get('SKILLS_REAL_INSTALLER',
                                        '["npx", "--yes", "skills@1.7.0"]'))
        if not isinstance(cli, list) or not cli or not all(isinstance(x, str) for x in cli):
            raise ValueError('SKILLS_REAL_INSTALLER must be a nonempty JSON argv')
        env['SKILLS_SYNC_INSTALLER'] = json.dumps(cli)
        home = Path(env['HOME'])
        cwd = base / 'consumer'
        cwd.mkdir()  # Discovery/installation start without any project checkout.

        def run(argv, allowed=(0,), directory=cwd):
            result = subprocess.run(argv, cwd=directory, env=env, text=True,
                                    capture_output=True, timeout=240)
            output = ANSI.sub('', result.stdout + result.stderr)
            case['commands'].append({'argv': argv, 'exit': result.returncode,
                                     'output': output})
            if result.returncode not in allowed:
                raise AssertionError(f'Command exited {result.returncode}: {argv}\n{output}')
            return result.returncode, output

        _, version = run(cli + ['--version'])
        case['cli_version'] = version.strip()
        if version.strip() != '1.7.0':
            raise AssertionError('This contract is verified with skills 1.7.0')
        _, node_version = run(['node', '--version'])
        case['node_version'] = node_version.strip()
        if local:
            _, commit = run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'])
            case['source_commit'] = commit.strip()
            case['source_worktree_dirty'] = bool(subprocess.check_output(
                ['git', '-C', str(REPO), 'status', '--porcelain'], text=True).strip())
        else:
            _, remote = run(['git', 'ls-remote', '--symref', URL, 'HEAD'])
            case['default_branch'] = next(line.split()[1] for line in remote.splitlines()
                                          if line.startswith('ref:'))
            case['source_commit'] = next(line.split()[0] for line in remote.splitlines()
                                         if not line.startswith('ref:'))

        _, listing = run(cli + ['add', source, '--list'])
        for name in NAMES:
            if not re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', listing):
                raise AssertionError(f'Discovery missing {name}')
        for store in (home / '.agents/skills', home / '.claude/skills', home / '.codex/skills'):
            if store.exists() and list(store.iterdir()):
                raise AssertionError(f'Discovery installed skills: {store}')
        case['discovery_without_installation'] = True
        run(cli + ['add', source, '--global', '--skill', '*', '--agent',
                   'claude-code', 'codex', '--yes'])
        canonical = home / '.agents/skills'
        if not canonical.is_dir() or {p.name for p in canonical.iterdir()} != NAMES:
            raise AssertionError('Installed collection must contain exactly the five intended skills')

        # Obtain an independent source baseline only AFTER URL/shorthand install.
        checkout = base / 'checkout'
        if local:
            shutil.copytree(REPO, checkout, ignore=shutil.ignore_patterns('.git', '__pycache__'))
            run(['git', 'init', '-q', str(checkout)])
        else:
            run(['git', 'clone', '--depth', '1', URL, str(checkout)])
            _, commit = run(['git', '-C', str(checkout), 'rev-parse', 'HEAD'])
            _, remote_after = run(['git', 'ls-remote', URL, 'HEAD'])
            if commit.strip() != case['source_commit'] or remote_after.split()[0] != case['source_commit']:
                raise AssertionError('Published default branch advanced during validation; retry')
        if {p.name for p in (checkout / 'skills').iterdir() if p.is_dir()} != NAMES:
            raise AssertionError('Source collection must contain exactly the five intended skills')
        evidence = {}
        for name in sorted(NAMES):
            expected = resources(checkout / 'skills' / name)
            actual = resources(canonical / name)
            if actual != expected:
                raise AssertionError(f'Resource bytes/modes differ for {name}')
            metadata = (canonical / name / 'SKILL.md').read_text()
            if not metadata.startswith('---\n') or f'name: {name}\n' not in metadata or not re.search(r'^description: \S', metadata, re.M):
                raise AssertionError(f'Invalid skill metadata for {name}')
            claude = home / '.claude/skills' / name
            if not claude.is_symlink() or claude.resolve() != canonical / name:
                raise AssertionError(f'Claude Code missing canonical link for {name}')
            if (home / '.codex/skills' / name).exists():
                raise AssertionError(f'Unexpected Codex shadow copy for {name}')
            evidence[name] = actual
        case['resources_sha256_executable_bits'] = evidence
        case['both_agents_verified'] = True
        run([sys.executable, '-m', 'unittest', 'discover', '-s',
             str(canonical / 'markdown-write/tests'), '-v'])
        run(['node', '--check', str(canonical / 'markdown-write/scripts/check_mermaid_blocks.mjs')])

        # Empty peer is explicit evidence, avoiding dependence on a live checkout.
        peer = base / 'peer'
        (peer / 'skills').mkdir(parents=True)
        run(['git', 'init', '-q', str(peer)])
        config = json.loads((checkout / 'collection-sync.json').read_text())
        config['collections'] = {'vimkim/my-skills': str(checkout),
                                 'vimkim/my-cubrid-skills': str(peer)}
        (peer / 'collection-sync.json').write_text(json.dumps({
            'version': 1, 'collection': 'vimkim/my-cubrid-skills', 'skill_root': 'skills',
            'collections': config['collections']}))
        configuration = base / 'consumer-sync.json'
        configuration.write_text(json.dumps(config))
        sync = ['just', '--justfile', str(checkout / 'justfile')]
        before = snapshot(home)
        run(sync + ['sync-dry-run', '--config', str(configuration)], allowed=(0, 2))
        if snapshot(home) != before:
            raise AssertionError('Dry run changed consumer home')
        status, output = run(sync + ['sync', '--config', str(configuration)], allowed=(0, 2))
        if status == 2:
            if snapshot(home) != before or any(f'conflict: {name}' not in output for name in NAMES):
                raise AssertionError('Protected transition must preserve all installations and ownership')
            case['local_sync_transition'] = 'protected conflict; installation and ownership unchanged'
        else:
            state = json.loads((home / '.local/state/skill-collections/state.json').read_text())
            if any(state['skills'][name]['owner'] != 'vimkim/my-skills' for name in NAMES):
                raise AssertionError('Successful transition did not record collection ownership')
            for name in NAMES:
                if resources(canonical / name) != evidence[name]:
                    raise AssertionError('Local transition changed installed resources')
            case['local_sync_transition'] = 'recognized source and recorded verified local ownership'
        case['passed'] = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', action='store_true', help='Local rehearsal only; never publication evidence')
    parser.add_argument('--output', type=Path, help='Save complete JSON evidence outside disposable home')
    args = parser.parse_args()
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'mode': 'local rehearsal' if args.local else 'published default branch',
              'published_default_branch_verified': False, 'cases': []}
    sources = [str(REPO)] if args.local else [URL, 'vimkim/my-skills']
    for source in sources:
        case = {'source': source, 'commands': [], 'passed': False}
        report['cases'].append(case)
        try:
            verify(case, source, args.local)
        except (AssertionError, OSError, ValueError, subprocess.SubprocessError, StopIteration, KeyError) as error:
            case['error'] = str(error)
    success = all(case['passed'] for case in report['cases'])
    if success and not args.local and len({case['source_commit'] for case in report['cases']}) != 1:
        success = False
        report['error'] = 'Default branch advanced between URL and shorthand cases; rerun both'
    report['published_default_branch_verified'] = success and not args.local
    encoded = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded, end='')
    print(f"{report['mode']}: {'PASS' if success else 'FAIL'}; "
          f"publication gate: {report['published_default_branch_verified']}", file=sys.stderr)
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
