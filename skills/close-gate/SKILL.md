---
name: close-gate
description: Fail-closed audit before closing a session. Finds unpersisted bugs, unregistered issues, unresolved decisions, and live workspace loose ends. Use when asked whether a session, tab, or conversation is safe to close or wrap up.
---

# Close Gate

Audit whether this session can close without losing context, decisions, or follow-up work.

Keep the audit read-only: inspect and report options without modifying files, git state, trackers, or tabs.

## Gate rule

Start from `HOLD`. Apply the persistence test to every finding: if this session closes now, does the context, decision, or follow-up vanish? Items already persisted in a commit, issue tracker, PR, durable document, or work tracker with enough detail to resume are safe; session-only items block closing.

Clear to `CLOSE` only after checking every applicable dimension below with direct evidence and finding zero `HOLD` or `RECORD` items.

## Audit dimensions

1. **Full conversation scan** (start to finish, not only the latest task)
   - Bugs, regressions, risks, or tech debt discovered during the session and neither fixed nor filed.
   - External follow-ups promised or needed (such as JIRA/GitHub issues, PR comments, reviews, or handoffs) not yet filed or posted.
   - Decisions only the user can make (fix now vs. file later, merge/ship/discard, scope or ownership choices).
   - Deferred tasks, skipped checks, or unresolved failures with no durable home.
2. **Live workspace and runtime checks** (verify with read-only commands; skip tools or repos absent from this session and note why)
   - **Git**: uncommitted edits, untracked deliverables, stashes, unpushed commits, unmerged topic branches, or leftover worktrees (`git status`, `git stash list`, ahead/behind status, `git worktree list`).
   - **Work tracker**: if a tracker such as `work-tracker` applies to this session, check whether item status (`active`/`waiting`/`done`) and resume notes match current state.
   - **Running resources**: active background tasks, CI watches, subagents, or child tabs/panes created in this session that need handoff or teardown.

## Verdict precedence

Pick the highest applicable verdict (`HOLD` > `RECORD` > `CLOSE`):

- `HOLD`: At least one item requires a user decision or immediate action before closing (unfixed bug decision, uncommitted work, unfulfilled core promise, unresolved choice).
- `RECORD`: No immediate code or execution work is needed, but at least one item must be persisted to an issue tracker, work tracker, or handoff document before closing.
- `CLOSE`: Every applicable dimension was verified with evidence and zero session-only loose ends remain.

## Output format

Write the report in Korean, including headings, verdict, evidence, choices, and recommendations. Preserve code, commands, paths, and identifiers as written.

1. **판정**: One line with `HOLD`, `RECORD`, or `CLOSE` and a brief reason.
2. **닫기 전 결정·조치 항목** (omit when `CLOSE`): One compact bullet per item — `[HOLD|RECORD]`, concrete evidence (session point or command output), actionable choices (e.g., 지금 처리 / 이슈·트래커 기록 후 닫기 / 의도적 폐기), and your recommendation.
3. **확인한 근거**: Compact list of checked dimensions with verified results (or why skipped).
4. **영속화 확인됨** (include only when relevant): Follow-ups already safely recorded externally (IDs, paths, or links) so the user knows they were checked.
