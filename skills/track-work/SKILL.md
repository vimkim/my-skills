---
name: track-work
description: "Track long-running and parallel work in the work-tracker ledger through its CLI, preserving status, notes, and history across agent sessions. Automatically register substantive work expected to run for 30 minutes or more, cross sessions, use parallel agents, or wait on long external queues; also use when explicitly asked to register, resume, update, complete, cancel, or inspect tracked work. Triggers on phrases like 'track this work', 'loop until CI passes', 'wait for company CI', 'run agents in parallel', 'check today's work', 'update work status', or 'resume work item'."
---

# Track Work

Keep one durable Work Item current while work crosses agent turns, long waits, or external queues.

## 1. Preflight the tracker

1. Require the `work-tracker` executable:

   ```bash
   command -v work-tracker
   work-tracker path
   ```

2. If it is missing, stop and tell the user to install it from the work-tracker repository with `just install`.
3. Use the configured database. Respect `WORK_TRACKER_DB` or the default printed by `work-tracker path`; never invent a second database for convenience.
4. Set a stable actor for this agent session, preferably through `WORK_TRACKER_ACTOR`. If the runtime exposes a stable agent or session identifier, use it. Do not put credentials or secrets in the actor or notes.

## 2. Find or register the Work Item

Register work without asking when at least one condition applies:

- The user explicitly asks to track or register it, or invokes `$track-work`.
- An agent loop is expected to run for 30 minutes or more.
- Progress will wait on a long external queue such as company CI.
- Multiple agents are performing parts of the same objective in parallel.
- The objective is likely to cross a session boundary or context compaction.

Do not auto-register a short investigation or edit expected to finish in the current response. Do not register when the user says not to track the work.

If the user supplies an item ID, inspect it before acting:

```bash
work-tracker show <ID> --json
work-tracker history <ID> --json
```

Otherwise, check the Daily View before creating an item. It lists every Actionable Work Item plus anything finished today, so an objective completed earlier today is recognised as already done:

```bash
work-tracker today --json
```

Create one concise Work Item when no existing item represents the same objective:

```bash
work-tracker add "<objective>" \
  --description "<scope, success condition, and important external references>" \
  --status active \
  --actor "<actor>" \
  --note "started" \
  --json
```

Capture the returned `id` and reuse it throughout the workflow. If creation output is lost, inspect `today --json`; do not create a second item blindly. Tell the user the ID when registration is automatic so the durable record is visible.

## 3. Keep status and context current

Use exactly one current Status:

- `pending`: accepted but not started.
- `active`: an agent or human is currently progressing it.
- `waiting`: progress depends on an expected external event, such as queued CI or a timed agent loop.
- `blocked`: progress cannot continue without a decision, permission, missing input, or failed dependency.
- `done`: the objective and its required verification are complete.
- `cancelled`: work was intentionally abandoned without completion.
- `deleted`: explicit cleanup only; never use it to mean done.

Apply status changes with a concrete reason:

```bash
work-tracker status <ID> waiting --actor "<actor>" --note "CI queued for commit <sha>"
work-tracker status <ID> active --actor "<actor>" --note "CI completed; analyzing two failures"
```

Add a note when new context matters but Status does not change:

```bash
work-tracker note <ID> "<result, blocker, external ID, evidence, or next step>" --actor "<actor>" --json
```

Record a note before yielding for a long wait or handing work to another session. Prefer evidence and a next action over heartbeat noise. Never include tokens, passwords, private keys, or unredacted secrets.

Update durable scope text only when the objective itself changes:

```bash
work-tracker update <ID> --description "<revised scope and success condition>" --actor "<actor>" --note "scope clarified" --json
```

## 4. Resume safely

Reconstruct context from the ledger instead of memory:

```bash
work-tracker show <ID> --json
work-tracker history <ID> --json
```

Before continuing, identify the current Status, latest meaningful note, unresolved dependency, and next action. If the stored objective conflicts with the user's current request, ask which one governs before mutating the item.

Use `work-tracker today --json` when no ID is available. Section 6 says when `list` is the better view.

## 5. Finish explicitly

Mark `done` only after the objective and required verification are complete:

```bash
work-tracker status <ID> done --actor "<actor>" --note "<outcome and verification evidence>" --json
```

Use `cancelled` with the reason when the objective is intentionally abandoned. Use `blocked` when work remains but cannot proceed. Do not delete completed or blocked items; deletion is a separate user-directed cleanup action with a 60-day retention window.

## 6. Inspect or host views

Pick the view by the question being answered:

| Question | Command |
|---|---|
| Is this objective already registered, or was it finished today? | `work-tracker today --json` |
| What is still open or unfinished? | `work-tracker list --json` |
| Which items have one exact status? | `work-tracker list --status <status> --json` |
| What was done before, or which ID belongs to a finished item? | `work-tracker list --all --json`, or `show <ID>` when the ID is known |

`list` shows only Actionable Work Items by default: pending, active, waiting, blocked. `--all` adds done and cancelled. Both `list` and `today` put the most urgent rows first: blocked, active, waiting, pending, then finished work.

Use human-readable output when reporting interactively:

```bash
work-tracker list
work-tracker today
work-tracker show <ID>
work-tracker history <ID>
```

The read-only HTML dashboard is available with `work-tracker serve`. Start a persistent server only when the user asks for hosting; by default it binds to `127.0.0.1:8787` for SSH tunneling.

## Failure handling

- Treat a nonzero exit as a failed tracker operation; report it instead of claiming the Status changed.
- On a busy-database error, retry the same idempotent read or Status operation after a short delay. Do not retry `add` without first checking whether creation succeeded.
- Do not edit the SQLite database directly. Use the CLI so mutations and History Entries remain atomic.
- A Deleted Work Item is readable but immutable during retention. Do not replace it with a duplicate unless the user defines a new objective.
