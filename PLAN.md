# Personal skills collection plan

Status: interview decisions recorded, awaiting final shared-understanding confirmation. This document records the agreed behavior and proposed implementation work; it is not yet an implementation spec.

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

The `/grill-with-docs` interview resolved source ownership, migration scope, daily refresh behavior, conflicts, recovery, and implementation language. Final shared-understanding confirmation is pending; implementation has not begun.

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

Reuse the justfile interface and port the helper’s relevant behavior to Python, adapting these concrete details:

- Its current and historical discovery assumes `<name>/SKILL.md`; adapt both to this plan's `skills/<name>/SKILL.md` layout.
- Historical names come from `git log --all`; any name present in the global lock is excluded from removal, regardless of its recorded source. Git history is candidate evidence, not proof of current installation ownership.
- A skill moved into another local collection may have no lock entry. Protect destination-owned names before either collection syncs so the old collection cannot delete the migrated copy.
- The existing helper prunes before installation. Change this sequence: verify new installations before pruning and retain recoverable copies of removed skills. A failed installation must not trigger pruning.

Validate recipe parsing, dry-run behavior, and migration behavior in a disposable home. This inspection read the helper; it did not run a live sync or validate its deletion behavior experimentally.

## Implementation language

The user selected Python 3 for synchronization, with the standard library only. Keep justfile as the command interface and keep daily-update's existing Bash entry point, which invokes collection sync.

- Implement ownership tracking, file comparison, conflict handling, dry runs, and recovery in Python.
- Invoke git and npx skills through subprocess argument lists; retain the skills CLI as the installer.
- Require no third-party Python packages or virtual environment for normal operation.
- Port the existing shell helper's relevant behavior while applying the agreed ownership and failure rules; copying the shell helper unchanged is superseded.
- Use Python's standard-library test tools and disposable directories for behavioral verification. Select and document the minimum Python version during implementation after inspecting the target environment.

## Migration candidates

The user approved the first five skills below for migration. The dependency audit remains implementation work; daily-schedule and my-cubrid-skills-create stay in the CUBRID collection for this batch.

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

The adopted sync contract includes pruning during sync; it supersedes the earlier proposal that collection pruning occurs only through `daily-update --prune`. A dry run must show what collection sync would remove. Verify new installations before pruning, retain recoverable copies of removed skills, and report failures clearly. A failed collection must not prevent the other collection from syncing, but unresolved ownership must still prevent unsafe removal. The current helper does not yet provide this recovery contract.

Locate the version-controlled source of the deployed daily-update script before editing it; the deployed directory itself did not resolve as a Git worktree during inspection. The user approved daily-update fast-forwarding clean source checkouts before sync. Dirty or diverged checkouts are reported and skipped without modification. The collection sync command itself does not pull Git changes.

## Decisions for the interview

1. Resolved: write the plan and create a public GitHub repository. This does not expand this turn into skill migration or daily-update implementation.
2. Resolved: my-skills is the authoritative editable source for migrated skills. GitHub is the remote backup; installed copies are generated. Each skill belongs to one collection.
3. Resolved: migrate gh-pr-comments-all, resolve-greptile-comments, markdown-write, question-socratically, and track-work. Defer daily-schedule.
4. Resolved: support GitHub URL installation and reuse the collection-only sync interface. Daily-update fast-forwards clean checkouts, then calls local just sync. Report and skip dirty or diverged checkouts.
5. Resolved: report and skip directly edited installed skills or same-name conflicts with another collection. Resolve conflicts at the source before syncing again; explicitly transfer ownership for the five approved migrations.
6. Resolved: verify new installations before pruning, keep recoverable copies of removed skills, and report failures. Continue syncing the other collection when one fails, subject to ownership protection.

7. Resolved: implement synchronization in Python 3 using only the standard library; expose it through justfile and keep daily-update in Bash.

All interview behavior and language decisions are answered. The user’s final confirmation of the consolidated understanding is pending. CLI behavior, metadata representation, and migration mechanics require implementation investigation and verification rather than additional preference questions.

## Implementation slices

These are planning slices, not published tickets.

1. **Repository foundation:** the public remote and source-of-truth policy are settled; add repository guidance, inventory, and the sync interface. Done when a disposable install discovers the intended skills and resources.
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
- Directly edited installed skills and same-name conflicts are reported and skipped; approved migrations explicitly transfer ownership. Manual and other-source skills remain protected.
- A failed collection reports its failure while the other collection can still sync safely. Failed installation prevents pruning, and removed copies remain recoverable.
- Existing unrelated daily-update behavior remains functional; the collection justfile contains no third-party update recipes.
- Source scans find no broken migrated paths or missing resources; repository diffs contain only the agreed changes.

Use fixtures and a disposable home for destructive-path tests. Do not use the live skills store to discover pruning semantics.
