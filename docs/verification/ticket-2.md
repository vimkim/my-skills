# Ticket #2 verification

Inspected 2026-10-01: cached npm package `skills` 1.7.0 declares Node `>=22.20.0`; target node is 25.8.0. Python 3.12 and 3.14.6 are installed. Inspection of the live global lock was read-only (schema version 3).

A real isolated `skills add <local-path> --global --agent claude-code codex --skill alpha --yes` produced a canonical directory under `.agents/skills` and a relative `.claude/skills` symlink. It produced **no global lock**. The implementation supplements this demonstrated metadata gap with verified content baselines. The CLI's `dist/cli.mjs` global lock writer is conditional on a nonempty normalized source; GitHub records contain source/sourceType/sourceUrl/skillPath/skillFolderHash. A global folder hash alone does not establish absence of installed edits, so bootstrap requires content equality.

Reproducible commands:

```sh
just test
SKILLS_SYNC_PYTHON=/usr/bin/python3.12 /usr/bin/python3.12 -m unittest discover -s tests -v
python3 tests/real_smoke.py
```

The public-command suite covers add/update/resources/new skills/idempotence; empty/deferred stale and nonmutating preview; edited/manual/foreign-source conflicts; local/GitHub metadata adoption and unverifiable old GitHub copies; partial installer failure, corrupt output and missing agent link; malformed state, incomplete scan, missing container/Git checkout; source/link escapes and legacy Codex shadows. Failure cases assert complete before/after filesystem snapshots. All installer execution is contained in disposable homes and caches.

The real smoke was run with the installed 1.7.0 CLI specified by `SKILLS_REAL_INSTALLER`, with temporary source/home/config/cache directories. Both initial and updated resources and Claude/Codex availability passed. No live installed-skill store was changed. These checks cover local-path compatibility; publication/default-branch install evidence belongs to ticket #6.
