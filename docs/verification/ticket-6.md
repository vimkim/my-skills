# Ticket #6: public consumer verification

## Status

**Incomplete: publication gate remains blocked.** No push, default-branch merge,
or deployment was authorized by this ticket. Do not close #6 based on the local
checks below. The validator does not push or publish anything.

Read-only checks against the real public repository found `main` at
`cca994efc008eec57e822805ccc152d9db957cce`. With real **skills 1.7.0** and
**Node v25.8.0**, both commands exited **1**, reporting **No skills found**:

```sh
npx --yes skills@1.7.0 add https://github.com/vimkim/my-skills --list
npx --yes skills@1.7.0 add vimkim/my-skills --list
```

Consequently, neither public-source installation nor its subsequent local-sync
transition could be checked yet. Full URL and shorthand use independent disposable
homes. [Recorded command output](ticket-6-published.json) preserves the default
branch revision, actual CLI invocation, version, and failed discovery for each.

## Local preparation

The local rehearsal uses migrated skill content from
`8a2fe861b7cba354684eb3e3095f1ad83961af24` and an inspected real CLI executable.
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

[Local evidence](ticket-6-local.json) records every invoked command, outcome,
resource SHA-256 and executable bits. **This is not GitHub-source transition
proof or a published-default-branch pass.** Real Mermaid rendering requires a
configured viewer bundle and jsdom; only syntax was checked here. Authenticated
GitHub operations and the external work-tracker ledger were not exercised.
Those runtime prerequisites are documented in the README and bundled skills.

## Reproduce

Requirements: Python 3.12+, Git, just, Node 22.20+ and npm/npx. Start from this
repository for the checker itself; its consumer processes begin in new empty
directories, with no pre-existing source checkout. Source cloning for resource
comparison happens only **after** remote installation.

```sh
# Local preparation; explicitly cannot satisfy the publication gate.
python3 tests/check_published.py --local --output /tmp/my-skills-local.json

# Run after separately authorized default-branch publication.
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

After publication, both cases must pass and the JSON field
`published_default_branch_verified` must be `true` before closing #6. Review the
recorded source commit and resource evidence, then update this status and the
README publication notice. A local pass, temporary branch URL or successful
push alone does not establish acceptance.
