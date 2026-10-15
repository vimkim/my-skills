---
name: serve-html
description: Print an html-serve command after creating an HTML or Markdown file, or when the user asks to open one.
---

# Open HTML or Markdown

After creating an `.html` or `.md` file, or when asked to open one, provide only
the following viewing command with the file's actual absolute path:

```sh
html-serve /absolute/path/to/file.html
```

Shell-quote the path when needed. Leave execution to the user.
