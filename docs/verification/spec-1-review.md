# Spec #1 integration review

Reviewed on 2026-10-01 for [spec #1](https://github.com/vimkim/my-skills/issues/1).
Work-tracker item: **251**. One dedicated agent implemented each of tickets
#2–#6; the coordinating agent reviewed changes and reran public-command checks.
All issue bodies and comments were read before implementation (no comments were
present). Work followed #2 → #3 → (#4 and #5), with #6 released after #4 alone.

## Acceptance and implementation evidence

| Ticket | Reviewed implementation | Evidence and result |
| --- | --- | --- |
| #2 | `cdf1cf2` in my-skills | Public `just` commands, verified CLI staging, ownership baselines, protected edits/manual/foreign installs, nonmutating preview, rollback and documented requirements. All initial 13 command tests passed on Python 3.12 and 3.14; the coordinator independently passed the suite and the real CLI smoke with an isolated npm cache. |
| #3 | `4fa4816` in my-skills; `48497b1` in my-cubrid-skills | Deletion/rename, actual recovery of resources/modes/links/state/installer metadata, peer protection and explicit five-name transfers in both orders. All 26 command tests passed on Python 3.12 and 3.14. Coordinator reran the suite and the actual old `just`/Bash wrapper smoke; vendored engines match. |
| #4 | `8a2fe86` in my-skills; `4292b76` in my-cubrid-skills | Exactly five names and ten files migrated unchanged, with provenance and MIT declaration; 18 old skills remain. Coordinator passed 27 standard tests and seven actual-resource migration scenarios. Agent passed three real CLI scenarios, four preserved resource tests and JavaScript syntax validation. Destination installation was verified before original source removal. |
| #5 | `2cacf35` in dotfiles | The version-controlled Bash entry point refreshes clean checkouts before local sync, skips dirty/ahead/diverged/unavailable checkouts and continues independent collections. Coordinator passed all 13 entry-point tests, Bash syntax, ShellCheck and the target-only rendered chezmoi diff. Both orders, refresh/sync failures, malformed metadata and third-party isolation are covered. |
| #6 | `9a4024c` in my-skills | Consumer documentation and a real CLI validator are ready. The default `npx` local rehearsal passes; both real public source forms fail discovery with “No skills found” at published `main` commit `cca994efc008eec57e822805ccc152d9db957cce`. Full published installation and its local-sync transition remain unverified; this ticket stays open. |

The final sync implementation deliberately protects unverifiable legacy local
installations, even if their content currently matches a source. The real
`skills@1.7.0` installer does not record local-path ownership, so sync records a
verified baseline after successful installation. Existing trustworthy GitHub
metadata plus exact content can be adopted; ambiguous or changed content stays
protected. This behavior is covered by tests and documented in the README.

Review found and corrected these issues before dependent tickets proceeded:

- Preserve the existing global meaning of `just list`.
- Treat dangling and incomplete source directories, including peer directories,
  as incomplete evidence rather than deletion.
- Reject symlinked recovery destinations and suppress collection pruning when a
  current installation conflicts.
- Keep daily-update's bulk updater away from personal sources and name
  collisions; never turn an empty third-party selection into an unfiltered run.
- Propagate the first failed inventory scan and reject a nested directory that
  would otherwise refresh its parent Git repository.
- Give the consumer validator distinct isolated npm user/global config files.
  The coordinator's default `npx` run found a duplicate-config error that the
  initial cached-CLI invocation bypassed; the documented default path was then
  repaired and rerun.

## Reproducing checks

From this checkout, using the coordinated old checkout:

```sh
just test
python3 tests/real_smoke.py
python3 tests/check_vendored_sync.py /path/to/my-cubrid-skills
python3 tests/check_migration.py /path/to/my-cubrid-skills
python3 tests/check_migration.py /path/to/my-cubrid-skills --real
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/markdown-write/tests -v
node --check skills/markdown-write/scripts/check_mermaid_blocks.mjs
python3 tests/check_published.py --local --output /tmp/my-skills-local.json
```

From the dotfiles topic checkout:

```sh
python3 -B -m unittest discover -s tests -p test_daily_update.py -v
bash -n private_dot_config/my-scripts/bin/executable_daily-update
shellcheck private_dot_config/my-scripts/bin/executable_daily-update
chezmoi --source /path/to/dotfiles-worktree diff -- ~/.config/my-scripts/bin/daily-update
```

Tests use disposable repositories, homes, configuration and caches. Controlled
substitutes cover failures; real installer checks use pinned `skills@1.7.0`.
No test upgrades live tools, changes live installed skills, or deploys dotfiles.
Detailed evidence and prerequisites are in [migration documentation](../migration.md),
[ticket #2 evidence](ticket-2.md), and dotfiles `docs/daily-update.md`.
The [ticket #6 report](ticket-6.md) links complete local and published-attempt
JSON evidence, including CLI version, source commit, outcomes and resource hashes.

## Remaining authorization and completion gates

The implementation is committed on topic branches for review. The user-provided
AGENTS.md requires approval before rebasing and fast-forward merging into local
`main`. That approval does not authorize a push or live deployment. The dotfiles
managed target is exactly `~/.config/my-scripts/bin/daily-update`; a future
authorized deployment must be limited to that target.

Tickets #2–#5 have passed local implementation acceptance and remain open pending
approved integration. Ticket #6 and parent spec #1 remain incomplete until the
migrated content is explicitly authorized for publication on the GitHub default
branch and both plain URL and shorthand installation checks pass there. The
published source commit and CLI version must be retained with those results.
After authorized publication, run `python3 tests/check_published.py --output
/tmp/my-skills-published.json`; both source forms must pass and
`published_default_branch_verified` must be `true` before closing #6 or #1.

Promotion rolls back ordinary I/O failures but is not a power-loss or forced-kill
transaction guarantee. Cooperating syncs serialize; running unrelated installers
or editing installed files concurrently remains unsupported. Skill runtime
credentials and external services are prerequisites, not exercised by migration
tests of unchanged skill content.
