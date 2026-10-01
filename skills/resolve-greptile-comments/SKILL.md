---
name: resolve-greptile-comments
description: "Resolve replied Greptile bot review comments on a GitHub PR. Use when the user wants to close, resolve, or dismiss Greptile comments that already have replies, or when they mention cleaning up bot review threads on a PR. Triggers on phrases like 'close greptile comments', 'resolve bot comments', 'clean up greptile threads', or 'dismiss replied review comments'."
argument-hint: "<pr-url-or-number> [--repo owner/repo]"
---

# Resolve Replied Greptile Comments

Resolve all Greptile bot review comment threads on a GitHub PR that already have human replies. This avoids cluttering the PR conversation view with already-addressed bot feedback.

## How it works

1. Parse the PR URL or number from `$ARGUMENTS` to extract `owner`, `repo`, and `pr_number`
2. Fetch all review threads via GitHub GraphQL API
3. Identify threads started by `greptile-apps` that have reply comments (i.e., already addressed)
4. Resolve those threads, skipping any already resolved
5. Report what was done

## Step 1: Parse PR reference

Extract owner, repo, and PR number from `$ARGUMENTS`. Supports formats:
- Full URL: `https://github.com/OWNER/REPO/pull/NUMBER`
- Short: `OWNER/REPO#NUMBER`
- Number only: `NUMBER` (requires `--repo` flag or defaults to current repo via `gh repo view`)

```bash
# Example parsing
PR_URL="$ARGUMENTS"
# Extract from URL pattern
if echo "$PR_URL" | grep -qE 'github\.com/'; then
  OWNER=$(echo "$PR_URL" | sed -E 's|.*github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\1|')
  REPO=$(echo "$PR_URL" | sed -E 's|.*github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\2|')
  PR_NUMBER=$(echo "$PR_URL" | sed -E 's|.*github\.com/([^/]+)/([^/]+)/pull/([0-9]+).*|\3|')
elif echo "$PR_URL" | grep -qE '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[0-9]+$'; then
  OWNER=$(echo "$PR_URL" | cut -d/ -f1)
  REPO=$(echo "$PR_URL" | cut -d/ -f2 | cut -d# -f1)
  PR_NUMBER=$(echo "$PR_URL" | cut -d# -f2)
else
  PR_NUMBER=$(echo "$PR_URL" | grep -oE '[0-9]+')
  # Get owner/repo from current git remote
  OWNER=$(gh repo view --json owner -q '.owner.login')
  REPO=$(gh repo view --json name -q '.name')
fi
```

## Step 2: Fetch review threads and identify Greptile threads with replies

Use the GraphQL API to get all review threads, filtering for ones started by `greptile-apps` that are not yet resolved.

```bash
gh api graphql -f query='
{
  repository(owner: "'"$OWNER"'", name: "'"$REPO"'") {
    pullRequest(number: '"$PR_NUMBER"') {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 2) {
            totalCount
            nodes {
              author { login }
            }
          }
        }
      }
    }
  }
}'
```

Filter the results to find threads where:
- First comment author is `greptile-apps` (the bot)
- `totalCount > 1` (has at least one reply)
- `isResolved` is `false`

## Step 3: Resolve the threads

For each matching thread ID, call the resolve mutation:

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "THREAD_NODE_ID"}) {
    thread { isResolved }
  }
}'
```

## Step 4: Report

Print a summary:
- How many Greptile threads were found total
- How many were already resolved
- How many were resolved now
- How many had no replies (left unresolved)
