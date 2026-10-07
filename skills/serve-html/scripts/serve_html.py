#!/usr/bin/env python3
"""Print an HTTP serving command and remote URLs for an absolute HTML path."""

import argparse
import ipaddress
import json
from pathlib import Path
import shlex
import socket
import subprocess
import sys
from urllib.parse import quote


VPN_PREFIXES = ("tailscale", "tun", "tap", "wg", "ppp", "vpn", "zt")
CONTAINER_PREFIXES = (
    "docker", "podman", "veth", "virbr", "br-", "cni", "flannel", "cali", "lxc",
)


def network_addresses(interface=None):
    """Find usable IPv4 addresses; private and VPN addresses are intentional."""
    try:
        result = subprocess.run(
            ["ip", "-j", "address", "show"],
            check=True, capture_output=True, text=True, timeout=5,
        )
        interfaces = json.loads(result.stdout)
    except FileNotFoundError as error:
        raise ValueError("'ip' is required; install the Linux iproute2 tools") from error
    except (subprocess.SubprocessError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read network addresses from 'ip': {error}") from error
    if not isinstance(interfaces, list):
        raise ValueError("'ip' returned an unexpected address list")

    addresses = []
    for entry in interfaces:
        name = entry["ifname"]
        if interface is not None and name != interface:
            continue
        if "UP" not in entry.get("flags", []) or entry.get("operstate") == "DOWN":
            continue
        if "LOOPBACK" in entry.get("flags", []) or name == "lo":
            continue
        if interface is None and name.startswith(CONTAINER_PREFIXES):
            continue
        for info in entry.get("addr_info", []):
            if info.get("family") != "inet" or info.get("scope") != "global":
                continue
            address = ipaddress.IPv4Address(info["local"])
            if (address.is_loopback or address.is_link_local or address.is_unspecified
                    or address.is_multicast):
                continue
            addresses.append({"interface": name, "address": str(address)})

    addresses.sort(key=lambda item: not item["interface"].startswith(VPN_PREFIXES))
    seen = set()
    unique = []
    for item in addresses:
        if item["address"] not in seen:
            unique.append(item)
            seen.add(item["address"])
    addresses = unique
    if not addresses:
        target = f" on interface {interface!r}" if interface else ""
        raise ValueError(f"no active VPN/LAN IPv4 address found{target}")
    return addresses


def available_port(requested=None):
    """Probe the same IPv4 wildcard bind used by the printed server command."""
    ports = [requested] if requested is not None else range(8000, 8100)
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("0.0.0.0", port))
            except OSError as error:
                if requested is not None:
                    raise ValueError(f"port {port} is unavailable: {error}") from error
                continue
        return port
    raise ValueError("no available serving port in 8000–8099")


def serving_plan(html_path, port=None, interface=None):
    html = Path(html_path)
    if not html.is_absolute():
        raise ValueError("HTML path must be absolute")
    if html.suffix.lower() not in (".html", ".htm"):
        raise ValueError("expected an .html or .htm file")
    if not html.is_file():
        raise ValueError(f"HTML file does not exist or is not a regular file: {html}")
    with html.open("rb"):
        pass
    # Preserve the supplied parent directory so symlinked HTML keeps nearby assets.
    directory = str(html.parent)
    addresses = network_addresses(interface)
    port = available_port(port)
    filename = quote(html.name, safe="")
    argv = [sys.executable, "-m", "http.server", str(port),
            "--bind", "0.0.0.0", "--directory", directory]
    return {
        "directory": directory,
        "port": port,
        "command": shlex.join(argv),
        "urls": [{"interface": item["interface"],
                  "url": f"http://{item['address']}:{port}/{filename}"}
                 for item in addresses],
        "local_url": f"http://127.0.0.1:{port}/{filename}",
    }


def port_number(value):
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("port must be an integer") from error
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_path", help="absolute path of the HTML file to review")
    parser.add_argument("--port", type=port_number, help="require this port (default: first free port from 8000)")
    parser.add_argument("--interface", help="use an address from this active interface")
    parser.add_argument("--json", action="store_true", help="print the serving plan as JSON")
    args = parser.parse_args()
    try:
        plan = serving_plan(args.html_path, args.port, args.interface)
    except (ValueError, OSError) as error:
        parser.exit(1, f"error: {error}\n")

    if args.json:
        print(json.dumps(plan, indent=2))
    else:
        print(f"Directory: {plan['directory']}\n\nStart the server:\n{plan['command']}")
        print("\nOpen from your local PC over the VPN:")
        for item in plan["urls"]:
            print(f"- [{item['interface']}]({item['url']})")
        print(f"\nServer-local check: {plan['local_url']}")
        print("\nRun the command in your SSH terminal, then open a network link.")
        print("Press Ctrl+C in that terminal when finished. No server was started.")


if __name__ == "__main__":
    main()
