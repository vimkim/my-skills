# Verification and Export

## Prerequisites

1. Build dependencies: `@slidev/cli` and `@slidev/theme-default`.
2. Visual verification: `playwright` or `playwright-chromium` (or `PLAYWRIGHT_PKG` pointing to an installed `playwright` package directory).
3. PDF export: `pdf-lib` in addition to Playwright/Chromium.

Install verification/export dependencies in the deck repository when missing:

```bash
npm install -D playwright-chromium pdf-lib
```

## Automated gate (`scripts/verify_slides.mjs`)

`scripts/verify_slides.mjs` serves `dist/` from an in-process HTTP server on `127.0.0.1` (ephemeral port `0`, with SPA fallback), opens each slide at `1280x720` in headless Chromium, and saves `.verify/slide-XX.png`.

Useful options:

- `--slides <N>` or `TOTAL_SLIDES=<N>`: specify slide count explicitly; when omitted, the script probes `1..200` until Slidev redirects away from `/${i}`.
- `--out-dir <path>`: customize screenshot output directory (default: `.verify`).

Failure criteria (causes exit `1`):

- `overflowY > 4` or `overflowX > 4` on the active `.slidev-layout` container.
- Any `<img>` without `data-optional-media="true"` fails to load (`!img.complete || img.naturalWidth === 0`).
- Unexpected `pageerror` events (excluding harmless headless `Wake Lock` errors).
- Unexpected `console.error` messages (excluding optional `/media/` asset 404s handled by `<MediaSlot>`).

## Visual inspection checklist (`read_file`)

DOM metrics alone do not catch visual defects. Inspect every generated `.verify/slide-XX.png` using `read_file` (or an image viewer) and check:

1. **CommonMark `<pre><code>` leaks**: blank lines inside indented `<div>` wrappers cause Markdown to render raw HTML as a grey code block. Remove blank lines inside HTML containers.
2. **Collapsed terminal newlines**: CLI blocks rendered without `<pre class="cli-body">` collapse onto one line. Verify line breaks and alignment in every terminal snippet.
3. **SVG and image cropping**: check `.svg-stage` and `<MediaSlot>` containers for clipped viewBox edges, tiny unreadable text, or dark-theme SVGs placed on light paper.
4. **Footer clearance**: verify `.slide-footer` does not collide with bottom text, tables, or rules.
5. **Contrast and hierarchy**: confirm headings, body text, inline `<code>`, and badges read cleanly on `#ffffff` / `#f8fafc`.
6. **Layout rhythm**: scan consecutive thumbnails to confirm adjacent slides do not repeat the same layout skeleton.

## PDF export (`scripts/export_pdf.mjs`)

`scripts/export_pdf.mjs` renders each slide individually using `page.emulateMedia({ media: 'screen' })` and `page.pdf({ width: '1280px', height: '720px', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } })`, then merges all pages with `pdf-lib`. Emulating `screen` media avoids print-stylesheet overrides that strip colors or reflow 16:9 grids.

Useful options:

- `--out <file>` or `OUT_PDF=<file>`: output PDF path (default: `slides.pdf`).
- `--slides <N>` or `TOTAL_SLIDES=<N>`: override auto-detected slide count.

## Remote and headless server checklist

- Keep `vite.config.ts` with `server: { host: '0.0.0.0', allowedHosts: true }` so Vite 8 serves requests addressed to a LAN hostname (for example `http://dev2:3030/`).
- Ignore `**/dist/**`, `**/.verify/**`, and `**/*.pdf` in `server.watch.ignored` so verification builds and exports do not trigger dev-server reload loops.
- Start dev mode with `--remote --bind 0.0.0.0` and omit `--open` on headless or SSH hosts.
- Serve built static decks with `scripts/serve_dist.mjs`, which supports SPA route fallback (`/1`, `/presenter`, `/overview`) while returning `404` for missing files with extensions.
