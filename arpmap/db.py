"""Persistent device database.

The database is a JSON object keyed by normalized MAC address. Each value is a
record::

    {
        "name": "arch-laptop",
        "vendor": "Raspberry Pi Foundation",
        "last_ip": "192.168.1.10",
        "first_seen": "2026-07-05T11:05:00",
        "last_seen":  "2026-07-05T11:05:00"
    }

Version 0.1 stored a flat ``{mac: "name"}`` mapping. :func:`load_db` transparently
upgrades that old shape so existing ``arpmap_db.json`` files keep working.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

DEFAULT_DB_FILE = "arpmap_db.json"

RECORD_FIELDS = ("name", "vendor", "last_ip", "first_seen", "last_seen")


def _blank_record() -> dict[str, Any]:
    return {field: None for field in RECORD_FIELDS}


def _migrate_value(value: Any) -> dict[str, Any]:
    """Coerce any stored value into the current record shape."""
    record = _blank_record()
    if isinstance(value, str):
        # Old flat format: the value was just the device name.
        record["name"] = value
    elif isinstance(value, dict):
        record.update({k: value.get(k) for k in RECORD_FIELDS if k in value})
    return record


def load_db(path: str = DEFAULT_DB_FILE) -> dict[str, dict[str, Any]]:
    """Load the database, migrating older formats. Missing file -> empty db."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict):
        return {}
    return {mac.lower(): _migrate_value(val) for mac, val in raw.items()}


def save_db(db: dict[str, dict[str, Any]], path: str = DEFAULT_DB_FILE) -> None:
    """Persist the database as pretty-printed JSON."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(db, fh, indent=4, sort_keys=True)
        fh.write("\n")


def now_iso() -> str:
    """Current local time as an ISO-8601 string (seconds precision)."""
    return datetime.now().replace(microsecond=0).isoformat()


def record_for(db: dict[str, dict[str, Any]], mac: str) -> dict[str, Any]:
    """Return the record for ``mac``, creating a blank one if absent."""
    mac = mac.lower()
    record = db.get(mac)
    if record is None:
        record = _blank_record()
        db[mac] = record
    return record


def touch(
    db: dict[str, dict[str, Any]],
    mac: str,
    *,
    ip: str | None = None,
    vendor: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Update first/last-seen (and optionally ip/vendor) for ``mac``.

    Returns the record. ``first_seen`` is only set once; ``last_seen`` and
    ``last_ip`` are refreshed each call. ``vendor`` is only filled if not already
    known, so a cached online lookup is never overwritten by a blank.
    """
    stamp = timestamp or now_iso()
    record = record_for(db, mac)
    if not record.get("first_seen"):
        record["first_seen"] = stamp
    record["last_seen"] = stamp
    if ip is not None:
        record["last_ip"] = ip
    if vendor and not record.get("vendor"):
        record["vendor"] = vendor
    return record


def find_mac(db: dict[str, dict[str, Any]], token: str) -> str | None:
    """Resolve ``token`` (a MAC or an IP) to a stored MAC key, or None."""
    from arpmap.arp import normalize_mac

    candidate = normalize_mac(token)
    if candidate in db:
        return candidate
    for mac, record in db.items():
        if record.get("last_ip") == token:
            return mac
    return None
