# Recording local skill sources automatically

Checked 2026-10-02 against the official Skills documentation, npm metadata,
published `skills@1.7.0`, and upstream commit
`3694740352eeef5cdd689af694c485f1ff62eec3`.

## Finding

`skills add . --global` cannot record its local source in the global lock with
published version **1.7.0**. Upstream has already fixed this: [PR #2301], merged
2026-09-28, makes the same command record local installations automatically.
No extra source flag or manually edited lockfile is required on the fixed code.
The npm `latest` tag still resolved to 1.7.0 when checked; its `gitHead` was
`7407f3893ad4dceab546ac002c3ef806e4000c73`. [npm metadata]

The fixed implementation records `sourceType: "local"`, the resolved absolute
local path as `source`/`sourceUrl`, and a hash of the skill directory. It does
**not** infer a GitHub owner/repository from the checkout's Git remote.
[Fixed implementation]

## Why published 1.7.0 skips it

The published implementation requires a non-null `normalizedSource` before
writing the global lock. `getOwnerRepo()` returns null for local paths, so the
write is skipped. Neither the documented install options/environment variables
nor the option parser provides an override for this condition.
[Published global-lock guard], [source parser], [documented options],
[documented environment], [option parser]

Upstream tracked this exact behavior in [issue #2278]. The implementation fix is
commit [`bcdcee671c59a32586f3ca8813ac964500ac2e94`][fix commit]; its added test
verifies that a global local-path install records the local source.

## Two different lockfiles

| Operation | Published 1.7.0 behavior |
| --- | --- |
| `skills add . --global` | Installs files, omits the local skill's global source entry. |
| `skills add .` | Automatically records the local source in project `skills-lock.json`. |
| `skills experimental_sync` | Scans `node_modules`, installs at project scope, and updates the project lock. It does not repair global local-path provenance. |

The project write is separately gated on `!installGlobally`; removing `--global`
changes installation scope, rather than providing a global ownership workaround.
[Published project-lock write], [experimental sync]

On the inspected upstream revision, the global lock path is
`$XDG_STATE_HOME/skills/.skill-lock.json` when `XDG_STATE_HOME` is set; otherwise
it is `~/.agents/.skill-lock.json`. The upstream regression test uses an isolated
state directory, explaining its `.local/state/skills` path. [Global lock path]

## Isolated reproduction

The coordinating agent ran published 1.7.0 in temporary homes against a temporary
Git repository with a valid dummy skill and an `origin` of
`https://github.com/vimkim/my-skills.git`:

```text
node <skills-1.7.0-cli> add . --agent claude-code codex --yes --global
  exit 0; no global lock and no project lock

node <skills-1.7.0-cli> add . --agent claude-code codex --yes
  exit 0; project skills-lock.json records source: ".", sourceType: "local",
  and computedHash; no global lock
```

Temporary homes were removed and live installed skills were untouched. Upstream
fixed behavior was verified from source and its regression test, not executed
locally during this investigation.

## Practical consequence

For the currently published package, no supported flag makes the exact global
local-path command write the missing source entry. A release containing PR #2301
will provide it automatically; alternatively, running the fixed upstream source
uses that implementation now. The upstream development script is
`node src/cli.ts`, and requires its development dependencies and supported Node
version. This source-run route was not tested here. [Upstream package scripts]

The fix addresses installer provenance. It does not itself replace this
repository's separate collection-sync state or define migration authorization.

[PR #2301]: https://github.com/vercel-labs/skills/pull/2301
[issue #2278]: https://github.com/vercel-labs/skills/issues/2278
[fix commit]: https://github.com/vercel-labs/skills/commit/bcdcee671c59a32586f3ca8813ac964500ac2e94
[npm metadata]: https://registry.npmjs.org/skills/latest
[Fixed implementation]: https://github.com/vercel-labs/skills/blob/3694740352eeef5cdd689af694c485f1ff62eec3/src/add.ts#L2086-L2138
[Published global-lock guard]: https://github.com/vercel-labs/skills/blob/v1.7.0/src/add.ts#L2086-L2128
[Published project-lock write]: https://github.com/vercel-labs/skills/blob/v1.7.0/src/add.ts#L2130-L2168
[source parser]: https://github.com/vercel-labs/skills/blob/v1.7.0/src/source-parser.ts#L11-L14
[documented options]: https://github.com/vercel-labs/skills/blob/v1.7.0/README.md#add-options
[documented environment]: https://github.com/vercel-labs/skills/blob/v1.7.0/README.md#environment-variables
[option parser]: https://github.com/vercel-labs/skills/blob/v1.7.0/src/add.ts#L2429-L2503
[experimental sync]: https://github.com/vercel-labs/skills/blob/v1.7.0/src/sync.ts#L327-L399
[Global lock path]: https://github.com/vercel-labs/skills/blob/3694740352eeef5cdd689af694c485f1ff62eec3/src/skill-lock.ts#L63-L73
[Upstream package scripts]: https://github.com/vercel-labs/skills/blob/3694740352eeef5cdd689af694c485f1ff62eec3/package.json
