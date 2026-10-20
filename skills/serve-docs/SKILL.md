---
name: serve-docs
description: Provide direct HTTPS viewing links after creating human-readable documents, such as HTML or Markdown, or when asked to view them.
---

# Serve documents

After creating human-readable documents, include a clickable viewing link for each document in the final response.
Do the same when the user asks to view an existing document.

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
