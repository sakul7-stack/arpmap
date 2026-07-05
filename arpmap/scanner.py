"""Orchestration: optionally sweep, read the ARP table, merge into the database.

This is the glue between :mod:`arpmap.arp`, :mod:`arpmap.sweep`,
:mod:`arpmap.vendor`, and :mod:`arpmap.db`. It produces a list of enriched rows
that the CLI/display layer renders, and mutates the database in place with fresh
timestamps and any newly-resolved vendors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arpmap import arp, db, sweep, vendor


@dataclass
class ScanRow:
    """A device seen in a scan, enriched with stored/looked-up metadata."""

    ip: str
    mac: str
    name: str | None
    vendor: str | None
    first_seen: str | None
    last_seen: str | None


def scan(
    database: dict[str, dict[str, Any]],
    *,
    do_sweep: bool = False,
    online: bool = False,
    only_private: bool = True,
) -> list[ScanRow]:
    """Discover devices and merge them into ``database``.

    Args:
        database: Loaded db dict; mutated in place (call :func:`arpmap.db.save_db`
            afterward to persist).
        do_sweep: Ping the local subnet first to widen discovery.
        online: Allow online vendor lookups for unknown OUIs.
        only_private: Restrict to RFC1918 addresses.
    """
    if do_sweep:
        sweep.sweep()

    stamp = db.now_iso()
    rows: list[ScanRow] = []
    for device in arp.get_devices(only_private=only_private):
        existing = database.get(device.mac, {})
        resolved_vendor = existing.get("vendor") or vendor.lookup(
            device.mac, online=online
        )
        record = db.touch(
            database,
            device.mac,
            ip=device.ip,
            vendor=resolved_vendor,
            timestamp=stamp,
        )
        rows.append(
            ScanRow(
                ip=device.ip,
                mac=device.mac,
                name=record.get("name"),
                vendor=record.get("vendor"),
                first_seen=record.get("first_seen"),
                last_seen=record.get("last_seen"),
            )
        )
    return rows


def inventory_rows(database: dict[str, dict[str, Any]]) -> list[ScanRow]:
    """Build rows from stored records only (no scan), sorted by name then MAC."""
    rows = [
        ScanRow(
            ip=rec.get("last_ip") or "",
            mac=mac,
            name=rec.get("name"),
            vendor=rec.get("vendor"),
            first_seen=rec.get("first_seen"),
            last_seen=rec.get("last_seen"),
        )
        for mac, rec in database.items()
    ]
    rows.sort(key=lambda r: ((r.name or "~").lower(), r.mac))
    return rows
