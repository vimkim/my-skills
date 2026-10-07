# pr-review-guide verification

Checked on 2026-10-07 in `/home/vimkim/gh/my-skills-pr-review-guide`, branch
`feat/pr-review-guide`, based on local `main` at `7847a1f`.

## Scope

The skill is general-purpose and writes Korean reviewer documentation from
committed PR changes. Its output destination is independent of the analyzed
source repository. For this user's CUBRID work it defaults to the available
`my-cubrid-docs` knowledge repository, following that repository's ticket and
index guidance. An explicit output path takes precedence.

The central explanation separates a symbol's responsibility from the reason
this PR changes it. The workflow includes revision selection, evidence
classification, change coverage, new/removed symbols, cross-cutting effects,
observed verification, and a linked reviewer-question index.

## Source and integration checks

- Skill-creator structural validation passed:
  `uv run --no-project --with pyyaml python /home/vimkim/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/pr-review-guide`.
- `just sync-dry-run` exited 0 and reported `add: pr-review-guide`; all seven
  existing skills were unchanged. This exercised collection discovery without
  installing or publishing anything.
- `just test` ran 28 tests: 27 passed and the existing migration fingerprint
  assertion for `skills/question-socratically/SKILL.md` failed. The same failure
  was reproduced on unchanged local `main` at `7847a1f` using
  `python3 -m unittest discover -s tests -p test_migration_inventory.py -v`.
  The actual SHA-256 is
  `1a89de149ab571be190d8a8285f89ab3d4bc3b84907d6925ab2cad1db8d87ec4`, while
  the historical manifest expects
  `f4a7761b509e94aab549b5aab92f0fcd263c5d521ed190bd52c360272dbe79bf`.
  This task does not alter that skill or migration provenance.
- `git diff --check` passed.

## Representative walkthroughs

The creating agent manually followed the skill for three synthetic Python Git
repositories and wrote Korean guides outside the task worktree. Each repository
had detached HEAD, staged and unstaged changes to a tracked local note, an
untracked scratch file, and a target `main` that advanced independently after
the PR branch diverged. PR/issue/CI metadata and hosted source URLs were absent;
the guides recorded local-only evidence and those limitations.

| Case | Change and reviewer explanation checked | Observed execution |
| --- | --- | --- |
| Bug fix | `run_with_retries` now includes the initial attempt in addition to the retry budget. The guide distinguishes the shared retry responsibility from the loop-bound correction and traces budgets 0 and 1. | Previous budget 0 raised `TypeError`; all 4 HEAD tests passed. |
| New struct/function | A payload/count tuple becomes a frozen `Receipt`, constructed by `make_receipt`; callers switch from indexing to named fields. The guide identifies the old representation, moved construction responsibility, return-contract dependency, and compatibility cost. | All 4 HEAD tests passed. An old caller with the new result raised `TypeError`; a new caller with the old result raised `AttributeError`. |
| Refactoring | `_normalized_label` replaces `_trim` plus duplicated lowercase operations. The guide locates the removed helper's responsibility and explains maintenance rationale without alleging a runtime defect in the old implementation. | All 3 existing HEAD tests passed. Both revisions produced equal results for spaces/case, empty strings, and mixed Korean/Latin input. |

The new-symbol case also checked a subtle invariant: directly constructing
`Receipt(b'a', 9)` succeeds. Its guide limits the length-consistency claim to
the factory path instead of treating frozen fields as constructor validation.

For all three generated guides:

- Merge-base differed from target tip, and merge-base-to-HEAD excluded the
  target-only file.
- Full HEAD, target and merge-base SHAs were present. Nine `git show` evidence
  lookups collectively resolved to the recorded HEAD or merge-base snapshots;
  described source lines were inspected manually.
- All 19 explicit section anchors were unique within their guide, and all 38
  contents/question/file links resolved to an anchor or existing local file.
- HEAD remained detached. The Git index and every working file retained their
  recorded SHA-256, and staged/unstaged/untracked status remained unchanged.
- Major-change coverage and the applicable symbol questions were reviewed
  manually. Executed tests and missing verification were identified separately.

Disposable walkthrough repositories, guides, test logs, the revision manifest,
and link/state check results were retained for this review in
`/home/vimkim/tmp/pr-review-guide-walkthrough-g47f0wik/`. They are synthetic
validation inputs and outputs, not a guide to an actual PR.

## Limits

These were manual walkthroughs by the creating agent, not independent model
forward tests. Structural validation, link checks, and fixture tests do not
establish that every future model run will investigate a large PR adequately.
Hosted PR discovery, mismatched/ambiguous remote metadata, inaccessible review
discussions, rendered viewer links, and writing a ticket/index in
`my-cubrid-docs` were not exercised. The destination rules were checked against
the live documentation repository's guidance, but that repository was not
modified. Global installation and publication remain outside these checks.
