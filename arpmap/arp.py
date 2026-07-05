"""Cross-platform ARP table reading and parsing.

Windows ``arp -a`` groups entries under ``Interface:`` headers with dash-separated
MACs::

    Interface: 192.168.1.48 --- 0x11
      Internet Address      Physical Address      Type
      192.168.1.1           d8-4a-2b-3e-16-f0     dynamic

Linux/macOS ``arp -a`` uses a flat, colon-separated layout::

    ? (192.168.1.1) at d8:4a:2b:3e:16:f0 [ether] on eth0
    router.lan (192.168.1.1) at d8:4a:2b:3e:16:f0 on en0 ifscope [ethernet]

A single regex handles all three; MACs are normalized to lowercase colon form so
the rest of the app never has to care about the source platform.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

# IP anywhere on the line, followed (in the same line) by a MAC in either
# ``aa:bb:cc:dd:ee:ff`` or ``aa-bb-cc-dd-ee-ff`` form.
_LINE_RE = re.compile(
    r"(?P<ip>\d{1,3}(?:\.\d{1,3}){3})"
    r".*?"
    r"(?P<mac>(?:[0-9a-fA-F]{1,2}[:-]){5}[0-9a-fA-F]{1,2})"
)

# MACs that are never a real unicast host we'd want to name/track.
_IGNORED_MAC_PREFIXES = ("ff:ff:ff", "00:00:00", "01:00:5e", "33:33")


@dataclass(frozen=True)
class Device:
    """A single (ip, mac) pair discovered in the ARP table."""

    ip: str
    mac: str


def normalize_mac(mac: str) -> str:
    """Return ``mac`` as lowercase, colon-separated, zero-padded octets.

    Handles BSD/macOS shorthand where leading zeros are stripped
    (``1:0:5e:0:0:fb`` -> ``01:00:5e:00:00:fb``).
    """
    octets = mac.replace("-", ":").lower().split(":")
    return ":".join(o.zfill(2) for o in octets)


def is_private_ipv4(ip: str) -> bool:
    """True if ``ip`` is in a private RFC1918 range.

    Fixes the original ``ip.startswith("172.")`` bug, which wrongly matched the
    entire 172.0.0.0/8 block instead of only 172.16.0.0/12.
    """
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        octets = [int(p) for p in parts]
    except ValueError:
        return False
    if any(o < 0 or o > 255 for o in octets):
        return False
    a, b = octets[0], octets[1]
    if a == 192 and b == 168:
        return True
    if a == 10:
        return True
    if a == 172 and 16 <= b <= 31:
        return True
    return False


def _is_ignorable_mac(mac: str) -> bool:
    if mac.startswith(_IGNORED_MAC_PREFIXES):
        return True
    # Locally-administered / multicast bit set on the first octet -> not a host.
    try:
        first = int(mac.split(":")[0], 16)
    except ValueError:
        return True
    return bool(first & 0x01)  # multicast bit


def parse_arp_output(output: str, *, only_private: bool = True) -> list[Device]:
    """Parse raw ``arp -a`` text into a de-duplicated list of :class:`Device`.

    Args:
        output: Raw stdout from ``arp -a``.
        only_private: When True, keep only RFC1918 addresses (default behavior,
            matching the original tool). Set False for ``--all``.
    """
    seen: set[str] = set()
    devices: list[Device] = []
    for line in output.splitlines():
        match = _LINE_RE.search(line)
        if not match:
            continue
        ip = match.group("ip")
        mac = normalize_mac(match.group("mac"))

        if only_private and not is_private_ipv4(ip):
            continue
        if _is_ignorable_mac(mac):
            continue
        if mac in seen:
            continue
        seen.add(mac)
        devices.append(Device(ip=ip, mac=mac))

    devices.sort(key=lambda d: tuple(int(o) for o in d.ip.split(".")))
    return devices


def read_arp_table() -> str:
    """Return raw ``arp -a`` output for the current host."""
    return subprocess.check_output(["arp", "-a"], text=True)


def get_devices(*, only_private: bool = True) -> list[Device]:
    """Read and parse the live ARP table."""
    return parse_arp_output(read_arp_table(), only_private=only_private)
