# Personal skills

This repository is a **source collection**: edit skills here. Installed skills are generated copies for Codex and Claude Code. A skill directory contains `SKILL.md` with matching `name` and a nonempty `description` in YAML frontmatter, plus its supporting resources. Skills live in `skills/<name>/`; keep the container present even when empty.

## Skills

| Invocation name | Purpose | Additional requirements |
|---|---|---|
| `gh-pr-comments-all` | Fetch all three GitHub PR comment streams | Authenticated `gh`, `jq`, Bash and standard shell tools |
| `resolve-greptile-comments` | Resolve replied Greptile review threads | Authenticated `gh` with repository permissions, Bash and standard shell tools |
| `markdown-write` | Write and validate copyparty-compatible Markdown | Python 3; Node/npm and `jsdom` for Mermaid; configured viewer and its vendored Mermaid bundle for rendering checks |
| `question-socratically` | One-question-at-a-time Socratic dialogue | No external command |
| `track-work` | Maintain durable work status and history | `work-tracker` CLI and configured ledger |
| `serve-html` | Generate an HTML serving command and clickable VPN/LAN URLs; stop with Ctrl+C | Linux, Python 3, and `ip` (iproute2) |

These skills retain their invocation names, original content and supporting resources. `markdown-write` includes two executable validators, its regression tests and agent metadata; `track-work` includes agent metadata. The Mermaid validator resolves its bundle from the target document tree or `MERMAID_BUNDLE`, and may install `jsdom` into `~/.cache/markdown-write-skill`. It does not bundle the viewer or dependencies. Install `work-tracker` from its source repository with `just install` when unavailable; the skill uses the executable on `PATH` and its configured ledger.

`daily-schedule` and `my-cubrid-skills-create` remain in the CUBRID collection. The former invokes this collection's `track-work`; `gh-pr-comments-all` refers to `resolve-greptile-comments` by its unchanged invocation name. See [migration provenance, sequence and verification](docs/migration.md).

## Install from GitHub

**Publication verified:** the plain GitHub URL and repository shorthand both
passed isolated discovery and installation for Claude Code and Codex on
2026-10-01, using published `main` commit `1f636b6` and `skills@1.7.0`.
[Verification evidence](docs/verification/ticket-6.md) records all resources,
command outcomes and the protected transition to local sync.

Installation requires Git and Node **22.20+** with npm/npx. It does not require a
pre-existing checkout, Python, or just. Individual skills have the runtime
requirements in the table above; installing their files does not provision
GitHub authentication, `work-tracker`, or the copyparty viewer.

Discover without installing (either spelling works):

```sh
npx --yes skills@1.7.0 add https://github.com/vimkim/my-skills --list
npx --yes skills@1.7.0 add vimkim/my-skills --list
```

Install all skills globally for **Claude Code and Codex**, using either
source form:

```sh
npx --yes skills@1.7.0 add https://github.com/vimkim/my-skills --global --skill '*' --agent claude-code codex --yes
npx --yes skills@1.7.0 add vimkim/my-skills --global --skill '*' --agent claude-code codex --yes
```

Choose one install command. Replace `'*'` with a skill name to select a subset.
The CLI writes the canonical Codex-compatible copies under `~/.agents/skills`
and Claude Code links under `~/.claude/skills`. Full URL and shorthand refer to
the same repository. See the [upstream CLI documentation](https://github.com/vercel-labs/skills#install-a-skill)
for source formats and agent selection.

Remote installation downloads published content. Local `just sync` reconciles a
source checkout with the safety and ownership rules below; it does not fetch
GitHub updates. When switching from GitHub installation to a local checkout,
use `just sync-dry-run` first. Matching installer ownership and content can be
adopted; uncertain or different content is a protected conflict. Review that
conflict before choosing any replacement. Direct local-path CLI installs lack
ownership metadata in version 1.7.0 and therefore remain protected.

The repeatable isolated check is documented in
[consumer verification evidence](docs/verification/ticket-6.md).

## Local sync requirements and commands

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

On the maintainer's host, the coordinated `daily-update` change in
`vimkim/dotfiles` refreshes both clean personal checkouts before invoking their
local `just sync`. It skips dirty, ahead or diverged checkouts and continues
independently safe work after a failure. Its source, policy and verification are
documented in that repository's `docs/daily-update.md`; deploying the updated
Bash entry point requires separate authorization. See the
[combined implementation review](docs/verification/spec-1-review.md).

Exit status is **0** for complete success (including an empty collection), **2** for conflicts/skipped skills with any independent eligible work completed, and **1** for configuration, scan, installer or verification errors. `just` propagates these statuses. Unknown peer evidence and skipped removals are visible failures, even when independent installation work succeeds.

## Ownership and conflicts

`collection-sync.json` identifies the collection, its configured source checkouts and the skill container (`skill_root`, default `skills`). Names are lowercase ASCII letters/digits/hyphens. Symlinked or special resources are rejected. Missing containers, unreadable/incomplete skills, non-Git collection roots and malformed ownership files fail closed. `skills/.gitkeep` permits an explicitly empty collection.

The verified installer layout is `~/.agents/skills/<name>` (Codex's universal store) and a Claude Code link to it under `~/.claude/skills/<name>`. `CLAUDE_CONFIG_DIR`, `CODEX_HOME` (for detecting legacy shadow copies), and `XDG_STATE_HOME` are respected. Managed parent directories must not be symlinks. A separate Codex legacy copy, unexpected Claude copy/link, edited resource, unknown owner, or manual installation is a conflict and is preserved. Independent eligible skills still synchronize.

The CLI's global metadata lives at `~/.agents/.skill-lock.json`. **skills 1.7.0 does not write a global lock record for local-path installations.** Sync therefore supplements it with `~/.local/state/skill-collections/state.json`, recording collection identity, source path and a content/executable-bit fingerprint only after successful installation verification. Historical skill membership is never proof of ownership.

Existing local installs lacking both a verified sync baseline and installer ownership evidence are protected as manual installations, **even if their bytes equal this checkout**. A matching local-source or GitHub-source installer record may bootstrap ownership only when both agent layouts and every installed byte already match the current source. An older/different GitHub copy cannot establish that local edits are absent and is skipped. Successful transition to local collection sync removes only that skill's superseded installer record; unrelated metadata remains intact.

Upstream [PR #2301](https://github.com/vercel-labs/skills/pull/2301) adds automatic
global ownership records for local-path installs. It is not in the pinned
`skills@1.7.0`; see the [versioned research](docs/verification/local-install-ownership.md).
When a configured installer writes matching local-source records during sync's
verified staging installation, sync prints a deprecation warning for the manual
ownership-bootstrap workaround. No enable flag or guessed version threshold is
used. Detection checks both the staged XDG state lock and the legacy `.agents`
lock. Dry runs and unchanged syncs do not invoke the installer, so they do not
probe or warn about this capability. A future pin update or an explicit
`SKILLS_SYNC_INSTALLER` override can activate detection.

The warning does not retire collection sync or its state file: edit protection,
approved migrations and recoverable pruning still depend on them. It does not
alter existing conflicts, adopt unknown installations, or recommend removing
existing files. For new direct installs with a fixed installer, normal
`skills add <local-path> --global` records provenance automatically. Existing
untracked or edited copies still need review.

Resolve ordinary conflicts by reviewing the installed copy, saving its edits into the authoritative source where appropriate, and preserving a separate backup. When deliberately replacing a legacy/manual installation, explicitly remove it with the installer after that review, then run sync. Do not fabricate ownership records or delete evidence merely to bypass protection. The five approved transfers are recorded explicitly in both collection configurations; arbitrary same-name collisions remain conflicts.

## Installation and failure behavior

Sync invokes the existing CLI with subprocess argument lists in a disposable home and contained config/cache directories. It compares all files and executable bits and verifies the Claude link before promoting eligible output. An installer partial failure or verification failure leaves the previous installations and ownership untouched. Promotion keeps temporary backups and rolls back targeted files and metadata on ordinary I/O exceptions. It rechecks source and ownership evidence before promotion. Cooperating sync processes serialize through an advisory lock on the existing home directory. Do not run other installers or edit installed files concurrently; abrupt process termination or power loss during promotion is not a crash-recovery guarantee.

`SKILLS_SYNC_INSTALLER` is an optional JSON argument list for an inspected installer executable or a deterministic test substitute; it is never shell-evaluated. Tests exercise `just sync` and `just sync-dry-run` with temporary Git repositories and disposable homes/caches. `tests/real_smoke.py` exercises first installation, updates, resources, both agents and repeat idempotence with the real pinned CLI. It downloads only into a disposable npm cache by default; `SKILLS_REAL_INSTALLER='["node","/absolute/path/to/skills/bin/cli.mjs"]'` reuses an already inspected installer without modifying its installation.

Public default-branch GitHub URL and shorthand installation passed the [published consumer check](docs/verification/ticket-6.md). A subsequent local sync reported protected conflicts and preserved the remote installation and ownership; review conflicts using the process above.

## Obsolete skills, migration and recovery

Both personal checkouts are listed in `collection-sync.json`. Paths resolve from the invoking checkout; the shipped configuration expects sibling `my-skills` and `my-cubrid-skills` directories. Topic worktrees or different layouts can pass `just sync --config /absolute/path/config.json` with the same identities and correct absolute peer paths. Every configured peer must scan successfully before pruning. A missing peer, wrong identity, incomplete source directory, unreadable content or malformed evidence protects stale installations; independent eligible additions and updates can still succeed with exit 2. Intentionally empty collections retain their skill container.

Sync identifies obsolete names only from successful ownership records, verifies current installation work first, then removes unchanged obsolete owned copies that no other configured collection supplies. Edited, manual and third-party skills are protected. Any current installation conflict suppresses all pruning for that collection, while independent installation work can proceed. Any installer or verification error prevents all promotion and pruning. Deletion means removing the whole source skill directory; a remaining directory without `SKILL.md` is incomplete evidence.

The approved migration policy names `gh-pr-comments-all`, `resolve-greptile-comments`, `markdown-write`, `question-socratically` and `track-work`, from `vimkim/my-cubrid-skills` to `vimkim/my-skills`. The destination verifies the previous state fingerprint (or existing old-source installer metadata and matching source bytes), installs and verifies its new content, then changes ownership. Untracked legacy copies still require the conflict review above. When the former source runs first and the destination already supplies the name, it preserves the installation. After transfer the former source cannot prune it, even if its checkout still contains the old source. This ordering permits destination verification before deleting original source files.

Before pruning, sync verifies a content backup and writes a manifest with ownership and the skill's installer metadata under `~/.local/state/skill-collections/recovery/removed-*` (or the configured `XDG_STATE_HOME`). It prints `recovery: /absolute/path`. Restore the reported directory with:

```sh
just sync-dry-run --restore /absolute/path/to/recovery/removed-XXXX
just sync --restore /absolute/path/to/recovery/removed-XXXX
```

Restore checks fingerprints, refuses to overwrite any existing installation or ownership, recreates the Claude link, and restores the saved state and metadata. Recovery copies remain available afterward. Restore the corresponding source directory before the next normal sync to avoid intentionally pruning it again. Explicit `just remove` is a separate installer operation and has no recovery snapshot.

The old collection vendors an identical copy of `scripts/sync_skills.py` at `tools/sync_skills.py`, so it can synchronize without importing unpublished code from another checkout. This repository is the authoritative engine source: update both copies together and verify the old entry point with `python3 tests/check_vendored_sync.py /path/to/my-cubrid-skills`. The check reads real source metadata but confines all installation/removal/recovery work to temporary checkouts and homes. The public-command suite covers both processing orders, all five names, local/GitHub metadata transitions, failures, conflicts, and actual restoration.

## License and provenance

The migrated skills retain the source collection’s **MIT** declaration. [Provenance](docs/migration.md#provenance) records the original repository, revision, authorship and complete resource fingerprints.
