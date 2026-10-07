# Implement the spec with one fresh agent per ticket

You are the main coordinator for this build. Read the primary sources below,
then use `implement-spec` to orchestrate the ticket graph under this contract.
The repository's instructions and the recorded user authorization govern
execution wherever the upstream skill assumes a different integration workflow.

## Sources and current state

- Repository and target environment: {{repository}}
- Spec: {{spec_pointer}}
- Ticket set and dependency source: {{ticket_pointers}}
- Ticket/blocker/status snapshot: {{ticket_snapshot}}
- Integration base, branch, commit, and worktrees: {{git_state}}
- Agent guidance and issue-tracker rules: {{guidance_pointers}}
- Glossary, ADRs, prototypes, and research: {{context_pointers}}
- Verification commands and baseline failures: {{verification}}
- Existing orchestration state and work-tracker item: {{state_pointer}}
- Unresolved decisions and prerequisites: {{prerequisites}}
- Existing authorization and remaining review gates: {{authorization}}

## Suggested skills

{{skill_pointers}}

Read the installed skill files using this harness's supported mechanism. Resolve
missing skills or required agent capabilities before beginning dependent work.

## Orchestration contract

1. **Reconstruct the graph.** Reread the current spec and the selected tickets,
   including comments and blocking relationships. Validate the ticket set,
   missing or external blockers, and cycles before dispatch. Resolve any
   decision that materially changes acceptance criteria or ordering. Create or
   reuse one integration branch in a dedicated worktree under the repository's
   rules. Register or resume this parallel build with `track-work`.

2. **Dispatch the ready frontier.** A ticket is ready when all its blockers have
   verified work integrated into the current integration branch; for external
   or previously closed blockers, confirm that the required result is present
   in this checkout. Run ready tickets concurrently within the harness's
   available capacity, serializing tickets that overlap shared code or other
   exclusive resources. Allocate a separate branch and worktree from the
   current integration tip for each ticket.

3. **Use one ticket per clean context.** Spawn a new implementer for every
   ticket with conversation inheritance disabled. In Codex collaboration tools,
   use `fork_turns="none"`. In another harness, use its equivalent independent
   context mechanism. Reusing an agent for a different ticket, or merely telling
   an agent to forget earlier work, does not meet this requirement. Send a
   compact assignment containing only:

   - Its one ticket reference and the spec reference.
   - Its worktree, branch, base commit, and relevant completed blocker commits.
   - Pointers to applicable agent guidance, domain decisions, research, skills,
     and verification commands, plus relevant session-only constraints and
     authorization from this handoff.
   - The requested result: implementation, meaningful verification, a scoped
     commit, and a report mapping acceptance criteria to evidence, with remaining
     blockers or failures stated explicitly.

   The implementer reads those primary sources, uses `tdd` at suitable seams,
   and works only on its ticket. The coordinator retains scheduling, integration,
   and overall status. Keep each repair assignment bounded to the same ticket;
   spawn a fresh replacement if its context is exhausted.

4. **Integrate with evidence.** Inspect the returned diff, commits, and reported
   checks. Serialize integration; follow the repository's rebase and merge
   policy, using linear history wherever required. Check the combined result
   before marking the ticket integrated and releasing its dependents. An agent
   reporting completion alone is insufficient. If integration requires changes,
   keep the dependent frontier blocked until those changes are verified. Record
   ticket state, branch/worktree, commit, evidence, and blocker in durable
   orchestration notes linked from the work-tracker item. Continue independent
   ready tickets when another ticket needs clarification or is blocked. Report
   the exact blocker when no progress is possible; avoid repeated identical
   attempts without new evidence.

5. **Review and hand back the whole build.** Once all tickets are integrated,
   run the relevant project checks and `code-review` against the recorded base
   for Standards and Spec. Delegate fixes in ticket-scoped contexts and repeat
   affected checks. Follow the recorded authorization and tracker completion
   rules for any issue updates, PR publication, default-branch merge, push, or
   deployment. When a human review gate remains, present the completed,
   committed integration branch for that review. Clean up disposable worktrees
   only after verifying their commits are retained and preserving valuable
   files. Finish with ticket outcomes, integration branch and commit, check
   results, outstanding blockers or approvals, and resumable state if incomplete.

Done means every selected ticket's acceptance criteria are satisfied in the
verified integration branch and the required whole-spec review has been
addressed. Keep remaining user review or publication gates visible.
