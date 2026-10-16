#!/usr/bin/env node
// Compatibility entry point. docserve owns Markdown recognition and Mermaid.
// New callers: docserve-check mermaid <file.md> [more.md ...] [--render] [--json]
// No dependency installation occurs here; child output and exit codes pass through.
import { spawnSync } from "node:child_process";

const result = spawnSync("docserve-check", ["mermaid", ...process.argv.slice(2)], {
  stdio: "inherit",
});
if (result.error || result.signal) {
  console.error(result.error?.code === "ENOENT"
    ? "docserve-check is unavailable. Install docserve with checker support; see https://github.com/vimkim/docserve/blob/main/docs/guide.md#mermaid-checks."
    : `Could not run docserve-check: ${result.error?.message || result.signal}`);
  process.exit(2);
}
process.exit(result.status ?? 2);
