#!/usr/bin/env node
// Parse-validate every ```mermaid fence in Markdown files using the SAME
// vendored mermaid bundle and initialize options as the copyparty viewer
// (copyparty-render.js), so a block that passes here renders there.
//
// Usage:
//   node check_mermaid_blocks.mjs <file.md> [more.md ...]
//
// Why: the viewer renders all diagrams in one mermaid.run() behind a single
// .catch(), so ONE unparseable diagram blanks EVERY diagram on the page.
// This script fails at authoring time instead.
//
// Bundle resolution: searches upward from each Markdown file's directory for
//   _copyparty_web/vendor/mermaid/mermaid.min.js
// Override with the MERMAID_BUNDLE environment variable (path to the bundle).
// A missing bundle is an error, never a silent pass.
//
// Dependency: jsdom (the mermaid bundle needs DOM globals even to parse).
// Resolution is deterministic and needs no package.json in the target repo:
//   1. require("jsdom") resolvable from this script's own directory;
//   2. the cached install dir ~/.cache/markdown-write-skill/node_modules;
//   3. otherwise it is installed once into that cache dir via
//      `npm install --prefix ~/.cache/markdown-write-skill jsdom`
//      (only the first run needs network; later runs are offline).
//
// Exit codes: 0 every block parses; 1 at least one block fails to parse;
// 2 environment error (bad arguments, missing bundle, jsdom unavailable).

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import vm from "node:vm";
import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";

const CACHE_DIR = path.join(os.homedir(), ".cache", "markdown-write-skill");
const BUNDLE_RELPATH = path.join("_copyparty_web", "vendor", "mermaid", "mermaid.min.js");

function fail(message) {
  console.error(message);
  process.exit(2);
}

function loadJsdom() {
  const requireHere = createRequire(import.meta.url);
  try {
    return requireHere("jsdom");
  } catch {}
  const requireCache = createRequire(path.join(CACHE_DIR, "resolve-anchor.js"));
  try {
    return requireCache("jsdom");
  } catch {}
  console.error(`jsdom not found; installing once into ${CACHE_DIR} ...`);
  try {
    execFileSync(
      "npm",
      ["install", "--prefix", CACHE_DIR, "--no-audit", "--no-fund", "jsdom"],
      { stdio: "inherit" }
    );
  } catch {
    fail(
      "Failed to install jsdom automatically. Install it manually with:\n" +
        `  npm install --prefix ${CACHE_DIR} jsdom\n` +
        "then rerun this check."
    );
  }
  try {
    return requireCache("jsdom");
  } catch (error) {
    fail(`jsdom is still not loadable from ${CACHE_DIR} after install: ${error.message}`);
  }
}

function installDomGlobals(JSDOM) {
  const dom = new JSDOM("<!DOCTYPE html><body></body>", { pretendToBeVisual: true });
  const names = [
    "window",
    "document",
    "DOMParser",
    "XMLSerializer",
    "SVGElement",
    "HTMLElement",
    "Element",
    "Node",
  ];
  for (const name of names) {
    if (dom.window[name] !== undefined) globalThis[name] = dom.window[name];
  }
  if (!globalThis.navigator) globalThis.navigator = dom.window.navigator;
}

function findBundleFor(mdFile) {
  if (process.env.MERMAID_BUNDLE) {
    const bundle = path.resolve(process.env.MERMAID_BUNDLE);
    if (!fs.existsSync(bundle)) fail(`MERMAID_BUNDLE points to a missing file: ${bundle}`);
    return bundle;
  }
  let dir = path.dirname(path.resolve(mdFile));
  for (;;) {
    const candidate = path.join(dir, BUNDLE_RELPATH);
    if (fs.existsSync(candidate)) return candidate;
    const parent = path.dirname(dir);
    if (parent === dir) return null;
    dir = parent;
  }
}

// Fence scanning mirrors check_copyparty_markdown.py: an opener is up to three
// leading spaces plus three or more backticks or tildes, and only a closing
// run of the same character at least as long ends the block, so a ```mermaid
// line inside a longer fence is content, not a new block.
const FENCE_RE = /^ {0,3}(`{3,}|~{3,})(?:[ \t]*([A-Za-z0-9_-]+))?.*$/;

function extractMermaidBlocks(mdFile) {
  const lines = fs.readFileSync(mdFile, "utf8").split(/\r?\n/);
  const blocks = [];
  let fenceChar = "";
  let fenceSize = 0;
  let language = "";
  let openLine = 0;
  let content = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!fenceChar) {
      const match = FENCE_RE.exec(line);
      if (match) {
        fenceChar = match[1][0];
        fenceSize = match[1].length;
        language = (match[2] || "").toLowerCase();
        openLine = i + 1;
        content = [];
      }
      continue;
    }
    const stripped = line.replace(/^ +/, "");
    if (new RegExp(`^[${fenceChar}]{${fenceSize},}[ \t]*$`).test(stripped)) {
      if (language === "mermaid") {
        blocks.push({ file: mdFile, line: openLine, src: content.join("\n") });
      }
      fenceChar = "";
      continue;
    }
    content.push(line);
  }
  if (fenceChar && language === "mermaid") {
    blocks.push({ file: mdFile, line: openLine, src: content.join("\n"), unclosed: true });
  }
  return blocks;
}

const files = process.argv.slice(2);
if (files.length === 0) {
  fail("Usage: node check_mermaid_blocks.mjs <file.md> [more.md ...]");
}
for (const file of files) {
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) {
    fail(`Not a readable file: ${file}`);
  }
}

const allBlocks = files.flatMap(extractMermaidBlocks);
if (allBlocks.length === 0) {
  for (const file of files) console.log(`OK    ${file} (no mermaid blocks)`);
  process.exit(0);
}

const bundles = new Set();
for (const file of files) {
  const bundle = findBundleFor(file);
  if (!bundle) {
    fail(
      `No mermaid bundle found searching upward from ${path.resolve(file)} for ${BUNDLE_RELPATH}.\n` +
        "This check must use the viewer's vendored bundle to be authoritative.\n" +
        "Either run it on files inside the copyparty-served repository, or point\n" +
        "MERMAID_BUNDLE at the viewer's mermaid.min.js. It never silently passes."
    );
  }
  bundles.add(bundle);
}
if (bundles.size > 1) {
  fail(
    "The given files resolve to different mermaid bundles; run the check once per repository:\n  " +
      [...bundles].join("\n  ")
  );
}
const bundlePath = [...bundles][0];

const { JSDOM } = loadJsdom();
installDomGlobals(JSDOM);
vm.runInThisContext(fs.readFileSync(bundlePath, "utf8"), { filename: bundlePath });
const mermaid = globalThis.mermaid;
if (!mermaid) fail(`Bundle did not define a mermaid global: ${bundlePath}`);

// Same options copyparty-render.js passes; theme is omitted because it does
// not affect parsing.
mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });

let failures = 0;
for (const block of allBlocks) {
  const where = `${block.file}:${block.line}`;
  if (block.unclosed) {
    failures++;
    console.log(`FAIL  ${where}\n      Unclosed mermaid fence`);
    continue;
  }
  try {
    await mermaid.parse(block.src);
    console.log(`OK    ${where}`);
  } catch (error) {
    failures++;
    const message = String(error && error.message ? error.message : error)
      .split("\n")
      .slice(0, 6)
      .join("\n      ");
    console.log(`FAIL  ${where}\n      ${message}`);
  }
}

console.log(
  failures
    ? `${failures} of ${allBlocks.length} mermaid block(s) failed to parse`
    : `All ${allBlocks.length} mermaid block(s) parse with the viewer bundle`
);
process.exit(failures ? 1 : 0);
