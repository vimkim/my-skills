# serve-html verification

Checked on 2026-10-07 in two topic worktrees:

- `fix/serve-html-cli` in `/home/vimkim/gh/my-skills-serve-html-cli`, based on
  `my-skills` main at `68daaa5`.
- `feat/serve-html-cli` in `/home/vimkim/.local/share/chezmoi-serve-html-cli`,
  based on `dotfiles` main at `f102638`.

## Behavior

The skill now only suggests a shell-quoted command for
`~/.config/my-scripts/bin/serve-html.py`, specifying the HTML file's parent
directory and filename. It applies after creating HTML as well as when asked to
open an existing HTML file from a PC. The agent leaves server execution, port
selection, address discovery, and link generation to the user-run CLI.

The maintained CLI and its tests moved to `vimkim/dotfiles`. Its chezmoi source
is `private_dot_config/my-scripts/bin/executable_serve-html.py`. The CLI binds
`0.0.0.0` by default, asks the kernel for an available port with port 0, retains
that socket throughout serving, and prints links after successfully binding.
It serves adjacent assets, URL-encodes the HTML path, prefers Tailscale/VPN
interfaces, and stops with Ctrl+C. Fixed `--port`, `--bind`, and `--interface`
options remain available. Discovery supports IPv4.

## Checks

- Skill-creator `quick_validate.py`: passed through
  `PYTHONDONTWRITEBYTECODE=1 uv run --no-project --with pyyaml`.
- Nine focused CLI tests in dotfiles: passed on Python 3.14.6. They cover network
  filtering, interface selection, bind-specific links, duplicate addresses,
  unavailable `ip`, occupied explicit ports, invalid paths and arguments, live
  HTTP serving, concurrent automatic ports, and Ctrl+C shutdown. The live check
  fetches HTML with a Unicode filename, spaces, an apostrophe, `#`, and `?`,
  fetches adjacent CSS, and checks that `../outside.txt` returns 404. Its directory
  includes literal shell syntax. Integration tests use a deterministic `ip`
  fixture and terminate their servers afterward.
- Real interface smoke: the CLI discovered `tailscale0` (`100.68.111.110`) and
  `eno1` (`192.168.4.2`), selected port `33475`, served HTTP through both addresses
  from this server, and exited with status 0 after SIGINT. The temporary directory
  and server were removed after verification.
- Targeted chezmoi diff: showed only the new executable target
  `/home/vimkim/.config/my-scripts/bin/serve-html.py`; rendered bytes matched the
  maintained script.
- `just test` in my-skills: 27 of 28 tests passed. The sole failure is the existing
  migration fingerprint mismatch for `skills/question-socratically/SKILL.md`.
  The same failure was reproduced on unchanged `main` at `68daaa5`.
  Its current SHA-256 is
  `1a89de149ab571be190d8a8285f89ab3d4bc3b84907d6925ab2cad1db8d87ec4`; the original
  manifest records
  `f4a7761b509e94aab549b5aab92f0fcd263c5d521ed190bd52c360272dbe79bf`.
- `git diff --check`: passed in both worktrees.

The CLI has been prepared for targeted installation, and the revised skill has
been prepared for collection sync. Active installed copies remain unchanged
pending the local merge review. PC reachability was not tested; the real HTTP
checks above ran on the server.
