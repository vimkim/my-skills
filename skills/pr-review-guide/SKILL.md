---
name: pr-review-guide
description: Write Korean Markdown guides for pull-request reviewers, explaining background, major code changes, function and struct responsibilities, and likely reviewer questions with revision-specific evidence. Use when the author wants a PR explanation or shareable answers for reviewers; supports any Git repository and a separate documentation destination such as my-cubrid-docs.
---

# Korean PR Review Guide

Produce a Korean Markdown file that lets a reviewer understand the PR and lets
its author answer recurring questions by linking to the relevant section.
Assume the reviewer reads code but may be unfamiliar with the subsystem.
Explain both **why a symbol's responsibility exists** and **why this PR changes
its implementation**; these require different answers.

## 1. Establish the comparison and destination

Invocation starts in a Git working directory at the intended PR HEAD, including
detached HEAD. Accept an optional PR URL/number, base ref, and output path.

- Inspect repository guidance, remotes, HEAD, and working-tree/index status.
  Keep the analyzed source checkout read-only and preserve local edits. Read
  committed snapshots rather than treating dirty files as the PR implementation.
- Use an explicit base ref when supplied. Otherwise discover the PR and target
  branch from reliable hosting metadata. Verify repository identity and PR HEAD
  against the local HEAD. Resolve multiple matching PRs, a HEAD mismatch, or an
  unknown target with the user before making claims about the comparison; the
  default branch alone is insufficient evidence of the PR target.
- Resolve full HEAD and target/base SHAs, then their merge-base. Inspect committed
  changes from **merge-base to HEAD**, not target-tip to HEAD. If needed objects
  are unavailable, retrieve the necessary refs without changing the checkout or
  request the missing comparison information.
- Use the user's output path first. Otherwise inspect the established
  documentation destination and choose a descriptive filename identifying the
  PR and revision. If none exists, use `docs/pr-review-guides/` in the repository
  with a PR number or branch identifier and short HEAD SHA in the filename.
  Inspect an existing output before revising it; preserve unrelated content.
- For CUBRID work, read `/home/vimkim/my-cubrid/CUBRID.md` when available and
  consult the user's local CUBRID knowledge and issue repositories. On this
  user's host, prefer `/home/vimkim/gh/my-cubrid-docs` when no destination was
  specified. Read its guidance and reuse an existing ticket directory and its
  spelling; follow its file-index rules rather than copying them into this skill.
  A PR without a known ticket still needs a destination consistent with that
  repository's guidance or a concise clarification.
- Follow the destination's worktree and commit workflow for the guide and any
  required index updates. Publication, PR comments, and reviewer messages are
  separate actions requiring authorization.

Before analyzing changes, have an unambiguous comparison and output destination.
Record PR identity (or local-only comparison), full HEAD, target/base ref and SHA,
merge-base SHA, and evidence collection date. State metadata freshness and any
unavailable inputs that limit the guide.

## 2. Gather context and trace behavior

Read available PR descriptions, linked issues, design documents, commit history,
and review discussions. For GitHub, include paginated inline review comments,
review summaries, and conversation comments; one stream alone misses feedback.
Report inaccessible context rather than inventing its contents. Tie author
statements to their sources and account for outdated review comments.

Use the diff as a map, then inspect old and new implementations, surrounding
control/data flow, callers, important types and fields, and relevant tests.
Group changes by behavior or responsibility. Cover changes to contracts,
invariants, state, ownership, lifetime, and representation individually where
they matter; group mechanical edits under their shared purpose.

Build a coverage map from changed code to the guide's major-change sections.
Every substantive change must have an explanation or a stated evidence gap;
files with only mechanical changes can share one explanation.

Distinguish claims in natural Korean prose:

- **코드에서 확인:** behavior traced in the recorded source revisions.
- **작성자가 명시:** intent explicitly stated in linked author material.
- **추론:** reasoning supported by evidence but not stated by the author.
- **미확인:** a remaining question or missing evidence.

Investigate material gaps in available artifacts before asking the author.
Retain unresolved uncertainty visibly when a reliable answer is unavailable.
Alternatives, failure scenarios, author intent, and test outcomes need their own
evidence; plausibility alone does not make them established facts.

## 3. Explain each major change

For every major changed function, struct, or important field, answer the following
in connected prose or a compact table. Adjust depth to significance, while
keeping responsibility and change rationale separate.

| Reviewer question | Required explanation |
| --- | --- |
| 무엇인가? | Responsibility, inputs/outputs or fields, callers, and place in the surrounding system. |
| 그 책임은 왜 필요한가? | The capability or contract that would be absent without it, including functional consequences beyond compilation when applicable. |
| 무엇이 달라지는가? | Precise previous/current behavior, contracts, and invariants. |
| 왜 이 변경이 필요한가? | Original problem or requirement → changed mechanism → resulting behavior. |
| 이전 구현을 유지하거나 이 변경을 빼면 어떻게 되는가? | An evidence-backed triggering scenario and consequence, including dependencies on other PR changes. For refactoring, identify design or maintenance consequences when runtime behavior is intended to remain the same. |
| 어떤 선택과 비용이 있는가? | Applicable costs and compatibility effects; distinguish a required behavior from a design preference. Discuss alternatives only to the extent evidence supports them, and identify newly proposed alternatives as analysis. |
| 무엇으로 확인했는가? | Tests or other evidence, what they establish, and their limits. |

For a new symbol, explain the previous path it replaces or extends. For a removed
symbol, explain where its responsibility moves or why it is no longer needed.
Trace a concrete execution scenario when it makes the cause and effect clearer.
Keep code identifiers exact and excerpts short.

Link code claims to immutable source URLs at the appropriate recorded revision
and line: old behavior at merge-base, new behavior at HEAD. Verify the path,
symbol, and line against that snapshot. If hosted links are unavailable, provide
repository-relative paths, revision, line numbers, and a short excerpt or
`git show <sha>:<path>` lookup; clearly mark local-only evidence. A moving branch
URL or dirty working-tree line is insufficient revision evidence.

## 4. Write the guide and question index

If `$asd-ste100` is available, use its STE-flavored mode for English explanations.
Keep Korean prose natural. Preserve required headings, identifiers, quotations,
and the strength of evidence claims.

Write natural Korean, keeping terminology understandable to a code-literate
reviewer new to the subsystem. Use this content order, adapting section depth to
the PR:

1. Title, comparison/evidence metadata, and table of contents.
2. **배경과 목표:** previous behavior, triggering conditions, practical problem or
   requirement, intended behavior, and a useful before/after example.
3. **코드를 읽기 전에:** subsystem, terminology, relevant control/data flow, and
   recommended reading order.
4. **주요 변경:** the explanations from step 3, organized by responsibility.
5. **연결되는 영향:** applicable error handling, cleanup, ownership, concurrency,
   performance, compatibility, and persistent-data effects. Point to established
   explanations when an impact is already covered.
6. **검증과 한계:** separate tests present in the tree, tests actually executed,
   and revision-specific CI evidence. Record commands, results, and coverage
   limits where available. State what remains unverified; run tests only when
   appropriate to the request and environment.
7. **리뷰어 질문 찾아보기:** questions specific to this PR, each linked directly to
   an authoritative answer elsewhere in the guide.

Add explicit, unique ASCII anchors before shareable sections, for example
`<a id="change-buffer-lifetime"></a>`, and link to them with
`[버퍼 수명은 어디서 보장되는가?](#change-buffer-lifetime)`. Use semantic anchor
names and preserve them when revising the same guide. Put each full explanation
in one authoritative section; the question index and contents link to it.

Derive questions from this PR's mechanisms and actual feedback: why the previous
mechanism is insufficient, why this layer owns the change, how cleanup or
consistent state is guaranteed, which callers and edge cases are affected, and
whether a smaller change could satisfy the requirement. Include only questions
the guide answers, including answers that explicitly identify a limitation.
Use short tables, excerpts, or diagrams where they clarify the explanation.

## 5. Verify and deliver

Read the draft as a skeptical reviewer. Check major-change coverage and the
applicable symbol questions, then resolve unanswered questions through evidence,
author clarification, or explicit uncertainty. Verify references against the
recorded revisions and check that every contents/question link resolves to one
unique anchor. Check required destination index updates and confirm the source
checkout and pre-existing local edits were preserved.

Deliver the Markdown path, revision scope, verification actually performed, and
material limitations. A guide without test execution must say so.
Use `$serve-docs` to provide the viewing link. Retain section anchors for
direct navigation within the guide.
