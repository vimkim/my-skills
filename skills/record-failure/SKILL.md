---
name: record-failure
description: "Record recurring workflow, skill, hook, or tool failures in failure-tracker so later improvement runs can fix root causes. Use when a workflow command, skill instruction, hook, or automation fails or causes rework, when close-gate flags an unpersisted workflow defect, or when asked to log a failure or mistake (for example, 'record this failure', 'log failure', '이 실수 기록해둬')."
---

# Record Failure

Record one concrete failure occurrence in `failure-tracker` so recurring patterns accumulate and can be fixed structurally.

## 1. Preflight the tracker

```bash
failure-tracker doctor --json
```

If `failure-tracker` is missing, stop and tell the user to install it from its repository with `just sync`. A `warn` for an uninitialized database or unset `FAILURE_TRACKER_ACTOR` is fine. Stop and report if any required check fails or `doctor` exits nonzero.

## 2. Identify the fix owner and stable pattern

Assign `--repo` to the repository that owns the fix (for example `my-skills`, `work-tracker`, or `my-workflow`), `--ref` to the concrete file, skill, or module path, and `--kind` to one of:

- `tool_bug`: CLI, script, or automation bug.
- `rule_drift`: mismatch between documented rules and actual implementation.
- `skill_gap`: missing, stale, or ambiguous skill instruction.
- `hook_failure`: hook or scheduled unit failure.
- `env_drift`: missing tool, stale path, or host environment mismatch.
- `agent_mistake`: recurring agent reasoning or execution mistake.

Check existing patterns for that repo when unsure whether a matching pattern already exists:

```bash
failure-tracker list --repo "<repo>" --json
```

Keep `--title` (or `--fingerprint-key`) canonical and free of volatile IDs, timestamps, or commit SHAs so repeated occurrences group under the same pattern.

## 3. Record the occurrence

```bash
failure-tracker record \
  --repo "<repo>" \
  --ref "<path/to/file-or-skill>" \
  --kind "<kind>" \
  --title "<canonical pattern title>" \
  --symptom "<observed error or misbehavior>" \
  --actor "<actor>" \
  --json
```

Pass `--root-cause`, `--severity <high|normal|low>`, `--command`, `--exit-code`, `--work-item`, `--workdir`, and `--conversation-id` whenever known. Store only redacted evidence; exclude tokens, passwords, and private keys.

## 4. Report the recorded pattern

Report the returned `pattern.id`, `created` or `reopened` state, and `occurrence_count`, and state whether the defect needs immediate repair now or belongs in a later `improve-failures` batch.
