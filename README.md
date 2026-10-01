# Personal skills

This repository is a **source collection**: edit skills here. Installed skills are generated copies for Codex and Claude Code. A skill directory contains `SKILL.md` with matching `name` and a nonempty `description` in YAML frontmatter, plus its supporting resources. Skills live in `skills/<name>/`; keep the container present even when empty.

## Requirements and commands

Linux, Python **3.12+**, Git, just, and Node **22.20+** with npm/npx are required. Python uses only its standard library; no virtual environment is needed. The installer is pinned to `skills@1.7.0`. Tests ran on Python 3.12 and 3.14.6; the real installer smoke used Node 25.8.0. Set `SKILLS_SYNC_PYTHON` to select a different Python executable.

```sh
just sync-dry-run
just sync
just list
just remove skill-name
just test
python3 tests/real_smoke.py
```

`sync` reconciles current checkout contents. It does **not** fetch or pull Git changes. Refresh your checkout separately. `sync-dry-run` describes additions, updates, unchanged skills, conflicts and stale candidates without modifying the checkout, installed skills, ownership or recovery files. `list` shows globally installed skills for Claude Code and Codex, including other collections; it can populate npm's cache but does not install skills. Discover this checkout separately with `npx --yes skills@1.7.0 add . --list`. `remove` explicitly invokes the installer's global removal for the named skill and both agents, regardless of collection ownership; it is not automatic reconciliation and does not provide recovery. The next sync can recreate a removed current skill. There is no third-party update recipe.

Exit status is **0** for complete success (including an empty collection), **2** for conflicts/skipped skills with any independent eligible work completed, and **1** for configuration, scan, installer or verification errors. `just` propagates these statuses. Automatic stale removal is deferred to ticket #3; this slice reports candidates and preserves them.

## Ownership and conflicts

`collection-sync.json` identifies the collection, its configured source checkouts and the skill container (`skill_root`, default `skills`). Names are lowercase ASCII letters/digits/hyphens. Symlinked or special resources are rejected. Missing containers, unreadable/incomplete skills, non-Git collection roots and malformed ownership files fail closed. `skills/.gitkeep` permits an explicitly empty collection.

The verified installer layout is `~/.agents/skills/<name>` (Codex's universal store) and a Claude Code link to it under `~/.claude/skills/<name>`. `CLAUDE_CONFIG_DIR`, `CODEX_HOME` (for detecting legacy shadow copies), and `XDG_STATE_HOME` are respected. Managed parent directories must not be symlinks. A separate Codex legacy copy, unexpected Claude copy/link, edited resource, unknown owner, or manual installation is a conflict and is preserved. Independent eligible skills still synchronize.

The CLI's global metadata lives at `~/.agents/.skill-lock.json`. **skills 1.7.0 does not write a global lock record for local-path installations.** Sync therefore supplements it with `~/.local/state/skill-collections/state.json`, recording collection identity, source path and a content/executable-bit fingerprint only after successful installation verification. Historical skill membership is never proof of ownership.

Existing local installs lacking both a verified sync baseline and installer ownership evidence are protected as manual installations, **even if their bytes equal this checkout**. A matching local-source or GitHub-source installer record may bootstrap ownership only when both agent layouts and every installed byte already match the current source. An older/different GitHub copy cannot establish that local edits are absent and is skipped. Successful transition to local collection sync removes only that skill's superseded installer record; unrelated metadata remains intact.

Resolve ordinary conflicts by reviewing the installed copy, saving its edits into the authoritative source where appropriate, and preserving a separate backup. When deliberately replacing a legacy/manual installation, explicitly remove it with the installer after that review, then run sync. Do not fabricate ownership records or delete evidence merely to bypass protection. Cross-collection ownership transfers require the explicit migration support in the following ticket.

## Installation and failure behavior

Sync invokes the existing CLI with subprocess argument lists in a disposable home and contained config/cache directories. It compares all files and executable bits and verifies the Claude link before promoting eligible output. An installer partial failure or verification failure leaves the previous installations and ownership untouched. Promotion keeps temporary backups and rolls back targeted files and metadata on ordinary I/O exceptions. It rechecks source and ownership evidence before promotion. Cooperating sync processes serialize through an advisory lock on the existing home directory. Do not run other installers or edit installed files concurrently; abrupt process termination or power loss during promotion is not a crash-recovery guarantee.

`SKILLS_SYNC_INSTALLER` is an optional JSON argument list for an inspected installer executable or a deterministic test substitute; it is never shell-evaluated. Tests exercise `just sync` and `just sync-dry-run` with temporary Git repositories and disposable homes/caches. `tests/real_smoke.py` exercises first installation, updates, resources, both agents and repeat idempotence with the real pinned CLI. It downloads only into a disposable npm cache by default; `SKILLS_REAL_INSTALLER='["node","/absolute/path/to/skills/bin/cli.mjs"]'` reuses an already inspected installer without modifying its installation.

Public default-branch GitHub URL and shorthand installation will be verified after the approved migration is published (ticket #6). Local smoke checks are not evidence of that publication gate.
