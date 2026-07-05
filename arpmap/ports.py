"""Lightweight TCP port scanning to fingerprint what a device is running.

A plain ``connect()`` scan (no raw sockets, so no admin rights needed): if the
three-way handshake completes, the port is open. Scans run concurrently with a
short timeout so probing a host across the common-ports set takes well under a
second on a responsive device.
"""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor

_DEFAULT_TIMEOUT = 0.5
_MAX_WORKERS = 100

# Common service ports, used when the caller doesn't specify a list. Chosen to
# hint at device type (NAS, printer, router admin, media, IoT, remote access).
COMMON_PORTS: dict[int, str] = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
    53: "dns",
    80: "http",
    139: "netbios",
    443: "https",
    445: "smb",
    515: "printer",
    554: "rtsp",
    631: "ipp",
    1883: "mqtt",
    3389: "rdp",
    5000: "upnp/http",
    5353: "mdns",
    6379: "redis",
    8080: "http-alt",
    8443: "https-alt",
    8123: "home-assistant",
    9100: "printer-raw",
    32400: "plex",
}


def service_name(port: int) -> str:
    """Best-effort service label for ``port``."""
    return COMMON_PORTS.get(port, "?")


def check_port(ip: str, port: int, timeout: float = _DEFAULT_TIMEOUT) -> bool:
    """True if a TCP connection to ``ip:port`` succeeds within ``timeout``."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            return sock.connect_ex((ip, port)) == 0
        except OSError:
            return False


def scan_host(
    ip: str,
    ports: list[int] | None = None,
    *,
    timeout: float = _DEFAULT_TIMEOUT,
) -> list[tuple[int, str]]:
    """Return the open ``(port, service)`` pairs on ``ip``, sorted by port."""
    ports = ports if ports is not None else sorted(COMMON_PORTS)
    open_ports: list[tuple[int, str]] = []
    with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, len(ports))) as pool:
        futures = {port: pool.submit(check_port, ip, port, timeout) for port in ports}
        for port, future in futures.items():
            if future.result():
                open_ports.append((port, service_name(port)))
    open_ports.sort()
    return open_ports


def parse_ports(spec: str) -> list[int]:
    """Parse a ``--ports`` spec like ``22,80,443`` or ``1-1024`` into a list.

    Supports comma-separated single ports and ``start-end`` ranges.
    """
    ports: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start, end = chunk.split("-", 1)
            ports.update(range(int(start), int(end) + 1))
        else:
            ports.add(int(chunk))
    return sorted(p for p in ports if 0 < p < 65536)
