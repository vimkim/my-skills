# Ticket #6: public consumer verification

## Status

**Acceptance verified against the published default branch.** Following explicit
publication authorization, the real plain GitHub URL and repository shorthand
both passed the default checker on **2026-10-01 at 07:31 UTC**, against `main`
commit **`1f636b69ab94e6e325857d3c0c892969fb3f81e2`**. The installed CLI was
**skills 1.7.0**, run through the documented default `npx` invocation, with
**Node v25.8.0** and no installer override.

[Complete published evidence](ticket-6-published.json) records every command,
exit status, resource fingerprint and source revision. Both cases passed and
`published_default_branch_verified` is **true**.

| Acceptance criterion | Verified result |
| --- | --- |
| Full URL and shorthand discovery | Both `add <source> --list` commands returned 0 and listed the five names without creating installed skills. |
| Real installation without a pre-existing checkout | Each source form installed in its own fresh disposable home and empty consumer directory, returning 0. Source cloning for comparison happened afterward. |
| Both intended agents | Exactly five canonical Codex-compatible skill directories and five correct Claude Code symlinks were verified for each source form. |
| Names, metadata and supporting resources | All five unchanged names and metadata passed; all ten files matched the fresh published checkout byte-for-byte and by executable bits. Four installed Markdown regression tests and Mermaid syntax validation passed in each home. |
| Consumer documentation and prerequisites | README documents both source forms, discovery, intended agents, runtime requirements, local synchronization and conflict handling. External authentication, work-tracker and viewer requirements are explicitly identified. |
| Plain published default branch | Both sources used `1f636b69ab94e6e325857d3c0c892969fb3f81e2`; checks rejected branch changes during or between cases. Publication was explicitly authorized before this run. |
| Evidence and isolation | Report records source commit, skills/Node versions, exact commands and all resource hashes. Home, agent directories, npm/XDG caches, Git configuration and temporary files were isolated and removed afterward. |
| Subsequent local sync | Each dry run and real sync returned **2**, reporting protected conflicts for all five names; the complete consumer home, installed resources and ownership remained unchanged. No silent ownership reassignment occurred. |

The protected-conflict result satisfies the agreed transition criterion. The
check does **not** claim the remote installation was automatically adopted into
local ownership. Consumers should follow the README conflict-review procedure.

The earlier checks against unpublished content correctly failed discovery at
`cca994efc008eec57e822805ccc152d9db957cce`; that historical evidence remains in
[the pre-publication report](ticket-6-published-before-publication.json). Those
failures are superseded by the published verification above.

No live installation, dotfiles deployment or third-party update was performed.

## Local preparation

The final local rehearsal ran from clean commit `6dcbfc8`, using migrated skill content from
`8a2fe861b7cba354684eb3e3095f1ad83961af24` and the default `npx --yes skills@1.7.0` invocation, with no installer override.
The evidence records the checkout HEAD and whether the worktree was dirty at
check time; the resource hashes identify the exact tested bytes independently.

The rehearsal passed:

- Discovery listed all five names without creating installed skills.
- Real CLI installation produced exactly the five skills in Codex's universal
  `~/.agents/skills` store and correct Claude Code symlinks.
- All ten supporting files and skill metadata matched the source bytes and
  executable bits, including agent metadata and both Markdown validators.
- The installed Markdown checker's four regression tests passed; the installed
  Mermaid validator passed Node's syntax check.
- Local collection dry run preserved the complete consumer home. Subsequent
  local sync returned **2** and reported all five as protected conflicts while
  preserving all installations and ownership. This is the expected safe result
  for direct local-path installation, for which skills 1.7.0 writes no global
  ownership record.

The repository public-command suite also passed all **27 tests** (`just test`).

[Local evidence](ticket-6-local.json) records every invoked command, outcome,
resource SHA-256 and executable bits. **This is not GitHub-source transition
proof or a published-default-branch pass.** Real Mermaid rendering requires a
configured viewer bundle and jsdom; only syntax was checked here. Authenticated
GitHub operations and the external work-tracker ledger were not exercised.
Those runtime prerequisites are documented in the README and bundled skills.

The recorded checks use the documented default npx path for **both** local
and published modes. Independent review found that the initial cached-CLI check
had bypassed an npm configuration error: npm rejects using `/dev/null` as both
its user and global configuration file. The checker now creates distinct empty
configuration files inside each disposable directory; the default npx path
passes both the local rehearsal and the published check.

## Reproduce

Requirements: Python 3.12+, Git, just, Node 22.20+ and npm/npx. Start from this
repository for the checker itself; its consumer processes begin in new empty
directories, with no pre-existing source checkout. Source cloning for resource
comparison happens only **after** remote installation.

```sh
# Local preparation; explicitly cannot satisfy the publication gate.
python3 tests/check_published.py --local --output /tmp/my-skills-local.json

# Check the real published default branch through both source forms.
python3 tests/check_published.py --output /tmp/my-skills-published.json
```

The default installer is `npx --yes skills@1.7.0`. To reuse an inspected cached
CLI without downloading another copy, set `SKILLS_REAL_INSTALLER` to a JSON argv:

```sh
export SKILLS_REAL_INSTALLER='["node","/absolute/path/to/skills/bin/cli.mjs"]'
```

The checker verifies the CLI version is exactly 1.7.0. Its subprocess environment
contains only executable lookup and contained home, agent, XDG, npm, temporary
and Git configuration locations. It drops inherited authentication, agent and
installer overrides. Public access requires no credentials. Temporary homes and
all installation/cache data are deleted on exit; the chosen JSON report remains.
No browser is launched, and the live installed-skill store is never used.

The default check independently exercises the **plain** URL and shorthand,
checks discovery without installation, installs for both agents, compares every
resource against a fresh default-branch clone, executes bundled resource checks,
and attempts local collection sync. That transition must either establish
verified `vimkim/my-skills` ownership or report protected conflicts with unchanged
installation and ownership. It rejects a default branch that advances during a
case or between the two cases so a passing report identifies one source commit.

For future published revisions, rerun the default check and require both cases
to pass with `published_default_branch_verified` set to `true`. Review the
recorded source commit and resource evidence. A local pass, temporary branch URL
or successful push alone does not establish acceptance.
