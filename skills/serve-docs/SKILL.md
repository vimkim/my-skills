---
name: serve-docs
description: Provide a docserve command after creating human-readable documents, such as HTML or Markdown, or when asked to view them.
---

# Serve documents

After creating human-readable documents, include a `docserve` command for each document in the final response.
Do the same when the user asks to view an existing document.

```sh
docserve /absolute/path/to/document.md
```

Use the document's actual absolute path. Shell-quote the path when needed.
Leave execution to the user.
