"""Exercise remote link discovery and the actual generated HTTP command."""

import importlib.util
import json
from pathlib import Path
import shlex
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import ProxyHandler, build_opener


SCRIPT = Path(__file__).resolve().parents[1] / "skills/serve-html/scripts/serve_html.py"
SPEC = importlib.util.spec_from_file_location("serve_html", SCRIPT)
helper = importlib.util.module_from_spec(SPEC)
with patch.object(sys, "dont_write_bytecode", True):
    SPEC.loader.exec_module(helper)


def interface(name, address, **extra):
    return {"ifname": name, "flags": ["UP"], "operstate": "UP",
            "addr_info": [{"family": "inet", "local": address, "scope": "global"}],
            **extra}


class ServeHTML(unittest.TestCase):
    def addresses(self, entries, selected=None):
        result = subprocess.CompletedProcess([], 0, json.dumps(entries), "")
        with patch.object(helper.subprocess, "run", return_value=result):
            return helper.network_addresses(selected)

    def test_vpn_preferred_and_non_remote_addresses_excluded(self):
        found = self.addresses([
            interface("lo", "127.0.0.1"),
            interface("eno1", "192.168.4.2"),
            interface("docker0", "172.17.0.1"),
            interface("podman0", "10.88.0.1"),
            interface("br-container", "172.18.0.1"),
            interface("eno2", "192.168.5.2", operstate="DOWN"),
            interface("wg0", "10.1.0.2", operstate="UNKNOWN"),
            interface("eno3", "169.254.1.2"),
            interface("eno4", "0.0.0.0"),
        ])
        self.assertEqual(found, [
            {"interface": "wg0", "address": "10.1.0.2"},
            {"interface": "eno1", "address": "192.168.4.2"},
        ])

    def test_interface_selection_and_missing_address(self):
        entries = [interface("eno1", "192.168.4.2"), interface("tailscale0", "100.68.111.110")]
        self.assertEqual(self.addresses(entries, "eno1"),
                         [{"interface": "eno1", "address": "192.168.4.2"}])
        with self.assertRaisesRegex(ValueError, "no active"):
            self.addresses(entries, "missing")
        with self.assertRaisesRegex(ValueError, "no active"):
            self.addresses([interface("lo", "127.0.0.1")])

    def test_duplicate_address_keeps_vpn_interface(self):
        found = self.addresses([interface("eno1", "10.1.0.2"), interface("tun0", "10.1.0.2")])
        self.assertEqual(found, [{"interface": "tun0", "address": "10.1.0.2"}])

    def test_ip_command_failures_are_actionable(self):
        for error in (FileNotFoundError(), subprocess.TimeoutExpired("ip", 5)):
            with self.subTest(error=error), patch.object(helper.subprocess, "run", side_effect=error):
                with self.assertRaisesRegex(ValueError, "ip"):
                    helper.network_addresses()
        with patch.object(helper.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "invalid", "")):
            with self.assertRaisesRegex(ValueError, "could not read"):
                helper.network_addresses()

    def test_busy_port_is_skipped_or_explicitly_rejected(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as busy:
            busy.bind(("0.0.0.0", helper.available_port()))
            port = busy.getsockname()[1]
            busy.listen()
            self.assertGreater(helper.available_port(), port)
            with self.assertRaisesRegex(ValueError, "unavailable"):
                helper.available_port(port)

    def test_invalid_file_paths_and_ports_fail_without_a_plan(self):
        for args in (["relative.html"], ["/nonexistent/review.html"], ["/tmp/file.txt"],
                     ["/tmp/page.html", "--port", "0"], ["/tmp/page.html", "--port", "65536"]):
            with self.subTest(args=args):
                run = subprocess.run([sys.executable, str(SCRIPT), *args, "--json"],
                                     text=True, capture_output=True)
                self.assertNotEqual(run.returncode, 0)
                self.assertEqual(run.stdout, "")
                self.assertIn("error:", run.stderr)

    def test_command_serves_encoded_html_and_adjacent_assets(self):
        with tempfile.TemporaryDirectory(prefix="serve-html-test-") as temp:
            directory = Path(temp) / "review's $(touch SHOULD_NOT_EXIST) files"
            directory.mkdir()
            html = directory / "한글 review #1's ?.html"
            content = b'<html><link rel="stylesheet" href="style.css">Review</html>'
            html.write_bytes(content)
            (directory / "style.css").write_bytes(b"body { color: navy; }")
            (directory.parent / "outside.txt").write_text("outside serving directory")
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                port = probe.getsockname()[1]

            result = subprocess.CompletedProcess([], 0, json.dumps([interface("tun0", "10.1.0.2")]), "")
            with patch.object(helper.subprocess, "run", return_value=result):
                plan = helper.serving_plan(str(html), port)
            self.assertEqual(plan["directory"], str(directory))
            self.assertEqual(plan["urls"][0]["url"], f"http://10.1.0.2:{port}/{quote(html.name, safe='')}")
            self.assertEqual(shlex.split(plan["command"])[-1], str(directory))

            # Execute through a shell to verify the printed command's quoting.
            process = subprocess.Popen("exec " + plan["command"], shell=True, cwd=temp,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
            try:
                client = build_opener(ProxyHandler({}))
                deadline = time.monotonic() + 5
                while True:
                    try:
                        with client.open(plan["local_url"], timeout=1) as response:
                            self.assertEqual(response.read(), content)
                        break
                    except OSError:
                        if process.poll() is not None or time.monotonic() >= deadline:
                            raise
                        time.sleep(0.05)
                with client.open(f"http://127.0.0.1:{port}/style.css", timeout=1) as response:
                    self.assertEqual(response.read(), b"body { color: navy; }")
                try:
                    with client.open(f"http://127.0.0.1:{port}/../outside.txt", timeout=1):
                        self.fail("server exposed a file outside its serving directory")
                except HTTPError as error:
                    self.assertEqual(error.code, 404)
                    error.close()
                self.assertFalse((Path(temp) / "SHOULD_NOT_EXIST").exists())
            finally:
                process.terminate()
                process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
