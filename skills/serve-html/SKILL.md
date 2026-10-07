---
name: serve-html
description: Generate a Python HTML serving command and clickable VPN or LAN URLs for reviewing a remote Linux server's HTML file on a local PC. Use when the user asks to serve or open an HTML review file remotely.
---

# Serve HTML

Give the user a foreground Python serving command and clickable links for the
requested HTML file. The user runs the command in their SSH terminal, opens the
link on their local PC over the VPN, then presses Ctrl+C to stop serving. Keep
browsers on the server closed; `DISPLAY` may forward windows over SSH.

## Generate the command and URLs

Resolve the requested file to an absolute path. If the current task produced one
HTML file, use it; ask which file only when the choice is ambiguous.

Resolve `skill_dir` to the directory containing this loaded `SKILL.md`, then invoke
the helper with the absolute HTML path:

```bash
python3 "$skill_dir/scripts/serve_html.py" "/absolute/path/to/review.html" --json
```

The helper returns the shell-quoted `command`, `directory`, `port`, `urls`, and
`local_url`. It reads `ip -j address show` (the JSON form of `ip a`), prefers VPN
interfaces, excludes loopback and container networks, and URL-encodes the filename.
It chooses an available port starting at 8000; `--port PORT` requests a specific
available port, and `--interface NAME` selects one discovered interface.

The command binds to `0.0.0.0` and serves the HTML file's parent directory,
including its adjacent assets. The helper prints a plan and exits. Leave starting
and stopping the server to the user; do not start a background server.

## Return the review link

Return the helper's `command` in a shell code block and the first entry in `urls`
as a Markdown link; show any other discovered network links with their interface
names. Tell the user to run the command in their SSH terminal before clicking,
and to press Ctrl+C there when finished. Use the generated command and URLs
exactly rather than guessing an address. `local_url` is for verification on the
server, not the user's PC. Report helper errors instead of inventing a URL.

The port was available when the plan was generated; rerun the helper if it becomes
occupied before the user starts serving. URLs require the PC's VPN route to the
server. If the user reports an unreachable link, check the other discovered
addresses and give an SSH forwarding command as a fallback; do not change
firewall or VPN configuration.
