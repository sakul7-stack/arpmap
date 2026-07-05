"""MAC-address -> hardware vendor resolution.

Offline by default: the first three octets of a MAC (its OUI) are looked up in a
small bundled table (``data/oui.csv``). Pass ``online=True`` to fall back to the
free macvendors.com API for prefixes that aren't bundled; results are cached in
memory for the process lifetime so each OUI is fetched at most once.
"""

from __future__ import annotations

import csv
import json
import os
import urllib.error
import urllib.request

_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "oui.csv")

_ONLINE_URL = "https://api.macvendors.com/{mac}"
_ONLINE_TIMEOUT = 4  # seconds

_oui_table: dict[str, str] | None = None
_online_cache: dict[str, str] = {}


def _load_table() -> dict[str, str]:
    global _oui_table
    if _oui_table is None:
        table: dict[str, str] = {}
        try:
            with open(_DATA_FILE, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    prefix = row["prefix"].strip().lower()
                    if prefix:
                        table[prefix] = row["vendor"].strip()
        except FileNotFoundError:
            pass
        _oui_table = table
    return _oui_table


def _oui(mac: str) -> str:
    """Return the ``aa:bb:cc`` prefix of a normalized MAC."""
    return ":".join(mac.split(":")[:3]).lower()


def _lookup_online(mac: str) -> str | None:
    prefix = _oui(mac)
    if prefix in _online_cache:
        return _online_cache[prefix] or None
    request = urllib.request.Request(
        _ONLINE_URL.format(mac=mac), headers={"User-Agent": "arpmap"}
    )
    try:
        with urllib.request.urlopen(request, timeout=_ONLINE_TIMEOUT) as resp:
            vendor = resp.read().decode().strip()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        vendor = ""
    _online_cache[prefix] = vendor
    return vendor or None


def lookup(mac: str, *, online: bool = False) -> str | None:
    """Resolve ``mac`` to a vendor name, or None if unknown.

    Tries the offline table first; only hits the network when ``online`` is True
    and the prefix is unknown offline.
    """
    if not mac:
        return None
    vendor = _load_table().get(_oui(mac))
    if vendor:
        return vendor
    if online:
        return _lookup_online(mac)
    return None
