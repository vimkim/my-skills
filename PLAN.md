# Personal skills collection plan

Status: draft for discussion, 2026-10-01. This document records the requested outcome and a proposed implementation. Open decisions below must be resolved before it becomes an implementation spec.

## Requested outcome

Use `/home/vimkim/gh/my-skills` as the Git-backed home and backup for personal skills that are not specific to CUBRID, following the pattern of `/home/vimkim/gh/my-cubrid-skills`. Publish the collection at `github.com/vimkim/my-skills`. Extract selected general-purpose skills from the CUBRID collection and integrate installation, updates, stale detection, and pruning with `daily-update`.

## Existing behavior inspected

- The destination directory was empty and had no Git repository. A local `main` baseline and a documentation worktree were created for this plan. The user selected a public repository, and `https://github.com/vimkim/my-skills` was created. The plan is published on its review branch; implementation remains pending.
- `my-cubrid-skills/AGENTS.md` treats its repository as the source of truth and installed copies as generated artifacts. At commit `795015e`, its justfile exposes `sync`, `sync-dry-run`, `list`, and `remove`. `sync` delegates to `tools/sync-skills.sh`, which prunes stale names before adding the current local collection through the skills CLI.
- `/home/vimkim/.config/my-scripts/bin/daily-update` runs global skills updates. Its `PERSONAL_REPO` points only to `my-cubrid-skills`; it does not explicitly reinstall that local collection.
- Its stale detection uses the global skills lock and protects names found in the personal collection. Local-path installs are described by the script as absent from that lock. This assumption needs a disposable-environment check before implementation.
- Normal daily updates report stale skills; `--prune` performs removal. Removed directories and a lock backup are retained in dated trash.
- The script identifies `~/.agents/skills` as the shared store and `~/.claude/skills` as links into it. Its existing boundary excludes `~/.codex/skills`; verify the installed CLI's actual behavior before changing destinations.

## Recommended workflow

Start with a short `/grill-with-docs` session to resolve the decisions below. Then use `/to-spec` to write a buildable contract. This is small enough to avoid `/wayfinder` and does not currently need a prototype.

If implementation fits one session, proceed to `/implement` after the decisions are recorded. If it will span sessions or separate repository changes, use `/to-tickets` and implement in dependency order. Tickets produced from the spec do not need triage. Configure the Matt workflow's tracker and document layout through `/setup-matt-pocock-skills` before starting that engineering flow.

This turn uses `/ask-matt` for routing; the interview and later engineering skills have not been run.

## Proposed repository contract

- `my-skills` becomes the authoritative editable source for migrated general-purpose skills; GitHub provides the remote backup.
- Use `skills/<name>/SKILL.md`, with supporting resources beside each skill, so the collection follows an explicitly documented discovery layout.
- Add a README with an inventory and installation instructions, repository guidance describing the source/installed-copy distinction, and a `justfile` consistent with the existing collection.
- Keep CUBRID-specific skills in `my-cubrid-skills`. Resolve generic skills' CUBRID dependencies before moving them.
- Keep existing skill names where possible so invocations and dependent skills continue to work.
- Ignore disposable generated outputs narrowly; track supporting resources needed for the skills to function.

## GitHub URL installation requirement

The user explicitly requires installation through the Vercel `skills` CLI by providing this repository's GitHub URL. The CLI documents full GitHub URLs, repository shorthand, discovery under `skills/`, and agent selection. See the [upstream README](https://github.com/vercel-labs/skills#readme), checked 2026-10-01.

The published collection must support:

```sh
# Discover available skills without installing
npx skills add https://github.com/vimkim/my-skills --list

# Install all collection skills globally for the intended agents
npx skills add https://github.com/vimkim/my-skills --skill '*' -g -a claude-code -a codex -y

# Equivalent repository shorthand
npx skills add vimkim/my-skills --skill '*' -g -a claude-code -a codex -y
```

These are target commands for the completed collection. The repository currently contains no skills, so installation is not yet ready. Publish skills on the default branch before validating the plain repository URL.

Keep GitHub URL installation available to consumers. On this host, use the collection’s local `just sync` interface as the proposed daily-update integration. Validate URL installation and local synchronization separately, including transitions between the two sources.

## Reuse the revamped sync interface

Use `my-cubrid-skills` commit `795015e` as the baseline. Its justfile now contains:

- `sync`: run `tools/sync-skills.sh` to prune deleted or renamed skills and then install the current collection.
- `sync-dry-run`: preview stale candidates and current names without mutation.
- `list`: list installed skills for the configured agents.
- `remove skill`: explicitly remove a named installed skill.

Adopt `sync` and `sync-dry-run` here. The previous proposal for `install`, `reinstall`, `install-published`, and global update recipes is superseded. Document the direct GitHub URL command separately. Keep third-party skill management outside this collection's justfile; the existing list/remove commands themselves are global views/actions rather than collection-filtered operations.

Reuse the helper as well as the justfile, adapting these concrete details:

- Its current and historical discovery assumes `<name>/SKILL.md`; adapt both to this plan's `skills/<name>/SKILL.md` layout.
- Historical names come from `git log --all`; any name present in the global lock is excluded from removal, regardless of its recorded source. Git history is candidate evidence, not proof of current installation ownership.
- A skill moved into another local collection may have no lock entry. Protect destination-owned names before either collection syncs so the old collection cannot delete the migrated copy.
- Pruning happens before installation, so an installation failure can leave removed skills absent. Define recovery before adopting this sequence for automated daily runs.

Validate recipe parsing, dry-run behavior, and migration behavior in a disposable home. This inspection read the helper; it did not run a live sync or validate its deletion behavior experimentally.

## Migration candidates

These are candidates from the existing tree, not an approved move list or a completed dependency audit.

| Candidate | Initial assessment |
| --- | --- |
| `gh-pr-comments-all` | General GitHub workflow; inspect references and resources before moving. |
| `resolve-greptile-comments` | General GitHub workflow; retain its authorization behavior. |
| `markdown-write` | Explicitly repository-agnostic; migrate its supporting resources together. |
| `question-socratically` | General dialogue workflow. |
| `track-work` | General work tracking; audit consumers in both collections. |
| `daily-schedule` | Contains explicit CUBRID repository and CI assumptions; keep initially or generalize through a separately agreed change. |
| `my-cubrid-skills-create` | Collection-specific; keep in the CUBRID collection and decide separately whether a generic creation workflow is needed. |

For every selected skill, inventory supporting files, cross-skill references, hard-coded source paths, external commands, and provenance/license obligations. Preserve required resources and history attribution. Install and verify the destination copy before removing the original source. Update inventories and references in both repositories as part of the migration.

## Proposed daily-update behavior

Represent both personal collections explicitly and have daily-update invoke their `just sync` interface. Collection sync owns refreshing and pruning its skills. Do not duplicate that logic in daily-update or add third-party management recipes to this repository. Existing unrelated daily-update behavior remains outside this change's scope.

Before automating sync, establish ownership across both collections so migrations survive either processing order. Preserve manually managed skills and other-source installations. Missing repositories, failed scans, and failed installs must not be treated as source deletions. Use the CLI's existing metadata where sufficient and add only the missing ownership or migration protection.

The adopted sync contract includes pruning during sync; it supersedes the earlier proposal that collection pruning occurs only through `daily-update --prune`. A dry run must show what collection sync would remove. Specify recoverability and failure behavior in the implementation spec; the current helper does not provide the dated-trash mechanism used by daily-update's existing prune path.

Locate the version-controlled source of the deployed daily-update script before editing it; the deployed directory itself did not resolve as a Git worktree during inspection. Decide separately whether daily-update refreshes source checkouts before syncing; sync itself currently does not pull Git changes.

## Decisions for the interview

1. Resolved: write the plan and create a public GitHub repository. This does not expand this turn into skill migration or daily-update implementation.
2. Does “backup” mean this repository becomes the editable source of truth, as proposed, or mirrors skills authored elsewhere?
3. Which migration candidates belong in the first batch? Recommendation: the five general-purpose candidates above; defer `daily-schedule`.
4. Resolved: support GitHub URL installation and reuse the collection-only `sync` interface. Proposed host integration: daily-update calls local `just sync`. Should it also refresh clean source checkouts first?
5. Resolve migration ownership and recovery for sync pruning before enabling automated runs. The interface now includes pruning as part of sync.

## Implementation slices

These are planning slices, not published tickets.

1. **Repository foundation:** settle visibility and source-of-truth policy; create the remote; add repository guidance, inventory, and installation interface. Done when a disposable install discovers the intended skills and resources.
2. **Installation and ownership:** locate the daily-update source repository; support both collections; verify actual installer behavior and persist ownership safely. Done when repeated updates are idempotent and failures preserve existing installations.
3. **Migration and pruning:** depends on slices 1 and 2. Move the agreed skills, update references, transfer ownership, and implement stale detection and recoverable removal. Done when migrated skills survive pruning and genuinely removed managed skills can be recovered from trash.
4. **Verification and documentation:** depends on slice 3. Run isolated end-to-end checks, document recovery and operation, and review the final changes in each repository.

Each affected repository follows the user's topic-worktree workflow: scoped commits, relevant checks, clean task status, review before merging. Remote publication and live installation follow the scope agreed for implementation.

## Acceptance checks for implementation

- In a fresh disposable home without a local checkout, the plain GitHub URL lists and installs every intended skill and supporting resource for the configured agents. Repository shorthand also works.
- A second update makes no unintended changes; publishing a source change refreshes its installed copy. Newly published skills are discovered and installed according to the agreed collection policy.
- A migrated skill remains installed through updates and pruning regardless of collection processing order.
- Removing a managed source skill produces a stale candidate; `sync-dry-run` previews it and `sync` removes it with the agreed recovery mechanism and ownership handling.
- Missing repositories, network failures, malformed state, incomplete scans, and failed installs do not cause removal or loss of the last working copy.
- Manual skills, other-source skills, edited installations, and same-name collisions are handled without silent data loss.
- Existing unrelated daily-update behavior remains functional; the collection justfile contains no third-party update recipes.
- Source scans find no broken migrated paths or missing resources; repository diffs contain only the agreed changes.

Use fixtures and a disposable home for destructive-path tests. Do not use the live skills store to discover pruning semantics.
