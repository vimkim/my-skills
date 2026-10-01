#!/usr/bin/env python3
"""Lint Markdown for the configured copyparty standalone viewer."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit


FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(?:[ \t]*([A-Za-z0-9_-]+))?.*$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^\s)>]+)>?")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(\s*<?([^\s)>]+)>?")
SINGLE_TEX_DELIMITER_RE = re.compile(r"(?<!\\)\\([\[\]\(\)])")
INLINE_CODE_RE = re.compile(r"(`+)(.*?)(?<!`)\1(?!`)")
INLINE_SVG_RE = re.compile(r"<svg\b.*?</svg\s*>", re.IGNORECASE | re.DOTALL)
SVG_OPEN_RE = re.compile(r"<svg\b", re.IGNORECASE)
SVG_CLOSE_RE = re.compile(r"</svg\s*>", re.IGNORECASE)

UNSAFE_SVG_PATTERNS = (
    (r"<script\b", "SVG must not contain scripts"),
    (r"\son[a-z]+\s*=", "SVG must not contain event-handler attributes"),
    (r"javascript\s*:", "SVG must not contain javascript: URLs"),
    (r"<foreignobject\b", "SVG must not use foreignObject"),
)


@dataclass(frozen=True)
class Diagnostic:
    path: Path
    line: int
    message: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def mask_inline_code(line: str) -> str:
    return INLINE_CODE_RE.sub(lambda match: " " * len(match.group(0)), line)


def visible_markdown(text: str, path: Path) -> tuple[str, list[Diagnostic]]:
    """Mask fenced code while retaining Mermaid fence validation."""
    output: list[str] = []
    diagnostics: list[Diagnostic] = []
    fence_char = ""
    fence_size = 0
    fence_language = ""
    fence_line = 0
    fence_has_content = False

    for number, line in enumerate(text.splitlines(keepends=True), start=1):
        match = FENCE_RE.match(line.rstrip("\r\n"))
        if not fence_char:
            if match:
                marker = match.group(1)
                fence_char = marker[0]
                fence_size = len(marker)
                raw_language = match.group(2) or ""
                fence_language = raw_language.lower()
                fence_line = number
                fence_has_content = False
                if fence_language == "mermaid" and raw_language != "mermaid":
                    diagnostics.append(
                        Diagnostic(path, number, "Mermaid fence language must be lowercase 'mermaid'")
                    )
                output.append("\n" if line.endswith("\n") else "")
                continue
            output.append(mask_inline_code(line))
            continue

        stripped = line.lstrip(" ")
        closing = re.match(rf"{re.escape(fence_char)}{{{fence_size},}}[ \t]*\r?\n?$", stripped)
        if closing:
            if fence_language == "mermaid" and not fence_has_content:
                diagnostics.append(Diagnostic(path, fence_line, "Mermaid fence is empty"))
            fence_char = ""
            fence_size = 0
            fence_language = ""
            output.append("\n" if line.endswith("\n") else "")
            continue

        if line.strip():
            fence_has_content = True
        output.append("\n" if line.endswith("\n") else "")

    if fence_char:
        diagnostics.append(Diagnostic(path, fence_line, "Unclosed fenced code block"))

    return "".join(output), diagnostics


def validate_links(text: str, path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for match in LINK_RE.finditer(text):
        target = match.group(1)
        lowered = target.lower()
        windows_absolute = bool(re.match(r"^[a-z]:[\\/]", target, re.IGNORECASE))
        if (
            lowered.startswith("file://")
            or target.startswith("/home/")
            or target.startswith("/Users/")
            or windows_absolute
        ):
            diagnostics.append(
                Diagnostic(
                    path,
                    line_number(text, match.start(1)),
                    f"Machine-local link is not portable: {target}",
                )
            )
    return diagnostics


def validate_svg_markup(svg: str, path: Path, number: int, label: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    opening_end = svg.find(">")
    opening = svg[: opening_end + 1] if opening_end >= 0 else svg

    if not re.search(r"\bviewbox\s*=", opening, re.IGNORECASE):
        diagnostics.append(Diagnostic(path, number, f"{label} is missing a viewBox"))
    if not re.search(
        r"\bxmlns\s*=\s*['\"]http://www\.w3\.org/2000/svg['\"]",
        opening,
        re.IGNORECASE,
    ):
        diagnostics.append(Diagnostic(path, number, f"{label} is missing the SVG xmlns"))

    for pattern, message in UNSAFE_SVG_PATTERNS:
        if re.search(pattern, svg, re.IGNORECASE):
            diagnostics.append(Diagnostic(path, number, f"{label}: {message}"))
    return diagnostics


def validate_external_svgs(text: str, path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for match in IMAGE_RE.finditer(text):
        alt_text = match.group(1).strip()
        target = match.group(2)
        parsed = urlsplit(target)
        if Path(parsed.path).suffix.lower() != ".svg":
            continue

        number = line_number(text, match.start())
        if not alt_text:
            diagnostics.append(Diagnostic(path, number, "External SVG image is missing alt text"))

        if parsed.scheme or parsed.netloc:
            continue
        if parsed.path.startswith("/"):
            diagnostics.append(
                Diagnostic(path, number, f"External SVG must use a repository-relative path: {target}")
            )
            continue

        svg_path = path.parent / unquote(parsed.path)
        if not svg_path.is_file():
            diagnostics.append(
                Diagnostic(path, number, f"Referenced external SVG does not exist: {target}")
            )
            continue

        try:
            svg = svg_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            diagnostics.append(
                Diagnostic(path, number, f"Referenced SVG is not UTF-8 text: {target}")
            )
            continue

        if not SVG_OPEN_RE.search(svg) or not SVG_CLOSE_RE.search(svg):
            diagnostics.append(
                Diagnostic(path, number, f"Referenced file is not a complete SVG document: {target}")
            )
            continue
        diagnostics.extend(validate_svg_markup(svg, svg_path, 1, "External SVG"))
    return diagnostics


def validate_tex(text: str, path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    visible_lines: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        visible = mask_inline_code(line)
        visible_lines.append(visible)
        for match in SINGLE_TEX_DELIMITER_RE.finditer(visible):
            delimiter = match.group(0)
            diagnostics.append(
                Diagnostic(
                    path,
                    number,
                    f"Single-backslash TeX delimiter {delimiter!r}; double the delimiter backslash for copyparty",
                )
            )
    visible_text = "\n".join(visible_lines)
    unescaped_dollars = len(re.findall(r"(?<!\\)\$", visible_text))
    if unescaped_dollars % 2:
        diagnostics.append(Diagnostic(path, 1, "Unbalanced dollar math delimiters"))

    doubled_delimiters = (
        (r"(?<!\\)\\\\\(", r"(?<!\\)\\\\\)", "\\\\(...\\\\)"),
        (r"(?<!\\)\\\\\[", r"(?<!\\)\\\\\]", "\\\\[...\\\\]"),
    )
    for opening, closing, label in doubled_delimiters:
        if len(re.findall(opening, visible_text)) != len(re.findall(closing, visible_text)):
            diagnostics.append(Diagnostic(path, 1, f"Unbalanced {label} math delimiters"))
    return diagnostics


def validate_inline_svg(text: str, path: Path) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if len(SVG_OPEN_RE.findall(text)) != len(SVG_CLOSE_RE.findall(text)):
        diagnostics.append(Diagnostic(path, 1, "Unbalanced inline <svg> and </svg> tags"))

    for match in INLINE_SVG_RE.finditer(text):
        block = match.group(0)
        number = line_number(text, match.start())
        diagnostics.extend(validate_svg_markup(block, path, number, "Inline SVG"))
    return diagnostics


def validate_file(path: Path) -> list[Diagnostic]:
    if not path.exists():
        return [Diagnostic(path, 1, "File does not exist")]
    if not path.is_file():
        return [Diagnostic(path, 1, "Path is not a regular file")]
    if path.suffix.lower() not in {".md", ".markdown"}:
        return [Diagnostic(path, 1, "Expected a .md or .markdown file")]

    text = path.read_text(encoding="utf-8")
    visible, diagnostics = visible_markdown(text, path)
    diagnostics.extend(validate_links(visible, path))
    diagnostics.extend(validate_external_svgs(visible, path))
    diagnostics.extend(validate_tex(visible, path))
    diagnostics.extend(validate_inline_svg(visible, path))
    return diagnostics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Markdown against the configured copyparty rendering contract."
    )
    parser.add_argument("files", nargs="+", type=Path, help="Markdown files to validate")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    diagnostics = [item for path in args.files for item in validate_file(path)]
    if diagnostics:
        for diagnostic in diagnostics:
            print(diagnostic.format(), file=sys.stderr)
        return 1

    for path in args.files:
        print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
