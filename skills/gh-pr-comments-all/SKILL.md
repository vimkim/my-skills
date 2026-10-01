---
name: gh-pr-comments-all
description: "Fetch every comment on a GitHub PR by querying all three GitHub REST endpoints (inline review comments, top-level review summaries, and PR-page discussion) and merging them into one chronological view. Use when the user asks to list all PR review comments, audit reviewer feedback, or check whether anything was missed — a single endpoint fetch silently drops top-level review bodies and conversation-tab comments. Triggers on phrases like 'list all pr comments', 'all comments on pr', 'fetch every review comment', 'audit pr feedback', 'why are some review comments missing', or 'show every reviewer comment'."
argument-hint: "<pr-url-or-number>"
---

# Fetch All PR Comments

A GitHub PR's "comments" live in three separate REST endpoints. Querying only `/pulls/{n}/comments` (the obvious one) silently drops top-level review bodies and PR-page discussion comments. This skill fetches all three, merges them, and prints a chronological view grouped by source.

This skill intentionally does NOT call the GraphQL `reviewThreads` endpoint — `isResolved` and `isOutdated` thread state is out of scope. If the user specifically needs to close already-replied Greptile bot threads, use `resolve-greptile-comments`. For raw thread-state on arbitrary reviewers, query the GraphQL endpoint directly, e.g.:

```bash
gh api graphql -f query='{repository(owner:"OWNER",name:"REPO"){pullRequest(number:N){reviewThreads(first:100){nodes{isResolved isOutdated comments(first:1){nodes{author{login} path}}}}}}}'
```

## The three endpoints

| Endpoint | Returns | UI origin |
|---|---|---|
| `GET /repos/{o}/{r}/pulls/{n}/comments` | Inline file/line review comments (root comments **and** replies in one flat list, distinguished by `in_reply_to_id`) | "Review changes → Comment on line" |
| `GET /repos/{o}/{r}/pulls/{n}/reviews` | Top-level review summaries (the body in the "Finish your review" dialog, plus `state` like APPROVED / CHANGES_REQUESTED / COMMENTED / DISMISSED / PENDING) | "Review changes → Summary box" |
| `GET /repos/{o}/{r}/issues/{n}/comments` | PR-page discussion comments (everything on the Conversation tab not tied to a review) | The bottom comment box on the PR page |

All three need `--paginate` because GitHub's default page size is 30.

## Step 1: Parse the PR reference

Extract `OWNER`, `REPO`, and `PR_NUMBER` from `$ARGUMENTS`. Supports:

- Full URL: `https://github.com/OWNER/REPO/pull/NUMBER`
- Short: `OWNER/REPO#NUMBER`
- Number only: `NUMBER` (defaults to current repo via `gh repo view`)

```bash
PR_REF="$ARGUMENTS"
if echo "$PR_REF" | grep -qE '^https?://(www\.)?github\.com/'; then
  OWNER=$(echo "$PR_REF" | sed -E 's|.*github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\1|')
  REPO=$(echo "$PR_REF" | sed -E 's|.*github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\2|')
  PR_NUMBER=$(echo "$PR_REF" | sed -E 's|.*github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\3|')
elif echo "$PR_REF" | grep -qE '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[0-9]+$'; then
  OWNER=$(echo "$PR_REF" | cut -d/ -f1)
  REPO=$(echo "$PR_REF" | cut -d/ -f2 | cut -d# -f1)
  PR_NUMBER=$(echo "$PR_REF" | cut -d# -f2)
else
  PR_NUMBER=$(echo "$PR_REF" | grep -oE '[0-9]+' | head -1)
  OWNER=$(gh repo view --json owner -q '.owner.login')
  REPO=$(gh repo view --json name -q '.name')
fi
```

If `PR_NUMBER` is empty after parsing, surface the error and stop — do not guess.

## Step 2: Fan out three paginated fetches in parallel

Run all three `gh api` calls in a single message with parallel Bash tool invocations — they are independent. Hardening:

- Use `(.user.login // "ghost")` because deleted accounts return `"user": null`.
- Use `(.line // .original_line)` so active threads show the current diff line and outdated threads fall back to the original.
- Write each stream to its own temp file so Step 5 can merge them.

```bash
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Inline review comments (file/line tied; includes replies flat)
gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments" --paginate \
  --jq '.[] | {source:"inline", id, user:(.user.login // "ghost"), created_at, path, line:(.line // .original_line), in_reply_to_id, state:null, body}' \
  > "$TMPDIR/inline.ndjson"

# Top-level review summaries
gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews" --paginate \
  --jq '.[] | {source:"review", id, user:(.user.login // "ghost"), created_at:.submitted_at, path:null, line:null, in_reply_to_id:null, state, body}' \
  > "$TMPDIR/reviews.ndjson"

# PR-page discussion comments
gh api "repos/$OWNER/$REPO/issues/$PR_NUMBER/comments" --paginate \
  --jq '.[] | {source:"issue", id, user:(.user.login // "ghost"), created_at, path:null, line:null, in_reply_to_id:null, state:null, body}' \
  > "$TMPDIR/issue.ndjson"
```

`--paginate` with a `--jq` filter that projects per-element emits newline-delimited JSON (NDJSON). Keep it as NDJSON until Step 5.

## Step 3: Filter the reviews stream

Apply this filter — it enumerates every review state explicitly:

| `state` | Body empty? | Decision |
|---|---|---|
| `APPROVED` | either | **keep** |
| `CHANGES_REQUESTED` | either | **keep** |
| `COMMENTED` | non-empty | **keep** (real top-level summary) |
| `COMMENTED` | empty | **drop** (wrapper around inline comments — already in `inline.ndjson`) |
| `DISMISSED` | either | **drop** (administratively removed; noise) |
| `PENDING` | either | **drop** (reviewer's private draft; should not surface even though API may return it) |

Concrete jq:

```bash
jq -c 'select(
  (.state == "APPROVED") or
  (.state == "CHANGES_REQUESTED") or
  (.state == "COMMENTED" and (.body // "") != "")
)' "$TMPDIR/reviews.ndjson" > "$TMPDIR/reviews.filtered.ndjson"
```

## Step 4: Tag known bot meta-comments separately

Bots post index-style summary comments on the Conversation tab. Tag them via body markers so they appear under a distinct "Bot meta" section, not the main feedback list. The marker list is extensible — add new markers as new bots are encountered:

```bash
jq -c '. + {category: (
  if (.body // "") | test("<!-- greptile_other_comments_section -->|<!-- This is an auto-generated comment.*coderabbit") then
    "bot-meta"
  else
    "comment"
  end
)}' "$TMPDIR/issue.ndjson" > "$TMPDIR/issue.tagged.ndjson"
```

Inline and review streams keep `category: "comment"` implicitly — no bot has been observed posting index summaries to those endpoints. The marker regex is empirical, not authoritative — extend it as new bots are encountered (verify each new marker against a real PR before adding it).

## Step 5: Merge, sort, and group threads

Each `*.ndjson` file is newline-delimited bare objects (the `--jq '.[] | {...}'` filter at the `gh` level already unrolled per-page arrays). Concatenate them and slurp into a single sorted array:

```bash
cat "$TMPDIR/inline.ndjson" "$TMPDIR/reviews.filtered.ndjson" "$TMPDIR/issue.tagged.ndjson" \
  | jq -s 'sort_by(.created_at)' > "$TMPDIR/merged.json"
```

`jq -s` (slurp) reads NDJSON and emits a JSON array. Empty input files contribute zero objects — no null-guard needed.

Then group inline replies under their root. `in_reply_to_id` on GitHub always points to the **root** comment (never to an intermediate reply), so a flat root→replies structure suffices — no recursion needed. **The root id must be bound to a variable before the inner `select` or jq will self-compare `.id == .id`:**

```bash
jq '
  (map(select(.source == "inline" and .in_reply_to_id == null))) as $roots
  | (map(select(.source == "inline" and .in_reply_to_id != null))) as $replies
  | (map(select(.source != "inline"))) as $flat
  | ($roots | map(. as $r | . + {replies: ($replies | map(select(.in_reply_to_id == $r.id)))}))
    + $flat
  | sort_by(.created_at)
' "$TMPDIR/merged.json" > "$TMPDIR/grouped.json"
```

## Step 6: Print a chronological view

Iterate `grouped.json` and emit one row per top-level item plus indented rows per inline reply. The exact layout is illustrative — adapt it to context (table, markdown, plain text). Normalize whitespace in bodies before slicing so embedded newlines don't break the one-row-per-item layout. The example uses ASCII `->` for the reply marker (UTF-8 safe but doesn't require it):

```bash
jq -r '
  def oneline: (. // "") | gsub("\\s+"; " ");
  .[] | (
    "[\(.source)] \(.user)  \(.path // "(no path)"):\(.line // "-")  \(.body | oneline | .[0:120])"
    + (if (.replies // []) | length > 0 then
         "\n" + ((.replies | map("  -> \(.user)  \(.body | oneline | .[0:120])")) | join("\n"))
       else "" end)
  )
' "$TMPDIR/grouped.json"
```

Adjust truncation length, column widths, or output format as the downstream task demands. If a UTF-8 terminal is guaranteed, `->` can be swapped for `↳`.

## Step 7: Print a summary footer

Capture the PR author up front for use in the unreplied heuristic:

```bash
PR_AUTHOR=$(gh pr view "$PR_NUMBER" --repo "$OWNER/$REPO" --json author -q '.author.login')
```

Then emit:

- Total counts by `source` (inline / review / issue / bot-meta).
- Total counts by `user`.
- **Unreplied inline roots** — comments not authored by the PR author themselves, with no entries in `replies`. Excluding the PR author's own roots prevents flagging the author's self-notes as "unanswered":

  ```bash
  jq --arg author "$PR_AUTHOR" '
    [.[] | select(.source == "inline" and .user != $author and ((.replies // []) | length == 0))]
    | map({user, path, line, snippet: ((.body // "") | gsub("\\s+"; " ") | .[0:120])})
  ' "$TMPDIR/grouped.json"
  ```

Top-level reviews and PR-page issue comments are intentionally omitted from the unreplied detection — GitHub provides no formal "reply-to" link for those endpoints, so any heuristic would be guesswork. If precision matters there, read them manually or query GraphQL `reviewThreads.isResolved` (out of scope for this skill).

Caveat to print in the output: this skill does not read GraphQL `isResolved`, so a thread that was textually unanswered but resolved-in-UI will appear as "unreplied". If precision matters, query `reviewThreads.isResolved` directly (see the snippet at the top of this skill).

## Failure modes to handle

- **Pagination dropped** — always pass `--paginate` to every `gh api` call. A 31-comment PR will silently lose comment #31 without it.
- **Ambiguous PR number** — if `$ARGUMENTS` is just `1234` and no git remote is configured, `gh repo view` fails. Surface the error rather than guessing.
- **Private PR / 404** — `gh` returns 404 if the user lacks access (or if the PR genuinely doesn't exist). Print which endpoint failed and stop; do not partial-merge a missing stream.
- **Empty body reviews** — handled in Step 3's enumerated table. Empty body + COMMENTED is a wrapper; empty body + APPROVED is meaningful.
- **`original_line` vs `line`** — handled in Step 2's jq: prefer `.line` (current diff position), fall back to `.original_line` (original commented position for outdated threads).
- **Deleted users** — handled in Step 2's jq: `null` user is projected as `"ghost"`.
- **Rate limits** — three `--paginate` calls run in parallel are fine (well under the 5000 req/hr authenticated limit for a single PR). For repeated batch runs across many PRs, watch for `403 rate limit exceeded` and respect the `X-RateLimit-Reset` header. The secondary rate limit on rapid parallel calls is not a concern at fan-out=3.
- **Empty streams** — `jq -s` on an empty file emits `[]`. Concatenating an empty stream contributes zero objects to `merged.json`, so a PR with zero issue comments still produces a valid result.
- **GraphQL state out of scope** — this skill does not return `isResolved`/`isOutdated`. If the user needs to close already-replied Greptile threads, defer to `resolve-greptile-comments`. For raw thread state on arbitrary reviewers, run the GraphQL one-liner shown at the top of this skill.
