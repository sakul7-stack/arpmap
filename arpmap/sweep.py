"""Active discovery: ping every host on the local /24 to populate the ARP cache.

``arp -a`` only shows addresses the OS has recently talked to. A quick concurrent
ping sweep forces the kernel to resolve every reachable host so the subsequent ARP
read sees the whole subnet, not just cached neighbours.
"""

from __future__ import annotations

import ipaddress
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

_MAX_WORKERS = 64
_PING_TIMEOUT_MS = 500


def local_ipv4() -> str | None:
    """Best-effort discovery of this host's primary IPv4 address."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No packets are actually sent; this just selects the outbound route.
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()


def subnet_hosts(ip: str, prefix: int = 24) -> list[str]:
    """All host addresses in the /``prefix`` network containing ``ip``."""
    network = ipaddress.ip_network(f"{ip}/{prefix}", strict=False)
    return [str(host) for host in network.hosts()]


def _ping_cmd(host: str) -> list[str]:
    if sys.platform.startswith("win"):
        return ["ping", "-n", "1", "-w", str(_PING_TIMEOUT_MS), host]
    # Unix ping uses whole-second waits; round up from the ms budget.
    seconds = max(1, _PING_TIMEOUT_MS // 1000)
    return ["ping", "-c", "1", "-W", str(seconds), host]


def _ping(host: str) -> bool:
    try:
        result = subprocess.run(
            _ping_cmd(host),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=_PING_TIMEOUT_MS / 1000 + 2,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def sweep(ip: str | None = None, *, prefix: int = 24) -> int:
    """Ping-sweep the subnet of ``ip`` (or the auto-detected local IP).

    Returns the number of hosts that responded. Failures are swallowed; the point
    is the side effect of populating the ARP cache, not the return value.
    """
    ip = ip or local_ipv4()
    if not ip:
        return 0
    hosts = subnet_hosts(ip, prefix)
    responded = 0
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        for alive in pool.map(_ping, hosts):
            if alive:
                responded += 1
    return responded
