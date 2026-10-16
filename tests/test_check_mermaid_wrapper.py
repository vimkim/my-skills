"""The legacy entry point delegates to docserve without interpreting documents."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/markdown-write/scripts/check_mermaid_blocks.mjs"
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node is required only to test the compatibility entry point")
class MermaidCompatibility(unittest.TestCase):
    def test_arguments_output_and_exit_status_pass_through(self):
        with tempfile.TemporaryDirectory() as directory:
            command = Path(directory) / "docserve-check"
            command.write_text(f"#!{sys.executable}\n" + """import json, os, sys
print(json.dumps(sys.argv[1:], ensure_ascii=False))
print('checker diagnostic', file=sys.stderr)
sys.exit(int(os.environ['CHECK_EXIT_CODE']))
""", encoding="utf-8")
            command.chmod(0o755)
            args = ["한글 review #1's ?.md", "other $(literal).md", "--render", "--json"]
            for status in (0, 1, 2):
                with self.subTest(status=status):
                    result = subprocess.run([NODE, str(SCRIPT), *args], text=True,
                                            capture_output=True, env={**os.environ,
                                            "PATH": directory, "CHECK_EXIT_CODE": str(status)}, timeout=5)
                    self.assertEqual(result.returncode, status)
                    self.assertEqual(json.loads(result.stdout), ["mermaid", *args])
                    self.assertEqual(result.stderr, "checker diagnostic\n")

    def test_missing_command_returns_actionable_environment_error(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([NODE, str(SCRIPT), "document.md"], text=True,
                                    capture_output=True, env={**os.environ, "PATH": directory}, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("docserve-check is unavailable", result.stderr)
        self.assertIn("checker support", result.stderr)


if __name__ == "__main__":
    unittest.main()
