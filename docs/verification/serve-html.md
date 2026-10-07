# serve-html verification

Checked on 2026-10-07 in the `feat/serve-html` worktree, based on `main` at
`59b5a93`.

## Behavior

The skill invokes `scripts/serve_html.py` with an absolute HTML path. The helper
prints a foreground `python -m http.server` command serving the parent directory
and discovers IPv4 URLs through `ip -j address show`. VPN addresses appear first;
loopback and ordinary container interfaces are excluded. The user starts the
command in their SSH terminal and stops it with Ctrl+C. Neither the skill nor the
helper starts a server or opens a browser.

The real address discovery produced `tailscale0` (`100.68.111.110`) followed by
`eno1` (`192.168.4.2`). Filenames are URL-encoded, and serving commands use shell
quoting. Explicit `--port` and `--interface` options are supported. An unspecified
port is selected from available ports in 8000–8099; it is not reserved while the
user prepares to start the command. Address discovery currently supports IPv4.

## Checks

- Skill-creator `quick_validate.py`: passed using a temporary PyYAML environment.
- Seven focused helper tests: passed on Python 3.12 and 3.14.6. They cover network
  filtering and preference, interface selection, duplicate addresses, unavailable
  `ip`, occupied ports, invalid paths, and a live HTTP request using the generated
  command. The live check uses a shell to verify quoting of a directory containing
  an apostrophe and literal shell syntax; it fetches HTML with a Unicode filename,
  spaces, `#` and `?`, fetches adjacent CSS, and checks an outside file returns 404.
  Its server is terminated after the check.
- `python3 tests/check_published.py --local`: passed with the real pinned
  `skills@1.7.0` installer in disposable homes. All six skills and their resources
  were installed and verified for Codex and Claude Code. This is local rehearsal,
  not evidence of publication or installation into the user's active skill store.
- `just test`: 34 of 35 tests passed. The sole failure is the existing migration
  fingerprint mismatch for `skills/question-socratically/SKILL.md`, reproduced by
  running `test_migration_inventory.py` on the unchanged `main` checkout. Its
  current SHA-256 is `1a89de149ab571be190d8a8285f89ab3d4bc3b84907d6925ab2cad1db8d87ec4`;
  the original migration manifest records
  `f4a7761b509e94aab549b5aab92f0fcd263c5d521ed190bd52c360272dbe79bf`.
- `git diff --check`: passed.

VPN reachability from the user's PC was not tested; generated addresses identify
the server's interfaces, while the PC's routes and firewall determine access.
