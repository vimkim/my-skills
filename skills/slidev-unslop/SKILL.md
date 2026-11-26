---
name: slidev-unslop
description: Build or reshape editorial, zero-AI-slop Slidev decks from talks, notes, or existing slides. Use when creating a technical presentation with Slidev, converting a dark or card-heavy deck into a light editorial layout, verifying 1280x720 slide overflow and images with Playwright, or wiring remote-safe Slidev dev/build/PDF scripts.
---

# Slidev Unslop

Turn technical talks, engineering notes, or draft decks into a crisp light-paper editorial Slidev presentation free of AI visual and copy tells, verified at `1280x720` in headless Chromium.

Use companion skills when available: `slidev` for Slidev syntax and built-in features, `frontend-design` for visual direction, `unslop` for English copy, `korean-humanizer` for Korean copy, and `my-just-preference` for `justfile` conventions.

## Step 1 — Plan the deck and layout cadence

1. Ground the deck in its subject matter, audience, talk duration, and language.
2. Pick a restrained token set. Default to light editorial paper (`#ffffff` / `#f8fafc`), deep slate ink (`#0f172a` / `#334155`), hairline borders (`#e2e8f0`), one domain accent, and one semantic danger accent; keep dark terminal blocks (`#0f172a`) as deliberate contrast islands. Use dark mode only when explicitly requested.
3. Map every slide to a single claim and assign a layout from [visual and copy rules](references/visual-and-copy-rules.md) so no two adjacent slides repeat the same structure.

*Done when*: a slide outline lists slide number, claim/title, layout pattern, visual or media asset, and time budget with zero adjacent duplicate layouts.

## Step 2 — Scaffold remote-safe Slidev plumbing

1. Set `slides.md` headmatter:
   `theme: default`, `colorSchema: light`, `aspectRatio: 16/9`, `canvasWidth: 980`, `highlighter: shiki`, `css: unocss`, `duration`, and `timer: countdown`.
2. Copy and adapt the starter files in `assets/` into the project:
   - `assets/vite.config.ts` -> `vite.config.ts` (`server: { host: '0.0.0.0', allowedHosts: true }` prevents Vite 8 `Blocked request` errors when accessing the dev server by LAN hostname).
   - `assets/style-editorial.css` -> `style.css` (editorial primitives scoped under `html:not(.dark)`).
   - `assets/components/MediaSlot.vue` -> `components/MediaSlot.vue` (drop-in image/GIF slot marked `data-optional-media="true"`).
   - `assets/global-bottom.vue` -> `global-bottom.vue` (page footer hidden on `cover` and `section` layouts).
   - `assets/scripts/verify_slides.mjs`, `assets/scripts/export_pdf.mjs`, `assets/scripts/serve_dist.mjs` -> `scripts/`.
   - `assets/justfile.template` -> `justfile` (zero-argument `just --choose` recipes binding `0.0.0.0`; keep browser auto-opening disabled on remote/SSH servers).

*Done when*: `npm run build` succeeds and `just --list` and `just --chooser 'sh -c "cat >&2"' --choose` display the expected zero-arg recipes.

## Step 3 — Author slides and presenter notes

Read [visual and copy rules](references/visual-and-copy-rules.md) and apply these technical guardrails while writing `slides.md`:

- **Keep HTML container blocks contiguous**: omit blank lines inside HTML `<div>...</div>` wrappers in Markdown slides. CommonMark treats 4-space indented sibling `<div>` elements after a blank line as `<pre><code>` code blocks. When placing a Markdown heading (`# Title`) inside a wrapper `<div>`, keep the heading flush-left (zero leading spaces) and pack nested HTML children tightly with no blank lines.
- **Render terminal snippets with `<pre class="cli-body">`**: Vue collapses newlines inside ordinary `<div>` or `<code>` tags. Use `<pre class="cli-body">` with `white-space: pre-wrap` and separate command groups with `<span class="block h-1.5"></span>` instead of blank lines.
- **Escape `<`, `>`, and `&` inside raw HTML and CLI blocks**: write `&lt;`, `&gt;`, and `&amp;` so Vue's template compiler does not parse shell redirections or type parameters as HTML tags.
- **Constrain visual and media heights explicitly**: size stages and media wrappers with fixed heights or flex constraints (`h-[335px]`, `min-h-0`, `object-contain`) so every 16:9 slide fits within `1280x720` with zero scrollbars.
- **Use `<MediaSlot>` for uncaptured screenshots or GIFs**: pending captures display clean dashed instructions without failing broken-image checks.
- **Unslop copy and presenter notes**: remove AI clichés in English and Korean, prefer concrete numbers, commands, and trade-offs, and write timed conversational notes in HTML comments (`<!-- [MM:SS - MM:SS] ... -->`).

*Done when*: all slides match the planned layout cadence, build with zero Vue/Vite template errors, and satisfy the copy and notes checklist.

## Step 4 — Verify programmatically and visually

Read [verification and export](references/verification-and-export.md) for Playwright resolution, flags, and triage.

1. Run `just verify` to build `dist/`, capture `1280x720` screenshots in `.verify/slide-XX.png`, and assert `overflowY <= 4`, `overflowX <= 4`, zero broken required `<img>` elements, and zero unexpected page or console errors.
2. Inspect every rendered screenshot in `.verify/` using `read_file`. Check for clipped SVG labels or viewBoxes, unintended `<pre><code>` blocks from CommonMark indentation, collapsed CLI newlines, footer collisions, low contrast, and repetitive slide rhythm.
3. Fix any layout, overflow, or visual defect and re-run `just verify` until both the automated gate and visual inspection are clean.

*Done when*: `just verify` exits `0` and every screenshot in `.verify/` passes visual inspection.

## Step 5 — Export PDF and confirm deliverables

1. Run `just export-pdf` when a PDF handout is needed. Confirm the output file exists, is non-empty, and matches the total slide count.
2. Report the served URLs (`http://localhost:<port>/` and any LAN/hostname URLs without launching a GUI browser), the verification summary, and any remaining `<MediaSlot>` items awaiting real captures.

*Done when*: requested build/PDF artifacts are verified on disk and the status summary accounts for every slide and pending media slot.
