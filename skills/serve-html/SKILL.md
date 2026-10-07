---
name: serve-html
description: Suggest the serve-html CLI command after creating an HTML file on a remote Linux server, or when the user asks to open one from their PC.
---

# Serve HTML

After creating an HTML file, expand `~/.config/my-scripts/bin/serve-html.py`
to its absolute path on the server. Suggest one command with the script path,
HTML file's absolute parent directory, and filename shell-quoted. Substitute
the actual paths and filename for the example:

```sh
python -B '/absolute/home/.config/my-scripts/bin/serve-html.py' --bind 0.0.0.0 --directory '/absolute/path/to/output' --file 'review.html'
```

The absolute paths and `-B` flag keep the command compatible with Bash and
Nushell; `-B` disables Python bytecode cache writes.

Tell the user to run it in their SSH terminal. The CLI starts the foreground
server, chooses and holds a free port, prints Tailscale/VPN and LAN links, and
stops with Ctrl+C. Leave port selection, address discovery, and URL generation
to the CLI; the agent's task ends after suggesting the command. Leave execution
and browser opening to the user.

The CLI is managed by chezmoi in `vimkim/dotfiles` at
`private_dot_config/my-scripts/bin/executable_serve-html.py` and requires Linux,
Python 3, and `ip` (iproute2). If it is missing, report that prerequisite.
