## Problem Statement

General-purpose personal agent skills currently live alongside CUBRID-specific skills. The user needs a dedicated, public source collection with a familiar synchronization command, installation from its GitHub URL, and daily maintenance that keeps installed skills current without losing local work or deleting skills transferred between collections.

The existing CUBRID collection sync helper uses historical skill names to identify removals and prunes before installation. Historical membership alone does not establish current ownership, especially after a migration between local collections. A failed installation can also leave previously removed skills unavailable. These behaviors must be addressed before automating synchronization across both collections.

## Solution

Make vimkim/my-skills the authoritative source collection for the agreed general-purpose skills. Preserve their names and resources, support installation through the Vercel skills CLI using the public GitHub URL or repository shorthand, and provide collection sync and a non-mutating preview through just.

Implement synchronization in Python 3 using only the standard library. Keep daily-update in Bash and let it refresh clean collection checkouts and invoke their sync interface. Protect conflicts and directly edited installed skills, explicitly transfer migration ownership, verify installation before pruning, and retain recoverable copies of removed skills.

## User Stories

1. As the collection maintainer, I want my-skills to be the authoritative source for general-purpose skills, so that I know where to edit them.
2. As the collection maintainer, I want GitHub to hold the public remote backup, so that the collection can be recovered and shared.
3. As a consumer, I want to install skills by supplying the GitHub repository URL to the skills CLI, so that I do not need a pre-existing checkout.
4. As a consumer, I want repository shorthand to work as well, so that installation is convenient.
5. As a consumer, I want to discover available skills without installing them, so that I can inspect the collection first.
6. As a user of Claude Code and Codex, I want the collection available to both configured agents, so that I can use the same workflows in either.
7. As the maintainer, I want each migrated skill's supporting resources preserved, so that its behavior remains usable after migration.
8. As an existing skill user, I want migrated skill names preserved, so that existing invocations continue to work.
9. As the maintainer, I want the five approved skills moved together, so that this first migration has a clear scope.
10. As a CUBRID collection user, I want the remaining skills and their references to continue working, so that extracting generic skills does not break specialized workflows.
11. As the maintainer, I want one collection sync command to reconcile additions, changes, and removals, so that separate install and reinstall workflows are unnecessary.
12. As the maintainer, I want a dry run to identify intended changes and conflicts without mutation, so that I can inspect synchronization safely.
13. As the maintainer, I want repeated syncs to converge without unintended changes, so that daily operation is predictable.
14. As the maintainer, I want newly added skills installed during collection sync, so that maintenance includes new content as well as existing installations.
15. As the maintainer, I want deleted and renamed skills removed when their ownership is established, so that obsolete installed skills do not linger.
16. As the maintainer, I want migration to transfer ownership explicitly, so that the former source collection cannot prune the destination's installed skill.
17. As the maintainer, I want either collection processing order to preserve migrated skills, so that safety does not depend on invocation order.
18. As a user with directly edited installed skills, I want conflicts reported and those skills skipped, so that sync does not silently overwrite my changes.
19. As a user with same-name skills from another collection, I want the conflict reported and skipped, so that ownership is not silently reassigned.
20. As a user with manually managed or third-party skills, I want collection sync to preserve them, so that its scope stays limited to the personal collection.
21. As the maintainer, I want new installations verified before stale skills are pruned, so that an installation failure does not trigger deletion.
22. As the maintainer, I want recoverable copies of removed skills, so that unintended removal can be repaired.
23. As the maintainer, I want missing repositories, failed scans, and malformed state treated as failures, so that unavailable evidence is not mistaken for source deletion.
24. As a daily-update user, I want clean checkouts fast-forwarded before sync, so that published changes reach my installed skills.
25. As a developer with a dirty or diverged checkout, I want that collection reported and skipped, so that daily maintenance preserves my work.
26. As a daily-update user, I want one collection's failure reported while the other can continue safely, so that an isolated problem does not stop all collection maintenance.
27. As the maintainer, I want the Python sync logic to require no third-party Python packages, so that operating it does not require managing a virtual environment.
28. As the maintainer, I want the collection justfile to avoid third-party update management, so that its purpose stays focused.
29. As the maintainer, I want failures and skips visible in command results, so that I can distinguish completed synchronization from partial work.
30. As the maintainer, I want tests to exercise public commands in an isolated environment, so that verification reflects user-visible behavior without risking live installed skills.

## Implementation Decisions

- **Source ownership:** my-skills is the authoritative editable collection for migrated skills; installed skills are generated copies. Each skill has one source collection. GitHub is the public remote backup.
- **Migration scope:** migrate gh-pr-comments-all, resolve-greptile-comments, markdown-write, question-socratically, and track-work. Preserve names, supporting resources, provenance, and applicable license obligations. Keep daily-schedule and my-cubrid-skills-create in the CUBRID collection for this batch.
- **Collection packaging:** use the skills CLI's documented skill-container layout with a directory per skill. Publish valid skill metadata and all required resources so discovery and installation work from the default branch through both the full GitHub URL and shorthand.
- **Command interface:** expose sync and sync-dry-run through just. Retain the familiar list and explicit remove conveniences with clearly documented scope. The collection interface does not manage third-party updates. GitHub URL installation remains a direct skills CLI operation.
- **Language and dependencies:** implement reconciliation, ownership checks, conflict detection, preview, and recovery in Python 3 using only its standard library. Invoke git and the skills CLI using subprocess argument lists. Keep the existing Bash daily-update entry point. Select and document the minimum supported Python version after inspecting the target environment.
- **Component boundaries:** keep collection reconciliation behind its public sync command. Daily-update coordinates repository refresh and collection invocation, without duplicating reconciliation logic. Use the existing installer for installation rather than creating a competing installation system.
- **Ownership evidence:** use existing installer metadata where sufficient and supplement demonstrated gaps. Historical membership can identify candidates but cannot by itself authorize removal. Record successful ownership transitions only after verifying the resulting installation. The exact metadata representation is an implementation choice constrained by these behaviors.
- **Conflict behavior:** detect directly edited installed skills and same-name ownership conflicts before overwriting or removing them. Report and skip the affected skill while allowing independent eligible work. Resolve ordinary conflicts in the source collection before retrying. The five approved migrations receive explicit ownership transfer rather than being treated as arbitrary name collisions.
- **Migration coordination:** audit dependencies and update references and inventories in both collections. Install and verify destination skills before removing their original source. Adapt the old collection's pruning behavior before migration can expose transferred skills to deletion. Protect migrated installations whether the old or new collection syncs first.
- **Reconciliation sequence:** inspect sources and ownership, identify conflicts, install eligible current skills, verify the result, then prune eligible obsolete skills. An installation or verification failure prevents pruning for that collection. Preserve the last working installation and ownership state on failure; the installer integration must accommodate partial failure rather than assuming the upstream CLI is transactional.
- **Pruning and recovery:** remove only obsolete installed skills whose ownership and eligibility are established and which are not supplied by another configured collection. Preserve recoverable copies and sufficient recovery information before removal. Report the recovery location and document restoration. Missing repositories, failed fetches, incomplete scans, or malformed state must not become evidence of deletion.
- **Dry run:** report planned reconciliation and conflicts without changing installed skills, ownership state, source checkouts, or recovery artifacts. Repeated successful syncs must be idempotent apart from incidental reporting.
- **Daily refresh:** daily-update fast-forwards clean, non-diverged collection checkouts before calling their local sync command. Report and skip dirty or diverged checkouts. Report failed refreshes and skip the affected collection's sync. Collection sync itself does not pull Git changes.
- **Failure isolation:** continue with another collection after a collection failure when its work is independently safe. Unknown ownership still blocks unsafe pruning. Report failures and skipped work clearly; preserve unrelated daily-update behavior.
- **Integration scope:** locate the version-controlled source of daily-update before changing it. Limit old-collection changes to the migration and compatible sync/ownership protection needed for the agreed behavior. A broad rewrite of its other tooling is not required.
- **Documentation:** document prerequisites, source ownership, GitHub installation, local sync, dry-run behavior, conflicts, recovery, and the distinction between repository refresh and installed-skill synchronization.

## Testing Decisions

- The user approved the public command interface as the primary testing boundary. Exercise sync and sync-dry-run through just, and daily-update through its existing entry point. Assert observable files, command results, recovery information, and ownership outcomes rather than Python helper structure.
- Use Python standard-library test tools, temporary collection repositories, and a disposable home. Ensure invoked tools' configuration and cache locations are contained; no test may mutate the live installed-skill store.
- Use controlled external-command substitutes for deterministic failure cases, plus a real skills CLI installation check in isolation. This establishes both failure behavior and compatibility with the actual installer.
- Verify GitHub URL and shorthand discovery and installation without an existing local checkout, including all resources and both intended agents. Validate the plain repository URL once the intended content is published on the default branch; branch-based checks alone do not establish that acceptance criterion.
- Verify first sync, source updates, newly added skills, repeat-sync idempotence, empty collections, removal, and rename behavior. Assert that dry runs leave the relevant filesystem and state unchanged.
- Exercise the five-skill migration with both collection invocation orders. Verify ownership transfer, preservation of destination-installed skills, and continued operation of remaining collection references. Include local-source and GitHub-source installation transitions.
- Exercise edited installed copies, manual installations, third-party ownership, and same-name conflicts. Verify the affected skills are reported and preserved while independent eligible work can proceed.
- Inject installer and verification failures, including partial installation, missing repositories, failed scans, incomplete source evidence, and malformed state. Verify failure cannot trigger pruning or silently lose the last working copy.
- Verify removed skills and associated recovery information can actually be restored, rather than merely asserting that a backup was created.
- Test daily-update against clean, dirty, diverged, and failed-refresh repositories. Verify clean refresh precedes sync, skipped repositories remain unchanged, one collection's failure does not stop safe work in another, and unrelated existing behavior remains functional.
- Prior art is the existing collection's shell sync command and dry-run interface. The new repository currently has no behavioral test suite; create tests at those existing user-facing boundaries rather than assuming an existing Python test architecture.
- Before implementation, inspect the live installer version and installation layout. Existing script comments and planning observations are evidence to verify, not permanent assumptions about installer behavior.

## Out of Scope

- Migrating additional skills, generalizing daily-schedule, or creating a generic replacement for my-cubrid-skills-create.
- Redesigning third-party skill management or adding third-party update recipes to the collection.
- Replacing the skills CLI, rewriting daily-update in Python, or introducing third-party Python dependencies.
- Silently overwriting edited installations, resolving ambiguous ownership by name alone, or discarding local repository changes.
- Building a general skill marketplace or a new cross-machine backup service.
- Implementing the feature, migrating live skills, or running destructive live-store tests as part of spec publication.
- Automatically merging, pushing implementation branches, or deploying changes without the authorization required by the user's repository workflow.

## Further Notes

The user confirmed the design interview, Python language choice, repository workflow configuration, and public-command testing boundary. This spec is ready for implementation planning without further triage.

The public repository and workflow documents already exist. The code, migration, and daily-update integration remain to be implemented. The inspected CUBRID collection baseline was commit 795015e; re-inspect current source before adapting its behavior.

Installer metadata format, the recovery representation, minimum Python version, and the deployed daily-update source location are engineering facts or implementation choices to resolve while preserving the agreed contract. Do not weaken conflict protection or recovery to fit an assumed installer behavior.

Local repository work must stay on review branches until the user approves rebase and fast-forward merge. Such approval does not authorize a push or deployment. Publishing this specification is authorized by the invoked to-spec workflow and is separate from executing it.
