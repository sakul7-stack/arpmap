"""Reverse-DNS / hostname resolution for discovered IPs.

Uses the standard resolver (``socket.gethostbyaddr``), which picks up PTR records
from your DNS server and, on many home networks, router-provided or mDNS names.
Lookups are done concurrently because a failed one can take up to the resolver
timeout.
"""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor

_MAX_WORKERS = 32


def resolve(ip: str) -> str | None:
    """Return the reverse-DNS hostname for ``ip``, or None if there isn't one."""
    try:
        host, _aliases, _addrs = socket.gethostbyaddr(ip)
    except (socket.herror, socket.gaierror, OSError):
        return None
    # Drop a trailing dot and an uninformative bare-IP answer.
    host = host.rstrip(".")
    return host or None if host != ip else None


def resolve_many(ips: list[str]) -> dict[str, str | None]:
    """Resolve many IPs concurrently -> ``{ip: hostname_or_None}``."""
    if not ips:
        return {}
    with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, len(ips))) as pool:
        results = pool.map(resolve, ips)
    return dict(zip(ips, results))
