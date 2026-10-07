---
name: handoff-implement-spec
description: Prepare a portable handoff after to-spec and to-tickets for a fresh orchestrator that assigns each ticket to its own clean-context agent. Use when handing the build to another session; this skill writes the handoff only.
---

# Handoff Implement Spec

Write an implementation handoff for a fresh main agent. Matt Pocock's
`implement-spec` supplies the task-graph workflow; the handoff adds explicit
context isolation and carries the project's integration and authorization rules.
Finish by saving the handoff and giving the user its path and a starter prompt.

## Gather the handoff inputs

Read the repository's agent guidance and configured issue-tracker instructions.
Find the spec and the tickets produced by `to-tickets` in the user's arguments
or current conversation. Read their bodies, comments, and blocking relationships.
Ask only for references or decisions that remain ambiguous after that lookup.
Tickets from `to-tickets` are already agent-ready.

Record pointers to:

- The repository root, integration base, current branch and commit, relevant
  worktrees, and any work already completed or in progress.
- The spec, the exact ticket set, and the authoritative source for their blocking
  relationships. Include external blockers when present.
- Applicable agent guidance, tracker rules, glossary, ADRs, prototypes, and
  research that affect implementation.
- Existing verification commands, known baseline failures, and unresolved
  decisions that affect whether tickets can start.
- Existing work-tracker or orchestration state, if this resumes a build.

Distinguish observed facts from assumptions. Carry forward permission already
given in this conversation and any remaining review gates; a handoff creates
no additional permission to merge into the default branch, push, publish a PR,
close issues, or deploy. Preserve the project's own workflow.

## Write the handoff

Use [the orchestrator template](assets/orchestrator-handoff.md). Replace every
placeholder with a concrete value or an explicit unresolved prerequisite.
Reference existing artifacts rather than copying their contents. Record the
ticket IDs and blockers as a snapshot, with links to reread their current state.
Include concise session-only decisions and constraints that are not captured
in those artifacts.

Resolve the available `implement-spec`, `tdd`, `code-review`, and `track-work`
skill locations and record them as suggested skills. Identify missing skills or
agent capabilities as prerequisites for the next session. The receiving agent
must be able to spawn independent contexts and isolate concurrent worktrees.
For another machine or harness, record how to find equivalent skills and
repository artifacts instead of assuming local paths will work there.

Save a uniquely named Markdown file under the OS temporary directory
(`$TMPDIR`, otherwise `/tmp`; `%TEMP%` on Windows), unless the user supplied a
destination. Redact secrets. Check that the saved file has no unfilled template
placeholders and that its local pointers exist or are marked as unavailable.

Return the absolute path and this starter prompt, filled with that path:

> Read the handoff at HANDOFF_PATH and carry out its orchestration contract.
> You are the main coordinator. Assign each ticket to a new clean-context agent.

The current session's work ends with the handoff; implementation belongs to the
receiving session.
