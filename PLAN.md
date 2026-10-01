# Personal skills collection plan

Status: draft for discussion, 2026-10-01. This document records the requested outcome and a proposed implementation. Open decisions below must be resolved before it becomes an implementation spec.

## Requested outcome

Use `/home/vimkim/gh/my-skills` as the Git-backed home and backup for personal skills that are not specific to CUBRID, following the pattern of `/home/vimkim/gh/my-cubrid-skills`. Publish the collection at `github.com/vimkim/my-skills`. Extract selected general-purpose skills from the CUBRID collection and integrate installation, updates, stale detection, and pruning with `daily-update`.

## Existing behavior inspected

- The destination directory was empty and had no Git repository. A local `main` baseline and a documentation worktree were created for this plan. The user selected a public repository, and `https://github.com/vimkim/my-skills` was created. The plan is published on its review branch; implementation remains pending.
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

Proposed default: use the GitHub source for normal installation and reserve local-path installation for development. Confirm the daily-update source policy during the interview. Prefer the CLI's existing source metadata and update behavior; add ownership state only for demonstrated gaps. Validate initial installation, discovery of newly added skills, updates to existing skills, and deleted-skill handling separately.

## Reuse the existing justfile

Use `my-cubrid-skills/justfile` as the starting point for this collection's command interface. It already wraps the skills CLI: `just install` runs `npx skills add . -y -g --agent claude-code --agent codex`, and `reinstall` aliases `install`. The local `cubrid-build` installation exists in the shared store, with a Claude symlink, and no matching entry was found in the global lock during inspection. This is consistent with the existing local-path installation workflow; it does not establish which historical command installed it.

Proposed small improvements when implementing the justfile:

- Keep `install` and `reinstall` for installing the current checkout; explicitly select all collection skills with `--skill '*'`.
- Add `install-published` for installing `https://github.com/vimkim/my-skills` with the same agent and scope choices. Document which source each recipe uses.
- Keep `list` and add a discovery recipe that lists this collection's available skills without installing.
- Make `update` refresh only this checkout with `git pull --ff-only` and reinstall this collection. Keep the all-collections global update as a separately named recipe; the existing `update` mixes both scopes.
- Validate supported flags against the actual CLI before copying `update-installed`; its existing agent flags must not be assumed to filter updates.
- Quote the skill argument safely and specify the intended agents for explicit removal. Collection-wide stale pruning remains the responsibility of `daily-update`.

The justfile is a convenience wrapper around the same CLI used by GitHub URL installation. It does not need a separate installer. Reusing it does not by itself implement stale-skill detection or pruning. Validate recipe parsing and dry-run output before running installs in a disposable home.

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

Whether additional ownership metadata is needed belongs in the spec after checking actual GitHub-source CLI behavior; do not assume a separate manifest is necessary. Locate the version-controlled source of the deployed `daily-update` script before editing it; the deployed directory itself did not resolve as a Git worktree during inspection.

## Decisions for the interview

1. Resolved: write the plan and create a public GitHub repository. This does not expand this turn into skill migration or daily-update implementation.
2. Does “backup” mean this repository becomes the editable source of truth, as proposed, or mirrors skills authored elsewhere?
3. Which migration candidates belong in the first batch? Recommendation: the five general-purpose candidates above; defer `daily-schedule`.
4. Resolved: the collection must install through `npx skills add` using its GitHub URL. Should daily-update also use that GitHub source (recommended), or retain local-checkout installation for this host? Local development changes must remain preserved.
5. Should pruning stay behind `daily-update --prune`, as proposed, or happen automatically on normal runs?

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
- Removing a managed source skill produces a stale report; explicit pruning moves the eligible installation into recoverable trash and updates ownership metadata.
- Missing repositories, network failures, malformed state, incomplete scans, and failed installs do not cause removal or loss of the last working copy.
- Manual skills, other-source skills, edited installations, and same-name collisions are handled without silent data loss.
- Existing global updates and reminder behavior remain functional.
- Source scans find no broken migrated paths or missing resources; repository diffs contain only the agreed changes.

Use fixtures and a disposable home for destructive-path tests. Do not use the live skills store to discover pruning semantics.
