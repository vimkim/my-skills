---
name: improve-failures
description: "Triage recorded failure patterns from failure-tracker and run parallel workers to fix root causes across repositories. Use when asked to improve recorded workflow, skill, or tool failures, run a self-improvement batch, or resolve recurring mistakes (for example, 'improve failures', 'self-improve workflow', '기록된 실패 개선해줘', '실패 패턴 병렬 개선')."
---

# Improve Failures

Triage open patterns in `failure-tracker`, dispatch isolated workers across repositories, verify every fix, and update the ledger.

## 1. Preflight and select candidates

```bash
failure-tracker doctor --json
failure-tracker list --status open --json
```

If `doctor` fails a required check or `failure-tracker` is missing, stop and report.

Prioritize patterns with `severity == "high"` or `occurrence_count >= 2` unless the user targets a specific pattern ID. Exclude patterns with `failed_attempts >= 2` from automatic dispatch and surface them for human triage.

## 2. Shard by repository and isolate writes

Group eligible patterns by `target_repo` so different repositories run in parallel without shared-state conflicts.

When multiple patterns target the same repository:

- Run only disjoint `(target_repo, target_ref)` work concurrently, each in its own sibling Git worktree on branch `improve/failure-<id>`.
- Serialize the final rebase and merge step per repository.
- Leave overlapping `target_ref` patterns for sequential handling or merge them via `resolve --status duplicate --duplicate-of <id>`.

Have each worker claim its target atomically before editing:

```bash
failure-tracker claim --repo "<repo>" --actor "<worker-id>" --ttl 30m --json
# or for an explicit pattern ID:
failure-tracker claim --id <id> --actor "<worker-id>" --ttl 30m --json
```

Use `--actor` consistently across `claim`, `attempt`, and `resolve`. Inspect the returned `occurrences` and `attempts` before designing a patch so you do not repeat a failed approach.

## 3. Enforce the fix hierarchy

Apply the highest-leverage structural fix that eliminates the failure class:

1. `code_or_check`: fix the CLI, script, hook, lint, preflight check, or automated test so the failure is blocked mechanically.
2. `delete_or_fix_doc`: repair stale paths, outdated commands, or contradictory instructions, or delete dead prose.
3. `add_doc`: add concise positive guidance and one concrete failure example only when the rule requires judgment that code cannot enforce.

## 4. Verify, integrate, and update the ledger

Run the target repository's real verification suite (`just check`, `just test`, drift check, or CLI smoke test) against the edited checkout.

Integrate according to the target repository's integration tier:

- Authorized solo repositories (Tier 1): rebase onto the destination branch, merge `--ff-only`, push when authorized, and clean up the sibling worktree and topic branch.
- Shared or upstream repositories (Tier 2), or changes that alter major global policy: keep the verified branch or PR ready for explicit human approval.

Record the verified outcome in `failure-tracker`:

```bash
failure-tracker resolve <id> \
  --fix-layer "<code_or_check|delete_or_fix_doc|add_doc>" \
  --commit "<sha>" \
  --verify "<verification command>" \
  --actor "<worker-id>" \
  --note "<summary of fix and check output>" \
  --json
```

If a worker fails, hits a blocker, or stops early, release the lease and preserve diagnostics:

```bash
failure-tracker attempt <id> \
  --outcome "<failed|blocked|abandoned>" \
  --actor "<worker-id>" \
  --note "<failure reason and next step>" \
  --json
```

## 5. Report batch results

Summarize resolved patterns (`#ID`, `fix_layer`, commit, verification), escalated patterns (`failed_attempts >= 2` or `blocked`), and remaining open patterns.
