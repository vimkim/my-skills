from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = SKILL_ROOT / "scripts" / "check_copyparty_markdown.py"
SPEC = importlib.util.spec_from_file_location("copyparty_markdown_checker", CHECKER_PATH)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


class CheckerTests(unittest.TestCase):
    def write(self, root: Path, relative: str, content: str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_accepts_supported_rendering_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "guide-assets/lifecycle.svg",
                '<svg viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">'
                '<rect width="20" height="20"/></svg>',
            )
            markdown = self.write(
                root,
                "guide.md",
                r'''# Guide

![Lifecycle](./guide-assets/lifecycle.svg)

```mermaid
flowchart LR
    A --> B
```

Inline math: $E = mc^2$

$$
\int_0^1 x\,dx
$$

\\(
a^2 + b^2 = c^2
\\)

\\[
\nabla \cdot \mathbf{E}
\\]

<svg viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg">
  <circle cx="5" cy="5" r="4"/>
</svg>
''',
            )

            self.assertEqual(CHECKER.validate_file(markdown), [])

    def test_rejects_broken_delimiters_mermaid_links_and_inline_svg(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            markdown = self.write(
                root,
                "broken.md",
                r'''[local](file:///home/user/private.md)

![](./missing.svg)

\[
x
\]

```mermaid
```

<svg onload="bad()"><foreignObject/></svg>
''',
            )

            messages = "\n".join(item.message for item in CHECKER.validate_file(markdown))
            for expected in (
                "Machine-local link",
                "missing alt text",
                "does not exist",
                "Single-backslash TeX delimiter",
                "Mermaid fence is empty",
                "missing a viewBox",
                "missing the SVG xmlns",
                "event-handler attributes",
                "foreignObject",
            ):
                self.assertIn(expected, messages)

    def test_rejects_unsafe_external_svg(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "assets/unsafe.svg",
                '<svg xmlns="http://www.w3.org/2000/svg"><script>bad()</script></svg>',
            )
            markdown = self.write(root, "doc.md", "![Unsafe](./assets/unsafe.svg)\n")

            messages = "\n".join(item.message for item in CHECKER.validate_file(markdown))
            self.assertIn("missing a viewBox", messages)
            self.assertIn("must not contain scripts", messages)

    def test_ignores_examples_inside_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            markdown = self.write(
                root,
                "code.md",
                r'''Literal `\[x\]` and a fenced example:

```markdown
\[
not rendered
\]
```
''',
            )

            self.assertEqual(CHECKER.validate_file(markdown), [])


if __name__ == "__main__":
    unittest.main()
