# Personal skills collection plan

Status: draft for discussion, 2026-10-01. This document records the requested outcome and a proposed implementation. Open decisions below must be resolved before it becomes an implementation spec.

## Requested outcome

Use `/home/vimkim/gh/my-skills` as the Git-backed home and backup for personal skills that are not specific to CUBRID, following the pattern of `/home/vimkim/gh/my-cubrid-skills`. Publish the collection at `github.com/vimkim/my-skills`. Extract selected general-purpose skills from the CUBRID collection and integrate installation, updates, stale detection, and pruning with `daily-update`.

## Existing behavior inspected

- The destination directory was empty and had no Git repository. A local `main` baseline and a documentation worktree were created for this plan. GitHub lookup could not resolve `vimkim/my-skills`; creation and visibility remain pending.
- `my-cubrid-skills/AGENTS.md` treats its repository as the source of truth and installed copies as generated artifacts. Its `justfile` installs from the local path with `npx skills add . -y -g --agent claude-code --agent codex`.
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
- Keep one top-level directory per skill, containing `SKILL.md` and its required scripts, references, and assets.
- Add a README with an inventory and installation instructions, repository guidance describing the source/installed-copy distinction, and a `justfile` consistent with the existing collection.
- Keep CUBRID-specific skills in `my-cubrid-skills`. Resolve generic skills' CUBRID dependencies before moving them.
- Keep existing skill names where possible so invocations and dependent skills continue to work.
- Ignore disposable generated outputs narrowly; track supporting resources needed for the skills to function.

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

Represent both personal collections explicitly. Normal updates install or refresh their skills and report stale managed installations. Preserve explicit `--prune` removal as the default proposal.

Installation ownership is the central requirement. Record which collection successfully installed each skill, and enough identity information to recognize subsequent edits or replacement. A missing directory, failed fetch, failed install, or incomplete scan is not evidence that its skills were deleted.

Compute current skill ownership across both collections before offering prune candidates. Moving a name between collections must transfer ownership without deleting the newly installed copy. Ambiguous collisions must be reported and resolved rather than silently overwritten. Skills installed manually, supplied by other sources, or modified after installation must remain protected unless their ownership and removal eligibility are established.

Only record a successful installation after verifying its result. Only propose a removed skill when the owning collection was successfully inspected and no configured collection currently supplies it. Preserve recoverable trash and metadata backups during pruning. Failed refreshes must retain the previous working installation and ownership state.

The exact manifest format and installer adapter belong in the spec after checking actual CLI behavior. Locate the version-controlled source of the deployed `daily-update` script before editing it; the deployed directory itself did not resolve as a Git worktree during inspection.

## Decisions for the interview

1. Is this turn planning only, or should it also create the GitHub repository? If creating it, public or private?
2. Does “backup” mean this repository becomes the editable source of truth, as proposed, or mirrors skills authored elsewhere?
3. Which migration candidates belong in the first batch? Recommendation: the five general-purpose candidates above; defer `daily-schedule`.
4. Should daily updates install from the local checkout, or fetch the published branch first? Recommendation: follow the local collection model initially and make remote refresh policy explicit; never discard local changes.
5. Should pruning stay behind `daily-update --prune`, as proposed, or happen automatically on normal runs?

## Implementation slices

These are planning slices, not published tickets.

1. **Repository foundation:** settle visibility and source-of-truth policy; create the remote; add repository guidance, inventory, and installation interface. Done when a disposable install discovers the intended skills and resources.
2. **Installation and ownership:** locate the daily-update source repository; support both collections; verify actual installer behavior and persist ownership safely. Done when repeated updates are idempotent and failures preserve existing installations.
3. **Migration and pruning:** depends on slices 1 and 2. Move the agreed skills, update references, transfer ownership, and implement stale detection and recoverable removal. Done when migrated skills survive pruning and genuinely removed managed skills can be recovered from trash.
4. **Verification and documentation:** depends on slice 3. Run isolated end-to-end checks, document recovery and operation, and review the final changes in each repository.

Each affected repository follows the user's topic-worktree workflow: scoped commits, relevant checks, clean task status, review before merging. Remote publication and live installation follow the scope agreed for implementation.

## Acceptance checks for implementation

- A fresh disposable home receives the intended skills and supporting resources for the configured agents.
- A second update makes no unintended changes; modifying a source skill refreshes its installed copy.
- A migrated skill remains installed through updates and pruning regardless of collection processing order.
- Removing a managed source skill produces a stale report; explicit pruning moves the eligible installation into recoverable trash and updates ownership metadata.
- Missing repositories, network failures, malformed state, incomplete scans, and failed installs do not cause removal or loss of the last working copy.
- Manual skills, other-source skills, edited installations, and same-name collisions are handled without silent data loss.
- Existing global updates and reminder behavior remain functional.
- Source scans find no broken migrated paths or missing resources; repository diffs contain only the agreed changes.

Use fixtures and a disposable home for destructive-path tests. Do not use the live skills store to discover pruning semantics.
