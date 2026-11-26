---
name: my-just-preference
description: Create or refine a project justfile with useful zero-argument recipes for just --choose and remote-reachable serve bindings (0.0.0.0 or dev2 IP). Use when adding a justfile, curating project just commands, or adapting recipes to personal just preferences.
---

# My justfile preferences

Create or refine a project `justfile` around useful, interactive `just --choose` recipes and remote-reachable `serve` defaults.

## 1. Inspect the project

Read any existing `justfile` alongside real project entry points (`package.json`, `pyproject.toml`, `Cargo.toml`, `Makefile`, `CMakeLists.txt`, CI workflows, scripts, README).

- Derive recipes from real commands used to set up, develop, serve, check, test, lint, format, build, install, and clean the repository.
- Preserve existing working recipe names and contracts when refining an existing `justfile`.
- Include only commands backed by this repository; omit speculative placeholders.

Finish with a concrete inventory of useful project commands before writing recipes.

## 2. Design recipes for `just --choose`

`just --choose` displays only public recipes invocable with zero required arguments (no parameters, parameters with default values, or `*args` variadic parameters). Any recipe with a required parameter (`recipe arg:` or `recipe +args:`) disappears from the chooser.

- Expose everyday workflows as concrete zero-argument recipes (for example: `check`, `test`, `lint`, `fmt`, `build`, `install`, `reinstall`, `sync`, `clean`, `serve`, `dev`).
- Split common modes or targets into distinct zero-arg recipes (such as `test-unit`, `test-e2e`, `serve`, `serve-dev2`, `build-release`) instead of gating them behind a required argument.
- When optional CLI overrides help, give parameters sensible defaults (e.g. `host=default_host`) or accept `*args` passthrough so the recipe remains selectable in `just --choose`, or wrap a `[private]` parameterized helper with zero-arg public recipes.
- Mark internal helpers `[private]` (or prefix with `_`) so `just --choose` stays focused on actionable recipes.
- Put a concise `#` doc comment above every public recipe so `just --list` is self-explanatory.
- Mark `default` as `[private]` (running `@just --list`) when creating a new `justfile` so plain `just` prints the menu without adding a redundant `default` entry to `just --choose`. Preserve an existing non-private `default` if the repository already relies on it.

## 3. Configure remote-reachable `serve` commands

Development runs on a remote Linux server (such as `dev2`, IP `192.168.4.2`), so loopback-only bindings (`localhost` or `127.0.0.1`) block remote browser and API access.

- Default `serve`, `dev`, `preview`, and docs-server recipes to bind `0.0.0.0` (preferred, reaching `192.168.4.2`, Tailscale, and loopback simultaneously) or the dev2 host IP (`192.168.4.2`) when single-interface binding is needed.
- Define host and port as top-level variables with defaults (for example: `host := env_var_or_default("HOST", "0.0.0.0")`, `dev2_host := "192.168.4.2"`, `port := env_var_or_default("PORT", "...")`) so zero-arg `just serve` works directly from `just --choose` while allowing env or `just host=... serve` overrides.
- Verify the underlying server's actual host flag before writing the recipe (for example: `--host 0.0.0.0` for Vite/Next/uvicorn/FastAPI/Flask, `--bind 0.0.0.0` for `python3 -m http.server` or Hugo) and keep browser auto-opening disabled on headless hosts.
- When both bindings are useful, provide `serve` (binding `0.0.0.0`) and `serve-dev2` (binding `192.168.4.2`).
- For persistent background services requiring process supervision (`systemd`, `up`/`down`/`restart`/`status`/`logs`), use `just-daemonize` for the service lifecycle while keeping these `just --choose` and serve-binding conventions.

## 4. Structure and verify

Order recipes by workflow (`default`, setup/install, serve/dev, check/test/lint/fmt, build, clean) or group them with `[group('...')]` when a `justfile` grows large.

Verify the resulting `justfile` before finishing:

1. Run `just --list` and confirm clean syntax and clear descriptions for every public recipe.
2. Inspect the exact `just --choose` candidates without running any recipe:
   ```sh
   just --chooser 'sh -c "cat >&2"' --choose
   ```
   Confirm every intended interactive command is listed and internal helpers are hidden.
3. Run `just --evaluate` and at least one safe read-only or fast validation recipe (such as lint/test when lightweight) and verify that `serve` bindings resolve to `0.0.0.0` (or the dev2 host IP) rather than `localhost`/`127.0.0.1`.
