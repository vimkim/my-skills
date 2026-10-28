---
name: serve-docs
description: Provide personal HTTPS viewing links in chat after creating human-readable documents, such as HTML or Markdown, or when asked to view them. These links are available only to the user and are excluded from shared document content.
---

# Serve documents

After creating human-readable documents, include a clickable viewing link for each document in the final response.
Do the same when the user asks to view an existing document.

These are personal viewing links available only to the user. Put them in the chat
handoff, outside document content. JIRA descriptions, PR bodies, reviewer guides,
and other material intended for others use verified URLs accessible to those
readers, such as GitHub, JIRA, or CI links. When no suitable shared URL exists,
include the essential evidence inline and omit the private link. Verify replacement
destinations; a need for a shared link does not authorize document publication.

The dev2 server already runs a persistent, PM2-managed docserve instance serving the filesystem root (`/`) at `https://dev2.baboon-rudd.ts.net:8443`.
Use this existing server directly; viewing a document requires only its link.

Append the document's actual absolute filesystem path, including its leading `/`, to that base URL.
Percent-encode path characters such as spaces, `#`, `?`, and `%`, while preserving `/` separators.
Append any section anchor after the encoded path.

For `/aaa/bbb/ccc.md`, provide:

```markdown
[View document](https://dev2.baboon-rudd.ts.net:8443/aaa/bbb/ccc.md)
```

Use the same mapping for HTML documents.
