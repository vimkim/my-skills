---
name: vimkim-mode
description: "Use for vimkim, /vimkim-mode, or requests to work in their style. Apply the user's shared conventions, preserve resumable context, and report CUBRID TC changes at merge handoff."
disable-model-invocation: true
---

# Vimkim mode

## Shared conventions

Read [global agent guidance](/home/vimkim/.codex/AGENTS.md) if its instructions are not already in context. It owns autonomy, work tracking, Herdr, headless operation, Git approvals, and next-step requests. Keep those rules in that file.

For CUBRID work, first read [personal CUBRID workflow](/home/vimkim/my-cubrid/CUBRID.md). Follow its links for the current task.

## Resumable context

The user conserves context through handoffs and fresh sessions. Before handing off long work, leave a compact record of the goal, verified state, unresolved decisions, and next action. Link to existing work-tracker entries and artifacts so a fresh session can resume without rereading the conversation.

## CUBRID merge handoff

Keep TC PRs open during development, review, and CI. Finalize them immediately before the engine PR merge. Read [testcase lifecycle](/home/vimkim/.agents/skills/cubrid-common/references/testcase-lifecycle.md) for preserving changed cases and refreshing the TC gate.

When engine review and all other applicable checks are complete, and the remaining TC work belongs to that final handoff, use this wording:

> PR 머지하셔도 됩니다. (TC도 닫으세요)

If a TC gate still awaits finalization, state that alongside the readiness message. Base the message on evidence for the current engine and TC revisions.

**Emphasize any TC changes in CUBRID PR reports.** Name the affected TC PRs and summarize their changes before the readiness message. Carry changed testcases into their intended targets before closing their PRs, following the lifecycle reference. A merge-readiness report does not authorize a merge or TC closure.
