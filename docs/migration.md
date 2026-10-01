# Five-skill migration

`vimkim/my-skills` is the authoritative editable source for exactly `gh-pr-comments-all`, `resolve-greptile-comments`, `markdown-write`, `question-socratically`, and `track-work`. They use the CLI's `skills/<name>/SKILL.md` container layout. Names, descriptions, content, resource bytes and executable bits are unchanged. The old collection retains its other 18 skills, including `daily-schedule` and `my-cubrid-skills-create`.

## Provenance

All ten files came from [vimkim/my-cubrid-skills at 795015e](https://github.com/vimkim/my-cubrid-skills/tree/795015e). [The manifest](migration-provenance.json) records the full source revision, original paths, SHA-256 values and executable bits. The original repository declares **MIT** in its README; the declaration is retained. No separate LICENSE, COPYING, NOTICE, per-file copyright notice, or third-party attribution file existed among these sources. The migration does not introduce a different license.

The original commit author is Daehyun Kim. The introduction commits are `0da3791` (gh-pr-comments-all), `db709eb` (resolve-greptile-comments), `e491869` (markdown-write), `792a77d` (question-socratically), and `8072a1d` (track-work). Subsequent preserved resource/workflow changes are `4820daf` and `ad163a3`. These commits remain in the original repository's history; the content manifest preserves exact provenance across repositories without rewriting history.

## Coordinated sequence

1. Both collections first adopt the compatible ownership-aware engine and the explicit five-name transfer policy. The old engine remains byte-identical to the authoritative new engine. Configure both peer paths; worktrees need absolute-path configuration overrides.
2. Copy complete source skills into the new collection while original source files remain available. Audit commands and dependencies using the README inventory. The migrated skills resolve resources relative to their loaded directory; none assumes the former source checkout path.
3. In disposable homes and repositories, install the old collection, then install and verify destination files, executable bits and both agent layouts. Successful verification transfers ownership. Check both collection orders. Old-first processing preserves destination-supplied names; new-first processing establishes destination ownership before old sync runs.
4. Only after destination verification remove the five original source directories. Update old inventories, identify `daily-schedule`'s external `track-work` dependency, and replace the creator skill's moved local example. Preserve its `CLAUDE.md` symlink to `AGENTS.md`.
5. Repeat sync and dry run, exercise edits and third-party conflicts, and verify remaining CUBRID resources. Commit both coordinated changes for review. Local main rebase/fast-forward requires the user's approval; pushing and live installation each require separate authorization.

This implementation completed steps 1–4 on topic branches with disposable installations. It has not migrated the live installed store. Existing local copies without trustworthy ownership metadata remain conflicts, even when identical; follow the README conflict-review procedure before any separately authorized live installation. Local verification does not satisfy ticket #6's published default-branch URL gate.

## Reproducible verification

From the new checkout, point to the coordinated old checkout:

```sh
just test
python3 tests/check_migration.py /absolute/path/to/my-cubrid-skills
python3 tests/check_migration.py /absolute/path/to/my-cubrid-skills --real
python3 tests/check_vendored_sync.py /absolute/path/to/my-cubrid-skills
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/markdown-write/tests -v
node --check skills/markdown-write/scripts/check_mermaid_blocks.mjs
```

`check_migration.py` copies real tracked old files and complete migrated destination resources into disposable repositories, reconstructing the original sources whether or not the supplied old checkout has removed them. The default run exercises state, local-source installer metadata and GitHub-source installer metadata in both orders using a controlled installer. `--real` exercises both orders and pre-transfer conflicts with pinned `skills@1.7.0`; `SKILLS_REAL_INSTALLER` can select an already inspected CLI argument list. All installation homes, configuration, ownership files, recovery areas and npm caches are contained. GitHub metadata fixtures test ownership transitions; they do not claim a real public URL installation.

The checks verify all ten migrated files byte-for-byte with executable bits, both agent layouts, actual retained dependencies, install-before-removal ordering, explicit owner transfer, pre/post-transfer edit protection, third-party conflicts, dry-run immutability and repeat-sync convergence. The provenance test in `just test` verifies the exact migrated inventory against the recorded original fingerprints. Resource tests verify the preserved Python checker; the Node syntax check verifies its shipped JavaScript parser. Live copyparty rendering is outside this migration's unchanged skill behavior.
